from marshmallow import Schema, fields

class VehicleCurrentResponseSchema(Schema):
    """Schema to serialize current vehicle response details"""
    vehicle_number = fields.Str(allow_none=True)
    vehicle_type = fields.Str(allow_none=True)
    odometer = fields.Raw(allow_none=True)
    insurance_expiry = fields.Str(allow_none=True)
    fitness_expiry = fields.Str(allow_none=True)
