from marshmallow import Schema, fields


class PermissionSchema(Schema):
    """Schema for Permission serialization"""
    id = fields.String(dump_only=True)
    name = fields.String()
    description = fields.String(allow_none=True)


class RoleSchema(Schema):
    """Schema for Role serialization"""
    id = fields.String(dump_only=True)
    name = fields.String(required=True)
    code = fields.String(dump_only=True)
    description = fields.String(allow_none=True)
    is_system = fields.Boolean()
    level = fields.Integer(allow_none=True)
    permissions_count = fields.Integer(dump_only=True)
    workflow_count = fields.Integer(dump_only=True)
    users_count = fields.Integer(dump_only=True)
    status = fields.String(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)


class RoleDetailSchema(Schema):
    """Schema for detailed role information"""
    id = fields.String(dump_only=True)
    name = fields.String()
    description = fields.String(allow_none=True)
    is_system = fields.Boolean()
    
    # Hierarchy
    hierarchy = fields.Dict(dump_only=True)
    
    # Permissions
    permissions = fields.List(fields.Nested(PermissionSchema), dump_only=True)
    permission_count = fields.Integer(dump_only=True)
    
    # Workflows
    workflows = fields.List(fields.Dict(), dump_only=True)
    
    # Module access
    modules = fields.List(fields.Dict(), dump_only=True)
    
    # Scopes
    scopes = fields.List(fields.Dict(), dump_only=True)
    
    # Users
    users_count = fields.Integer(dump_only=True)
    
    # Audit
    audit_logs = fields.List(fields.Dict(), dump_only=True)


class WorkflowPermissionSchema(Schema):
    """Schema for workflow permission"""
    workflow_type = fields.String(required=True)
    can_approve = fields.Boolean()
    can_reject = fields.Boolean()
    can_escalate = fields.Boolean()
    can_override = fields.Boolean()
    can_close_workflow = fields.Boolean()
    approval_level = fields.Integer()


class ModuleAccessSchema(Schema):
    """Schema for module access"""
    module = fields.String(required=True)
    can_view = fields.Boolean()
    can_create = fields.Boolean()
    can_edit = fields.Boolean()
    can_delete = fields.Boolean()
    can_approve = fields.Boolean()
    can_export = fields.Boolean()
    can_assign = fields.Boolean()


class PermissionMatrixSchema(Schema):
    """Schema for permission matrix"""
    pass  # Dynamic schema


class RoleComparisonSchema(Schema):
    """Schema for role comparison"""
    role1 = fields.Dict(dump_only=True)
    role2 = fields.Dict(dump_only=True)


class PermissionGroupSchema(Schema):
    """Schema for permission group"""
    id = fields.String(dump_only=True)
    name = fields.String()
    code = fields.String()
    category = fields.String()
    permissions_count = fields.Integer(dump_only=True)
    is_active = fields.Boolean()


class RoleHierarchySchema(Schema):
    """Schema for role hierarchy"""
    level = fields.Integer()
    tier = fields.String()
    parent_level = fields.Integer(allow_none=True)
    role_id = fields.String()
    role_name = fields.String()
    description = fields.String(allow_none=True)


class KPISchema(Schema):
    """Schema for KPI metric"""
    title = fields.String()
    value = fields.Integer()
    icon = fields.String()
    trend = fields.String()
    description = fields.String()
