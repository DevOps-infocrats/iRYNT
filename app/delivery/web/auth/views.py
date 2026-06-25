from flask import abort, render_template, request
from flask_login import current_user
from app.services.dashboard_analytics import DashboardAnalyticsService
from app.domain.auth.policies.auth_policy import has_role
from app.modules.drivers.models import DriverProfile


_dashboard_service = DashboardAnalyticsService()


def render_login(form, next_url=None):
    return render_template('login.html', form=form, next_url=next_url)


def render_forgot_password(form):
    return render_template('forgot_password.html', form=form)


def render_reset_password(form, token=None):
    return render_template('reset_password.html', form=form, token=token)


def render_dashboard():
    # Block Driver and Helper roles from viewing the dashboard
    is_field = has_role('Driver') or has_role('Helper')
    is_admin = has_role('Super Admin') or has_role('Admin')
    if is_field and not is_admin:
        abort(403)

    # provide dynamic KPI metrics and dashboard payload for the dashboard
    filters = {}
    if not current_user.is_superadmin:
        if current_user.circle_id:
            filters['circle_id'] = current_user.circle_id
        elif current_user.company_id:
            filters['company_id'] = current_user.company_id
    
    kpis = _dashboard_service.get_kpis(filters)
    dashboard_payload = _dashboard_service.get_dashboard_payload(filters)
    pending_approvals = next((k['value'] for k in kpis if k['title'] == 'Pending Approvals'), None)
    compliance_counters = _dashboard_service.get_compliance_counters(filters)
    return render_template(
        'dashboard.html',
        active_page='dashboard',
        kpis=kpis,
        pending_approvals=pending_approvals,
        dashboard_payload=dashboard_payload,
        compliance_counters=compliance_counters,
    )
