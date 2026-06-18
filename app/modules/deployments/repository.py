"""
Deployment Repository

Data access layer for deployment operations, queries, and persistence.
"""

from sqlalchemy import or_, and_, func
from app.extensions import db
from app.modules.deployments.models import VehicleDeployment, DeploymentApprovalLog


class DeploymentRepository:
    """Repository for deployment data access"""

    def get_deployment(self, deployment_id):
        """Get deployment by ID"""
        return VehicleDeployment.query.filter_by(id=deployment_id).first()

    def list_deployments(self, filters=None, offset=0, limit=20):
        """List deployments with optional filters"""
        filters = filters or {}
        query = VehicleDeployment.query.order_by(VehicleDeployment.created_at.desc())

        if filters.get('vehicle_id'):
            query = query.filter_by(vehicle_id=filters['vehicle_id'])
        if filters.get('driver_id'):
            query = query.filter_by(driver_id=filters['driver_id'])
        if filters.get('status'):
            query = query.filter_by(status=filters['status'])
        if filters.get('approval_status'):
            query = query.filter_by(approval_status=filters['approval_status'])
        if filters.get('project_id'):
            query = query.filter_by(project_id=filters['project_id'])
        if filters.get('subzone_id'):
            query = query.filter_by(subzone_id=filters['subzone_id'])

        total = query.count()
        deployments = query.offset(offset).limit(limit).all()
        return deployments, total

    def create_deployment(self, payload):
        """Create new deployment"""
        deployment = VehicleDeployment(**payload)
        db.session.add(deployment)
        db.session.commit()
        return deployment

    def update_deployment(self, deployment_id, payload):
        """Update deployment"""
        deployment = self.get_deployment(deployment_id)
        if not deployment:
            return None

        for key, value in payload.items():
            setattr(deployment, key, value)

        db.session.commit()
        return deployment

    def delete_deployment(self, deployment_id):
        """Delete deployment (soft delete via status)"""
        deployment = self.get_deployment(deployment_id)
        if not deployment:
            return False

        deployment.status = 'Cancelled'
        db.session.commit()
        return True

    def get_active_deployments(self, offset=0, limit=20):
        """Get active deployments"""
        query = VehicleDeployment.query.filter(
            VehicleDeployment.status.in_(['Active', 'Approved'])
        ).order_by(VehicleDeployment.scheduled_start)

        total = query.count()
        deployments = query.offset(offset).limit(limit).all()
        return deployments, total

    def get_pending_approvals(self, offset=0, limit=20):
        """Get deployments pending approval"""
        query = VehicleDeployment.query.filter(
            VehicleDeployment.approval_status.in_(['Pending', 'Escalated'])
        ).order_by(VehicleDeployment.created_at)

        total = query.count()
        deployments = query.offset(offset).limit(limit).all()
        return deployments, total

    def get_deployment_history(self, vehicle_id=None, driver_id=None, offset=0, limit=20):
        """Get historical deployments"""
        query = VehicleDeployment.query.filter(
            VehicleDeployment.status.in_(['Completed', 'Cancelled'])
        ).order_by(VehicleDeployment.actual_end.desc())

        if vehicle_id:
            query = query.filter_by(vehicle_id=vehicle_id)
        if driver_id:
            query = query.filter_by(driver_id=driver_id)

        total = query.count()
        deployments = query.offset(offset).limit(limit).all()
        return deployments, total

    def get_vehicle_current_deployment(self, vehicle_id):
        """Get current/active deployment for vehicle"""
        return VehicleDeployment.query.filter_by(
            vehicle_id=vehicle_id,
            status='Active'
        ).order_by(VehicleDeployment.actual_start.desc()).first()

    def get_driver_current_deployment(self, driver_id):
        """Get current/active deployment for driver"""
        return VehicleDeployment.query.filter_by(
            driver_id=driver_id,
            status='Active'
        ).order_by(VehicleDeployment.actual_start.desc()).first()

    def count_active_deployments(self, filters=None):
        """Count active deployments"""
        filters = filters or {}
        query = VehicleDeployment.query.filter_by(status='Active')

        if filters.get('project_id'):
            query = query.filter_by(project_id=filters['project_id'])
        if filters.get('subzone_id'):
            query = query.filter_by(subzone_id=filters['subzone_id'])

        return query.count()

    def get_approval_logs(self, deployment_id):
        """Get approval audit trail for deployment"""
        return DeploymentApprovalLog.query.filter_by(
            deployment_id=deployment_id
        ).order_by(DeploymentApprovalLog.created_at.desc()).all()

    def add_approval_log(self, deployment_id, action, actor_id, reason=None):
        """Add approval action to audit trail"""
        log = DeploymentApprovalLog(
            deployment_id=deployment_id,
            action=action,
            actor_id=actor_id,
            reason=reason
        )
        db.session.add(log)
        db.session.commit()
        return log

    def get_deployment_stats(self, filters=None):
        """Get deployment statistics"""
        filters = filters or {}
        query = VehicleDeployment.query

        if filters.get('project_id'):
            query = query.filter_by(project_id=filters['project_id'])
        if filters.get('subzone_id'):
            query = query.filter_by(subzone_id=filters['subzone_id'])

        total = query.count()
        active = query.filter_by(status='Active').count()
        pending_approval = query.filter_by(approval_status='Pending').count()
        completed = query.filter_by(status='Completed').count()

        return {
            'total': total,
            'active': active,
            'pending_approval': pending_approval,
            'completed': completed,
        }
