import logging
from app.modules.users.services import UserService
from app.extensions import db

logger = logging.getLogger(__name__)

class BulkImportService:
    """Service to import validated user rows into the database."""

    def __init__(self):
        self.user_service = UserService()

    def _parse_bool(self, val) -> bool:
        if val is None:
            return True
        s = str(val).strip().lower()
        if s in ("yes", "true", "1", "active", "y", "t"):
            return True
        if s in ("no", "false", "0", "inactive", "n", "f"):
            return False
        return True

    def import_rows(self, valid_rows: list, importer_id: str) -> dict:
        """Create users for all valid rows.
        Returns a dict summarizing the operation.
        """
        created_count = 0
        failed_count = 0
        runtime_errors = []

        for row in valid_rows:
            try:
                # Map Excel headers to the payload fields expected by UserService.create_user
                phone = row.get("Phone")
                if phone is not None:
                    phone = str(phone).strip().split('.')[0] # Remove any decimal formatting if read as float
                
                payload = {
                    "username": str(row.get("Username") or "").strip(),
                    "email": str(row.get("Email") or "").strip(),
                    "phone": phone if phone else None,
                    "company_id": row.get("company_id"),
                    "circle_id": row.get("circle_id"),
                    "role_id": row.get("role_id"),
                    "project_id": row.get("project_id"),
                    "is_active": self._parse_bool(row.get("Is Active")),
                    "is_verified": self._parse_bool(row.get("Is Verified")),
                    "password": str(row.get("Password") or "").strip() or None,
                }

                # Create user
                self.user_service.create_user(payload)
                created_count += 1
            except Exception as e:
                db.session.rollback()
                failed_count += 1
                row_num = row.get("row_number", "Unknown")
                err_msg = f"Row {row_num}: Failed to save user. Error: {str(e)}"
                logger.error(err_msg)
                runtime_errors.append(err_msg)

        return {
            "created": created_count,
            "failed": failed_count,
            "errors": runtime_errors
        }
