import unittest
from app import create_app
from app.extensions import db
from app.modules.auth.models import User, Role
from app.modules.companies.models import Company
from app.modules.circles.models import Circle
from app.modules.projects.models import Project
from app.modules.clients.models import Client
from app.modules.users.services.validation_service import ValidationService
from app.modules.users.services.bulk_import_service import BulkImportService
from app.modules.drivers.models import DriverProfile

class TestBulkImportFlows(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        
        self.db = db
        
        # Ensure we have active test master data
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
            
        self.driver_role = Role.query.filter_by(name='Driver').first()
        if not self.driver_role:
            self.driver_role = Role(name='Driver')
            db.session.add(self.driver_role)
            
        self.helper_role = Role.query.filter_by(name='Helper').first()
        if not self.helper_role:
            self.helper_role = Role(name='Helper')
            db.session.add(self.helper_role)
            
        db.session.commit()
        
        # Clean up any test users from previous test runs to avoid duplicate conflicts
        User.query.filter(User.username.like('import_%')).delete(synchronize_session=False)
        db.session.commit()

    def tearDown(self):
        db.session.rollback()
        # Clean up test users
        User.query.filter(User.username.like('import_%')).delete(synchronize_session=False)
        db.session.commit()
        self.app_context.pop()

    def test_valid_import(self):
        rows = [
            {
                "row_number": 2,
                "Username": "import_driver1",
                "Email": "import_driver1@example.com",
                "Phone": "9999900001",
                "Role": "Driver",
                "Company": "Test Company",
                "Circle": "Delhi NCR",
                "Project": "OFC Project",
                "Is Active": "Yes",
                "Is Verified": "Yes",
                "Password": "SecurePassword123!"
            },
            {
                "row_number": 3,
                "Username": "import_helper1",
                "Email": "import_helper1@example.com",
                "Phone": "9999900002",
                "Role": "Helper",
                "Company": "Test Company",
                "Circle": "Delhi NCR",
                "Project": "OFC Project",
                "Is Active": "Yes",
                "Is Verified": "Yes",
                "Password": ""
            }
        ]
        
        validator = ValidationService()
        summary, errors = validator.validate(rows)
        
        self.assertEqual(len(errors), 0, f"Validation failed: {errors}")
        self.assertEqual(summary["valid"], 2)
        
        # Check resolved IDs
        self.assertEqual(rows[0]["role_id"], self.driver_role.id)
        self.assertEqual(rows[0]["company_id"], self.company.id)
        self.assertEqual(rows[0]["circle_id"], self.circle.id)
        self.assertEqual(rows[0]["project_id"], self.project.id)
        
        # Execute Import
        importer = BulkImportService()
        result = importer.import_rows(rows, importer_id="test_admin")
        
        self.assertEqual(result["created"], 2)
        self.assertEqual(result["failed"], 0)
        
        # Verify Users exist in db
        user_drv = User.query.filter_by(username="import_driver1").first()
        self.assertIsNotNone(user_drv)
        self.assertEqual(user_drv.primary_role.name, "Driver")
        
        user_hlp = User.query.filter_by(username="import_helper1").first()
        self.assertIsNotNone(user_hlp)
        self.assertEqual(user_hlp.primary_role.name, "Helper")
        
        # Verify DriverProfile creation
        drv_profile = DriverProfile.query.filter_by(user_id=user_drv.id).first()
        self.assertIsNotNone(drv_profile)
        self.assertEqual(drv_profile.project_id, self.project.id)
        self.assertEqual(drv_profile.client_id, self.client.id)
        
        hlp_profile = DriverProfile.query.filter_by(user_id=user_hlp.id).first()
        self.assertIsNotNone(hlp_profile)
        self.assertEqual(hlp_profile.project_id, self.project.id)

    def test_invalid_role(self):
        rows = [
            {
                "row_number": 2,
                "Username": "import_invalid_role",
                "Email": "import_invalid_role@example.com",
                "Phone": "9999900003",
                "Role": "Driverx",  # Invalid
                "Company": "Test Company",
                "Circle": "Delhi NCR",
                "Project": "OFC Project",
                "Is Active": "Yes",
                "Is Verified": "Yes",
                "Password": ""
            }
        ]
        
        validator = ValidationService()
        summary, errors = validator.validate(rows)
        
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0]["column"], "Role")
        self.assertEqual(errors[0]["value"], "Driverx")
        self.assertIn("Driver", errors[0]["suggested_fix"])

    def test_invalid_company(self):
        rows = [
            {
                "row_number": 2,
                "Username": "import_invalid_company",
                "Email": "import_invalid_company@example.com",
                "Phone": "9999900004",
                "Role": "Driver",
                "Company": "Test Company Mismatch",  # Invalid
                "Circle": "Delhi NCR",
                "Project": "OFC Project",
                "Is Active": "Yes",
                "Is Verified": "Yes",
                "Password": ""
            }
        ]
        
        validator = ValidationService()
        summary, errors = validator.validate(rows)
        
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0]["column"], "Company")
        self.assertIn("Test Company", errors[0]["suggested_fix"])

    def test_invalid_circle(self):
        rows = [
            {
                "row_number": 2,
                "Username": "import_invalid_circle",
                "Email": "import_invalid_circle@example.com",
                "Phone": "9999900005",
                "Role": "Driver",
                "Company": "Test Company",
                "Circle": "Delhi NCR Mismatch",  # Invalid
                "Project": "OFC Project",
                "Is Active": "Yes",
                "Is Verified": "Yes",
                "Password": ""
            }
        ]
        
        validator = ValidationService()
        summary, errors = validator.validate(rows)
        
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0]["column"], "Circle")

    def test_missing_project(self):
        rows = [
            {
                "row_number": 2,
                "Username": "import_no_project",
                "Email": "import_no_project@example.com",
                "Phone": "9999900006",
                "Role": "Driver",
                "Company": "Test Company",
                "Circle": "Delhi NCR",
                "Project": "",  # Missing/Optional Project
                "Is Active": "Yes",
                "Is Verified": "Yes",
                "Password": ""
            }
        ]
        
        validator = ValidationService()
        summary, errors = validator.validate(rows)
        
        self.assertEqual(len(errors), 0)
        self.assertEqual(summary["valid"], 1)

    def test_duplicate_checks(self):
        # Setup existing user
        existing_user = User(
            username="import_duplicate_user",
            email="import_dup@example.com",
            phone="9999900007"
        )
        existing_user.set_password("Admin@123")
        db.session.add(existing_user)
        db.session.commit()
        
        rows = [
            {
                "row_number": 2,
                "Username": "import_duplicate_user",  # System Duplicate
                "Email": "new_email@example.com",
                "Phone": "9999900008",
                "Role": "Driver",
                "Company": "Test Company",
                "Circle": "Delhi NCR",
                "Project": "",
                "Is Active": "Yes",
                "Is Verified": "Yes",
                "Password": ""
            },
            {
                "row_number": 3,
                "Username": "import_sheet_dup",
                "Email": "sheet_dup@example.com",  # Sheet Duplicate 1
                "Phone": "9999900009",
                "Role": "Driver",
                "Company": "Test Company",
                "Circle": "Delhi NCR",
                "Project": "",
                "Is Active": "Yes",
                "Is Verified": "Yes",
                "Password": ""
            },
            {
                "row_number": 4,
                "Username": "import_sheet_dup_different",
                "Email": "sheet_dup@example.com",  # Sheet Duplicate 2
                "Phone": "9999900009",
                "Role": "Driver",
                "Company": "Test Company",
                "Circle": "Delhi NCR",
                "Project": "",
                "Is Active": "Yes",
                "Is Verified": "Yes",
                "Password": ""
            }
        ]
        
        validator = ValidationService()
        summary, errors = validator.validate(rows)
        
        self.assertEqual(summary["failed"], 2)
        self.assertEqual(summary["valid"], 1)
        
        row2_errors = [e for e in errors if e["row_number"] == 2]
        self.assertEqual(row2_errors[0]["column"], "Username")
        
        row4_errors = [e for e in errors if e["row_number"] == 4]
        cols_flagged = {e["column"] for e in row4_errors}
        self.assertIn("Email", cols_flagged)

    def test_mixed_success_batch(self):
        rows = [
            {
                "row_number": 2,
                "Username": "import_mixed_success",
                "Email": "mixed_success@example.com",
                "Phone": "9999900010",
                "Role": "Driver",
                "Company": "Test Company",
                "Circle": "Delhi NCR",
                "Project": "OFC Project",
                "Is Active": "Yes",
                "Is Verified": "Yes",
                "Password": ""
            },
            {
                "row_number": 3,
                "Username": "import_mixed_failure",
                "Email": "mixed_failure@example.com",
                "Phone": "9999900011",
                "Role": "InvalidRoleName",  # Failed
                "Company": "Test Company",
                "Circle": "Delhi NCR",
                "Project": "OFC Project",
                "Is Active": "Yes",
                "Is Verified": "Yes",
                "Password": ""
            }
        ]
        
        validator = ValidationService()
        summary, errors = validator.validate(rows)
        
        self.assertEqual(summary["valid"], 1)
        self.assertEqual(summary["failed"], 1)
        
        error_row_indices = {e["row_number"] - 2 for e in errors}
        valid_rows = [row for idx, row in enumerate(rows) if idx not in error_row_indices]
        
        self.assertEqual(len(valid_rows), 1)
        self.assertEqual(valid_rows[0]["Username"], "import_mixed_success")
        
        importer = BulkImportService()
        result = importer.import_rows(valid_rows, importer_id="test_admin")
        
        self.assertEqual(result["created"], 1)
        self.assertEqual(result["failed"], 0)
        
        # Verify valid user exists, invalid does not
        self.assertIsNotNone(User.query.filter_by(username="import_mixed_success").first())
        self.assertIsNone(User.query.filter_by(username="import_mixed_failure").first())

if __name__ == '__main__':
    unittest.main()
