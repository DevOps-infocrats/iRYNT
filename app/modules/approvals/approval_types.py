"""
Approval Types

Shared approval type constants, display labels, and default workflow mappings.
"""

APPROVAL_TYPE_CHOICES = [
    ('employee_onboarding', 'Employee Onboarding'),
    ('driver_verification', 'Driver Verification'),
    ('labour_approval', 'Labour Approval'),
    ('frt_assignment', 'FRT Assignment'),
    ('user_activation', 'User Activation'),
    ('license_verification', 'License Verification'),
    ('insurance_verification', 'Insurance Verification'),
    ('compliance_approval', 'Compliance Approval'),
    ('medical_certificate', 'Medical Certificate Approval'),
    ('vehicle_document', 'Vehicle Document Approval'),
    ('project_approval', 'Project Approval'),
    ('subzone_approval', 'SubZone Approval'),
    ('frt_activation', 'FRT Activation'),
    ('vehicle_assignment', 'Vehicle Assignment'),
    ('attendance_correction', 'Attendance Correction'),
    ('attendance_verification', 'Attendance Verification'),
    ('leave_approval', 'Leave Approval'),
    ('overtime_approval', 'Overtime Approval'),
    ('payroll_verification', 'Payroll Verification'),
    ('escalation_closure', 'Escalation Closure'),
    ('sla_override', 'SLA Override'),
    ('critical_incident', 'Critical Incident Approval'),
    ('escalation_reassignment', 'Escalation Reassignment'),
]

APPROVAL_TYPE_LABELS = {key: label for key, label in APPROVAL_TYPE_CHOICES}

DEFAULT_APPROVAL_WORKFLOW = {
    'employee_onboarding': [
        {'approval_level': 1, 'role_name': 'HR Coordinator', 'escalation_after_minutes': 240, 'auto_escalate': True},
        {'approval_level': 2, 'role_name': 'HR Manager', 'escalation_after_minutes': 480, 'auto_escalate': True},
        {'approval_level': 3, 'role_name': 'Operations Director', 'escalation_after_minutes': 720, 'auto_escalate': False},
    ],
    'driver_verification': [
        {'approval_level': 1, 'role_name': 'Safety Supervisor', 'escalation_after_minutes': 180, 'auto_escalate': True},
        {'approval_level': 2, 'role_name': 'Operations Manager', 'escalation_after_minutes': 360, 'auto_escalate': True},
    ],
    'labour_approval': [
        {'approval_level': 1, 'role_name': 'Site Supervisor', 'escalation_after_minutes': 240, 'auto_escalate': True},
        {'approval_level': 2, 'role_name': 'Project Manager', 'escalation_after_minutes': 480, 'auto_escalate': False},
    ],
    'frt_assignment': [
        {'approval_level': 1, 'role_name': 'Fleet Coordinator', 'escalation_after_minutes': 120, 'auto_escalate': True},
        {'approval_level': 2, 'role_name': 'Fleet Manager', 'escalation_after_minutes': 300, 'auto_escalate': False},
    ],
    'user_activation': [
        {'approval_level': 1, 'role_name': 'IT Support', 'escalation_after_minutes': 120, 'auto_escalate': True},
        {'approval_level': 2, 'role_name': 'Security Officer', 'escalation_after_minutes': 360, 'auto_escalate': False},
    ],
    'license_verification': [
        {'approval_level': 1, 'role_name': 'Compliance Officer', 'escalation_after_minutes': 240, 'auto_escalate': True},
        {'approval_level': 2, 'role_name': 'Operations Manager', 'escalation_after_minutes': 480, 'auto_escalate': False},
    ],
    'insurance_verification': [
        {'approval_level': 1, 'role_name': 'Insurance Coordinator', 'escalation_after_minutes': 240, 'auto_escalate': True},
        {'approval_level': 2, 'role_name': 'Risk Manager', 'escalation_after_minutes': 480, 'auto_escalate': False},
    ],
    'compliance_approval': [
        {'approval_level': 1, 'role_name': 'Compliance Officer', 'escalation_after_minutes': 180, 'auto_escalate': True},
        {'approval_level': 2, 'role_name': 'Compliance Manager', 'escalation_after_minutes': 360, 'auto_escalate': False},
    ],
    'medical_certificate': [
        {'approval_level': 1, 'role_name': 'Medical Reviewer', 'escalation_after_minutes': 240, 'auto_escalate': True},
        {'approval_level': 2, 'role_name': 'HR Manager', 'escalation_after_minutes': 480, 'auto_escalate': False},
    ],
    'vehicle_document': [
        {'approval_level': 1, 'role_name': 'Fleet Coordinator', 'escalation_after_minutes': 180, 'auto_escalate': True},
        {'approval_level': 2, 'role_name': 'Compliance Officer', 'escalation_after_minutes': 360, 'auto_escalate': False},
    ],
    'project_approval': [
        {'approval_level': 1, 'role_name': 'Project Manager', 'escalation_after_minutes': 240, 'auto_escalate': True},
        {'approval_level': 2, 'role_name': 'Business Head', 'escalation_after_minutes': 480, 'auto_escalate': False},
    ],
    'subzone_approval': [
        {'approval_level': 1, 'role_name': 'Area Supervisor', 'escalation_after_minutes': 180, 'auto_escalate': True},
        {'approval_level': 2, 'role_name': 'Project Manager', 'escalation_after_minutes': 360, 'auto_escalate': False},
    ],
    'frt_activation': [
        {'approval_level': 1, 'role_name': 'Fleet Coordinator', 'escalation_after_minutes': 120, 'auto_escalate': True},
        {'approval_level': 2, 'role_name': 'Operations Manager', 'escalation_after_minutes': 300, 'auto_escalate': False},
    ],
    'vehicle_assignment': [
        {'approval_level': 1, 'role_name': 'Dispatcher', 'escalation_after_minutes': 120, 'auto_escalate': True},
        {'approval_level': 2, 'role_name': 'Fleet Manager', 'escalation_after_minutes': 240, 'auto_escalate': False},
    ],
    'attendance_correction': [
        {'approval_level': 1, 'role_name': 'Line Supervisor', 'escalation_after_minutes': 120, 'auto_escalate': True},
        {'approval_level': 2, 'role_name': 'HR Manager', 'escalation_after_minutes': 360, 'auto_escalate': False},
    ],
    'attendance_verification': [
        {'approval_level': 1, 'role_name': 'MIS', 'escalation_after_minutes': 480, 'auto_escalate': True},
        {'approval_level': 2, 'role_name': 'Circle KAM', 'escalation_after_minutes': 480, 'auto_escalate': False},
    ],
    'leave_approval': [
        {'approval_level': 1, 'role_name': 'Supervisor', 'escalation_after_minutes': 120, 'auto_escalate': True},
        {'approval_level': 2, 'role_name': 'HR Manager', 'escalation_after_minutes': 360, 'auto_escalate': False},
    ],
    'overtime_approval': [
        {'approval_level': 1, 'role_name': 'Supervisor', 'escalation_after_minutes': 120, 'auto_escalate': True},
        {'approval_level': 2, 'role_name': 'HR Manager', 'escalation_after_minutes': 360, 'auto_escalate': False},
    ],
    'payroll_verification': [
        {'approval_level': 1, 'role_name': 'Payroll Analyst', 'escalation_after_minutes': 240, 'auto_escalate': True},
        {'approval_level': 2, 'role_name': 'Finance Manager', 'escalation_after_minutes': 480, 'auto_escalate': False},
    ],
    'escalation_closure': [
        {'approval_level': 1, 'role_name': 'Escalation Manager', 'escalation_after_minutes': 60, 'auto_escalate': False},
    ],
    'sla_override': [
        {'approval_level': 1, 'role_name': 'Service Delivery Manager', 'escalation_after_minutes': 60, 'auto_escalate': False},
    ],
    'critical_incident': [
        {'approval_level': 1, 'role_name': 'Incident Commander', 'escalation_after_minutes': 60, 'auto_escalate': True},
        {'approval_level': 2, 'role_name': 'Operations Director', 'escalation_after_minutes': 120, 'auto_escalate': False},
    ],
    'escalation_reassignment': [
        {'approval_level': 1, 'role_name': 'Escalation Manager', 'escalation_after_minutes': 60, 'auto_escalate': True},
        {'approval_level': 2, 'role_name': 'Operations Director', 'escalation_after_minutes': 120, 'auto_escalate': False},
    ],
}


def get_approval_type_label(approval_type):
    return APPROVAL_TYPE_LABELS.get(approval_type, approval_type or 'Unknown')


def get_approval_workflow_template(approval_type):
    return DEFAULT_APPROVAL_WORKFLOW.get(approval_type, [])


def get_approval_type_choices():
    return APPROVAL_TYPE_CHOICES
