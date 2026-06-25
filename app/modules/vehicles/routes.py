from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.modules.vehicles.forms import VehicleForm
from app.modules.vehicles.services import VehicleService
from app.modules.companies.models import Company
from app.modules.circles.models import Circle
from app.modules.clients.models import Client
from app.modules.projects.models import Project
from app.modules.subzones.models import Subzone
from app.modules.vehicles.services.excel_parser_service import VehicleExcelParserService
from app.modules.vehicles.services.validation_service import VehicleValidationService
from app.modules.vehicles.services.bulk_import_service import VehicleBulkImportService
import io
from flask import send_file, session

vehicles_bp = Blueprint('vehicles', __name__, url_prefix='/vehicles')
vehicle_service = VehicleService()


def get_company_choices():
    query = Company.query.filter_by(status='Active')
    if not current_user.is_superadmin:
        if current_user.company_id:
            query = query.filter_by(id=current_user.company_id)
    companies = query.order_by(Company.company_name).all()
    return [('', 'Select company')] + [(c.id, f"{c.company_name} ({c.company_code})") for c in companies]


def get_circle_choices(company_id):
    if not company_id:
        return [('', 'Select circle')]
    query = Circle.query.filter_by(company_id=company_id, status='Active')
    if not current_user.is_superadmin:
        if current_user.circle_id:
            query = query.filter_by(id=current_user.circle_id)
    circles = query.order_by(Circle.circle_name).all()
    return [('', 'Select circle')] + [(c.id, f"{c.circle_name} ({c.circle_code})") for c in circles]


def get_client_choices(circle_id):
    if not circle_id:
        return [('', 'Select client')]
    clients = Client.query.filter_by(circle_id=circle_id, status='Active').order_by(Client.client_name).all()
    return [('', 'Select client')] + [(c.id, f"{c.client_name} ({c.client_code})") for c in clients]


def get_project_choices(client_id):
    if not client_id:
        return [('', 'Select project')]
    projects = Project.query.filter_by(client_id=client_id, status='Active').order_by(Project.project_name).all()
    return [('', 'Select project')] + [(p.id, f"{p.project_name} ({p.project_code})") for p in projects]


def get_subzone_choices(project_id):
    if not project_id:
        return [('', 'Select subzone')]
    subzones = Subzone.query.filter_by(project_id=project_id, status='Active').order_by(Subzone.subzone_name).all()
    return [('', 'Select subzone')] + [(s.id, f"{s.subzone_name} ({s.subzone_code})") for s in subzones]


@vehicles_bp.route('/')
@login_required
def index():
    page = request.args.get('page', 1, type=int)
    per_page = 20
    company_id = None
    circle_id = None
    if not current_user.is_superadmin:
        if current_user.circle_id:
            circle_id = current_user.circle_id
        elif current_user.company_id:
            company_id = current_user.company_id

    vehicles = vehicle_service.list_vehicles(
        company_id=company_id,
        circle_id=circle_id,
        limit=per_page,
        offset=(page - 1) * per_page,
    )
    return render_template('vehicles/list.html', vehicles=vehicles, active_page='vehicle_master')


@vehicles_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    form = VehicleForm()
    form.company_id.choices = get_company_choices()

    if request.method == 'POST':
        form.circle_id.choices = get_circle_choices(form.company_id.data)
        form.client_id.choices = get_client_choices(form.circle_id.data)
        form.project_id.choices = get_project_choices(form.client_id.data)
        form.subzone_id.choices = get_subzone_choices(form.project_id.data)

        if form.validate_on_submit():
            if vehicle_service.exists_by_vehicle_number(
                form.company_id.data,
                form.circle_id.data,
                form.client_id.data,
                form.project_id.data,
                form.subzone_id.data,
                form.vehicle_number.data,
            ):
                form.vehicle_number.errors.append('A vehicle with this number already exists in the selected subzone.')
            else:
                payload = {
                    'company_id': form.company_id.data,
                    'circle_id': form.circle_id.data,
                    'client_id': form.client_id.data,
                    'project_id': form.project_id.data,
                    'subzone_id': form.subzone_id.data,
                    'vehicle_number': form.vehicle_number.data,
                    'vehicle_type': form.vehicle_type.data,
                    'vehicle_category': form.vehicle_category.data,
                    'vehicle_brand': form.vehicle_brand.data,
                    'vehicle_model': form.vehicle_model.data,
                    'manufacturing_year': form.manufacturing_year.data,
                    'chassis_number': form.chassis_number.data,
                    'engine_number': form.engine_number.data,
                    'owner_name': form.owner_name.data,
                    'owner_phone': form.owner_phone.data,
                    'vendor_name': form.vendor_name.data,
                    'vendor_contact': form.vendor_contact.data,
                    'gps_enabled': form.gps_enabled.data,
                    'realtime_tracking_enabled': form.realtime_tracking_enabled.data,
                    'deployment_allowed': form.deployment_allowed.data,
                    'attendance_linked': form.attendance_linked.data,
                    'fuel_tracking_enabled': form.fuel_tracking_enabled.data,
                    'geo_fencing_enabled': form.geo_fencing_enabled.data,
                    'incident_monitoring_enabled': form.incident_monitoring_enabled.data,
                    'maintenance_tracking_enabled': form.maintenance_tracking_enabled.data,
                    'load_capacity': form.load_capacity.data,
                    'passenger_capacity': form.passenger_capacity.data,
                    'fuel_capacity': form.fuel_capacity.data,
                    'operational_capacity': form.operational_capacity.data,
                    'status': form.status.data,
                    'insurance_status': form.insurance_status.data,
                    'fitness_status': form.fitness_status.data,
                    'permit_status': form.permit_status.data,
                    'puc_status': form.puc_status.data,
                    'verification_status': form.verification_status.data,
                    'assigned_driver': form.assigned_driver.data,
                    'current_deployment': form.current_deployment.data,
                }
                vehicle = vehicle_service.create_vehicle(payload, current_user.get_id())
                flash('Vehicle created successfully.', 'success')
                return redirect(url_for('vehicles.details', vehicle_id=vehicle.id))

    return render_template('vehicles/create.html', form=form, active_page='vehicle_master')


@vehicles_bp.route('/<vehicle_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(vehicle_id):
    vehicle = vehicle_service.get_vehicle(vehicle_id)
    if not vehicle:
        flash('Vehicle not found.', 'danger')
        return redirect(url_for('vehicles.index'))

    form = VehicleForm(obj=vehicle)
    form.company_id.choices = get_company_choices()
    form.circle_id.choices = get_circle_choices(vehicle.company_id)
    form.client_id.choices = get_client_choices(vehicle.circle_id)
    form.project_id.choices = get_project_choices(vehicle.client_id)
    form.subzone_id.choices = get_subzone_choices(vehicle.project_id)

    if request.method == 'POST':
        form.circle_id.choices = get_circle_choices(form.company_id.data)
        form.client_id.choices = get_client_choices(form.circle_id.data)
        form.project_id.choices = get_project_choices(form.client_id.data)
        form.subzone_id.choices = get_subzone_choices(form.project_id.data)

        if form.validate_on_submit():
            if vehicle_service.exists_by_vehicle_number(
                form.company_id.data,
                form.circle_id.data,
                form.client_id.data,
                form.project_id.data,
                form.subzone_id.data,
                form.vehicle_number.data,
                exclude_id=vehicle.id,
            ):
                form.vehicle_number.errors.append('A vehicle with this number already exists in the selected subzone.')
            else:
                payload = {
                    'company_id': form.company_id.data,
                    'circle_id': form.circle_id.data,
                    'client_id': form.client_id.data,
                    'project_id': form.project_id.data,
                    'subzone_id': form.subzone_id.data,
                    'vehicle_number': form.vehicle_number.data,
                    'vehicle_type': form.vehicle_type.data,
                    'vehicle_category': form.vehicle_category.data,
                    'vehicle_brand': form.vehicle_brand.data,
                    'vehicle_model': form.vehicle_model.data,
                    'manufacturing_year': form.manufacturing_year.data,
                    'chassis_number': form.chassis_number.data,
                    'engine_number': form.engine_number.data,
                    'owner_name': form.owner_name.data,
                    'owner_phone': form.owner_phone.data,
                    'vendor_name': form.vendor_name.data,
                    'vendor_contact': form.vendor_contact.data,
                    'gps_enabled': form.gps_enabled.data,
                    'realtime_tracking_enabled': form.realtime_tracking_enabled.data,
                    'deployment_allowed': form.deployment_allowed.data,
                    'attendance_linked': form.attendance_linked.data,
                    'fuel_tracking_enabled': form.fuel_tracking_enabled.data,
                    'geo_fencing_enabled': form.geo_fencing_enabled.data,
                    'incident_monitoring_enabled': form.incident_monitoring_enabled.data,
                    'maintenance_tracking_enabled': form.maintenance_tracking_enabled.data,
                    'load_capacity': form.load_capacity.data,
                    'passenger_capacity': form.passenger_capacity.data,
                    'fuel_capacity': form.fuel_capacity.data,
                    'operational_capacity': form.operational_capacity.data,
                    'status': form.status.data,
                    'insurance_status': form.insurance_status.data,
                    'fitness_status': form.fitness_status.data,
                    'permit_status': form.permit_status.data,
                    'puc_status': form.puc_status.data,
                    'verification_status': form.verification_status.data,
                    'assigned_driver': form.assigned_driver.data,
                    'current_deployment': form.current_deployment.data,
                }
                vehicle_service.update_vehicle(vehicle.id, payload)
                flash('Vehicle updated successfully.', 'success')
                return redirect(url_for('vehicles.details', vehicle_id=vehicle.id))

    return render_template('vehicles/edit.html', form=form, vehicle=vehicle, active_page='vehicle_master')


@vehicles_bp.route('/<vehicle_id>')
@login_required
def details(vehicle_id):
    vehicle = vehicle_service.get_vehicle(vehicle_id)
    if not vehicle:
        flash('Vehicle not found.', 'danger')
        return redirect(url_for('vehicles.index'))

    summary = vehicle_service.get_vehicle_summary(vehicle)
    return render_template('vehicles/details.html', vehicle=vehicle, summary=summary, active_page='vehicle_master')


@vehicles_bp.route('/ajax/circles')
@login_required
def ajax_circles():
    company_id = request.args.get('company_id')
    circles = Circle.query.filter_by(company_id=company_id, status='Active').order_by(Circle.circle_name).all() if company_id else []
    return jsonify([
        {'id': circle.id, 'text': f"{circle.circle_name} ({circle.circle_code})"}
        for circle in circles
    ])


@vehicles_bp.route('/ajax/clients')
@login_required
def ajax_clients():
    circle_id = request.args.get('circle_id')
    clients = Client.query.filter_by(circle_id=circle_id, status='Active').order_by(Client.client_name).all() if circle_id else []
    return jsonify([
        {'id': client.id, 'text': f"{client.client_name} ({client.client_code})"}
        for client in clients
    ])


@vehicles_bp.route('/ajax/projects')
@login_required
def ajax_projects():
    client_id = request.args.get('client_id')
    projects = Project.query.filter_by(client_id=client_id, status='Active').order_by(Project.project_name).all() if client_id else []
    return jsonify([
        {'id': project.id, 'text': f"{project.project_name} ({project.project_code})"}
        for project in projects
    ])


@vehicles_bp.route('/ajax/subzones')
@login_required
def ajax_subzones():
    project_id = request.args.get('project_id')
    subzones = Subzone.query.filter_by(project_id=project_id, status='Active').order_by(Subzone.subzone_name).all() if project_id else []
    return jsonify([
        {'id': subzone.id, 'text': f"{subzone.subzone_name} ({subzone.subzone_code})"}
        for subzone in subzones
    ])


@vehicles_bp.route('/ajax/check-number')
@login_required
def ajax_check_number():
    company_id = request.args.get('company_id')
    circle_id = request.args.get('circle_id')
    client_id = request.args.get('client_id')
    project_id = request.args.get('project_id')
    subzone_id = request.args.get('subzone_id')
    vehicle_number = request.args.get('vehicle_number', '').strip().upper()
    exclude_id = request.args.get('exclude_id')
    exists = vehicle_service.exists_by_vehicle_number(
        company_id,
        circle_id,
        client_id,
        project_id,
        subzone_id,
        vehicle_number,
        exclude_id=exclude_id,
    )
    return jsonify({'exists': exists})


def _has_bulk_import_permission():
    allowed_roles = {'Super Admin', 'Corporate Admin', 'Circle Admin'}
    user_roles = [r.name for r in getattr(current_user, 'roles', [])]
    if hasattr(current_user, 'primary_role') and current_user.primary_role:
        user_roles.append(current_user.primary_role.name)
    return any(role in allowed_roles for role in user_roles)

@vehicles_bp.route('/bulk-import', methods=['GET'])
@login_required
def bulk_import_page():
    if not _has_bulk_import_permission():
        return jsonify({'error': 'Forbidden'}), 403
    return render_template('vehicles/bulk_import.html')

@vehicles_bp.route('/bulk-import/template', methods=['GET'])
@login_required
def download_template():
    if not _has_bulk_import_permission():
        return jsonify({'error': 'Forbidden'}), 403
    parser = VehicleExcelParserService()
    wb_bytes = parser.generate_template()
    return send_file(
        io.BytesIO(wb_bytes),
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name='VIL_Vehicle_Import_Template.xlsx'
    )

@vehicles_bp.route('/bulk-import/validate', methods=['POST'])
@login_required
def validate_upload():
    if not _has_bulk_import_permission():
        return jsonify({'error': 'Forbidden'}), 403
    uploaded_file = request.files.get('file')
    if not uploaded_file:
        return jsonify({'error': 'No file provided'}), 400
    parser = VehicleExcelParserService()
    rows = parser.parse_excel(uploaded_file)
    validator = VehicleValidationService()
    summary, errors = validator.validate(rows)
    session['vehicle_import_data'] = {'rows': rows, 'errors': errors}
    return jsonify({'summary': summary, 'errors': errors, 'rows': rows})

@vehicles_bp.route('/bulk-import/import', methods=['POST'])
@login_required
def import_vehicles():
    if not _has_bulk_import_permission():
        return jsonify({'error': 'Forbidden'}), 403
    data = session.get('vehicle_import_data')
    if not data:
        return jsonify({'error': 'No validation data found'}), 400
    rows = data.get('rows', [])
    errors = data.get('errors', [])
    error_row_indices = {e['row_number'] - 2 for e in errors}
    valid_rows = [row for idx, row in enumerate(rows) if idx not in error_row_indices]
    import_service = VehicleBulkImportService()
    import_result = import_service.import_rows(valid_rows, current_user.id)
    session.pop('vehicle_import_data', None)
    return jsonify(import_result)

@vehicles_bp.route('/bulk-import/error-report', methods=['GET'])
@login_required
def download_error_report():
    if not _has_bulk_import_permission():
        return jsonify({'error': 'Forbidden'}), 403
    data = session.get('vehicle_import_data', {})
    errors = data.get('errors', [])
    if not errors:
        return jsonify({'error': 'No errors to report'}), 400
    parser = VehicleExcelParserService()
    wb_bytes = parser.generate_error_report(errors)
    return send_file(
        io.BytesIO(wb_bytes),
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name='Vehicle_Bulk_Import_Error_Report.xlsx'
    )

