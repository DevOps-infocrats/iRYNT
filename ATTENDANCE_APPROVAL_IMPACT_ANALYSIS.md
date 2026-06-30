# Attendance Approval Impact Analysis

**Date:** 2026-06-30  
**Scope:** Circle MIS → Circle KAM attendance approval workflow (extension only)  
**Status:** Investigation complete — no breaking changes identified when implemented additively

---

## Executive Summary

The VIL attendance module is production-critical and shared by the web app and Android app. This analysis maps all touchpoints for adding a **two-stage circle-level approval workflow** (MIS → KAM) while preserving existing submission, geo, OCR, reporting, and payroll behavior.

The existing `DriverAttendance.status` field (values such as `Present`) remains the operational attendance state. A new independent `approval_status` field on `driver_attendance` carries the approval lifecycle without replacing or renaming existing fields.

---

## 1. Data Model

### Primary table: `driver_attendance` (`DriverAttendance`)

| Field | Purpose | Impact |
|-------|---------|--------|
| `status` | Operational attendance (`Present`, etc.) | **Unchanged** — not renamed to `attendance_status` |
| `verification_status` | Geo/KM anomaly flags | **Unchanged** |
| `selfie_storage_path`, `dashboard_storage_path` | Driver verification images | **Unchanged** |
| `start_odometer`, `end_odometer` | OCR/odometer capture | **Unchanged** |
| Geo fields (`geo_status`, `geo_verified`, etc.) | GPS validation | **Unchanged** |
| **NEW** `approval_status` | `SUBMITTED`, `MIS_APPROVED`, `KAM_APPROVED`, `REJECTED` | Additive, nullable for history |
| **NEW** Driver MIS checklist booleans | `seatbelt_verified`, `selfie_verified`, `dashboard_verified`, `odometer_verified` | Default `false` |
| **NEW** Helper MIS checklist booleans | `helmet_verified`, `safety_shoes_verified`, `safety_jacket_verified`, `id_card_verified` | Default `false` |
| **NEW** MIS audit | `mis_verified_by`, `mis_verified_at`, `mis_remarks` | Nullable |
| **NEW** KAM audit | `kam_verified_by`, `kam_verified_at`, `kam_remarks` | Nullable |

### Related entities (read-only for approval context)

- `driver_profiles` — `circle_id`, employee linkage
- `users` — `circle_id`, roles (Driver, Helper, MIS, Circle KAM)
- `vehicle_deployments` — active deployment, vehicle, project, circle
- `approval_requests` — **separate** geo-correction workflow; must not be conflated with new `approval_status`

### Backward compatibility

- Historical rows: `approval_status = NULL` remain valid
- No column drops, renames, or table changes
- Runtime schema guard + Alembic migration both support nullable new columns

---

## 2. Services & Business Logic

### `AttendanceService` (`app/modules/attendance/services.py`)

| Method | Current behavior | Extension impact |
|--------|------------------|------------------|
| `mark_attendance()` | Check-in/out, geo, images, odometer, notifications | **Minimal hook:** set `approval_status = SUBMITTED` on check-in; allow re-check-in after MIS resubmission |
| `get_attendance_approvals()` | Lists geo `ApprovalRequest` records | **Unchanged** — geo approvals remain separate |
| `_process_attendance_odometer()` | KM anomaly handling | **Unchanged** |
| `_trigger_attendance_notifications()` | User + KAM geo alerts | **Unchanged** |

### `AttendanceGeoService` (`app/services/geolocation/attendance_geo_service.py`)

- GPS validation, geofence, `ApprovalRequest` for geo review — **no changes required**

### New: `AttendanceApprovalService` (`app/modules/attendance/approval_service.py`)

- MIS queue, KAM queue, circle access checks, checklist persistence, notifications
- Does not replace or wrap `mark_attendance`

---

## 3. Web Routes

### Existing (`app/modules/attendance/routes.py`)

| Route | Purpose | Impact |
|-------|---------|--------|
| `/attendance/live` | Mark/view live attendance | Display new approval labels for helpers/drivers |
| `/attendance/history` | History listing | Optional `approval_status` filter added |
| `/attendance/monitoring` | Check-in monitoring | **Unchanged** counts |
| `/attendance/approvals` | Geo correction approvals | **Unchanged** |
| `/attendance/mark` | Web check-in/out POST | **Unchanged** payload |
| `/attendance/verification-image/...` | Image serving | Extended RBAC for same-circle MIS/KAM |

### New routes

| Route | Role | Purpose |
|-------|------|---------|
| `/attendance/mis-approvals` | MIS (same circle) | Verification dashboard |
| `/attendance/mis-approvals/<id>/action` | MIS | Approve / Reject / Request Resubmission |
| `/attendance/kam-approvals` | Circle KAM (same circle) | Final approval dashboard |
| `/attendance/kam-approvals/<id>/action` | Circle KAM | Approve / Reject |

---

## 4. Android / REST APIs

### Endpoints (`app/api/v1/attendance/routes.py`)

| Endpoint | Method | Impact |
|----------|--------|--------|
| `/api/v1/attendance/check-in` | POST | **Payload unchanged**; response adds `approval_status`, `approval_status_label` |
| `/api/v1/attendance/check-out` | POST | **Payload unchanged**; response adds approval fields |
| `/api/v1/attendance/history` | GET | **Unchanged** query params; response adds approval fields |
| `/api/v1/attendance/gps/sync` | POST | **Unchanged** |

### Serializers (`app/api/v1/attendance/serializers.py`)

- `CheckInRequestSchema` / `CheckOutRequestSchema` — **unchanged**
- `AttendanceResponseSchema` — **additive** `approval_status`, `approval_status_label`

**Android integration:** No Retrofit request changes. Display-only consumption of new response fields.

---

## 5. Reports & Dashboards

| Component | File | Impact |
|-----------|------|--------|
| Live dashboard | `templates/attendance/live.html` | Approval badge labels for mobile-facing statuses |
| Monitoring summary | `repository.get_monitoring_summary()` | **Unchanged** — still counts check-ins by geo |
| Shift reports | `get_shift_reports()` placeholder | **Unchanged** |
| History export | History template | **Unchanged**; optional filter via query param |
| Driver profile stats | `drivers/repository.py` avg hours | **Unchanged** — uses `hours_worked` |

Existing geo-based **Attendance Approvals** page (`templates/attendance/approvals.html`) remains for `ApprovalRequest` geo corrections.

---

## 6. Payroll Dependencies

- `DriverPayroll` is a separate table; no direct FK to `approval_status`
- Driver stats use `DriverAttendance.hours_worked` and `status` — **unchanged**
- Payroll module does not filter on approval state today — **no payroll logic modified**

---

## 7. Existing Approval Systems (Do Not Conflate)

| System | Table/Model | Purpose |
|--------|-------------|---------|
| Geo attendance correction | `approval_requests` | Outside geofence / low accuracy |
| Deployment approval | `vehicle_deployments.approval_status` | Deployment lifecycle |
| Generic approvals module | `ApprovalRequest` | Cross-module workflows |

New workflow uses **`driver_attendance.approval_status`** only — independent from all above.

---

## 8. Role & Access Control

| Role | Circle scope | New capability |
|------|--------------|--------------|
| MIS | `user.circle_id` | Verify SUBMITTED attendance in same circle |
| Circle KAM | `user.circle_id` | Approve MIS_APPROVED attendance in same circle |
| Driver / Helper | Own records | View approval status on live/history/API |
| Super Admin | Global | Bypass circle filter |

**Enforcement:** `employee.circle_id == approver.circle_id` (via profile, user, or active deployment project).

---

## 9. Risk Assessment

| Risk | Mitigation |
|------|------------|
| Breaking Android check-in | No request schema changes; only additive response fields |
| Breaking geo workflow | Separate `ApprovalRequest` path untouched |
| Historical data invalid | Nullable `approval_status`; NULL = pre-workflow records |
| Cross-circle data leak | Explicit circle check on MIS/KAM actions and image access |
| Payroll miscount | No change to `hours_worked` or `status` calculation |
| Migration failure | Runtime `_ensure_attendance_approval_schema()` + Alembic migration |

---

## 10. Files Inspected

```
app/modules/drivers/models.py
app/modules/attendance/models.py
app/modules/attendance/services.py
app/modules/attendance/repository.py
app/modules/attendance/routes.py
app/modules/attendance/api_routes.py
app/api/v1/attendance/routes.py
app/api/v1/attendance/controllers.py
app/api/v1/attendance/serializers.py
app/services/geolocation/attendance_geo_service.py
app/modules/approvals/models.py
app/modules/approvals/services.py
app/modules/drivers/repository.py
app/core/sidebar.py
app/__init__.py
templates/attendance/live.html
templates/attendance/history.html
templates/attendance/approvals.html
templates/attendance/monitoring.html
tests/api/test_attendance_api.py
tests/test_attendance_verification.py
migrations/versions/9a1b2c3d4e5f_add_attendance_geo_fields.py
app/modules/roles/templates/mis.json
app/modules/roles/templates/circle_kam.json
```

---

## 11. Recommended Implementation Order

1. Database columns + runtime schema guard  
2. `AttendanceApprovalService` + check-in hook (`SUBMITTED`)  
3. MIS/KAM web dashboards and actions  
4. API response fields for Android display  
5. Optional history filter  
6. Automated tests + regression suite  

---

## 12. Conclusion

The attendance module can safely extended with a circle-scoped MIS → KAM approval workflow using **additive database columns**, a **new service**, and **new web routes** without modifying OCR, GPS, deployment, payroll, or existing API request payloads. The existing `status` field and geo-based `ApprovalRequest` flow remain fully operational.
