from app.modules.notifications.helpers import create_notifications_for_roles_safe, create_notification_safe


def report_critical_incident(title: str, description: str, related_type: str = None, related_id: str = None, roles=None, metadata=None):
    """Send a critical-incident notification to a list of roles (role names)."""
    try:
        roles = roles or ['Operations Director', 'Corporate Admin', 'Super Admin']
        message = f"CRITICAL: {title} - {description}"
        # Notify roles
        create_notifications_for_roles_safe(
            roles,
            message=message,
            module='incidents',
            priority='Critical',
            related_type=related_type,
            related_id=related_id,
            route=None,
            metadata=metadata or {}
        )
        # Also create a system-wide alert (user_id=None) for audit
        create_notification_safe(
            user_id=None,
            message=message,
            module='incidents',
            priority='Critical',
            related_type=related_type,
            related_id=related_id,
            route=None,
            metadata=metadata or {}
        )
    except Exception:
        return None
