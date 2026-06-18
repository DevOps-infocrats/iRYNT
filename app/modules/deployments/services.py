"""
Deployment Service

Business logic for deployment operations, approvals, and validations.
"""

from datetime import datetime, timezone
from app.modules.deployments.repository import DeploymentRepository
from app.modules.vehicles.models import Vehicle
from app.modules.auth.models import User
from app.extensions import db
from app.services.compliance.deployment_validation_service import DeploymentValidationService
from app.modules.notifications.helpers import create_notification_safe


class DeploymentService:
    """Service layer for deployment operations"""

    def __init__(self):
        self.repository = DeploymentRepository()
        self.validation_service = DeploymentValidationService()

    def list_deployments(self, filters=None, page=1, per_page=20):
        """List deployments with pagination"""
        offset = (page - 1) * per_page
        deployments, total = self.repository.list_deployments(filters, offset, per_page)
        
        return {
            'deployments': [d.to_dict() for d in deployments],
            'total': total,
            'page': page,
            'per_page': per_page,
            'pages': (total + per_page - 1) // per_page
        }

    def get_deployment(self, deployment_id):
        """Get deployment details"""
        deployment = self.repository.get_deployment(deployment_id)
        if not deployment:
            return None
        
        return {
            'deployment': deployment.to_dict(),
            'approval_logs': [
                {
                    'action': log.action,
                    'actor': log.actor.username if log.actor else 'System',
                    'reason': log.reason,
                    'timestamp': log.created_at.isoformat() if log.created_at else None,
                }
                for log in self.repository.get_approval_logs(deployment_id)
            ]
        }

    def create_deployment(self, payload, created_by_user_id):
        """Create new deployment with validation"""
        # Validate vehicle exists
        vehicle = Vehicle.query.get(payload['vehicle_id'])
        if not vehicle:
            return None, 'Vehicle not found'

        # Validate vehicle status
        if vehicle.status not in ['Available', 'Assigned']:
            return None, f'Vehicle is {vehicle.status}, cannot deploy'

        # Validate driver if provided
        if payload.get('driver_id'):
            driver = User.query.get(payload['driver_id'])
            if not driver:
                return None, 'Driver not found'

        # Ensure vehicle can be deployed
        if not vehicle.deployment_allowed:
            return None, 'This vehicle cannot be deployed'

        # Run centralized validation checks (driver + vehicle + assignment)
        try:
            validation = self.validation_service.validate_deployment(
                driver_id=payload.get('driver_id'),
                vehicle_id=payload.get('vehicle_id'),
                project_id=payload.get('project_id'),
                subzone_id=payload.get('subzone_id'),
            )
        except Exception as e:
            return None, f'Validation service error: {e}'

        if not validation.get('is_valid', False):
            return None, 'Validation failed: ' + '; '.join(validation.get('blocking_issues', []))

        # Add metadata
        payload['created_by'] = created_by_user_id
        # Auto-approve deployments on creation (no request/approval flow)
        payload['status'] = 'Active'
        payload['approval_status'] = 'Approved'
        payload['approved_by'] = created_by_user_id
        payload['approval_timestamp'] = datetime.now(timezone.utc)

        deployment = self.repository.create_deployment(payload)
        
        # Update vehicle status to reflect deployment assignment
        vehicle.current_deployment = deployment.id

        # Double validation right before commit
        try:
            revalidation = self.validation_service.validate_deployment(
                driver_id=deployment.driver_id,
                vehicle_id=deployment.vehicle_id,
                project_id=deployment.project_id,
                subzone_id=deployment.subzone_id,
            )
            if not revalidation.get('is_valid', False):
                db.session.rollback()
                return None, 'Revalidation failed before commit: ' + '; '.join(revalidation.get('blocking_issues', []))
        except Exception as e:
            db.session.rollback()
            return None, f'Revalidation service error: {e}'

        db.session.commit()
        # Add approval log to preserve audit trail (auto-approved)
        try:
            self.repository.add_approval_log(deployment.id, 'approved', created_by_user_id, 'Auto-approved on creation')
        except Exception:
            # Keep create flow resilient; do not block on logging
            pass
        # Safe notification: notify driver if assigned
        try:
            if deployment.driver_id:
                create_notification_safe(
                    user_id=deployment.driver_id,
                    message=f"You have been assigned a deployment: {deployment.id}",
                    module='deployments',
                    priority='Info',
                    related_type='deployment',
                    related_id=str(deployment.id),
                    route=f"/deployments/{deployment.id}",
                    metadata={'deployment_id': deployment.id}
                )
        except Exception:
            pass
        
        return deployment, None

    def approve_deployment(self, deployment_id, approved_by_user_id, reason=None):
        """Approve deployment for execution"""
        deployment = self.repository.get_deployment(deployment_id)
        if not deployment:
            return None, 'Deployment not found'

        if deployment.approval_status != 'Pending':
            return None, f'Cannot approve: status is {deployment.approval_status}'

        # Validate vehicle/driver fitness
        errors = self._validate_deployment_fitness(deployment)
        if errors:
            return None, f'Validation failed: {"; ".join(errors)}'

        # Update deployment
        update_payload = {
            'approval_status': 'Approved',
            'approved_by': approved_by_user_id,
            'approval_timestamp': datetime.now(timezone.utc),
        }
        deployment = self.repository.update_deployment(deployment_id, update_payload)

        # Log approval action
        self.repository.add_approval_log(
            deployment_id, 'approved', approved_by_user_id, reason
        )

        return deployment, None

    def reject_deployment(self, deployment_id, rejected_by_user_id, reason):
        """Reject deployment"""
        deployment = self.repository.get_deployment(deployment_id)
        if not deployment:
            return None, 'Deployment not found'

        if deployment.approval_status != 'Pending':
            return None, f'Cannot reject: status is {deployment.approval_status}'

        # Update deployment
        update_payload = {
            'approval_status': 'Rejected',
            'rejection_reason': reason,
            'status': 'Cancelled',
        }
        deployment = self.repository.update_deployment(deployment_id, update_payload)

        # Clear vehicle deployment
        vehicle = deployment.vehicle
        if vehicle and vehicle.current_deployment == deployment_id:
            vehicle.current_deployment = None
            db.session.commit()

        # Log rejection
        self.repository.add_approval_log(
            deployment_id, 'rejected', rejected_by_user_id, reason
        )

        return deployment, None

    def escalate_deployment(self, deployment_id, escalated_by_user_id, reason=None):
        """Escalate deployment approval request"""
        deployment = self.repository.get_deployment(deployment_id)
        if not deployment:
            return None, 'Deployment not found'

        if deployment.approval_status != 'Pending':
            return None, f'Cannot escalate: status is {deployment.approval_status}'

        update_payload = {
            'approval_status': 'Escalated',
            'rejection_reason': reason,
        }
        deployment = self.repository.update_deployment(deployment_id, update_payload)
        self.repository.add_approval_log(
            deployment_id, 'escalated', escalated_by_user_id, reason
        )
        # Safe notification: inform creator and driver about escalation
        try:
            if deployment.created_by:
                create_notification_safe(
                    user_id=deployment.created_by,
                    message=f"Deployment {deployment.id} has been escalated for review.",
                    module='deployments',
                    priority='High',
                    related_type='deployment',
                    related_id=str(deployment.id),
                    route=f"/deployments/{deployment.id}",
                    metadata={'deployment_id': deployment.id}
                )
            if deployment.driver_id:
                create_notification_safe(
                    user_id=deployment.driver_id,
                    message=f"Your deployment {deployment.id} has been escalated.",
                    module='deployments',
                    priority='Info',
                    related_type='deployment',
                    related_id=str(deployment.id),
                    route=f"/deployments/{deployment.id}",
                    metadata={'deployment_id': deployment.id}
                )
        except Exception:
            pass
        return deployment, None

    def start_deployment(self, deployment_id):
        """Mark deployment as active (operation started)"""
        deployment = self.repository.get_deployment(deployment_id)
        if not deployment:
            return None, 'Deployment not found'

        if deployment.approval_status != 'Approved':
            return None, 'Deployment must be approved before starting'

        update_payload = {
            'status': 'Active',
            'actual_start': datetime.now(timezone.utc),
        }
        deployment = self.repository.update_deployment(deployment_id, update_payload)

        return deployment, None

    def complete_deployment(self, deployment_id, payload=None):
        """Mark deployment as completed with metrics"""
        deployment = self.repository.get_deployment(deployment_id)
        if not deployment:
            return None, 'Deployment not found'

        if deployment.status != 'Active':
            return None, f'Cannot complete: status is {deployment.status}'

        payload = payload or {}
        update_payload = {
            'status': 'Completed',
            'actual_end': datetime.now(timezone.utc),
            'distance_km': payload.get('distance_km'),
            'duration_minutes': payload.get('duration_minutes'),
            'fuel_consumed': payload.get('fuel_consumed'),
            'notes': payload.get('notes'),
        }
        deployment = self.repository.update_deployment(deployment_id, update_payload)

        # Clear vehicle deployment
        vehicle = deployment.vehicle
        if vehicle and vehicle.current_deployment == deployment_id:
            vehicle.current_deployment = None
            db.session.commit()

        return deployment, None

    def get_active_deployments(self, page=1, per_page=20):
        """Get all active deployments"""
        offset = (page - 1) * per_page
        deployments, total = self.repository.get_active_deployments(offset, per_page)

        return {
            'deployments': [d.to_dict() for d in deployments],
            'total': total,
            'page': page,
            'per_page': per_page,
        }

    def get_pending_approvals(self, page=1, per_page=20):
        """Get deployments awaiting approval"""
        offset = (page - 1) * per_page
        deployments, total = self.repository.get_pending_approvals(offset, per_page)

        return {
            'deployments': [d.to_dict() for d in deployments],
            'total': total,
            'page': page,
            'per_page': per_page,
        }

    def get_deployment_history(self, vehicle_id=None, driver_id=None, page=1, per_page=20):
        """Get completed/cancelled deployment history"""
        offset = (page - 1) * per_page
        deployments, total = self.repository.get_deployment_history(
            vehicle_id, driver_id, offset, per_page
        )

        return {
            'deployments': [d.to_dict() for d in deployments],
            'total': total,
            'page': page,
            'per_page': per_page,
        }

    def get_deployment_stats(self, filters=None):
        """Get deployment statistics"""
        return self.repository.get_deployment_stats(filters)

    def _validate_deployment_fitness(self, deployment):
        """Validate vehicle and driver fitness for deployment"""
        errors = []

        # Validate vehicle compliance
        vehicle = deployment.vehicle
        if vehicle:
            if vehicle.insurance_status != 'Valid':
                errors.append('Vehicle insurance not valid')
            if vehicle.fitness_status != 'Valid':
                errors.append('Vehicle fitness not valid')
            if vehicle.puc_status != 'Valid':
                errors.append('Vehicle PUC not valid')

        # Validate driver if present
        driver = deployment.driver
        if driver and hasattr(driver, 'driver_profile') and driver.driver_profile:
            profile = driver.driver_profile
            # Driver license and compliance checks bypassed per user request
            # if profile.license_status != 'Verified':
            #     errors.append('Driver license not verified')
            # if profile.compliance_status != 'Verified':
            #     errors.append('Driver compliance not verified')
            pass

        return errors
