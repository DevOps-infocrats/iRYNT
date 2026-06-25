from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.modules.companies.forms import CompanyForm
from app.modules.companies.services import CompanyService

companies_bp = Blueprint('companies', __name__, url_prefix='/companies')
company_service = CompanyService()

COUNTRIES = [
    {'id': 'IN', 'name': 'India'},
]
STATES = {
    'IN': [
        {'id': 'UP', 'name': 'Uttar Pradesh'},
        {'id': 'MH', 'name': 'Maharashtra'},
        {'id': 'DL', 'name': 'Delhi'},
    ]
}
CITIES = {
    'UP': [
        {'id': 'LKO', 'name': 'Lucknow'},
        {'id': 'GWL', 'name': 'Gwalior'},
        {'id': 'KAN', 'name': 'Kanpur'},
    ],
    'MH': [
        {'id': 'MUM', 'name': 'Mumbai'},
        {'id': 'PUN', 'name': 'Pune'},
        {'id': 'NAG', 'name': 'Nagpur'},
    ],
    'DL': [
        {'id': 'NDL', 'name': 'New Delhi'},
        {'id': 'DLF', 'name': 'Delhi'},
    ],
}


@companies_bp.route('/')
@login_required
def index():
    if not current_user.is_superadmin and current_user.company_id:
        companies = [c for c in company_service.list_companies() if c.id == current_user.company_id]
    else:
        companies = company_service.list_companies()
    return render_template('companies/index.html', companies=companies, active_page='companies')


@companies_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    form = CompanyForm(company_id=None)
    if form.validate_on_submit():
        payload = {
            'company_name': form.company_name.data,
            'company_code': form.company_code.data,
            'gst_number': form.gst_number.data or None,
            'pan_number': form.pan_number.data or None,
            'email': form.email.data or None,
            'phone': form.phone.data or None,
            'country_id': form.country_id.data,
            'state_id': form.state_id.data,
            'city_id': form.city_id.data,
            'pincode': form.pincode.data,
            'status': form.status.data,
            'created_by': current_user.get_id(),
        }
        company_service.create_company(payload)
        flash('Company created successfully.', 'success')
        return redirect(url_for('companies.index'))

    return render_template('companies/create.html', form=form, active_page='companies')


@companies_bp.route('/<company_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(company_id):
    company = company_service.get_company(company_id)
    if not company:
        flash('Company not found.', 'danger')
        return redirect(url_for('companies.index'))

    form = CompanyForm(company_id=company.id, obj=company)
    if form.validate_on_submit():
        payload = {
            'company_name': form.company_name.data,
            'company_code': form.company_code.data,
            'gst_number': form.gst_number.data or None,
            'pan_number': form.pan_number.data or None,
            'email': form.email.data or None,
            'phone': form.phone.data or None,
            'country_id': form.country_id.data,
            'state_id': form.state_id.data,
            'city_id': form.city_id.data,
            'pincode': form.pincode.data,
            'status': form.status.data,
        }
        company_service.update_company(company, payload)
        flash('Company updated successfully.', 'success')
        return redirect(url_for('companies.index'))

    return render_template('companies/edit.html', form=form, company=company, active_page='companies')


@companies_bp.route('/locations/countries')
@login_required
def countries():
    return jsonify(COUNTRIES)


@companies_bp.route('/locations/states')
@login_required
def states():
    country = request.args.get('country_id')
    return jsonify(STATES.get(country, []))


@companies_bp.route('/locations/cities')
@login_required
def cities():
    state = request.args.get('state_id')
    return jsonify(CITIES.get(state, []))
