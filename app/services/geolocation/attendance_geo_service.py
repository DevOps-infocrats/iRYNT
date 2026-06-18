from datetime import timedelta

from sqlalchemy import or_

from app.extensions import db
from app.modules.approvals.models import ApprovalRequest
from app.modules.auth.models import Role, User
from app.modules.deployments.models import VehicleDeployment
from app.modules.drivers.models import DriverActivityLog, DriverVehicleAssignment
from app.services.geolocation.geofence_service import GeofenceService
from app.services.geolocation.location_validation_service import LocationValidationService
from app.modules.attendance.utils import get_india_now


REVIEW_GEO_STATUSES = {'OUTSIDE_GEOFENCE', 'LOW_ACCURACY', 'MANUAL_OVERRIDE'}


class AttendanceGeoService:
    def __init__(self):
        self.geofence_service = GeofenceService()
        self.location_validation_service = LocationValidationService()

    def validate_attendance_location(self, driver_profile, location_payload):
        deployment = self._get_active_deployment(driver_profile)

        from app.domain.auth.policies.auth_policy import has_role
        is_helper = has_role(driver_profile.user, 'Helper') if (driver_profile and driver_profile.user) else False

        active_helper_assignment = None
        if is_helper:
            from app.modules.deployments.models import HelperAssignment
            active_helper_assignment = HelperAssignment.query.filter_by(
                helper_id=driver_profile.user_id,
                status='Active'
            ).first()
            if not active_helper_assignment and not deployment and not driver_profile.subzone_id:
                return None, 'No active deployment assignment found. Please contact your supervisor.'

        if not deployment and not is_helper:
            return None, 'Active deployment is required before attendance can be marked.'

        if not is_helper:
            assignment = self._get_active_assignment(driver_profile, deployment)
            if not assignment:
                return None, 'Active vehicle assignment is required before attendance can be marked.'

        if is_helper:
            if active_helper_assignment:
                subzone = active_helper_assignment.subzone
            elif deployment:
                subzone = deployment.subzone
            else:
                subzone = driver_profile.subzone
        else:
            subzone = (deployment.subzone if deployment else None) or driver_profile.subzone
        if not subzone:
            return self._manual_review_response(
                deployment,
                None,
                location_payload,
                'Assigned deployment has no subzone configured.' if deployment else 'No subzone configured for Helper profile.',
            ), None

        location = self.location_validation_service.parse_payload(location_payload)
        if not location['has_location']:
            return self._manual_review_response(
                deployment,
                subzone,
                location_payload,
                'Live GPS coordinates were not available.',
            ), None

        if not location['is_accuracy_acceptable']:
            return {
                'is_inside_geofence': False,
                'distance_meters': None,
                'allowed_radius': self.geofence_service.allowed_radius_for(subzone),
                'accuracy': location['accuracy'],
                'geo_status': 'LOW_ACCURACY',
                'geo_verified': False,
                'deployment': deployment,
                'subzone': subzone,
            }, None

        geofence = self.geofence_service.validate(subzone, location['latitude'], location['longitude'])
        geofence.update(
            {
                'accuracy': location['accuracy'],
                'geo_verified': geofence['geo_status'] == 'GEO_VERIFIED',
                'deployment': deployment,
                'subzone': subzone,
                'helper_assignment': active_helper_assignment,
            }
        )
        return geofence, None

    def apply_geo_result(self, attendance, action, location_payload, geo_result):
        location = self.location_validation_service.parse_payload(location_payload)
        if action == 'check_in':
            attendance.checkin_latitude = location['latitude']
            attendance.checkin_longitude = location['longitude']
        elif action == 'check_out':
            attendance.checkout_latitude = location['latitude']
            attendance.checkout_longitude = location['longitude']

        attendance.location_accuracy = geo_result.get('accuracy')
        attendance.geo_verified = geo_result.get('geo_verified', False)
        attendance.geo_status = geo_result.get('geo_status')
        attendance.geo_distance_meters = geo_result.get('distance_meters')

    def create_review_request_if_needed(self, attendance, driver_profile, geo_result, action, requested_by_id):
        if geo_result.get('geo_status') not in REVIEW_GEO_STATUSES:
            return None

        existing = ApprovalRequest.query.filter_by(
            approval_type='attendance_correction',
            entity_type='driver_attendance',
            entity_id=attendance.id,
        ).filter(ApprovalRequest.approval_status.in_(['Pending', 'Under Review', 'Escalated'])).first()
        if existing:
            return existing

        deployment = geo_result.get('deployment')
        subzone = geo_result.get('subzone')
        helper_assignment = geo_result.get('helper_assignment')

        target_company_id = driver_profile.user.company_id if driver_profile.user else None
        target_circle_id = driver_profile.circle_id or (driver_profile.user.circle_id if driver_profile.user else None)
        target_client_id = driver_profile.client_id
        target_project_id = driver_profile.project_id
        target_subzone_id = subzone.id if subzone else driver_profile.subzone_id

        if helper_assignment:
            target_company_id = helper_assignment.project.company_id if helper_assignment.project else None
            target_circle_id = helper_assignment.circle_id
            target_client_id = helper_assignment.project.client_id if helper_assignment.project else None
            target_project_id = helper_assignment.project_id
            target_subzone_id = helper_assignment.subzone_id
        elif deployment and deployment.project:
            target_company_id = deployment.project.company_id
            target_circle_id = deployment.project.circle_id
            target_client_id = deployment.project.client_id
            target_project_id = deployment.project_id
            if deployment.subzone_id:
                target_subzone_id = deployment.subzone_id

        approver = self._resolve_geo_reviewer(driver_profile, company_id=target_company_id, circle_id=target_circle_id)
        description = (
            f"Attendance {action.replace('_', ' ')} requires geo review. "
            f"Status: {geo_result.get('geo_status')}. "
            f"Distance: {geo_result.get('distance_meters') or 'N/A'} meters. "
            f"Accuracy: {geo_result.get('accuracy') or 'N/A'} meters."
        )

        approval = ApprovalRequest(
            approval_type='attendance_correction',
            module_name='attendance',
            entity_type='driver_attendance',
            entity_id=attendance.id,
            request_title=f"Geo attendance review - {driver_profile.user.username if driver_profile.user else driver_profile.id}",
            request_description=description,
            requested_by_id=requested_by_id,
            assigned_approver_id=approver.id if approver else None,
            hierarchy_scope='attendance_geo_review',
            company_id=target_company_id,
            circle_id=target_circle_id,
            client_id=target_client_id,
            project_id=target_project_id,
            subzone_id=target_subzone_id,
            priority='High' if geo_result.get('geo_status') == 'OUTSIDE_GEOFENCE' else 'Medium',
            approval_status='Under Review',
            sla_due_at=get_india_now() + timedelta(hours=8),
            remarks='Automatically flagged by live geo attendance verification.',
        )
        db.session.add(approval)
        return approval

    def log_geo_audit(self, attendance, driver_profile, geo_result, action, actor_id):
        log = DriverActivityLog(
            driver_id=driver_profile.id,
            actor_id=actor_id,
            event_type='attendance_geo_verification',
            description=f"Attendance {action} geo status: {geo_result.get('geo_status')}",
            event_metadata={
                'attendance_id': attendance.id,
                'geo_status': geo_result.get('geo_status'),
                'geo_verified': geo_result.get('geo_verified'),
                'distance_meters': geo_result.get('distance_meters'),
                'allowed_radius': geo_result.get('allowed_radius'),
                'accuracy': geo_result.get('accuracy'),
                'deployment_id': geo_result.get('deployment').id if geo_result.get('deployment') else None,
                'subzone_id': geo_result.get('subzone').id if geo_result.get('subzone') else None,
            },
        )
        db.session.add(log)

    def _manual_review_response(self, deployment, subzone, location_payload, reason):
        location = self.location_validation_service.parse_payload(location_payload)
        return {
            'is_inside_geofence': False,
            'distance_meters': None,
            'allowed_radius': self.geofence_service.allowed_radius_for(subzone) if subzone else None,
            'accuracy': location['accuracy'],
            'geo_status': 'MANUAL_OVERRIDE',
            'geo_verified': False,
            'deployment': deployment,
            'subzone': subzone,
            'reason': reason,
        }

    def _get_active_deployment(self, driver_profile):
        if not driver_profile.user_id:
            return None
        return (
            VehicleDeployment.query.filter(
                VehicleDeployment.driver_id == driver_profile.user_id,
                VehicleDeployment.status == 'Active',
                VehicleDeployment.approval_status == 'Approved',
            )
            .order_by(VehicleDeployment.actual_start.desc(), VehicleDeployment.created_at.desc())
            .first()
        )

    def _get_active_assignment(self, driver_profile, deployment):
        query = DriverVehicleAssignment.query.filter(
            DriverVehicleAssignment.driver_id == driver_profile.id,
            DriverVehicleAssignment.status == 'Active',
            DriverVehicleAssignment.released_at.is_(None),
        )
        if deployment and deployment.vehicle_id:
            query = query.filter(DriverVehicleAssignment.vehicle_id == deployment.vehicle_id)
        return query.order_by(DriverVehicleAssignment.assigned_at.desc()).first()

    def _resolve_geo_reviewer(self, driver_profile, company_id=None, circle_id=None):
        role_names = ['Key Account Manager', 'Circle KAM', 'CBH']
        query = User.query.join(Role, User.role_id == Role.id).filter(Role.name.in_(role_names))
        
        target_circle_id = circle_id or driver_profile.circle_id or (driver_profile.user.circle_id if driver_profile.user else None)
        target_company_id = company_id or (driver_profile.user.company_id if driver_profile.user else None)

        if target_circle_id:
            query = query.filter(or_(User.circle_id == target_circle_id, User.circle_id.is_(None)))
        elif target_company_id:
            query = query.filter(or_(User.company_id == target_company_id, User.company_id.is_(None)))
        return query.order_by(Role.name.asc(), User.username.asc()).first()
