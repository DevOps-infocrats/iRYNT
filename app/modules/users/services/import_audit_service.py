from app.modules.auth.models import AuditLog
from app.extensions import db
from flask import request

class ImportAuditService:
    """Service to log bulk import metrics in the AuditLog database table."""

    def record_import(self, importer_id: str, total: int, succeeded: int, failed: int) -> AuditLog:
        """Create an AuditLog entry for the bulk import execution."""
        ip_address = request.remote_addr if request else None
        user_agent = request.user_agent.string if request and request.user_agent else None
        
        details = {
            "total_rows": total,
            "succeeded": succeeded,
            "failed": failed,
        }

        audit_entry = AuditLog(
            user_id=importer_id,
            action="BULK_USER_IMPORT",
            ip_address=ip_address,
            user_agent=user_agent,
            details=details
        )
        
        db.session.add(audit_entry)
        db.session.commit()
        return audit_entry
