from dataclasses import dataclass

VEHICLE_TYPES = [
    ('', 'Select vehicle type'),
    ('Bike', 'Bike'),
    ('Scooter', 'Scooter'),
    ('Car', 'Car'),
    ('Van', 'Van'),
    ('Truck', 'Truck'),
    ('Mini Truck', 'Mini Truck'),
    ('Bus', 'Bus'),
    ('EV Vehicle', 'EV Vehicle'),
]

VEHICLE_CATEGORIES = [
    ('', 'Select vehicle category'),
    ('Owned', 'Owned'),
    ('Vendor', 'Vendor'),
    ('Rental', 'Rental'),
    ('Contract', 'Contract'),
    ('Leased', 'Leased'),
]

VEHICLE_STATUS_CHOICES = [
    ('Available', 'Available'),
    ('Deployed', 'Deployed'),
    ('Maintenance', 'Maintenance'),
    ('Inactive', 'Inactive'),
    ('Blocked', 'Blocked'),
    ('Expired', 'Expired'),
    ('Under Verification', 'Under Verification'),
]

COMPLIANCE_STATUS_CHOICES = [
    ('Valid', 'Valid'),
    ('Expiring Soon', 'Expiring Soon'),
    ('Expired', 'Expired'),
    ('Not Submitted', 'Not Submitted'),
]

@dataclass
class ComplianceSnapshot:
    label: str
    status: str


def compliance_color(status: str) -> str:
    status_lower = status.lower() if status else ''
    if status_lower == 'valid':
        return 'success'
    if status_lower == 'expiring soon':
        return 'warning'
    if status_lower == 'expired':
        return 'danger'
    return 'secondary'

