"""
Assignment Dashboard Services

Helper functions for fetching assignment statistics and operational data.
"""

from datetime import datetime, timezone

from app.modules.vehicles.models import Vehicle
from app.modules.auth.models import User, Role
from app.modules.drivers.models import DriverProfile, DriverVehicleAssignment
from app.modules.deployments.models import VehicleDeployment
from app.extensions import db


class AssignmentDashboardService:
    """Service for assignment dashboard metrics and data"""

    @staticmethod
    def normalize_released_vehicle_state():
        """Clear stale deployment state for vehicles already marked available."""
        available_unassigned = Vehicle.query.filter(
            Vehicle.status == 'Available',
            Vehicle.assigned_driver_id.is_(None),
        ).all()

        changed = False
        now = datetime.now(timezone.utc)
        for vehicle in available_unassigned:
            active_deployments = VehicleDeployment.query.filter(
                VehicleDeployment.vehicle_id == vehicle.id,
                VehicleDeployment.status.in_(['Pending', 'Approved', 'Active']),
            ).all()
            for deployment in active_deployments:
                deployment.status = 'Cancelled'
                deployment.actual_end = deployment.actual_end or now
                changed = True

            if vehicle.current_deployment:
                vehicle.current_deployment = None
                changed = True

        if changed:
            db.session.commit()

    @staticmethod
    def get_kpi_metrics():
        """Get KPI cards for dashboard"""
        total_drivers = DriverProfile.query.filter_by(active=True).count()
        
        assigned_drivers = db.session.query(DriverProfile.id).join(
            Vehicle, Vehicle.assigned_driver_id == DriverProfile.user_id
        ).distinct().count()
        
        available_drivers = total_drivers - assigned_drivers
        
        # Compliance failed: drivers with license_status != 'Verified' OR compliance_status != 'Verified'
        non_compliant = DriverProfile.query.filter(
            db.or_(
                DriverProfile.license_status != 'Verified',
                DriverProfile.compliance_status != 'Verified'
            )
        ).count()
        
        # Deployment ready: available vehicles with valid compliance
        deployment_ready = Vehicle.query.filter_by(status='Available').filter(
            Vehicle.insurance_status == 'Valid',
            Vehicle.fitness_status == 'Valid',
            Vehicle.puc_status == 'Valid'
        ).count()
        
        # Expiring licenses (next 30 days)
        from datetime import datetime, timedelta, timezone
        thirty_days = datetime.now(timezone.utc) + timedelta(days=30)
        from app.modules.drivers.models import DriverLicense
        expiring = DriverLicense.query.filter(
            DriverLicense.expiry_date.isnot(None),
            DriverLicense.expiry_date <= thirty_days.date(),
            DriverLicense.expiry_date > datetime.now(timezone.utc).date()
        ).count()
        
        return {
            'total_drivers': total_drivers,
            'assigned_drivers': assigned_drivers,
            'available_drivers': available_drivers,
            'compliance_failed': non_compliant,
            'deployment_ready': deployment_ready,
            'expiring_licenses': expiring,
        }

    @staticmethod
    def get_assignments_list(offset=0, limit=20, filter_status=None):
        """Get paginated list of driver-vehicle assignments with details"""
        from sqlalchemy.orm import lazyload
        query = db.session.query(
            DriverVehicleAssignment,
            DriverProfile,
            Vehicle,
            User
        ).join(
            DriverProfile, DriverProfile.id == DriverVehicleAssignment.driver_id
        ).join(
            Vehicle, Vehicle.id == DriverVehicleAssignment.vehicle_id
        ).join(
            User, User.id == DriverProfile.user_id
        ).options(
            lazyload('*')
        )
        
        if filter_status:
            query = query.filter(DriverVehicleAssignment.status == filter_status)
        else:
            query = query.filter(DriverVehicleAssignment.status.in_(['Active', 'Failed_Validation']))
        
        total = query.count()
        results = query.order_by(DriverVehicleAssignment.assigned_at.desc()).offset(offset).limit(limit).all()
        
        assignments = []
        for assign, profile, vehicle, user in results:
            # Get latest deployment for this assignment
            deployment = VehicleDeployment.query.filter_by(
                driver_id=user.id,
                vehicle_id=vehicle.id
            ).order_by(VehicleDeployment.created_at.desc()).first()
            
            assignments.append({
                'assignment_id': assign.id,
                'driver_id': user.id,
                'driver_name': user.username,
                'license_status': profile.license_status,
                'compliance_status': profile.compliance_status,
                'vehicle_id': vehicle.id,
                'vehicle_number': vehicle.vehicle_number,
                'vehicle_type': vehicle.vehicle_type,
                'insurance_status': vehicle.insurance_status,
                'fitness_status': vehicle.fitness_status,
                'project_id': vehicle.project_id,
                'project_name': vehicle.project.project_name if vehicle.project else None,
                'subzone_id': vehicle.subzone_id,
                'subzone_name': vehicle.subzone.subzone_name if vehicle.subzone else None,
                'assignment_status': assign.status,
                'assigned_at': assign.assigned_at.isoformat() if assign.assigned_at else None,
                'deployment_status': deployment.status if deployment else None,
                'deployment_id': deployment.id if deployment else None,
            })
        
        return assignments, total

    @staticmethod
    def get_available_drivers(project_id=None, subzone_id=None):
        """Get list of drivers for assignment."""
        assigned_driver_ids = db.session.query(Vehicle.assigned_driver_id).filter(Vehicle.assigned_driver_id.isnot(None))
        query = DriverProfile.query.join(User).filter(
            User.is_active.is_(True),
            ~User.id.in_(assigned_driver_ids)
        )
        
        # Filter by project/subzone if specified
        if project_id:
            query = query.filter(DriverProfile.project_id == project_id)
        if subzone_id:
            query = query.filter(DriverProfile.subzone_id == subzone_id)
        
        drivers = query.order_by(User.username).all()
        rows = [
            {
                'driver_id': d.user_id,
                'driver_name': d.user.username if d.user else None,
                'driver_code': d.driver_code,
                'license_status': d.license_status,
                'compliance_status': d.compliance_status,
                'active': d.active,
                'project_id': d.project_id,
                'project_name': d.project.project_name if d.project else None,
                'subzone_id': d.subzone_id,
                'subzone_name': d.subzone.subzone_name if d.subzone else None,
            }
            for d in drivers
            if d.user
        ]

        seen_user_ids = {row['driver_id'] for row in rows}
        driver_role = Role.query.filter(Role.name.ilike('driver')).first()
        if driver_role:
            role_users = (
                User.query
                .filter(User.is_active.is_(True))
                .filter(
                    db.or_(
                        User.role_id == driver_role.id,
                        User.roles.any(Role.id == driver_role.id),
                    )
                )
                .order_by(User.username)
                .all()
            )
            assigned_uids = {v[0] for v in db.session.query(Vehicle.assigned_driver_id).filter(Vehicle.assigned_driver_id.isnot(None)).all()}
            for user in role_users:
                if user.id in seen_user_ids or user.id in assigned_uids:
                    continue
                rows.append({
                    'driver_id': user.id,
                    'driver_name': user.username,
                    'driver_code': None,
                    'license_status': 'Pending',
                    'compliance_status': 'Pending',
                    'active': user.is_active,
                    'project_id': None,
                    'project_name': None,
                    'subzone_id': None,
                    'subzone_name': None,
                })

        return sorted(rows, key=lambda row: (row['driver_name'] or '').lower())

    @staticmethod
    def get_available_vehicles(project_id=None, subzone_id=None):
        """Get list of available vehicles for assignment"""
        AssignmentDashboardService.normalize_released_vehicle_state()

        active_deployment_exists = db.session.query(VehicleDeployment.id).filter(
            VehicleDeployment.vehicle_id == Vehicle.id,
            VehicleDeployment.status.in_(['Pending', 'Approved', 'Active']),
        ).exists()

        query = Vehicle.query.filter(
            Vehicle.status == 'Available',
            Vehicle.assigned_driver_id.is_(None),
            ~active_deployment_exists,
        )
        
        if project_id:
            query = query.filter_by(project_id=project_id)
        if subzone_id:
            query = query.filter_by(subzone_id=subzone_id)
        
        vehicles = query.all()
        return [
            {
                'vehicle_id': v.id,
                'vehicle_number': v.vehicle_number,
                'vehicle_type': v.vehicle_type,
                'insurance_status': v.insurance_status,
                'fitness_status': v.fitness_status,
                'puc_status': v.puc_status,
                'project_id': v.project_id,
                'project_name': v.project.project_name if v.project else None,
                'subzone_id': v.subzone_id,
                'subzone_name': v.subzone.subzone_name if v.subzone else None,
            }
            for v in vehicles
        ]
