import uuid
from datetime import datetime, timezone

from app.extensions import db


def make_uuid():
    return str(uuid.uuid4())


class Project(db.Model):
    __tablename__ = 'projects'
    __table_args__ = (
        db.UniqueConstraint('company_id', 'circle_id', 'client_id', 'project_code', name='uix_project_code'),
        db.Index('idx_company_id', 'company_id'),
        db.Index('idx_circle_id', 'circle_id'),
        db.Index('idx_client_id', 'client_id'),
        db.Index('idx_status', 'status'),
    )

    id = db.Column(db.String(36), primary_key=True, default=make_uuid)
    company_id = db.Column(db.String(36), db.ForeignKey('companies.id'), nullable=False, index=True)
    circle_id = db.Column(db.String(36), db.ForeignKey('circles.id'), nullable=False, index=True)
    client_id = db.Column(db.String(36), db.ForeignKey('clients.id'), nullable=False, index=True)
    
    # Basic Information
    project_code = db.Column(db.String(20), nullable=False, index=True)
    project_name = db.Column(db.String(150), nullable=False)
    project_type = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='Active')
    
    # Timeline
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=True)
    expected_completion_date = db.Column(db.Date, nullable=True)
    operational_shift = db.Column(db.String(50), nullable=True)
    
    # Location
    country = db.Column(db.String(100), nullable=True)
    state = db.Column(db.String(100), nullable=True)
    city = db.Column(db.String(100), nullable=True)
    pincode = db.Column(db.String(10), nullable=True)
    full_address = db.Column(db.Text, nullable=True)
    
    # Operational Configuration
    deployment_allowed = db.Column(db.Boolean, default=True)
    attendance_required = db.Column(db.Boolean, default=True)
    gps_tracking_enabled = db.Column(db.Boolean, default=False)
    realtime_monitoring_enabled = db.Column(db.Boolean, default=False)
    geo_fencing_enabled = db.Column(db.Boolean, default=False)
    workflow_approval_enabled = db.Column(db.Boolean, default=False)
    document_verification_required = db.Column(db.Boolean, default=False)
    shift_based_attendance = db.Column(db.Boolean, default=False)
    
    # Resource Configuration
    max_vehicles = db.Column(db.Integer, nullable=True)
    max_drivers = db.Column(db.Integer, nullable=True)
    deployment_capacity = db.Column(db.Integer, nullable=True)
    required_vehicle_types = db.Column(db.String(255), nullable=True)
    operational_capacity = db.Column(db.Integer, nullable=True)
    
    # Project Management
    project_manager = db.Column(db.String(150), nullable=True)
    operational_head = db.Column(db.String(150), nullable=True)
    contact_number = db.Column(db.String(15), nullable=True)
    operational_email = db.Column(db.String(120), nullable=True)
    
    # Audit
    created_by = db.Column(db.String(36), nullable=True, index=True)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_by = db.Column(db.String(36), nullable=True)

    # Relationships
    company = db.relationship('Company', foreign_keys=[company_id], lazy='joined')
    circle = db.relationship('Circle', foreign_keys=[circle_id], lazy='joined')
    client = db.relationship('Client', foreign_keys=[client_id], lazy='joined')

    def to_dict(self):
        return {
            'id': self.id,
            'company_id': self.company_id,
            'circle_id': self.circle_id,
            'client_id': self.client_id,
            'project_code': self.project_code,
            'project_name': self.project_name,
            'project_type': self.project_type,
            'status': self.status,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'expected_completion_date': self.expected_completion_date.isoformat() if self.expected_completion_date else None,
            'operational_shift': self.operational_shift,
            'country': self.country,
            'state': self.state,
            'city': self.city,
            'pincode': self.pincode,
            'full_address': self.full_address,
            'deployment_allowed': self.deployment_allowed,
            'attendance_required': self.attendance_required,
            'gps_tracking_enabled': self.gps_tracking_enabled,
            'realtime_monitoring_enabled': self.realtime_monitoring_enabled,
            'geo_fencing_enabled': self.geo_fencing_enabled,
            'workflow_approval_enabled': self.workflow_approval_enabled,
            'document_verification_required': self.document_verification_required,
            'shift_based_attendance': self.shift_based_attendance,
            'max_vehicles': self.max_vehicles,
            'max_drivers': self.max_drivers,
            'deployment_capacity': self.deployment_capacity,
            'required_vehicle_types': self.required_vehicle_types,
            'operational_capacity': self.operational_capacity,
            'project_manager': self.project_manager,
            'operational_head': self.operational_head,
            'contact_number': self.contact_number,
            'operational_email': self.operational_email,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self):
        return f'<Project {self.project_code}>'

