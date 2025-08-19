"""
Database initialization script for SoftBankCashWire
"""
from app import create_app
from models import db, User, UserRole, AccountStatus, Account
from decimal import Decimal

def init_database():
    """Initialize the database with tables and sample data"""
    app = create_app()
    
    with app.app_context():
        # Drop all tables (for development)
        db.drop_all()
        
        # Create all tables
        db.create_all()
        print("Database tables created successfully!")
        
        # Print table information
        inspector = db.inspect(db.engine)
        tables = inspector.get_table_names()
        print(f"Created tables: {', '.join(tables)}")
        
        # Create sample users for development
        create_sample_data()

def create_sample_data():
    """Create sample data for development and testing"""
    try:
        # Create sample users
        admin_user = User(
            microsoft_id="admin-123",
            email="admin@softbank.com",
            name="Admin User",
            role=UserRole.ADMIN,
            account_status=AccountStatus.ACTIVE
        )
        
        finance_user = User(
            microsoft_id="finance-123",
            email="finance@softbank.com",
            name="Finance User",
            role=UserRole.FINANCE,
            account_status=AccountStatus.ACTIVE
        )
        
        employee1 = User(
            microsoft_id="emp1-123",
            email="john.doe@softbank.com",
            name="John Doe",
            role=UserRole.EMPLOYEE,
            account_status=AccountStatus.ACTIVE
        )
        
        employee2 = User(
            microsoft_id="emp2-123",
            email="jane.smith@softbank.com",
            name="Jane Smith",
            role=UserRole.EMPLOYEE,
            account_status=AccountStatus.ACTIVE
        )
        
        # Add users to session
        db.session.add_all([admin_user, finance_user, employee1, employee2])
        db.session.flush()  # Flush to get IDs
        
        # Create accounts for users
        admin_account = Account(user_id=admin_user.id, balance=Decimal('100.00'))
        finance_account = Account(user_id=finance_user.id, balance=Decimal('50.00'))
        emp1_account = Account(user_id=employee1.id, balance=Decimal('75.00'))
        emp2_account = Account(user_id=employee2.id, balance=Decimal('25.00'))
        
        db.session.add_all([admin_account, finance_account, emp1_account, emp2_account])
        
        # Commit all changes
        db.session.commit()
        
        print("Sample data created successfully!")
        print(f"- Admin User: {admin_user.email} (ID: {admin_user.id})")
        print(f"- Finance User: {finance_user.email} (ID: {finance_user.id})")
        print(f"- Employee 1: {employee1.email} (ID: {employee1.id})")
        print(f"- Employee 2: {employee2.email} (ID: {employee2.id})")
        
    except Exception as e:
        db.session.rollback()
        print(f"Error creating sample data: {e}")

if __name__ == '__main__':
    init_database()