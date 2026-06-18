class DriverListSchema:
    @staticmethod
    def row(driver_data):
        return {
            'id': driver_data['id'],
            'name': driver_data['name'],
            'employee_id': driver_data['employee_id'],
            'role': driver_data['role'],
            'assigned_vehicle': driver_data['assigned_vehicle'],
            'status': driver_data['operational_status'],
            'last_activity': driver_data['last_activity'],
        }


class DriverProfileSchema:
    @staticmethod
    def details(profile_data):
        user = profile_data['user']
        return {
            'id': user.id,
            'name': user.username,
            'email': user.email,
            'phone': user.phone,
            'role': user.primary_role.name if user.primary_role else 'Driver',
            'driver_code': profile_data['driver_profile'].driver_code if profile_data['driver_profile'] else None,
        }
