from flask import Blueprint, jsonify, render_template, request
from flask_login import login_required, current_user

from app.core.decorators import permission_required
from app.infrastructure.repositories.notifications.notifications_repository import NotificationsRepository

notifications_bp = Blueprint('notifications', __name__, url_prefix='/notifications')


@notifications_bp.route('/unread_count', methods=['GET'])
@login_required
def unread_count():
	count = NotificationsRepository.unread_count_for_user(current_user.id)
	return jsonify({'unread': count})


@notifications_bp.route('/feed', methods=['GET'])
@login_required
def feed():
	try:
		from app.services.compliance.alerts_service import trigger_lightweight_compliance_checks
		trigger_lightweight_compliance_checks()
	except Exception:
		pass
	page = request.args.get('page', 1, type=int)
	per_page = request.args.get('per_page', 10, type=int)
	filters = {}
	is_read = request.args.get('is_read')
	if is_read is not None:
		filters['is_read'] = True if is_read in ['1', 'true', 'True'] else False

	# Support both legacy 'type' filtering and new category-based 'module' filtering
	category = request.args.get('category')
	notif_type = request.args.get('type')
	if category:
		# Apply both module and type filters for compatibility
		filters['module'] = category
		# Also filter by type if notifications use type field
		filters.setdefault('type', category)
	if notif_type:
		filters['type'] = notif_type

	result = NotificationsRepository.list_for_user(current_user.id, filters=filters, page=page, per_page=per_page)
	return jsonify(result)


def migrate_existing_notifications():
	try:
		from app.modules.notifications.models import Notification
		from app.extensions import db
		
		# 1. Update module 'attendance' to type 'attendance'
		Notification.query.filter(Notification.type == 'system', Notification.module == 'attendance').update({Notification.type: 'attendance'}, synchronize_session=False)
		# 2. Update module 'deployments' to type 'deployment'
		Notification.query.filter(Notification.type == 'system', Notification.module == 'deployments').update({Notification.type: 'deployment'}, synchronize_session=False)
		# 3. Update approvals containing escalat
		Notification.query.filter(Notification.type == 'system', Notification.module == 'approvals', Notification.message.ilike('%escalat%')).update({Notification.type: 'escalation'}, synchronize_session=False)
		# 4. Update other approvals
		Notification.query.filter(Notification.type == 'system', Notification.module == 'approvals').update({Notification.type: 'approval'}, synchronize_session=False)
		# 5. Update documents/compliance/expiry/vehicles messages
		Notification.query.filter(
			Notification.type == 'system',
			(Notification.module == 'documents') |
			(Notification.module == 'compliance') |
			(Notification.module == 'vehicles') |
			Notification.message.ilike('%expiry%') |
			Notification.message.ilike('%expired%') |
			Notification.message.ilike('%km%') |
			Notification.message.ilike('%odometer%')
		).update({Notification.type: 'expiry'}, synchronize_session=False)
		db.session.commit()
	except Exception:
		pass


@notifications_bp.route('/', methods=['GET'])
@login_required
@permission_required('notifications.view')
def index():
	try:
		from app.services.compliance.alerts_service import trigger_lightweight_compliance_checks
		trigger_lightweight_compliance_checks()
	except Exception:
		pass
	migrate_existing_notifications()
	return render_template('notifications/index.html', active_page='notifications', page_title='Notifications Center')


@notifications_bp.route('/system', methods=['GET'])
@login_required
@permission_required('notifications.view')
def system_notifications():
	migrate_existing_notifications()
	return render_template(
		'notifications/index.html',
		category='system',
		page_title='System Notifications',
		active_page='system_notifications'
	)


@notifications_bp.route('/expiry', methods=['GET'])
@login_required
@permission_required('notifications.view')
def expiry_alerts():
	migrate_existing_notifications()
	return render_template(
		'notifications/index.html',
		category='expiry',
		page_title='Expiry Alerts',
		active_page='expiry_alerts'
	)


@notifications_bp.route('/attendance', methods=['GET'])
@login_required
@permission_required('notifications.view')
def attendance_alerts():
	migrate_existing_notifications()
	return render_template(
		'notifications/index.html',
		category='attendance',
		page_title='Attendance Alerts',
		active_page='attendance_alerts'
	)


@notifications_bp.route('/deployment', methods=['GET'])
@login_required
@permission_required('notifications.view')
def deployment_alerts():
	migrate_existing_notifications()
	return render_template(
		'notifications/index.html',
		category='deployment',
		page_title='Deployment Alerts',
		active_page='deployment_alerts'
	)


@notifications_bp.route('/mark_all_read', methods=['POST'])
@login_required
def mark_all_read():
	updated = NotificationsRepository.mark_all_read_for_user(current_user.id)
	return jsonify({'updated': updated})

