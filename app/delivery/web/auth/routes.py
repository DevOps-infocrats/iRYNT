import logging
from datetime import timedelta

from flask import (
    Blueprint,
    current_app,
    flash,
    jsonify,
    make_response,
    redirect,
    request,
    session,
    url_for,
)
from flask_login import current_user, login_required, login_user, logout_user

from app.application.auth.use_cases.forgot_password import ForgotPasswordUseCase
from app.application.auth.use_cases.login_user import LoginUserUseCase
from app.application.auth.use_cases.logout_user import LogoutUserUseCase
from app.application.auth.use_cases.reset_password import ResetPasswordUseCase
from app.delivery.web.auth.forms import ForgotPasswordForm, LoginForm, ResetPasswordForm
from app.delivery.web.auth.views import (
    render_dashboard,
    render_forgot_password,
    render_login,
    render_reset_password,
)


auth_bp = Blueprint('auth', __name__)

login_use_case = LoginUserUseCase()
logout_use_case = LogoutUserUseCase()
forgot_use_case = ForgotPasswordUseCase()
reset_use_case = ResetPasswordUseCase()


def _is_ajax(request):
    return request.headers.get('X-Requested-With') == 'XMLHttpRequest'


def _json_response(result, status=200):
    payload = {
        'success': result.get('success', False),
        'message': result.get('message', ''),
        'data': {},
    }
    if result.get('access_token'):
        payload['data'] = {
            'access_token': result.get('access_token'),
            'refresh_token': result.get('refresh_token'),
            'user': result.get('user').to_dict() if result.get('user') else None,
            'permissions': result.get('user').permissions if result.get('user') else [],
        }
    return jsonify(payload), status


@auth_bp.route('/', methods=['GET', 'POST'])
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        is_field = False
        if current_user.primary_role and current_user.primary_role.name.lower() in ('driver', 'helper'):
            is_field = True
        elif any(r.name.lower() in ('driver', 'helper') for r in current_user.roles):
            is_field = True

        is_admin = False
        if current_user.primary_role and current_user.primary_role.name.lower() in ('super admin', 'admin'):
            is_admin = True
        elif any(r.name.lower() in ('super admin', 'admin') for r in current_user.roles):
            is_admin = True

        if is_field and not is_admin:
            return redirect(url_for('attendance.live'))
        return redirect(url_for('auth.dashboard'))

    form = LoginForm()
    next_url = request.args.get('next') or request.form.get('next')
    if form.validate_on_submit():
        try:
            result = login_use_case.execute(
                identifier=form.login_identifier.data,
                password=form.password.data,
                remember_me=form.remember_me.data,
                ip_address=request.remote_addr,
                user_agent=request.user_agent.string,
            )
        except Exception as exc:
            logging.exception('Login failure')
            result = {'success': False, 'message': str(exc)}

        if result.get('success'):
            user = result['user']
            try:
                from app.services.compliance.alerts_service import trigger_lightweight_compliance_checks
                trigger_lightweight_compliance_checks()
            except Exception:
                pass
            login_user(user, remember=form.remember_me.data, duration=current_app.config.get('REMEMBER_COOKIE_DURATION'))
            session.permanent = True
            session['auth_session_key'] = result.get('session_key')
            
            is_field = False
            if user.primary_role and user.primary_role.name in ('Driver', 'Helper'):
                is_field = True
            elif any(r.name in ('Driver', 'Helper') for r in user.roles):
                is_field = True

            is_admin = False
            if user.primary_role and user.primary_role.name in ('Super Admin', 'Admin'):
                is_admin = True
            elif any(r.name in ('Super Admin', 'Admin') for r in user.roles):
                is_admin = True

            if is_field and not is_admin:
                # For drivers/helpers always go to live attendance, ignoring any next_url
                redirect_location = url_for('attendance.live')
            else:
                redirect_location = next_url or url_for('auth.dashboard')
                
            response = make_response(redirect(redirect_location))
            if result.get('remember_token'):
                response.set_cookie(
                    'remember_me',
                    result['remember_token'],
                    max_age=int(current_app.config.get('REMEMBER_COOKIE_DURATION').total_seconds()),
                    httponly=True,
                    secure=current_app.config.get('SESSION_COOKIE_SECURE', False),
                    samesite='Lax',
                )
            if _is_ajax(request):
                return jsonify({'success': True, 'message': 'Login successful.', 'redirect': redirect_location})
            return response

        if _is_ajax(request):
            return jsonify({'success': False, 'message': result.get('message')}), 401

        flash(result.get('message', 'Login failed.'), 'danger')

    return render_login(form, next_url=next_url)


@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    form = ForgotPasswordForm()
    if form.validate_on_submit():
        try:
            response = forgot_use_case.execute(email=form.email.data)
        except Exception as exc:
            logging.exception('Forgot password failure')
            response = {'success': False}

        if response.get('success'):
            flash('If this email exists, a reset link has been sent.', 'success')
        else:
            flash('If this email exists, a reset link has been sent.', 'success')

        if _is_ajax(request):
            return jsonify({'success': True, 'message': 'If this email exists, a reset link has been sent.'})

    return render_forgot_password(form)


@auth_bp.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    token = request.args.get('token') or request.form.get('token')
    form = ResetPasswordForm(token=token)
    if form.validate_on_submit():
        try:
            result = reset_use_case.execute(token=form.token.data, new_password=form.new_password.data)
        except Exception as exc:
            logging.exception('Reset password failure')
            result = {'success': False, 'message': str(exc)}

        if result.get('success'):
            flash(result.get('message'), 'success')
            return redirect(url_for('auth.login'))

        flash(result.get('message', 'Unable to reset password.'), 'danger')

    return render_reset_password(form, token=token)


@auth_bp.route('/logout')
@login_required
def logout():
    token = request.cookies.get('refresh_token')
    result = logout_use_case.execute(current_user, refresh_token=token)
    logout_user()
    response = redirect(url_for('auth.login'))
    response.delete_cookie('remember_me')
    response.delete_cookie('refresh_token')
    if _is_ajax(request):
        return jsonify({'success': True, 'message': result.get('message', 'Logged out'), 'redirect': url_for('auth.login')})
    return response


@auth_bp.route('/dashboard')
@auth_bp.route('/dashboard/')
@login_required
def dashboard():
    is_field = False
    if current_user.primary_role and current_user.primary_role.name in ('Driver', 'Helper'):
        is_field = True
    elif any(r.name in ('Driver', 'Helper') for r in current_user.roles):
        is_field = True

    is_admin = False
    if current_user.primary_role and current_user.primary_role.name in ('Super Admin', 'Admin'):
        is_admin = True
    elif any(r.name in ('Super Admin', 'Admin') for r in current_user.roles):
        is_admin = True

    if is_field and not is_admin:
        return redirect(url_for('attendance.live'))

    try:
        from app.services.compliance.alerts_service import trigger_lightweight_compliance_checks
        trigger_lightweight_compliance_checks()
    except Exception:
        pass
    return render_dashboard()
