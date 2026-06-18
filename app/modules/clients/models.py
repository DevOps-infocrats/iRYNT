import uuid
from datetime import datetime, timezone

from app.extensions import db


def make_uuid():
    return str(uuid.uuid4())


class Client(db.Model):
    __tablename__ = 'clients'
    __table_args__ = (
        db.UniqueConstraint('company_id', 'circle_id', 'client_code', name='uix_company_circle_client_code'),
    )

    id = db.Column(db.String(36), primary_key=True, default=make_uuid)
    company_id = db.Column(db.String(36), db.ForeignKey('companies.id'), nullable=False, index=True)
    circle_id = db.Column(db.String(36), db.ForeignKey('circles.id'), nullable=False, index=True)
    client_code = db.Column(db.String(20), nullable=False, index=True)
    client_name = db.Column(db.String(150), nullable=False)
    primary_contact = db.Column(db.String(150), nullable=True)
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

    company = db.relationship('Company', foreign_keys=[company_id], lazy='joined')
    circle = db.relationship('Circle', foreign_keys=[circle_id], lazy='joined')

    def to_dict(self):
        return {
            'id': self.id,
            'company_id': self.company_id,
            'circle_id': self.circle_id,
            'client_code': self.client_code,
            'client_name': self.client_name,
            'primary_contact': self.primary_contact,
            'email': self.email,
            'phone': self.phone,
            'address': self.address,
            'status': self.status,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self):
        return f'<Client {self.client_name} ({self.client_code})>'
