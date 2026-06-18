from app.extensions import db
from app.modules.projects.models import Project


class ProjectRepository:
    """Repository layer for Project model"""

    @staticmethod
    def create(data):
        """Create a new project"""
        project = Project(**data)
        db.session.add(project)
        db.session.commit()
        return project

    @staticmethod
    def get_by_id(project_id):
        """Get project by ID"""
        return Project.query.filter_by(id=project_id).first()

    @staticmethod
    def get_by_code_and_client(company_id, client_id, project_code):
        """Get project by code within client"""
        return Project.query.filter_by(
            company_id=company_id,
            client_id=client_id,
            project_code=project_code.upper(),
            status='Active'
        ).first()

    @staticmethod
    def list_by_company(company_id=None, status=None, limit=None, offset=0):
        """Get all projects for a company"""
        query = Project.query
        if company_id:
            query = query.filter_by(company_id=company_id)
        if status:
            query = query.filter_by(status=status)
        query = query.order_by(Project.created_at.desc())
        if limit:
            query = query.limit(limit).offset(offset)
        return query.all()

    @staticmethod
    def list_by_circle(company_id, circle_id, status='Active', limit=None, offset=0):
        """Get all projects for a circle"""
        query = Project.query.filter_by(
            company_id=company_id,
            circle_id=circle_id,
            status=status
        )
        query = query.order_by(Project.created_at.desc())
        if limit:
            query = query.limit(limit).offset(offset)
        return query.all()

    @staticmethod
    def list_by_client(company_id, circle_id, client_id, status='Active', limit=None, offset=0):
        """Get all projects for a client"""
        query = Project.query.filter_by(
            company_id=company_id,
            circle_id=circle_id,
            client_id=client_id,
            status=status
        )
        query = query.order_by(Project.created_at.desc())
        if limit:
            query = query.limit(limit).offset(offset)
        return query.all()

    @staticmethod
    def list_active(limit=None, offset=0):
        """Get all active projects"""
        query = Project.query.filter_by(status='Active')
        query = query.order_by(Project.created_at.desc())
        if limit:
            query = query.limit(limit).offset(offset)
        return query.all()

    @staticmethod
    def search(search_term, company_id=None, limit=20):
        """Search projects by code or name"""
        query = Project.query.filter_by(status='Active')
        
        if company_id:
            query = query.filter_by(company_id=company_id)
        
        if search_term:
            like_term = f"%{search_term}%"
            query = query.filter(
                (Project.project_code.ilike(like_term)) |
                (Project.project_name.ilike(like_term))
            )
        
        return query.order_by(Project.project_name).limit(limit).all()

    @staticmethod
    def update(project_id, data):
        """Update a project"""
        project = Project.query.filter_by(id=project_id).first()
        if not project:
            return None
        
        for key, value in data.items():
            if hasattr(project, key):
                setattr(project, key, value)
        
        db.session.commit()
        return project

    @staticmethod
    def delete(project_id):
        """Delete a project (soft delete by marking inactive)"""
        project = Project.query.filter_by(id=project_id).first()
        if not project:
            return False
        
        project.status = 'Closed'
        db.session.commit()
        return True

    @staticmethod
    def exists_by_code(company_id, client_id, project_code):
        """Check if project code exists for a client"""
        return Project.query.filter_by(
            company_id=company_id,
            client_id=client_id,
            project_code=project_code.upper(),
            status='Active'
        ).first() is not None

    @staticmethod
    def count_by_status(status='Active'):
        """Count projects by status"""
        return Project.query.filter_by(status=status).count()

    @staticmethod
    def count_by_company(company_id, status='Active'):
        """Count projects for a company"""
        return Project.query.filter_by(
            company_id=company_id,
            status=status
        ).count()

    @staticmethod
    def get_summary(company_id, circle_id, client_id):
        """Get project summary statistics"""
        total = Project.query.filter_by(
            company_id=company_id,
            circle_id=circle_id,
            client_id=client_id
        ).count()
        
        active = Project.query.filter_by(
            company_id=company_id,
            circle_id=circle_id,
            client_id=client_id,
            status='Active'
        ).count()
        
        planning = Project.query.filter_by(
            company_id=company_id,
            circle_id=circle_id,
            client_id=client_id,
            status='Planning'
        ).count()
        
        return {
            'total': total,
            'active': active,
            'planning': planning,
        }

