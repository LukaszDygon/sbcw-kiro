"""
Tests for MoneyRequestService
"""
import pytest
from decimal import Decimal
from datetime import datetime, timedelta
from services.money_request_service import MoneyRequestService
from models import (
    db, User, UserRole, AccountStatus, Account, 
    MoneyRequest, RequestStatus
)

class TestMoneyRequestService:
    """Test cases for MoneyRequestService"""
    
    def test_create_money_request_success(self, app):
        """Test successful money request creation"""
        with app.app_context():
            # Create users and accounts
            requester = User(microsoft_id='requester', email='requester@test.com', name='Requester')
            recipient = User(microsoft_id='recipient', email='recipient@test.com', name='Recipient')
            db.session.add_all([requester, recipient])
            db.session.flush()
            
            requester_account = Account(user_id=requester.id, balance=Decimal('50.00'))
            recipient_account = Account(user_id=recipient.id, balance=Decimal('100.00'))
            db.session.add_all([requester_account, recipient_account])
            db.session.commit()
            
            # Test money request creation
            result = MoneyRequestService.create_money_request(
                requester_id=requester.id,
                recipient_id=recipient.id,
                amount=Decimal('25.00'),
                note='Lunch payment',
                expires_in_days=5
            )
            
            assert result['success'] is True
            assert result['request']['amount'] == '25.00'
            assert result['request']['requester_name'] == 'Requester'
            assert result['request']['recipient_name'] == 'Recipient'
            assert result['request']['note'] == 'Lunch payment'
            assert result['request']['status'] == 'PENDING'
            assert result['expires_in_hours'] > 0
    
    def test_create_money_request_self_request(self, app):
        """Test creating money request to self (should fail)"""
        with app.app_context():
            # Create user and account
            user = User(microsoft_id='user', email='user@test.com', name='User')
            db.session.add(user)
            db.session.flush()
            
            account = Account(user_id=user.id, balance=Decimal('100.00'))
            db.session.add(account)
            db.session.commit()
            
            # Test self request
            with pytest.raises(ValueError, match="Cannot request money from yourself"):
                MoneyRequestService.create_money_request(
                    requester_id=user.id,
                    recipient_id=user.id,
                    amount=Decimal('25.00')
                )
    
    def test_create_money_request_duplicate(self, app):
        """Test creating duplicate money request"""
        with app.app_context():
            # Create users and accounts
            requester = User(microsoft_id='requester', email='requester@test.com', name='Requester')
            recipient = User(microsoft_id='recipient', email='recipient@test.com', name='Recipient')
            db.session.add_all([requester, recipient])
            db.session.flush()
            
            requester_account = Account(user_id=requester.id, balance=Decimal('50.00'))
            recipient_account = Account(user_id=recipient.id, balance=Decimal('100.00'))
            db.session.add_all([requester_account, recipient_account])
            db.session.commit()
            
            # Create first request
            MoneyRequestService.create_money_request(
                requester_id=requester.id,
                recipient_id=recipient.id,
                amount=Decimal('25.00')
            )
            
            # Test duplicate request
            with pytest.raises(ValueError, match="already have a pending request"):
                MoneyRequestService.create_money_request(
                    requester_id=requester.id,
                    recipient_id=recipient.id,
                    amount=Decimal('30.00')
                )
    
    def test_create_money_request_inactive_user(self, app):
        """Test creating request with inactive user"""
        with app.app_context():
            # Create users and accounts
            requester = User(microsoft_id='requester', email='requester@test.com', name='Requester')
            recipient = User(
                microsoft_id='recipient', 
                email='recipient@test.com', 
                name='Recipient',
                account_status=AccountStatus.SUSPENDED
            )
            db.session.add_all([requester, recipient])
            db.session.flush()
            
            requester_account = Account(user_id=requester.id, balance=Decimal('50.00'))
            recipient_account = Account(user_id=recipient.id, balance=Decimal('100.00'))
            db.session.add_all([requester_account, recipient_account])
            db.session.commit()
            
            # Test request to inactive user
            with pytest.raises(ValueError, match="Recipient account not found or inactive"):
                MoneyRequestService.create_money_request(
                    requester_id=requester.id,
                    recipient_id=recipient.id,
                    amount=Decimal('25.00')
                )
    
    def test_respond_to_request_approve(self, app):
        """Test approving a money request"""
        with app.app_context():
            # Create users and accounts
            requester = User(microsoft_id='requester', email='requester@test.com', name='Requester')
            recipient = User(microsoft_id='recipient', email='recipient@test.com', name='Recipient')
            db.session.add_all([requester, recipient])
            db.session.flush()
            
            requester_account = Account(user_id=requester.id, balance=Decimal('50.00'))
            recipient_account = Account(user_id=recipient.id, balance=Decimal('100.00'))
            db.session.add_all([requester_account, recipient_account])
            db.session.commit()
            
            # Create money request
            create_result = MoneyRequestService.create_money_request(
                requester_id=requester.id,
                recipient_id=recipient.id,
                amount=Decimal('25.00'),
                note='Lunch payment'
            )
            
            request_id = create_result['request']['id']
            
            # Test approving request
            result = MoneyRequestService.respond_to_request(
                request_id=request_id,
                user_id=recipient.id,
                approved=True
            )
            
            assert result['success'] is True
            assert result['approved'] is True
            assert result['request']['status'] == 'APPROVED'
            assert 'transaction' in result
            assert result['transaction']['amount'] == '25.00'
            assert result['sender_balance'] == Decimal('75.00')  # Recipient paid
            assert result['recipient_balance'] == Decimal('75.00')  # Requester received
    
    def test_respond_to_request_decline(self, app):
        """Test declining a money request"""
        with app.app_context():
            # Create users and accounts
            requester = User(microsoft_id='requester', email='requester@test.com', name='Requester')
            recipient = User(microsoft_id='recipient', email='recipient@test.com', name='Recipient')
            db.session.add_all([requester, recipient])
            db.session.flush()
            
            requester_account = Account(user_id=requester.id, balance=Decimal('50.00'))
            recipient_account = Account(user_id=recipient.id, balance=Decimal('100.00'))
            db.session.add_all([requester_account, recipient_account])
            db.session.commit()
            
            # Create money request
            create_result = MoneyRequestService.create_money_request(
                requester_id=requester.id,
                recipient_id=recipient.id,
                amount=Decimal('25.00')
            )
            
            request_id = create_result['request']['id']
            
            # Test declining request
            result = MoneyRequestService.respond_to_request(
                request_id=request_id,
                user_id=recipient.id,
                approved=False
            )
            
            assert result['success'] is True
            assert result['approved'] is False
            assert result['request']['status'] == 'DECLINED'
            assert 'transaction' not in result
            assert 'message' in result
    
    def test_respond_to_request_unauthorized(self, app):
        """Test responding to request by unauthorized user"""
        with app.app_context():
            # Create users and accounts
            requester = User(microsoft_id='requester', email='requester@test.com', name='Requester')
            recipient = User(microsoft_id='recipient', email='recipient@test.com', name='Recipient')
            other_user = User(microsoft_id='other', email='other@test.com', name='Other')
            db.session.add_all([requester, recipient, other_user])
            db.session.flush()
            
            requester_account = Account(user_id=requester.id, balance=Decimal('50.00'))
            recipient_account = Account(user_id=recipient.id, balance=Decimal('100.00'))
            other_account = Account(user_id=other_user.id, balance=Decimal('75.00'))
            db.session.add_all([requester_account, recipient_account, other_account])
            db.session.commit()
            
            # Create money request
            create_result = MoneyRequestService.create_money_request(
                requester_id=requester.id,
                recipient_id=recipient.id,
                amount=Decimal('25.00')
            )
            
            request_id = create_result['request']['id']
            
            # Test responding as unauthorized user
            with pytest.raises(ValueError, match="not authorized to respond"):
                MoneyRequestService.respond_to_request(
                    request_id=request_id,
                    user_id=other_user.id,
                    approved=True
                )
    
    def test_respond_to_request_expired(self, app):
        """Test responding to expired request"""
        with app.app_context():
            # Create users and accounts
            requester = User(microsoft_id='requester', email='requester@test.com', name='Requester')
            recipient = User(microsoft_id='recipient', email='recipient@test.com', name='Recipient')
            db.session.add_all([requester, recipient])
            db.session.flush()
            
            requester_account = Account(user_id=requester.id, balance=Decimal('50.00'))
            recipient_account = Account(user_id=recipient.id, balance=Decimal('100.00'))
            db.session.add_all([requester_account, recipient_account])
            db.session.flush()
            
            # Create expired money request
            money_request = MoneyRequest.create_request(
                requester_id=requester.id,
                recipient_id=recipient.id,
                amount=Decimal('25.00'),
                expires_in_days=1
            )
            
            # Manually set expiry to past
            money_request.expires_at = datetime.utcnow() - timedelta(hours=1)
            db.session.add(money_request)
            db.session.commit()
            
            # Test responding to expired request
            with pytest.raises(ValueError, match="request has expired"):
                MoneyRequestService.respond_to_request(
                    request_id=money_request.id,
                    user_id=recipient.id,
                    approved=True
                )
    
    def test_cancel_request_success(self, app):
        """Test successful request cancellation"""
        with app.app_context():
            # Create users and accounts
            requester = User(microsoft_id='requester', email='requester@test.com', name='Requester')
            recipient = User(microsoft_id='recipient', email='recipient@test.com', name='Recipient')
            db.session.add_all([requester, recipient])
            db.session.flush()
            
            requester_account = Account(user_id=requester.id, balance=Decimal('50.00'))
            recipient_account = Account(user_id=recipient.id, balance=Decimal('100.00'))
            db.session.add_all([requester_account, recipient_account])
            db.session.commit()
            
            # Create money request
            create_result = MoneyRequestService.create_money_request(
                requester_id=requester.id,
                recipient_id=recipient.id,
                amount=Decimal('25.00')
            )
            
            request_id = create_result['request']['id']
            
            # Test cancelling request
            result = MoneyRequestService.cancel_request(
                request_id=request_id,
                user_id=requester.id
            )
            
            assert result['success'] is True
            assert result['request']['status'] == 'DECLINED'
            assert 'cancelled successfully' in result['message']
    
    def test_cancel_request_unauthorized(self, app):
        """Test cancelling request by unauthorized user"""
        with app.app_context():
            # Create users and accounts
            requester = User(microsoft_id='requester', email='requester@test.com', name='Requester')
            recipient = User(microsoft_id='recipient', email='recipient@test.com', name='Recipient')
            db.session.add_all([requester, recipient])
            db.session.flush()
            
            requester_account = Account(user_id=requester.id, balance=Decimal('50.00'))
            recipient_account = Account(user_id=recipient.id, balance=Decimal('100.00'))
            db.session.add_all([requester_account, recipient_account])
            db.session.commit()
            
            # Create money request
            create_result = MoneyRequestService.create_money_request(
                requester_id=requester.id,
                recipient_id=recipient.id,
                amount=Decimal('25.00')
            )
            
            request_id = create_result['request']['id']
            
            # Test cancelling as recipient (should fail)
            with pytest.raises(ValueError, match="not authorized to cancel"):
                MoneyRequestService.cancel_request(
                    request_id=request_id,
                    user_id=recipient.id
                )
    
    def test_get_pending_requests_for_user(self, app):
        """Test getting pending requests for user"""
        with app.app_context():
            # Create users and accounts
            requester1 = User(microsoft_id='req1', email='req1@test.com', name='Requester 1')
            requester2 = User(microsoft_id='req2', email='req2@test.com', name='Requester 2')
            recipient = User(microsoft_id='recipient', email='recipient@test.com', name='Recipient')
            db.session.add_all([requester1, requester2, recipient])
            db.session.flush()
            
            req1_account = Account(user_id=requester1.id, balance=Decimal('50.00'))
            req2_account = Account(user_id=requester2.id, balance=Decimal('75.00'))
            recipient_account = Account(user_id=recipient.id, balance=Decimal('100.00'))
            db.session.add_all([req1_account, req2_account, recipient_account])
            db.session.commit()
            
            # Create multiple requests to recipient
            MoneyRequestService.create_money_request(
                requester_id=requester1.id,
                recipient_id=recipient.id,
                amount=Decimal('25.00'),
                note='Request 1'
            )
            
            MoneyRequestService.create_money_request(
                requester_id=requester2.id,
                recipient_id=recipient.id,
                amount=Decimal('30.00'),
                note='Request 2'
            )
            
            # Test getting pending requests
            pending_requests = MoneyRequestService.get_pending_requests_for_user(recipient.id)
            
            assert len(pending_requests) == 2
            assert all(req.status == RequestStatus.PENDING for req in pending_requests)
            assert all(req.recipient_id == recipient.id for req in pending_requests)
    
    def test_get_sent_requests(self, app):
        """Test getting sent requests"""
        with app.app_context():
            # Create users and accounts
            requester = User(microsoft_id='requester', email='requester@test.com', name='Requester')
            recipient1 = User(microsoft_id='rec1', email='rec1@test.com', name='Recipient 1')
            recipient2 = User(microsoft_id='rec2', email='rec2@test.com', name='Recipient 2')
            db.session.add_all([requester, recipient1, recipient2])
            db.session.flush()
            
            requester_account = Account(user_id=requester.id, balance=Decimal('100.00'))
            rec1_account = Account(user_id=recipient1.id, balance=Decimal('50.00'))
            rec2_account = Account(user_id=recipient2.id, balance=Decimal('75.00'))
            db.session.add_all([requester_account, rec1_account, rec2_account])
            db.session.commit()
            
            # Create multiple requests from requester
            MoneyRequestService.create_money_request(
                requester_id=requester.id,
                recipient_id=recipient1.id,
                amount=Decimal('25.00')
            )
            
            MoneyRequestService.create_money_request(
                requester_id=requester.id,
                recipient_id=recipient2.id,
                amount=Decimal('30.00')
            )
            
            # Test getting sent requests
            result = MoneyRequestService.get_sent_requests(requester.id)
            
            assert len(result['requests']) == 2
            assert result['pagination']['total'] == 2
            assert all(req['requester_id'] == requester.id for req in result['requests'])
    
    def test_get_request_statistics(self, app):
        """Test getting request statistics"""
        with app.app_context():
            # Create users and accounts
            requester = User(microsoft_id='requester', email='requester@test.com', name='Requester')
            recipient = User(microsoft_id='recipient', email='recipient@test.com', name='Recipient')
            db.session.add_all([requester, recipient])
            db.session.flush()
            
            requester_account = Account(user_id=requester.id, balance=Decimal('50.00'))
            recipient_account = Account(user_id=recipient.id, balance=Decimal('200.00'))
            db.session.add_all([requester_account, recipient_account])
            db.session.commit()
            
            # Create and respond to requests
            # Approved request
            create_result1 = MoneyRequestService.create_money_request(
                requester_id=requester.id,
                recipient_id=recipient.id,
                amount=Decimal('25.00')
            )
            MoneyRequestService.respond_to_request(
                request_id=create_result1['request']['id'],
                user_id=recipient.id,
                approved=True
            )
            
            # Declined request
            create_result2 = MoneyRequestService.create_money_request(
                requester_id=requester.id,
                recipient_id=recipient.id,
                amount=Decimal('30.00')
            )
            MoneyRequestService.respond_to_request(
                request_id=create_result2['request']['id'],
                user_id=recipient.id,
                approved=False
            )
            
            # Test getting statistics for requester
            stats = MoneyRequestService.get_request_statistics(requester.id, days=30)
            
            assert stats['sent_requests']['total'] == 2
            assert stats['sent_requests']['approved'] == 1
            assert stats['sent_requests']['declined'] == 1
            assert stats['sent_requests']['total_amount_approved'] == '25.00'
            assert stats['sent_requests']['approval_rate'] == 50.0
    
    def test_validate_request_creation_success(self, app):
        """Test successful request validation"""
        with app.app_context():
            # Create users and accounts
            requester = User(microsoft_id='requester', email='requester@test.com', name='Requester')
            recipient = User(microsoft_id='recipient', email='recipient@test.com', name='Recipient')
            db.session.add_all([requester, recipient])
            db.session.flush()
            
            requester_account = Account(user_id=requester.id, balance=Decimal('50.00'))
            recipient_account = Account(user_id=recipient.id, balance=Decimal('100.00'))
            db.session.add_all([requester_account, recipient_account])
            db.session.commit()
            
            # Test validation
            validation = MoneyRequestService.validate_request_creation(
                requester_id=requester.id,
                recipient_id=recipient.id,
                amount=Decimal('25.00')
            )
            
            assert validation['valid'] is True
            assert len(validation['errors']) == 0
    
    def test_validate_request_creation_self_request(self, app):
        """Test validation of self request"""
        with app.app_context():
            # Create user and account
            user = User(microsoft_id='user', email='user@test.com', name='User')
            db.session.add(user)
            db.session.flush()
            
            account = Account(user_id=user.id, balance=Decimal('100.00'))
            db.session.add(account)
            db.session.commit()
            
            # Test self request validation
            validation = MoneyRequestService.validate_request_creation(
                requester_id=user.id,
                recipient_id=user.id,
                amount=Decimal('25.00')
            )
            
            assert validation['valid'] is False
            assert any(error['code'] == 'SELF_REQUEST' for error in validation['errors'])
    
    def test_expire_old_requests(self, app):
        """Test expiring old requests"""
        with app.app_context():
            # Create users and accounts
            requester = User(microsoft_id='requester', email='requester@test.com', name='Requester')
            recipient = User(microsoft_id='recipient', email='recipient@test.com', name='Recipient')
            db.session.add_all([requester, recipient])
            db.session.flush()
            
            requester_account = Account(user_id=requester.id, balance=Decimal('50.00'))
            recipient_account = Account(user_id=recipient.id, balance=Decimal('100.00'))
            db.session.add_all([requester_account, recipient_account])
            db.session.flush()
            
            # Create expired request
            money_request = MoneyRequest.create_request(
                requester_id=requester.id,
                recipient_id=recipient.id,
                amount=Decimal('25.00')
            )
            
            # Manually set expiry to past
            money_request.expires_at = datetime.utcnow() - timedelta(hours=1)
            db.session.add(money_request)
            db.session.commit()
            
            # Test expiring old requests
            result = MoneyRequestService.expire_old_requests()
            
            assert result['success'] is True
            assert result['expired_count'] == 1
            
            # Verify request was marked as expired
            db.session.refresh(money_request)
            assert money_request.status == RequestStatus.EXPIRED