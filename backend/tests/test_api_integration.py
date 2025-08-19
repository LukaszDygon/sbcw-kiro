"""
Comprehensive API integration tests for SoftBankCashWire
"""
import pytest
import json
from decimal import Decimal
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from models import (
    db, User, UserRole, AccountStatus, Account, 
    Transaction, TransactionType, EventAccount, EventStatus,
    MoneyRequest, RequestStatus
)

class TestAuthAPIIntegration:
    """Integration tests for authentication API"""
    
    @patch('services.auth_service.requests.post')
    @patch('services.auth_service.requests.get')
    def test_microsoft_sso_login_flow(self, mock_get, mock_post, client, app):
        """Test complete Microsoft SSO login flow"""
        with app.app_context():
            # Mock token exchange
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = {
                'access_token': 'test-access-token',
                'token_type': 'Bearer',
                'expires_in': 3600
            }
            
            # Mock user info retrieval
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = {
                'id': 'microsoft-123',
                'mail': 'test@company.com',
                'displayName': 'Test User'
            }
            
            # Test login endpoint
            response = client.post('/api/auth/login', json={
                'code': 'auth-code',
                'redirect_uri': 'http://localhost:3000/callback'
            })
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True
            assert 'access_token' in data
            assert data['user']['name'] == 'Test User'
            assert data['user']['email'] == 'test@company.com'
            
            # Verify user was created in database
            user = User.query.filter_by(microsoft_id='microsoft-123').first()
            assert user is not None
            assert user.name == 'Test User'
            assert user.email == 'test@company.com'
            
            # Verify account was created
            account = Account.query.filter_by(user_id=user.id).first()
            assert account is not None
            assert account.balance == Decimal('0.00')
    
    def test_protected_endpoint_without_token(self, client, app):
        """Test accessing protected endpoint without token"""
        with app.app_context():
            response = client.get('/api/accounts/balance')
            assert response.status_code == 401
            
            data = response.get_json()
            assert 'error' in data
            assert 'token' in data['error']['message'].lower()
    
    def test_protected_endpoint_with_invalid_token(self, client, app):
        """Test accessing protected endpoint with invalid token"""
        with app.app_context():
            headers = {'Authorization': 'Bearer invalid-token'}
            response = client.get('/api/accounts/balance', headers=headers)
            assert response.status_code == 401
    
    @patch('services.auth_service.jwt.decode')
    def test_protected_endpoint_with_valid_token(self, mock_decode, client, app):
        """Test accessing protected endpoint with valid token"""
        with app.app_context():
            # Create user and account
            user = User(microsoft_id='test-123', email='test@test.com', name='Test User')
            db.session.add(user)
            db.session.flush()
            
            account = Account(user_id=user.id, balance=Decimal('100.00'))
            db.session.add(account)
            db.session.commit()
            
            # Mock JWT decode
            mock_decode.return_value = {'user_id': user.id}
            
            headers = {'Authorization': 'Bearer valid-token'}
            response = client.get('/api/accounts/balance', headers=headers)
            assert response.status_code == 200
            
            data = response.get_json()
            assert data['balance'] == '100.00'


class TestAccountAPIIntegration:
    """Integration tests for account API"""
    
    def setup_authenticated_user(self, app):
        """Helper to set up authenticated user"""
        user = User(microsoft_id='test-123', email='test@test.com', name='Test User')
        db.session.add(user)
        db.session.flush()
        
        account = Account(user_id=user.id, balance=Decimal('150.00'))
        db.session.add(account)
        db.session.commit()
        
        return user
    
    @patch('services.auth_service.jwt.decode')
    def test_get_account_balance(self, mock_decode, client, app):
        """Test getting account balance"""
        with app.app_context():
            user = self.setup_authenticated_user(app)
            mock_decode.return_value = {'user_id': user.id}
            
            headers = {'Authorization': 'Bearer valid-token'}
            response = client.get('/api/accounts/balance', headers=headers)
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['balance'] == '150.00'
            assert data['currency'] == 'GBP'
    
    @patch('services.auth_service.jwt.decode')
    def test_get_transaction_history(self, mock_decode, client, app):
        """Test getting transaction history"""
        with app.app_context():
            # Create users
            user1 = User(microsoft_id='user1', email='user1@test.com', name='User 1')
            user2 = User(microsoft_id='user2', email='user2@test.com', name='User 2')
            db.session.add_all([user1, user2])
            db.session.flush()
            
            account1 = Account(user_id=user1.id, balance=Decimal('100.00'))
            account2 = Account(user_id=user2.id, balance=Decimal('50.00'))
            db.session.add_all([account1, account2])
            db.session.flush()
            
            # Create transactions
            transaction = Transaction.create_transfer(
                sender_id=user1.id,
                recipient_id=user2.id,
                amount=Decimal('25.00'),
                note='Test payment'
            )
            transaction.mark_as_processed()
            db.session.add(transaction)
            db.session.commit()
            
            mock_decode.return_value = {'user_id': user1.id}
            
            headers = {'Authorization': 'Bearer valid-token'}
            response = client.get('/api/accounts/transactions', headers=headers)
            
            assert response.status_code == 200
            data = response.get_json()
            assert len(data['transactions']) == 1
            assert data['transactions'][0]['amount'] == '25.00'
            assert data['transactions'][0]['recipient_name'] == 'User 2'
    
    @patch('services.auth_service.jwt.decode')
    def test_get_transaction_history_with_filters(self, mock_decode, client, app):
        """Test getting transaction history with filters"""
        with app.app_context():
            user = self.setup_authenticated_user(app)
            mock_decode.return_value = {'user_id': user.id}
            
            headers = {'Authorization': 'Bearer valid-token'}
            query_params = {
                'start_date': '2024-01-01',
                'end_date': '2024-12-31',
                'min_amount': '10.00',
                'max_amount': '100.00',
                'limit': '10'
            }
            
            response = client.get('/api/accounts/transactions', 
                                headers=headers, 
                                query_string=query_params)
            
            assert response.status_code == 200
            data = response.get_json()
            assert 'transactions' in data
            assert 'pagination' in data


class TestTransactionAPIIntegration:
    """Integration tests for transaction API"""
    
    def setup_users_with_accounts(self, app):
        """Helper to set up users with accounts"""
        sender = User(microsoft_id='sender', email='sender@test.com', name='Sender')
        recipient = User(microsoft_id='recipient', email='recipient@test.com', name='Recipient')
        db.session.add_all([sender, recipient])
        db.session.flush()
        
        sender_account = Account(user_id=sender.id, balance=Decimal('200.00'))
        recipient_account = Account(user_id=recipient.id, balance=Decimal('50.00'))
        db.session.add_all([sender_account, recipient_account])
        db.session.commit()
        
        return sender, recipient
    
    @patch('services.auth_service.jwt.decode')
    def test_send_money_success(self, mock_decode, client, app):
        """Test successful money transfer"""
        with app.app_context():
            sender, recipient = self.setup_users_with_accounts(app)
            mock_decode.return_value = {'user_id': sender.id}
            
            headers = {'Authorization': 'Bearer valid-token'}
            payload = {
                'recipient_id': recipient.id,
                'amount': '25.00',
                'category': 'Lunch',
                'note': 'Lunch payment'
            }
            
            response = client.post('/api/transactions/send', 
                                 headers=headers, 
                                 json=payload)
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True
            assert data['transaction']['amount'] == '25.00'
            assert data['sender_balance'] == '175.00'
            assert data['recipient_balance'] == '75.00'
            
            # Verify database changes
            sender_account = Account.query.filter_by(user_id=sender.id).first()
            recipient_account = Account.query.filter_by(user_id=recipient.id).first()
            assert sender_account.balance == Decimal('175.00')
            assert recipient_account.balance == Decimal('75.00')
    
    @patch('services.auth_service.jwt.decode')
    def test_send_money_insufficient_funds(self, mock_decode, client, app):
        """Test money transfer with insufficient funds"""
        with app.app_context():
            sender, recipient = self.setup_users_with_accounts(app)
            mock_decode.return_value = {'user_id': sender.id}
            
            headers = {'Authorization': 'Bearer valid-token'}
            payload = {
                'recipient_id': recipient.id,
                'amount': '500.00',  # Exceeds balance + overdraft
                'note': 'Large payment'
            }
            
            response = client.post('/api/transactions/send', 
                                 headers=headers, 
                                 json=payload)
            
            assert response.status_code == 400
            data = response.get_json()
            assert 'error' in data
            assert 'insufficient' in data['error']['message'].lower()
    
    @patch('services.auth_service.jwt.decode')
    def test_send_bulk_money(self, mock_decode, client, app):
        """Test bulk money transfer"""
        with app.app_context():
            # Create sender and multiple recipients
            sender = User(microsoft_id='sender', email='sender@test.com', name='Sender')
            recipient1 = User(microsoft_id='rec1', email='rec1@test.com', name='Recipient 1')
            recipient2 = User(microsoft_id='rec2', email='rec2@test.com', name='Recipient 2')
            db.session.add_all([sender, recipient1, recipient2])
            db.session.flush()
            
            sender_account = Account(user_id=sender.id, balance=Decimal('200.00'))
            rec1_account = Account(user_id=recipient1.id, balance=Decimal('50.00'))
            rec2_account = Account(user_id=recipient2.id, balance=Decimal('30.00'))
            db.session.add_all([sender_account, rec1_account, rec2_account])
            db.session.commit()
            
            mock_decode.return_value = {'user_id': sender.id}
            
            headers = {'Authorization': 'Bearer valid-token'}
            payload = {
                'recipients': [
                    {
                        'recipient_id': recipient1.id,
                        'amount': '25.00',
                        'category': 'Lunch',
                        'note': 'Lunch split'
                    },
                    {
                        'recipient_id': recipient2.id,
                        'amount': '30.00',
                        'category': 'Lunch',
                        'note': 'Lunch split'
                    }
                ]
            }
            
            response = client.post('/api/transactions/send-bulk', 
                                 headers=headers, 
                                 json=payload)
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True
            assert data['total_amount'] == '55.00'
            assert data['recipient_count'] == 2
            assert len(data['transactions']) == 2
    
    @patch('services.auth_service.jwt.decode')
    def test_validate_transaction(self, mock_decode, client, app):
        """Test transaction validation endpoint"""
        with app.app_context():
            sender, recipient = self.setup_users_with_accounts(app)
            mock_decode.return_value = {'user_id': sender.id}
            
            headers = {'Authorization': 'Bearer valid-token'}
            payload = {
                'recipient_id': recipient.id,
                'amount': '25.00',
                'transaction_type': 'transfer'
            }
            
            response = client.post('/api/transactions/validate', 
                                 headers=headers, 
                                 json=payload)
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['valid'] is True
            assert len(data['errors']) == 0


class TestMoneyRequestAPIIntegration:
    """Integration tests for money request API"""
    
    def setup_users_with_accounts(self, app):
        """Helper to set up users with accounts"""
        requester = User(microsoft_id='requester', email='requester@test.com', name='Requester')
        recipient = User(microsoft_id='recipient', email='recipient@test.com', name='Recipient')
        db.session.add_all([requester, recipient])
        db.session.flush()
        
        requester_account = Account(user_id=requester.id, balance=Decimal('50.00'))
        recipient_account = Account(user_id=recipient.id, balance=Decimal('100.00'))
        db.session.add_all([requester_account, recipient_account])
        db.session.commit()
        
        return requester, recipient
    
    @patch('services.auth_service.jwt.decode')
    def test_create_money_request(self, mock_decode, client, app):
        """Test creating money request"""
        with app.app_context():
            requester, recipient = self.setup_users_with_accounts(app)
            mock_decode.return_value = {'user_id': requester.id}
            
            headers = {'Authorization': 'Bearer valid-token'}
            payload = {
                'recipient_id': recipient.id,
                'amount': '25.00',
                'note': 'Lunch money',
                'expires_in_days': 7
            }
            
            response = client.post('/api/money-requests/create', 
                                 headers=headers, 
                                 json=payload)
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True
            assert data['request']['amount'] == '25.00'
            assert data['request']['status'] == RequestStatus.PENDING.value
            
            # Verify database
            request = MoneyRequest.query.filter_by(
                requester_id=requester.id,
                recipient_id=recipient.id
            ).first()
            assert request is not None
            assert request.amount == Decimal('25.00')
    
    @patch('services.auth_service.jwt.decode')
    def test_approve_money_request(self, mock_decode, client, app):
        """Test approving money request"""
        with app.app_context():
            requester, recipient = self.setup_users_with_accounts(app)
            
            # Create money request
            request = MoneyRequest(
                requester_id=requester.id,
                recipient_id=recipient.id,
                amount=Decimal('25.00'),
                note='Lunch money',
                expires_at=datetime.utcnow() + timedelta(days=7)
            )
            db.session.add(request)
            db.session.commit()
            
            mock_decode.return_value = {'user_id': recipient.id}
            
            headers = {'Authorization': 'Bearer valid-token'}
            response = client.post(f'/api/money-requests/{request.id}/approve', 
                                 headers=headers)
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True
            
            # Verify request status and balances
            updated_request = MoneyRequest.query.get(request.id)
            assert updated_request.status == RequestStatus.APPROVED
            
            requester_account = Account.query.filter_by(user_id=requester.id).first()
            recipient_account = Account.query.filter_by(user_id=recipient.id).first()
            assert requester_account.balance == Decimal('75.00')  # 50 + 25
            assert recipient_account.balance == Decimal('75.00')   # 100 - 25
    
    @patch('services.auth_service.jwt.decode')
    def test_decline_money_request(self, mock_decode, client, app):
        """Test declining money request"""
        with app.app_context():
            requester, recipient = self.setup_users_with_accounts(app)
            
            # Create money request
            request = MoneyRequest(
                requester_id=requester.id,
                recipient_id=recipient.id,
                amount=Decimal('25.00'),
                expires_at=datetime.utcnow() + timedelta(days=7)
            )
            db.session.add(request)
            db.session.commit()
            
            mock_decode.return_value = {'user_id': recipient.id}
            
            headers = {'Authorization': 'Bearer valid-token'}
            response = client.post(f'/api/money-requests/{request.id}/decline', 
                                 headers=headers)
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True
            
            # Verify request status and balances unchanged
            updated_request = MoneyRequest.query.get(request.id)
            assert updated_request.status == RequestStatus.DECLINED
            
            requester_account = Account.query.filter_by(user_id=requester.id).first()
            recipient_account = Account.query.filter_by(user_id=recipient.id).first()
            assert requester_account.balance == Decimal('50.00')  # Unchanged
            assert recipient_account.balance == Decimal('100.00') # Unchanged
    
    @patch('services.auth_service.jwt.decode')
    def test_get_money_requests(self, mock_decode, client, app):
        """Test getting money requests"""
        with app.app_context():
            requester, recipient = self.setup_users_with_accounts(app)
            
            # Create money requests
            request1 = MoneyRequest(
                requester_id=requester.id,
                recipient_id=recipient.id,
                amount=Decimal('25.00'),
                expires_at=datetime.utcnow() + timedelta(days=7)
            )
            request2 = MoneyRequest(
                requester_id=recipient.id,
                recipient_id=requester.id,
                amount=Decimal('15.00'),
                expires_at=datetime.utcnow() + timedelta(days=5)
            )
            db.session.add_all([request1, request2])
            db.session.commit()
            
            mock_decode.return_value = {'user_id': recipient.id}
            
            headers = {'Authorization': 'Bearer valid-token'}
            response = client.get('/api/money-requests', headers=headers)
            
            assert response.status_code == 200
            data = response.get_json()
            assert len(data['received_requests']) == 1
            assert len(data['sent_requests']) == 1
            assert data['received_requests'][0]['amount'] == '25.00'
            assert data['sent_requests'][0]['amount'] == '15.00'


class TestEventAPIIntegration:
    """Integration tests for event API"""
    
    def setup_users_with_accounts(self, app):
        """Helper to set up users with accounts"""
        creator = User(microsoft_id='creator', email='creator@test.com', name='Creator')
        contributor = User(microsoft_id='contributor', email='contributor@test.com', name='Contributor')
        db.session.add_all([creator, contributor])
        db.session.flush()
        
        creator_account = Account(user_id=creator.id, balance=Decimal('100.00'))
        contributor_account = Account(user_id=contributor.id, balance=Decimal('150.00'))
        db.session.add_all([creator_account, contributor_account])
        db.session.commit()
        
        return creator, contributor
    
    @patch('services.auth_service.jwt.decode')
    def test_create_event_account(self, mock_decode, client, app):
        """Test creating event account"""
        with app.app_context():
            creator, _ = self.setup_users_with_accounts(app)
            mock_decode.return_value = {'user_id': creator.id}
            
            headers = {'Authorization': 'Bearer valid-token'}
            payload = {
                'name': 'Team Lunch',
                'description': 'Monthly team lunch gathering',
                'target_amount': '200.00',
                'deadline_days': 7
            }
            
            response = client.post('/api/events/create', 
                                 headers=headers, 
                                 json=payload)
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True
            assert data['event']['name'] == 'Team Lunch'
            assert data['event']['target_amount'] == '200.00'
            assert data['event']['status'] == EventStatus.ACTIVE.value
    
    @patch('services.auth_service.jwt.decode')
    def test_contribute_to_event(self, mock_decode, client, app):
        """Test contributing to event"""
        with app.app_context():
            creator, contributor = self.setup_users_with_accounts(app)
            
            # Create event
            event = EventAccount(
                creator_id=creator.id,
                name='Team Event',
                description='Test event',
                target_amount=Decimal('100.00')
            )
            db.session.add(event)
            db.session.commit()
            
            mock_decode.return_value = {'user_id': contributor.id}
            
            headers = {'Authorization': 'Bearer valid-token'}
            payload = {
                'amount': '30.00',
                'note': 'Happy to contribute!'
            }
            
            response = client.post(f'/api/events/{event.id}/contribute', 
                                 headers=headers, 
                                 json=payload)
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True
            assert data['contribution']['amount'] == '30.00'
            assert data['contributor_balance'] == '120.00'
            assert data['event_total'] == '30.00'
    
    @patch('services.auth_service.jwt.decode')
    def test_get_active_events(self, mock_decode, client, app):
        """Test getting active events"""
        with app.app_context():
            creator, _ = self.setup_users_with_accounts(app)
            
            # Create events
            active_event = EventAccount(
                creator_id=creator.id,
                name='Active Event',
                description='Active event description',
                status=EventStatus.ACTIVE
            )
            closed_event = EventAccount(
                creator_id=creator.id,
                name='Closed Event',
                description='Closed event description',
                status=EventStatus.CLOSED
            )
            db.session.add_all([active_event, closed_event])
            db.session.commit()
            
            mock_decode.return_value = {'user_id': creator.id}
            
            headers = {'Authorization': 'Bearer valid-token'}
            response = client.get('/api/events', headers=headers)
            
            assert response.status_code == 200
            data = response.get_json()
            assert len(data['events']) == 1  # Only active events
            assert data['events'][0]['name'] == 'Active Event'
    
    @patch('services.auth_service.jwt.decode')
    def test_close_event_account(self, mock_decode, client, app):
        """Test closing event account"""
        with app.app_context():
            creator, _ = self.setup_users_with_accounts(app)
            creator.role = UserRole.FINANCE  # Give finance permissions
            db.session.commit()
            
            # Create event
            event = EventAccount(
                creator_id=creator.id,
                name='Test Event',
                description='Test event'
            )
            db.session.add(event)
            db.session.commit()
            
            mock_decode.return_value = {'user_id': creator.id}
            
            headers = {'Authorization': 'Bearer valid-token'}
            payload = {
                'closure_reason': 'Event completed successfully'
            }
            
            response = client.post(f'/api/events/{event.id}/close', 
                                 headers=headers, 
                                 json=payload)
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True
            assert data['event']['status'] == EventStatus.CLOSED.value


class TestReportingAPIIntegration:
    """Integration tests for reporting API"""
    
    def setup_finance_user(self, app):
        """Helper to set up finance user"""
        finance_user = User(
            microsoft_id='finance', 
            email='finance@test.com', 
            name='Finance User',
            role=UserRole.FINANCE
        )
        db.session.add(finance_user)
        db.session.flush()
        
        finance_account = Account(user_id=finance_user.id, balance=Decimal('1000.00'))
        db.session.add(finance_account)
        db.session.commit()
        
        return finance_user
    
    @patch('services.auth_service.jwt.decode')
    def test_get_transaction_report(self, mock_decode, client, app):
        """Test getting transaction report"""
        with app.app_context():
            finance_user = self.setup_finance_user(app)
            mock_decode.return_value = {'user_id': finance_user.id}
            
            headers = {'Authorization': 'Bearer valid-token'}
            query_params = {
                'start_date': '2024-01-01',
                'end_date': '2024-12-31',
                'report_type': 'summary'
            }
            
            response = client.get('/api/reports/transactions', 
                                headers=headers, 
                                query_string=query_params)
            
            assert response.status_code == 200
            data = response.get_json()
            assert 'report' in data
            assert 'summary' in data['report']
            assert 'transactions' in data['report']
    
    @patch('services.auth_service.jwt.decode')
    def test_get_user_activity_report(self, mock_decode, client, app):
        """Test getting user activity report"""
        with app.app_context():
            finance_user = self.setup_finance_user(app)
            mock_decode.return_value = {'user_id': finance_user.id}
            
            headers = {'Authorization': 'Bearer valid-token'}
            query_params = {
                'start_date': '2024-01-01',
                'end_date': '2024-12-31'
            }
            
            response = client.get('/api/reports/user-activity', 
                                headers=headers, 
                                query_string=query_params)
            
            assert response.status_code == 200
            data = response.get_json()
            assert 'report' in data
            assert 'user_statistics' in data['report']
    
    @patch('services.auth_service.jwt.decode')
    def test_export_report_csv(self, mock_decode, client, app):
        """Test exporting report as CSV"""
        with app.app_context():
            finance_user = self.setup_finance_user(app)
            mock_decode.return_value = {'user_id': finance_user.id}
            
            headers = {'Authorization': 'Bearer valid-token'}
            payload = {
                'report_type': 'transactions',
                'start_date': '2024-01-01',
                'end_date': '2024-12-31',
                'format': 'csv'
            }
            
            response = client.post('/api/reports/export', 
                                 headers=headers, 
                                 json=payload)
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True
            assert data['format'] == 'csv'
            assert 'download_url' in data or 'data' in data
    
    @patch('services.auth_service.jwt.decode')
    def test_unauthorized_report_access(self, mock_decode, client, app):
        """Test unauthorized access to reports"""
        with app.app_context():
            # Create regular employee user
            regular_user = User(
                microsoft_id='regular', 
                email='regular@test.com', 
                name='Regular User',
                role=UserRole.EMPLOYEE
            )
            db.session.add(regular_user)
            db.session.commit()
            
            mock_decode.return_value = {'user_id': regular_user.id}
            
            headers = {'Authorization': 'Bearer valid-token'}
            response = client.get('/api/reports/transactions', headers=headers)
            
            assert response.status_code == 403
            data = response.get_json()
            assert 'error' in data
            assert 'permission' in data['error']['message'].lower()


class TestSecurityAPIIntegration:
    """Integration tests for security features"""
    
    @patch('services.auth_service.jwt.decode')
    def test_rate_limiting(self, mock_decode, client, app):
        """Test API rate limiting"""
        with app.app_context():
            user = User(microsoft_id='test', email='test@test.com', name='Test User')
            db.session.add(user)
            db.session.flush()
            
            account = Account(user_id=user.id, balance=Decimal('100.00'))
            db.session.add(account)
            db.session.commit()
            
            mock_decode.return_value = {'user_id': user.id}
            headers = {'Authorization': 'Bearer valid-token'}
            
            # Make multiple rapid requests
            responses = []
            for _ in range(10):
                response = client.get('/api/accounts/balance', headers=headers)
                responses.append(response.status_code)
            
            # Should eventually hit rate limit
            assert any(status == 429 for status in responses[-5:])
    
    def test_input_validation(self, client, app):
        """Test input validation"""
        with app.app_context():
            # Test invalid JSON
            response = client.post('/api/auth/login', 
                                 data='invalid json',
                                 content_type='application/json')
            assert response.status_code == 400
            
            # Test missing required fields
            response = client.post('/api/auth/login', json={})
            assert response.status_code == 400
            
            data = response.get_json()
            assert 'error' in data
    
    @patch('services.auth_service.jwt.decode')
    def test_sql_injection_protection(self, mock_decode, client, app):
        """Test SQL injection protection"""
        with app.app_context():
            user = User(microsoft_id='test', email='test@test.com', name='Test User')
            db.session.add(user)
            db.session.flush()
            
            account = Account(user_id=user.id, balance=Decimal('100.00'))
            db.session.add(account)
            db.session.commit()
            
            mock_decode.return_value = {'user_id': user.id}
            headers = {'Authorization': 'Bearer valid-token'}
            
            # Attempt SQL injection in query parameters
            malicious_query = "'; DROP TABLE users; --"
            response = client.get(f'/api/accounts/transactions?search={malicious_query}', 
                                headers=headers)
            
            # Should not cause server error, should handle gracefully
            assert response.status_code in [200, 400]  # Either works or validates input
            
            # Verify users table still exists by making another request
            response2 = client.get('/api/accounts/balance', headers=headers)
            assert response2.status_code == 200