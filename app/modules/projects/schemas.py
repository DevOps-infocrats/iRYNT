from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional


@dataclass
class ProjectDTO:
    """Data Transfer Object for Project"""
    id: str
    company_id: str
    circle_id: str
    client_id: str
    project_code: str
    project_name: str
    project_type: str
    status: str
    start_date: date
    end_date: Optional[date]
    expected_completion_date: Optional[date]
    operational_shift: Optional[str]
    country: Optional[str]
    state: Optional[str]
    city: Optional[str]
    pincode: Optional[str]
    full_address: Optional[str]
    deployment_allowed: bool
    attendance_required: bool
    gps_tracking_enabled: bool
    realtime_monitoring_enabled: bool
    geo_fencing_enabled: bool
    workflow_approval_enabled: bool
    document_verification_required: bool
    shift_based_attendance: bool
    max_vehicles: Optional[int]
    max_drivers: Optional[int]
    deployment_capacity: Optional[int]
    required_vehicle_types: Optional[str]
    operational_capacity: Optional[int]
    project_manager: Optional[str]
    operational_head: Optional[str]
    contact_number: Optional[str]
    operational_email: Optional[str]
    created_by: Optional[str]
    created_at: datetime
    updated_at: datetime
    updated_by: Optional[str]

    @classmethod
    def from_model(cls, project):
        """Create DTO from Project model"""
        return cls(
            id=project.id,
            company_id=project.company_id,
            circle_id=project.circle_id,
            client_id=project.client_id,
            project_code=project.project_code,
            project_name=project.project_name,
            project_type=project.project_type,
            status=project.status,
            start_date=project.start_date,
            end_date=project.end_date,
            expected_completion_date=project.expected_completion_date,
            operational_shift=project.operational_shift,
            country=project.country,
            state=project.state,
            city=project.city,
            pincode=project.pincode,
            full_address=project.full_address,
            deployment_allowed=project.deployment_allowed,
            attendance_required=project.attendance_required,
            gps_tracking_enabled=project.gps_tracking_enabled,
            realtime_monitoring_enabled=project.realtime_monitoring_enabled,
            geo_fencing_enabled=project.geo_fencing_enabled,
            workflow_approval_enabled=project.workflow_approval_enabled,
            document_verification_required=project.document_verification_required,
            shift_based_attendance=project.shift_based_attendance,
            max_vehicles=project.max_vehicles,
            max_drivers=project.max_drivers,
            deployment_capacity=project.deployment_capacity,
            required_vehicle_types=project.required_vehicle_types,
            operational_capacity=project.operational_capacity,
            project_manager=project.project_manager,
            operational_head=project.operational_head,
            contact_number=project.contact_number,
            operational_email=project.operational_email,
            created_by=project.created_by,
            created_at=project.created_at,
            updated_at=project.updated_at,
            updated_by=project.updated_by,
        )

