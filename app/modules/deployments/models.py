"""
Vehicle Deployment Models

Normalized deployment entities tracking vehicle/driver assignments,
route operations, approvals, and audit trails.
"""

import uuid
from datetime import datetime, timezone

from app.extensions import db


def make_uuid():
    return str(uuid.uuid4())


class VehicleDeployment(db.Model):
    """
    Represents a single vehicle deployment operation.
    
    A deployment is a specific assignment of a vehicle to a driver/route
    with approval workflow, compliance checks, and audit logging.
    """
    __tablename__ = 'vehicle_deployments'
    __table_args__ = (
        db.Index('idx_deployments_vehicle_id', 'vehicle_id'),
        db.Index('idx_deployments_driver_id', 'driver_id'),
        db.Index('idx_deployments_status', 'status'),
        db.Index('idx_deployments_created_at', 'created_at'),
    )

    id = db.Column(db.String(36), primary_key=True, default=make_uuid)
    
    # Core References
    vehicle_id = db.Column(db.String(36), db.ForeignKey('vehicles.id', ondelete='CASCADE'), nullable=False, index=True)
    driver_id = db.Column(db.String(36), db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True)
    project_id = db.Column(db.String(36), db.ForeignKey('projects.id', ondelete='SET NULL'), nullable=True, index=True)
    subzone_id = db.Column(db.String(36), db.ForeignKey('subzones.id', ondelete='SET NULL'), nullable=True, index=True)

    # Deployment Details
    deployment_type = db.Column(db.String(50), nullable=False, default='Standard')  # Standard, Express, Special, etc.
    route_name = db.Column(db.String(255), nullable=True)
    pickup_location = db.Column(db.String(255), nullable=True)
    dropoff_location = db.Column(db.String(255), nullable=True)
    
    # Operational Status
    status = db.Column(db.String(30), nullable=False, default='Pending')  # Pending, Approved, Active, Completed, Cancelled
    current_location = db.Column(db.String(255), nullable=True)
    
    # Timeline
    scheduled_start = db.Column(db.DateTime(timezone=True), nullable=True)
    actual_start = db.Column(db.DateTime(timezone=True), nullable=True)
    scheduled_end = db.Column(db.DateTime(timezone=True), nullable=True)
    actual_end = db.Column(db.DateTime(timezone=True), nullable=True)
    
    # Operational Metrics
    distance_km = db.Column(db.Float, nullable=True, default=0)
    duration_minutes = db.Column(db.Integer, nullable=True, default=0)
    fuel_consumed = db.Column(db.Float, nullable=True, default=0)
    
    # Approval Workflow
    approval_status = db.Column(db.String(30), nullable=False, default='Pending')  # Pending, Approved, Rejected, Escalated
    approved_by = db.Column(db.String(36), db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    approval_timestamp = db.Column(db.DateTime(timezone=True), nullable=True)
    rejection_reason = db.Column(db.String(512), nullable=True)
    
    # Compliance & Validation
    vehicle_fitness_verified = db.Column(db.Boolean, default=False)
    driver_license_verified = db.Column(db.Boolean, default=False)
    insurance_verified = db.Column(db.Boolean, default=False)
    safety_checklist_completed = db.Column(db.Boolean, default=False)
    
    # Notes & Metadata
    notes = db.Column(db.Text, nullable=True)
    special_instructions = db.Column(db.Text, nullable=True)
    
    # Audit Trail
    created_by = db.Column(db.String(36), db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    vehicle = db.relationship('Vehicle', foreign_keys=[vehicle_id], backref='deployments', lazy='joined')
    driver = db.relationship('User', foreign_keys=[driver_id], lazy='joined')
    project = db.relationship('Project', foreign_keys=[project_id], lazy='joined')
    subzone = db.relationship('Subzone', foreign_keys=[subzone_id], lazy='joined')
    approver = db.relationship('User', foreign_keys=[approved_by], lazy='joined')
    creator = db.relationship('User', foreign_keys=[created_by], lazy='joined')

    def to_dict(self):
        """Serialize deployment to dictionary"""
        # Resolve active helpers assigned to this deployment's vehicle or project+subzone
        from app.modules.deployments.models import HelperAssignment
        active_helpers = HelperAssignment.query.filter(
            HelperAssignment.status == 'Active',
            db.or_(
                HelperAssignment.assigned_vehicle_id == self.vehicle_id,
                db.and_(
                    HelperAssignment.project_id == self.project_id,
                    HelperAssignment.subzone_id == self.subzone_id,
                    HelperAssignment.assigned_vehicle_id == None
                )
            )
        ).all()
        helper_names = [ha.helper.username for ha in active_helpers if ha.helper]

        return {
            'id': self.id,
            'vehicle_id': self.vehicle_id,
            'vehicle_number': self.vehicle.vehicle_number if self.vehicle else None,
            'driver_id': self.driver_id,
            'driver_name': self.driver.username if self.driver else None,
            'project_id': self.project_id,
            'project_name': self.project.project_name if self.project else None,
            'subzone_id': self.subzone_id,
            'subzone_name': self.subzone.subzone_name if self.subzone else None,
            'deployment_type': self.deployment_type,
            'route_name': self.route_name,
            'pickup_location': self.pickup_location,
            'dropoff_location': self.dropoff_location,
            'status': self.status,
            'current_location': self.current_location,
            'approval_status': self.approval_status,
            'scheduled_start': self.scheduled_start.isoformat() if self.scheduled_start else None,
            'actual_start': self.actual_start.isoformat() if self.actual_start else None,
            'scheduled_end': self.scheduled_end.isoformat() if self.scheduled_end else None,
            'actual_end': self.actual_end.isoformat() if self.actual_end else None,
            'distance_km': self.distance_km,
            'duration_minutes': self.duration_minutes,
            'fuel_consumed': self.fuel_consumed,
            'vehicle_fitness_verified': self.vehicle_fitness_verified,
            'driver_license_verified': self.driver_license_verified,
            'insurance_verified': self.insurance_verified,
            'safety_checklist_completed': self.safety_checklist_completed,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'assigned_helpers': ", ".join(helper_names) if helper_names else "None",
            'helper_count': len(active_helpers),
        }

    def __repr__(self):
        return f'<VehicleDeployment {self.id} {self.status}>'


class DeploymentApprovalLog(db.Model):
    """
    Audit trail for deployment approvals, rejections, and escalations.
    """
    __tablename__ = 'deployment_approval_logs'
    __table_args__ = (
        db.Index('idx_approval_deployment_id', 'deployment_id'),
        db.Index('idx_approval_created_at', 'created_at'),
    )

    id = db.Column(db.String(36), primary_key=True, default=make_uuid)
    deployment_id = db.Column(db.String(36), db.ForeignKey('vehicle_deployments.id', ondelete='CASCADE'), nullable=False, index=True)
    action = db.Column(db.String(50), nullable=False)  # approved, rejected, escalated, overridden
    actor_id = db.Column(db.String(36), db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    reason = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    deployment = db.relationship('VehicleDeployment', lazy='joined')
    actor = db.relationship('User', foreign_keys=[actor_id], lazy='joined')

    def __repr__(self):
        return f'<DeploymentApprovalLog {self.action}>'


class HelperAssignment(db.Model):
    """
    Represents an assignment of a Helper to a Circle -> Project -> Subzone
    """
    __tablename__ = 'helper_assignments'
    __table_args__ = (
        db.Index('idx_helper_assignments_helper_id', 'helper_id'),
        db.Index('idx_helper_assignments_status', 'status'),
    )

    id = db.Column(db.String(36), primary_key=True, default=make_uuid)
    
    # Core References
    helper_id = db.Column(db.String(36), db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    circle_id = db.Column(db.String(36), db.ForeignKey('circles.id', ondelete='SET NULL'), nullable=True)
    project_id = db.Column(db.String(36), db.ForeignKey('projects.id', ondelete='SET NULL'), nullable=True)
    subzone_id = db.Column(db.String(36), db.ForeignKey('subzones.id', ondelete='SET NULL'), nullable=True)
    
    # Assignment Details
    shift = db.Column(db.String(50), nullable=True)
    start_date = db.Column(db.Date, nullable=False, default=lambda: datetime.now(timezone.utc).date())
    end_date = db.Column(db.Date, nullable=True)
    status = db.Column(db.String(30), nullable=False, default='Active')  # Active, Ended
    remarks = db.Column(db.Text, nullable=True)
    
    # Optional fields
    assigned_driver_id = db.Column(db.String(36), db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    assigned_vehicle_id = db.Column(db.String(36), db.ForeignKey('vehicles.id', ondelete='SET NULL'), nullable=True)

    # Audit Trail
    created_by = db.Column(db.String(36), db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    helper = db.relationship('User', foreign_keys=[helper_id], backref=db.backref('helper_assignments', lazy='dynamic'))
    circle = db.relationship('Circle', foreign_keys=[circle_id], lazy='joined')
    project = db.relationship('Project', foreign_keys=[project_id], lazy='joined')
    subzone = db.relationship('Subzone', foreign_keys=[subzone_id], lazy='joined')
    assigned_driver = db.relationship('User', foreign_keys=[assigned_driver_id], lazy='joined')
    assigned_vehicle = db.relationship('Vehicle', foreign_keys=[assigned_vehicle_id], lazy='joined')
    creator = db.relationship('User', foreign_keys=[created_by], lazy='joined')

    def to_dict(self):
        return {
            'id': self.id,
            'helper_id': self.helper_id,
            'helper_name': self.helper.username if self.helper else None,
            'circle_id': self.circle_id,
            'circle_name': self.circle.circle_name if self.circle else None,
            'project_id': self.project_id,
            'project_name': self.project.project_name if self.project else None,
            'subzone_id': self.subzone_id,
            'subzone_name': self.subzone.subzone_name if self.subzone else None,
            'shift': self.shift,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'status': self.status,
            'remarks': self.remarks,
            'assigned_driver_id': self.assigned_driver_id,
            'assigned_driver_name': self.assigned_driver.username if self.assigned_driver else None,
            'assigned_vehicle_id': self.assigned_vehicle_id,
            'assigned_vehicle_number': self.assigned_vehicle.vehicle_number if self.assigned_vehicle else None,
            'created_by': self.created_by,
            'created_by_name': self.creator.username if self.creator else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
