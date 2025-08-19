"""
SoftBankCashWire Flask Application Entry Point
"""
from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from config import Config, DevelopmentConfig
from models import db
from middleware import AuthMiddleware
from middleware.security_middleware import SecurityMiddleware
from api.auth import auth_bp
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def create_app(config_class=None):
    """Application factory pattern for Flask app creation"""
    if config_class is None:
        config_class = DevelopmentConfig if os.environ.get('FLASK_ENV') == 'development' else Config
    
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize extensions
    db.init_app(app)
    CORS(app)
    jwt = JWTManager(app)
    
    # Initialize middleware
    AuthMiddleware(app)
    SecurityMiddleware(app)
    
    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    
    # Import and register accounts blueprint
    from api.accounts import accounts_bp
    app.register_blueprint(accounts_bp, url_prefix='/api/accounts')
    
    # Import and register transactions blueprint
    from api.transactions import transactions_bp
    app.register_blueprint(transactions_bp, url_prefix='/api/transactions')
    
    # Import and register money requests blueprint
    from api.money_requests import money_requests_bp
    app.register_blueprint(money_requests_bp, url_prefix='/api/money-requests')
    
    # Import and register events blueprint
    from api.events import events_bp
    app.register_blueprint(events_bp, url_prefix='/api/events')
    
    # Import and register audit blueprint
    from api.audit import audit_bp
    app.register_blueprint(audit_bp, url_prefix='/api/audit')
    
    # Import and register reporting blueprint
    from api.reporting import reporting_bp
    app.register_blueprint(reporting_bp, url_prefix='/api/reporting')
    
    # Import and register system blueprint
    from api.system import system_bp
    app.register_blueprint(system_bp, url_prefix='/api/system')
    
    # Import and register security blueprint
    from api.security import security_bp
    app.register_blueprint(security_bp, url_prefix='/api/security')
    
    # Import and register admin blueprint
    from api.admin import admin_bp
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    
    # Import and register notifications blueprint
    from api.notifications import notifications_bp
    app.register_blueprint(notifications_bp, url_prefix='/api/notifications')
    
    # Import and register backup blueprint
    from api.backup import backup_bp
    app.register_blueprint(backup_bp, url_prefix='/api/backup')
    
    # Import and register development blueprint (only in development)
    if config_class == DevelopmentConfig:
        from api.dev import dev_bp
        app.register_blueprint(dev_bp, url_prefix='/api/dev')
    
    # Configure JWT
    configure_jwt(jwt)
    
    # Register error handlers
    register_error_handlers(app)
    
    # Create tables in development
    if config_class == DevelopmentConfig:
        with app.app_context():
            db.create_all()
    
    return app

def configure_jwt(jwt):
    """Configure JWT manager"""
    
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return {
            'error': {
                'code': 'TOKEN_EXPIRED',
                'message': 'Token has expired'
            }
        }, 401
    
    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return {
            'error': {
                'code': 'INVALID_TOKEN',
                'message': 'Invalid token'
            }
        }, 401
    
    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return {
            'error': {
                'code': 'TOKEN_REQUIRED',
                'message': 'Authentication token required'
            }
        }, 401
    
    @jwt.needs_fresh_token_loader
    def token_not_fresh_callback(jwt_header, jwt_payload):
        return {
            'error': {
                'code': 'FRESH_TOKEN_REQUIRED',
                'message': 'Fresh token required'
            }
        }, 401
    
    @jwt.revoked_token_loader
    def revoked_token_callback(jwt_header, jwt_payload):
        return {
            'error': {
                'code': 'TOKEN_REVOKED',
                'message': 'Token has been revoked'
            }
        }, 401

def register_error_handlers(app):
    """Register global error handlers"""
    
    @app.errorhandler(400)
    def bad_request(error):
        return {'error': {'code': 'BAD_REQUEST', 'message': 'Bad request'}}, 400
    
    @app.errorhandler(401)
    def unauthorized(error):
        return {'error': {'code': 'UNAUTHORIZED', 'message': 'Authentication required'}}, 401
    
    @app.errorhandler(403)
    def forbidden(error):
        return {'error': {'code': 'FORBIDDEN', 'message': 'Access denied'}}, 403
    
    @app.errorhandler(404)
    def not_found(error):
        return {'error': {'code': 'NOT_FOUND', 'message': 'Resource not found'}}, 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return {'error': {'code': 'INTERNAL_ERROR', 'message': 'Internal server error'}}, 500

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5002)