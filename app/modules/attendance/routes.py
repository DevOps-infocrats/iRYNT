from datetime import date

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for, current_app, send_from_directory
from flask_login import current_user, login_required

from app.core.decorators import permission_required
from app.domain.auth.policies.auth_policy import has_permission, has_role
from app.modules.attendance.services import AttendanceService
from app.modules.attendance.utils import get_india_today
from app.modules.drivers.models import DriverProfile, DriverAttendance
from app.modules.attendance.verification_helpers import decode_base64_image, save_verification_image, validate_verification_image

attendance_bp = Blueprint('attendance', __name__, url_prefix='/attendance')
attendance_service = AttendanceService()


@attendance_bp.route('/live')
@login_required
@permission_required('attendance.view')
def live():
    from app.domain.auth.policies.auth_policy import has_role
    
    page = request.args.get('page', 1, type=int)
    per_page = 20
    filters = {
        'search_query': request.args.get('q', '').strip() or None,
        'company_id': request.args.get('company_id') or None,
        'circle_id': request.args.get('circle_id') or None,
    }

    if not current_user.is_superadmin:
        if current_user.circle_id:
            filters['circle_id'] = current_user.circle_id
        elif current_user.company_id:
            filters['company_id'] = current_user.company_id

    is_driver_user = has_role('Driver') and not has_role('Super Admin') and not has_role('Admin')
    is_helper_user = has_role('Helper') and not has_role('Super Admin') and not has_role('Admin')
    if is_helper_user:
        is_driver_user = True
        from app.modules.users.services.user_service import ensure_helper_profile
        ensure_helper_profile(current_user)

    driver_profile = None
    driver_history = []
    history_total = 0

    # If user is ONLY a driver or helper (not admin), only show their own attendance
    if is_driver_user:
        driver_profile = DriverProfile.query.filter_by(user_id=current_user.id).first()
        if driver_profile:
            filters['driver_id'] = driver_profile.id
            driver_history, history_total = attendance_service.list_attendance_history(
                {'driver_id': driver_profile.id}, page=1, per_page=7
            )
        else:
            # No driver profile, return empty
            return render_template(
                'attendance/live.html',
                drivers=[],
                total=0,
                page=1,
                per_page=per_page,
                current_date=get_india_today(),
                filters=filters,
                active_page='live_attendance',
                page_title='Mark Attendance',
                is_driver_user=True,
                is_helper_user=is_helper_user,
                driver_history=[],
                active_deployment=None,
                attendance_status='Absent'
            )

    drivers, total = attendance_service.list_live_attendance(filters, page, per_page)
    current_date = get_india_today()
    page_title = 'Mark Attendance' if is_driver_user else 'Live Attendance Dashboard'

    active_deployment = None
    active_helper_assignment = None
    attendance_status = 'Absent'
    if is_helper_user and driver_profile:
        from app.modules.deployments.models import HelperAssignment
        active_helper_assignment = HelperAssignment.query.filter_by(
            helper_id=current_user.id,
            status='Active'
        ).first()
        if not active_helper_assignment:
            from app.modules.deployments.models import VehicleDeployment
            active_dep = VehicleDeployment.query.filter_by(
                driver_id=current_user.id,
                status='Active',
                approval_status='Approved'
            ).first()
            if active_dep:
                from app.modules.attendance.services import FallbackHelperAssignment
                active_helper_assignment = FallbackHelperAssignment(
                    circle=active_dep.project.circle if (active_dep.project and hasattr(active_dep.project, 'circle')) else None,
                    project=active_dep.project,
                    subzone=active_dep.subzone,
                    shift='Day'
                )
            elif driver_profile.circle_id and driver_profile.project_id and driver_profile.subzone_id:
                from app.modules.circles.models import Circle
                from app.modules.projects.models import Project
                from app.modules.subzones.models import Subzone
                from app.modules.attendance.services import FallbackHelperAssignment
                circle = Circle.query.get(driver_profile.circle_id)
                project = Project.query.get(driver_profile.project_id)
                subzone = Subzone.query.get(driver_profile.subzone_id)
                active_helper_assignment = FallbackHelperAssignment(
                    circle=circle,
                    project=project,
                    subzone=subzone,
                    shift='Day'
                )
        
        if drivers:
            helper_driver = drivers[0]
            if helper_driver.get('attendance_id'):
                from app.modules.approvals.models import ApprovalRequest
                app_req = ApprovalRequest.query.filter_by(
                    entity_type='driver_attendance',
                    entity_id=helper_driver['attendance_id']
                ).filter(ApprovalRequest.approval_status.in_(['Pending', 'Under Review', 'Escalated', 'Approved', 'Rejected'])).first()
                
                if app_req:
                    if app_req.approval_status in ['Pending', 'Under Review', 'Escalated']:
                        attendance_status = 'Pending Approval'
                    elif app_req.approval_status == 'Approved':
                        attendance_status = 'Approved'
                    elif app_req.approval_status == 'Rejected':
                        attendance_status = 'Rejected'
                else:
                    if helper_driver.get('geo_status') == 'OUTSIDE_GEOFENCE':
                        attendance_status = 'Outside Geofence'
                    else:
                        attendance_status = 'Present'

    return render_template(
        'attendance/live.html',
        drivers=drivers,
        total=total,
        page=page,
        per_page=per_page,
        current_date=current_date,
        filters=filters,
        active_page='live_attendance',
        page_title=page_title,
        is_driver_user=is_driver_user,
        is_helper_user=is_helper_user,
        active_deployment=active_deployment,
        active_helper_assignment=active_helper_assignment,
        attendance_status=attendance_status,
        driver_history=driver_history,
        history_total=history_total,
    )


@attendance_bp.route('/history')
@login_required
@permission_required('attendance.history.view')
def history():
    from app.domain.auth.policies.auth_policy import has_role
    
    page = request.args.get('page', 1, type=int)
    per_page = 20

    filters = {
        'search_query': request.args.get('q', '').strip() or None,
        'date_from': request.args.get('date_from') or None,
        'date_to': request.args.get('date_to') or None,
        'company_id': None,
        'circle_id': None,
    }

    if not current_user.is_superadmin:
        if current_user.circle_id:
            filters['circle_id'] = current_user.circle_id
        elif current_user.company_id:
            filters['company_id'] = current_user.company_id

    # If user is ONLY a driver (not admin), only show their own attendance history
    if has_role('Driver') and not has_role('Super Admin') and not has_role('Admin'):
        driver_profile = DriverProfile.query.filter_by(user_id=current_user.id).first()
        if driver_profile:
            filters['driver_id'] = driver_profile.id
        else:
            # No driver profile, return empty
            return render_template(
                'attendance/history.html',
                records=[],
                total=0,
                page=1,
                per_page=per_page,
                filters=filters,
                active_page='attendance_history',
            )

    records, total = attendance_service.list_attendance_history(filters, page, per_page)

    return render_template(
        'attendance/history.html',
        records=records,
        total=total,
        page=page,
        per_page=per_page,
        filters=filters,
        active_page='attendance_history',
    )


@attendance_bp.route('/monitoring')
@login_required
@permission_required('attendance.view')
def monitoring():
    filters = {
        'search_query': request.args.get('q', '').strip() or None,
        'company_id': request.args.get('company_id') or None,
        'circle_id': request.args.get('circle_id') or None,
    }

    if not current_user.is_superadmin:
        if current_user.circle_id:
            filters['circle_id'] = current_user.circle_id
        elif current_user.company_id:
            filters['company_id'] = current_user.company_id

    summary = attendance_service.get_monitoring_summary(filters)

    return render_template(
        'attendance/monitoring.html',
        summary=summary,
        active_page='check_in_monitoring',
    )


@attendance_bp.route('/approvals')
@login_required
@permission_required('attendance.approve')
def approvals():
    approvals = attendance_service.get_attendance_approvals(user=current_user)
    total = len(approvals)

    return render_template(
        'attendance/approvals.html',
        approvals=approvals,
        total=total,
        active_page='attendance_approvals',
    )


@attendance_bp.route('/shift-reports')
@login_required
@permission_required('reports.view')
def shift_reports():
    report_summary = attendance_service.get_shift_reports()

    return render_template(
        'attendance/shift_reports.html',
        report_summary=report_summary,
        active_page='shift_reports',
    )


@attendance_bp.route('/mark', methods=['POST'], endpoint='mark')
@login_required
@permission_required('attendance.mark')
def mark_attendance():
    driver_profile_id = request.form.get('driver_profile_id')
    action = request.form.get('action')

    if not driver_profile_id or action not in ('check_in', 'check_out'):
        flash('Invalid attendance request.', 'danger')
        return redirect(url_for('attendance.live'))

    driver_profile = DriverProfile.query.get(driver_profile_id)
    if not driver_profile:
        abort(404)

    if driver_profile.user_id != current_user.id and not has_permission('attendance.override'):
        abort(403)

    # Decode and save selfie & dashboard image verification if provided
    selfie_data = request.form.get('selfie_data')
    dashboard_data = request.form.get('dashboard_data')
    
    selfie_file = request.files.get('selfie_file')
    dashboard_file = request.files.get('dashboard_file')

    # Helper role validation
    from app.domain.auth.policies.auth_policy import has_role
    is_helper_user = has_role(driver_profile.user, 'Helper') if (driver_profile and driver_profile.user) else False
    if is_helper_user:
        # Enforce selfie is provided
        has_selfie = (selfie_data and selfie_data.strip()) or (selfie_file and selfie_file.filename)
        if not has_selfie:
            flash('Verification failed: A selfie is required to mark attendance.', 'danger')
            return redirect(url_for('attendance.live'))
        # Overwrite/ignore dashboard and odometer values for helper
        dashboard_data = None
        dashboard_file = None
        request.form = request.form.copy()
        if 'odometer' in request.form:
            del request.form['odometer']

    try:
        if selfie_data and selfie_data.strip():
            selfie_file = decode_base64_image(selfie_data, 'selfie.jpg')
        if dashboard_data and dashboard_data.strip():
            dashboard_file = decode_base64_image(dashboard_data, 'dashboard.jpg')
            
        if selfie_file and selfie_file.filename:
            validate_verification_image(selfie_file)
        if dashboard_file and dashboard_file.filename:
            validate_verification_image(dashboard_file)
    except ValueError as exc:
        flash(f"Verification failed: {str(exc)}", 'danger')
        return redirect(url_for('attendance.live'))

    upload_folder = current_app.config['DRIVER_DOCUMENT_UPLOAD_FOLDER']
    selfie_path = None
    dashboard_path = None

    try:
        if selfie_file and selfie_file.filename:
            selfie_path = save_verification_image(selfie_file, upload_folder, driver_profile.id)
        if dashboard_file and dashboard_file.filename:
            dashboard_path = save_verification_image(dashboard_file, upload_folder, driver_profile.id)
    except Exception as exc:
        flash(f"Failed to save verification images: {str(exc)}", 'danger')
        return redirect(url_for('attendance.live'))

    odometer_val = request.form.get('odometer')
    odometer = None
    if odometer_val and odometer_val.strip():
        try:
            odometer = float(odometer_val)
        except ValueError:
            pass

    location_payload = {
        'latitude': request.form.get('latitude'),
        'longitude': request.form.get('longitude'),
        'accuracy': request.form.get('accuracy'),
    }

    attendance, error = attendance_service.mark_attendance(
        driver_profile_id,
        action,
        location_payload=location_payload,
        actor_id=current_user.id,
        selfie_path=selfie_path,
        dashboard_path=dashboard_path,
        odometer=odometer
    )
    if error:
        flash(error, 'warning')
    else:
        flash('Attendance updated successfully.', 'success')

    return redirect(url_for('attendance.live'))


@attendance_bp.route('/verification-image/<attendance_id>/<image_type>')
@login_required
def view_verification_image(attendance_id, image_type):
    from app.domain.auth.policies.auth_policy import has_role
    
    attendance = DriverAttendance.query.get_or_404(attendance_id)
    profile = attendance.driver
    if not profile:
        abort(404)
        
    # RBAC logic
    # DRIVER: Can view own captures.
    # KAM-CIRCLE, KAM-CORPORATE, SUPERADMIN, ADMIN: Can view any.
    is_driver = has_role('Driver') and not has_role('Super Admin') and not has_role('Admin')
    if is_driver:
        if profile.user_id != current_user.id:
            abort(403)
            
    if image_type == 'selfie':
        path = attendance.selfie_storage_path
    elif image_type == 'dashboard':
        path = attendance.dashboard_storage_path
    else:
        abort(404)
        
    if not path:
        abort(404)
        
    return send_from_directory(
        current_app.config['DRIVER_DOCUMENT_UPLOAD_FOLDER'],
        path,
        as_attachment=False
    )
