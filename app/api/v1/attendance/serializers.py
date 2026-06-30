from marshmallow import Schema, fields, validate

from app.modules.attendance.approval_constants import approval_status_label


class CheckInRequestSchema(Schema):
    """Schema to validate check-in payload"""
    driver_profile_id = fields.Str(required=True, validate=validate.Length(min=1))
    latitude = fields.Float(required=True)
    longitude = fields.Float(required=True)
    accuracy = fields.Float(required=True)
    selfie_data = fields.Str(allow_none=True, validate=validate.Length(max=5242880))
    dashboard_data = fields.Str(allow_none=True, validate=validate.Length(max=5242880))
    odometer = fields.Float(allow_none=True, validate=validate.Range(min=0))

class CheckOutRequestSchema(Schema):
    """Schema to validate check-out payload"""
    driver_profile_id = fields.Str(required=True, validate=validate.Length(min=1))
    latitude = fields.Float(required=True)
    longitude = fields.Float(required=True)
    accuracy = fields.Float(required=True)
    selfie_data = fields.Str(allow_none=True, validate=validate.Length(max=5242880))
    dashboard_data = fields.Str(allow_none=True, validate=validate.Length(max=5242880))
    odometer = fields.Float(allow_none=True, validate=validate.Range(min=0))

class GPSSyncPointSchema(Schema):
    """Schema to validate individual GPS track coordinate"""
    latitude = fields.Float(required=True)
    longitude = fields.Float(required=True)
    timestamp = fields.DateTime(required=True)
    speed = fields.Float(allow_none=True)
    accuracy = fields.Float(allow_none=True)

class GPSSyncRequestSchema(Schema):
    """Schema to validate GPS sync request payload"""
    deployment_id = fields.Str(required=True, validate=validate.Length(min=1))
    coordinates = fields.List(fields.Nested(GPSSyncPointSchema), required=True, validate=validate.Length(min=1))

class AttendanceResponseSchema(Schema):
    """Schema to serialize attendance details response"""
    id = fields.Str()
    driver_id = fields.Str()
    date = fields.Date()
    shift_name = fields.Str(allow_none=True)
    check_in = fields.DateTime(allow_none=True)
    check_out = fields.DateTime(allow_none=True)
    hours_worked = fields.Float(allow_none=True)
    status = fields.Str()
    notes = fields.Str(allow_none=True)
    checkin_latitude = fields.Float(allow_none=True)
    checkin_longitude = fields.Float(allow_none=True)
    checkout_latitude = fields.Float(allow_none=True)
    checkout_longitude = fields.Float(allow_none=True)
    location_accuracy = fields.Float(allow_none=True)
    geo_verified = fields.Bool(allow_none=True)
    geo_status = fields.Str(allow_none=True)
    geo_distance_meters = fields.Float(allow_none=True)
    selfie_storage_path = fields.Str(allow_none=True)
    dashboard_storage_path = fields.Str(allow_none=True)
    start_odometer = fields.Float(allow_none=True)
    end_odometer = fields.Float(allow_none=True)
    verification_status = fields.Str(allow_none=True)
    approval_status = fields.Str(allow_none=True)
    approval_status_label = fields.Method('serialize_approval_status_label')

    def serialize_approval_status_label(self, obj):
        return approval_status_label(getattr(obj, 'approval_status', None))
