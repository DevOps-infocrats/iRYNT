from dataclasses import dataclass
from typing import Optional


@dataclass
class VehicleDTO:
    id: str
    company_id: str
    circle_id: str
    client_id: str
    project_id: str
    subzone_id: str
    vehicle_number: str
    vehicle_type: str
    vehicle_category: str
    vehicle_brand: str
    vehicle_model: str
    manufacturing_year: Optional[str] = None
    chassis_number: Optional[str] = None
    engine_number: Optional[str] = None
    owner_name: Optional[str] = None
    owner_phone: Optional[str] = None
    vendor_name: Optional[str] = None
    vendor_contact: Optional[str] = None
    gps_enabled: bool = False
    realtime_tracking_enabled: bool = False
    deployment_allowed: bool = False
    attendance_linked: bool = False
    fuel_tracking_enabled: bool = False
    geo_fencing_enabled: bool = False
    incident_monitoring_enabled: bool = False
    maintenance_tracking_enabled: bool = False
    load_capacity: Optional[int] = None
    passenger_capacity: Optional[int] = None
    fuel_capacity: Optional[int] = None
    operational_capacity: Optional[int] = None
    status: Optional[str] = None
    insurance_status: Optional[str] = None
    fitness_status: Optional[str] = None
    permit_status: Optional[str] = None
    puc_status: Optional[str] = None
    verification_status: Optional[str] = None
    assigned_driver: Optional[str] = None
    current_deployment: Optional[str] = None

    def to_dict(self):
        return self.__dict__
