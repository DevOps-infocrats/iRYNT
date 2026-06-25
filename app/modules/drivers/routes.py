from flask import Blueprint, abort, current_app, flash, jsonify, redirect, render_template, request, send_from_directory, url_for
from flask_login import current_user, login_required
from sqlalchemy.exc import IntegrityError

from app.domain.auth.policies.auth_policy import has_permission
from app.modules.drivers.forms import DriverCreateForm, DriverEditForm
from app.modules.drivers.models import DriverDocument, DriverLicense, DriverProfile
from app.modules.drivers.services import DriverService
from app.modules.drivers.utils import save_driver_document_file, validate_driver_document_file
from app.services.compliance.document_compliance import build_driver_compliance
from app.extensions import db
from app.modules.auth.models import User, Role
from app.modules.circles.models import Circle
from app.modules.projects.models import Project
from app.modules.subzones.models import Subzone
from app.modules.users.services import UserService
from app.modules.roles.services.role_template_service import RoleTemplateService
import uuid
import os


drivers_bp = Blueprint('drivers', __name__, url_prefix='/drivers')
service = DriverService()


@drivers_bp.route('/')
@login_required
def index():
    from app.domain.auth.policies.auth_policy import has_role

    if has_role('Helper') and not has_role('Super Admin') and not has_role('Admin'):
        abort(403)
    if not has_permission('driver_profiles.view'):
        abort(403)

    page = request.args.get('page', 1, type=int)
    per_page = 20
    filters = {
        'company_id': request.args.get('company_id') or None,
        'circle_id': request.args.get('circle_id') or None,
        'status': request.args.get('status') or None,
        'search_query': request.args.get('q', '').strip() or None,
    }

    if not current_user.is_superadmin:
        if current_user.circle_id:
            filters['circle_id'] = current_user.circle_id
        elif current_user.company_id:
            filters['company_id'] = current_user.company_id

    drivers, total = service.list_drivers(filters, page, per_page)
    payload = service.get_filter_payload(filters)

    return render_template(
        'drivers/list.html',
        drivers=drivers,
        total=total,
        page=page,
        per_page=per_page,
        companies=payload['companies'],
        circles=payload['circles'],
        status_options=payload['status_options'],
        filters=filters,
        active_page='driver_profiles',
    )


@drivers_bp.route('/<driver_id>')
@login_required
def profile(driver_id):
    from app.domain.auth.policies.auth_policy import has_role

    if has_role('Helper') and not has_role('Super Admin') and not has_role('Admin'):
        current_driver_profile = DriverProfile.query.filter_by(user_id=current_user.id).first()
        if not current_driver_profile or str(current_driver_profile.id) != str(driver_id):
            abort(403)

    if not has_permission('driver_profiles.view'):
        abort(403)

    profile_data = service.get_driver_profile(driver_id)
    if not profile_data:
        flash('Driver profile not found.', 'danger')
        return redirect(url_for('drivers.index'))

    can_mark_attendance = (
        has_permission('attendance.mark') or current_user.id == profile_data['user'].id
    )
    driver_compliance = build_driver_compliance(
        profile_data.get('driver_profile'),
        profile_data.get('documents'),
        profile_data.get('latest_license'),
    )

    return render_template(
        'drivers/profile.html',
        profile=profile_data,
        driver_compliance=driver_compliance,
        active_page='driver_profiles',
        can_edit=has_permission('driver_profiles.manage') and bool(profile_data.get('driver_profile')),
        can_view_payroll=has_permission('payroll.view'),
        can_mark_attendance=can_mark_attendance,
    )


@drivers_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    if not has_permission('driver_profiles.manage'):
        abort(403)

    form = DriverCreateForm()
    form.company_id.choices = service.get_company_choices(include_all=False)
    form.circle_id.choices = [('', 'Select circle')]
    form.client_id.choices = [('', 'Select client')]
    form.project_id.choices = [('', 'Select project')]
    form.subzone_id.choices = [('', 'Select subzone')]

    if request.method == 'POST':
        company_id = form.company_id.data or request.form.get('company_id') or getattr(current_user, 'company_id', None)
        circle_id = form.circle_id.data or request.form.get('circle_id') or getattr(current_user, 'circle_id', None)
        client_id = form.client_id.data or request.form.get('client_id')
        project_id = form.project_id.data or request.form.get('project_id')

        form.circle_id.choices = service.get_circle_choices(company_id, include_all=False)
        form.client_id.choices = service.get_client_choices(circle_id, include_all=False)
        form.project_id.choices = service.get_project_choices(client_id, include_all=False)
        form.subzone_id.choices = service.get_subzone_choices(project_id, include_all=False)
    else:
        company_id = getattr(current_user, 'company_id', None)
        circle_id = getattr(current_user, 'circle_id', None)
        client_id = getattr(current_user, 'client_id', None)
        project_id = getattr(current_user, 'project_id', None)

        if company_id:
            form.company_id.data = company_id
            form.circle_id.choices = service.get_circle_choices(company_id, include_all=False)
        if circle_id:
            form.circle_id.data = circle_id
            form.client_id.choices = service.get_client_choices(circle_id, include_all=False)
        if client_id:
            form.client_id.data = client_id
            form.project_id.choices = service.get_project_choices(client_id, include_all=False)
        if project_id:
            form.project_id.data = project_id
            form.subzone_id.choices = service.get_subzone_choices(project_id, include_all=False)

    if form.validate_on_submit():
        identifier = form.identifier.data.strip()
        phone = form.phone.data.strip() if form.phone.data else None
        user = service.find_user_by_identifier(identifier)
        new_user_created = False

        if not user:
            # Auto-create a User record when identifier is not found
            user_service = UserService()
            if '@' in identifier:
                username = identifier.split('@')[0].strip() or identifier
                email = identifier
            else:
                username = identifier.strip()
                email = f"{username}@gmail.com"

            # Ensure unique username
            base_username = username
            while User.query.filter_by(username=username).first():
                username = f"{base_username}_{uuid.uuid4().hex[:6]}"

            if User.query.filter_by(email=email).first():
                form.identifier.errors.append('A user with this email already exists. Use that user email as the identifier.')
                return render_template('drivers/create.html', form=form, active_page='driver_profiles')

            if phone and User.query.filter_by(phone=phone).first():
                form.phone.errors.append('A user with this phone number already exists. Use that user as the identifier or enter a different phone number.')
                return render_template('drivers/create.html', form=form, active_page='driver_profiles')

            # Try to find the Driver role to assign
            driver_role = Role.query.filter_by(name='Driver').first()
            if not driver_role:
                driver_role = RoleTemplateService.create_role_from_template('driver')
            role_id = driver_role.id if driver_role else None

            new_user_payload = {
                'username': username,
                'email': email,
                'password': f"{username}@123",
                'phone': phone,
                'company_id': company_id,
                'circle_id': circle_id,
                'is_active': True,
                'is_verified': True,
                'role_id': role_id,
            }
            try:
                user = user_service.create_user(new_user_payload)
                new_user_created = True
                flash(f'User {user.username} created automatically with generated credentials.', 'info')
            except IntegrityError:
                db.session.rollback()
                form.identifier.errors.append('Automatic user creation failed because the username, email, or phone number already exists.')
                return render_template('drivers/create.html', form=form, active_page='driver_profiles')
            except Exception:
                db.session.rollback()
                form.identifier.errors.append('User not found and automatic creation failed. Create the user first or provide a valid identifier.')
                return render_template('drivers/create.html', form=form, active_page='driver_profiles')

        # Since user is now found/created, validate the rest of the fields
        has_validation_errors = False

        if phone and not user.phone:
            if User.query.filter(User.phone == phone, User.id != user.id).first():
                form.phone.errors.append('A user with this phone number already exists.')
                has_validation_errors = True
            else:
                user.phone = phone
                try:
                    db.session.commit()
                except IntegrityError:
                    db.session.rollback()
                    form.phone.errors.append('A user with this phone number already exists.')
                    has_validation_errors = True

        if getattr(user, 'driver_profile', None):
            flash('This user already has a driver profile.', 'info')
            if new_user_created and user:
                try:
                    db.session.delete(user)
                    db.session.commit()
                except Exception:
                    db.session.rollback()
            return redirect(url_for('drivers.profile', driver_id=user.id))

        if form.driver_code.data and service.driver_code_exists(form.driver_code.data):
            form.driver_code.errors.append('Driver code already exists.')
            has_validation_errors = True

        if form.license_number.data and service.license_number_exists(form.license_number.data):
            form.license_number.errors.append('This license number is already registered.')
            has_validation_errors = True

        if form.issue_date.data and form.expiry_date.data and form.issue_date.data > form.expiry_date.data:
            form.expiry_date.errors.append('Expiry date must be the same or after issue date.')
            has_validation_errors = True

        if form.dob.data and form.join_date.data and form.dob.data >= form.join_date.data:
            form.join_date.errors.append('Join date must be after date of birth.')
            has_validation_errors = True

        # Validate Driving License, Aadhaar, PAN
        document_file = form.document_file.data
        document_type = form.document_type.data
        
        for field_name, name in [
            ('driving_license_file', 'Driving License'),
            ('aadhaar_file', 'Aadhaar'),
            ('pan_file', 'PAN')
        ]:
            file_field = getattr(form, field_name).data
            if file_field and file_field.filename:
                try:
                    validate_driver_document_file(file_field)
                except ValueError as exc:
                    getattr(form, field_name).errors.append(str(exc))
                    has_validation_errors = True
        
        if document_file and document_file.filename:
            try:
                validate_driver_document_file(document_file)
            except ValueError as exc:
                form.document_file.errors.append(str(exc))
                has_validation_errors = True

        if has_validation_errors or form.errors:
            if new_user_created and user:
                try:
                    db.session.delete(user)
                    db.session.commit()
                except Exception:
                    db.session.rollback()
            return render_template('drivers/create.html', form=form, active_page='driver_profiles')

        # Document storage and database entries in safe transaction
        upload_folder = current_app.config['DRIVER_DOCUMENT_UPLOAD_FOLDER']
        saved_files = []
        uploaded_documents = []
        new_profile = None
        try:
            new_profile = service.create_driver_profile(
                {
                    'user_id': user.id,
                    'driver_code': form.driver_code.data.strip() if form.driver_code.data else None,
                    'circle_id': form.circle_id.data,
                    'client_id': form.client_id.data,
                    'project_id': form.project_id.data,
                    'subzone_id': form.subzone_id.data,
                    'dob': form.dob.data,
                    'gender': form.gender.data,
                    'blood_group': form.blood_group.data,
                    'nationality': form.nationality.data,
                    'address': form.address.data,
                    'emergency_contact_name': form.emergency_contact_name.data,
                    'emergency_contact_phone': form.emergency_contact_phone.data,
                    'experience_years': form.experience_years.data,
                    'join_date': form.join_date.data,
                    'license_number': form.license_number.data.strip() if form.license_number.data else None,
                    'vehicle_classes': form.vehicle_classes.data,
                    'issue_date': form.issue_date.data,
                    'expiry_date': form.expiry_date.data,
                }
            )

            for field_name, doc_type in [
                ('driving_license_file', 'Driving License'),
                ('aadhaar_file', 'Aadhaar'),
                ('pan_file', 'PAN')
            ]:
                file_field = getattr(form, field_name).data
                if file_field and file_field.filename:
                    storage_name = save_driver_document_file(file_field, upload_folder, new_profile.id)
                    saved_files.append(os.path.join(upload_folder, storage_name))
                    
                    document = DriverDocument(
                        driver_id=new_profile.id,
                        document_type=doc_type,
                        file_name=file_field.filename,
                        storage_path=storage_name,
                        uploaded_by=current_user.id,
                        expiry_date=form.expiry_date.data if doc_type == 'Driving License' else None,
                        status='Pending Verification',
                    )
                    db.session.add(document)
                    uploaded_documents.append(document)

            if document_file and document_file.filename:
                storage_name = save_driver_document_file(document_file, upload_folder, new_profile.id)
                saved_files.append(os.path.join(upload_folder, storage_name))
                
                document = DriverDocument(
                    driver_id=new_profile.id,
                    document_type=document_type,
                    file_name=document_file.filename,
                    storage_path=storage_name,
                    uploaded_by=current_user.id,
                    expiry_date=form.expiry_date.data,
                    status='Pending Verification',
                )
                db.session.add(document)
                uploaded_documents.append(document)

            db.session.commit()

            # Add timeline / activity logs
            from app.modules.drivers.models import DriverActivityLog
            for doc in uploaded_documents:
                db.session.add(DriverActivityLog(
                    driver_id=new_profile.id,
                    actor_id=current_user.id,
                    event_type='Uploaded',
                    description=f'{doc.document_type} uploaded during driver creation.',
                    event_metadata={'document_id': doc.id, 'document_type': doc.document_type},
                ))
            db.session.commit()

        except Exception as exc:
            db.session.rollback()
            
            # Cleanup database records
            if new_profile:
                try:
                    from app.modules.drivers.models import DriverLicense
                    DriverLicense.query.filter_by(driver_id=new_profile.id).delete()
                    db.session.delete(new_profile)
                    db.session.commit()
                except Exception as e:
                    print("--- Error deleting new_profile on error cleanup:", e, flush=True)
                    db.session.rollback()

            # Cleanup physical saved files
            for file_path in saved_files:
                try:
                    if os.path.exists(file_path):
                        os.remove(file_path)
                except Exception:
                    pass

            # If user was newly created, delete user
            if new_user_created and user:
                try:
                    db.session.delete(user)
                    db.session.commit()
                except Exception as e:
                    print("--- Error deleting new user on error cleanup:", e, flush=True)
                    db.session.rollback()

            if isinstance(exc, IntegrityError):
                form.identifier.errors.append('Driver profile creation failed because one of the unique values (like driver code or license number) already exists.')
            else:
                form.errors['document_upload'] = [f"Failed to upload documents: {str(exc)}"]
            return render_template('drivers/create.html', form=form, active_page='driver_profiles')

        flash('Driver profile and onboarding record created successfully.', 'success')
        return redirect(url_for('drivers.profile', driver_id=user.id))

    return render_template('drivers/create.html', form=form, active_page='driver_profiles')


@drivers_bp.route('/<driver_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(driver_id):
    """Edit existing driver profile"""
    if not has_permission('driver_profiles.manage'):
        abort(403)
    profile_data = service.get_driver_profile(driver_id)
    if not profile_data:
        flash('Driver profile not found.', 'danger')
        return redirect(url_for('drivers.index'))

    user = profile_data['user']
    profile = profile_data.get('driver_profile')
    if not profile:
        flash('Driver profile details are missing for this user. Create the driver profile before editing documents or compliance data.', 'warning')
        return redirect(url_for('drivers.index'))

    form = DriverEditForm()
    company_id = None
    if profile and profile.circle:
        company_id = profile.circle.company_id
    
    form.circle_id.choices = service.get_circle_choices(company_id, include_all=False)
    form.client_id.choices = [('', 'Select client')]
    form.project_id.choices = [('', 'Select project')]
    form.subzone_id.choices = [('', 'Select subzone')]

    if request.method == 'POST':
        circle_id = form.circle_id.data or request.form.get('circle_id')
        client_id = form.client_id.data or request.form.get('client_id')
        project_id = form.project_id.data or request.form.get('project_id')

        form.circle_id.choices = service.get_circle_choices(company_id, include_all=False)
        form.client_id.choices = service.get_client_choices(circle_id, include_all=False)
        form.project_id.choices = service.get_project_choices(client_id, include_all=False)
        form.subzone_id.choices = service.get_subzone_choices(project_id, include_all=False)
    else:
        if profile:
            form.driver_code.data = profile.driver_code
            form.circle_id.data = profile.circle_id
            form.client_id.data = profile.client_id
            form.project_id.data = profile.project_id
            form.subzone_id.data = profile.subzone_id
            form.dob.data = profile.dob
            form.gender.data = profile.gender
            form.blood_group.data = profile.blood_group
            form.nationality.data = profile.nationality
            form.address.data = profile.address
            form.emergency_contact_name.data = profile.emergency_contact_name
            form.emergency_contact_phone.data = profile.emergency_contact_phone
            form.experience_years.data = profile.experience_years
            form.join_date.data = profile.join_date
            
            # License data from latest_license
            latest_license = profile_data.get('latest_license')
            if latest_license:
                form.license_number.data = latest_license.license_number
                form.vehicle_classes.data = latest_license.vehicle_classes
                form.issue_date.data = latest_license.issue_date
                form.expiry_date.data = latest_license.expiry_date

            if profile.circle_id:
                form.circle_id.choices = service.get_circle_choices(company_id, include_all=False)
            if profile.client_id:
                form.client_id.choices = service.get_client_choices(profile.circle_id, include_all=False)
            if profile.project_id:
                form.project_id.choices = service.get_project_choices(profile.client_id, include_all=False)
            if profile.subzone_id:
                form.subzone_id.choices = service.get_subzone_choices(profile.project_id, include_all=False)

    if form.validate_on_submit():
        latest_license = profile_data.get('latest_license')
        
        # Validate license number if changed
        if form.license_number.data and latest_license and form.license_number.data != latest_license.license_number:
            if service.license_number_exists(form.license_number.data):
                form.license_number.errors.append('This license number is already registered.')
                return render_template('drivers/edit.html', form=form, profile_data=profile_data, user=user, active_page='driver_profiles')

        # Validate date range
        if form.issue_date.data and form.expiry_date.data and form.issue_date.data > form.expiry_date.data:
            form.expiry_date.errors.append('Expiry date must be the same or after issue date.')
            return render_template('drivers/edit.html', form=form, profile_data=profile_data, user=user, active_page='driver_profiles')

        # Update profile fields
        profile.driver_code = form.driver_code.data.strip() if form.driver_code.data else None
        profile.circle_id = form.circle_id.data or None
        profile.client_id = form.client_id.data or None
        profile.project_id = form.project_id.data or None
        profile.subzone_id = form.subzone_id.data or None
        profile.dob = form.dob.data
        profile.gender = form.gender.data or None
        profile.blood_group = form.blood_group.data or None
        profile.nationality = form.nationality.data or None
        profile.address = form.address.data or None
        profile.emergency_contact_name = form.emergency_contact_name.data or None
        profile.emergency_contact_phone = form.emergency_contact_phone.data or None
        profile.experience_years = form.experience_years.data
        profile.join_date = form.join_date.data
        
        db.session.commit()
        
        # Update or create license record
        if form.license_number.data:
            license_record = latest_license or DriverLicense(driver_id=profile.id)
            license_record.license_number = form.license_number.data.strip()
            license_record.vehicle_classes = form.vehicle_classes.data or None
            license_record.issue_date = form.issue_date.data
            license_record.expiry_date = form.expiry_date.data
            
            if not latest_license:
                db.session.add(license_record)
            db.session.commit()

        # Handle document upload if provided
        document_file = form.document_file.data
        document_type = form.document_type.data
        if document_file and document_file.filename:
            upload_folder = current_app.config['DRIVER_DOCUMENT_UPLOAD_FOLDER']
            try:
                storage_name = save_driver_document_file(document_file, upload_folder, profile.id)
            except ValueError as exc:
                db.session.rollback()
                form.document_file.errors.append(str(exc))
                return render_template('drivers/edit.html', form=form, profile_data=profile_data, user=user, active_page='driver_profiles')
            document = DriverDocument(
                driver_id=profile.id,
                document_type=document_type,
                file_name=document_file.filename,
                storage_path=storage_name,
                uploaded_by=current_user.id,
                expiry_date=form.expiry_date.data,
            )
            db.session.add(document)
            db.session.commit()

        flash('Driver profile updated successfully.', 'success')
        return redirect(url_for('drivers.profile', driver_id=driver_id))

    return render_template('drivers/edit.html', form=form, profile_data=profile_data, user=user, active_page='driver_profiles')


@drivers_bp.route('/<driver_id>/documents/<document_id>/download')
@login_required
def download_document(driver_id, document_id):
    if not has_permission('driver_profiles.view'):
        abort(403)

    document = DriverDocument.query.filter_by(id=document_id, driver_id=driver_id).first()
    if not document:
        abort(404)

    return send_from_directory(
        current_app.config['DRIVER_DOCUMENT_UPLOAD_FOLDER'],
        document.storage_path,
        as_attachment=True,
        download_name=document.file_name,
    )


@drivers_bp.route('/<driver_id>/license/verify', methods=['POST'])
@login_required
def verify_license(driver_id):
    # License verification endpoint removed — verification functionality deprecated.
    # Keep route to avoid 404s but return a no-op response to preserve compatibility.
    return jsonify({'success': False, 'message': 'License verification is disabled'}), 410
