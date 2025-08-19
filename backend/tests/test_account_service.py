"""
Tests for AccountService
"""
import pytest
from decimal import Decimal
from datetime import datetime, timedelta
from services.account_service import AccountService
from models import (
    db, User, UserRole, Account, Transaction, TransactionType, 
    TransactionStatus, AuditLog
)

class TestAccountService:
    """Test cases for AccountService"""
    
    def test_get_account_balance_success(self, app):
        """Test getting account balance"""
        with app.app_context():
            # Create user and account
            user = User(microsoft_id='test-123', email='test@test.com', name='Test User')
            db.session.add(user)
            db.session.flush()
            
            account = Account(user_id=user.id, balance=Decimal('100.00'))
            db.session.add(account)
            db.session.commit()
            
            # Test getting balance
            balance = AccountService.get_account_balance(user.id)
            assert balance == Decimal('100.00')
    
    def test_get_account_balance_not_found(self, app):
        """Test getting balance for non-existent account"""
        with app.app_context():
            with pytest.raises(ValueError, match="Account not found"):
                AccountService.get_account_balance('non-existent-id')
    
    def test_validate_transaction_limits_valid(self, app):
        """Test transaction limit validation with valid amount"""
        with app.app_context():
            # Create user and account
            user = User(microsoft_id='test-123', email='test@test.com', name='Test User')
            db.session.add(user)
            db.session.flush()
            
            account = Account(user_id=user.id, balance=Decimal('100.00'))
            db.session.add(account)
            db.session.commit()
            
            # Test valid transaction
            validation = AccountService.validate_transaction_limits(user.id, Decimal('-50.00'))
            
            assert validation['valid'] is True
            assert validation['current_balance'] == Decimal('100.00')
            assert validation['new_balance'] == Decimal('50.00')
            assert len(validation['errors']) == 0
    
    def test_validate_transaction_limits_insufficient_funds(self, app):
        """Test transaction limit validation with insufficient funds"""
        with app.app_context():
            # Create user and account
            user = User(microsoft_id='test-123', email='test@test.com', name='Test User')
            db.session.add(user)
            db.session.flush()
            
            account = Account(user_id=user.id, balance=Decimal('100.00'))
            db.session.add(account)
            db.session.commit()
            
            # Test transaction that would exceed overdraft
            validation = AccountService.validate_transaction_limits(user.id, Decimal('-400.00'))
            
            assert validation['valid'] is False
            assert len(validation['errors']) == 1
            assert validation['errors'][0]['code'] == 'INSUFFICIENT_FUNDS'
    
    def test_validate_transaction_limits_max_balance_exceeded(self, app):
        """Test transaction limit validation with max balance exceeded"""
        with app.app_context():
            # Create user and account
            user = User(microsoft_id='test-123', email='test@test.com', name='Test User')
            db.session.add(user)
            db.session.flush()
            
            account = Account(user_id=user.id, balance=Decimal('200.00'))
            db.session.add(account)
            db.session.commit()
            
            # Test transaction that would exceed maximum balance
            validation = AccountService.validate_transaction_limits(user.id, Decimal('100.00'))
            
            assert validation['valid'] is False
            assert len(validation['errors']) == 1
            assert validation['errors'][0]['code'] == 'BALANCE_LIMIT_EXCEEDED'
    
    def test_validate_transaction_limits_overdraft_warning(self, app):
        """Test transaction limit validation with overdraft warning"""
        with app.app_context():
            # Create user and account
            user = User(microsoft_id='test-123', email='test@test.com', name='Test User')
            db.session.add(user)
            db.session.flush()
            
            account = Account(user_id=user.id, balance=Decimal('75.00'))
            db.session.add(account)
            db.session.commit()
            
            # Test transaction that would trigger overdraft warning
            validation = AccountService.validate_transaction_limits(user.id, Decimal('-50.00'))
            
            assert validation['valid'] is True
            assert len(validation['warnings']) == 1
            assert validation['warnings'][0]['code'] == 'APPROACHING_OVERDRAFT'
    
    def test_get_available_balance(self, app):
        """Test getting available balance including overdraft"""
        with app.app_context():
            # Create user and account
            user = User(microsoft_id='test-123', email='test@test.com', name='Test User')
            db.session.add(user)
            db.session.flush()
            
            account = Account(user_id=user.id, balance=Decimal('100.00'))
            db.session.add(account)
            db.session.commit()
            
            # Test available balance (current balance + overdraft limit)
            available = AccountService.get_available_balance(user.id)
            assert available == Decimal('350.00')  # 100 + 250 overdraft
    
    def test_update_account_balance_success(self, app):
        """Test successful balance update"""
        with app.app_context():
            # Create user and account
            user = User(microsoft_id='test-123', email='test@test.com', name='Test User')
            db.session.add(user)
            db.session.flush()
            
            account = Account(user_id=user.id, balance=Decimal('100.00'))
            db.session.add(account)
            db.session.commit()
            
            # Test balance update
            result = AccountService.update_account_balance(
                user_id=user.id,
                amount=Decimal('-25.00'),
                ip_address='127.0.0.1'
            )
            
            assert result['success'] is True
            assert result['old_balance'] == Decimal('100.00')
            assert result['new_balance'] == Decimal('75.00')
            assert result['amount'] == Decimal('-25.00')
            
            # Verify balance was updated
            updated_balance = AccountService.get_account_balance(user.id)
            assert updated_balance == Decimal('75.00')
    
    def test_update_account_balance_validation_failure(self, app):
        """Test balance update with validation failure"""
        with app.app_context():
            # Create user and account
            user = User(microsoft_id='test-123', email='test@test.com', name='Test User')
            db.session.add(user)
            db.session.flush()
            
            account = Account(user_id=user.id, balance=Decimal('100.00'))
            db.session.add(account)
            db.session.commit()
            
            # Test balance update that would exceed limits
            with pytest.raises(ValueError, match="Transaction validation failed"):
                AccountService.update_account_balance(
                    user_id=user.id,
                    amount=Decimal('-400.00')
                )
    
    def test_get_transaction_history_basic(self, app):
        """Test getting basic transaction history"""
        with app.app_context():
            # Create users and accounts
            user1 = User(microsoft_id='user1', email='user1@test.com', name='User 1')
            user2 = User(microsoft_id='user2', email='user2@test.com', name='User 2')
            db.session.add_all([user1, user2])
            db.session.flush()
            
            account1 = Account(user_id=user1.id, balance=Decimal('100.00'))
            account2 = Account(user_id=user2.id, balance=Decimal('50.00'))
            db.session.add_all([account1, account2])
            db.session.flush()
            
            # Create transactions
            transaction1 = Transaction.create_transfer(
                sender_id=user1.id,
                recipient_id=user2.id,
                amount=Decimal('25.00'),
                note='Test transfer'
            )
            transaction1.mark_as_processed()
            
            transaction2 = Transaction.create_transfer(
                sender_id=user2.id,
                recipient_id=user1.id,
                amount=Decimal('10.00'),
                note='Return payment'
            )
            transaction2.mark_as_processed()
            
            db.session.add_all([transaction1, transaction2])
            db.session.commit()
            
            # Test getting history for user1
            history = AccountService.get_transaction_history(user1.id)
            
            assert len(history['transactions']) == 2
            assert history['pagination']['total'] == 2
            
            # Check transaction details
            transactions = history['transactions']
            
            # First transaction (most recent)
            assert transactions[0]['direction'] == 'incoming'
            assert transactions[0]['amount'] == '10.00'
            assert transactions[0]['other_party_name'] == 'User 2'
            
            # Second transaction
            assert transactions[1]['direction'] == 'outgoing'
            assert transactions[1]['amount'] == '25.00'
            assert transactions[1]['other_party_name'] == 'User 2'
    
    def test_get_transaction_history_with_filters(self, app):
        """Test getting transaction history with filters"""
        with app.app_context():
            # Create users and accounts
            user1 = User(microsoft_id='user1', email='user1@test.com', name='User 1')
            user2 = User(microsoft_id='user2', email='user2@test.com', name='User 2')
            db.session.add_all([user1, user2])
            db.session.flush()
            
            account1 = Account(user_id=user1.id, balance=Decimal('100.00'))
            account2 = Account(user_id=user2.id, balance=Decimal('50.00'))
            db.session.add_all([account1, account2])
            db.session.flush()
            
            # Create transactions with different amounts and categories
            transaction1 = Transaction.create_transfer(
                sender_id=user1.id,
                recipient_id=user2.id,
                amount=Decimal('25.00'),
                category='Lunch',
                note='Lunch payment'
            )
            transaction1.mark_as_processed()
            
            transaction2 = Transaction.create_transfer(
                sender_id=user1.id,
                recipient_id=user2.id,
                amount=Decimal('50.00'),
                category='Office Supplies',
                note='Office supplies'
            )
            transaction2.mark_as_processed()
            
            db.session.add_all([transaction1, transaction2])
            db.session.commit()
            
            # Test filtering by minimum amount
            history = AccountService.get_transaction_history(
                user1.id,
                filters={'min_amount': Decimal('30.00')}
            )
            
            assert len(history['transactions']) == 1
            assert history['transactions'][0]['amount'] == '50.00'
            
            # Test filtering by category
            history = AccountService.get_transaction_history(
                user1.id,
                filters={'category': 'Lunch'}
            )
            
            assert len(history['transactions']) == 1
            assert history['transactions'][0]['category'] == 'Lunch'
    
    def test_get_account_summary(self, app):
        """Test getting account summary"""
        with app.app_context():
            # Create user and account
            user = User(microsoft_id='test-123', email='test@test.com', name='Test User')
            db.session.add(user)
            db.session.flush()
            
            account = Account(user_id=user.id, balance=Decimal('100.00'))
            db.session.add(account)
            db.session.commit()
            
            # Test getting summary
            summary = AccountService.get_account_summary(user.id)
            
            assert summary['user_id'] == user.id
            assert summary['current_balance'] == '100.00'
            assert summary['available_balance'] == '350.00'
            assert summary['currency'] == 'GBP'
            assert 'account_limits' in summary
            assert 'recent_activity' in summary
            assert 'warnings' in summary
    
    def test_get_spending_analytics(self, app):
        """Test getting spending analytics"""
        with app.app_context():
            # Create users and accounts
            user1 = User(microsoft_id='user1', email='user1@test.com', name='User 1')
            user2 = User(microsoft_id='user2', email='user2@test.com', name='User 2')
            db.session.add_all([user1, user2])
            db.session.flush()
            
            account1 = Account(user_id=user1.id, balance=Decimal('200.00'))
            account2 = Account(user_id=user2.id, balance=Decimal('50.00'))
            db.session.add_all([account1, account2])
            db.session.flush()
            
            # Create transactions in different categories
            lunch_transaction = Transaction.create_transfer(
                sender_id=user1.id,
                recipient_id=user2.id,
                amount=Decimal('25.00'),
                category='Lunch',
                note='Lunch payment'
            )
            lunch_transaction.mark_as_processed()
            
            office_transaction = Transaction.create_transfer(
                sender_id=user1.id,
                recipient_id=user2.id,
                amount=Decimal('50.00'),
                category='Office Supplies',
                note='Office supplies'
            )
            office_transaction.mark_as_processed()
            
            db.session.add_all([lunch_transaction, office_transaction])
            db.session.commit()
            
            # Test getting analytics
            analytics = AccountService.get_spending_analytics(user1.id, period_days=30)
            
            assert analytics['total_spent'] == '75.00'
            assert analytics['total_transactions'] == 2
            assert len(analytics['categories']) == 2
            
            # Check categories are sorted by amount (descending)
            categories = analytics['categories']
            assert categories[0]['category'] == 'Office Supplies'
            assert categories[0]['total_amount'] == '50.00'
            assert categories[1]['category'] == 'Lunch'
            assert categories[1]['total_amount'] == '25.00'
    
    def test_check_account_status_healthy(self, app):
        """Test checking healthy account status"""
        with app.app_context():
            # Create user and account with good balance
            user = User(microsoft_id='test-123', email='test@test.com', name='Test User')
            db.session.add(user)
            db.session.flush()
            
            account = Account(user_id=user.id, balance=Decimal('100.00'))
            db.session.add(account)
            db.session.commit()
            
            # Test status check
            status = AccountService.check_account_status(user.id)
            
            assert status['account_status'] == 'HEALTHY'
            assert status['balance_status'] == 'NORMAL'
            assert len(status['issues']) == 0
    
    def test_check_account_status_overdraft(self, app):
        """Test checking account status with overdraft"""
        with app.app_context():
            # Create user and account with negative balance
            user = User(microsoft_id='test-123', email='test@test.com', name='Test User')
            db.session.add(user)
            db.session.flush()
            
            account = Account(user_id=user.id, balance=Decimal('-50.00'))
            db.session.add(account)
            db.session.commit()
            
            # Test status check
            status = AccountService.check_account_status(user.id)
            
            assert status['balance_status'] == 'OVERDRAFT'
            assert len(status['issues']) == 1
            assert 'overdraft' in status['issues'][0].lower()
            assert len(status['recommendations']) > 0
    
    def test_check_account_status_low_balance(self, app):
        """Test checking account status with low balance"""
        with app.app_context():
            # Create user and account with low balance
            user = User(microsoft_id='test-123', email='test@test.com', name='Test User')
            db.session.add(user)
            db.session.flush()
            
            account = Account(user_id=user.id, balance=Decimal('25.00'))  # Below warning threshold
            db.session.add(account)
            db.session.commit()
            
            # Test status check
            status = AccountService.check_account_status(user.id)
            
            assert status['balance_status'] == 'LOW'
            assert len(status['issues']) == 1
            assert 'low' in status['issues'][0].lower()
            assert len(status['recommendations']) > 0