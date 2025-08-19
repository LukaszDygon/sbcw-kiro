"""
Tests for Accounts API endpoints
"""
import pytest
import json
from decimal import Decimal
from flask_jwt_extended import create_access_token
from models import db, User, Account, Transaction, TransactionType

class TestAccountsAPI:
    """Test cases for Accounts API"""
    
    def test_get_balance_success(self, client, app):
        """Test getting account balance"""
        with app.app_context():
            # Create user and account
            user = User(microsoft_id='test-123', email='test@test.com', name='Test User')
            db.session.add(user)
            db.session.flush()
            
            account = Account(user_id=user.id, balance=Decimal('100.00'))
            db.session.add(account)
            db.session.commit()
            
            # Create access token
            access_token = create_access_token(identity=user.id)
            
            # Test getting balance
            response = client.get('/api/accounts/balance',
                                headers={'Authorization': f'Bearer {access_token}'})
            
            assert response.status_code == 200
            data = json.loads(response.data)
            
            assert data['balance'] == '100.00'
            assert data['available_balance'] == '350.00'
            assert data['currency'] == 'GBP'
            assert 'limits' in data
    
    def test_get_balance_no_token(self, client, app):
        """Test getting balance without authentication"""
        with app.app_context():
            response = client.get('/api/accounts/balance')
            
            assert response.status_code == 401
    
    def test_get_account_summary_success(self, client, app):
        """Test getting account summary"""
        with app.app_context():
            # Create user and account
            user = User(microsoft_id='test-123', email='test@test.com', name='Test User')
            db.session.add(user)
            db.session.flush()
            
            account = Account(user_id=user.id, balance=Decimal('150.00'))
            db.session.add(account)
            db.session.commit()
            
            # Create access token
            access_token = create_access_token(identity=user.id)
            
            # Test getting summary
            response = client.get('/api/accounts/summary',
                                headers={'Authorization': f'Bearer {access_token}'})
            
            assert response.status_code == 200
            data = json.loads(response.data)
            
            assert data['user_id'] == user.id
            assert data['current_balance'] == '150.00'
            assert 'account_limits' in data
            assert 'recent_activity' in data
            assert 'warnings' in data
    
    def test_get_transaction_history_success(self, client, app):
        """Test getting transaction history"""
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
            
            # Create transaction
            transaction = Transaction.create_transfer(
                sender_id=user1.id,
                recipient_id=user2.id,
                amount=Decimal('25.00'),
                note='Test transfer'
            )
            transaction.mark_as_processed()
            db.session.add(transaction)
            db.session.commit()
            
            # Create access token
            access_token = create_access_token(identity=user1.id)
            
            # Test getting history
            response = client.get('/api/accounts/history',
                                headers={'Authorization': f'Bearer {access_token}'})
            
            assert response.status_code == 200
            data = json.loads(response.data)
            
            assert 'transactions' in data
            assert 'pagination' in data
            assert len(data['transactions']) == 1
            assert data['transactions'][0]['amount'] == '25.00'
            assert data['transactions'][0]['direction'] == 'outgoing'
    
    def test_get_transaction_history_with_filters(self, client, app):
        """Test getting transaction history with filters"""
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
            
            # Create transactions
            transaction1 = Transaction.create_transfer(
                sender_id=user1.id,
                recipient_id=user2.id,
                amount=Decimal('25.00'),
                category='Lunch'
            )
            transaction1.mark_as_processed()
            
            transaction2 = Transaction.create_transfer(
                sender_id=user1.id,
                recipient_id=user2.id,
                amount=Decimal('50.00'),
                category='Office'
            )
            transaction2.mark_as_processed()
            
            db.session.add_all([transaction1, transaction2])
            db.session.commit()
            
            # Create access token
            access_token = create_access_token(identity=user1.id)
            
            # Test filtering by minimum amount
            response = client.get('/api/accounts/history?min_amount=30.00',
                                headers={'Authorization': f'Bearer {access_token}'})
            
            assert response.status_code == 200
            data = json.loads(response.data)
            
            assert len(data['transactions']) == 1
            assert data['transactions'][0]['amount'] == '50.00'
    
    def test_get_transaction_history_invalid_date(self, client, app):
        """Test getting transaction history with invalid date format"""
        with app.app_context():
            # Create user and account
            user = User(microsoft_id='test-123', email='test@test.com', name='Test User')
            db.session.add(user)
            db.session.flush()
            
            account = Account(user_id=user.id, balance=Decimal('100.00'))
            db.session.add(account)
            db.session.commit()
            
            # Create access token
            access_token = create_access_token(identity=user.id)
            
            # Test with invalid date format
            response = client.get('/api/accounts/history?start_date=invalid-date',
                                headers={'Authorization': f'Bearer {access_token}'})
            
            assert response.status_code == 400
            data = json.loads(response.data)
            
            assert data['error']['code'] == 'INVALID_DATE_FORMAT'
    
    def test_get_spending_analytics_success(self, client, app):
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
            
            # Create transactions
            transaction = Transaction.create_transfer(
                sender_id=user1.id,
                recipient_id=user2.id,
                amount=Decimal('25.00'),
                category='Lunch'
            )
            transaction.mark_as_processed()
            db.session.add(transaction)
            db.session.commit()
            
            # Create access token
            access_token = create_access_token(identity=user1.id)
            
            # Test getting analytics
            response = client.get('/api/accounts/analytics',
                                headers={'Authorization': f'Bearer {access_token}'})
            
            assert response.status_code == 200
            data = json.loads(response.data)
            
            assert 'total_spent' in data
            assert 'categories' in data
            assert data['total_spent'] == '25.00'
            assert len(data['categories']) == 1
            assert data['categories'][0]['category'] == 'Lunch'
    
    def test_get_spending_analytics_invalid_period(self, client, app):
        """Test getting analytics with invalid period"""
        with app.app_context():
            # Create user and account
            user = User(microsoft_id='test-123', email='test@test.com', name='Test User')
            db.session.add(user)
            db.session.flush()
            
            account = Account(user_id=user.id, balance=Decimal('100.00'))
            db.session.add(account)
            db.session.commit()
            
            # Create access token
            access_token = create_access_token(identity=user.id)
            
            # Test with invalid period
            response = client.get('/api/accounts/analytics?period_days=500',
                                headers={'Authorization': f'Bearer {access_token}'})
            
            assert response.status_code == 400
            data = json.loads(response.data)
            
            assert data['error']['code'] == 'INVALID_PERIOD'
    
    def test_validate_transaction_amount_success(self, client, app):
        """Test validating transaction amount"""
        with app.app_context():
            # Create user and account
            user = User(microsoft_id='test-123', email='test@test.com', name='Test User')
            db.session.add(user)
            db.session.flush()
            
            account = Account(user_id=user.id, balance=Decimal('100.00'))
            db.session.add(account)
            db.session.commit()
            
            # Create access token
            access_token = create_access_token(identity=user.id)
            
            # Test validating amount
            response = client.post('/api/accounts/validate-amount',
                                 json={'amount': '-50.00'},
                                 headers={'Authorization': f'Bearer {access_token}'})
            
            assert response.status_code == 200
            data = json.loads(response.data)
            
            assert data['valid'] is True
            assert data['current_balance'] == '100.00'
            assert data['new_balance'] == '50.00'
    
    def test_validate_transaction_amount_invalid(self, client, app):
        """Test validating invalid transaction amount"""
        with app.app_context():
            # Create user and account
            user = User(microsoft_id='test-123', email='test@test.com', name='Test User')
            db.session.add(user)
            db.session.flush()
            
            account = Account(user_id=user.id, balance=Decimal('100.00'))
            db.session.add(account)
            db.session.commit()
            
            # Create access token
            access_token = create_access_token(identity=user.id)
            
            # Test validating amount that would exceed limits
            response = client.post('/api/accounts/validate-amount',
                                 json={'amount': '-400.00'},
                                 headers={'Authorization': f'Bearer {access_token}'})
            
            assert response.status_code == 200
            data = json.loads(response.data)
            
            assert data['valid'] is False
            assert len(data['errors']) == 1
            assert data['errors'][0]['code'] == 'INSUFFICIENT_FUNDS'
    
    def test_validate_transaction_amount_missing_data(self, client, app):
        """Test validating amount with missing data"""
        with app.app_context():
            # Create user and account
            user = User(microsoft_id='test-123', email='test@test.com', name='Test User')
            db.session.add(user)
            db.session.flush()
            
            account = Account(user_id=user.id, balance=Decimal('100.00'))
            db.session.add(account)
            db.session.commit()
            
            # Create access token
            access_token = create_access_token(identity=user.id)
            
            # Test with missing amount
            response = client.post('/api/accounts/validate-amount',
                                 json={},
                                 headers={'Authorization': f'Bearer {access_token}'})
            
            assert response.status_code == 400
            data = json.loads(response.data)
            
            assert data['error']['code'] == 'MISSING_FIELDS'
    
    def test_get_account_status_success(self, client, app):
        """Test getting account status"""
        with app.app_context():
            # Create user and account
            user = User(microsoft_id='test-123', email='test@test.com', name='Test User')
            db.session.add(user)
            db.session.flush()
            
            account = Account(user_id=user.id, balance=Decimal('100.00'))
            db.session.add(account)
            db.session.commit()
            
            # Create access token
            access_token = create_access_token(identity=user.id)
            
            # Test getting status
            response = client.get('/api/accounts/status',
                                headers={'Authorization': f'Bearer {access_token}'})
            
            assert response.status_code == 200
            data = json.loads(response.data)
            
            assert 'account_status' in data
            assert 'balance_status' in data
            assert 'issues' in data
            assert 'recommendations' in data
    
    def test_get_account_limits_success(self, client, app):
        """Test getting account limits"""
        with app.app_context():
            # Create user and account
            user = User(microsoft_id='test-123', email='test@test.com', name='Test User')
            db.session.add(user)
            db.session.flush()
            
            account = Account(user_id=user.id, balance=Decimal('100.00'))
            db.session.add(account)
            db.session.commit()
            
            # Create access token
            access_token = create_access_token(identity=user.id)
            
            # Test getting limits
            response = client.get('/api/accounts/limits',
                                headers={'Authorization': f'Bearer {access_token}'})
            
            assert response.status_code == 200
            data = json.loads(response.data)
            
            assert 'limits' in data
            assert 'currency' in data
            assert 'description' in data
            assert data['limits']['minimum_balance'] == '-250.00'
            assert data['limits']['maximum_balance'] == '250.00'
            assert data['currency'] == 'GBP'