"""
API routes package for SoftBankCashWire
"""
from .auth import auth_bp
from .accounts import accounts_bp
from .transactions import transactions_bp
from .events import events_bp
from .reporting import reporting_bp

def register_blueprints(app):
    """Register all API blueprints with the Flask app"""
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(accounts_bp, url_prefix='/api/accounts')
    app.register_blueprint(transactions_bp, url_prefix='/api/transactions')
    app.register_blueprint(events_bp, url_prefix='/api/events')
    app.register_blueprint(reporting_bp, url_prefix='/api/reports')

__all__ = [
    'register_blueprints',
    'auth_bp',
    'accounts_bp', 
    'transactions_bp',
    'events_bp',
    'reporting_bp'
]