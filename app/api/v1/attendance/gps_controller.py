from app.modules.deployments.models import VehicleDeployment
from app.modules.vehicles.models import Vehicle
from app.extensions import db
from datetime import datetime

class GpsApiController:
    def sync_gps(self, data, actor):
        """
        Synchronizes a list of GPS coordinates for a deployment.
        :param data: Parsed JSON payload dict containing deployment_id and coordinates list
        :param actor: Authenticated User object
        """
        deployment_id = data.get('deployment_id')
        deployment = VehicleDeployment.query.get(deployment_id)
        if not deployment:
            return {'success': False, 'message': 'Deployment not found.', 'status': 404}

        # RBAC Check: Ensure the user can only upload coordinates for their own deployment,
        # unless they have override or admin scopes
        from app.domain.auth.policies.auth_policy import has_permission
        if deployment.driver_id != actor.id and not has_permission(actor, 'attendance.override'):
            return {'success': False, 'message': 'You do not have permission to sync GPS data for this deployment.', 'status': 403}

        coordinates = data.get('coordinates', [])
        if not coordinates:
            return {'success': True, 'message': 'No coordinates to sync.', 'status': 200}

        # Find the latest coordinate by sorting by timestamp
        # coordinates is a list of dicts with timestamp as datetime or string
        def get_timestamp(coord):
            ts = coord.get('timestamp')
            if isinstance(ts, str):
                try:
                    return datetime.fromisoformat(ts.replace('Z', '+00:00'))
                except ValueError:
                    return datetime.utcnow()
            return ts or datetime.utcnow()

        latest_coord = max(coordinates, key=get_timestamp)
        latest_ts = get_timestamp(latest_coord)
        latest_lat = latest_coord.get('latitude')
        latest_lon = latest_coord.get('longitude')
        location_str = f"{latest_lat},{latest_lon}"

        # Update Vehicle Deployment location
        deployment.current_location = location_str
        
        # Update Vehicle status, location and last ping timestamp
        if deployment.vehicle:
            vehicle = deployment.vehicle
            vehicle.current_location = location_str
            vehicle.last_gps_ping = latest_ts
            db.session.add(vehicle)

        db.session.add(deployment)
        db.session.commit()

        return {'success': True, 'message': 'GPS telemetry synchronized successfully.', 'status': 200}
