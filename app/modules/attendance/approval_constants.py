APPROVAL_STATUS_SUBMITTED = 'SUBMITTED'
APPROVAL_STATUS_MIS_APPROVED = 'MIS_APPROVED'
APPROVAL_STATUS_KAM_APPROVED = 'KAM_APPROVED'
APPROVAL_STATUS_REJECTED = 'REJECTED'

APPROVAL_STATUS_LABELS = {
    APPROVAL_STATUS_SUBMITTED: 'Submitted — Waiting for Circle MIS Approval',
    APPROVAL_STATUS_MIS_APPROVED: 'MIS Approved — Waiting for Circle KAM Approval',
    APPROVAL_STATUS_KAM_APPROVED: 'Attendance Approved Successfully',
    APPROVAL_STATUS_REJECTED: 'Rejected',
}


def approval_status_label(status):
    if not status:
        return None
    return APPROVAL_STATUS_LABELS.get(status, status)
