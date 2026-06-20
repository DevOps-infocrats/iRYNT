import re
from datetime import date
from app.modules.companies.models import Company
from app.modules.circles.models import Circle
from app.modules.clients.models import Client
from app.modules.projects.models import Project
from app.modules.subzones.models import Subzone
from app.modules.vehicles.models import Vehicle
from app.modules.vehicles.vehicle_status import VEHICLE_TYPES, VEHICLE_CATEGORIES

class VehicleValidationService:
    """Service to validate vehicle data parsed from Excel files."""

    def __init__(self):
        self.year_regex = re.compile(r"^\d{4}$")
        self.phone_regex = re.compile(r"^\d{10}$")

    def validate(self, rows: list) -> tuple:
        """Validate a list of vehicle row dicts.
        Returns a tuple of (summary, errors).
        """
        errors = []
        
        # 1. Pre-fetch active master lists to optimize lookups
        companies = Company.query.filter_by(status='Active').all()
        circles = Circle.query.filter_by(status='Active').all()
        clients = Client.query.filter_by(status='Active').all()
        projects = Project.query.filter_by(status='Active').all()
        subzones = Subzone.query.filter_by(status='Active').all()
        vehicles = Vehicle.query.all()

        # Dictionaries for hierarchy resolution
        companies_by_name = {c.company_name.strip().lower(): c for c in companies}
        
        circles_by_name_and_company = {}
        circles_by_name = {}
        for circ in circles:
            circles_by_name_and_company[(circ.circle_name.strip().lower(), circ.company_id)] = circ
            circles_by_name[circ.circle_name.strip().lower()] = circ

        clients_by_name_circle_company = {}
        clients_by_name = {}
        for cl in clients:
            clients_by_name_circle_company[(cl.client_name.strip().lower(), cl.circle_id, cl.company_id)] = cl
            clients_by_name[cl.client_name.strip().lower()] = cl

        projects_by_name_client_circle_company = {}
        projects_by_name = {}
        for p in projects:
            projects_by_name_client_circle_company[(p.project_name.strip().lower(), p.client_id, p.circle_id, p.company_id)] = p
            projects_by_name[p.project_name.strip().lower()] = p

        subzones_by_name_project_client_circle_company = {}
        subzones_by_name = {}
        for s in subzones:
            subzones_by_name_project_client_circle_company[(s.subzone_name.strip().lower(), s.project_id, s.client_id, s.circle_id, s.company_id)] = s
            subzones_by_name[s.subzone_name.strip().lower()] = s

        # Global system uniqueness lists
        existing_vehicle_keys = {
            (v.company_id, v.circle_id, v.client_id, v.project_id, v.subzone_id, v.vehicle_number.strip().upper())
            for v in vehicles if v.vehicle_number
        }
        existing_chassis = {v.chassis_number.strip().lower() for v in vehicles if v.chassis_number}
        existing_engines = {v.engine_number.strip().lower() for v in vehicles if v.engine_number}

        # Valid choices lists
        valid_types = {t[1].lower(): t[1] for t in VEHICLE_TYPES if t[0]}
        valid_categories = {c[1].lower(): c[1] for c in VEHICLE_CATEGORIES if c[0]}

        current_year = date.today().year
        valid_years = {str(y) for y in range(current_year, current_year - 25, -1)}

        # Sheet-level trackers for duplicate detection
        sheet_vehicles = {}
        sheet_chassis = {}
        sheet_engines = {}

        error_rows = set()

        for row in rows:
            row_num = row.get("row_number")
            
            def add_error(column_name, cell_val, msg, fix):
                error_rows.add(row_num)
                errors.append({
                    "row_number": row_num,
                    "column": column_name,
                    "value": cell_val,
                    "message": msg,
                    "suggested_fix": fix
                })

            # Helper for yes/no parsing
            def parse_bool(val, default_val=True):
                if val is None:
                    return default_val
                val_str = str(val).strip().lower()
                if val_str in ("yes", "y", "true", "1"):
                    return True
                if val_str in ("no", "n", "false", "0"):
                    return False
                return default_val

            # Resolve Boolean flags
            row["gps_enabled"] = parse_bool(row.get("GPS Enabled"), True)
            row["realtime_tracking_enabled"] = parse_bool(row.get("Realtime Tracking Enabled"), True)
            row["deployment_allowed"] = parse_bool(row.get("Deployment Allowed"), True)

            # Resolve free-text or optional fields
            row["vehicle_brand"] = str(row.get("Vehicle Brand") or "").strip()
            row["vehicle_model"] = str(row.get("Vehicle Model") or "").strip()
            row["owner_name"] = str(row.get("Owner Name") or "").strip() or None
            row["owner_phone"] = str(row.get("Owner Phone") or "").strip() or None
            row["vendor_name"] = str(row.get("Vendor Name") or "").strip() or None
            row["vendor_contact"] = str(row.get("Vendor Contact") or "").strip() or None

            # Validate Vehicle Brand & Model
            if not row["vehicle_brand"]:
                add_error("Vehicle Brand", row.get("Vehicle Brand"), "Vehicle Brand is required.", "Enter a brand name like Tata, Mahindra.")
            if not row["vehicle_model"]:
                add_error("Vehicle Model", row.get("Vehicle Model"), "Vehicle Model is required.", "Enter a model name like Ace, Eeco.")

            # Validate phone numbers if provided
            for key, col in [("owner_phone", "Owner Phone"), ("vendor_contact", "Vendor Contact")]:
                val = row[key]
                if val:
                    # Clean float string format if parsed as number
                    val_str = val.split('.')[0]
                    if not self.phone_regex.match(val_str):
                        add_error(col, val, f"{col} must be a 10-digit mobile number.", "Enter a valid 10-digit phone number.")
                    else:
                        row[key] = val_str

            # 2. Hierarchy validation (Company -> Circle -> Client -> Project -> Subzone)
            # Resolve Company
            company_val = row.get("Company")
            company_str = str(company_val or "").strip()
            resolved_company = None
            if not company_str:
                add_error("Company", company_val, "Company name is required.", "Select an active Company.")
            else:
                resolved_company = companies_by_name.get(company_str.lower())
                if not resolved_company:
                    available = [c.company_name for c in companies[:8]]
                    add_error("Company", company_val, f"Company '{company_val}' not found.", f"Select from: {', '.join(available)}")
                else:
                    row["company_id"] = resolved_company.id

            # Resolve Circle
            circle_val = row.get("Circle")
            circle_str = str(circle_val or "").strip()
            resolved_circle = None
            if not circle_str:
                add_error("Circle", circle_val, "Circle name is required.", "Select an active Circle.")
            else:
                if resolved_company:
                    resolved_circle = circles_by_name_and_company.get((circle_str.lower(), resolved_company.id))
                    if not resolved_circle:
                        available_circles = [c.circle_name for c in circles if c.company_id == resolved_company.id]
                        add_error(
                            "Circle", 
                            circle_val, 
                            f"Circle '{circle_val}' is not associated with company '{company_str}'.", 
                            f"Select from circles for this company: {', '.join(available_circles) if available_circles else 'None'}"
                        )
                    else:
                        row["circle_id"] = resolved_circle.id
                else:
                    resolved_circle = circles_by_name.get(circle_str.lower())
                    if not resolved_circle:
                        add_error("Circle", circle_val, f"Circle '{circle_val}' not found.", "Select an active Circle.")
                    else:
                        row["circle_id"] = resolved_circle.id

            # Resolve Client
            client_val = row.get("Client")
            client_str = str(client_val or "").strip()
            resolved_client = None
            if not client_str:
                add_error("Client", client_val, "Client name is required.", "Select an active Client.")
            else:
                if resolved_company and resolved_circle:
                    resolved_client = clients_by_name_circle_company.get((client_str.lower(), resolved_circle.id, resolved_company.id))
                    if not resolved_client:
                        available_clients = [c.client_name for c in clients if c.circle_id == resolved_circle.id and c.company_id == resolved_company.id]
                        add_error(
                            "Client", 
                            client_val, 
                            f"Client '{client_val}' not found under company '{company_str}' & circle '{circle_str}'.", 
                            f"Select from clients in this scope: {', '.join(available_clients) if available_clients else 'None'}"
                        )
                    else:
                        row["client_id"] = resolved_client.id
                else:
                    resolved_client = clients_by_name.get(client_str.lower())
                    if not resolved_client:
                        add_error("Client", client_val, f"Client '{client_val}' not found.", "Select an active Client.")
                    else:
                        row["client_id"] = resolved_client.id

            # Resolve Project
            project_val = row.get("Project")
            project_str = str(project_val or "").strip()
            resolved_project = None
            if not project_str:
                add_error("Project", project_val, "Project name is required.", "Select an active Project.")
            else:
                if resolved_company and resolved_circle and resolved_client:
                    resolved_project = projects_by_name_client_circle_company.get((project_str.lower(), resolved_client.id, resolved_circle.id, resolved_company.id))
                    if not resolved_project:
                        available_projects = [p.project_name for p in projects if p.client_id == resolved_client.id and p.circle_id == resolved_circle.id and p.company_id == resolved_company.id]
                        add_error(
                            "Project", 
                            project_val, 
                            f"Project '{project_val}' not found under company '{company_str}', circle '{circle_str}' & client '{client_str}'.", 
                            f"Select from projects in this scope: {', '.join(available_projects) if available_projects else 'None'}"
                        )
                    else:
                        row["project_id"] = resolved_project.id
                else:
                    resolved_project = projects_by_name.get(project_str.lower())
                    if not resolved_project:
                        add_error("Project", project_val, f"Project '{project_val}' not found.", "Select an active Project.")
                    else:
                        row["project_id"] = resolved_project.id

            # Resolve Subzone
            subzone_val = row.get("Subzone")
            subzone_str = str(subzone_val or "").strip()
            resolved_subzone = None
            if not subzone_str:
                add_error("Subzone", subzone_val, "Subzone name is required.", "Select an active Subzone.")
            else:
                if resolved_company and resolved_circle and resolved_client and resolved_project:
                    resolved_subzone = subzones_by_name_project_client_circle_company.get((subzone_str.lower(), resolved_project.id, resolved_client.id, resolved_circle.id, resolved_company.id))
                    if not resolved_subzone:
                        available_subzones = [s.subzone_name for s in subzones if s.project_id == resolved_project.id and s.client_id == resolved_client.id and s.circle_id == resolved_circle.id and s.company_id == resolved_company.id]
                        add_error(
                            "Subzone", 
                            subzone_val, 
                            f"Subzone '{subzone_val}' not found under Project '{project_str}'.", 
                            f"Select from subzones in this scope: {', '.join(available_subzones) if available_subzones else 'None'}"
                        )
                    else:
                        row["subzone_id"] = resolved_subzone.id
                else:
                    resolved_subzone = subzones_by_name.get(subzone_str.lower())
                    if not resolved_subzone:
                        add_error("Subzone", subzone_val, f"Subzone '{subzone_val}' not found.", "Select an active Subzone.")
                    else:
                        row["subzone_id"] = resolved_subzone.id

            # 3. Vehicle Number Validation
            vnum_val = row.get("Vehicle Number")
            vnum_str = str(vnum_val or "").strip().upper()
            if not vnum_str:
                add_error("Vehicle Number", vnum_val, "Vehicle Number is required.", "Enter a vehicle registration number.")
            elif len(vnum_str) < 8 or len(vnum_str) > 12:
                add_error("Vehicle Number", vnum_str, "Vehicle number must be between 8 and 12 characters.", "Use format like UP32AB1234.")
            else:
                row["vehicle_number"] = vnum_str
                # Scope-based duplicate check
                if resolved_company and resolved_circle and resolved_client and resolved_project and resolved_subzone:
                    scope_key = (resolved_company.id, resolved_circle.id, resolved_client.id, resolved_project.id, resolved_subzone.id, vnum_str)
                    if scope_key in existing_vehicle_keys:
                        add_error("Vehicle Number", vnum_str, f"Vehicle '{vnum_str}' already exists in this Subzone.", "Enter a unique vehicle number.")
                    elif scope_key in sheet_vehicles:
                        add_error("Vehicle Number", vnum_str, f"Duplicate vehicle '{vnum_str}' in this sheet for this Subzone.", f"Coordinate with row {sheet_vehicles[scope_key]}.")
                    else:
                        sheet_vehicles[scope_key] = row_num

            # 4. Vehicle Type Validation
            vtype_val = row.get("Vehicle Type")
            vtype_str = str(vtype_val or "").strip()
            if not vtype_str:
                add_error("Vehicle Type", vtype_val, "Vehicle Type is required.", f"Allowed: {', '.join(valid_types.values())}")
            elif vtype_str.lower() not in valid_types:
                add_error("Vehicle Type", vtype_val, f"Vehicle Type '{vtype_val}' is invalid.", f"Allowed: {', '.join(valid_types.values())}")
            else:
                row["vehicle_type"] = valid_types[vtype_str.lower()]

            # 5. Vehicle Category Validation
            vcat_val = row.get("Vehicle Category")
            vcat_str = str(vcat_val or "").strip()
            if not vcat_str:
                add_error("Vehicle Category", vcat_val, "Vehicle Category is required.", f"Allowed: {', '.join(valid_categories.values())}")
            elif vcat_str.lower() not in valid_categories:
                add_error("Vehicle Category", vcat_val, f"Vehicle Category '{vcat_val}' is invalid.", f"Allowed: {', '.join(valid_categories.values())}")
            else:
                row["vehicle_category"] = valid_categories[vcat_str.lower()]

            # 6. Manufacturing Year Validation
            myear_val = row.get("Manufacturing Year")
            myear_str = str(myear_val or "").strip().split('.')[0]
            if not myear_str:
                add_error("Manufacturing Year", myear_val, "Manufacturing Year is required.", "Enter a valid 4-digit year.")
            elif myear_str not in valid_years:
                add_error("Manufacturing Year", myear_val, f"Manufacturing Year '{myear_val}' is invalid or too old.", f"Must be between {current_year - 24} and {current_year}.")
            else:
                row["manufacturing_year"] = myear_str

            # 7. Unique Chassis & Engine checks
            for field, col, existing_set, sheet_dict in [
                ("Chassis Number", "Chassis Number", existing_chassis, sheet_chassis),
                ("Engine Number", "Engine Number", existing_engines, sheet_engines)
            ]:
                val = row.get(field)
                val_str = str(val or "").strip().lower() if val is not None else ""
                row[field.lower().replace(" ", "_")] = val_str or None
                if val_str:
                    if val_str in existing_set:
                        add_error(field, val, f"{field} '{val}' already exists in system.", f"Choose a unique {field.lower()}.")
                    elif val_str in sheet_dict:
                        add_error(field, val, f"Duplicate {field} '{val}' in this sheet.", f"Coordinate with row {sheet_dict[val_str]}.")
                    else:
                        sheet_dict[val_str] = row_num

            row["is_valid"] = (row_num not in error_rows)

        total = len(rows)
        failed = len(error_rows)
        valid = total - failed

        return {
            "total": total,
            "valid": valid,
            "failed": failed
        }, errors
