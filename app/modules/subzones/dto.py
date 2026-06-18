from dataclasses import dataclass


@dataclass
class SubzoneDTO:
    company_id: str
    circle_id: str
    client_id: str
    project_id: str
    subzone_code: str
    subzone_name: str
    subzone_type: str
    status: str
    country: str = None
    state: str = None
    city: str = None
    pincode: str = None
    full_address: str = None
    latitude: str = None
    longitude: str = None
    geo_fencing_enabled: bool = False
    allowed_radius: int = None
    attendance_radius: int = None
    gps_validation: bool = False
    restricted_movement_detection: bool = False
    max_vehicles: int = None
    max_drivers: int = None
    shift_operations_enabled: bool = False
    attendance_required: bool = False
    deployment_allowed: bool = False
    realtime_tracking_enabled: bool = False
    workflow_approval_enabled: bool = False
    incident_reporting_enabled: bool = False
    vehicle_capacity: int = None
    driver_capacity: int = None
    parking_capacity: int = None
    operational_capacity: int = None
    created_by: str = None

    def to_dict(self):
        return self.__dict__
