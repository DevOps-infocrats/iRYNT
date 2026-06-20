from app.extensions import db
from app.modules.vehicles.services import VehicleService
from app.modules.auth.models import AuditLog
from flask import request

class VehicleBulkImportService:
    """Service to handle importing rows of validated vehicle data."""

    def __init__(self):
        self.vehicle_service = VehicleService()

    def import_rows(self, valid_rows: list, importer_id: str) -> dict:
        """Import the list of valid vehicle payloads into the database and audit the action."""
        created_count = 0
        failed_count = 0

        for row in valid_rows:
            payload = {
                "company_id": row.get("company_id"),
                "circle_id": row.get("circle_id"),
                "client_id": row.get("client_id"),
                "project_id": row.get("project_id"),
                "subzone_id": row.get("subzone_id"),
                "vehicle_number": row.get("vehicle_number"),
                "vehicle_type": row.get("vehicle_type"),
                "vehicle_category": row.get("vehicle_category"),
                "vehicle_brand": row.get("vehicle_brand"),
                "vehicle_model": row.get("vehicle_model"),
                "manufacturing_year": row.get("manufacturing_year"),
                "chassis_number": row.get("chassis_number"),
                "engine_number": row.get("engine_number"),
                "owner_name": row.get("owner_name"),
                "owner_phone": row.get("owner_phone"),
                "vendor_name": row.get("vendor_name"),
                "vendor_contact": row.get("vendor_contact"),
                "gps_enabled": row.get("gps_enabled", True),
                "realtime_tracking_enabled": row.get("realtime_tracking_enabled", True),
                "deployment_allowed": row.get("deployment_allowed", True),
            }

            try:
                self.vehicle_service.create_vehicle(payload, importer_id)
                created_count += 1
            except Exception as e:
                db.session.rollback()
                failed_count += 1

        # Audit the action
        ip_address = request.remote_addr if request else None
        user_agent = request.user_agent.string if request and request.user_agent else None
        
        details = {
            "total_rows": len(valid_rows),
            "succeeded": created_count,
            "failed": failed_count,
        }

        audit_entry = AuditLog(
            user_id=importer_id,
            action="BULK_VEHICLE_IMPORT",
            ip_address=ip_address,
            user_agent=user_agent,
            details=details
        )
        
        db.session.add(audit_entry)
        db.session.commit()

        return {
            "created": created_count,
            "failed": failed_count
        }
