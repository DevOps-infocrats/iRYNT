import uuid
from datetime import datetime

from app.extensions import db
from app.modules.circles.models import Circle
from app.modules.clients.models import Client
from app.modules.projects.models import Project
from app.modules.subzones.models import Subzone


def make_uuid():
    return str(uuid.uuid4())


class DriverProfile(db.Model):
    __tablename__ = 'driver_profiles'

    id = db.Column(db.String(36), primary_key=True, default=make_uuid)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, unique=True, index=True)
    driver_code = db.Column(db.String(50), nullable=True, unique=True, index=True)
    circle_id = db.Column(db.String(36), db.ForeignKey('circles.id'), nullable=True, index=True)
    client_id = db.Column(db.String(36), db.ForeignKey('clients.id'), nullable=True, index=True)
    project_id = db.Column(db.String(36), db.ForeignKey('projects.id'), nullable=True, index=True)
    subzone_id = db.Column(db.String(36), db.ForeignKey('subzones.id'), nullable=True, index=True)
    dob = db.Column(db.Date, nullable=True)
    gender = db.Column(db.String(20), nullable=True)
    blood_group = db.Column(db.String(10), nullable=True)
    nationality = db.Column(db.String(60), nullable=True, default='Indian')
    address = db.Column(db.String(255), nullable=True)
    emergency_contact_name = db.Column(db.String(120), nullable=True)
    emergency_contact_phone = db.Column(db.String(30), nullable=True)
    experience_years = db.Column(db.Float, nullable=True)
    join_date = db.Column(db.Date, nullable=True)
    license_status = db.Column(db.String(30), nullable=True, default='Pending')
    compliance_status = db.Column(db.String(30), nullable=True, default='Pending')
    active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    user = db.relationship('User', back_populates='driver_profile', uselist=False)
    circle = db.relationship('Circle', foreign_keys=[circle_id], lazy='joined')
    client = db.relationship('Client', foreign_keys=[client_id], lazy='joined')
    project = db.relationship('Project', foreign_keys=[project_id], lazy='joined')
    subzone = db.relationship('Subzone', foreign_keys=[subzone_id], lazy='joined')
    licenses = db.relationship('DriverLicense', back_populates='driver', cascade='all, delete-orphan', lazy='dynamic')
    documents = db.relationship('DriverDocument', back_populates='driver', cascade='all, delete-orphan', lazy='dynamic')
    vehicle_assignments = db.relationship('DriverVehicleAssignment', back_populates='driver', cascade='all, delete-orphan', lazy='dynamic')
    attendances = db.relationship('DriverAttendance', back_populates='driver', cascade='all, delete-orphan', lazy='dynamic')
    trips = db.relationship('DriverTrip', back_populates='driver', cascade='all, delete-orphan', lazy='dynamic')
    performance_records = db.relationship('DriverPerformance', back_populates='driver', cascade='all, delete-orphan', lazy='dynamic')
    incidents = db.relationship('DriverIncident', back_populates='driver', cascade='all, delete-orphan', lazy='dynamic')
    payroll_records = db.relationship('DriverPayroll', back_populates='driver', cascade='all, delete-orphan', lazy='dynamic')
    activity_logs = db.relationship('DriverActivityLog', back_populates='driver', cascade='all, delete-orphan', lazy='dynamic')

    def __repr__(self):
        return f'<DriverProfile {self.driver_code or self.user_id}>'


class DriverLicense(db.Model):
    __tablename__ = 'driver_licenses'
    __table_args__ = (
        db.Index('idx_driver_licenses_license_number', 'license_number'),
        db.Index('idx_driver_licenses_expiry_date', 'expiry_date'),
    )

    id = db.Column(db.String(36), primary_key=True, default=make_uuid)
    driver_id = db.Column(db.String(36), db.ForeignKey('driver_profiles.id', ondelete='CASCADE'), nullable=False, index=True)
    license_number = db.Column(db.String(80), nullable=False, unique=True)
    vehicle_classes = db.Column(db.String(120), nullable=True)
    issue_date = db.Column(db.Date, nullable=True)
    expiry_date = db.Column(db.Date, nullable=True)
    verification_status = db.Column(db.String(30), nullable=True, default='Pending')
    medical_certificate_status = db.Column(db.String(30), nullable=True, default='Pending')
    police_verification_status = db.Column(db.String(30), nullable=True, default='Pending')
    insurance_compliance_status = db.Column(db.String(30), nullable=True, default='Pending')
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    driver = db.relationship('DriverProfile', back_populates='licenses')

    def is_expired(self):
        if self.expiry_date is None:
            return False
        return self.expiry_date < datetime.utcnow().date()

    def __repr__(self):
        return f'<DriverLicense {self.license_number}>'


class DriverDocument(db.Model):
    __tablename__ = 'driver_documents'
    __table_args__ = (
        db.Index('idx_driver_documents_document_type', 'document_type'),
        db.Index('idx_driver_documents_expiry_date', 'expiry_date'),
    )

    id = db.Column(db.String(36), primary_key=True, default=make_uuid)
    driver_id = db.Column(db.String(36), db.ForeignKey('driver_profiles.id', ondelete='CASCADE'), nullable=False, index=True)
    document_type = db.Column(db.String(80), nullable=False)
    file_name = db.Column(db.String(255), nullable=False)
    storage_path = db.Column(db.String(512), nullable=False)
    uploaded_by = db.Column(db.String(36), nullable=True)
    uploaded_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    expiry_date = db.Column(db.Date, nullable=True)
    status = db.Column(db.String(30), nullable=True, default='Uploaded')

    driver = db.relationship('DriverProfile', back_populates='documents')

    def __repr__(self):
        return f'<DriverDocument {self.document_type}>'


class DriverVehicleAssignment(db.Model):
    __tablename__ = 'driver_vehicle_assignments'
    __table_args__ = (
        db.Index('idx_driver_vehicle_assignments_driver_id', 'driver_id'),
        db.Index('idx_driver_vehicle_assignments_vehicle_id', 'vehicle_id'),
    )

    id = db.Column(db.String(36), primary_key=True, default=make_uuid)
    driver_id = db.Column(db.String(36), db.ForeignKey('driver_profiles.id', ondelete='CASCADE'), nullable=False, index=True)
    vehicle_id = db.Column(db.String(36), db.ForeignKey('vehicles.id', ondelete='SET NULL'), nullable=True, index=True)
    assigned_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    released_at = db.Column(db.DateTime(timezone=True), nullable=True)
    assignment_reason = db.Column(db.String(255), nullable=True)
    status = db.Column(db.String(30), nullable=False, default='Active')

    driver = db.relationship('DriverProfile', back_populates='vehicle_assignments')
    vehicle = db.relationship('Vehicle', foreign_keys=[vehicle_id], lazy='joined')

    def __repr__(self):
        return f'<DriverVehicleAssignment {self.driver_id} -> {self.vehicle_id}>'


class DriverAttendance(db.Model):
    __tablename__ = 'driver_attendance'
    __table_args__ = (
        db.Index('idx_driver_attendance_driver_id', 'driver_id'),
        db.Index('idx_driver_attendance_date', 'date'),
    )

    id = db.Column(db.String(36), primary_key=True, default=make_uuid)
    driver_id = db.Column(db.String(36), db.ForeignKey('driver_profiles.id', ondelete='CASCADE'), nullable=False, index=True)
    date = db.Column(db.Date, nullable=False, index=True)
    shift_name = db.Column(db.String(80), nullable=True)
    check_in = db.Column(db.DateTime(timezone=True), nullable=True)
    check_out = db.Column(db.DateTime(timezone=True), nullable=True)
    hours_worked = db.Column(db.Float, nullable=True)
    status = db.Column(db.String(30), nullable=True, default='Present')
    notes = db.Column(db.String(512), nullable=True)
    checkin_latitude = db.Column(db.Float, nullable=True)
    checkin_longitude = db.Column(db.Float, nullable=True)
    checkout_latitude = db.Column(db.Float, nullable=True)
    checkout_longitude = db.Column(db.Float, nullable=True)
    location_accuracy = db.Column(db.Float, nullable=True)
    geo_verified = db.Column(db.Boolean, nullable=True)
    geo_status = db.Column(db.String(30), nullable=True)
    geo_distance_meters = db.Column(db.Float, nullable=True)
    selfie_storage_path = db.Column(db.String(512), nullable=True)
    dashboard_storage_path = db.Column(db.String(512), nullable=True)
    start_odometer = db.Column(db.Float, nullable=True)
    end_odometer = db.Column(db.Float, nullable=True)
    verification_status = db.Column(db.String(50), nullable=True)

    driver = db.relationship('DriverProfile', back_populates='attendances')

    def __repr__(self):
        return f'<DriverAttendance {self.driver_id} {self.date}>'


class DriverTrip(db.Model):
    __tablename__ = 'driver_trips'
    __table_args__ = (
        db.Index('idx_driver_trips_driver_id', 'driver_id'),
        db.Index('idx_driver_trips_trip_date', 'trip_date'),
    )

    id = db.Column(db.String(36), primary_key=True, default=make_uuid)
    driver_id = db.Column(db.String(36), db.ForeignKey('driver_profiles.id', ondelete='CASCADE'), nullable=False, index=True)
    vehicle_id = db.Column(db.String(36), db.ForeignKey('vehicles.id', ondelete='SET NULL'), nullable=True, index=True)
    trip_date = db.Column(db.DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    pickup_location = db.Column(db.String(255), nullable=True)
    dropoff_location = db.Column(db.String(255), nullable=True)
    distance_km = db.Column(db.Float, nullable=True)
    duration_minutes = db.Column(db.Integer, nullable=True)
    earnings = db.Column(db.Numeric(12, 2), nullable=True)
    fuel_consumed_liters = db.Column(db.Float, nullable=True)
    status = db.Column(db.String(30), nullable=True, default='Completed')

    driver = db.relationship('DriverProfile', back_populates='trips')
    vehicle = db.relationship('Vehicle', foreign_keys=[vehicle_id], lazy='joined')

    def __repr__(self):
        return f'<DriverTrip {self.id}>'


class DriverPerformance(db.Model):
    __tablename__ = 'driver_performance'
    __table_args__ = (
        db.Index('idx_driver_performance_driver_id', 'driver_id'),
        db.Index('idx_driver_performance_period', 'period_start', 'period_end'),
    )

    id = db.Column(db.String(36), primary_key=True, default=make_uuid)
    driver_id = db.Column(db.String(36), db.ForeignKey('driver_profiles.id', ondelete='CASCADE'), nullable=False, index=True)
    period_start = db.Column(db.Date, nullable=True)
    period_end = db.Column(db.Date, nullable=True)
    rating = db.Column(db.Float, nullable=True)
    safety_score = db.Column(db.Float, nullable=True)
    on_time_percentage = db.Column(db.Float, nullable=True)
    harsh_braking_events = db.Column(db.Integer, nullable=True)
    overspeeding_events = db.Column(db.Integer, nullable=True)
    complaint_count = db.Column(db.Integer, nullable=True)
    violation_count = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    driver = db.relationship('DriverProfile', back_populates='performance_records')

    def __repr__(self):
        return f'<DriverPerformance {self.driver_id}>'


class DriverIncident(db.Model):
    __tablename__ = 'driver_incidents'
    __table_args__ = (
        db.Index('idx_driver_incidents_driver_id', 'driver_id'),
        db.Index('idx_driver_incidents_date', 'incident_date'),
    )

    id = db.Column(db.String(36), primary_key=True, default=make_uuid)
    driver_id = db.Column(db.String(36), db.ForeignKey('driver_profiles.id', ondelete='CASCADE'), nullable=False, index=True)
    incident_date = db.Column(db.DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    severity = db.Column(db.String(30), nullable=False, default='Medium')
    category = db.Column(db.String(80), nullable=True)
    description = db.Column(db.String(512), nullable=True)
    action_taken = db.Column(db.String(255), nullable=True)
    status = db.Column(db.String(30), nullable=True, default='Open')

    driver = db.relationship('DriverProfile', back_populates='incidents')

    def __repr__(self):
        return f'<DriverIncident {self.id}>'


class DriverPayroll(db.Model):
    __tablename__ = 'driver_payroll'
    __table_args__ = (
        db.Index('idx_driver_payroll_driver_id', 'driver_id'),
        db.Index('idx_driver_payroll_period', 'period_start', 'period_end'),
    )

    id = db.Column(db.String(36), primary_key=True, default=make_uuid)
    driver_id = db.Column(db.String(36), db.ForeignKey('driver_profiles.id', ondelete='CASCADE'), nullable=False, index=True)
    period_start = db.Column(db.Date, nullable=True)
    period_end = db.Column(db.Date, nullable=True)
    base_salary = db.Column(db.Numeric(12, 2), nullable=True)
    incentives = db.Column(db.Numeric(12, 2), nullable=True)
    deductions = db.Column(db.Numeric(12, 2), nullable=True)
    net_pay = db.Column(db.Numeric(12, 2), nullable=True)
    payment_date = db.Column(db.Date, nullable=True)
    bank_account_masked = db.Column(db.String(32), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    driver = db.relationship('DriverProfile', back_populates='payroll_records')

    def __repr__(self):
        return f'<DriverPayroll {self.driver_id}>'


class DriverActivityLog(db.Model):
    __tablename__ = 'driver_activity_logs'
    __table_args__ = (
        db.Index('idx_driver_activity_logs_driver_id', 'driver_id'),
        db.Index('idx_driver_activity_logs_actor_id', 'actor_id'),
    )

    id = db.Column(db.String(36), primary_key=True, default=make_uuid)
    driver_id = db.Column(db.String(36), db.ForeignKey('driver_profiles.id', ondelete='CASCADE'), nullable=False, index=True)
    actor_id = db.Column(db.String(36), db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True)
    event_type = db.Column(db.String(80), nullable=False)
    description = db.Column(db.String(512), nullable=True)
    event_metadata = db.Column(db.JSON, nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    driver = db.relationship('DriverProfile', back_populates='activity_logs')

    def __repr__(self):
        return f'<DriverActivityLog {self.event_type}>'
