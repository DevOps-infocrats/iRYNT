from app.modules.vehicles.repository import VehicleRepository
from app.modules.vehicles.models import Vehicle

vehicle_repository = VehicleRepository()


def normalize_vehicle_payload(payload):
    payload['vehicle_number'] = (payload.get('vehicle_number') or '').strip().upper()
    payload['vehicle_brand'] = (payload.get('vehicle_brand') or '').strip() or None
    payload['vehicle_model'] = (payload.get('vehicle_model') or '').strip() or None
    payload['chassis_number'] = (payload.get('chassis_number') or '').strip() or None
    payload['engine_number'] = (payload.get('engine_number') or '').strip() or None
    payload['owner_name'] = (payload.get('owner_name') or '').strip() or None
    payload['owner_phone'] = (payload.get('owner_phone') or '').strip() or None
    payload['vendor_name'] = (payload.get('vendor_name') or '').strip() or None
    payload['vendor_contact'] = (payload.get('vendor_contact') or '').strip() or None
    payload['current_deployment'] = (payload.get('current_deployment') or '').strip() or None
    return payload


class VehicleService:
    def list_vehicles(self, company_id=None, limit=20, offset=0):
        return vehicle_repository.list_vehicles(company_id=company_id, limit=limit, offset=offset)

    def get_vehicle(self, vehicle_id):
        return vehicle_repository.get_vehicle(vehicle_id)

    def create_vehicle(self, payload, created_by):
        payload = normalize_vehicle_payload(payload)
        payload['created_by'] = created_by
        return vehicle_repository.create_vehicle(payload)

    def update_vehicle(self, vehicle_id, payload):
        vehicle = self.get_vehicle(vehicle_id)
        if not vehicle:
            return None
        payload = normalize_vehicle_payload(payload)
        return vehicle_repository.update_vehicle(vehicle, payload)

    def exists_by_vehicle_number(self, company_id, circle_id, client_id, project_id, subzone_id, vehicle_number, exclude_id=None):
        return vehicle_repository.exists_vehicle_number(
            company_id,
            circle_id,
            client_id,
            project_id,
            subzone_id,
            vehicle_number.strip().upper(),
            exclude_id=exclude_id,
        )

    def get_vehicle_summary(self, vehicle):
        compliance_states = [
            vehicle.insurance_status,
            vehicle.fitness_status,
            vehicle.permit_status,
            vehicle.puc_status,
            vehicle.verification_status,
        ]
        pending_compliance = sum(1 for state in compliance_states if state and state != 'Valid')

        return {
            'deployment_hours': 48,
            'trips_completed': 12,
            'fuel_usage': 586,
            'operational_efficiency': 88,
            'attendance_linked': 1 if vehicle.attendance_linked else 0,
            'pending_compliance': pending_compliance,
            'gps_status': 'Connected' if vehicle.gps_enabled else 'Disconnected',
            'last_activity': vehicle.last_activity or 'No recent activity',
            'current_location': vehicle.current_location or 'Not available',
            'last_gps_ping': vehicle.last_gps_ping.isoformat() if vehicle.last_gps_ping else None,
        }

    def get_dashboard_metrics(self, company_id=None):
        vehicles = self.list_vehicles(company_id=company_id, limit=100)
        return {
            'total_vehicles': len(vehicles),
            'available': sum(1 for v in vehicles if v.status == 'Available'),
            'deployed': sum(1 for v in vehicles if v.status == 'Deployed'),
            'maintenance': sum(1 for v in vehicles if v.status == 'Maintenance'),
            'inactive': sum(1 for v in vehicles if v.status == 'Inactive'),
        }
