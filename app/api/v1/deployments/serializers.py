from marshmallow import Schema, fields

class DeploymentCurrentResponseSchema(Schema):
    """Schema to serialize current deployment response details"""
    project = fields.Str(allow_none=True)
    circle = fields.Str(allow_none=True)
    subzone = fields.Str(allow_none=True)
    vehicle_number = fields.Str(allow_none=True)
    status = fields.Str(allow_none=True)
