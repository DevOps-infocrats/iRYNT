"""
Approval Routes

Flask Blueprint for approval workflow management.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import current_user, login_required

from app.core.decorators import permission_required
from app.modules.approvals.services import ApprovalService

approval_bp = Blueprint('approvals', __name__, url_prefix='/pending-approvals')
approval_service = ApprovalService()


@approval_bp.route('/')
@login_required
@permission_required('workflows.view')
def index():
    """Approval dashboard - main page"""
    page = request.args.get('page', 1, type=int)
    approval_status = request.args.get('approval_status', '', type=str)
    approval_type = request.args.get('approval_type', '', type=str)
    priority = request.args.get('priority', '', type=str)
    company_id = request.args.get('company_id', '', type=str)
    search_query = request.args.get('q', '', type=str)
    category = request.args.get('category', 'all', type=str)
    assigned_approver_id = request.args.get('assigned_approver_id', '', type=str)

    filters = {
        'approval_status': approval_status if approval_status else None,
        'approval_type': approval_type if approval_type else None,
        'priority': priority if priority else None,
        'company_id': company_id if company_id else None,
        'search_query': search_query if search_query else None,
        'assigned_approver_id': assigned_approver_id if assigned_approver_id else None,
    }

    # Apply category translation
    if category == 'documents':
        filters['approval_types'] = ['license_verification', 'insurance_verification', 'compliance_approval', 'medical_certificate', 'vehicle_document']
    elif category == 'attendance':
        filters['approval_types'] = ['attendance_correction', 'leave_approval', 'overtime_approval']
    elif category == 'compliance':
        filters['approval_types'] = ['driver_verification', 'license_verification', 'compliance_approval', 'medical_certificate', 'vehicle_document', 'insurance_verification']
    elif category == 'deployments':
        filters['approval_types'] = ['frt_assignment', 'vehicle_assignment', 'frt_activation']
    elif category == 'escalations':
        filters['approval_types'] = ['escalation_closure', 'sla_override', 'critical_incident', 'escalation_reassignment']
    elif category == 'payroll':
        filters['approval_types'] = ['payroll_verification']
    elif category == 'critical':
        filters['priority'] = 'Critical'
    elif category == 'overdue':
        filters['is_overdue'] = True

    approvals, total = approval_service.list_approvals(
        filters=filters,
        offset=(page - 1) * 20,
        limit=20,
        user=current_user
    )

    metrics = approval_service.get_dashboard_metrics(
        user=current_user,
        company_id=company_id if company_id else None
    )

    return render_template(
        'approvals/index.html',
        approvals=approvals,
        total=total,
        page=page,
        metrics=metrics,
        filters=filters,
        category=category,
        active_page='approvals'
    )


@approval_bp.route('/view/<approval_id>')
@login_required
@permission_required('workflows.view')
def view(approval_id):
    """View approval details"""
    approval = approval_service.get_approval(approval_id)
    if not approval:
        flash('Approval not found.', 'danger')
        return redirect(url_for('approvals.index'))

    history = approval_service.get_approval_history(approval_id)
    comments = approval_service.get_approval_comments(approval_id)

    return render_template(
        'approvals/view.html',
        approval=approval,
        history=history,
        comments=comments,
        active_page='approvals'
    )


@approval_bp.route('/approve/<approval_id>', methods=['POST'])
@login_required
@permission_required('workflows.approve')
def approve(approval_id):
    """Approve request"""
    remarks = request.form.get('remarks', '')
    next_url = request.form.get('next') or request.args.get('next')
    
    approval, error = approval_service.approve_approval(
        approval_id,
        current_user.id,
        remarks
    )

    if error:
        flash(f'Error: {error}', 'danger')
    else:
        flash('Approval completed successfully.', 'success')

    return redirect(next_url or url_for('approvals.view', approval_id=approval_id))


@approval_bp.route('/reject/<approval_id>', methods=['POST'])
@login_required
@permission_required('workflows.approve')
def reject(approval_id):
    """Reject request"""
    remarks = request.form.get('remarks', '')
    next_url = request.form.get('next') or request.args.get('next')
    
    approval, error = approval_service.reject_approval(
        approval_id,
        current_user.id,
        remarks
    )

    if error:
        flash(f'Error: {error}', 'danger')
    else:
        flash('Approval rejected successfully.', 'warning')

    return redirect(next_url or url_for('approvals.view', approval_id=approval_id))


@approval_bp.route('/escalate/<approval_id>', methods=['POST'])
@login_required
@permission_required('workflows.approve')
def escalate(approval_id):
    """Escalate request"""
    remarks = request.form.get('remarks', '')
    next_url = request.form.get('next') or request.args.get('next')
    
    approval, error = approval_service.escalate_approval(
        approval_id,
        current_user.id,
        remarks
    )

    if error:
        flash(f'Error: {error}', 'danger')
    else:
        flash('Approval escalated successfully.', 'info')

    return redirect(next_url or url_for('approvals.view', approval_id=approval_id))


@approval_bp.route('/comment/<approval_id>', methods=['POST'])
@login_required
@permission_required('workflows.view')
def add_comment(approval_id):
    """Add comment to approval"""
    comment_text = request.form.get('comment', '').strip()
    next_url = request.form.get('next') or request.args.get('next')
    
    if not comment_text:
        flash('Comment cannot be empty.', 'warning')
    else:
        approval_service.add_comment(approval_id, current_user.id, comment_text)
        flash('Comment added successfully.', 'success')

    return redirect(next_url or url_for('approvals.view', approval_id=approval_id))


@approval_bp.route('/bulk-approve', methods=['POST'])
@login_required
@permission_required('workflows.approve')
def bulk_approve():
    """Bulk approve approvals"""
    approval_ids = request.form.getlist('approval_ids[]')
    remarks = request.form.get('remarks', '')

    if not approval_ids:
        flash('No approvals selected.', 'warning')
    else:
        results = approval_service.bulk_approve(approval_ids, current_user.id, remarks)
        flash(f'Bulk approved {len([r for r in results if not r[1]])} approvals.', 'success')

    return redirect(url_for('approvals.index'))


@approval_bp.route('/bulk-reject', methods=['POST'])
@login_required
@permission_required('workflows.approve')
def bulk_reject():
    """Bulk reject approvals"""
    approval_ids = request.form.getlist('approval_ids[]')
    remarks = request.form.get('remarks', '')

    if not approval_ids:
        flash('No approvals selected.', 'warning')
    else:
        results = approval_service.bulk_reject(approval_ids, current_user.id, remarks)
        flash(f'Bulk rejected {len([r for r in results if not r[1]])} approvals.', 'success')

    return redirect(url_for('approvals.index'))


@approval_bp.route('/analytics')
@login_required
@permission_required('workflows.view')
def analytics():
    """Approval analytics dashboard"""
    company_id = request.args.get('company_id', '', type=str)

    metrics = approval_service.get_dashboard_metrics(
        user_id=current_user.id,
        company_id=company_id if company_id else None
    )

    # Get escalated and breached approvals
    escalated, _ = approval_service.list_approvals(
        filters={'approval_status': 'Escalated'},
        limit=5
    )
    breached = approval_service.get_sla_breached_approvals()[:5]

    return render_template(
        'approvals/analytics.html',
        metrics=metrics,
        escalated_approvals=escalated,
        breached_approvals=breached,
        active_page='approvals_analytics'
    )


# ============================================================================
# AJAX Endpoints
# ============================================================================

@approval_bp.route('/ajax/stats', methods=['GET'])
@login_required
def ajax_stats():
    """Get approval statistics (AJAX)"""
    company_id = request.args.get('company_id', '', type=str)
    
    metrics = approval_service.get_dashboard_metrics(
        user=current_user,
        company_id=company_id if company_id else None
    )
    return jsonify(metrics)


@approval_bp.route('/ajax/pending', methods=['GET'])
@login_required
def ajax_pending():
    """Get pending approvals (AJAX)"""
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 10, type=int)

    approvals, total = approval_service.get_approvals_for_approver(
        current_user.id,
        offset=(page - 1) * limit,
        limit=limit
    )

    return jsonify({
        'approvals': [a.to_dict() for a in approvals],
        'total': total,
        'page': page,
        'pages': (total + limit - 1) // limit,
    })


@approval_bp.route('/ajax/search', methods=['GET'])
@login_required
def ajax_search():
    """Search approvals (AJAX)"""
    search_query = request.args.get('q', '', type=str)
    approval_type = request.args.get('approval_type', '', type=str)

    filters = {
        'search_query': search_query if search_query else None,
        'approval_type': approval_type if approval_type else None,
    }

    approvals, total = approval_service.list_approvals(
        filters=filters,
        limit=10,
        user=current_user
    )

    return jsonify({
        'approvals': [a.to_dict() for a in approvals],
        'total': total,
    })


@approval_bp.route('/ajax/detail/<approval_id>', methods=['GET'])
@login_required
@permission_required('workflows.view')
def ajax_detail(approval_id):
    """Get approval details (AJAX JSON)"""
    approval = approval_service.get_approval(approval_id)
    if not approval:
        return jsonify({'error': 'Approval not found'}), 404

    # Role-based visibility enforcement for single approval
    is_allowed = False
    if current_user.is_superadmin:
        is_allowed = True
    elif 'driver' in current_user.role_names or 'helper' in current_user.role_names:
        is_allowed = (approval.requested_by_id == current_user.id)
    elif 'circle kam' in current_user.role_names or 'circle admin' in current_user.role_names:
        allowed_types = [
            'attendance_correction', 'leave_approval', 'overtime_approval', 'payroll_verification',
            'driver_verification', 'license_verification', 'compliance_approval', 'medical_certificate',
            'vehicle_document', 'insurance_verification', 'vehicle_assignment',
            'escalation_closure', 'sla_override', 'critical_incident', 'escalation_reassignment'
        ]
        is_allowed = (approval.circle_id == current_user.circle_id and approval.approval_type in allowed_types)
    elif 'pmo' in current_user.role_names:
        allowed_types = ['project_approval', 'subzone_approval', 'sla_override']
        is_allowed = (approval.approval_type in allowed_types)
    elif any(r in current_user.role_names for r in ['corporate admin', 'corporate kam', 'cbh', 'key account manager', 'corporate customer']):
        if current_user.company_id:
            is_allowed = (approval.company_id == current_user.company_id)
        else:
            is_allowed = True
    else:
        is_allowed = (approval.assigned_approver_id == current_user.id or approval.requested_by_id == current_user.id)

    if not is_allowed:
        return jsonify({'error': 'Unauthorized'}), 403

    history = approval_service.get_approval_history(approval_id)
    comments = approval_service.get_approval_comments(approval_id)

    # Fetch potential assignees
    from app.modules.auth.models import User
    assignees_query = User.query.filter(User.is_active == True)
    if current_user.company_id:
        assignees_query = assignees_query.filter(User.company_id == current_user.company_id)
    if current_user.circle_id:
        assignees_query = assignees_query.filter(User.circle_id == current_user.circle_id)
    assignees = assignees_query.limit(20).all()

    # Workflow level tracing
    from app.modules.approvals.approval_types import get_approval_workflow_template
    workflow_template = get_approval_workflow_template(approval.approval_type)
    
    levels_to_use = workflow_template or [
        {'approval_level': 1, 'role_name': 'Supervisor'},
        {'approval_level': 2, 'role_name': 'Manager'},
        {'approval_level': 3, 'role_name': 'Director'}
    ]
    
    approved_levels = [h.action_taken for h in history if h.action_taken == 'APPROVED']
    completed_count = len(approved_levels)
    levels_trace = []
    
    for idx, lvl in enumerate(levels_to_use):
        lvl_num = lvl.get('approval_level', idx + 1)
        role_name = lvl.get('role_name', 'Approver')
        if approval.approval_status == 'Approved':
            status = 'Completed'
        elif approval.approval_status == 'Rejected' and idx == completed_count:
            status = 'Rejected'
        elif idx < completed_count:
            status = 'Completed'
        elif idx == completed_count:
            status = 'Pending'
        else:
            status = 'Waiting'
            
        levels_trace.append({
            'level': lvl_num,
            'role_name': role_name,
            'status': status
        })

    return jsonify({
        'approval': approval.to_dict(),
        'history': [{
            'id': h.id,
            'action_taken': h.action_taken,
            'action_by': h.action_by.username if h.action_by else 'System',
            'action_time': h.action_time.strftime('%Y-%m-%d %H:%M:%S'),
            'previous_status': h.previous_status,
            'new_status': h.new_status,
            'remarks': h.remarks
        } for h in history],
        'comments': [{
            'id': c.id,
            'user': c.user.username if c.user else 'Unknown',
            'comment': c.comment,
            'created_at': c.created_at.strftime('%Y-%m-%d %H:%M:%S')
        } for c in comments],
        'assignees': [{'id': u.id, 'username': u.username} for u in assignees],
        'levels_trace': levels_trace,
        'current_user_id': current_user.id
    })


@approval_bp.route('/reassign/<approval_id>', methods=['POST'])
@login_required
@permission_required('workflows.approve')
def reassign(approval_id):
    """Reassign approval request to another user"""
    approver_id = request.form.get('approver_id')
    next_url = request.form.get('next') or request.args.get('next')
    
    if not approver_id:
        flash('No approver selected.', 'warning')
        return redirect(next_url or url_for('approvals.index'))

    approval, error = approval_service.assign_approver(
        approval_id,
        approver_id,
        current_user.id
    )

    if error:
        flash(f'Error reassigning: {error}', 'danger')
    else:
        flash('Approval reassigned successfully.', 'success')

    return redirect(next_url or url_for('approvals.index'))
