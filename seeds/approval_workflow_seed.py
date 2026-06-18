"""
Approval Workflow Seed

Idempotent seeding of approval workflows by mapping default workflow role names
to existing seeded role templates. Creates or updates `approval_workflows` rows
from `app.modules.approvals.approval_types.DEFAULT_APPROVAL_WORKFLOW`.
"""
from typing import Dict

from app.extensions import db


def _normalize_role_lookup(role_name: str, Role):
    """Try to resolve an approval role_name to an existing Role record.

    Strategy:
    - Exact case-insensitive match
    - Normalization map (common synonyms → seeded role names)
    - Fallback fuzzy contains match on keyword tokens
    """
    if not role_name:
        return None
    name = role_name.strip()
    # exact case-insensitive
    role = Role.query.filter(db.func.lower(Role.name) == name.lower()).first()
    if role:
        return role

    # normalization map for common business role synonyms
    NORMALIZATION_MAP = {
        'business head': 'CBH',
        'operations director': 'Director',
        'project manager': 'PMO',
        'hr manager': 'PMO',
        'hr coordinator': 'Helper',
        'insurance coordinator': 'Corporate Admin',
        'safety supervisor': 'CBH',
        'operations manager': 'Corporate Admin',
        'fleet coordinator': 'Circle Admin',
        'fleet manager': 'Circle Admin',
        'it support': 'MIS',
        'security officer': 'Circle Admin',
        'compliance officer': 'Circle Admin',
        'compliance manager': 'Director',
        'medical reviewer': 'MIS',
        'dispatcher': 'CBH',
        'line supervisor': 'CBH',
        'supervisor': 'CBH',
        'payroll analyst': 'PMO',
        'finance manager': 'Corporate Admin',
        'escalation manager': 'Director',
        'service delivery manager': 'Director',
        'incident commander': 'Director',
        'risk manager': 'Director',
        'site supervisor': 'CBH',
        'area supervisor': 'CBH',
    }

    mapped = NORMALIZATION_MAP.get(name.lower())
    if mapped:
        role = Role.query.filter(db.func.lower(Role.name) == mapped.lower()).first()
        if role:
            return role

    # fuzzy token contains search (try tokens in descending length order)
    tokens = sorted([t for t in name.lower().split() if t], key=lambda x: -len(x))
    for token in tokens:
        candidate = Role.query.filter(Role.name.ilike(f"%{token}%")).first()
        if candidate:
            return candidate

    return None


def seed_approval_workflows() -> Dict[str, int]:
    """Seed ApprovalWorkflow rows from default templates.

    Returns summary dict with counts.
    """
    print('\n' + '=' * 60)
    print('SEEDING DEFAULT APPROVAL WORKFLOWS (mapping templates)')
    print('=' * 60)

    try:
        from app.modules.approvals.approval_types import DEFAULT_APPROVAL_WORKFLOW
        from app.modules.approvals.models import ApprovalWorkflow
        from app.modules.auth.models import Role
    except Exception as e:
        print(f"Error importing approvals or role models: {e}")
        return {'created': 0, 'updated': 0, 'skipped': 0}

    created = 0
    updated = 0
    skipped = 0

    for approval_type, levels in DEFAULT_APPROVAL_WORKFLOW.items():
        for lvl in levels:
            approval_level = int(lvl.get('approval_level', 0))
            role_name = lvl.get('role_name')
            escalation_after = int(lvl.get('escalation_after_minutes', 1440))
            auto_escalate = bool(lvl.get('auto_escalate', False))

            # find matching role
            role = _normalize_role_lookup(role_name, Role)

            existing = ApprovalWorkflow.query.filter_by(approval_type=approval_type, approval_level=approval_level).first()

            if existing:
                # update fields (idempotent)
                if role:
                    existing.role_id = role.id
                existing.escalation_after_minutes = escalation_after
                existing.auto_escalate = auto_escalate
                existing.active = True
                updated += 1
            else:
                if not role:
                    print(f"Skipping workflow {approval_type} L{approval_level}: role '{role_name}' not found/mapped")
                    skipped += 1
                    continue

                new = ApprovalWorkflow(
                    approval_type=approval_type,
                    approval_level=approval_level,
                    role_id=role.id,
                    escalation_after_minutes=escalation_after,
                    auto_escalate=auto_escalate,
                    active=True,
                )
                db.session.add(new)
                created += 1

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Error committing approval workflow seeds: {e}")

    print('\nSeeding Summary:')
    print(f'  Created: {created}')
    print(f'  Updated: {updated}')
    print(f'  Skipped (no matching role): {skipped}')
    print('=' * 60 + '\n')

    return {'created': created, 'updated': updated, 'skipped': skipped}


if __name__ == '__main__':
    # Allow running the seed standalone
    from app import create_app

    app = create_app()
    with app.app_context():
        seed_approval_workflows()
