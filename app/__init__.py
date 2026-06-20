import os
from flask import Flask, redirect, request, url_for
from sqlalchemy import inspect, text
from sqlalchemy.engine.url import make_url
from werkzeug.routing import BuildError
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

from config import config
from app.extensions import csrf, db, jwt, login_manager, migrate
from app.middleware import init_middleware
from app.infrastructure.repositories.auth.auth_repository import AuthRepository
from app.core.sidebar import build_sidebar_menu
from app.domain.auth.policies.auth_policy import has_permission, has_role, has_scope
from app.domain.auth.services.auth_service import AuthService
from app.delivery.web.auth import auth_bp
from app.delivery.api.v1.auth import api_auth_bp


def _ensure_database_exists(sqlalchemy_uri):
    url = make_url(sqlalchemy_uri)
    if not url.drivername.startswith('postgresql'):
        return

    database_name = url.database
    if not database_name:
        return

    conn = psycopg2.connect(
        dbname='postgres',
        user=url.username,
        password=url.password,
        host=url.host or 'localhost',
        port=url.port or 5432,
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    with conn.cursor() as cursor:
        cursor.execute('SELECT 1 FROM pg_database WHERE datname=%s', (database_name,))
        if not cursor.fetchone():
            cursor.execute(f'CREATE DATABASE "{database_name}"')
    conn.close()


def _register_default_auth_data():
    from app.modules.auth.models import Role, User

    super_role = Role.query.filter_by(name='Super Admin').first()
    if not super_role:
        super_role = Role(
            name='Super Admin',
            description='Enterprise super administrator role.',
            is_system=True,
        )
        db.session.add(super_role)
        db.session.commit()

    super_user = User.query.filter_by(username='superadmin').first()
    if not super_user:
        super_user = User(
            username='superadmin',
            email='superadmin@example.com',
            phone='0000000000',
            is_active=True,
            is_verified=True,
            company_id=None,
            circle_id=None,
            role_id=super_role.id,
        )
        super_user.set_password('Admin@321')
        super_user.roles.append(super_role)
        db.session.add(super_user)
        db.session.commit()

    return super_user


def _ensure_permissions_schema():
    inspector = inspect(db.engine)
    if inspector.has_table('permissions'):
        columns = [col['name'] for col in inspector.get_columns('permissions')]
        if 'category_id' not in columns:
            with db.engine.begin() as connection:
                connection.execute(
                    text('ALTER TABLE permissions ADD COLUMN category_id VARCHAR(36) NULL')
                )
                connection.execute(
                    text(
                        'ALTER TABLE permissions ADD CONSTRAINT fk_permissions_category_id '
                        'FOREIGN KEY (category_id) REFERENCES permission_category (id)'
                    )
                )


def _ensure_attendance_verification_schema():
    inspector = inspect(db.engine)
    if inspector.has_table('driver_attendance'):
        columns = [col['name'] for col in inspector.get_columns('driver_attendance')]
        with db.engine.begin() as connection:
            if 'selfie_storage_path' not in columns:
                connection.execute(
                    text('ALTER TABLE driver_attendance ADD COLUMN selfie_storage_path VARCHAR(512) NULL')
                )
            if 'dashboard_storage_path' not in columns:
                connection.execute(
                    text('ALTER TABLE driver_attendance ADD COLUMN dashboard_storage_path VARCHAR(512) NULL')
                )
            if 'start_odometer' not in columns:
                connection.execute(
                    text('ALTER TABLE driver_attendance ADD COLUMN start_odometer FLOAT NULL')
                )
            if 'end_odometer' not in columns:
                connection.execute(
                    text('ALTER TABLE driver_attendance ADD COLUMN end_odometer FLOAT NULL')
                )
            if 'verification_status' not in columns:
                connection.execute(
                    text('ALTER TABLE driver_attendance ADD COLUMN verification_status VARCHAR(30) NULL')
                )

    if inspector.has_table('vehicles'):
        columns = [col['name'] for col in inspector.get_columns('vehicles')]
        with db.engine.begin() as connection:
            if 'vehicle_running' not in columns:
                connection.execute(
                    text('ALTER TABLE vehicles ADD COLUMN vehicle_running FLOAT DEFAULT 0.0 NULL')
                )
            if 'insurance_expiry' not in columns:
                connection.execute(
                    text('ALTER TABLE vehicles ADD COLUMN insurance_expiry DATE NULL')
                )
            if 'fitness_expiry' not in columns:
                connection.execute(
                    text('ALTER TABLE vehicles ADD COLUMN fitness_expiry DATE NULL')
                )
            if 'permit_expiry' not in columns:
                connection.execute(
                    text('ALTER TABLE vehicles ADD COLUMN permit_expiry DATE NULL')
                )
            if 'puc_expiry' not in columns:
                connection.execute(
                    text('ALTER TABLE vehicles ADD COLUMN puc_expiry DATE NULL')
                )

    if inspector.has_table('notifications'):
        columns = [col['name'] for col in inspector.get_columns('notifications')]
        with db.engine.begin() as connection:
            if 'company_id' not in columns:
                connection.execute(
                    text('ALTER TABLE notifications ADD COLUMN company_id VARCHAR(36) NULL')
                )
            if 'circle_id' not in columns:
                connection.execute(
                    text('ALTER TABLE notifications ADD COLUMN circle_id VARCHAR(36) NULL')
                )





def create_app(config_name=None):
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')

    template_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates')
    static_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static')

    app = Flask(__name__, template_folder=template_path, static_folder=static_path)
    app.config.from_object(config[config_name])
    os.makedirs(app.config['DRIVER_DOCUMENT_UPLOAD_FOLDER'], exist_ok=True)

    import jinja2
    from flask import send_from_directory

    app.jinja_loader = jinja2.ChoiceLoader([
        jinja2.FileSystemLoader(template_path),
        jinja2.FileSystemLoader(os.path.join(os.path.dirname(__file__), 'templates'))
    ])

    def custom_send_static_file(filename):
        root_static = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static')
        if os.path.exists(os.path.join(root_static, filename)):
            return send_from_directory(root_static, filename)
        app_static = os.path.join(os.path.dirname(__file__), 'static')
        return send_from_directory(app_static, filename)

    app.send_static_file = custom_send_static_file

    _ensure_database_exists(app.config['SQLALCHEMY_DATABASE_URI'])
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)
    jwt.init_app(app)

    repository = AuthRepository()
    service = AuthService(repository)

    @login_manager.user_loader
    def load_user(user_id):
        return repository.get_user_by_id(user_id)

    @login_manager.unauthorized_handler
    def unauthorized():
        next_url = request.path
        return redirect(url_for('auth.login', next=next_url))

    from app.modules.companies.routes import companies_bp
    from app.modules.circles.routes import circles_bp
    from app.modules.clients.routes import clients_bp
    from app.modules.projects.routes import projects_bp
    from app.modules.subzones.routes import subzones_bp
    from app.modules.vehicles.routes import vehicles_bp
    from app.modules.users.routes import users_bp
    from app.modules.users.controllers.bulk_import_controller import bulk_import_bp
    from app.modules.drivers.routes import drivers_bp
    from app.modules.attendance.routes import attendance_bp
    from app.modules.deployments.routes import deployments_bp
    from app.modules.roles.routes import roles_bp
    from app.modules.roles.api_routes import roles_api_bp
    from app.modules.permissions.routes import permissions_bp
    from app.modules.permissions.api_routes import permissions_api_bp
    from app.modules.access_control.routes import access_control_bp
    from app.modules.approvals.routes import approval_bp
    from app.modules.documents.routes import documents_bp
    # Import notifications blueprint. The delivery.web package uses a module named
    # `routes.py`, which conflicts with the `routes` directory. Attempt a normal
    # import first; if that fails, fall back to loading the file directly so
    # the app can start without restructuring packages.
    try:
        # pyrefly: ignore [missing-import]
        from app.delivery.web.routes.notifications_routes import notifications_bp
    except Exception:
        import importlib.util
        notif_path = os.path.join(os.path.dirname(__file__), 'delivery', 'web', 'routes', 'notifications_routes.py')
        spec = importlib.util.spec_from_file_location('app.delivery.web.routes.notifications_routes', notif_path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        notifications_bp = getattr(mod, 'notifications_bp')

    app.register_blueprint(auth_bp)
    app.register_blueprint(api_auth_bp, url_prefix='/api/v1/auth')
    app.register_blueprint(roles_api_bp)
    app.register_blueprint(permissions_api_bp)
    app.register_blueprint(companies_bp)
    app.register_blueprint(circles_bp)
    app.register_blueprint(clients_bp)
    app.register_blueprint(projects_bp)
    app.register_blueprint(subzones_bp)
    app.register_blueprint(vehicles_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(bulk_import_bp)
    app.register_blueprint(drivers_bp)
    app.register_blueprint(attendance_bp)
    app.register_blueprint(deployments_bp)
    app.register_blueprint(roles_bp)
    app.register_blueprint(permissions_bp)
    app.register_blueprint(access_control_bp)
    app.register_blueprint(approval_bp)
    app.register_blueprint(documents_bp)
    app.register_blueprint(notifications_bp)
    csrf.exempt(api_auth_bp)
    init_middleware(app)

    def url_for_safe(endpoint, **values):
        try:
            return url_for(endpoint, **values)
        except BuildError:
            return '#'

    app.add_template_global(url_for_safe, 'url_for_safe')
    app.add_template_global(has_permission, 'has_permission')
    app.add_template_global(has_role, 'has_role')
    app.add_template_global(has_scope, 'has_scope')

    from app.modules.attendance.utils import to_india_datetime

    @app.context_processor
    def inject_sidebar_globals():
        return {
            'sidebar_menu': build_sidebar_menu(),
            'has_permission': has_permission,
            'has_role': has_role,
            'has_scope': has_scope,
        }

    app.add_template_global(to_india_datetime, 'to_india_datetime')

    @jwt.token_in_blocklist_loader
    def check_if_token_revoked(jwt_header, jwt_payload):
        return service.blocklisted_token(jwt_header, jwt_payload)

    with app.app_context():
        import app.modules.auth.models as auth_models
        import app.modules.permissions.models as permissions_models
        db.create_all()
        _ensure_permissions_schema()
        _ensure_attendance_verification_schema()
        _register_default_auth_data()
        
        # Seed predefined permissions and roles from templates
        try:
            from seeds.permissions_seed import seed_predefined_permissions
            from seeds.roles_seed import ensure_predefined_roles
            
            # Seed permissions first (roles depend on permissions)
            seed_predefined_permissions()
            
            # Ensure predefined roles are seeded
            ensure_predefined_roles()
            try:
                # Seed approval workflows after roles exist
                from seeds.approval_workflow_seed import seed_approval_workflows
                seed_approval_workflows()
            except Exception as e:
                print(f"Warning: Error seeding approval workflows: {e}")
        except Exception as e:
            print(f"Warning: Error seeding predefined permissions and roles: {e}")
            # Don't fail app startup if seeding fails
            pass

    @app.errorhandler(401)
    def unauthorized_error(error):
        return {'error': 'Unauthorized access'}, 401

    @app.errorhandler(403)
    def forbidden_error(error):
        return {'error': 'Forbidden access'}, 403

    @app.errorhandler(404)
    def not_found(error):
        return {'error': 'Not found'}, 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return {'error': 'Internal server error'}, 500

    return app
