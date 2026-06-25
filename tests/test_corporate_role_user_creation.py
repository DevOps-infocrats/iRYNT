import unittest
from app import create_app
from app.extensions import db
from app.modules.auth.models import Role, User
from app.modules.users.forms import UserForm
from app.modules.users.services.validation_service import ValidationService

class TestCorporateRoleUserCreation(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        
        # Ensure database tables exist
        db.create_all()
        
        # Setup test roles
        self.super_admin_role = Role.query.filter_by(name='Super Admin').first()
        if not self.super_admin_role:
            self.super_admin_role = Role(name='Super Admin')
            db.session.add(self.super_admin_role)
            
        self.pmo_role = Role.query.filter_by(name='PMO').first()
        if not self.pmo_role:
            self.pmo_role = Role(name='PMO')
            db.session.add(self.pmo_role)

        self.circle_admin_role = Role.query.filter_by(name='Circle Admin').first()
        if not self.circle_admin_role:
            self.circle_admin_role = Role(name='Circle Admin')
            db.session.add(self.circle_admin_role)

        self.driver_role = Role.query.filter_by(name='Driver').first()
        if not self.driver_role:
            self.driver_role = Role(name='Driver')
            db.session.add(self.driver_role)
            
        db.session.commit()

    def tearDown(self):
        db.session.rollback()
        self.app_context.pop()

    def test_form_validation_for_corporate_role(self):
        # 1. Super Admin role - should not require company or circle
        with self.app.test_request_context():
            form = UserForm()
            form.role_id.data = self.super_admin_role.id
            form.username.data = "test_super_admin"
            form.email.data = "super@example.com"
            form.company_id.data = ""
            form.circle_id.data = ""
            
            # Populate choices for validation
            form.role_id.choices = [(self.super_admin_role.id, 'Super Admin')]
            form.company_id.choices = [('', 'Select company')]
            form.circle_id.choices = [('', 'Select circle')]
            
            is_valid = form.validate()
            self.assertTrue(is_valid, f"Super Admin form validation failed: {form.errors}")

        # 2. PMO role - corporate, should not require company or circle
        with self.app.test_request_context():
            form = UserForm()
            form.role_id.data = self.pmo_role.id
            form.username.data = "test_pmo"
            form.email.data = "pmo@example.com"
            form.company_id.data = ""
            form.circle_id.data = ""
            
            # Populate choices
            form.role_id.choices = [(self.pmo_role.id, 'PMO')]
            form.company_id.choices = [('', 'Select company')]
            form.circle_id.choices = [('', 'Select circle')]
            
            is_valid = form.validate()
            self.assertTrue(is_valid, f"PMO form validation failed: {form.errors}")

    def test_form_validation_for_non_corporate_role(self):
        # 1. Driver role - non-corporate, should require company but not circle
        with self.app.test_request_context():
            form = UserForm()
            form.role_id.data = self.driver_role.id
            form.username.data = "test_driver"
            form.email.data = "driver@example.com"
            form.company_id.data = "" # Empty
            form.circle_id.data = ""
            
            form.role_id.choices = [(self.driver_role.id, 'Driver')]
            form.company_id.choices = [('', 'Select company')]
            form.circle_id.choices = [('', 'Select circle')]
            
            is_valid = form.validate()
            self.assertFalse(is_valid)
            self.assertIn('company_id', form.errors)
            self.assertNotIn('circle_id', form.errors)

        # 2. Circle Admin role - non-corporate, should require company AND circle
        with self.app.test_request_context():
            form = UserForm()
            form.role_id.data = self.circle_admin_role.id
            form.username.data = "test_circle_admin"
            form.email.data = "circle_admin@example.com"
            form.company_id.data = "" # Empty
            form.circle_id.data = ""  # Empty
            
            form.role_id.choices = [(self.circle_admin_role.id, 'Circle Admin')]
            form.company_id.choices = [('', 'Select company')]
            form.circle_id.choices = [('', 'Select circle')]
            
            is_valid = form.validate()
            self.assertFalse(is_valid)
            self.assertIn('company_id', form.errors)
            self.assertIn('circle_id', form.errors)

    def test_excel_validation_for_corporate_role(self):
        rows = [
            {
                "row_number": 2,
                "Username": "excel_pmo",
                "Email": "excel_pmo@example.com",
                "Phone": "9999900101",
                "Role": "PMO",
                "Company": "", # Missing
                "Circle": "",  # Missing
            },
            {
                "row_number": 3,
                "Username": "excel_driver",
                "Email": "excel_driver@example.com",
                "Phone": "9999900102",
                "Role": "Driver",
                "Company": "", # Missing
                "Circle": "",  # Missing
            }
        ]
        
        validator = ValidationService()
        summary, errors = validator.validate(rows)
        
        # Row 2 (PMO) should have no Company/Circle errors
        pmo_errors = [e for e in errors if e["row_number"] == 2]
        pmo_cols = [e["column"] for e in pmo_errors]
        self.assertNotIn("Company", pmo_cols)
        self.assertNotIn("Circle", pmo_cols)
        
        # Row 3 (Driver) should have Company error
        driver_errors = [e for e in errors if e["row_number"] == 3]
        driver_cols = [e["column"] for e in driver_errors]
        self.assertIn("Company", driver_cols)
        self.assertNotIn("Circle", driver_cols)

if __name__ == '__main__':
    unittest.main()
