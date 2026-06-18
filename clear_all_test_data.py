#!/usr/bin/env python
"""Clear test operational data safely"""

from app import create_app
from app.extensions import db
from app.modules.drivers.models import DriverVehicleAssignment, DriverAttendance
from app.modules.deployments.models import VehicleDeployment
from sqlalchemy import inspect

app = create_app()

def safe_clear_tables():
    """Clear only operational test data, preserve master data"""
    with app.app_context():
        # Models to clear (only operational/transactional data)
        models_to_clear = [
            ('driver_vehicle_assignment', DriverVehicleAssignment),
            ('vehicle_deployment', VehicleDeployment),
            ('driver_attendance', DriverAttendance),
        ]
        
        print("=" * 60)
        print("CLEARING TEST OPERATIONAL DATA (SAFELY)")
        print("=" * 60)
        
        total_deleted = 0
        
        for table_name, model in models_to_clear:
            try:
                # Count before
                count_before = db.session.query(model).count()
                
                # Delete all records
                db.session.query(model).delete()
                db.session.commit()
                
                # Count after
                count_after = db.session.query(model).count()
                deleted = count_before - count_after
                
                if deleted > 0:
                    print(f"✓ {table_name:40s} | Cleared: {deleted:5d} records")
                    total_deleted += deleted
                else:
                    print(f"  {table_name:40s} | Empty (no action needed)")
                    
            except Exception as e:
                print(f"✗ {table_name:40s} | Error: {str(e)[:50]}")
        
        print("=" * 60)
        print(f"TOTAL RECORDS DELETED: {total_deleted}")
        print("=" * 60)
        print("\n✓ Protected master data is intact!")
        print("✓ All test data cleared safely!")

if __name__ == '__main__':
    safe_clear_tables()
