import re
from app.modules.auth.models import User, Role
from app.modules.companies.models import Company
from app.modules.circles.models import Circle
from app.modules.projects.models import Project

class ValidationService:
    """Service to validate user rows parsed from Excel."""

    def __init__(self):
        self.email_regex = re.compile(r"^[\w\.-]+@[\w\.-]+\.\w+$")

    def validate(self, rows: list) -> tuple:
        """Validate a list of row dicts.
        Returns a tuple of (summary, errors).
        
        `summary` is a dict with total, valid, and failed counts.
        `errors` is a list of dicts: {row_number, column, value, message, suggested_fix}
        """
        errors = []
        
        # 1. Pre-fetch active lookup master records to avoid N+1 queries
        roles = Role.query.all()
        companies = Company.query.filter_by(status='Active').all()
        circles = Circle.query.filter_by(status='Active').all()
        projects = Project.query.filter_by(status='Active').all()

        # Build optimized dictionaries
        roles_by_name = {r.name.strip().lower(): r for r in roles}
        companies_by_name = {c.company_name.strip().lower(): c for c in companies}
        
        # Circles keyed by name and company_id, and globally
        circles_by_name_and_company = {}
        circles_by_name = {}
        for circ in circles:
            circles_by_name_and_company[(circ.circle_name.strip().lower(), circ.company_id)] = circ
            circles_by_name[circ.circle_name.strip().lower()] = circ

        # Projects keyed by name, circle_id, company_id, and globally
        projects_by_name_circle_company = {}
        projects_by_name = {}
        for proj in projects:
            projects_by_name_circle_company[(proj.project_name.strip().lower(), proj.circle_id, proj.company_id)] = proj
            projects_by_name[proj.project_name.strip().lower()] = proj

        # Lists for error messages
        available_role_names = [r.name for r in roles]
        available_company_names = [c.company_name for c in companies]
        available_circle_names = [c.circle_name for c in circles]
        available_project_names = [p.project_name for p in projects]

        # Check against existing users in database
        existing_usernames = {u.username.lower() for u in User.query.with_entities(User.username).all()}
        existing_emails = {u.email.lower() for u in User.query.with_entities(User.email).all()}
        existing_phones = {u.phone for u in User.query.with_entities(User.phone).all() if u.phone}

        # Sheet-level trackers for duplicate checks
        sheet_usernames = {}
        sheet_emails = {}
        sheet_phones = {}

        # Set of row numbers that have errors
        error_rows = set()

        for row in rows:
            row_num = row.get("row_number")
            
            # Helper to append cell-level errors
            def add_error(column_name, cell_val, msg, fix):
                error_rows.add(row_num)
                errors.append({
                    "row_number": row_num,
                    "column": column_name,
                    "value": cell_val,
                    "message": msg,
                    "suggested_fix": fix
                })

            # 1. Username validation
            username_val = row.get("Username")
            username = str(username_val or "").strip()
            if not username:
                add_error("Username", username_val, "Username is required.", "Enter a non-empty username.")
            else:
                if username.lower() in existing_usernames:
                    add_error("Username", username, f"Username '{username}' already exists in system.", "Choose a unique username.")
                if username.lower() in sheet_usernames:
                    add_error("Username", username, f"Duplicate Username '{username}' in this sheet.", f"Coordinate with row {sheet_usernames[username.lower()]}.")
                else:
                    sheet_usernames[username.lower()] = row_num

            # 2. Email validation
            email_val = row.get("Email")
            email = str(email_val or "").strip()
            if not email:
                add_error("Email", email_val, "Email is required.", "Enter a valid email address.")
            elif not self.email_regex.match(email):
                add_error("Email", email, f"Email '{email}' is not valid format.", "Use format: name@example.com")
            else:
                if email.lower() in existing_emails:
                    add_error("Email", email, f"Email '{email}' already exists in system.", "Choose a unique email address.")
                if email.lower() in sheet_emails:
                    add_error("Email", email, f"Duplicate Email '{email}' in this sheet.", f"Coordinate with row {sheet_emails[email.lower()]}.")
                else:
                    sheet_emails[email.lower()] = row_num

            # 3. Phone validation
            phone_val = row.get("Phone")
            if phone_val is not None:
                phone_str = str(phone_val).strip().split('.')[0]
                if phone_str:
                    if phone_str in existing_phones:
                        add_error("Phone", phone_val, f"Phone number '{phone_str}' already exists in system.", "Enter a unique phone number or leave blank.")
                    if phone_str in sheet_phones:
                        add_error("Phone", phone_val, f"Duplicate Phone number '{phone_str}' in this sheet.", f"Coordinate with row {sheet_phones[phone_str]}.")
                    else:
                        sheet_phones[phone_str] = row_num

            # 4. Role validation
            role_val = row.get("Role")
            role_str = str(role_val or "").strip()
            resolved_role = None
            if not role_str:
                add_error("Role", role_val, "Role is required.", f"Available roles: {', '.join(available_role_names[:8])}")
            else:
                resolved_role = roles_by_name.get(role_str.lower())
                if not resolved_role:
                    add_error(
                        "Role", 
                        role_val, 
                        f"Role '{role_val}' not found.", 
                        f"Available roles: {', '.join(available_role_names)}"
                    )
                else:
                    row["role_id"] = resolved_role.id

            # 5. Company validation
            company_val = row.get("Company")
            company_str = str(company_val or "").strip()
            resolved_company = None
            if not company_str:
                add_error("Company", company_val, "Company is required.", f"Available companies: {', '.join(available_company_names[:5])}")
            else:
                resolved_company = companies_by_name.get(company_str.lower())
                if not resolved_company:
                    add_error(
                        "Company", 
                        company_val, 
                        f"Company '{company_val}' not found.", 
                        f"Available companies: {', '.join(available_company_names)}"
                    )
                else:
                    row["company_id"] = resolved_company.id

            # 6. Circle validation
            circle_val = row.get("Circle")
            circle_str = str(circle_val or "").strip()
            resolved_circle = None
            if not circle_str:
                add_error("Circle", circle_val, "Circle is required.", f"Available circles: {', '.join(available_circle_names[:5])}")
            else:
                # If company is resolved, check if circle is under that company
                if resolved_company:
                    resolved_circle = circles_by_name_and_company.get((circle_str.lower(), resolved_company.id))
                    if not resolved_circle:
                        # Circle name exists but not under this company?
                        global_circle = circles_by_name.get(circle_str.lower())
                        if global_circle:
                            # Find the company name of that circle
                            gc_company = Company.query.get(global_circle.company_id)
                            comp_name = gc_company.company_name if gc_company else "another company"
                            add_error(
                                "Circle",
                                circle_val,
                                f"Circle '{circle_val}' is associated with Company '{comp_name}', not '{company_str}'.",
                                f"Enter a circle belonging to '{company_str}'."
                            )
                        else:
                            company_circles = [c.circle_name for c in circles if c.company_id == resolved_company.id]
                            add_error(
                                "Circle",
                                circle_val,
                                f"Circle '{circle_val}' not found under company '{company_str}'.",
                                f"Available circles for this company: {', '.join(company_circles) if company_circles else 'None'}"
                            )
                    else:
                        row["circle_id"] = resolved_circle.id
                else:
                    # Company not resolved, try global lookup
                    resolved_circle = circles_by_name.get(circle_str.lower())
                    if not resolved_circle:
                        add_error(
                            "Circle",
                            circle_val,
                            f"Circle '{circle_val}' not found.",
                            f"Available circles: {', '.join(available_circle_names[:10])}"
                        )
                    else:
                        row["circle_id"] = resolved_circle.id

            # 7. Project validation (Optional)
            project_val = row.get("Project")
            project_str = str(project_val or "").strip()
            resolved_project = None
            if project_str:
                # If company and circle are resolved, check if project is under that scope
                if resolved_company and resolved_circle:
                    resolved_project = projects_by_name_circle_company.get((project_str.lower(), resolved_circle.id, resolved_company.id))
                    if not resolved_project:
                        # Project exists globally?
                        global_proj = projects_by_name.get(project_str.lower())
                        if global_proj:
                            # Retrieve mismatch details
                            gp_company = Company.query.get(global_proj.company_id)
                            gp_circle = Circle.query.get(global_proj.circle_id)
                            comp_name = gp_company.company_name if gp_company else "another company"
                            circ_name = gp_circle.circle_name if gp_circle else "another circle"
                            add_error(
                                "Project",
                                project_val,
                                f"Project '{project_val}' belongs to Company '{comp_name}' and Circle '{circ_name}'.",
                                f"Move project under '{company_str}' and '{circle_str}', or use a correct project name."
                            )
                        else:
                            scope_projects = [p.project_name for p in projects if p.company_id == resolved_company.id and p.circle_id == resolved_circle.id]
                            add_error(
                                "Project",
                                project_val,
                                f"Project '{project_val}' not found under company '{company_str}' & circle '{circle_str}'.",
                                f"Available projects for this circle: {', '.join(scope_projects) if scope_projects else 'None'}"
                            )
                    else:
                        row["project_id"] = resolved_project.id
                else:
                    # Mismatch or missing company/circle, fallback to global check
                    resolved_project = projects_by_name.get(project_str.lower())
                    if not resolved_project:
                        add_error(
                            "Project",
                            project_val,
                            f"Project '{project_val}' not found.",
                            f"Available projects: {', '.join(available_project_names[:10])}"
                        )
                    else:
                        row["project_id"] = resolved_project.id

            # Save the is_valid status directly on the row for easier UI preview mapping
            row["is_valid"] = (row_num not in error_rows)

        # Calculate summary metrics
        total = len(rows)
        failed = len(error_rows)
        valid = total - failed
        
        summary = {
            "total": total,
            "valid": valid,
            "failed": failed
        }
        
        return summary, errors
