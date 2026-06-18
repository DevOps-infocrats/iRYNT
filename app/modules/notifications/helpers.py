from typing import Optional, Dict


def create_notification_safe(user_id: Optional[str], message: str, module: str = 'system', priority: str = 'info', related_type: Optional[str] = None, related_id: Optional[str] = None, route: Optional[str] = None, metadata: Optional[Dict] = None, company_id: Optional[str] = None, circle_id: Optional[str] = None, type: Optional[str] = None):
    """Create a notification in a non-blocking, safe manner.

    This helper logs failures silently to avoid breaking the caller flows.
    """
    try:
        from app.infrastructure.repositories.notifications.notifications_repository import NotificationsRepository
        from app.modules.notifications.models import Notification
        from datetime import datetime, timedelta

        # 1. Deduplication (24 hours) for compliance-related messages/modules
        is_compliance = (
            module in ('compliance', 'documents', 'vehicles') or
            any(k in message.lower() for k in ('odometer', 'compliance', 'expiry', 'expired', 'warning', 'restrict'))
        )
        if is_compliance:
            cutoff = datetime.utcnow() - timedelta(hours=24)
            existing = Notification.query.filter(
                Notification.user_id == user_id,
                Notification.message == message,
                Notification.module == module,
                Notification.created_at >= cutoff
            ).first()
            if existing:
                return None

        # 2. Priority mapping
        msg_lower = message.lower()
        if 'approaching' in msg_lower:
            priority = 'Warning'
        elif '140000 km' in msg_lower or 'maintenance warning' in msg_lower:
            priority = 'Warning'
        elif '150000 km' in msg_lower or 'deployment restricted' in msg_lower or 'insurance expired' in msg_lower or 'expired' in msg_lower:
            priority = 'Critical'
        elif 'outside geofence' in msg_lower or 'geofence' in msg_lower:
            priority = 'High'
        elif 'reassigned' in msg_lower:
            priority = 'Medium'

        # 3. Resolve company_id and circle_id
        if not company_id or not circle_id:
            resolved_company_id = None
            resolved_circle_id = None
            if user_id:
                from app.modules.auth.models import User
                user = User.query.get(user_id)
                if user:
                    resolved_company_id = getattr(user, 'company_id', None)
                    resolved_circle_id = getattr(user, 'circle_id', None)
            
            if not company_id:
                company_id = resolved_company_id
            if not circle_id:
                circle_id = resolved_circle_id

        # 4. Determine notification type/category
        resolved_type = type
        if not resolved_type:
            resolved_type = 'system'
            if module == 'attendance':
                resolved_type = 'attendance'
            elif module == 'deployments':
                resolved_type = 'deployment'
            elif module == 'approvals':
                if 'escalat' in message.lower():
                    resolved_type = 'escalation'
                else:
                    resolved_type = 'approval'
            elif module in ('documents', 'compliance', 'vehicles') or any(k in message.lower() for k in ('expiry', 'expired', 'odometer', 'km')):
                resolved_type = 'expiry'

        payload = {
            'user_id': user_id,
            'type': resolved_type,
            'message': message,
            'module': module,
            'priority': priority,
            'related_type': related_type,
            'related_id': related_id,
            'route': route,
            'metadata': metadata or {},
            'company_id': company_id,
            'circle_id': circle_id,
        }
        NotificationsRepository.create(payload)
    except Exception:
        # Fail silently — notifications must not break main workflows
        return None



def create_notifications_for_roles_safe(role_names, message: str, module: str = 'system', priority: str = 'info', related_type: Optional[str] = None, related_id: Optional[str] = None, route: Optional[str] = None, metadata: Optional[Dict] = None, type: Optional[str] = None):
    """Create notifications for all users belonging to any of the given role names.

    Non-blocking and resilient: exceptions are swallowed to avoid impacting callers.
    """
    try:
        from app.modules.auth.models import User, Role
        from sqlalchemy.orm import joinedload

        # Normalize names
        names = [n.strip() for n in role_names] if isinstance(role_names, (list, tuple)) else [role_names]
        # Find users who have any of these roles (primary or secondary)
        users = (
            User.query.join(User.roles)
            .filter(Role.name.in_(names))
            .options(joinedload(User.roles))
            .all()
        )
        seen = set()
        for u in users:
            if not u or not getattr(u, 'id', None):
                continue
            if u.id in seen:
                continue
            seen.add(u.id)
            create_notification_safe(
                user_id=u.id,
                message=message,
                module=module,
                priority=priority,
                related_type=related_type,
                related_id=related_id,
                route=route,
                metadata=metadata,
                type=type,
            )

        # Fallback to system-wide notification if target roles have no users
        if not seen:
            create_notification_safe(
                user_id=None,
                message=message,
                module=module,
                priority=priority,
                related_type=related_type,
                related_id=related_id,
                route=route,
                metadata=metadata,
                type=type,
            )
    except Exception:
        return None
