from typing import Dict, Any, List, Optional
from app.extensions import db
from app.modules.notifications.models import Notification
from sqlalchemy import desc


class NotificationsRepository:
	@staticmethod
	def create(payload: Dict[str, Any]) -> Notification:
		# Support both `metadata` and `meta` keys in payload for compatibility
		if 'metadata' in payload and 'meta' not in payload:
			payload['meta'] = payload.pop('metadata')
		note = Notification(**payload)
		db.session.add(note)
		db.session.commit()
		return note

	@staticmethod
	def list_for_user(user_id: str = None, filters: Dict[str, Any] = None, page: int = 1, per_page: int = 10):
		query = Notification.query
		if user_id:
			try:
				from app.modules.auth.models import User
				from app.domain.auth.access import AccessManager
				user = User.query.get(user_id)
				if user:
					manager = AccessManager(user)
					is_super = manager.is_superadmin()
					has_view_all = manager.has_permission('notifications.view')

					if is_super:
						pass
					elif has_view_all:
						company_id = getattr(user, 'company_id', None)
						circle_id = getattr(user, 'circle_id', None)
						if company_id:
							query = query.filter((Notification.company_id == company_id) | (Notification.company_id.is_(None)))
						if circle_id:
							query = query.filter((Notification.circle_id == circle_id) | (Notification.circle_id.is_(None)))
					else:
						query = query.filter((Notification.user_id == user_id) | (Notification.user_id.is_(None)))
						company_id = getattr(user, 'company_id', None)
						circle_id = getattr(user, 'circle_id', None)
						if company_id:
							query = query.filter((Notification.company_id == company_id) | (Notification.company_id.is_(None)))
						if circle_id:
							query = query.filter((Notification.circle_id == circle_id) | (Notification.circle_id.is_(None)))
				else:
					query = query.filter((Notification.user_id == user_id) | (Notification.user_id.is_(None)))
			except Exception:
				query = query.filter((Notification.user_id == user_id) | (Notification.user_id.is_(None)))
		if filters:
			if 'is_read' in filters:
				query = query.filter(Notification.is_read == bool(filters['is_read']))
			if 'priority' in filters:
				query = query.filter(Notification.priority == filters['priority'])
			if 'module' in filters:
				# Match both module field and legacy type field for backward compatibility
				from sqlalchemy import or_
				query = query.filter(or_(Notification.module == filters['module'], Notification.type == filters['module']))
			if 'type' in filters:
				query = query.filter(Notification.type == filters['type'])

		page_obj = query.order_by(desc(Notification.created_at)).paginate(page=page, per_page=per_page, error_out=False)
		
		# Return summary counts
		summary = NotificationsRepository.summary_counts_for_user(user_id)
		return {
			'items': [n.to_dict() for n in page_obj.items],
			'total': page_obj.total,
			'page': page_obj.page,
			'pages': page_obj.pages,
			'summary': summary
		}

	@staticmethod
	def summary_counts_for_user(user_id: str, filters: Dict[str, Any] = None) -> dict:
		if not user_id:
			return {'unread': 0, 'critical': 0, 'approvals': 0, 'escalations': 0}
		
		query = Notification.query
		try:
			from app.modules.auth.models import User
			from app.domain.auth.access import AccessManager
			user = User.query.get(user_id)
			if user:
				manager = AccessManager(user)
				is_super = manager.is_superadmin()
				has_view_all = manager.has_permission('notifications.view')

				if is_super:
					pass
				elif has_view_all:
					company_id = getattr(user, 'company_id', None)
					circle_id = getattr(user, 'circle_id', None)
					if company_id:
						query = query.filter((Notification.company_id == company_id) | (Notification.company_id.is_(None)))
					if circle_id:
						query = query.filter((Notification.circle_id == circle_id) | (Notification.circle_id.is_(None)))
				else:
					query = query.filter((Notification.user_id == user_id) | (Notification.user_id.is_(None)))
					company_id = getattr(user, 'company_id', None)
					circle_id = getattr(user, 'circle_id', None)
					if company_id:
						query = query.filter((Notification.company_id == company_id) | (Notification.company_id.is_(None)))
					if circle_id:
						query = query.filter((Notification.circle_id == circle_id) | (Notification.circle_id.is_(None)))
			else:
				query = query.filter((Notification.user_id == user_id) | (Notification.user_id.is_(None)))
		except Exception:
			query = query.filter((Notification.user_id == user_id) | (Notification.user_id.is_(None)))

		if filters:
			if 'module' in filters:
				from sqlalchemy import or_
				query = query.filter(or_(Notification.module == filters['module'], Notification.type == filters['module']))
			if 'type' in filters:
				query = query.filter(Notification.type == filters['type'])

		unread = query.filter(Notification.is_read == False).count()
		critical = query.filter(Notification.priority == 'Critical').count()
		approvals = query.filter(Notification.type == 'approval').count()
		escalations = query.filter(Notification.type == 'escalation').count()

		return {
			'unread': unread,
			'critical': critical,
			'approvals': approvals,
			'escalations': escalations
		}

	@staticmethod
	def unread_count_for_user(user_id: str) -> int:
		if not user_id:
			return 0
		query = Notification.query
		try:
			from app.modules.auth.models import User
			from app.domain.auth.access import AccessManager
			user = User.query.get(user_id)
			if user:
				manager = AccessManager(user)
				is_super = manager.is_superadmin()
				has_view_all = manager.has_permission('notifications.view')

				if is_super:
					pass
				elif has_view_all:
					company_id = getattr(user, 'company_id', None)
					circle_id = getattr(user, 'circle_id', None)
					if company_id:
						query = query.filter((Notification.company_id == company_id) | (Notification.company_id.is_(None)))
					if circle_id:
						query = query.filter((Notification.circle_id == circle_id) | (Notification.circle_id.is_(None)))
				else:
					query = query.filter((Notification.user_id == user_id) | (Notification.user_id.is_(None)))
					company_id = getattr(user, 'company_id', None)
					circle_id = getattr(user, 'circle_id', None)
					if company_id:
						query = query.filter((Notification.company_id == company_id) | (Notification.company_id.is_(None)))
					if circle_id:
						query = query.filter((Notification.circle_id == circle_id) | (Notification.circle_id.is_(None)))
			else:
				query = query.filter((Notification.user_id == user_id) | (Notification.user_id.is_(None)))
		except Exception:
			query = query.filter((Notification.user_id == user_id) | (Notification.user_id.is_(None)))
		return query.filter(Notification.is_read == False).count()

	@staticmethod
	def mark_read(notification_id: int, user_id: Optional[int] = None) -> bool:
		note = Notification.query.get(notification_id)
		if not note:
			return False
		# Only allow marking if owned or system-wide
		if note.user_id and user_id and note.user_id != user_id:
			return False
		note.is_read = True
		db.session.add(note)
		db.session.commit()
		return True

	@staticmethod
	def mark_all_read_for_user(user_id: int) -> int:
		updated = Notification.query.filter((Notification.user_id == user_id) | (Notification.user_id.is_(None))).filter(Notification.is_read == False).update({'is_read': True})
		db.session.commit()
		return updated

