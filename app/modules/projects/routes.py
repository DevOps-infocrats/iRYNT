from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user

from app.modules.projects.forms import ProjectForm
from app.modules.projects.services import project_service
from app.modules.companies.models import Company
from app.modules.circles.models import Circle
from app.modules.clients.models import Client

# Create blueprint
projects_bp = Blueprint('projects', __name__, url_prefix='/projects')


@projects_bp.route('/')
@login_required
def index():
    """Projects dashboard"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    projects = project_service.list_projects_by_company(
        current_user.company_id if hasattr(current_user, 'company_id') else None,
        limit=per_page,
        offset=(page - 1) * per_page
    )
    
    return render_template(
        'projects/index.html',
        projects=projects,
        active_page='projects'
    )


@projects_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    """Create new project"""
    form = ProjectForm()
    
    # Load companies for dropdown
    companies = Company.query.filter_by(status='Active').order_by(Company.company_name).all()
    form.company_id.choices = [('', 'Select company')] + [(c.id, f"{c.company_name} ({c.company_code})") for c in companies]
    
    # Populate dependent dropdown choices on POST (before validation) or on GET if company_id/circle_id are preset
    company_id = form.company_id.data or request.form.get('company_id') or request.args.get('company_id')
    circle_id = form.circle_id.data or request.form.get('circle_id') or request.args.get('circle_id')
    
    if company_id:
        circles = Circle.query.filter_by(company_id=company_id, status='Active').order_by(Circle.circle_name).all()
        form.circle_id.choices = [('', 'Select circle')] + [(c.id, f"{c.circle_name} ({c.circle_code})") for c in circles]
    else:
        form.circle_id.choices = [('', 'Select circle')]
        
    if company_id and circle_id:
        clients = Client.query.filter_by(company_id=company_id, circle_id=circle_id, status='Active').order_by(Client.client_name).all()
        form.client_id.choices = [('', 'Select client')] + [(c.id, f"{c.client_name} ({c.client_code})") for c in clients]
    else:
        form.client_id.choices = [('', 'Select client')]
    
    if form.validate_on_submit():
        try:
            data = {
                'company_id': form.company_id.data,
                'circle_id': form.circle_id.data,
                'client_id': form.client_id.data,
                'project_code': form.project_code.data.strip().upper(),
                'project_name': form.project_name.data.strip(),
                'project_type': form.project_type.data,
                'status': form.status.data,
                'start_date': form.start_date.data,
                'end_date': form.end_date.data,
                'expected_completion_date': form.expected_completion_date.data,
                'operational_shift': form.operational_shift.data,
                'country': form.country.data,
                'state': form.state.data,
                'city': form.city.data,
                'pincode': form.pincode.data,
                'full_address': form.full_address.data,
                'deployment_allowed': form.deployment_allowed.data,
                'attendance_required': form.attendance_required.data,
                'gps_tracking_enabled': form.gps_tracking_enabled.data,
                'realtime_monitoring_enabled': form.realtime_monitoring_enabled.data,
                'geo_fencing_enabled': form.geo_fencing_enabled.data,
                'workflow_approval_enabled': form.workflow_approval_enabled.data,
                'document_verification_required': form.document_verification_required.data,
                'shift_based_attendance': form.shift_based_attendance.data,
                'max_vehicles': form.max_vehicles.data,
                'max_drivers': form.max_drivers.data,
                'deployment_capacity': form.deployment_capacity.data,
                'required_vehicle_types': form.required_vehicle_types.data,
                'operational_capacity': form.operational_capacity.data,
                'project_manager': form.project_manager.data,
                'operational_head': form.operational_head.data,
                'contact_number': form.contact_number.data,
                'operational_email': form.operational_email.data,
            }
            
            project = project_service.create_project(data, current_user.id)
            flash('Project created successfully!', 'success')
            return redirect(url_for('projects.details', project_id=project.id))
        except Exception as e:
            flash(f'Error creating project: {str(e)}', 'danger')
    
    return render_template('projects/create.html', form=form, active_page='projects')


@projects_bp.route('/<project_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(project_id):
    """Edit project"""
    project = project_service.get_project(project_id)
    
    if not project:
        flash('Project not found.', 'danger')
        return redirect(url_for('projects.index'))
    
    form = ProjectForm()
    
    # Load companies for dropdown
    companies = Company.query.filter_by(status='Active').order_by(Company.company_name).all()
    form.company_id.choices = [('', 'Select company')] + [(c.id, f"{c.company_name} ({c.company_code})") for c in companies]
    
    # Determine company_id and circle_id for choices population
    if request.method == 'POST':
        company_id = form.company_id.data or request.form.get('company_id')
        circle_id = form.circle_id.data or request.form.get('circle_id')
    else:
        company_id = project.company_id
        circle_id = project.circle_id

    if company_id:
        circles = Circle.query.filter_by(company_id=company_id, status='Active').order_by(Circle.circle_name).all()
        form.circle_id.choices = [('', 'Select circle')] + [(c.id, f"{c.circle_name} ({c.circle_code})") for c in circles]
    else:
        form.circle_id.choices = [('', 'Select circle')]
        
    if company_id and circle_id:
        clients = Client.query.filter_by(company_id=company_id, circle_id=circle_id, status='Active').order_by(Client.client_name).all()
        form.client_id.choices = [('', 'Select client')] + [(c.id, f"{c.client_name} ({c.client_code})") for c in clients]
    else:
        form.client_id.choices = [('', 'Select client')]

    if form.validate_on_submit():
        try:
            data = {
                'project_code': form.project_code.data.strip().upper(),
                'project_name': form.project_name.data.strip(),
                'project_type': form.project_type.data,
                'status': form.status.data,
                'start_date': form.start_date.data,
                'end_date': form.end_date.data,
                'expected_completion_date': form.expected_completion_date.data,
                'operational_shift': form.operational_shift.data,
                'country': form.country.data,
                'state': form.state.data,
                'city': form.city.data,
                'pincode': form.pincode.data,
                'full_address': form.full_address.data,
                'deployment_allowed': form.deployment_allowed.data,
                'attendance_required': form.attendance_required.data,
                'gps_tracking_enabled': form.gps_tracking_enabled.data,
                'realtime_monitoring_enabled': form.realtime_monitoring_enabled.data,
                'geo_fencing_enabled': form.geo_fencing_enabled.data,
                'workflow_approval_enabled': form.workflow_approval_enabled.data,
                'document_verification_required': form.document_verification_required.data,
                'shift_based_attendance': form.shift_based_attendance.data,
                'max_vehicles': form.max_vehicles.data,
                'max_drivers': form.max_drivers.data,
                'deployment_capacity': form.deployment_capacity.data,
                'required_vehicle_types': form.required_vehicle_types.data,
                'operational_capacity': form.operational_capacity.data,
                'project_manager': form.project_manager.data,
                'operational_head': form.operational_head.data,
                'contact_number': form.contact_number.data,
                'operational_email': form.operational_email.data,
            }
            
            project_service.update_project(project_id, data, current_user.id)
            flash('Project updated successfully!', 'success')
            return redirect(url_for('projects.details', project_id=project_id))
        except Exception as e:
            flash(f'Error updating project: {str(e)}', 'danger')
    elif request.method == 'GET':
        form.company_id.data = project.company_id
        form.circle_id.data = project.circle_id
        form.client_id.data = project.client_id
        form.project_code.data = project.project_code
        form.project_name.data = project.project_name
        form.project_type.data = project.project_type
        form.status.data = project.status
        form.start_date.data = project.start_date
        form.end_date.data = project.end_date
        form.expected_completion_date.data = project.expected_completion_date
        form.operational_shift.data = project.operational_shift
        form.country.data = project.country
        form.state.data = project.state
        form.city.data = project.city
        form.pincode.data = project.pincode
        form.full_address.data = project.full_address
        form.deployment_allowed.data = project.deployment_allowed
        form.attendance_required.data = project.attendance_required
        form.gps_tracking_enabled.data = project.gps_tracking_enabled
        form.realtime_monitoring_enabled.data = project.realtime_monitoring_enabled
        form.geo_fencing_enabled.data = project.geo_fencing_enabled
        form.workflow_approval_enabled.data = project.workflow_approval_enabled
        form.document_verification_required.data = project.document_verification_required
        form.shift_based_attendance.data = project.shift_based_attendance
        form.max_vehicles.data = project.max_vehicles
        form.max_drivers.data = project.max_drivers
        form.deployment_capacity.data = project.deployment_capacity
        form.required_vehicle_types.data = project.required_vehicle_types
        form.operational_capacity.data = project.operational_capacity
        form.project_manager.data = project.project_manager
        form.operational_head.data = project.operational_head
        form.contact_number.data = project.contact_number
        form.operational_email.data = project.operational_email
        form.submit.label.text = 'Update Project'
        
    return render_template('projects/edit.html', form=form, project=project, active_page='projects')


@projects_bp.route('/<project_id>')
@login_required
def details(project_id):
    """Project details and dashboard"""
    project = project_service.get_project(project_id)
    
    if not project:
        flash('Project not found.', 'danger')
        return redirect(url_for('projects.index'))
    
    summary = project_service.get_project_summary(project.company_id, project.circle_id, project.client_id)
    
    return render_template(
        'projects/details.html',
        project=project,
        summary=summary,
        active_page='projects'
    )


# AJAX Endpoints for dependent dropdowns
@projects_bp.route('/circles/search')
@login_required
def circles_search():
    """Get circles for a company"""
    company_id = request.args.get('company_id')
    q = request.args.get('q', '').strip()
    
    if not company_id:
        return jsonify(items=[])
    
    query = Circle.query.filter_by(company_id=company_id, status='Active')
    if q:
        like = f"%{q}%"
        query = query.filter((Circle.circle_name.ilike(like)) | (Circle.circle_code.ilike(like)))
    
    circles = query.order_by(Circle.circle_name).limit(20).all()
    data = [
        {
            'id': circle.id,
            'text': f"{circle.circle_name} ({circle.circle_code})",
            'circle_name': circle.circle_name,
            'circle_code': circle.circle_code,
        }
        for circle in circles
    ]
    return jsonify(items=data)


@projects_bp.route('/clients/search')
@login_required
def clients_search():
    """Get clients for a circle"""
    company_id = request.args.get('company_id')
    circle_id = request.args.get('circle_id')
    q = request.args.get('q', '').strip()
    
    if not company_id or not circle_id:
        return jsonify(items=[])
    
    query = Client.query.filter_by(company_id=company_id, circle_id=circle_id, status='Active')
    if q:
        like = f"%{q}%"
        query = query.filter((Client.client_name.ilike(like)) | (Client.client_code.ilike(like)))
    
    clients = query.order_by(Client.client_name).limit(20).all()
    data = [
        {
            'id': client.id,
            'text': f"{client.client_name} ({client.client_code})",
            'client_name': client.client_name,
            'client_code': client.client_code,
        }
        for client in clients
    ]
    return jsonify(items=data)


@projects_bp.route('/check_code')
@login_required
def check_code():
    """Check if project code is unique"""
    company_id = request.args.get('company_id')
    client_id = request.args.get('client_id')
    code = (request.args.get('code') or '').strip().upper()
    
    exists = project_service.project_code_exists(company_id, client_id, code)
    return jsonify({'exists': exists})


@projects_bp.route('/get_data')
@login_required
def get_data():
    """Get project data for preview/info"""
    project_id = request.args.get('project_id')
    project = project_service.get_project(project_id)
    
    if not project:
        return jsonify({'error': 'Project not found'}), 404
    
    return jsonify(project.to_dict())

