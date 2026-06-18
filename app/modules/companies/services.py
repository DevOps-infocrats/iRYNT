from app.modules.companies.repository import CompanyRepository


class CompanyService:
    def __init__(self, repository=None):
        self.repository = repository or CompanyRepository()

    def list_companies(self):
        return self.repository.list_all()

    def get_company(self, company_id):
        return self.repository.get_by_id(company_id)

    def create_company(self, payload):
        return self.repository.create(payload)

    def update_company(self, company, payload):
        return self.repository.update(company, payload)

    def delete_company(self, company):
        return self.repository.delete(company)
