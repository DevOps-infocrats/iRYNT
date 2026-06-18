import uuid
from datetime import datetime, timezone

from app.extensions import db


def make_uuid():
	return str(uuid.uuid4())


class Circle(db.Model):
	__tablename__ = 'circles'
	__table_args__ = (db.UniqueConstraint('company_id', 'circle_code', name='uix_company_circle_code'),)

	id = db.Column(db.String(36), primary_key=True, default=make_uuid)
	company_id = db.Column(db.String(36), db.ForeignKey('companies.id'), nullable=False, index=True)
	circle_code = db.Column(db.String(20), nullable=False, index=True)
	circle_name = db.Column(db.String(150), nullable=False)
	regional_manager = db.Column(db.String(150), nullable=True)
	email = db.Column(db.String(120), nullable=True, index=True)
	phone = db.Column(db.String(15), nullable=True, index=True)
	address = db.Column(db.Text, nullable=True)
	status = db.Column(db.String(20), nullable=False, default='Active')
	created_by = db.Column(db.String(36), nullable=True, index=True)
	created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
	updated_at = db.Column(
		db.DateTime(timezone=True),
		default=lambda: datetime.now(timezone.utc),
		onupdate=lambda: datetime.now(timezone.utc),
		nullable=False,
	)

	def to_dict(self):
		return {
			'id': self.id,
			'company_id': self.company_id,
			'circle_code': self.circle_code,
			'circle_name': self.circle_name,
			'regional_manager': self.regional_manager,
			'email': self.email,
			'phone': self.phone,
			'address': self.address,
			'status': self.status,
			'created_by': self.created_by,
			'created_at': self.created_at.isoformat() if self.created_at else None,
			'updated_at': self.updated_at.isoformat() if self.updated_at else None,
		}

	def __repr__(self):
		return f'<Circle {self.circle_name} ({self.circle_code})>'
