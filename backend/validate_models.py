"""
Model validation script for SoftBankCashWire
"""
from app import create_app
from models import (
    db, User, UserRole, AccountStatus, Account,
    Transaction, TransactionType, EventAccount, EventStatus,
    MoneyRequest, AuditLog
)
from decimal import Decimal

def validate_models():
    """Validate that all models work correctly"""
    app = create_app()
    
    with app.app_context():
        try:
            # Test User model
            print("Testing User model...")
            user = User(
                microsoft_id="test-validation",
                email="validation@test.com",
                name="Validation User",
                role=UserRole.EMPLOYEE
            )
            db.session.add(user)
            db.session.flush()
            print(f"✓ User created: {user}")
            
            # Test Account model
            print("Testing Account model...")
            account = Account(user_id=user.id, balance=Decimal('100.00'))
            db.session.add(account)
            db.session.flush()
            print(f"✓ Account created: {account}")
            
            # Test balance validation
            assert account.has_sufficient_funds(Decimal('50.00'))
            assert not account.has_sufficient_funds(Decimal('400.00'))
            print("✓ Account balance validation works")
            
            # Test Transaction model
            print("Testing Transaction model...")
            recipient = User(
                microsoft_id="recipient-test",
                email="recipient@test.com",
                name="Recipient User"
            )
            db.session.add(recipient)
            db.session.flush()
            
            transaction = Transaction.create_transfer(
                sender_id=user.id,
                recipient_id=recipient.id,
                amount=Decimal('25.00'),
                note="Test transaction"
            )
            db.session.add(transaction)
            db.session.flush()
            print(f"✓ Transaction created: {transaction}")
            
            # Test EventAccount model
            print("Testing EventAccount model...")
            event = EventAccount(
                creator_id=user.id,
                name="Test Event",
                description="Test event description",
                target_amount=Decimal('200.00')
            )
            db.session.add(event)
            db.session.flush()
            print(f"✓ EventAccount created: {event}")
            
            # Test MoneyRequest model
            print("Testing MoneyRequest model...")
            money_request = MoneyRequest.create_request(
                requester_id=user.id,
                recipient_id=recipient.id,
                amount=Decimal('30.00'),
                note="Test request"
            )
            db.session.add(money_request)
            db.session.flush()
            print(f"✓ MoneyRequest created: {money_request}")
            
            # Test AuditLog model
            print("Testing AuditLog model...")
            audit_log = AuditLog.log_user_action(
                user_id=user.id,
                action_type="VALIDATION_TEST",
                entity_type="User",
                entity_id=user.id,
                new_values={"test": "validation"}
            )
            db.session.flush()
            print(f"✓ AuditLog created: {audit_log}")
            
            # Test relationships
            print("Testing model relationships...")
            assert user.account == account
            assert account.user == user
            assert transaction.sender == user
            assert transaction.recipient == recipient
            assert event.creator == user
            assert money_request.requester == user
            assert money_request.recipient == recipient
            print("✓ All relationships work correctly")
            
            # Test model methods
            print("Testing model methods...")
            assert user.is_active()
            assert user.has_role(UserRole.EMPLOYEE)
            assert account.has_sufficient_funds(Decimal('25.00'))
            assert transaction.is_transfer()
            assert event.is_active()
            assert money_request.is_pending()
            print("✓ All model methods work correctly")
            
            # Commit all changes
            db.session.commit()
            print("\n✅ All models validated successfully!")
            
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ Validation failed: {e}")
            raise

if __name__ == '__main__':
    validate_models()