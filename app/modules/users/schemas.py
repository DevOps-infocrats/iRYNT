class UserSchema:
    @staticmethod
    def summary(user):
        return {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'role': user.primary_role.name if user.primary_role else None,
            'company_id': user.company_id,
            'circle_id': user.circle_id,
            'is_active': user.is_active,
            'is_verified': user.is_verified,
        }


class UserProfileSchema:
    @staticmethod
    def details(profile_data):
        user = profile_data.get('user')
        return {
            'id': user.id,
            'full_name': user.username,
            'email': user.email,
            'phone': user.phone,
            'role': user.primary_role.name if user.primary_role else 'Unassigned',
            'company': profile_data['hierarchy']['company'],
            'circle': profile_data['hierarchy']['circle'],
            'permissions': profile_data.get('permissions', []),
        }

