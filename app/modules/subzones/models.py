import uuid
from datetime import datetime, timezone

from app.extensions import db


def make_uuid():
    return str(uuid.uuid4())


class Subzone(db.Model):
    __tablename__ = 'subzones'
    __table_args__ = (
        db.UniqueConstraint('company_id', 'circle_id', 'client_id', 'project_id', 'subzone_code', name='uix_subzone_code'),
    )

    id = db.Column(db.String(36), primary_key=True, default=make_uuid)
    company_id = db.Column(db.String(36), db.ForeignKey('companies.id'), nullable=False, index=True)
    circle_id = db.Column(db.String(36), db.ForeignKey('circles.id'), nullable=False, index=True)
    client_id = db.Column(db.String(36), db.ForeignKey('clients.id'), nullable=False, index=True)
    project_id = db.Column(db.String(36), db.ForeignKey('projects.id'), nullable=False, index=True)

    subzone_code = db.Column(db.String(20), nullable=False, index=True)
    subzone_name = db.Column(db.String(150), nullable=False)
    subzone_type = db.Column(db.String(50), nullable=True)
    status = db.Column(db.String(20), nullable=False, default='Active', index=True)

    country = db.Column(db.String(100), nullable=True)
    state = db.Column(db.String(100), nullable=True)
    city = db.Column(db.String(100), nullable=True)
    pincode = db.Column(db.String(10), nullable=True)
    full_address = db.Column(db.Text, nullable=True)
    latitude = db.Column(db.String(20), nullable=True)
    longitude = db.Column(db.String(20), nullable=True)

    geo_fencing_enabled = db.Column(db.Boolean, default=False)
    allowed_radius = db.Column(db.Integer, nullable=True)
    attendance_radius = db.Column(db.Integer, nullable=True)
    gps_validation = db.Column(db.Boolean, default=False)
    restricted_movement_detection = db.Column(db.Boolean, default=False)

    max_vehicles = db.Column(db.Integer, nullable=True)
    max_drivers = db.Column(db.Integer, nullable=True)
    shift_operations_enabled = db.Column(db.Boolean, default=False)
    attendance_required = db.Column(db.Boolean, default=False)
    deployment_allowed = db.Column(db.Boolean, default=False)
    realtime_tracking_enabled = db.Column(db.Boolean, default=False)
    workflow_approval_enabled = db.Column(db.Boolean, default=False)
    incident_reporting_enabled = db.Column(db.Boolean, default=False)

    vehicle_capacity = db.Column(db.Integer, nullable=True)
    driver_capacity = db.Column(db.Integer, nullable=True)
    parking_capacity = db.Column(db.Integer, nullable=True)
    operational_capacity = db.Column(db.Integer, nullable=True)

    created_by = db.Column(db.String(36), nullable=True, index=True)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    company = db.relationship('Company', foreign_keys=[company_id], lazy='joined')
    circle = db.relationship('Circle', foreign_keys=[circle_id], lazy='joined')
    client = db.relationship('Client', foreign_keys=[client_id], lazy='joined')
    project = db.relationship('Project', foreign_keys=[project_id], lazy='joined')

    @property
    def allowed_radius_meters(self):
        return self.attendance_radius or self.allowed_radius

    @allowed_radius_meters.setter
    def allowed_radius_meters(self, value):
        self.attendance_radius = value

    def to_dict(self):
        return {
            'id': self.id,
            'company_id': self.company_id,
            'circle_id': self.circle_id,
            'client_id': self.client_id,
            'project_id': self.project_id,
            'subzone_code': self.subzone_code,
            'subzone_name': self.subzone_name,
            'subzone_type': self.subzone_type,
            'status': self.status,
            'country': self.country,
            'state': self.state,
            'city': self.city,
            'pincode': self.pincode,
            'full_address': self.full_address,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'geo_fencing_enabled': self.geo_fencing_enabled,
            'allowed_radius': self.allowed_radius,
            'attendance_radius': self.attendance_radius,
            'allowed_radius_meters': self.allowed_radius_meters,
            'gps_validation': self.gps_validation,
            'restricted_movement_detection': self.restricted_movement_detection,
            'max_vehicles': self.max_vehicles,
            'max_drivers': self.max_drivers,
            'shift_operations_enabled': self.shift_operations_enabled,
            'attendance_required': self.attendance_required,
            'deployment_allowed': self.deployment_allowed,
            'realtime_tracking_enabled': self.realtime_tracking_enabled,
            'workflow_approval_enabled': self.workflow_approval_enabled,
            'incident_reporting_enabled': self.incident_reporting_enabled,
            'vehicle_capacity': self.vehicle_capacity,
            'driver_capacity': self.driver_capacity,
            'parking_capacity': self.parking_capacity,
            'operational_capacity': self.operational_capacity,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self):
        return f'<Subzone {self.subzone_code}>'

