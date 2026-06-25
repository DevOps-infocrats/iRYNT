from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.modules.circles.forms import CircleForm
from app.modules.circles.services import CircleService
from app.modules.companies.models import Company

circles_bp = Blueprint('circles', __name__, url_prefix='/circles')
circle_service = CircleService()


@circles_bp.route('/')
@login_required
def index():
    circles = circle_service.list_circles()
    if not current_user.is_superadmin:
        if current_user.circle_id:
            circles = [c for c in circles if c.id == current_user.circle_id]
        elif current_user.company_id:
            circles = [c for c in circles if c.company_id == current_user.company_id]
    # build a small company map to show names in the list
    company_ids = list({c.company_id for c in circles if c.company_id})
    companies = Company.query.filter(Company.id.in_(company_ids)).all() if company_ids else []
    company_map = {c.id: c.company_name for c in companies}
    return render_template('circles/index.html', circles=circles, company_map=company_map, active_page='circles')


@circles_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    form = CircleForm(company_id=None)
    if form.validate_on_submit():
        payload = {
            'company_id': form.company_id.data,
            'circle_code': form.circle_code.data,
            'circle_name': form.circle_name.data,
            'regional_manager': form.regional_manager.data or None,
            'email': form.email.data or None,
            'phone': form.phone.data or None,
            'address': form.address.data or None,
            'status': form.status.data,
            'created_by': current_user.get_id(),
        }
        circle_service.create_circle(payload)
        flash('Circle created successfully.', 'success')
        return redirect(url_for('circles.index'))

    return render_template('circles/create.html', form=form, active_page='circles')


@circles_bp.route('/companies/search')
@login_required
def companies_search():
    q = request.args.get('q', '').strip()
    query = Company.query.filter(Company.status == 'Active')
    if q:
        like = f"%{q}%"
        query = query.filter((Company.company_name.ilike(like)) | (Company.company_code.ilike(like)))
    companies = query.order_by(Company.company_name).limit(20).all()
    data = [{'id': c.id, 'text': f"{c.company_name} ({c.company_code})", 'company_name': c.company_name, 'company_code': c.company_code, 'location': '', 'status': c.status} for c in companies]
    return jsonify(items=data)


@circles_bp.route('/check_code')
@login_required
def check_code():
    company_id = request.args.get('company_id')
    code = (request.args.get('code') or '').strip().upper()
    repo = circle_service.repository
    exists = repo.exists_by_field('circle_code', code, company_id=company_id)
    return jsonify({'exists': exists})
# auto-generated placeholder
