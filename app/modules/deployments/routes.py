"""
Deployment Web Routes

User interface routes for vehicle deployment management.
"""

from datetime import datetime, timezone
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import current_user, login_required

from app.core.decorators import permission_required
from app.modules.deployments.services import DeploymentService
from app.modules.deployments.forms import DeploymentForm, DeploymentApprovalForm, DeploymentCompletionForm, HelperAssignmentForm
from app.modules.vehicles.models import Vehicle
from app.modules.projects.models import Project
from app.modules.subzones.models import Subzone
from app.modules.auth.models import User, Role
from app.modules.drivers.models import DriverProfile
from app.modules.deployments.models import VehicleDeployment, HelperAssignment
from app.modules.deployments.forms import AssignDriverForm
from app.modules.deployments.assignment_dashboard_service import AssignmentDashboardService
from app.extensions import db
deployments_bp = Blueprint('deployments', __name__, url_prefix='/deployments')
deployment_service = DeploymentService()


def get_vehicle_choices():
    """Get available vehicles for deployment"""
    vehicles = Vehicle.query.filter(Vehicle.status.in_(['Available', 'Assigned'])).order_by(Vehicle.vehicle_number).all()
    return [('', 'Select vehicle')] + [(v.id, f"{v.vehicle_number} ({v.vehicle_type})") for v in vehicles]


def get_driver_choices():
    """Get available drivers for deployment"""
    drivers = AssignmentDashboardService.get_available_drivers()
    return [('', 'Select driver (optional)')] + [
        (driver['driver_id'], driver['driver_name'])
        for driver in drivers
        if driver.get('driver_id') and driver.get('driver_name')
    ]


def ensure_driver_profile(driver, vehicle=None):
    """Create a minimal profile for Driver-role users missing one."""
    profile = getattr(driver, 'driver_profile', None)
    if profile:
        return profile

    profile = DriverProfile(
        user_id=driver.id,
        circle_id=getattr(driver, 'circle_id', None) or getattr(vehicle, 'circle_id', None),
        client_id=getattr(vehicle, 'client_id', None),
        project_id=getattr(vehicle, 'project_id', None),
        subzone_id=getattr(vehicle, 'subzone_id', None),
        license_status='Pending',
        compliance_status='Pending',
        active=True,
    )
    db.session.add(profile)
    db.session.flush()
    return profile


def get_project_choices():
    """Get active projects for deployment"""
    projects = Project.query.filter_by(status='Active').order_by(Project.project_name).all()
    return [('', 'Select project')] + [(p.id, f"{p.project_name} ({p.project_code})") for p in projects]


def get_subzone_choices(project_id):
    """Get subzones for project"""
    if not project_id:
        return [('', 'Select subzone')]
    subzones = Subzone.query.filter_by(project_id=project_id, status='Active').order_by(Subzone.subzone_name).all()
    return [('', 'Select subzone')] + [(s.id, f"{s.subzone_name} ({s.subzone_code})") for s in subzones]


# ============================================================================
# Main Deployment Routes
# ============================================================================

@deployments_bp.route('/', methods=['GET'])
@login_required
@permission_required('deployments.view')
def index():
    """Vehicle deployment list view"""
    from app.domain.auth.policies.auth_policy import has_role
    from app.modules.drivers.models import DriverProfile
    
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', '', type=str)
    approval_filter = request.args.get('approval_status', '', type=str)
    
    filters = {}
    if status_filter:
        filters['status'] = status_filter
    if approval_filter:
        filters['approval_status'] = approval_filter

    # If user is ONLY a driver (not admin), only show their own deployments
    if has_role('Driver') and not has_role('Super Admin') and not has_role('Admin'):
        # Deployments use user_id, not driver_profile_id
        filters['driver_id'] = current_user.id

    result = deployment_service.list_deployments(filters, page, per_page=20)
    
    return render_template(
        'deployments/index.html',
        deployments=result['deployments'],
        total=result['total'],
        page=result['page'],
        pages=result['pages'],
        status_filter=status_filter,
        approval_filter=approval_filter,
        active_page='deployments'
    )


@deployments_bp.route('/create', methods=['GET', 'POST'])
@login_required
@permission_required('deployments.create')
def create():
    """Create new deployment"""
    form = DeploymentForm()
    form.vehicle_id.choices = get_vehicle_choices()
    form.driver_id.choices = get_driver_choices()
    form.project_id.choices = get_project_choices()

    if request.method == 'POST':
        form.subzone_id.choices = get_subzone_choices(form.project_id.data)
        if form.validate_on_submit():
            payload = {
                'vehicle_id': form.vehicle_id.data,
                'driver_id': form.driver_id.data if form.driver_id.data else None,
                'project_id': form.project_id.data,
                'subzone_id': form.subzone_id.data,
                'deployment_type': form.deployment_type.data,
                'route_name': form.route_name.data,
                'pickup_location': form.pickup_location.data,
                'dropoff_location': form.dropoff_location.data,
                'vehicle_fitness_verified': form.vehicle_fitness_verified.data,
                'driver_license_verified': form.driver_license_verified.data,
                'insurance_verified': form.insurance_verified.data,
                'safety_checklist_completed': form.safety_checklist_completed.data,
                'special_instructions': form.special_instructions.data,
                'notes': form.notes.data,
            }
            
            deployment, error = deployment_service.create_deployment(payload, current_user.id)
            if error:
                flash(f'Error creating deployment: {error}', 'danger')
                return redirect(url_for('deployments.create'))

            flash('Deployment created and awaiting approval.', 'success')
            return redirect(url_for('deployments.detail', deployment_id=deployment.id))

    return render_template(
        'deployments/create.html',
        form=form,
        active_page='deployments'
    )


@deployments_bp.route('/<deployment_id>', methods=['GET'])
@login_required
@permission_required('deployments.view')
def detail(deployment_id):
    """Deployment detail view"""
    from app.domain.auth.policies.auth_policy import has_role
    
    result = deployment_service.get_deployment(deployment_id)
    if not result:
        flash('Deployment not found.', 'danger')
        return redirect(url_for('deployments.index'))

    # If user is ONLY a driver (not admin), verify they can only see their own deployments
    if has_role('Driver') and not has_role('Super Admin') and not has_role('Admin'):
        deployment_data = result['deployment']
        # deployment_data['driver_id'] is the user_id
        if deployment_data.get('driver_id') != current_user.id:
            flash('You do not have permission to view this deployment.', 'danger')
            return redirect(url_for('deployments.index'))

    return render_template(
        'deployments/detail.html',
        deployment=result['deployment'],
        approval_logs=result['approval_logs'],
        active_page='deployments'
    )


# ============================================================================
# Approval Workflow Routes
# ============================================================================

@deployments_bp.route('/<deployment_id>/approve', methods=['GET', 'POST'])
@login_required
@permission_required('deployments.approve')
def approve(deployment_id):
    """Approve deployment"""
    result = deployment_service.get_deployment(deployment_id)
    if not result:
        flash('Deployment not found.', 'danger')
        return redirect(url_for('deployments.index'))

    deployment = result['deployment']
    if deployment['approval_status'] != 'Pending':
        flash(f'Deployment is {deployment["approval_status"]} and cannot be approved.', 'danger')
        return redirect(url_for('deployments.detail', deployment_id=deployment_id))

    form = DeploymentApprovalForm()
    if form.validate_on_submit():
        if form.approval_action.data == 'approve':
            deployment, error = deployment_service.approve_deployment(
                deployment_id, current_user.id, form.reason.data
            )
            if error:
                flash(f'Approval failed: {error}', 'danger')
            else:
                flash('Deployment approved successfully.', 'success')
        elif form.approval_action.data == 'reject':
            deployment, error = deployment_service.reject_deployment(
                deployment_id, current_user.id, form.reason.data
            )
            if error:
                flash(f'Rejection failed: {error}', 'danger')
            else:
                flash('Deployment rejected.', 'warning')
        elif form.approval_action.data == 'escalate':
            deployment, error = deployment_service.escalate_deployment(
                deployment_id, current_user.id, form.reason.data
            )
            if error:
                flash(f'Escalation failed: {error}', 'danger')
            else:
                flash('Deployment escalated for review.', 'info')
        else:
            flash('Invalid approval action selected.', 'danger')

        return redirect(url_for('deployments.detail', deployment_id=deployment_id))

    return render_template(
        'deployments/approve.html',
        deployment=deployment,
        form=form,
        active_page='deployments'
    )


# ============================================================================
# Active & History Views
# ============================================================================

@deployments_bp.route('/active', methods=['GET'])
@login_required
@permission_required('deployments.view')
def active():
    """View active deployments"""
    page = request.args.get('page', 1, type=int)
    result = deployment_service.get_active_deployments(page, per_page=20)

    return render_template(
        'deployments/active.html',
        deployments=result['deployments'],
        total=result['total'],
        page=result['page'],
        active_page='deployments_active'
    )


@deployments_bp.route('/history', methods=['GET'])
@login_required
@permission_required('deployments.view')
def history():
    """View deployment history"""
    page = request.args.get('page', 1, type=int)
    vehicle_id = request.args.get('vehicle_id', '', type=str)
    driver_id = request.args.get('driver_id', '', type=str)

    result = deployment_service.get_deployment_history(
        vehicle_id if vehicle_id else None,
        driver_id if driver_id else None,
        page, per_page=20
    )

    return render_template(
        'deployments/history.html',
        deployments=result['deployments'],
        total=result['total'],
        page=result['page'],
        vehicle_id=vehicle_id,
        driver_id=driver_id,
        active_page='deployments_history'
    )


@deployments_bp.route('/requests', methods=['GET'])
@login_required
@permission_required('deployments.view')
def requests():
    """View pending deployment requests"""
    page = request.args.get('page', 1, type=int)
    result = deployment_service.get_pending_approvals(page, per_page=20)

    return render_template(
        'deployments/requests.html',
        deployments=result['deployments'],
        total=result['total'],
        page=result['page'],
        active_page='deployment_requests'
    )


@deployments_bp.route('/assignment-dashboard', methods=['GET', 'POST'])
@login_required
@permission_required('deployments.assign')
def assignment_dashboard():
    """Operational Workforce Allocation Dashboard
    
    Shows:
    - KPI metrics (total drivers, assigned, available, compliance failed, deployment ready, expiring)
    - Paginated assignment table with compliance status
    - Modal for creating new assignments with validation
    """
    from datetime import datetime, timezone
    from app.modules.drivers.models import DriverVehicleAssignment
    
    page = request.args.get('page', 1, type=int)
    filter_status = request.args.get('filter_status', '', type=str)
    per_page = 20

    # Get KPI metrics
    kpis = AssignmentDashboardService.get_kpi_metrics()

    # Get assignments list
    offset = (page - 1) * per_page
    assignments, total = AssignmentDashboardService.get_assignments_list(offset, per_page, filter_status or None)

    # Get available drivers and vehicles for modal
    available_drivers = AssignmentDashboardService.get_available_drivers()
    available_vehicles = AssignmentDashboardService.get_available_vehicles()

    # Handle POST: new assignment via dashboard
    if request.method == 'POST':
        from app.services.compliance.assignment_validation_service import AssignmentValidationService
        
        driver_id = request.form.get('driver_id')
        vehicle_id = request.form.get('vehicle_id')

        if not driver_id or not vehicle_id:
            flash('Driver and vehicle are required.', 'danger')
            return redirect(url_for('deployments.assignment_dashboard', page=page))

        vehicle = Vehicle.query.get(vehicle_id)
        driver = User.query.get(driver_id)

        if not vehicle or not driver:
            flash('Invalid vehicle or driver selected.', 'danger')
            return redirect(url_for('deployments.assignment_dashboard', page=page))

        # Validate
        validator = AssignmentValidationService()
        result = validator.validate_assignment(driver_id=driver.id, vehicle_id=vehicle.id, project_id=vehicle.project_id, subzone_id=vehicle.subzone_id)

        # Record audit assignment
        profile = ensure_driver_profile(driver, vehicle)
        driver_profile_id = profile.id if profile else None
        from app.modules.drivers.models import DriverVehicleAssignment
        assignment_record = DriverVehicleAssignment(
            driver_id=driver_profile_id,
            vehicle_id=vehicle.id,
            assigned_at=datetime.now(timezone.utc),
            assignment_reason='Assigned via operational dashboard',
            status='Failed_Validation' if not result['is_valid'] else 'Active'
        )
        db.session.add(assignment_record)
        db.session.commit()

        if not result['is_valid']:
            flash('Assignment blocked: ' + '; '.join(result.get('blocking_issues', [])), 'danger')
            return redirect(url_for('deployments.assignment_dashboard', page=page))

        # Perform assignment
        vehicle.assigned_driver_id = driver.id
        vehicle.assigned_driver = driver.username
        vehicle.status = 'Assigned'
        if profile:
            profile.active = True
        db.session.commit()

        # Create deployment
        payload = {
            'vehicle_id': vehicle.id,
            'driver_id': driver.id,
            'project_id': vehicle.project_id,
            'subzone_id': vehicle.subzone_id,
            'deployment_type': 'Standard',
            'route_name': 'Operational Assignment',
            'vehicle_fitness_verified': True,
            'driver_license_verified': True,
            'insurance_verified': True,
            'safety_checklist_completed': True,
            'special_instructions': 'Auto-created from assignment dashboard',
            'notes': 'Created from Driver Assignment Dashboard',
        }

        deployment, error = deployment_service.create_deployment(payload, current_user.id)
        if error:
            flash('Assignment saved but deployment creation failed: ' + str(error), 'warning')
            return redirect(url_for('deployments.assignment_dashboard', page=page))

        flash(f'Driver {driver.username} assigned to {vehicle.vehicle_number} and deployment activated.', 'success')
        return redirect(url_for('deployments.assignment_dashboard', page=page))

    pages = (total + per_page - 1) // per_page

    return render_template(
        'deployments/assignment_dashboard.html',
        kpis=kpis,
        assignments=assignments,
        total=total,
        page=page,
        pages=pages,
        available_drivers=available_drivers,
        available_vehicles=available_vehicles,
        active_page='driver_assignment'
    )


@deployments_bp.route('/assign', methods=['GET', 'POST'])
@login_required
@permission_required('deployments.assign')
def assign():
    """Assign a driver to a vehicle (operational assignment with validation).

    - Runs validation engine
    - Records DriverVehicleAssignment audit entry
    - Creates a deployment (auto-approved) on success
    """
    from app.services.compliance.assignment_validation_service import AssignmentValidationService
    from app.modules.drivers.models import DriverVehicleAssignment, DriverProfile
    from app.extensions import db
    from datetime import datetime, timezone

    form = AssignDriverForm()
    form.vehicle_id.choices = get_vehicle_choices()
    form.driver_id.choices = get_driver_choices()

    if form.validate_on_submit():
        vehicle = Vehicle.query.filter_by(id=form.vehicle_id.data).first()
        driver = User.query.filter_by(id=form.driver_id.data).first()
        if not vehicle or not driver:
            flash('Invalid vehicle or driver selected.', 'danger')
            return redirect(url_for('deployments.assign'))

        # Validate assignment using central validation engine
        validator = AssignmentValidationService()
        result = validator.validate_assignment(driver_id=driver.id, vehicle_id=vehicle.id, project_id=form.project_id.data if hasattr(form, 'project_id') else None, subzone_id=form.subzone_id.data if hasattr(form, 'subzone_id') else None)

        # Create audit assignment record regardless (preserve history)
        profile = ensure_driver_profile(driver, vehicle)
        driver_profile_id = profile.id if profile else None
        assignment = DriverVehicleAssignment(
            driver_id=driver_profile_id,
            vehicle_id=vehicle.id,
            assigned_at=datetime.now(timezone.utc),
            assignment_reason='Assigned via operational UI',
            status='Failed_Validation' if not result['is_valid'] else 'Active'
        )
        db.session.add(assignment)
        db.session.commit()

        if not result['is_valid']:
            flash('Assignment blocked: ' + '; '.join(result.get('blocking_issues', [])), 'danger')
            return redirect(url_for('deployments.assign'))

        # Perform assignment
        vehicle.assigned_driver_id = driver.id
        vehicle.assigned_driver = getattr(driver, 'username', None)
        vehicle.status = 'Assigned'

        # Update driver profile status if available
        if profile:
            profile.active = True

        db.session.commit()

        # Create a deployment record (auto-approved behavior in service)
        payload = {
            'vehicle_id': vehicle.id,
            'driver_id': driver.id,
            'project_id': vehicle.project_id,
            'subzone_id': vehicle.subzone_id,
            'deployment_type': 'Standard',
            'route_name': 'Operational Assignment',
            'pickup_location': None,
            'dropoff_location': None,
            'vehicle_fitness_verified': True,
            'driver_license_verified': True,
            'insurance_verified': True,
            'safety_checklist_completed': True,
            'special_instructions': 'Auto-created deployment for assignment',
            'notes': 'Created from Driver Assignment UI',
        }

        deployment, error = deployment_service.create_deployment(payload, current_user.id)
        if error:
            flash('Assignment saved but deployment creation failed: ' + str(error), 'warning')
            return redirect(url_for('deployments.index'))

        flash(f'Driver {driver.username} assigned to {vehicle.vehicle_number} and deployment started.', 'success')
        return redirect(url_for('deployments.detail', deployment_id=deployment.id))

    return render_template(
        'deployments/assign.html',
        form=form,
        active_page='driver_assignment'
    )


@deployments_bp.route('/release-assignment/<assignment_id>', methods=['POST'])
@login_required
@permission_required('deployments.assign')
def release_assignment(assignment_id):
    """Release/remove a driver from a vehicle assignment"""
    from app.modules.drivers.models import DriverVehicleAssignment
    
    assignment = DriverVehicleAssignment.query.get(assignment_id)
    if not assignment:
        flash('Assignment not found.', 'danger')
        return redirect(url_for('deployments.assignment_dashboard'))
    
    # Get associated vehicle and driver
    vehicle = Vehicle.query.get(assignment.vehicle_id)
    driver_profile = assignment.driver
    driver_user = driver_profile.user if driver_profile else None
    
    if not vehicle or not driver_user:
        flash('Vehicle or driver not found.', 'danger')
        return redirect(url_for('deployments.assignment_dashboard'))
    
    try:
        now = datetime.now(timezone.utc)

        active_deployments = VehicleDeployment.query.filter(
            VehicleDeployment.vehicle_id == vehicle.id,
            VehicleDeployment.driver_id == driver_user.id,
            VehicleDeployment.status.in_(['Pending', 'Approved', 'Active']),
        ).all()
        for deployment in active_deployments:
            deployment.status = 'Cancelled'
            deployment.actual_end = deployment.actual_end or now

        active_assignments = DriverVehicleAssignment.query.filter(
            DriverVehicleAssignment.driver_id == assignment.driver_id,
            DriverVehicleAssignment.vehicle_id == assignment.vehicle_id,
            DriverVehicleAssignment.status.in_(['Active', 'Failed_Validation']),
        ).all()
        for active_assignment in active_assignments:
            active_assignment.released_at = active_assignment.released_at or now
            active_assignment.status = 'Released'

        # Release the vehicle and make it available again
        if str(vehicle.assigned_driver_id or '') == str(driver_user.id) or vehicle.assigned_driver == driver_user.username:
            vehicle.assigned_driver_id = None
            vehicle.assigned_driver = None
            vehicle.current_deployment = None
            vehicle.status = 'Available'
        
        db.session.commit()

        message = f'Assignment released: {driver_user.username} removed from {vehicle.vehicle_number}.'
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.accept_mimetypes.best == 'application/json':
            return jsonify({'success': True, 'message': message})

        flash(message, 'success')
    except Exception as e:
        db.session.rollback()
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.accept_mimetypes.best == 'application/json':
            return jsonify({'success': False, 'message': str(e)}), 500
        flash(f'Error releasing assignment: {str(e)}', 'danger')
    
    page = request.args.get('page', 1, type=int)
    return redirect(url_for('deployments.assignment_dashboard', page=page))


# ============================================================================
# AJAX Helpers
# ============================================================================

@deployments_bp.route('/ajax/subzones', methods=['GET'])
@login_required
def ajax_subzones():
    """Get subzones for project (AJAX)"""
    project_id = request.args.get('project_id', '', type=str)
    choices = get_subzone_choices(project_id)
    return jsonify([
        {'id': code, 'text': text}
        for code, text in choices if code
    ])


@deployments_bp.route('/ajax/vehicle-info', methods=['GET'])
@login_required
def ajax_vehicle_info():
    """Get vehicle metadata and matching drivers for deployment (AJAX)"""
    vehicle_id = request.args.get('vehicle_id', '', type=str)
    if not vehicle_id:
        return jsonify({'project_id': None, 'subzone_id': None, 'drivers': []})

    vehicle = Vehicle.query.filter_by(id=vehicle_id).first()
    if not vehicle:
        return jsonify({'project_id': None, 'subzone_id': None, 'drivers': []})

    drivers = (
        DriverProfile.query
        .filter_by(active=True, project_id=vehicle.project_id, subzone_id=vehicle.subzone_id)
        .join(User)
        .order_by(User.username)
        .all()
    )

    return jsonify({
        'project_id': vehicle.project_id,
        'subzone_id': vehicle.subzone_id,
        'drivers': [
            {'id': profile.user_id, 'text': profile.user.username}
            for profile in drivers
            if profile.user
        ],
    })


@deployments_bp.route('/ajax/stats', methods=['GET'])
@login_required
@permission_required('deployments.view')
def ajax_stats():
    """Get deployment statistics (AJAX)"""
    stats = deployment_service.get_deployment_stats()
    return jsonify(stats)


# ============================================================================
# Helper Assignment Routes
# ============================================================================

@deployments_bp.route('/helper-assignments', methods=['GET'])
@login_required
@permission_required('helper_assignments.view')
def helper_assignments_index():
    """List helper assignments"""
    from app.modules.circles.models import Circle
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    query = HelperAssignment.query
    
    # Scope restrictions
    if current_user.has_role('Helper') and not current_user.has_role('Super Admin') and not current_user.has_role('Admin'):
        query = query.filter_by(helper_id=current_user.id)
    else:
        if current_user.circle_id:
            query = query.filter_by(circle_id=current_user.circle_id)
        elif current_user.company_id:
            query = query.join(Circle, HelperAssignment.circle_id == Circle.id).filter(Circle.company_id == current_user.company_id)
            
    total = query.count()
    assignments = query.order_by(HelperAssignment.created_at.desc()).offset((page - 1) * per_page).limit(per_page).all()
    pages = (total + per_page - 1) // per_page
    
    return render_template(
        'deployments/helper_assignments/index.html',
        assignments=assignments,
        page=page,
        pages=pages,
        total=total,
        active_page='helper_assignments'
    )


@deployments_bp.route('/helper-assignments/create', methods=['GET', 'POST'])
@login_required
@permission_required('helper_assignments.create')
def helper_assignments_create():
    """Create a new helper assignment"""
    from app.modules.circles.models import Circle
    from app.modules.clients.models import Client
    from app.modules.notifications.helpers import create_notification_safe
    
    form = HelperAssignmentForm()
    
    # Helpers choice list
    helpers = User.query.join(User.roles).filter(Role.name == 'Helper').all()
    form.helper_id.choices = [('', 'Select helper')] + [(h.id, h.username) for h in helpers]
    
    # Circles choice list
    if current_user.circle_id:
        circles = Circle.query.filter_by(id=current_user.circle_id).all()
    elif current_user.company_id:
        circles = Circle.query.filter_by(company_id=current_user.company_id).all()
    else:
        circles = Circle.query.all()
    form.circle_id.choices = [('', 'Select circle')] + [(c.id, c.circle_name) for c in circles]
    
    # Pre-populate clients, projects, subzones dynamically
    projects = Project.query.filter_by(status='Active').all()
    form.project_id.choices = [('', 'Select project')] + [(p.id, p.project_name) for p in projects]
    
    subzones = Subzone.query.filter_by(status='Active').all()
    form.subzone_id.choices = [('', 'Select subzone')] + [(s.id, s.subzone_name) for s in subzones]
    
    # Optional drivers and vehicles
    drivers = User.query.join(User.roles).filter(Role.name == 'Driver').all()
    form.assigned_driver_id.choices = [('', 'Select driver (optional)')] + [(d.id, d.username) for d in drivers]
    
    vehicles = Vehicle.query.filter(Vehicle.status.in_(['Available', 'Assigned'])).all()
    form.assigned_vehicle_id.choices = [('', 'Select vehicle (optional)')] + [(v.id, v.vehicle_number) for v in vehicles]
    
    if request.method == 'POST':
        # Re-populate choices before validation
        if form.validate_on_submit():
            # Check for existing active assignment
            active_assignment = HelperAssignment.query.filter_by(
                helper_id=form.helper_id.data,
                status='Active'
            ).first()
            
            if active_assignment:
                form.helper_id.errors.append("Helper already has an active assignment.")
            else:
                assignment = HelperAssignment(
                    helper_id=form.helper_id.data,
                    circle_id=form.circle_id.data,
                    project_id=form.project_id.data,
                    subzone_id=form.subzone_id.data,
                    shift=form.shift.data or None,
                    start_date=form.start_date.data,
                    end_date=form.end_date.data,
                    status=form.status.data,
                    remarks=form.remarks.data or None,
                    assigned_driver_id=form.assigned_driver_id.data or None,
                    assigned_vehicle_id=form.assigned_vehicle_id.data or None,
                    created_by=current_user.id
                )
                db.session.add(assignment)
                
                # Also ensure driver profile is populated for attendance tracking
                helper_user = User.query.get(form.helper_id.data)
                if helper_user:
                    from app.modules.users.services.user_service import ensure_helper_profile
                    ensure_helper_profile(helper_user)
                
                db.session.commit()
                
                # Trigger Helper Assigned Notification
                create_notification_safe(
                    user_id=assignment.helper_id,
                    message=f"You have been assigned to Circle: {assignment.circle.circle_name if assignment.circle else 'N/A'}, Project: {assignment.project.project_name if assignment.project else 'N/A'}.",
                    module='deployments',
                    priority='Info',
                    related_type='helper_assignment',
                    related_id=assignment.id,
                    company_id=assignment.project.company_id if assignment.project else None,
                    circle_id=assignment.circle_id
                )
                
                flash('Helper assignment created successfully.', 'success')
                return redirect(url_for('deployments.helper_assignments_index'))
                
    else:
        # Default start date to today
        form.start_date.data = datetime.now(timezone.utc).date()
        
    return render_template(
        'deployments/helper_assignments/create.html',
        form=form,
        active_page='helper_assignments'
    )


@deployments_bp.route('/helper-assignments/<id>/edit', methods=['GET', 'POST'])
@login_required
@permission_required('helper_assignments.edit')
def helper_assignments_edit(id):
    """Edit an existing helper assignment"""
    from app.modules.circles.models import Circle
    from app.modules.notifications.helpers import create_notification_safe
    
    assignment = HelperAssignment.query.get_or_404(id)
    form = HelperAssignmentForm(obj=assignment)
    
    helpers = User.query.join(User.roles).filter(Role.name == 'Helper').all()
    form.helper_id.choices = [('', 'Select helper')] + [(h.id, h.username) for h in helpers]
    
    if current_user.circle_id:
        circles = Circle.query.filter_by(id=current_user.circle_id).all()
    elif current_user.company_id:
        circles = Circle.query.filter_by(company_id=current_user.company_id).all()
    else:
        circles = Circle.query.all()
    form.circle_id.choices = [('', 'Select circle')] + [(c.id, c.circle_name) for c in circles]
    
    projects = Project.query.filter_by(status='Active').all()
    form.project_id.choices = [('', 'Select project')] + [(p.id, p.project_name) for p in projects]
    
    subzones = Subzone.query.filter_by(status='Active').all()
    form.subzone_id.choices = [('', 'Select subzone')] + [(s.id, s.subzone_name) for s in subzones]
    
    drivers = User.query.join(User.roles).filter(Role.name == 'Driver').all()
    form.assigned_driver_id.choices = [('', 'Select driver (optional)')] + [(d.id, d.username) for d in drivers]
    
    vehicles = Vehicle.query.filter(Vehicle.status.in_(['Available', 'Assigned'])).all()
    form.assigned_vehicle_id.choices = [('', 'Select vehicle (optional)')] + [(v.id, v.vehicle_number) for v in vehicles]
    
    if request.method == 'POST':
        if form.validate_on_submit():
            # Check for another active assignment
            active_assignment = HelperAssignment.query.filter(
                HelperAssignment.helper_id == form.helper_id.data,
                HelperAssignment.status == 'Active',
                HelperAssignment.id != id
            ).first()
            
            if active_assignment:
                form.helper_id.errors.append("Helper already has an active assignment.")
            else:
                form.populate_obj(assignment)
                assignment.updated_at = datetime.now(timezone.utc)
                db.session.commit()
                
                # Trigger Helper Reassigned Notification
                create_notification_safe(
                    user_id=assignment.helper_id,
                    message="Your deployment assignment has been updated.",
                    module='deployments',
                    priority='Medium',
                    related_type='helper_assignment',
                    related_id=assignment.id,
                    company_id=assignment.project.company_id if assignment.project else None,
                    circle_id=assignment.circle_id
                )
                
                flash('Helper assignment updated successfully.', 'success')
                return redirect(url_for('deployments.helper_assignments_index'))
                
    return render_template(
        'deployments/helper_assignments/edit.html',
        form=form,
        assignment=assignment,
        active_page='helper_assignments'
    )


@deployments_bp.route('/helper-assignments/<id>/end', methods=['POST'])
@login_required
@permission_required('helper_assignments.delete')
def helper_assignments_end(id):
    """End a helper assignment"""
    from app.modules.notifications.helpers import create_notification_safe
    
    assignment = HelperAssignment.query.get_or_404(id)
    assignment.status = 'Ended'
    assignment.end_date = datetime.now(timezone.utc).date()
    assignment.updated_at = datetime.now(timezone.utc)
    db.session.commit()
    
    # Trigger Assignment Ended Notification
    create_notification_safe(
        user_id=assignment.helper_id,
        message="Your deployment assignment has ended.",
        module='deployments',
        priority='Info',
        related_type='helper_assignment',
        related_id=assignment.id,
        company_id=assignment.project.company_id if assignment.project else None,
        circle_id=assignment.circle_id
    )
    
    flash('Helper assignment ended successfully.', 'success')
    return redirect(url_for('deployments.helper_assignments_index'))


@deployments_bp.route('/helper-assignments/<id>/view', methods=['GET'])
@login_required
@permission_required('helper_assignments.view')
def helper_assignments_view(id):
    """View helper assignment details"""
    assignment = HelperAssignment.query.get_or_404(id)
    
    # Scope check for helper
    if current_user.has_role('Helper') and not current_user.has_role('Super Admin') and not current_user.has_role('Admin'):
        if assignment.helper_id != current_user.id:
            flash('Access denied.', 'danger')
            return redirect(url_for('deployments.helper_assignments_index'))
            
    return render_template(
        'deployments/helper_assignments/view.html',
        assignment=assignment,
        active_page='helper_assignments'
    )
