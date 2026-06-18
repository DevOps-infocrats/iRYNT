import uuid
from datetime import datetime, timezone

from app.extensions import db


def make_uuid():
    return str(uuid.uuid4())


class Company(db.Model):
    __tablename__ = 'companies'

    id = db.Column(db.String(36), primary_key=True, default=make_uuid)
    company_name = db.Column(db.String(150), unique=True, nullable=False, index=True)
    company_code = db.Column(db.String(20), unique=True, nullable=False, index=True)
    gst_number = db.Column(db.String(15), unique=True, nullable=True, index=True)
    pan_number = db.Column(db.String(10), unique=True, nullable=True, index=True)
    email = db.Column(db.String(120), unique=True, nullable=True, index=True)
    phone = db.Column(db.String(10), unique=True, nullable=True, index=True)
    country_id = db.Column(db.String(32), nullable=True, index=True)
    state_id = db.Column(db.String(32), nullable=True, index=True)
    city_id = db.Column(db.String(32), nullable=True, index=True)
    pincode = db.Column(db.String(6), nullable=False)
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
            'company_name': self.company_name,
            'company_code': self.company_code,
            'gst_number': self.gst_number,
            'pan_number': self.pan_number,
            'email': self.email,
            'phone': self.phone,
            'country_id': self.country_id,
            'state_id': self.state_id,
            'city_id': self.city_id,
            'pincode': self.pincode,
            'status': self.status,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self):
        return f'<Company {self.company_name}>'
