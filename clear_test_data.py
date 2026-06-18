#!/usr/bin/env python
"""Clear test driver assignment data"""

from app import create_app
from app.extensions import db
from app.modules.drivers.models import DriverVehicleAssignment

app = create_app()
with app.app_context():
    # Get count before deletion
    count_before = DriverVehicleAssignment.query.count()
    print(f"Total assignments before deletion: {count_before}")
    
    # Delete all assignments
    DriverVehicleAssignment.query.delete()
    db.session.commit()
    
    # Verify deletion
    count_after = DriverVehicleAssignment.query.count()
    print(f"Total assignments after deletion: {count_after}")
    print("✓ All test data cleared successfully!")
