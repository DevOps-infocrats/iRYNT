from app.modules.attendance.services import AttendanceService
from app.modules.drivers.models import DriverProfile
from app.modules.auth.models import User
from app.domain.auth.policies.auth_policy import has_permission
from app.modules.attendance.verification_helpers import decode_base64_image, save_verification_image
from flask import current_app

class AttendanceApiController:
    def __init__(self):
        self.attendance_service = AttendanceService()

    def mark(self, action, data, actor):
        """
        Processes check-in / check-out API request.
        :param action: 'check_in' or 'check_out'
        :param data: Parsed JSON payload dict
        :param actor: User object of the authenticated requester
        """
        driver_profile_id = data.get('driver_profile_id')
        driver_profile = None
        if driver_profile_id:
            driver_profile = DriverProfile.query.get(driver_profile_id)
            if not driver_profile:
                # If they passed User ID instead of DriverProfile ID
                driver_profile = DriverProfile.query.filter_by(user_id=driver_profile_id).first()
        
        if not driver_profile:
            # Fallback to the authenticated actor's own profile
            driver_profile = DriverProfile.query.filter_by(user_id=actor.id).first()

        if not driver_profile:
            return {'success': False, 'message': 'Driver profile could not be found.', 'status': 404}

        # RBAC Check: Ensure the actor can only mark their own attendance, unless they have attendance.override
        if driver_profile.user_id != actor.id and not has_permission(actor, 'attendance.override'):
            return {'success': False, 'message': 'You do not have permission to mark attendance for this user.', 'status': 403}

        # Decode base64 image captures if provided
        selfie_data = data.get('selfie_data')
        dashboard_data = data.get('dashboard_data')

        selfie_file = None
        dashboard_file = None
        try:
            if selfie_data and selfie_data.strip():
                selfie_file = decode_base64_image(selfie_data, 'selfie.jpg')
            if dashboard_data and dashboard_data.strip():
                dashboard_file = decode_base64_image(dashboard_data, 'dashboard.jpg')
        except ValueError as exc:
            return {'success': False, 'message': f"Image decoding failed: {str(exc)}", 'status': 400}

        # Save files to disk
        upload_folder = current_app.config['DRIVER_DOCUMENT_UPLOAD_FOLDER']
        selfie_path = None
        dashboard_path = None

        try:
            if selfie_file:
                selfie_path = save_verification_image(selfie_file, upload_folder, driver_profile.id)
            if dashboard_file:
                dashboard_path = save_verification_image(dashboard_file, upload_folder, driver_profile.id)
        except Exception as exc:
            return {'success': False, 'message': f"Failed to save verification images: {str(exc)}", 'status': 500}

        # Extract odometer & geolocation coordinates
        odometer = data.get('odometer')
        if odometer is not None:
            try:
                odometer = float(odometer)
            except ValueError:
                odometer = None

        location_payload = {
            'latitude': str(data.get('latitude')),
            'longitude': str(data.get('longitude')),
            'accuracy': str(data.get('accuracy')),
        }

        # Call service to mark attendance
        attendance, error = self.attendance_service.mark_attendance(
            driver_profile_id=driver_profile.id,
            action=action,
            location_payload=location_payload,
            actor_id=actor.id,
            selfie_path=selfie_path,
            dashboard_path=dashboard_path,
            odometer=odometer
        )

        if error:
            return {'success': False, 'message': error, 'status': 400}

        return {'success': True, 'attendance': attendance, 'status': 200}
