from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.modules.clients.forms import ClientForm
from app.modules.clients.services import ClientService
from app.modules.clients.repository import ClientRepository
from app.modules.companies.models import Company
from app.modules.circles.models import Circle

clients_bp = Blueprint('clients', __name__, url_prefix='/clients')
client_service = ClientService()


@clients_bp.route('/')
@login_required
def index():
    clients = client_service.list_clients()
    company_ids = list({client.company_id for client in clients if client.company_id})
    circle_ids = list({client.circle_id for client in clients if client.circle_id})
    companies = Company.query.filter(Company.id.in_(company_ids)).all() if company_ids else []
    circles = Circle.query.filter(Circle.id.in_(circle_ids)).all() if circle_ids else []

    company_map = {company.id: company.company_name for company in companies}
    circle_map = {circle.id: circle.circle_name for circle in circles}
    total_clients = len(clients)
    active_clients = sum(1 for client in clients if client.status == 'Active')
    inactive_clients = total_clients - active_clients
    company_count = len(set(company_ids))

    return render_template(
        'clients/index.html',
        clients=clients,
        company_map=company_map,
        circle_map=circle_map,
        total_clients=total_clients,
        active_clients=active_clients,
        inactive_clients=inactive_clients,
        company_count=company_count,
        active_page='clients',
    )


@clients_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    companies = Company.query.filter(Company.status == 'Active').order_by(Company.company_name).all()
    if request.method == 'GET':
        company_id = request.args.get('company_id')
        circles = Circle.query.filter(Circle.company_id == company_id, Circle.status == 'Active').order_by(Circle.circle_name).all() if company_id else []
        form = ClientForm(companies=companies, circles=circles, company_id=company_id)
    else:
        form = ClientForm(companies=companies)
        company_id = form.company_id.data
        circles = Circle.query.filter(Circle.company_id == company_id, Circle.status == 'Active').order_by(Circle.circle_name).all() if company_id else []
        form.circle_id.choices = [('', 'Select circle')] + [
            (circle.id, f"{circle.circle_name} ({circle.circle_code})") for circle in circles
        ]
    selected_company = Company.query.get(company_id) if company_id else None
    selected_circle = Circle.query.get(form.circle_id.data) if form.circle_id.data else None

    if form.validate_on_submit():
        payload = {
            'company_id': form.company_id.data,
            'circle_id': form.circle_id.data,
            'client_code': form.client_code.data,
            'client_name': form.client_name.data,
            'primary_contact': form.primary_contact.data or None,
            'email': form.email.data or None,
            'phone': form.phone.data or None,
            'address': form.address.data or None,
            'status': form.status.data,
            'created_by': current_user.get_id(),
        }
        client_service.create_client(payload)
        flash('Client created successfully.', 'success')
        return redirect(url_for('clients.index'))

    if request.method == 'POST':
        selected_company = Company.query.get(form.company_id.data) if form.company_id.data else None
        selected_circle = Circle.query.get(form.circle_id.data) if form.circle_id.data else None

    return render_template(
        'clients/create.html',
        form=form,
        selected_company=selected_company,
        selected_circle=selected_circle,
        active_page='clients',
    )


@clients_bp.route('/<client_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(client_id):
    client = client_service.get_client(client_id)
    if not client:
        flash('Client not found.', 'danger')
        return redirect(url_for('clients.index'))

    companies = Company.query.filter(Company.status == 'Active').order_by(Company.company_name).all()
    if request.method == 'GET':
        circles = Circle.query.filter(Circle.company_id == client.company_id, Circle.status == 'Active').order_by(Circle.circle_name).all()
        form = ClientForm(companies=companies, circles=circles, company_id=client.company_id, circle_id=client.circle_id, client_id=client.id, obj=client)
        selected_company = Company.query.get(client.company_id)
        selected_circle = Circle.query.get(client.circle_id)
    else:
        form = ClientForm(companies=companies, client_id=client.id)
        company_id = form.company_id.data
        circles = Circle.query.filter(Circle.company_id == company_id, Circle.status == 'Active').order_by(Circle.circle_name).all() if company_id else []
        form.circle_id.choices = [('', 'Select circle')] + [
            (circle.id, f"{circle.circle_name} ({circle.circle_code})") for circle in circles
        ]
        selected_company = Company.query.get(company_id) if company_id else None
        selected_circle = Circle.query.get(form.circle_id.data) if form.circle_id.data else None

    if form.validate_on_submit():
        payload = {
            'company_id': form.company_id.data,
            'circle_id': form.circle_id.data,
            'client_code': form.client_code.data,
            'client_name': form.client_name.data,
            'primary_contact': form.primary_contact.data or None,
            'email': form.email.data or None,
            'phone': form.phone.data or None,
            'address': form.address.data or None,
            'status': form.status.data,
        }
        client_service.update_client(client, payload)
        flash('Client updated successfully.', 'success')
        return redirect(url_for('clients.index'))

    if request.method == 'POST':
        selected_company = Company.query.get(form.company_id.data) if form.company_id.data else selected_company
        selected_circle = Circle.query.get(form.circle_id.data) if form.circle_id.data else selected_circle

    return render_template(
        'clients/edit.html',
        form=form,
        selected_company=selected_company,
        selected_circle=selected_circle,
        client=client,
        active_page='clients',
    )


@clients_bp.route('/<client_id>')
@login_required
def details(client_id):
    client = client_service.get_client(client_id)
    if not client:
        flash('Client not found.', 'danger')
        return redirect(url_for('clients.index'))

    company = Company.query.get(client.company_id)
    circle = Circle.query.get(client.circle_id)
    return render_template('clients/details.html', client=client, company=company, circle=circle, active_page='clients')


@clients_bp.route('/companies/search')
@login_required
def companies_search():
    q = request.args.get('q', '').strip()
    query = Company.query.filter(Company.status == 'Active')
    if q:
        like = f"%{q}%"
        query = query.filter((Company.company_name.ilike(like)) | (Company.company_code.ilike(like)))
    companies = query.order_by(Company.company_name).limit(20).all()
    data = [
        {
            'id': company.id,
            'text': f"{company.company_name} ({company.company_code})",
            'company_name': company.company_name,
            'company_code': company.company_code,
            'status': company.status,
        }
        for company in companies
    ]
    return jsonify(items=data)


@clients_bp.route('/circles/search')
@login_required
def circles_search():
    company_id = request.args.get('company_id')
    q = request.args.get('q', '').strip()
    if not company_id:
        return jsonify(items=[])

    query = Circle.query.filter(Circle.company_id == company_id, Circle.status == 'Active')
    if q:
        like = f"%{q}%"
        query = query.filter((Circle.circle_name.ilike(like)) | (Circle.circle_code.ilike(like)))
    circles = query.order_by(Circle.circle_name).limit(20).all()
    data = [
        {
            'id': circle.id,
            'text': f"{circle.circle_name} ({circle.circle_code})",
            'circle_name': circle.circle_name,
            'circle_code': circle.circle_code,
            'status': circle.status,
        }
        for circle in circles
    ]
    return jsonify(items=data)


@clients_bp.route('/check_code')
@login_required
def check_code():
    company_id = request.args.get('company_id')
    code = (request.args.get('code') or '').strip().upper()
    repo = client_service.repository
    exists = repo.exists_by_field('client_code', code, company_id=company_id)
    return jsonify({'exists': exists})
