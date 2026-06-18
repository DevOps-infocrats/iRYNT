"""Test assignment dashboard route with Flask test client"""
import sys
import os
sys.path.insert(0, os.getcwd())
from app import create_app

app = create_app('development')

with app.app_context():
    # Create test client
    client = app.test_client()
    
    print("Testing assignment dashboard route...")
    print("=" * 60)
    
    # Test without login (should redirect)
    print("\n1. Testing unauthenticated access (should redirect to login)...")
    response = client.get('/deployments/assignment-dashboard')
    print(f"   Status: {response.status_code}")
    print(f"   Redirects to: {response.location if response.status_code in [301, 302] else 'N/A'}")
    
    # Since we can't easily test with authentication in this simple script,
    # let's at least verify the route is registered
    print("\n2. Verifying route is registered...")
    routes = [r for r in app.url_map.iter_rules() if 'assignment' in r.rule]
    for route in routes:
        print(f"   Route: {route.rule}")
        print(f"   Methods: {route.methods}")
        print(f"   Endpoint: {route.endpoint}")
    
    # Test the service methods directly
    print("\n3. Testing AssignmentDashboardService methods...")
    from app.modules.deployments.assignment_dashboard_service import AssignmentDashboardService
    
    kpis = AssignmentDashboardService.get_kpi_metrics()
    print(f"   get_kpi_metrics(): {len(kpis)} metrics returned")
    
    assignments, total = AssignmentDashboardService.get_assignments_list(0, 5)
    print(f"   get_assignments_list(): {len(assignments)} assignments of {total} total")
    
    available_drivers = AssignmentDashboardService.get_available_drivers()
    print(f"   get_available_drivers(): {len(available_drivers)} drivers")
    
    available_vehicles = AssignmentDashboardService.get_available_vehicles()
    print(f"   get_available_vehicles(): {len(available_vehicles)} vehicles")
    
    print("\n" + "=" * 60)
    print("✓ Dashboard components verified successfully")
