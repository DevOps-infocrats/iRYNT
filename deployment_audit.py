# deployment_audit.py
"""Deployment Readiness Audit Script
Generates two reports:
- DEPLOYMENT_READINESS_REPORT.md
- RESOLUTION_GUIDE.md
The script performs static analysis of the Flask project located in the same directory.
"""
import os
import ast
import re
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
REPORT_DIR = PROJECT_ROOT / "audit_reports"
REPORT_DIR.mkdir(exist_ok=True)

REPORT_MD = REPORT_DIR / "DEPLOYMENT_READINESS_REPORT.md"
RESOLUTION_MD = REPORT_DIR / "RESOLUTION_GUIDE.md"

# Helper data structures
issues = []
issue_counter = 1

def add_issue(severity, module, description, location, recommendation=""):
    global issue_counter
    issue_id = f"ISSUE-{issue_counter:03d}"
    issue_counter += 1
    issues.append({
        "id": issue_id,
        "severity": severity,
        "module": module,
        "description": description,
        "location": location,
        "recommendation": recommendation,
    })
    return issue_id

# Phase 1: Project inventory (collect files)
python_files = list(PROJECT_ROOT.rglob("*.py"))
template_files = list(PROJECT_ROOT.rglob("templates/**/*.html"))
static_files = list(PROJECT_ROOT.rglob("static/**/*"))

# Phase 2: Route & navigation audit
route_pattern = re.compile(r"@(?:app|bp)\.route\(['\"]([^'\"]+)['\"]")
url_for_pattern = re.compile(r"url_for\(['\"]([^'\"]+)['\"]")

registered_routes = {}
for py_path in python_files:
    try:
        source = py_path.read_text(encoding="utf-8")
    except Exception:
        continue
    for match in route_pattern.finditer(source):
        route = match.group(1)
        registered_routes.setdefault(route, []).append(str(py_path))

# Check for duplicate routes
for route, files in registered_routes.items():
    if len(files) > 1:
        add_issue(
            severity="High",
            module="Routing",
            description=f"Duplicate route definition for '{route}'.",
            location=", ".join(files),
            recommendation="Consolidate to a single definition."
        )

# Scan templates for url_for references that may be broken
all_endpoint_names = set()
# Collect endpoint names from @app.route decorators (function names)
for py_path in python_files:
    try:
        tree = ast.parse(py_path.read_text(encoding="utf-8"), filename=str(py_path))
    except Exception:
        continue
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            # Find decorators that are route decorators
            for dec in node.decorator_list:
                if isinstance(dec, ast.Call) and isinstance(dec.func, ast.Attribute):
                    if dec.func.attr == "route":
                        endpoint = getattr(dec.func.value, "id", None)
                        # endpoint could be "app" or blueprint variable
                        # Use function name as endpoint unless endpoint defined via name param
                        name_arg = None
                        for kw in dec.keywords:
                            if kw.arg == "endpoint":
                                if isinstance(kw.value, ast.Str):
                                    name_arg = kw.value.s
                        endpoint_name = name_arg if name_arg else node.name
                        all_endpoint_names.add(endpoint_name)

# Validate url_for usages
for tmpl_path in template_files:
    tmpl_text = tmpl_path.read_text(encoding="utf-8")
    for match in url_for_pattern.finditer(tmpl_text):
        endpoint = match.group(1)
        if endpoint not in all_endpoint_names:
            add_issue(
                severity="Medium",
                module="Template Links",
                description=f"url_for reference to unknown endpoint '{endpoint}'.",
                location=str(tmpl_path),
                recommendation="Create the missing view function or correct the endpoint name."
            )

# Phase 3: Database audit (SQLAlchemy models)
model_classes = []
for py_path in python_files:
    try:
        tree = ast.parse(py_path.read_text(encoding="utf-8"), filename=str(py_path))
    except Exception:
        continue
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.ClassDef):
            # Look for inheritance from db.Model (or similar)
            for base in node.bases:
                if isinstance(base, ast.Attribute) and base.attr == "Model":
                    model_classes.append((node.name, py_path))
                elif isinstance(base, ast.Name) and base.id == "Model":
                    model_classes.append((node.name, py_path))

# Simple check for missing __tablename__
for name, path in model_classes:
    src = path.read_text(encoding="utf-8")
    if "__tablename__" not in src:
        add_issue(
            severity="Low",
            module="Database Models",
            description=f"Model '{name}' missing explicit __tablename__.",
            location=str(path),
            recommendation="Define __tablename__ to avoid naming ambiguities."
        )

# Phase 4: Migration audit (Alembic)
alembic_dir = PROJECT_ROOT / "migrations"
if alembic_dir.is_dir():
    revision_files = list(alembic_dir.rglob("*.py"))
    revisions = {}
    for rev_path in revision_files:
        text = rev_path.read_text(encoding="utf-8")
        rev_match = re.search(r"revision = ['\"]([a-f0-9]+)['\"]", text)
        down_match = re.search(r"down_revision = ['\"]([a-f0-9]+|None)['\"]", text)
        if rev_match:
            rev_id = rev_match.group(1)
            down_id = down_match.group(1) if down_match else None
            revisions[rev_id] = {
                "path": str(rev_path),
                "down": down_id,
                "content": text,
            }
    # Detect missing down_revision links
    for rev_id, data in revisions.items():
        if data["down"] == "None":
            continue
        if data["down"] not in revisions:
            add_issue(
                severity="High",
                module="Migrations",
                description=f"Migration {rev_id} has missing down_revision {data['down']}.",
                location=data["path"],
                recommendation="Create the missing migration or fix the revision chain."
            )
else:
    add_issue(
        severity="Medium",
        module="Migrations",
        description="Migrations directory not found.",
        location="Project root",
        recommendation="Ensure Alembic is initialized and migrations are present."
    )

# Phase 5: Production configuration audit
config_path = PROJECT_ROOT / "config.py"
if config_path.is_file():
    config_text = config_path.read_text(encoding="utf-8")
    if "DEBUG = True" in config_text or "DEBUG=True" in config_text:
        add_issue(
            severity="High",
            module="Configuration",
            description="DEBUG mode is enabled in config.py.",
            location=str(config_path),
            recommendation="Set DEBUG=False for production."
        )
    if re.search(r"SECRET_KEY\s*=\s*['\"][^'\"]+['\"]", config_text):
        add_issue(
            severity="Critical",
            module="Configuration",
            description="Hard‑coded SECRET_KEY found.",
            location=str(config_path),
            recommendation="Load SECRET_KEY from environment variable."
        )
else:
    add_issue(
        severity="Medium",
        module="Configuration",
        description="config.py not found.",
        location="Project root",
        recommendation="Create a configuration module with proper environment handling."
    )

# Phase 6: File storage audit (look for upload folder definitions)
upload_patterns = [r"UPLOAD_FOLDER\s*=\s*['\"]([^'\"]+)['\"]", r"upload_path\s*=\s*['\"]([^'\"]+)['\"]"]
for py_path in python_files:
    text = py_path.read_text(encoding="utf-8")
    for pat in upload_patterns:
        for m in re.finditer(pat, text):
            folder = m.group(1)
            # Resolve relative to project root
            folder_path = (PROJECT_ROOT / folder).resolve()
            if not folder_path.is_dir():
                add_issue(
                    severity="Medium",
                    module="File Storage",
                    description=f"Upload folder '{folder}' may not exist at runtime.",
                    location=str(py_path),
                    recommendation="Ensure the folder is created and has proper permissions."
                )

# Phase 7: Security audit (basic checks)
# Look for usage of Flask-WTF CSRFProtect
csrf_used = any("CSRFProtect" in p.read_text(encoding="utf-8") for p in python_files)
if not csrf_used:
    add_issue(
        severity="High",
        module="Security",
        description="CSRF protection not enabled via Flask-WTF.",
        location="Project code",
        recommendation="Initialize CSRFProtect(app) and ensure forms have csrf_token."
    )
# Look for plain password handling (e.g., storing "password" directly)
for py_path in python_files:
    txt = py_path.read_text(encoding="utf-8")
    if re.search(r"password\s*=\s*['\"][^'\"]+['\"]", txt):
        add_issue(
            severity="Critical",
            module="Security",
            description="Hard‑coded password found.",
            location=str(py_path),
            recommendation="Remove hard‑coded passwords and use proper hashing."
        )

# Phase 8 & 9: Attendance & Deployment workflow audit (simple presence checks)
# Search for 'attendance' module functions and missing validations
attendance_routes = PROJECT_ROOT / "app" / "modules" / "attendance" / "routes.py"
if attendance_routes.is_file():
    att_text = attendance_routes.read_text(encoding="utf-8")
    if "@app.route" not in att_text and "@bp.route" not in att_text:
        add_issue(
            severity="Low",
            module="Attendance",
            description="No routes defined in attendance module.",
            location=str(attendance_routes),
            recommendation="Define Flask routes for attendance endpoints."
        )
else:
    add_issue(
        severity="Medium",
        module="Attendance",
        description="Attendance routes file missing.",
        location="app/modules/attendance",
        recommendation="Create routes for attendance functionality."
    )

# Phase 10: Notification audit – check for duplicate alerts in helpers
notif_helper = PROJECT_ROOT / "app" / "modules" / "notifications" / "helpers.py"
if notif_helper.is_file():
    notif_text = notif_helper.read_text(encoding="utf-8")
    if "def create_notification" not in notif_text:
        add_issue(
            severity="Medium",
            module="Notifications",
            description="Notification creation helper missing expected function.",
            location=str(notif_helper),
            recommendation="Implement create_notification helper."
        )

# Phase 11: VPS deployment readiness – requirements.txt
req_path = PROJECT_ROOT / "requirements.txt"
if req_path.is_file():
    req_text = req_path.read_text(encoding="utf-8")
    # Look for gunicorn and psycopg2
    if not re.search(r"gunicorn", req_text, re.IGNORECASE):
        add_issue(
            severity="Medium",
            module="Deployment",
            description="gunicorn not listed in requirements.txt.",
            location=str(req_path),
            recommendation="Add gunicorn to requirements for production WSGI server."
        )
    if not re.search(r"psycopg2", req_text, re.IGNORECASE):
        add_issue(
            severity="Medium",
            module="Deployment",
            description="PostgreSQL driver (psycopg2) missing in requirements.txt.",
            location=str(req_path),
            recommendation="Add psycopg2 or psycopg2-binary."
        )
else:
    add_issue(
        severity="Critical",
        module="Deployment",
        description="requirements.txt not found.",
        location="Project root",
        recommendation="Create a requirements file with all dependencies."
    )

# Phase 12: Performance audit – simple N+1 detection
for py_path in python_files:
    src = py_path.read_text(encoding="utf-8")
    if ".all()" in src and "for" in src:
        # naive detection of .all() inside loop
        add_issue(
            severity="Medium",
            module="Performance",
            description="Potential N+1 query pattern detected ('.all()' inside loop).",
            location=str(py_path),
            recommendation="Refactor to bulk query or use joinedload."
        )
        break

# Phase 13: Automated failure scan
markers = ["TODO", "FIXME", "pass", "NotImplemented", "debug=True", "localhost", "127.0.0.1"]
for py_path in python_files:
    lines = py_path.read_text(encoding="utf-8").splitlines()
    for idx, line in enumerate(lines, start=1):
        for marker in markers:
            if marker in line:
                add_issue(
                    severity="Low",
                    module="Code Quality",
                    description=f"Found marker '{marker}' in code.",
                    location=f"{py_path}:{idx}",
                    recommendation="Address or remove marker."
                )

# Generate reports
severity_order = {"Critical": 1, "High": 2, "Medium": 3, "Low": 4}
issues_sorted = sorted(issues, key=lambda x: severity_order.get(x["severity"], 5))

# DEPLOYMENT_READINESS_REPORT.md
with open(REPORT_MD, "w", encoding="utf-8") as f:
    f.write("# Deployment Readiness Report\n\n")
    f.write("## Executive Summary\n\n")
    total = len(issues_sorted)
    f.write(f"Found **{total}** potential issues across the project.\n\n")
    # Simple score: 100 - (critical*5 + high*3 + medium*1) * 2
    score = 100
    for iss in issues_sorted:
        if iss["severity"] == "Critical":
            score -= 5
        elif iss["severity"] == "High":
            score -= 3
        elif iss["severity"] == "Medium":
            score -= 1
    score = max(score, 0)
    f.write(f"**Deployment Readiness Score:** {score}/100\n\n")
    # Group by severity
    for sev in ["Critical", "High", "Medium", "Low"]:
        sev_issues = [i for i in issues_sorted if i["severity"] == sev]
        if sev_issues:
            f.write(f"### {sev} Issues\n\n")
            for i in sev_issues:
                f.write(f"- **{i['id']}** ({i['module']}): {i['description']}  \n  Location: `{i['location']}`  \n  Recommendation: {i['recommendation']}\n\n")

# RESOLUTION_GUIDE.md
with open(RESOLUTION_MD, "w", encoding="utf-8") as f:
    f.write("# Resolution Guide\n\n")
    for i in issues_sorted:
        f.write(f"## {i['id']}\n")
        f.write(f"- **Severity:** {i['severity']}\n")
        f.write(f"- **Module:** {i['module']}\n")
        f.write(f"- **Description:** {i['description']}\n")
        f.write(f"- **Location:** `{i['location']}`\n")
        f.write(f"- **Recommended Fix:** {i['recommendation']}\n")
        f.write("- **Implementation Steps:** *(to be defined by engineers)*\n")
        f.write("- **Testing Steps:** *(to be defined)*\n")
        f.write("- **Regression Risk:** *(to be assessed)*\n")
        f.write("- **Rollback Strategy:** *(to be defined)*\n\n")

print(f"Audit completed. Reports generated at {REPORT_DIR}")
