from collections import defaultdict

from flask import Blueprint, abort, current_app, flash, redirect, render_template, request, send_from_directory, url_for
from flask_login import current_user, login_required
from sqlalchemy.orm import joinedload

from app.domain.auth.policies.auth_policy import has_permission, has_role
from app.extensions import db
from app.modules.auth.models import User
from app.modules.drivers.models import DriverActivityLog, DriverDocument, DriverLicense, DriverProfile
from app.modules.vehicles.models import Vehicle
from app.services.compliance.document_compliance import build_driver_compliance, build_vehicle_compliance
from app.modules.notifications.helpers import create_notification_safe
from app.services.compliance.alerts_service import run_compliance_alerts
from app.domain.auth.policies.auth_policy import has_permission


documents_bp = Blueprint('documents', __name__, url_prefix='/documents')


def can_review_documents():
    return (
        has_permission('documents.verify')
        or has_permission('documents.approvals.view')
        or has_role(['Super Admin', 'KAM-CIRCLE', 'KAM-CORPORATE', 'Key Account Manager', 'Corporate Admin'])
    )


def can_view_documents():
    return has_permission('documents.view') or has_permission('driver_profiles.view') or has_role(['Driver'])


def can_view_enterprise_documents():
    return has_permission('documents.view') or has_permission('driver_profiles.view') or has_role(['Super Admin'])


def current_driver_profile():
    return DriverProfile.query.filter_by(user_id=current_user.id).first()


def driver_documents_for(profile):
    if not profile:
        return []
    return (
        DriverDocument.query.filter_by(driver_id=profile.id)
        .order_by(DriverDocument.uploaded_at.desc())
        .all()
    )


@documents_bp.route('/drivers')
@login_required
def drivers():
    if not can_view_documents():
        abort(403)

    own_profile = current_driver_profile()
    if has_role(['Driver']) and not has_permission('documents.view'):
        profiles = [own_profile] if own_profile else []
    else:
        profiles = (
            DriverProfile.query.options(
                joinedload(DriverProfile.user),
                joinedload(DriverProfile.circle),
                joinedload(DriverProfile.project),
                joinedload(DriverProfile.subzone),
            )
            .order_by(DriverProfile.updated_at.desc())
            .limit(100)
            .all()
        )

    profile_ids = [profile.id for profile in profiles if profile]
    documents = DriverDocument.query.filter(DriverDocument.driver_id.in_(profile_ids)).all() if profile_ids else []
    licenses = DriverLicense.query.filter(DriverLicense.driver_id.in_(profile_ids)).all() if profile_ids else []
    docs_by_driver = defaultdict(list)
    license_by_driver = {}
    for document in documents:
        docs_by_driver[document.driver_id].append(document)
    for license_record in licenses:
        current = license_by_driver.get(license_record.driver_id)
        if not current or (license_record.expiry_date or license_record.created_at.date()) > (current.expiry_date or current.created_at.date()):
            license_by_driver[license_record.driver_id] = license_record

    rows = []
    totals = defaultdict(int)
    for profile in profiles:
        compliance = build_driver_compliance(profile, docs_by_driver.get(profile.id, []), license_by_driver.get(profile.id))
        totals[compliance['compliance_status'].lower().replace(' ', '_')] += 1
        totals[compliance['deployment_eligibility'].lower().replace(' ', '_')] += 1
        rows.append({'profile': profile, 'compliance': compliance})

    selected = rows[0] if rows else None
    return render_template(
        'documents/drivers.html',
        rows=rows,
        selected=selected,
        totals=dict(totals),
        active_page='driver_documents',
        can_review=can_review_documents(),
    )


@documents_bp.route('/drivers/<driver_profile_id>')
@login_required
def driver_detail(driver_profile_id):
    profile = DriverProfile.query.options(
        joinedload(DriverProfile.user),
        joinedload(DriverProfile.circle),
        joinedload(DriverProfile.project),
        joinedload(DriverProfile.subzone),
    ).get_or_404(driver_profile_id)
    if not can_view_documents():
        abort(403)
    if has_role(['Driver']) and profile.user_id != current_user.id and not has_permission('documents.view'):
        abort(403)

    documents = driver_documents_for(profile)
    latest_license = DriverLicense.query.filter_by(driver_id=profile.id).order_by(DriverLicense.expiry_date.desc().nulls_last()).first()
    compliance = build_driver_compliance(profile, documents, latest_license)
    timeline = (
        DriverActivityLog.query.filter_by(driver_id=profile.id)
        .filter(DriverActivityLog.event_type.in_(['Uploaded', 'Updated', 'Verified', 'Rejected', 'Re-uploaded', 'Request Re-upload']))
        .order_by(DriverActivityLog.created_at.desc())
        .limit(20)
        .all()
    )
    return render_template(
        'documents/driver_detail.html',
        profile=profile,
        documents=documents,
        compliance=compliance,
        timeline=timeline,
        active_page='driver_documents',
        can_review=can_review_documents(),
    )


@documents_bp.route('/drivers/<driver_profile_id>/documents/<document_id>/view')
@login_required
def view_driver_document(driver_profile_id, document_id):
    document = DriverDocument.query.filter_by(id=document_id, driver_id=driver_profile_id).first_or_404()
    profile = document.driver
    if not can_view_documents():
        abort(403)
    if has_role(['Driver']) and profile.user_id != current_user.id and not has_permission('documents.view'):
        abort(403)
    return send_from_directory(
        current_app.config['DRIVER_DOCUMENT_UPLOAD_FOLDER'],
        document.storage_path,
        as_attachment=False,
        download_name=document.file_name,
    )


@documents_bp.route('/drivers/<driver_profile_id>/documents/<document_id>/<action>', methods=['POST'])
@login_required
def review_driver_document(driver_profile_id, document_id, action):
    if not can_review_documents():
        abort(403)
    document = DriverDocument.query.filter_by(id=document_id, driver_id=driver_profile_id).first_or_404()
    action_map = {
        'verify': ('Verified', 'Verified'),
        'reject': ('Rejected', 'Rejected'),
        'request-reupload': ('Re-upload Requested', 'Request Re-upload'),
    }
    if action not in action_map:
        abort(404)

    document.status, event_type = action_map[action]
    db.session.add(DriverActivityLog(
        driver_id=driver_profile_id,
        actor_id=current_user.id,
        event_type=event_type,
        description=f'{document.document_type} marked as {document.status}.',
        event_metadata={'document_id': document.id, 'document_type': document.document_type},
    ))
    db.session.commit()
    # Safe notifications: inform driver and compliance team on status changes
    try:
        driver_user_id = document.driver.user_id if document.driver else None
        if driver_user_id:
            create_notification_safe(
                user_id=driver_user_id,
                message=f"Your {document.document_type} was marked as {document.status}.",
                module='documents',
                priority='Info' if document.status == 'Verified' else 'High',
                related_type='document',
                related_id=str(document.id),
                route=f"/documents/drivers/{document.driver_id}",
                metadata={'document_id': document.id, 'document_type': document.document_type}
            )
        # System-wide alert for compliance officers (user_id=None)
        if document.status in ('Rejected', 'Re-upload Requested'):
            create_notification_safe(
                user_id=None,
                message=f"Document {document.document_type} for driver {document.driver_id} requires attention: {document.status}.",
                module='documents',
                priority='High',
                related_type='document',
                related_id=str(document.id),
                route=f"/documents/drivers/{document.driver_id}",
                metadata={'document_id': document.id, 'document_type': document.document_type}
            )
    except Exception:
        pass
    flash('Document review status updated.', 'success')
    return redirect(request.referrer or url_for('documents.driver_detail', driver_profile_id=driver_profile_id))


@documents_bp.route('/vehicles')
@login_required
def vehicles():
    if not can_view_enterprise_documents():
        abort(403)
    query = Vehicle.query.options(
        joinedload(Vehicle.circle),
        joinedload(Vehicle.project),
        joinedload(Vehicle.subzone),
        joinedload(Vehicle.assigned_driver_user),
    )
    if getattr(current_user, 'company_id', None) and not has_role(['Super Admin']):
        query = query.filter(Vehicle.company_id == current_user.company_id)
    rows = []
    totals = defaultdict(int)
    for vehicle in query.order_by(Vehicle.updated_at.desc()).limit(150).all():
        compliance = build_vehicle_compliance(vehicle)
        totals[compliance['vehicle_compliance'].lower().replace(' ', '_')] += 1
        rows.append({'vehicle': vehicle, 'compliance': compliance})

    selected = rows[0] if rows else None
    return render_template(
        'documents/vehicles.html',
        rows=rows,
        selected=selected,
        totals=dict(totals),
        active_page='vehicle_documents',
    )


@documents_bp.route('/expiry')
@login_required
def expiry():
    # Manual trigger: run compliance alerts (permission-protected)
    if not has_permission('documents.manage'):
        abort(403)
    results = run_compliance_alerts()
    flash(f"Compliance alerts created: drivers={results.get('drivers')}, vehicles={results.get('vehicles')}", 'info')
    return redirect(url_for('documents.drivers'))


@documents_bp.route('/pending')
@login_required
def pending():
    return redirect(url_for('documents.drivers'))


@documents_bp.route('/approvals')
@login_required
def approvals():
    return redirect(url_for('documents.drivers'))
