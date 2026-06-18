import sys
import os
sys.path.insert(0, os.getcwd())
from app import create_app
from app.modules.deployments.assignment_dashboard_service import AssignmentDashboardService

app = create_app('development')
with app.app_context():
    vehicles = AssignmentDashboardService.get_available_vehicles()
    print(f"Available vehicles returned by service: {len(vehicles)}")
    for v in vehicles:
        print(v)
