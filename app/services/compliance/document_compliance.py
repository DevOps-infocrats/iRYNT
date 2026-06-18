from collections import defaultdict
from datetime import date, timedelta


DRIVER_REQUIRED_DOCUMENTS = [
    'Driving License',
    'Aadhaar',
    'PAN',
    'Address Proof',
]

DRIVER_OPTIONAL_DOCUMENTS = [
    'Medical Certificate',
    'Police Verification',
    'Training Certificate',
]

VEHICLE_DOCUMENTS = [
    'RC',
    'Insurance',
    'Fitness Certificate',
    'PUC Certificate',
    'Permit',
    'Tax Receipt',
]


def normalize_status(status):
    return (status or '').strip().lower()


def expiry_state(expiry_date, today=None):
    if not expiry_date:
        return {'label': 'No expiry', 'severity': 'muted', 'days': None}
    today = today or date.today()
    days = (expiry_date - today).days
    if days < 0:
        return {'label': 'Expired', 'severity': 'danger', 'days': days}
    if days <= 7:
        return {'label': 'Expiring in 7 days', 'severity': 'danger', 'days': days}
    if days <= 30:
        return {'label': 'Expiring in 30 days', 'severity': 'warning', 'days': days}
    return {'label': 'Valid', 'severity': 'success', 'days': days}


def document_verification_status(document):
    if not document:
        return 'Pending'
    status = normalize_status(getattr(document, 'status', None))
    if status == 'verified':
        return 'Verified'
    if status == 'rejected':
        return 'Rejected'
    if status in {'re-upload requested', 'request re-upload'}:
        return 'Pending'
    return 'Pending'


def document_compliance_status(document, required=True):
    if not document:
        return 'Incomplete' if required else 'Pending'
    verification = document_verification_status(document)
    if verification == 'Rejected':
        return 'Rejected'
    expiry = expiry_state(getattr(document, 'expiry_date', None))
    if expiry['label'] == 'Expired':
        return 'Expired'
    if verification == 'Verified':
        return 'Verified'
    return 'Pending'


def group_latest_documents(documents):
    grouped = {}
    for document in documents or []:
        doc_type = getattr(document, 'document_type', None)
        if not doc_type:
            continue
        current = grouped.get(doc_type)
        if not current or getattr(document, 'uploaded_at', None) > getattr(current, 'uploaded_at', None):
            grouped[doc_type] = document
    return grouped


def build_driver_compliance(driver_profile, documents=None, latest_license=None):
    documents = documents if documents is not None else list(driver_profile.documents.all() if driver_profile else [])
    latest_by_type = group_latest_documents(documents)
    cards = []
    alerts = defaultdict(int)

    for doc_type in DRIVER_REQUIRED_DOCUMENTS + DRIVER_OPTIONAL_DOCUMENTS:
        required = doc_type in DRIVER_REQUIRED_DOCUMENTS
        document = latest_by_type.get(doc_type)
        if doc_type == 'Driving License' and latest_license and not document:
            class LicenseDocumentAdapter:
                status = getattr(latest_license, 'verification_status', 'Pending')
                expiry_date = getattr(latest_license, 'expiry_date', None)
                document_type = 'Driving License'
                file_name = None
                uploaded_at = getattr(latest_license, 'updated_at', None)
                id = None

            document = LicenseDocumentAdapter()

        expiry = expiry_state(getattr(document, 'expiry_date', None) if document else None)
        status = document_compliance_status(document, required=required)
        if status == 'Expired':
            alerts['expired'] += 1
        elif expiry['label'] == 'Expiring in 7 days':
            alerts['expiring_7'] += 1
        elif expiry['label'] == 'Expiring in 30 days':
            alerts['expiring_30'] += 1
        if document_verification_status(document) == 'Rejected':
            alerts['rejected'] += 1
        elif document_verification_status(document) == 'Pending' and document:
            alerts['pending'] += 1

        cards.append({
            'type': doc_type,
            'required': required,
            'document': document,
            'uploaded': bool(document and getattr(document, 'file_name', None)),
            'status': status,
            'verification_status': document_verification_status(document),
            'expiry': getattr(document, 'expiry_date', None) if document else None,
            'expiry_state': expiry,
        })

    required_cards = [card for card in cards if card['required']]
    if any(card['type'] == 'Driving License' and card['status'] == 'Expired' for card in cards):
        compliance_status = 'Incomplete'
        deployment_eligibility = 'Blocked'
    elif any(card['status'] in {'Expired', 'Incomplete', 'Rejected'} for card in required_cards):
        compliance_status = 'Incomplete'
        deployment_eligibility = 'Flagged'
    elif any(card['status'] == 'Pending' for card in required_cards):
        compliance_status = 'Pending'
        deployment_eligibility = 'Pending Verification'
    else:
        compliance_status = 'Verified'
        deployment_eligibility = 'Eligible'

    return {
        'cards': cards,
        'alerts': dict(alerts),
        'compliance_status': compliance_status,
        'deployment_eligibility': deployment_eligibility,
    }


def vehicle_status_card(label, status=None):
    normalized = normalize_status(status)
    if normalized in {'expired', 'invalid', 'rejected'}:
        compliance = 'Expired'
        severity = 'danger'
    elif normalized in {'pending', 'verification pending'}:
        compliance = 'Verification Pending'
        severity = 'warning'
    elif normalized in {'expiring soon'}:
        compliance = 'Expiring Soon'
        severity = 'warning'
    elif normalized in {'valid', 'verified', 'compliant'}:
        compliance = 'Compliant'
        severity = 'success'
    else:
        compliance = 'Verification Pending'
        severity = 'warning'
    return {
        'type': label,
        'status': compliance,
        'verification_status': status or 'Pending',
        'expiry': None,
        'expiry_state': {'label': 'Tracked in vehicle record', 'severity': severity, 'days': None},
    }


def check_document_expiry_status(expiry_date, current_status):
    if not expiry_date:
        return current_status or 'Pending'
    try:
        from app.modules.attendance.utils import get_india_today
        today = get_india_today()
    except Exception:
        today = date.today()
    
    if expiry_date < today:
        return 'Expired'
    elif expiry_date <= today + timedelta(days=30):
        return 'Expiring Soon'
    else:
        return 'Valid'


def build_vehicle_compliance(vehicle):
    insurance_status = check_document_expiry_status(getattr(vehicle, 'insurance_expiry', None), getattr(vehicle, 'insurance_status', None))
    fitness_status = check_document_expiry_status(getattr(vehicle, 'fitness_expiry', None), getattr(vehicle, 'fitness_status', None))
    permit_status = check_document_expiry_status(getattr(vehicle, 'permit_expiry', None), getattr(vehicle, 'permit_status', None))
    puc_status = check_document_expiry_status(getattr(vehicle, 'puc_expiry', None), getattr(vehicle, 'puc_status', None))
    verification_status = getattr(vehicle, 'verification_status', None) or 'Pending'

    status_map = {
        'RC': verification_status,
        'Insurance': insurance_status,
        'Fitness Certificate': fitness_status,
        'PUC Certificate': puc_status,
        'Permit': permit_status,
        'Tax Receipt': verification_status,
    }
    cards = [vehicle_status_card(label, status_map.get(label)) for label in VEHICLE_DOCUMENTS]
    insurance_bad = cards[1]['status'] in {'Expired', 'Verification Pending'}
    fitness_bad = cards[2]['status'] in {'Expired', 'Verification Pending'}
    if insurance_bad or fitness_bad:
        vehicle_compliance = 'Flagged'
    elif any(card['status'] == 'Expiring Soon' for card in cards):
        vehicle_compliance = 'Expiring Soon'
    elif any(card['status'] == 'Verification Pending' for card in cards):
        vehicle_compliance = 'Verification Pending'
    else:
        vehicle_compliance = 'Compliant'

    return {
        'cards': cards,
        'vehicle_compliance': vehicle_compliance,
        'alerts': {
            'expired': sum(1 for card in cards if card['status'] == 'Expired'),
            'pending': sum(1 for card in cards if card['status'] == 'Verification Pending'),
            'flagged': 1 if vehicle_compliance == 'Flagged' else 0,
        },
    }

