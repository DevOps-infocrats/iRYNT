import uuid
from datetime import datetime, timezone

from app.extensions import db


def make_uuid():
    return str(uuid.uuid4())


class Vehicle(db.Model):
    __tablename__ = 'vehicles'
    __table_args__ = (
        db.UniqueConstraint(
            'company_id', 'circle_id', 'client_id', 'project_id', 'subzone_id', 'vehicle_number',
            name='uix_vehicle_number'
        ),
        db.Index('idx_vehicles_vehicle_number', 'vehicle_number'),
        db.Index('idx_vehicles_company_id', 'company_id'),
        db.Index('idx_vehicles_circle_id', 'circle_id'),
        db.Index('idx_vehicles_client_id', 'client_id'),
        db.Index('idx_vehicles_project_id', 'project_id'),
        db.Index('idx_vehicles_subzone_id', 'subzone_id'),
        db.Index('idx_vehicles_status', 'status'),
    )

    id = db.Column(db.String(36), primary_key=True, default=make_uuid)
    company_id = db.Column(db.String(36), db.ForeignKey('companies.id'), nullable=False)
    circle_id = db.Column(db.String(36), db.ForeignKey('circles.id'), nullable=False)
    client_id = db.Column(db.String(36), db.ForeignKey('clients.id'), nullable=False)
    project_id = db.Column(db.String(36), db.ForeignKey('projects.id'), nullable=False)
    subzone_id = db.Column(db.String(36), db.ForeignKey('subzones.id'), nullable=False)

    vehicle_number = db.Column(db.String(20), nullable=False)
    vehicle_type = db.Column(db.String(50), nullable=False)
    vehicle_category = db.Column(db.String(50), nullable=False)
    vehicle_brand = db.Column(db.String(100), nullable=False)
    vehicle_model = db.Column(db.String(100), nullable=False)
    manufacturing_year = db.Column(db.String(4), nullable=True)
    chassis_number = db.Column(db.String(100), unique=True, nullable=True)
    engine_number = db.Column(db.String(100), unique=True, nullable=True)

    owner_name = db.Column(db.String(120), nullable=True)
    owner_phone = db.Column(db.String(15), nullable=True)
    vendor_name = db.Column(db.String(120), nullable=True)
    vendor_contact = db.Column(db.String(15), nullable=True)

    gps_enabled = db.Column(db.Boolean, default=True)
    realtime_tracking_enabled = db.Column(db.Boolean, default=True)
    deployment_allowed = db.Column(db.Boolean, default=True)
    attendance_linked = db.Column(db.Boolean, default=False)
    fuel_tracking_enabled = db.Column(db.Boolean, default=False)
    geo_fencing_enabled = db.Column(db.Boolean, default=False)
    incident_monitoring_enabled = db.Column(db.Boolean, default=False)
    maintenance_tracking_enabled = db.Column(db.Boolean, default=False)

    load_capacity = db.Column(db.Integer, nullable=True)
    passenger_capacity = db.Column(db.Integer, nullable=True)
    fuel_capacity = db.Column(db.Integer, nullable=True)
    operational_capacity = db.Column(db.Integer, nullable=True)

    status = db.Column(db.String(30), nullable=False, default='Available')
    insurance_status = db.Column(db.String(30), nullable=True, default='Valid')
    fitness_status = db.Column(db.String(30), nullable=True, default='Valid')
    permit_status = db.Column(db.String(30), nullable=True, default='Valid')
    puc_status = db.Column(db.String(30), nullable=True, default='Valid')
    verification_status = db.Column(db.String(30), nullable=True, default='Valid')

    vehicle_running = db.Column(db.Float, default=0.0, nullable=True)
    insurance_expiry = db.Column(db.Date, nullable=True)
    fitness_expiry = db.Column(db.Date, nullable=True)
    permit_expiry = db.Column(db.Date, nullable=True)
    puc_expiry = db.Column(db.Date, nullable=True)

    assigned_driver = db.Column(db.String(120), nullable=True)
    assigned_driver_id = db.Column(db.String(36), db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True)
    current_deployment = db.Column(db.String(150), nullable=True)
    last_activity = db.Column(db.String(255), nullable=True)
    current_location = db.Column(db.String(255), nullable=True)
    last_gps_ping = db.Column(db.DateTime(timezone=True), nullable=True)

    created_by = db.Column(db.String(36), nullable=True)
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
    subzone = db.relationship('Subzone', foreign_keys=[subzone_id], lazy='joined')
    assigned_driver_user = db.relationship('User', foreign_keys=[assigned_driver_id], lazy='joined')

    @property
    def resolved_status(self):
        if self.vehicle_running and self.vehicle_running >= 150000:
            return 'Deployment Restricted'
        try:
            from app.modules.attendance.utils import get_india_today
            today = get_india_today()
        except Exception:
            from datetime import date
            today = date.today()
        doc_expiries = [
            self.insurance_expiry,
            self.fitness_expiry,
            self.permit_expiry,
            self.puc_expiry
        ]
        if any(d and d < today for d in doc_expiries):
            return 'Maintenance Required'
        if self.vehicle_running and self.vehicle_running >= 140000:
            return 'Maintenance Warning'
        return self.status or 'Available'

    def to_dict(self):
        return {
            'id': self.id,
            'company_id': self.company_id,
            'circle_id': self.circle_id,
            'client_id': self.client_id,
            'project_id': self.project_id,
            'subzone_id': self.subzone_id,
            'vehicle_number': self.vehicle_number,
            'vehicle_type': self.vehicle_type,
            'vehicle_category': self.vehicle_category,
            'vehicle_brand': self.vehicle_brand,
            'vehicle_model': self.vehicle_model,
            'manufacturing_year': self.manufacturing_year,
            'chassis_number': self.chassis_number,
            'engine_number': self.engine_number,
            'owner_name': self.owner_name,
            'owner_phone': self.owner_phone,
            'vendor_name': self.vendor_name,
            'vendor_contact': self.vendor_contact,
            'gps_enabled': self.gps_enabled,
            'realtime_tracking_enabled': self.realtime_tracking_enabled,
            'deployment_allowed': self.deployment_allowed,
            'attendance_linked': self.attendance_linked,
            'fuel_tracking_enabled': self.fuel_tracking_enabled,
            'geo_fencing_enabled': self.geo_fencing_enabled,
            'incident_monitoring_enabled': self.incident_monitoring_enabled,
            'maintenance_tracking_enabled': self.maintenance_tracking_enabled,
            'load_capacity': self.load_capacity,
            'passenger_capacity': self.passenger_capacity,
            'fuel_capacity': self.fuel_capacity,
            'operational_capacity': self.operational_capacity,
            'status': self.resolved_status,
            'insurance_status': self.insurance_status,
            'fitness_status': self.fitness_status,
            'permit_status': self.permit_status,
            'puc_status': self.puc_status,
            'verification_status': self.verification_status,
            'vehicle_running': self.vehicle_running,
            'insurance_expiry': self.insurance_expiry.isoformat() if self.insurance_expiry else None,
            'fitness_expiry': self.fitness_expiry.isoformat() if self.fitness_expiry else None,
            'permit_expiry': self.permit_expiry.isoformat() if self.permit_expiry else None,
            'puc_expiry': self.puc_expiry.isoformat() if self.puc_expiry else None,
            'assigned_driver': self.assigned_driver,
            'current_deployment': self.current_deployment,
            'last_activity': self.last_activity,
            'current_location': self.current_location,
            'last_gps_ping': self.last_gps_ping.isoformat() if self.last_gps_ping else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self):
        return f'<Vehicle {self.vehicle_number}>'

