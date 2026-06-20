import unittest
from app import create_app
from app.extensions import db
from app.modules.companies.models import Company
from app.modules.circles.models import Circle
from app.modules.clients.models import Client
from app.modules.projects.models import Project
from app.modules.subzones.models import Subzone
from app.modules.vehicles.models import Vehicle
from app.modules.auth.models import User, AuditLog
from app.modules.vehicles.services.validation_service import VehicleValidationService
from app.modules.vehicles.services.bulk_import_service import VehicleBulkImportService

class TestVehicleBulkImport(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        
        self.db = db

        # 1. Ensure master testing scope
        self.company = Company.query.filter_by(company_name='Test Company').first()
        if not self.company:
            self.company = Company(
                company_name='Test Company', 
                company_code='TC001', 
                pincode='123456', 
                status='Active'
            )
            db.session.add(self.company)
            
        self.circle = Circle.query.filter_by(circle_name='Delhi NCR').first()
        if not self.circle:
            self.circle = Circle(
                circle_name='Delhi NCR',
                circle_code='DEL01',
                company_id=self.company.id,
                status='Active'
            )
            db.session.add(self.circle)
            
        self.client = Client.query.filter_by(client_name='Test Client').first()
        if not self.client:
            self.client = Client(
                client_name='Test Client',
                client_code='CLI001',
                company_id=self.company.id,
                circle_id=self.circle.id,
                status='Active'
            )
            db.session.add(self.client)
            
        self.project = Project.query.filter_by(project_name='OFC Project').first()
        if not self.project:
            self.project = Project(
                project_name='OFC Project',
                project_code='PRJ001',
                company_id=self.company.id,
                circle_id=self.circle.id,
                client_id=self.client.id,
                project_type='OFC',
                start_date=db.func.current_date(),
                status='Active'
            )
            db.session.add(self.project)

        self.subzone = Subzone.query.filter_by(subzone_name='Noida Subzone').first()
        if not self.subzone:
            self.subzone = Subzone(
                subzone_name='Noida Subzone',
                subzone_code='NOI001',
                company_id=self.company.id,
                circle_id=self.circle.id,
                client_id=self.client.id,
                project_id=self.project.id,
                status='Active'
            )
            db.session.add(self.subzone)

        # Pre-seed a test user to act as importer
        self.test_user = User.query.filter_by(username='test_admin').first()
        if not self.test_user:
            self.test_user = User(
                username='test_admin',
                email='test_admin@example.com',
                phone='1112223334',
                is_active=True,
                is_verified=True
            )
            self.test_user.set_password('Admin@123')
            db.session.add(self.test_user)
            
        db.session.commit()

        # Clean existing test vehicles from previous runs
        Vehicle.query.filter(Vehicle.vehicle_number.like('UP99%')).delete(synchronize_session=False)
        db.session.commit()

    def tearDown(self):
        db.session.rollback()
        Vehicle.query.filter(Vehicle.vehicle_number.like('UP99%')).delete(synchronize_session=False)
        db.session.commit()
        self.app_context.pop()

    def test_valid_import(self):
        rows = [
            {
                "row_number": 2,
                "Vehicle Number": "UP99AB1234",
                "Vehicle Type": "Mini Truck",
                "Vehicle Category": "Vendor",
                "Vehicle Brand": "Tata",
                "Vehicle Model": "Ace",
                "Company": "Test Company",
                "Circle": "Delhi NCR",
                "Client": "Test Client",
                "Project": "OFC Project",
                "Subzone": "Noida Subzone",
                "Manufacturing Year": "2024",
                "Chassis Number": "CHAS990001",
                "Engine Number": "ENG990001",
                "GPS Enabled": "Yes",
                "Realtime Tracking Enabled": "Yes",
                "Deployment Allowed": "Yes"
            }
        ]

        validator = VehicleValidationService()
        summary, errors = validator.validate(rows)

        self.assertEqual(len(errors), 0, f"Validation errors found: {errors}")
        self.assertEqual(summary["valid"], 1)

        # Execute Import
        importer = VehicleBulkImportService()
        result = importer.import_rows(rows, self.test_user.id)

        self.assertEqual(result["created"], 1)
        self.assertEqual(result["failed"], 0)

        # Check vehicle exists in database
        vehicle = Vehicle.query.filter_by(vehicle_number="UP99AB1234").first()
        self.assertIsNotNone(vehicle)
        self.assertEqual(vehicle.vehicle_type, "Mini Truck")
        self.assertEqual(vehicle.chassis_number, "chas990001") # normalized to lower
        self.assertEqual(vehicle.subzone_id, self.subzone.id)

        # Check audit log entry
        audit = AuditLog.query.filter_by(user_id=self.test_user.id, action="BULK_VEHICLE_IMPORT").first()
        self.assertIsNotNone(audit)
        self.assertEqual(audit.details["succeeded"], 1)

    def test_invalid_type_category(self):
        rows = [
            {
                "row_number": 2,
                "Vehicle Number": "UP99AB1235",
                "Vehicle Type": "Aeroplane",  # Invalid type
                "Vehicle Category": "Vendor",
                "Vehicle Brand": "Tata",
                "Vehicle Model": "Ace",
                "Company": "Test Company",
                "Circle": "Delhi NCR",
                "Client": "Test Client",
                "Project": "OFC Project",
                "Subzone": "Noida Subzone",
                "Manufacturing Year": "2024",
                "Chassis Number": "CHAS990002",
                "Engine Number": "ENG990002"
            }
        ]

        validator = VehicleValidationService()
        summary, errors = validator.validate(rows)

        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0]["column"], "Vehicle Type")
        self.assertIn("Mini Truck", errors[0]["suggested_fix"])

    def test_hierarchical_mismatches(self):
        # Create another company
        other_company = Company(
            company_name='Other Company', 
            company_code='OC001', 
            pincode='654321', 
            status='Active'
        )
        db.session.add(other_company)
        db.session.commit()

        rows = [
            {
                "row_number": 2,
                "Vehicle Number": "UP99AB1236",
                "Vehicle Type": "Mini Truck",
                "Vehicle Category": "Vendor",
                "Vehicle Brand": "Tata",
                "Vehicle Model": "Ace",
                "Company": "Other Company", # Mismatch: Circle Delhi NCR belongs to Test Company
                "Circle": "Delhi NCR",
                "Client": "Test Client",
                "Project": "OFC Project",
                "Subzone": "Noida Subzone",
                "Manufacturing Year": "2024",
                "Chassis Number": "CHAS990003",
                "Engine Number": "ENG990003"
            }
        ]

        validator = VehicleValidationService()
        summary, errors = validator.validate(rows)

        self.assertTrue(len(errors) >= 1)
        # Delhi NCR circle does not belong to Other Company, so circle validation should fail
        circle_errors = [e for e in errors if e["column"] == "Circle"]
        self.assertEqual(len(circle_errors), 1)
        self.assertIn("Delhi NCR", circle_errors[0]["value"])

        # Clean up
        db.session.delete(other_company)
        db.session.commit()

    def test_duplications(self):
        # Pre-seed a vehicle with a chassis number
        existing_v = Vehicle(
            company_id=self.company.id,
            circle_id=self.circle.id,
            client_id=self.client.id,
            project_id=self.project.id,
            subzone_id=self.subzone.id,
            vehicle_number="UP99AB9999",
            vehicle_type="Mini Truck",
            vehicle_category="Vendor",
            vehicle_brand="Tata",
            vehicle_model="Ace",
            chassis_number="chas990005", # existing
            engine_number="eng990005"
        )
        db.session.add(existing_v)
        db.session.commit()

        rows = [
            {
                "row_number": 2,
                "Vehicle Number": "UP99AB9999",  # System Duplicate vehicle number in same subzone
                "Vehicle Type": "Mini Truck",
                "Vehicle Category": "Vendor",
                "Vehicle Brand": "Tata",
                "Vehicle Model": "Ace",
                "Company": "Test Company",
                "Circle": "Delhi NCR",
                "Client": "Test Client",
                "Project": "OFC Project",
                "Subzone": "Noida Subzone",
                "Manufacturing Year": "2024",
                "Chassis Number": "CHAS990005",  # System Duplicate chassis
                "Engine Number": "ENG990006"
            },
            {
                "row_number": 3,
                "Vehicle Number": "UP99AB7777",
                "Vehicle Type": "Mini Truck",
                "Vehicle Category": "Vendor",
                "Vehicle Brand": "Tata",
                "Vehicle Model": "Ace",
                "Company": "Test Company",
                "Circle": "Delhi NCR",
                "Client": "Test Client",
                "Project": "OFC Project",
                "Subzone": "Noida Subzone",
                "Manufacturing Year": "2024",
                "Chassis Number": "CHAS990007",
                "Engine Number": "ENG990007"  # Sheet Duplicate Engine Number (row 3 vs 4)
            },
            {
                "row_number": 4,
                "Vehicle Number": "UP99AB8888",
                "Vehicle Type": "Mini Truck",
                "Vehicle Category": "Vendor",
                "Vehicle Brand": "Tata",
                "Vehicle Model": "Ace",
                "Company": "Test Company",
                "Circle": "Delhi NCR",
                "Client": "Test Client",
                "Project": "OFC Project",
                "Subzone": "Noida Subzone",
                "Manufacturing Year": "2024",
                "Chassis Number": "CHAS990008",
                "Engine Number": "ENG990007"  # Sheet Duplicate Engine Number (row 4 vs 3)
            }
        ]

        validator = VehicleValidationService()
        summary, errors = validator.validate(rows)

        self.assertEqual(summary["failed"], 2)
        self.assertEqual(summary["valid"], 1)

        # Row 2 should flag duplicates on vehicle number and chassis number
        row2_errors = [e for e in errors if e["row_number"] == 2]
        cols_row2 = {e["column"] for e in row2_errors}
        self.assertIn("Vehicle Number", cols_row2)
        self.assertIn("Chassis Number", cols_row2)

        # Row 4 should flag duplicate engine number
        row4_errors = [e for e in errors if e["row_number"] == 4]
        cols_row4 = {e["column"] for e in row4_errors}
        self.assertIn("Engine Number", cols_row4)

        # Clean up
        db.session.delete(existing_v)
        db.session.commit()

    def test_mixed_success(self):
        rows = [
            {
                "row_number": 2,
                "Vehicle Number": "UP99AB1111",  # Valid
                "Vehicle Type": "Mini Truck",
                "Vehicle Category": "Vendor",
                "Vehicle Brand": "Tata",
                "Vehicle Model": "Ace",
                "Company": "Test Company",
                "Circle": "Delhi NCR",
                "Client": "Test Client",
                "Project": "OFC Project",
                "Subzone": "Noida Subzone",
                "Manufacturing Year": "2024",
                "Chassis Number": "CHAS991111",
                "Engine Number": "ENG991111"
            },
            {
                "row_number": 3,
                "Vehicle Number": "UP99AB2222",  # Invalid (Role Mismatch or other error)
                "Vehicle Type": "Aeroplane",
                "Vehicle Category": "Vendor",
                "Vehicle Brand": "Tata",
                "Vehicle Model": "Ace",
                "Company": "Test Company",
                "Circle": "Delhi NCR",
                "Client": "Test Client",
                "Project": "OFC Project",
                "Subzone": "Noida Subzone",
                "Manufacturing Year": "2024",
                "Chassis Number": "CHAS992222",
                "Engine Number": "ENG992222"
            }
        ]

        validator = VehicleValidationService()
        summary, errors = validator.validate(rows)

        self.assertEqual(summary["valid"], 1)
        self.assertEqual(summary["failed"], 1)

        error_row_indices = {e["row_number"] - 2 for e in errors}
        valid_rows = [row for idx, row in enumerate(rows) if idx not in error_row_indices]

        self.assertEqual(len(valid_rows), 1)
        self.assertEqual(valid_rows[0]["Vehicle Number"], "UP99AB1111")

        importer = VehicleBulkImportService()
        result = importer.import_rows(valid_rows, self.test_user.id)

        self.assertEqual(result["created"], 1)
        self.assertEqual(result["failed"], 0)

        # Verify only UP99AB1111 exists in DB
        self.assertIsNotNone(Vehicle.query.filter_by(vehicle_number="UP99AB1111").first())
        self.assertIsNone(Vehicle.query.filter_by(vehicle_number="UP99AB2222").first())

if __name__ == '__main__':
    unittest.main()
