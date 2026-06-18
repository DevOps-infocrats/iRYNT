from math import asin, cos, radians, sin, sqrt


EARTH_RADIUS_METERS = 6371000


def haversine_distance_meters(origin_latitude, origin_longitude, target_latitude, target_longitude):
    """Return distance in meters between two latitude/longitude points."""
    origin_lat = radians(float(origin_latitude))
    origin_lon = radians(float(origin_longitude))
    target_lat = radians(float(target_latitude))
    target_lon = radians(float(target_longitude))

    lat_delta = target_lat - origin_lat
    lon_delta = target_lon - origin_lon

    value = (
        sin(lat_delta / 2) ** 2
        + cos(origin_lat) * cos(target_lat) * sin(lon_delta / 2) ** 2
    )
    return 2 * EARTH_RADIUS_METERS * asin(sqrt(value))


class GeofenceService:
    def calculate_distance(self, subzone, latitude, longitude):
        return haversine_distance_meters(subzone.latitude, subzone.longitude, latitude, longitude)

    def allowed_radius_for(self, subzone):
        return subzone.attendance_radius or subzone.allowed_radius

    def has_geofence(self, subzone):
        return bool(
            subzone
            and subzone.latitude
            and subzone.longitude
            and self.allowed_radius_for(subzone)
        )

    def validate(self, subzone, latitude, longitude):
        if not self.has_geofence(subzone):
            return {
                'is_inside_geofence': False,
                'distance_meters': None,
                'allowed_radius': None,
                'geo_status': 'MANUAL_OVERRIDE',
            }

        distance = self.calculate_distance(subzone, latitude, longitude)
        allowed_radius = self.allowed_radius_for(subzone)

        return {
            'is_inside_geofence': distance <= allowed_radius,
            'distance_meters': round(distance, 2),
            'allowed_radius': allowed_radius,
            'geo_status': 'GEO_VERIFIED' if distance <= allowed_radius else 'OUTSIDE_GEOFENCE',
        }

