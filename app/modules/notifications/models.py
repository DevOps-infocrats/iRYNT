from datetime import datetime
from app.extensions import db


class Notification(db.Model):
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=True)
    type = db.Column(db.String(64), nullable=False, default='system')
    module = db.Column(db.String(64), nullable=True)
    message = db.Column(db.Text, nullable=False)
    priority = db.Column(db.String(16), nullable=False, default='info')
    meta = db.Column(db.JSON, nullable=True)
    related_type = db.Column(db.String(64), nullable=True)
    related_id = db.Column(db.String(64), nullable=True)
    route = db.Column(db.String(256), nullable=True)
    is_read = db.Column(db.Boolean, default=False, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    # Optional scope fields to reuse existing hierarchy filtering
    company_id = db.Column(db.String(36), nullable=True)
    circle_id = db.Column(db.String(36), nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'type': self.type,
            'module': self.module,
            'message': self.message,
            'priority': self.priority,
            'metadata': self.meta,
            'related_type': self.related_type,
            'related_id': self.related_id,
            'route': self.route,
            'is_read': self.is_read,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'company_id': self.company_id,
            'circle_id': self.circle_id,
        }

    def __repr__(self):
        return f"<Notification {self.id} {self.type} {self.priority}>"
