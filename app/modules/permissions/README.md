# Permissions Management Module

## Overview

The Permissions Management Module is an enterprise-grade authorization and access governance system for the Fleet + Workforce + Operations Management Platform. It provides:

- **Role-Based Access Control (RBAC)**: Manage permissions by roles
- **Scope-Based Access**: Control access by organizational scope (global, company, circle, client, project, subzone)
- **Workflow Authority**: Define approval, rejection, escalation, and override capabilities
- **Module-Level Access**: Fine-grained control over module and action-level permissions
- **Permission Inheritance**: Support for hierarchical permission inheritance
- **Audit & Security**: Complete audit trails for all permission changes and access events
- **Dynamic Access Control**: Real-time permission checking and validation

## Architecture

### Database Models

**Core Models**:
- `PermissionDetail`: Extended permission information (module, action, scope, security level)
- `PermissionWorkflowAccess`: Workflow-specific permission attributes
- `PermissionCategory`: Logical grouping of permissions
- `PermissionAuditLog`: Audit trail for permission changes
- `PermissionScope`: Scope restrictions for permissions
- `RolePermissionMatrix`: Denormalized role-permission mapping

### Components

```
app/modules/permissions/
├── models.py           # Database models
├── repository.py       # Data access layer
├── services.py         # Business logic
├── validators.py       # Input validation
├── decorators.py       # Authorization decorators
├── schemas.py          # Data transfer objects
├── routes.py           # Web UI routes
├── api_routes.py       # REST API routes
├── seed.py             # Database seeding
└── __init__.py         # Package initialization
```

## Usage

### 1. Basic Permission Check

```python
from app.modules.permissions.decorators import permission_required

@app.route('/users/create', methods=['POST'])
@permission_required('users.create')
def create_user():
    # This route requires users.create permission
    pass
```

### 2. Scope-Based Access

```python
from app.modules.permissions.decorators import scope_required

@app.route('/company/<company_id>', methods=['GET'])
@scope_required('company')
def view_company(company_id):
    # User must have company-level access
    pass
```

### 3. Workflow Authority

```python
from app.modules.permissions.decorators import workflow_authority_required

@app.route('/deployments/<id>/approve', methods=['POST'])
@workflow_authority_required('deployment', 'approve')
def approve_deployment(id):
    # User must have deployment approval authority
    pass
```

### 4. Permission Service Usage

```python
from app.modules.permissions.services import PermissionService

service = PermissionService()

# Get dashboard KPIs
kpis = service.get_dashboard_kpis()

# Create a new permission
permission, error = service.create_permission({
    'code': 'vehicles.service',
    'description': 'Service vehicles',
    'module': 'vehicles',
    'action': 'service',
    'scope_type': 'project',
    'security_level': 'medium',
})

# Assign permission to role
success = service.assign_permission_to_role(role_id, permission_id)

# Get role permissions grouped by module
grouped = service.get_role_permissions_grouped(role_id)

# Get permission matrix for UI
matrix = service.get_permission_matrix(role_id=role_id)
```

## Permission Format

Permissions follow a standardized `module.action` format:

```
users.view
users.create
users.edit
users.delete
users.block

vehicles.view
vehicles.assign
vehicles.block

deployments.create
deployments.approve
deployments.close

reports.export
reports.analytics
```

## Scopes

Permissions can be scoped to different organizational levels:

- **global**: Accessible system-wide
- **company**: Limited to specific company
- **circle**: Limited to specific circle
- **client**: Limited to specific client
- **project**: Limited to specific project
- **subzone**: Limited to specific subzone
- **operational**: Operational-level access

## Security Levels

Each permission has a security classification:

- **low**: Basic operational permissions (view, read)
- **medium**: Modification permissions (create, edit)
- **critical**: Sensitive operations (delete, admin, override)

## Routes

### Web UI Routes

```
GET    /permissions/                     # Dashboard
GET    /permissions/registry              # Permission list/registry
GET    /permissions/<id>                  # Permission details
GET    /permissions/create                # Create permission form
POST   /permissions/create                # Submit new permission
GET    /permissions/<id>/edit             # Edit permission form
POST   /permissions/<id>/edit             # Update permission
POST   /permissions/<id>/delete           # Delete permission

GET    /permissions/matrix                # Permission matrix
GET    /permissions/roles/<role_id>/permissions  # Role permissions
POST   /permissions/roles/<role_id>/assign       # Assign to role
POST   /permissions/roles/<role_id>/revoke       # Revoke from role

GET    /permissions/workflows             # Workflow access
GET    /permissions/analytics             # Analytics
GET    /permissions/audit                 # Audit logs
GET    /permissions/settings              # Settings
```

### API Routes

```
GET    /api/v1/permissions                # List permissions
GET    /api/v1/permissions/<id>           # Get permission
POST   /api/v1/permissions                # Create permission
PUT    /api/v1/permissions/<id>           # Update permission
DELETE /api/v1/permissions/<id>           # Delete permission

GET    /api/v1/permissions/roles/<role_id>/permissions    # Role permissions
POST   /api/v1/permissions/roles/<role_id>/assign         # Assign
POST   /api/v1/permissions/roles/<role_id>/revoke         # Revoke
POST   /api/v1/permissions/roles/<role_id>/bulk-assign    # Bulk assign

GET    /api/v1/permissions/matrix         # Permission matrix
GET    /api/v1/permissions/analytics      # Analytics
GET    /api/v1/permissions/analytics/role/<role_id>  # Role analytics
GET    /api/v1/permissions/audit          # Audit logs
GET    /api/v1/permissions/dashboard      # Dashboard data
GET    /api/v1/permissions/search         # Search permissions
```

## Setup & Configuration

### 1. Database Migration

The models are automatically created when the app initializes. To manually create tables:

```bash
flask db init
flask db migrate -m "Add permissions module"
flask db upgrade
```

### 2. Seed Initial Permissions

Run the seed script to populate standard permissions:

```bash
python app/modules/permissions/seed.py
```

Or from Flask shell:

```python
from app import create_app
from app.modules.permissions.seed import seed_permissions

app = create_app()
with app.app_context():
    seed_permissions()
```

### 3. Integration with Existing System

The module integrates seamlessly with:
- Existing Role model in `app.modules.auth.models`
- Existing User model for permission checking
- Existing authentication system
- Sidebar rendering for dynamic menu
- Existing API structure

## Features

### Dashboard
- Real-time KPI cards
- Permission statistics
- Quick access shortcuts
- Recent activity feed
- Categorized access panels

### Permission Registry
- Searchable permission list
- Advanced filtering (module, action, security level, status)
- Paginated display
- Individual permission details
- Bulk operations

### Permission Matrix
- Interactive role-permission grid
- Module-based organization
- Security level color coding
- Real-time assignment/revocation
- Role selection dropdown

### Role Management
- View permissions by role
- Assign/revoke permissions
- Bulk operations
- Permission analytics per role
- Inheritance visualization

### Workflow Access
- Define approval authorities
- Configure escalation rights
- Set override capabilities
- Approval level management
- Threshold-based approvals

### Analytics
- Permission distribution charts
- Module access trends
- Role access analytics
- Workflow authorization usage
- Security level breakdown

### Audit & Security
- Complete permission change log
- Access attempt tracking
- Unauthorized attempt logging
- Security event classification
- Severity indicators

## Security Considerations

1. **Access Control**: All permission routes require `permission_required` decorator
2. **Audit Logging**: Every permission change is logged
3. **Role-Based Validation**: Permissions are validated against user roles
4. **Scope Enforcement**: Scope-based access is enforced automatically
5. **CSRF Protection**: All POST requests are CSRF-protected
6. **Rate Limiting**: API endpoints should be rate-limited (future enhancement)

## Best Practices

1. **Use Permission Codes**: Always use standardized `module.action` format
2. **Scope Correctly**: Define appropriate scopes for each permission
3. **Audit Regularly**: Review audit logs for unauthorized attempts
4. **Minimize Critical Permissions**: Restrict critical permissions to essential roles
5. **Use Decorators**: Apply decorators for route-level access control
6. **Document Permissions**: Keep permission documentation updated
7. **Test Access**: Verify access control in development before deployment

## Troubleshooting

### Permission Not Working
1. Verify permission code is created in database
2. Check role is assigned to user
3. Confirm permission is assigned to role
4. Review audit logs for errors

### Access Denied Error
1. Check user roles
2. Verify role has required permission
3. Confirm scope matches user's organizational level
4. Review audit logs for security events

### Performance Issues
1. Check database indexes on permission tables
2. Verify caching is enabled
3. Review audit log size (archive old logs)
4. Consider pagination for large datasets

## Future Enhancements

- [ ] Permission caching layer
- [ ] Rate limiting
- [ ] Time-based permission expiration
- [ ] Delegation workflows
- [ ] Multi-factor authentication for critical actions
- [ ] Permission request workflow
- [ ] API key management
- [ ] OAuth/OIDC integration

## Support

For issues or questions:
1. Check audit logs: `/permissions/audit`
2. Review API responses
3. Consult permission matrix: `/permissions/matrix`
4. Check role permissions: `/permissions/roles/<role_id>/permissions`
