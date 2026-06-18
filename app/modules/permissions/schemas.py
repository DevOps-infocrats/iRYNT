"""
Permission Schemas

Data transfer objects and validation schemas for permissions
"""

from marshmallow import Schema, fields, validate


class PermissionDetailSchema(Schema):
    """Permission detail schema"""
    id = fields.Str(dump_only=True)
    permission_id = fields.Str()
    module = fields.Str(required=True, validate=validate.Length(min=1, max=120))
    action = fields.Str(required=True, validate=validate.Length(min=1, max=80))
    scope_type = fields.Str(missing='global')
    security_level = fields.Str(missing='medium')
    is_active = fields.Bool(missing=True)
    can_delegate = fields.Bool(missing=False)
    requires_mfa = fields.Bool(missing=False)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)


class PermissionWorkflowAccessSchema(Schema):
    """Workflow permission schema"""
    id = fields.Str(dump_only=True)
    permission_id = fields.Str()
    workflow_type = fields.Str(required=True)
    can_approve = fields.Bool(missing=False)
    can_reject = fields.Bool(missing=False)
    can_escalate = fields.Bool(missing=False)
    can_override = fields.Bool(missing=False)
    can_close_workflow = fields.Bool(missing=False)
    approval_level = fields.Int(missing=0)
    auto_approve_threshold = fields.Float(allow_none=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)


class PermissionCategorySchema(Schema):
    """Permission category schema"""
    id = fields.Str(dump_only=True)
    name = fields.Str(required=True, validate=validate.Length(min=1, max=120))
    code = fields.Str(required=True, validate=validate.Length(min=1, max=80))
    description = fields.Str(allow_none=True)
    icon = fields.Str(allow_none=True)
    display_order = fields.Int(missing=0)
    is_active = fields.Bool(missing=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)


class PermissionCreateSchema(Schema):
    """Schema for creating a new permission"""
    code = fields.Str(required=True, validate=validate.Length(min=1, max=255))
    name = fields.Str(required=True, validate=validate.Length(min=1, max=255))
    description = fields.Str(allow_none=True)
    module = fields.Str(required=True, validate=validate.Length(min=1, max=120))
    action = fields.Str(required=True, validate=validate.Length(min=1, max=80))
    scope_type = fields.Str(missing='global')
    security_level = fields.Str(missing='medium', validate=validate.OneOf(['low', 'medium', 'critical']))
    category_id = fields.Str(allow_none=True)
    is_active = fields.Bool(missing=True)
    can_delegate = fields.Bool(missing=False)
    requires_mfa = fields.Bool(missing=False)
    workflow_access = fields.Nested(PermissionWorkflowAccessSchema, allow_none=True)


class PermissionUpdateSchema(Schema):
    """Schema for updating a permission"""
    description = fields.Str(allow_none=True)
    scope_type = fields.Str(allow_none=True)
    security_level = fields.Str(allow_none=True, validate=validate.OneOf(['low', 'medium', 'critical']))
    is_active = fields.Bool(allow_none=True)
    can_delegate = fields.Bool(allow_none=True)
    requires_mfa = fields.Bool(allow_none=True)


class PermissionAuditLogSchema(Schema):
    """Permission audit log schema"""
    id = fields.Str(dump_only=True)
    permission_id = fields.Str(allow_none=True)
    role_id = fields.Str(allow_none=True)
    user_id = fields.Str(allow_none=True)
    action = fields.Str()
    entity_type = fields.Str()
    entity_id = fields.Str(allow_none=True)
    action_type = fields.Str()
    status = fields.Str()
    old_value = fields.Dict(allow_none=True)
    new_value = fields.Dict(allow_none=True)
    reason = fields.Str(allow_none=True)
    ip_address = fields.Str(allow_none=True)
    user_agent = fields.Str(allow_none=True)
    severity = fields.Str()
    created_at = fields.DateTime(dump_only=True)


class PermissionScopeSchema(Schema):
    """Permission scope schema"""
    id = fields.Str(dump_only=True)
    permission_id = fields.Str()
    scope_code = fields.Str()
    scope_value = fields.Str(allow_none=True)
    is_default = fields.Bool(missing=False)
    created_at = fields.DateTime(dump_only=True)


class RolePermissionMatrixSchema(Schema):
    """Role-Permission matrix schema"""
    id = fields.Str(dump_only=True)
    role_id = fields.Str()
    permission_id = fields.Str()
    inherited_from = fields.Str(allow_none=True)
    is_inherited = fields.Bool()
    can_delegate = fields.Bool()
    assigned_by = fields.Str(allow_none=True)
    assigned_at = fields.DateTime()
    expires_at = fields.DateTime(allow_none=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)


class BulkPermissionAssignSchema(Schema):
    """Schema for bulk permission assignment"""
    role_id = fields.Str(required=True)
    permission_ids = fields.List(fields.Str(), required=True)


class PermissionMatrixRowSchema(Schema):
    """Schema for permission matrix row"""
    module = fields.Str()
    actions = fields.Dict(keys=fields.Str(), values=fields.Dict())


class PermissionListSchema(Schema):
    """Schema for permission list response"""
    id = fields.Str()
    name = fields.Str()
    code = fields.Str()
    description = fields.Str(allow_none=True)
    module = fields.Str()
    action = fields.Str()
    scope_type = fields.Str()
    security_level = fields.Str()
    is_active = fields.Bool()
    assigned_roles_count = fields.Int()
    created_at = fields.DateTime()
    updated_at = fields.DateTime()


class RolePermissionsSchema(Schema):
    """Schema for role permissions response"""
    role_id = fields.Str()
    role_name = fields.Str()
    permissions_count = fields.Int()
    permissions = fields.List(fields.Nested(PermissionListSchema))
    grouped = fields.Dict(keys=fields.Str(), values=fields.List(fields.Dict()))
