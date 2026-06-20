from app import create_app
from app.extensions import db
from app.modules.companies.models import Company
from app.modules.circles.models import Circle
from app.modules.projects.models import Project

app = create_app()  # default config (development)
with app.app_context():
    print("Default context (Development) counts:")
    print("Active Companies:", Company.query.filter_by(status='Active').count())
    print("Active Circles:", Circle.query.filter_by(status='Active').count())
    print("Active Projects:", Project.query.filter_by(status='Active').count())
    
    print("\nAll Companies:")
    for c in Company.query.all():
        print(f"  Name: {c.company_name}, Status: {c.status}")
        
    print("\nAll Circles:")
    for c in Circle.query.all():
        print(f"  Name: {c.circle_name}, Status: {c.status}")

    print("\nAll Projects:")
    for p in Project.query.all():
        print(f"  Name: {p.project_name}, Status: {p.status}")
