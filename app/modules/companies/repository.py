from app.modules.companies.models import Company
from app.extensions import db


class CompanyRepository:
    def get_by_id(self, company_id):
        return Company.query.get(company_id)

    def list_all(self):
        return Company.query.order_by(Company.company_name).all()

    def find_by_field(self, field_name, value, exclude_id=None):
        if not value:
            return None
        query = Company.query.filter(getattr(Company, field_name) == value)
        if exclude_id:
            query = query.filter(Company.id != exclude_id)
        return query.first()

    def exists_by_field(self, field_name, value, exclude_id=None):
        return self.find_by_field(field_name, value, exclude_id) is not None

    def create(self, data):
        company = Company(**data)
        db.session.add(company)
        db.session.commit()
        return company

    def update(self, company, data):
        for key, value in data.items():
            setattr(company, key, value)
        db.session.commit()
        return company

    def delete(self, company):
        db.session.delete(company)
        db.session.commit()
