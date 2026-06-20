# UI Inventory Report

This document presents a comprehensive inventory of the frontend assets and layout patterns across the VIL application, as part of Phase 0 frontend audit.

## 1. Templates Audited
*   **Total Templates**: 82
*   **Inheriting from `layouts/main.html`**: 34 templates
*   **NOT Inheriting from Layout (Manual Boilerplate Duplicate)**: 45 templates

### A. Templates Using Layout Inheritance
These templates correctly extend `layouts/main.html` and only define `content` or `scripts` blocks:
*   [access_control/index.html](file:///c:/Users/yadve/OneDrive/Desktop/vil-project-full-report/vil_zip_escalation/vil-project-full-report/templates/access_control/index.html)
*   [approvals/analytics.html](file:///c:/Users/yadve/OneDrive/Desktop/vil-project-full-report/vil_zip_escalation/vil-project-full-report/templates/approvals/analytics.html)
*   [approvals/index.html](file:///c:/Users/yadve/OneDrive/Desktop/vil-project-full-report/vil_zip_escalation/vil-project-full-report/templates/approvals/index.html)
*   [approvals/view.html](file:///c:/Users/yadve/OneDrive/Desktop/vil-project-full-report/vil_zip_escalation/vil-project-full-report/templates/approvals/view.html)
*   [attendance/approvals.html](file:///c:/Users/yadve/OneDrive/Desktop/vil-project-full-report/vil_zip_escalation/vil-project-full-report/templates/attendance/approvals.html)
*   [attendance/history.html](file:///c:/Users/yadve/OneDrive/Desktop/vil-project-full-report/vil_zip_escalation/vil-project-full-report/templates/attendance/history.html)
*   [attendance/live.html](file:///c:/Users/yadve/OneDrive/Desktop/vil-project-full-report/vil_zip_escalation/vil-project-full-report/templates/attendance/live.html)
*   [attendance/monitoring.html](file:///c:/Users/yadve/OneDrive/Desktop/vil-project-full-report/vil_zip_escalation/vil-project-full-report/templates/attendance/monitoring.html)
*   [attendance/shift_reports.html](file:///c:/Users/yadve/OneDrive/Desktop/vil-project-full-report/vil_zip_escalation/vil-project-full-report/templates/attendance/shift_reports.html)
*   [deployments/active.html](file:///c:/Users/yadve/OneDrive/Desktop/vil-project-full-report/vil_zip_escalation/vil-project-full-report/templates/deployments/active.html)
*   [deployments/approve.html](file:///c:/Users/yadve/OneDrive/Desktop/vil-project-full-report/vil_zip_escalation/vil-project-full-report/templates/deployments/approve.html)
*   [deployments/assign.html](file:///c:/Users/yadve/OneDrive/Desktop/vil-project-full-report/vil_zip_escalation/vil-project-full-report/templates/deployments/assign.html)
*   [deployments/assignment_dashboard.html](file:///c:/Users/yadve/OneDrive/Desktop/vil-project-full-report/vil_zip_escalation/vil-project-full-report/templates/deployments/assignment_dashboard.html)
*   [deployments/create.html](file:///c:/Users/yadve/OneDrive/Desktop/vil-project-full-report/vil_zip_escalation/vil-project-full-report/templates/deployments/create.html)
*   [deployments/detail.html](file:///c:/Users/yadve/OneDrive/Desktop/vil-project-full-report/vil_zip_escalation/vil-project-full-report/templates/deployments/detail.html)
*   [deployments/history.html](file:///c:/Users/yadve/OneDrive/Desktop/vil-project-full-report/vil_zip_escalation/vil-project-full-report/templates/deployments/history.html)
*   [deployments/index.html](file:///c:/Users/yadve/OneDrive/Desktop/vil-project-full-report/vil_zip_escalation/vil-project-full-report/templates/deployments/index.html)
*   [deployments/requests.html](file:///c:/Users/yadve/OneDrive/Desktop/vil-project-full-report/vil_zip_escalation/vil-project-full-report/templates/deployments/requests.html)
*   [deployments/helper_assignments/create.html](file:///c:/Users/yadve/OneDrive/Desktop/vil-project-full-report/vil_zip_escalation/vil-project-full-report/templates/deployments/helper_assignments/create.html)
*   [deployments/helper_assignments/edit.html](file:///c:/Users/yadve/OneDrive/Desktop/vil-project-full-report/vil_zip_escalation/vil-project-full-report/templates/deployments/helper_assignments/edit.html)
*   [deployments/helper_assignments/index.html](file:///c:/Users/yadve/OneDrive/Desktop/vil-project-full-report/vil_zip_escalation/vil-project-full-report/templates/deployments/helper_assignments/index.html)
*   [deployments/helper_assignments/view.html](file:///c:/Users/yadve/OneDrive/Desktop/vil-project-full-report/vil_zip_escalation/vil-project-full-report/templates/deployments/helper_assignments/view.html)
*   [notifications/index.html](file:///c:/Users/yadve/OneDrive/Desktop/vil-project-full-report/vil_zip_escalation/vil-project-full-report/templates/notifications/index.html)
*   [permissions/analytics.html](file:///c:/Users/yadve/OneDrive/Desktop/vil-project-full-report/vil_zip_escalation/vil-project-full-report/templates/permissions/analytics.html)
*   [permissions/audit.html](file:///c:/Users/yadve/OneDrive/Desktop/vil-project-full-report/vil_zip_escalation/vil-project-full-report/templates/permissions/audit.html)
*   [permissions/create.html](file:///c:/Users/yadve/OneDrive/Desktop/vil-project-full-report/vil_zip_escalation/vil-project-full-report/templates/permissions/create.html)
*   [permissions/dashboard.html](file:///c:/Users/yadve/OneDrive/Desktop/vil-project-full-report/vil_zip_escalation/vil-project-full-report/templates/permissions/dashboard.html)
*   [permissions/details.html](file:///c:/Users/yadve/OneDrive/Desktop/vil-project-full-report/vil_zip_escalation/vil-project-full-report/templates/permissions/details.html)
*   [permissions/edit.html](file:///c:/Users/yadve/OneDrive/Desktop/vil-project-full-report/vil_zip_escalation/vil-project-full-report/templates/permissions/edit.html)
*   [permissions/matrix.html](file:///c:/Users/yadve/OneDrive/Desktop/vil-project-full-report/vil_zip_escalation/vil-project-full-report/templates/permissions/matrix.html)
*   [permissions/registry.html](file:///c:/Users/yadve/OneDrive/Desktop/vil-project-full-report/vil_zip_escalation/vil-project-full-report/templates/permissions/registry.html)
*   [permissions/role_permissions.html](file:///c:/Users/yadve/OneDrive/Desktop/vil-project-full-report/vil_zip_escalation/vil-project-full-report/templates/permissions/role_permissions.html)
*   [permissions/settings.html](file:///c:/Users/yadve/OneDrive/Desktop/vil-project-full-report/vil_zip_escalation/vil-project-full-report/templates/permissions/settings.html)
*   [permissions/workflow_access.html](file:///c:/Users/yadve/OneDrive/Desktop/vil-project-full-report/vil_zip_escalation/vil-project-full-report/templates/permissions/workflow_access.html)

### B. Templates NOT Using Layout Inheritance
These templates repeat full boilerplate including `<!DOCTYPE html>`, `<head>`, styles imports, sidebar, navbar, and scripts manually:
*   [dashboard.html](file:///c:/Users/yadve/OneDrive/Desktop/vil-project-full-report/vil_zip_escalation/vil-project-full-report/templates/dashboard.html)
*   **Circles module**: `circles/create.html`, `circles/edit.html`, `circles/index.html`
*   **Clients module**: `clients/create.html`, `clients/details.html`, `clients/edit.html`, `clients/index.html`
*   **Companies module**: `companies/create.html`, `companies/edit.html`, `companies/index.html`
*   **Documents module**: `documents/drivers.html`, `documents/driver_detail.html`, `documents/vehicles.html`
*   **Drivers module**: `drivers/create.html`, `drivers/edit.html`, `drivers/list.html`, `drivers/profile.html`
*   **Projects module**: `projects/create.html`, `projects/details.html`, `projects/edit.html`, `projects/index.html`
*   **Roles module**: `roles/compare.html`, `roles/create.html`, `roles/detail.html`, `roles/list.html`
*   **Subzones module**: `subzones/create.html`, `subzones/details.html`, `subzones/edit.html`, `subzones/list.html`
*   **Users module**: `users/bulk_import.html`, `users/list.html`, `users/manage.html`, `users/profile.html`
*   **Vehicles module**: `vehicles/bulk_import.html`, `vehicles/create.html`, `vehicles/details.html`, `vehicles/edit.html`, `vehicles/index.html`, `vehicles/list.html`
*   **Auth modules**: `forgot_password.html`, `login.html`, `reset_password.html`
*   **Index Redirect**: `index.html`

---

## 2. Style Sheet Inventory
### A. CSS Files Loaded Globally
The following CSS files are loaded within the main layout (`layouts/main.html`) and therefore globally on inheriting pages:
*   `https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css` (Bootstrap 5 Core UI Framework)
*   `https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap` (Typography)
*   `https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@24,400,0,0` (Icons)
*   `static/css/design-tokens.css` (Design tokens variables for background, borders, colors, padding)
*   `static/css/sidebar.css` (Sidebar layout styling)
*   `static/css/navbar.css` (Navbar header styling)
*   `static/css/dashboard.css` (Operations metrics command dashboard template layout)
*   `static/css/permissions/permissions.css` (Module permissions styling overrides)

### B. CSS Files Loaded Per Module
*   `static/css/auth.css` -> loaded by login, forgot password, reset password templates.
*   `static/css/circle.css` -> loaded by circles create, edit, list templates.
*   `static/css/client.css` -> loaded by clients create, edit, list templates.
*   `static/css/company.css` -> loaded by companies create, edit, list templates.
*   `static/css/compliance.css` -> loaded by driver and vehicle documents compliance templates.
*   `static/css/drivers.css` -> loaded by driver profiles, create, edit, grid templates.
*   `static/css/projects/project.css` -> loaded by projects index, details, create, edit.
*   `static/css/projects/project-dashboard.css` -> loaded by projects details template.
*   `static/css/subzones/subzone.css` -> loaded by subzones list, edit, details, create.
*   `static/css/subzones/subzone-dashboard.css` -> loaded by subzones details.
*   `static/css/subzones/subzone-responsive.css` -> loaded by subzones create, details, edit.
*   `static/css/users/users.css` -> loaded by user profiles, management, index grid.
*   `static/css/vehicles/vehicle.css` -> loaded by vehicles list, edit, details, create.
*   `static/css/vehicles/vehicle-dashboard.css` -> loaded by vehicles details.
*   `static/css/vehicles/vehicle-responsive.css` -> loaded by vehicles create.

---

## 3. JavaScript Script Inventory
### A. JS Files Loaded Globally
*   `https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js` (Bootstrap 5 JS framework)
*   `static/js/sidebar.js` (Sidebar controls/responsive toggles)
*   `static/js/dashboard.js` (Command widgets updates)

### B. JS Files Loaded Per Module
*   `static/js/auth.js` -> loaded by `login.html`.
*   `static/js/circle.js` -> loaded by `circles/create.html`.
*   `static/js/client.js` -> loaded by `clients/create.html`, `clients/edit.html`.
*   `static/js/company.js` -> loaded by `companies/create.html`, `companies/edit.html`.
*   `static/js/drivers.js` -> loaded by `drivers/list.html`, `drivers/profile.html`.
*   `static/js/projects/project.js` -> loaded by `projects/create.html`, `projects/edit.html`.
*   `static/js/roles/roles.js` -> loaded by `roles/create.html`, `roles/list.html`.
*   `static/js/subzones/subzone.js` -> loaded by `subzones/create.html`, `subzones/edit.html`.
*   `static/js/subzones/dashboard.js` -> loaded by `subzones/details.html`.
*   `static/js/users/users.js` -> loaded by `users/list.html`, `users/manage.html`, `users/profile.html`.
*   `static/js/vehicles/vehicle.js` -> loaded by `drivers/create.html`, `drivers/edit.html`, `vehicles/create.html`, `vehicles/edit.html`.
*   `static/js/filters.js`, `static/js/widgets.js`, `static/js/charts.js`, `static/js/realtime.js` -> loaded by `dashboard.html`.

---

## 4. UI Duplications & Inconsistencies Identified
*   **Duplicate Layouts**: 45 modules carry repeating blocks representing base HTML shells, navbar integrations, and sidebar bindings. This makes visual adjustments complex and error-prone.
*   **Duplicate Forms Layouts**: Create and Edit forms for companies, circles, clients, projects, subzones, and vehicles repeat field elements and styling containers, often using different grid spacing (some use `g-3`, some use custom margins).
*   **Duplicate Table Data Grids**: Search filters, sorting headers, tables, and pagination items are repeated across 15+ list views. Status indicators use hardcoded Bootstrap classes instead of referencing standardized badge components.
*   **Page Header Inconsistencies**: Header sections use varying paddings and classes (e.g. `.dashboard-header`, `.permissions-header`, `.page-header`) resulting in inconsistent visual spacing between pages.
*   **Form Field Heights**: Heights for inputs range from 38px to 50px across modules, with variable border-radii (some use default, some use 4px, 8px, or 10px).
*   **Modals Redundancy**: HTML structures for Delete Confirmation, Bulk Import, and and State dropdowns are duplicated inline in multiple pages instead of using standardized modal layers or global trigger handlers.
