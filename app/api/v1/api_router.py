from app.api.v1.deployments.routes import api_deployments_bp
from app.api.v1.vehicles.routes import api_vehicles_bp
from app.extensions import csrf

def register_api_v1_routes(app):
    """
    Registers the v1 API routes for deployments and vehicles,
    and configures them to be exempt from CSRF protection for API clients.
    """
    app.register_blueprint(api_deployments_bp, url_prefix='/api/v1/deployments')
    app.register_blueprint(api_vehicles_bp, url_prefix='/api/v1/vehicles')
    
    # Exempt from CSRF for mobile/API access
    csrf.exempt(api_deployments_bp)
    csrf.exempt(api_vehicles_bp)
