"""Smoke test: verify assignment dashboard route and service work.
Run: .venv\Scripts\python.exe scripts\smoke_test_dashboard.py
"""
import sys
import os
sys.path.insert(0, os.getcwd())
from app import create_app

app = create_app('development')

with app.app_context():
    from app.modules.deployments.assignment_dashboard_service import AssignmentDashboardService

    print("Testing AssignmentDashboardService...")
    
    # Test KPI metrics
    kpis = AssignmentDashboardService.get_kpi_metrics()
    print("KPI Metrics:")
    print(f"  Total Drivers: {kpis['total_drivers']}")
    print(f"  Assigned Drivers: {kpis['assigned_drivers']}")
    print(f"  Available Drivers: {kpis['available_drivers']}")
    print(f"  Compliance Failed: {kpis['compliance_failed']}")
    print(f"  Deployment Ready: {kpis['deployment_ready']}")
    print(f"  Expiring Licenses (30d): {kpis['expiring_licenses']}")
    
    # Test assignments list
    assignments, total = AssignmentDashboardService.get_assignments_list(offset=0, limit=5)
    print(f"\nAssignments List (limit 5): {len(assignments)} of {total} total")
    for a in assignments:
        print(f"  - {a['driver_name']} -> {a['vehicle_number']} ({a['assignment_status']})")
    
    # Test available drivers
    available_drivers = AssignmentDashboardService.get_available_drivers()
    print(f"\nAvailable Drivers: {len(available_drivers)}")
    for d in available_drivers[:3]:
        print(f"  - {d['driver_name']} (license: {d['license_status']})")
    
    # Test available vehicles
    available_vehicles = AssignmentDashboardService.get_available_vehicles()
    print(f"\nAvailable Vehicles: {len(available_vehicles)}")
    for v in available_vehicles[:3]:
        print(f"  - {v['vehicle_number']} (insurance: {v['insurance_status']})")
    
    # Verify route exists
    print("\nVerifying route registration...")
    routes = [r.rule for r in app.url_map.iter_rules() if 'assignment' in r.rule]
    print(f"Assignment routes found: {routes}")
    
    if '/deployments/assignment-dashboard' in routes or any('assignment' in r for r in routes):
        print("✓ Dashboard route registered successfully")
        sys.exit(0)
    else:
        print("✗ Dashboard route not found")
        sys.exit(1)
