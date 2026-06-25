from app.extensions import db
from app.modules.subzones.models import Subzone


class SubzoneRepository:
    @staticmethod
    def create(data):
        subzone = Subzone(**data)
        db.session.add(subzone)
        db.session.commit()
        return subzone

    @staticmethod
    def get_by_id(subzone_id):
        return Subzone.query.filter_by(id=subzone_id).first()

    @staticmethod
    def list_active(company_id=None, circle_id=None, status='Active', limit=None, offset=0):
        query = Subzone.query.filter_by(status=status)
        if company_id:
            query = query.filter_by(company_id=company_id)
        if circle_id:
            query = query.filter_by(circle_id=circle_id)
        query = query.order_by(Subzone.created_at.desc())
        if limit:
            query = query.limit(limit).offset(offset)
        return query.all()

    @staticmethod
    def list_by_project(company_id, circle_id, client_id, project_id, status='Active', limit=None, offset=0):
        query = Subzone.query.filter_by(
            company_id=company_id,
            circle_id=circle_id,
            client_id=client_id,
            project_id=project_id,
            status=status,
        )
        query = query.order_by(Subzone.created_at.desc())
        if limit:
            query = query.limit(limit).offset(offset)
        return query.all()

    @staticmethod
    def update(subzone_id, data):
        subzone = Subzone.query.filter_by(id=subzone_id).first()
        if not subzone:
            return None

        for key, value in data.items():
            if hasattr(subzone, key):
                setattr(subzone, key, value)

        db.session.commit()
        return subzone

    @staticmethod
    def delete(subzone_id):
        subzone = Subzone.query.filter_by(id=subzone_id).first()
        if not subzone:
            return False
        subzone.status = 'Closed'
        db.session.commit()
        return True

    @staticmethod
    def exists_by_code(company_id, circle_id, client_id, project_id, code):
        return Subzone.query.filter_by(
            company_id=company_id,
            circle_id=circle_id,
            client_id=client_id,
            project_id=project_id,
            subzone_code=code.upper(),
            status='Active',
        ).first() is not None

