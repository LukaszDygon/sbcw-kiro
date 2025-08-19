"""
Tests for TransactionService
"""
import pytest
from decimal import Decimal
from services.transaction_service import TransactionService
from models import (
    db, User, UserRole, AccountStatus, Account, 
    Transaction, TransactionType, TransactionStatus
)

class TestTransactionService:
    """Test cases for TransactionService"""
    
    def test_send_money_success(self, app):
        """Test successful money transfer"""
        with app.app_context():
            # Create users and accounts
            sender = User(microsoft_id='sender', email='sender@test.com', name='Sender')
            recipient = User(microsoft_id='recipient', email='recipient@test.com', name='Recipient')
            db.session.add_all([sender, recipient])
            db.session.flush()
            
            sender_account = Account(user_id=sender.id, balance=Decimal('100.00'))
            recipient_account = Account(user_id=recipient.id, balance=Decimal('50.00'))
            db.session.add_all([sender_account, recipient_account])
            db.session.commit()
            
            # Test money transfer
            result = TransactionService.send_money(
                sender_id=sender.id,
                recipient_id=recipient.id,
                amount=Decimal('25.00'),
                category='Test',
                note='Test transfer'
            )
            
            assert result['success'] is True
            assert result['transaction']['amount'] == '25.00'
            assert result['transaction']['sender_name'] == 'Sender'
            assert result['transaction']['recipient_name'] == 'Recipient'
            assert result['sender_balance'] == Decimal('75.00')
            assert result['recipient_balance'] == Decimal('75.00')
    
    def test_send_money_self_transfer(self, app):
        """Test sending money to self (should fail)"""
        with app.app_context():
            # Create user and account
            user = User(microsoft_id='user', email='user@test.com', name='User')
            db.session.add(user)
            db.session.flush()
            
            account = Account(user_id=user.id, balance=Decimal('100.00'))
            db.session.add(account)
            db.session.commit()
            
            # Test self transfer
            with pytest.raises(ValueError, match="Cannot send money to yourself"):
                TransactionService.send_money(
                    sender_id=user.id,
                    recipient_id=user.id,
                    amount=Decimal('25.00')
                )
    
    def test_send_money_insufficient_funds(self, app):
        """Test sending money with insufficient funds"""
        with app.app_context():
            # Create users and accounts
            sender = User(microsoft_id='sender', email='sender@test.com', name='Sender')
            recipient = User(microsoft_id='recipient', email='recipient@test.com', name='Recipient')
            db.session.add_all([sender, recipient])
            db.session.flush()
            
            sender_account = Account(user_id=sender.id, balance=Decimal('10.00'))
            recipient_account = Account(user_id=recipient.id, balance=Decimal('50.00'))
            db.session.add_all([sender_account, recipient_account])
            db.session.commit()
            
            # Test transfer that would exceed overdraft
            with pytest.raises(ValueError, match="Sender validation failed"):
                TransactionService.send_money(
                    sender_id=sender.id,
                    recipient_id=recipient.id,
                    amount=Decimal('300.00')  # Would exceed overdraft limit
                )
    
    def test_send_money_inactive_user(self, app):
        """Test sending money with inactive user"""
        with app.app_context():
            # Create users and accounts
            sender = User(
                microsoft_id='sender', 
                email='sender@test.com', 
                name='Sender',
                account_status=AccountStatus.SUSPENDED
            )
            recipient = User(microsoft_id='recipient', email='recipient@test.com', name='Recipient')
            db.session.add_all([sender, recipient])
            db.session.flush()
            
            sender_account = Account(user_id=sender.id, balance=Decimal('100.00'))
            recipient_account = Account(user_id=recipient.id, balance=Decimal('50.00'))
            db.session.add_all([sender_account, recipient_account])
            db.session.commit()
            
            # Test transfer with inactive sender
            with pytest.raises(ValueError, match="Sender account not found or inactive"):
                TransactionService.send_money(
                    sender_id=sender.id,
                    recipient_id=recipient.id,
                    amount=Decimal('25.00')
                )
    
    def test_send_bulk_money_success(self, app):
        """Test successful bulk money transfer"""
        with app.app_context():
            # Create users and accounts
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
            
            # Test bulk transfer
            recipients = [
                {
                    'recipient_id': recipient1.id,
                    'amount': Decimal('25.00'),
                    'category': 'Lunch',
                    'note': 'Lunch split'
                },
                {
                    'recipient_id': recipient2.id,
                    'amount': Decimal('30.00'),
                    'category': 'Lunch',
                    'note': 'Lunch split'
                }
            ]
            
            result = TransactionService.send_bulk_money(
                sender_id=sender.id,
                recipients=recipients
            )
            
            assert result['success'] is True
            assert result['total_amount'] == '55.00'
            assert result['recipient_count'] == 2
            assert result['sender_balance'] == Decimal('145.00')
            assert len(result['transactions']) == 2
    
    def test_send_bulk_money_insufficient_funds(self, app):
        """Test bulk transfer with insufficient funds"""
        with app.app_context():
            # Create users and accounts
            sender = User(microsoft_id='sender', email='sender@test.com', name='Sender')
            recipient1 = User(microsoft_id='rec1', email='rec1@test.com', name='Recipient 1')
            recipient2 = User(microsoft_id='rec2', email='rec2@test.com', name='Recipient 2')
            db.session.add_all([sender, recipient1, recipient2])
            db.session.flush()
            
            sender_account = Account(user_id=sender.id, balance=Decimal('50.00'))
            rec1_account = Account(user_id=recipient1.id, balance=Decimal('50.00'))
            rec2_account = Account(user_id=recipient2.id, balance=Decimal('30.00'))
            db.session.add_all([sender_account, rec1_account, rec2_account])
            db.session.commit()
            
            # Test bulk transfer that would exceed sender's balance
            recipients = [
                {
                    'recipient_id': recipient1.id,
                    'amount': Decimal('200.00'),
                    'category': 'Test'
                },
                {
                    'recipient_id': recipient2.id,
                    'amount': Decimal('100.00'),
                    'category': 'Test'
                }
            ]
            
            with pytest.raises(ValueError, match="Sender validation failed"):
                TransactionService.send_bulk_money(
                    sender_id=sender.id,
                    recipients=recipients
                )
    
    def test_send_bulk_money_too_many_recipients(self, app):
        """Test bulk transfer with too many recipients"""
        with app.app_context():
            # Create sender
            sender = User(microsoft_id='sender', email='sender@test.com', name='Sender')
            db.session.add(sender)
            db.session.flush()
            
            sender_account = Account(user_id=sender.id, balance=Decimal('1000.00'))
            db.session.add(sender_account)
            db.session.commit()
            
            # Create too many recipients
            recipients = [
                {
                    'recipient_id': f'recipient-{i}',
                    'amount': Decimal('1.00')
                }
                for i in range(51)  # Exceeds limit of 50
            ]
            
            with pytest.raises(ValueError, match="Too many recipients"):
                TransactionService.send_bulk_money(
                    sender_id=sender.id,
                    recipients=recipients
                )
    
    def test_validate_transaction_success(self, app):
        """Test successful transaction validation"""
        with app.app_context():
            # Create users and accounts
            sender = User(microsoft_id='sender', email='sender@test.com', name='Sender')
            recipient = User(microsoft_id='recipient', email='recipient@test.com', name='Recipient')
            db.session.add_all([sender, recipient])
            db.session.flush()
            
            sender_account = Account(user_id=sender.id, balance=Decimal('100.00'))
            recipient_account = Account(user_id=recipient.id, balance=Decimal('50.00'))
            db.session.add_all([sender_account, recipient_account])
            db.session.commit()
            
            # Test validation
            validation = TransactionService.validate_transaction(
                sender_id=sender.id,
                recipient_id=recipient.id,
                amount=Decimal('25.00'),
                transaction_type=TransactionType.TRANSFER
            )
            
            assert validation['valid'] is True
            assert len(validation['errors']) == 0
    
    def test_validate_transaction_self_transfer(self, app):
        """Test validation of self transfer"""
        with app.app_context():
            # Create user and account
            user = User(microsoft_id='user', email='user@test.com', name='User')
            db.session.add(user)
            db.session.flush()
            
            account = Account(user_id=user.id, balance=Decimal('100.00'))
            db.session.add(account)
            db.session.commit()
            
            # Test self transfer validation
            validation = TransactionService.validate_transaction(
                sender_id=user.id,
                recipient_id=user.id,
                amount=Decimal('25.00'),
                transaction_type=TransactionType.TRANSFER
            )
            
            assert validation['valid'] is False
            assert any(error['code'] == 'SELF_TRANSFER' for error in validation['errors'])
    
    def test_validate_transaction_invalid_amount(self, app):
        """Test validation with invalid amount"""
        with app.app_context():
            # Create users and accounts
            sender = User(microsoft_id='sender', email='sender@test.com', name='Sender')
            recipient = User(microsoft_id='recipient', email='recipient@test.com', name='Recipient')
            db.session.add_all([sender, recipient])
            db.session.flush()
            
            sender_account = Account(user_id=sender.id, balance=Decimal('100.00'))
            recipient_account = Account(user_id=recipient.id, balance=Decimal('50.00'))
            db.session.add_all([sender_account, recipient_account])
            db.session.commit()
            
            # Test negative amount validation
            validation = TransactionService.validate_transaction(
                sender_id=sender.id,
                recipient_id=recipient.id,
                amount=Decimal('-25.00'),
                transaction_type=TransactionType.TRANSFER
            )
            
            assert validation['valid'] is False
            assert any(error['code'] == 'INVALID_AMOUNT' for error in validation['errors'])
    
    def test_get_transaction_by_id_success(self, app):
        """Test getting transaction by ID"""
        with app.app_context():
            # Create users and accounts
            sender = User(microsoft_id='sender', email='sender@test.com', name='Sender')
            recipient = User(microsoft_id='recipient', email='recipient@test.com', name='Recipient')
            db.session.add_all([sender, recipient])
            db.session.flush()
            
            sender_account = Account(user_id=sender.id, balance=Decimal('100.00'))
            recipient_account = Account(user_id=recipient.id, balance=Decimal('50.00'))
            db.session.add_all([sender_account, recipient_account])
            db.session.flush()
            
            # Create transaction
            transaction = Transaction.create_transfer(
                sender_id=sender.id,
                recipient_id=recipient.id,
                amount=Decimal('25.00'),
                note='Test transaction'
            )
            db.session.add(transaction)
            db.session.commit()
            
            # Test getting transaction
            found_transaction = TransactionService.get_transaction_by_id(transaction.id, sender.id)
            
            assert found_transaction is not None
            assert found_transaction.id == transaction.id
            assert found_transaction.amount == Decimal('25.00')
    
    def test_get_transaction_by_id_access_denied(self, app):
        """Test getting transaction with access denied"""
        with app.app_context():
            # Create users and accounts
            sender = User(microsoft_id='sender', email='sender@test.com', name='Sender')
            recipient = User(microsoft_id='recipient', email='recipient@test.com', name='Recipient')
            other_user = User(microsoft_id='other', email='other@test.com', name='Other')
            db.session.add_all([sender, recipient, other_user])
            db.session.flush()
            
            sender_account = Account(user_id=sender.id, balance=Decimal('100.00'))
            recipient_account = Account(user_id=recipient.id, balance=Decimal('50.00'))
            other_account = Account(user_id=other_user.id, balance=Decimal('75.00'))
            db.session.add_all([sender_account, recipient_account, other_account])
            db.session.flush()
            
            # Create transaction
            transaction = Transaction.create_transfer(
                sender_id=sender.id,
                recipient_id=recipient.id,
                amount=Decimal('25.00')
            )
            db.session.add(transaction)
            db.session.commit()
            
            # Test getting transaction as uninvolved user
            found_transaction = TransactionService.get_transaction_by_id(transaction.id, other_user.id)
            
            assert found_transaction is None
    
    def test_get_recent_transactions(self, app):
        """Test getting recent transactions"""
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
            
            # Create multiple transactions
            for i in range(5):
                transaction = Transaction.create_transfer(
                    sender_id=user1.id,
                    recipient_id=user2.id,
                    amount=Decimal(f'{10 + i}.00'),
                    note=f'Transaction {i+1}'
                )
                db.session.add(transaction)
            
            db.session.commit()
            
            # Test getting recent transactions
            recent = TransactionService.get_recent_transactions(user1.id, limit=3)
            
            assert len(recent) == 3
            # Should be ordered by most recent first
            assert recent[0].note == 'Transaction 5'
            assert recent[1].note == 'Transaction 4'
            assert recent[2].note == 'Transaction 3'
    
    def test_get_transaction_statistics(self, app):
        """Test getting transaction statistics"""
        with app.app_context():
            # Create users and accounts
            user1 = User(microsoft_id='user1', email='user1@test.com', name='User 1')
            user2 = User(microsoft_id='user2', email='user2@test.com', name='User 2')
            user3 = User(microsoft_id='user3', email='user3@test.com', name='User 3')
            db.session.add_all([user1, user2, user3])
            db.session.flush()
            
            account1 = Account(user_id=user1.id, balance=Decimal('200.00'))
            account2 = Account(user_id=user2.id, balance=Decimal('100.00'))
            account3 = Account(user_id=user3.id, balance=Decimal('50.00'))
            db.session.add_all([account1, account2, account3])
            db.session.flush()
            
            # Create transactions
            # User1 sends to User2
            transaction1 = Transaction.create_transfer(
                sender_id=user1.id,
                recipient_id=user2.id,
                amount=Decimal('25.00')
            )
            transaction1.mark_as_processed()
            
            # User2 sends to User1
            transaction2 = Transaction.create_transfer(
                sender_id=user2.id,
                recipient_id=user1.id,
                amount=Decimal('15.00')
            )
            transaction2.mark_as_processed()
            
            # User1 sends to User3
            transaction3 = Transaction.create_transfer(
                sender_id=user1.id,
                recipient_id=user3.id,
                amount=Decimal('30.00')
            )
            transaction3.mark_as_processed()
            
            db.session.add_all([transaction1, transaction2, transaction3])
            db.session.commit()
            
            # Test getting statistics for User1
            stats = TransactionService.get_transaction_statistics(user1.id, days=30)
            
            assert stats['total_transactions'] == 3
            assert stats['total_sent'] == '55.00'  # 25 + 30
            assert stats['total_received'] == '15.00'
            assert stats['net_amount'] == '-40.00'  # 15 - 55
            assert stats['sent_count'] == 2
            assert stats['received_count'] == 1
            assert len(stats['top_partners']) == 2  # User2 and User3
    
    def test_cancel_transaction_completed(self, app):
        """Test cancelling a completed transaction"""
        with app.app_context():
            # Create users and accounts
            sender = User(microsoft_id='sender', email='sender@test.com', name='Sender')
            recipient = User(microsoft_id='recipient', email='recipient@test.com', name='Recipient')
            db.session.add_all([sender, recipient])
            db.session.flush()
            
            sender_account = Account(user_id=sender.id, balance=Decimal('100.00'))
            recipient_account = Account(user_id=recipient.id, balance=Decimal('50.00'))
            db.session.add_all([sender_account, recipient_account])
            db.session.flush()
            
            # Create completed transaction
            transaction = Transaction.create_transfer(
                sender_id=sender.id,
                recipient_id=recipient.id,
                amount=Decimal('25.00')
            )
            transaction.mark_as_processed()
            db.session.add(transaction)
            db.session.commit()
            
            # Test cancelling completed transaction
            with pytest.raises(ValueError, match="Cannot cancel completed transaction"):
                TransactionService.cancel_transaction(transaction.id, sender.id)
    
    def test_cancel_transaction_failed(self, app):
        """Test cancelling a failed transaction"""
        with app.app_context():
            # Create users and accounts
            sender = User(microsoft_id='sender', email='sender@test.com', name='Sender')
            recipient = User(microsoft_id='recipient', email='recipient@test.com', name='Recipient')
            db.session.add_all([sender, recipient])
            db.session.flush()
            
            sender_account = Account(user_id=sender.id, balance=Decimal('100.00'))
            recipient_account = Account(user_id=recipient.id, balance=Decimal('50.00'))
            db.session.add_all([sender_account, recipient_account])
            db.session.flush()
            
            # Create failed transaction
            transaction = Transaction.create_transfer(
                sender_id=sender.id,
                recipient_id=recipient.id,
                amount=Decimal('25.00')
            )
            transaction.mark_as_failed()
            db.session.add(transaction)
            db.session.commit()
            
            # Test cancelling failed transaction
            result = TransactionService.cancel_transaction(transaction.id, sender.id)
            
            assert result['success'] is True
            assert 'already failed' in result['message']