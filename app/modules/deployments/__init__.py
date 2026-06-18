"""
Deployments Module

Complete vehicle deployment management system with:
- Normalized VehicleDeployment model
- Approval workflow and audit trail
- Integration with vehicle & driver management
- Permission-based access control
"""

from app.modules.deployments.models import VehicleDeployment, DeploymentApprovalLog
from app.modules.deployments.repository import DeploymentRepository
from app.modules.deployments.services import DeploymentService
from app.modules.deployments.routes import deployments_bp

__all__ = [
    'VehicleDeployment',
    'DeploymentApprovalLog',
    'DeploymentRepository',
    'DeploymentService',
    'deployments_bp',
]