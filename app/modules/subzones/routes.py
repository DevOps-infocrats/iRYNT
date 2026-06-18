from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.modules.subzones.forms import SubzoneForm
from app.modules.subzones.services import SubzoneService
from app.modules.companies.models import Company
from app.modules.circles.models import Circle
from app.modules.clients.models import Client
from app.modules.projects.models import Project

subzones_bp = Blueprint('subzones', __name__, url_prefix='/subzones')
subzone_service = SubzoneService()


def get_company_choices():
    companies = Company.query.filter_by(status='Active').order_by(Company.company_name).all()
    return [('', 'Select company')] + [(c.id, f"{c.company_name} ({c.company_code})") for c in companies]


def get_circle_choices(company_id):
    if not company_id:
        return [('', 'Select circle')]
    circles = Circle.query.filter_by(company_id=company_id, status='Active').order_by(Circle.circle_name).all()
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


@subzones_bp.route('/')
@login_required
def index():
    subzones = subzone_service.list_subzones()
    return render_template('subzones/list.html', subzones=subzones, active_page='subzones')


@subzones_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    form = SubzoneForm()
    form.company_id.choices = get_company_choices()

    if request.method == 'POST':
        form.circle_id.choices = get_circle_choices(form.company_id.data)
        form.client_id.choices = get_client_choices(form.circle_id.data)
        form.project_id.choices = get_project_choices(form.client_id.data)

        if form.validate_on_submit():
            if subzone_service.exists_by_code(
                form.company_id.data,
                form.circle_id.data,
                form.client_id.data,
                form.project_id.data,
                form.subzone_code.data,
            ):
                form.subzone_code.errors.append('A subzone with this code already exists for the selected project.')
            else:
                payload = {
                    'company_id': form.company_id.data,
                    'circle_id': form.circle_id.data,
                    'client_id': form.client_id.data,
                    'project_id': form.project_id.data,
                    'subzone_code': form.subzone_code.data,
                    'subzone_name': form.subzone_name.data,
                    'subzone_type': form.subzone_type.data,
                    'status': form.status.data,
                    'country': form.country.data,
                    'state': form.state.data,
                    'city': form.city.data,
                    'pincode': form.pincode.data,
                    'full_address': form.full_address.data,
                    'latitude': form.latitude.data,
                    'longitude': form.longitude.data,
                    'geo_fencing_enabled': form.geo_fencing_enabled.data,
                    'allowed_radius': form.allowed_radius.data,
                    'attendance_radius': form.attendance_radius.data,
                    'gps_validation': form.gps_validation.data,
                    'restricted_movement_detection': form.restricted_movement_detection.data,
                    'max_vehicles': form.max_vehicles.data,
                    'max_drivers': form.max_drivers.data,
                    'shift_operations_enabled': form.shift_operations_enabled.data,
                    'attendance_required': form.attendance_required.data,
                    'deployment_allowed': form.deployment_allowed.data,
                    'realtime_tracking_enabled': form.realtime_tracking_enabled.data,
                    'workflow_approval_enabled': form.workflow_approval_enabled.data,
                    'incident_reporting_enabled': form.incident_reporting_enabled.data,
                    'vehicle_capacity': form.vehicle_capacity.data,
                    'driver_capacity': form.driver_capacity.data,
                    'parking_capacity': form.parking_capacity.data,
                    'operational_capacity': form.operational_capacity.data,
                }
                subzone = subzone_service.create_subzone(payload, current_user.get_id())
                flash('Subzone created successfully.', 'success')
                return redirect(url_for('subzones.details', subzone_id=subzone.id))

    return render_template('subzones/create.html', form=form, active_page='subzones')


@subzones_bp.route('/<subzone_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(subzone_id):
    subzone = subzone_service.get_subzone(subzone_id)
    if not subzone:
        flash('Subzone not found.', 'danger')
        return redirect(url_for('subzones.index'))

    form = SubzoneForm(obj=subzone)
    form.company_id.choices = get_company_choices()
    form.circle_id.choices = get_circle_choices(subzone.company_id)
    form.client_id.choices = get_client_choices(subzone.circle_id)
    form.project_id.choices = get_project_choices(subzone.client_id)

    if request.method == 'POST':
        form.circle_id.choices = get_circle_choices(form.company_id.data)
        form.client_id.choices = get_client_choices(form.circle_id.data)
        form.project_id.choices = get_project_choices(form.client_id.data)

        if form.validate_on_submit():
            duplicate = subzone_service.exists_by_code(
                form.company_id.data,
                form.circle_id.data,
                form.client_id.data,
                form.project_id.data,
                form.subzone_code.data,
            )
            if duplicate and form.subzone_code.data != subzone.subzone_code:
                form.subzone_code.errors.append('A subzone with this code already exists for the selected project.')
            else:
                payload = {
                    'company_id': form.company_id.data,
                    'circle_id': form.circle_id.data,
                    'client_id': form.client_id.data,
                    'project_id': form.project_id.data,
                    'subzone_code': form.subzone_code.data,
                    'subzone_name': form.subzone_name.data,
                    'subzone_type': form.subzone_type.data,
                    'status': form.status.data,
                    'country': form.country.data,
                    'state': form.state.data,
                    'city': form.city.data,
                    'pincode': form.pincode.data,
                    'full_address': form.full_address.data,
                    'latitude': form.latitude.data,
                    'longitude': form.longitude.data,
                    'geo_fencing_enabled': form.geo_fencing_enabled.data,
                    'allowed_radius': form.allowed_radius.data,
                    'attendance_radius': form.attendance_radius.data,
                    'gps_validation': form.gps_validation.data,
                    'restricted_movement_detection': form.restricted_movement_detection.data,
                    'max_vehicles': form.max_vehicles.data,
                    'max_drivers': form.max_drivers.data,
                    'shift_operations_enabled': form.shift_operations_enabled.data,
                    'attendance_required': form.attendance_required.data,
                    'deployment_allowed': form.deployment_allowed.data,
                    'realtime_tracking_enabled': form.realtime_tracking_enabled.data,
                    'workflow_approval_enabled': form.workflow_approval_enabled.data,
                    'incident_reporting_enabled': form.incident_reporting_enabled.data,
                    'vehicle_capacity': form.vehicle_capacity.data,
                    'driver_capacity': form.driver_capacity.data,
                    'parking_capacity': form.parking_capacity.data,
                    'operational_capacity': form.operational_capacity.data,
                }
                subzone_service.update_subzone(subzone.id, payload)
                flash('Subzone updated successfully.', 'success')
                return redirect(url_for('subzones.details', subzone_id=subzone.id))

    return render_template('subzones/edit.html', form=form, subzone=subzone, active_page='subzones')


@subzones_bp.route('/<subzone_id>/details')
@login_required
def details(subzone_id):
    subzone = subzone_service.get_subzone(subzone_id)
    if not subzone:
        flash('Subzone not found.', 'danger')
        return redirect(url_for('subzones.index'))

    summary = subzone_service.get_dashboard_summary(subzone)
    analytics_payload = subzone_service.get_dashboard_data(subzone)
    return render_template(
        'subzones/details.html',
        subzone=subzone,
        summary=summary,
        analytics_payload=analytics_payload,
        active_page='subzones',
    )


@subzones_bp.route('/ajax/companies')
@login_required
def ajax_companies():
    companies = Company.query.filter_by(status='Active').order_by(Company.company_name).all()
    return jsonify([
        {'id': company.id, 'name': company.company_name, 'code': company.company_code}
        for company in companies
    ])


@subzones_bp.route('/ajax/circles')
@login_required
def ajax_circles():
    company_id = request.args.get('company_id')
    circles = Circle.query.filter_by(company_id=company_id, status='Active').order_by(Circle.circle_name).all() if company_id else []
    return jsonify([
        {'id': circle.id, 'name': circle.circle_name, 'code': circle.circle_code}
        for circle in circles
    ])


@subzones_bp.route('/ajax/clients')
@login_required
def ajax_clients():
    circle_id = request.args.get('circle_id')
    clients = Client.query.filter_by(circle_id=circle_id, status='Active').order_by(Client.client_name).all() if circle_id else []
    return jsonify([
        {'id': client.id, 'name': client.client_name, 'code': client.client_code}
        for client in clients
    ])


@subzones_bp.route('/ajax/projects')
@login_required
def ajax_projects():
    client_id = request.args.get('client_id')
    projects = Project.query.filter_by(client_id=client_id, status='Active').order_by(Project.project_name).all() if client_id else []
    return jsonify([
        {'id': project.id, 'name': project.project_name, 'code': project.project_code}
        for project in projects
    ])


@subzones_bp.route('/ajax/check-code')
@login_required
def ajax_check_code():
    company_id = request.args.get('company_id')
    circle_id = request.args.get('circle_id')
    client_id = request.args.get('client_id')
    project_id = request.args.get('project_id')
    subzone_code = request.args.get('subzone_code', '').strip().upper()
    exists = subzone_service.exists_by_code(company_id, circle_id, client_id, project_id, subzone_code)
    return jsonify({'exists': exists})

