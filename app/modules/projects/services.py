from app.modules.projects.repository import ProjectRepository
from app.modules.projects.models import Project


class ProjectService:
    """Service layer for Project business logic"""

    def __init__(self):
        self.repository = ProjectRepository()

    def create_project(self, data, created_by):
        """Create a new project with audit data"""
        data['created_by'] = created_by
        # Auto uppercase project code
        if 'project_code' in data:
            data['project_code'] = data['project_code'].strip().upper()
        
        return self.repository.create(data)

    def get_project(self, project_id):
        """Get project by ID"""
        return self.repository.get_by_id(project_id)

    def update_project(self, project_id, data, updated_by):
        """Update a project"""
        # Auto uppercase project code if provided
        if 'project_code' in data:
            data['project_code'] = data['project_code'].strip().upper()
        
        data['updated_by'] = updated_by
        return self.repository.update(project_id, data)

    def delete_project(self, project_id):
        """Delete a project"""
        return self.repository.delete(project_id)

    def list_projects_by_company(self, company_id=None, circle_id=None, status=None, limit=None, offset=0):
        """List all projects for a company / circle"""
        return self.repository.list_by_company(company_id=company_id, circle_id=circle_id, status=status, limit=limit, offset=offset)

    def list_projects_by_circle(self, company_id, circle_id, status='Active', limit=None, offset=0):
        """List all projects for a circle"""
        return self.repository.list_by_circle(company_id, circle_id, status, limit, offset)

    def list_projects_by_client(self, company_id, circle_id, client_id, status='Active', limit=None, offset=0):
        """List all projects for a client"""
        return self.repository.list_by_client(company_id, circle_id, client_id, status, limit, offset)

    def search_projects(self, search_term, company_id=None, limit=20):
        """Search projects"""
        return self.repository.search(search_term, company_id, limit)

    def get_project_summary(self, company_id, circle_id, client_id):
        """Get project summary statistics"""
        return self.repository.get_summary(company_id, circle_id, client_id)

    def project_code_exists(self, company_id, client_id, project_code):
        """Check if project code exists"""
        return self.repository.exists_by_code(company_id, client_id, project_code)

    def validate_hierarchy(self, company_id, circle_id, client_id):
        """Validate company-circle-client hierarchy"""
        from app.modules.companies.models import Company
        from app.modules.circles.models import Circle
        from app.modules.clients.models import Client

        company = Company.query.filter_by(id=company_id, status='Active').first()
        if not company:
            return False, 'Invalid company'

        circle = Circle.query.filter_by(id=circle_id, company_id=company_id, status='Active').first()
        if not circle:
            return False, 'Circle does not belong to company or is inactive'

        client = Client.query.filter_by(id=client_id, company_id=company_id, circle_id=circle_id, status='Active').first()
        if not client:
            return False, 'Client does not belong to company/circle or is inactive'

        return True, 'Valid'


# Create singleton instance
project_service = ProjectService()

