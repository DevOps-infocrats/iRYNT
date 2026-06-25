from flask import Blueprint, abort, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.domain.auth.policies.auth_policy import has_permission
from app.modules.users.forms import UserForm
from app.modules.users.services import UserService

users_bp = Blueprint('users', __name__, url_prefix='/users')
user_service = UserService()


@users_bp.route('/')
@login_required
def index():
    if not has_permission('users.view'):
        abort(403)

    page = request.args.get('page', 1, type=int)
    per_page = 20
    filters = {
        'company_id': request.args.get('company_id') or None,
        'circle_id': request.args.get('circle_id') or None,
        'client_id': request.args.get('client_id') or None,
        'project_id': request.args.get('project_id') or None,
        'subzone_id': request.args.get('subzone_id') or None,
        'role_id': request.args.get('role_id') or None,
        'status': request.args.get('status') or None,
        'search_query': request.args.get('q', '').strip() or None,
        'access_scope': request.args.get('access_scope') or None,
    }

    if not current_user.is_superadmin:
        if current_user.circle_id:
            filters['circle_id'] = current_user.circle_id
        elif current_user.company_id:
            filters['company_id'] = current_user.company_id

    users, total = user_service.search_users(filters, page, per_page)
    kpis = user_service.get_dashboard_metrics(filters)
    filters_payload = user_service.get_filter_payload(filters)

    return render_template(
        'users/list.html',
        users=users,
        total=total,
        page=page,
        per_page=per_page,
        kpis=kpis,
        companies=filters_payload['companies'],
        circles=filters_payload['circles'],
        clients=filters_payload['clients'],
        projects=filters_payload['projects'],
        subzones=filters_payload['subzones'],
        roles=filters_payload['roles'],
        status_options=filters_payload['status_options'],
        access_scopes=filters_payload['access_scopes'],
        operational_types=filters_payload['operational_types'],
        filters=filters,
        active_page='users',
    )


@users_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    if not has_permission('users.create'):
        abort(403)

    form = UserForm()
    form.company_id.choices = user_service.get_company_choices()
    form.circle_id.choices = user_service.get_circle_choices()
    form.role_id.choices = user_service.get_role_choices()

    if request.method == 'POST':
        form.circle_id.choices = user_service.get_circle_choices(form.company_id.data)
        if form.validate_on_submit():
            if not form.password.data:
                form.password.errors.append('Password is required for new users.')
            if not form.errors:
                try:
                    user_service.create_user(
                        {
                            'username': form.username.data,
                            'email': form.email.data,
                            'phone': form.phone.data,
                            'password': form.password.data,
                            'company_id': form.company_id.data,
                            'circle_id': form.circle_id.data,
                            'role_id': form.role_id.data,
                            'is_active': form.is_active.data,
                            'is_verified': form.is_verified.data,
                        }
                    )
                    flash('Workforce identity record created.', 'success')
                    return redirect(url_for('users.index'))
                except Exception as e:
                    from app.extensions import db
                    db.session.rollback()
                    msg = str(e).lower()
                    if 'username' in msg:
                        form.username.errors.append('Username already exists.')
                    elif 'email' in msg:
                        form.email.errors.append('Email already exists.')
                    elif 'phone' in msg:
                        form.phone.errors.append('Phone number already exists.')
                    else:
                        flash(f'An error occurred: {str(e)}', 'danger')

    return render_template(
        'users/manage.html',
        form=form,
        title='Add Workforce User',
        active_page='users',
    )


@users_bp.route('/<user_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(user_id):
    if not has_permission('users.edit'):
        abort(403)

    user = user_service.get_user(user_id)
    if not user:
        flash('User not found.', 'danger')
        return redirect(url_for('users.index'))

    form = UserForm(obj=user)
    form.company_id.choices = user_service.get_company_choices()
    form.role_id.choices = user_service.get_role_choices()
    form.circle_id.choices = user_service.get_circle_choices(user.company_id)

    if request.method == 'POST':
        form.circle_id.choices = user_service.get_circle_choices(form.company_id.data)
        if form.validate_on_submit():
            try:
                user_service.update_user(
                    user_id,
                    {
                        'username': form.username.data,
                        'email': form.email.data,
                        'phone': form.phone.data,
                        'password': form.password.data,
                        'company_id': form.company_id.data,
                        'circle_id': form.circle_id.data,
                        'role_id': form.role_id.data,
                        'is_active': form.is_active.data,
                        'is_verified': form.is_verified.data,
                    },
                )
                flash('User record updated successfully.', 'success')
                return redirect(url_for('users.profile', user_id=user_id))
            except Exception as e:
                from app.extensions import db
                db.session.rollback()
                msg = str(e).lower()
                if 'username' in msg:
                    form.username.errors.append('Username already exists.')
                elif 'email' in msg:
                    form.email.errors.append('Email already exists.')
                elif 'phone' in msg:
                    form.phone.errors.append('Phone number already exists.')
                else:
                    flash(f'An error occurred: {str(e)}', 'danger')

    return render_template(
        'users/manage.html',
        form=form,
        user=user,
        title='Edit Workforce User',
        active_page='users',
    )


@users_bp.route('/<user_id>')
@login_required
def profile(user_id):
    if not has_permission('users.view'):
        abort(403)

    profile_data = user_service.get_user_profile(user_id)
    if not profile_data:
        flash('User not found.', 'danger')
        return redirect(url_for('users.index'))

    return render_template(
        'users/profile.html',
        profile=profile_data,
        active_page='users',
        can_edit=has_permission('users.edit'),
        can_manage=has_permission('users.manage'),
    )


@users_bp.route('/ajax/hierarchy')
@login_required
def ajax_hierarchy():
    if not has_permission('users.view'):
        return jsonify([])

    filter_type = request.args.get('type')
    parent_id = request.args.get('parent_id')
    return jsonify(user_service.get_hierarchy_options(filter_type, parent_id))


@users_bp.route('/ajax/search')
@login_required
def ajax_search():
    if not has_permission('users.view'):
        return jsonify([])

    query_text = request.args.get('q', '').strip()
    results = user_service.search_suggestions(query_text)
    return jsonify(results)

