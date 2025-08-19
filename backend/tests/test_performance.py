"""
Performance tests for SoftBankCashWire transaction processing
"""
import pytest
import time
import threading
import concurrent.futures
from decimal import Decimal
from datetime import datetime
from models import (
    db, User, UserRole, AccountStatus, Account, 
    Transaction, TransactionType, TransactionStatus
)
from services.transaction_service import TransactionService
from services.account_service import AccountService

class TestTransactionPerformance:
    """Test transaction processing performance"""
    
    def setup_test_users(self, app, count=100):
        """Helper to create test users and accounts"""
        users = []
        accounts = []
        
        for i in range(count):
            user = User(
                microsoft_id=f'user-{i}',
                email=f'user{i}@test.com',
                name=f'User {i}'
            )
            users.append(user)
        
        db.session.add_all(users)
        db.session.flush()
        
        for user in users:
            account = Account(
                user_id=user.id,
                balance=Decimal('1000.00')  # Start with £1000
            )
            accounts.append(account)
        
        db.session.add_all(accounts)
        db.session.commit()
        
        return users, accounts
    
    def test_single_transaction_performance(self, app):
        """Test single transaction processing time"""
        with app.app_context():
            users, accounts = self.setup_test_users(app, 2)
            sender, recipient = users[0], users[1]
            
            # Measure transaction processing time
            start_time = time.time()
            
            result = TransactionService.send_money(
                sender_id=sender.id,
                recipient_id=recipient.id,
                amount=Decimal('25.00'),
                note='Performance test'
            )
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            # Transaction should complete in under 100ms
            assert processing_time < 0.1
            assert result['success'] is True
            
            # Verify balances updated correctly
            sender_account = Account.query.filter_by(user_id=sender.id).first()
            recipient_account = Account.query.filter_by(user_id=recipient.id).first()
            
            assert sender_account.balance == Decimal('975.00')
            assert recipient_account.balance == Decimal('1025.00')
    
    def test_concurrent_transactions_same_users(self, app):
        """Test concurrent transactions between same users"""
        with app.app_context():
            users, accounts = self.setup_test_users(app, 2)
            sender, recipient = users[0], users[1]
            
            def send_transaction(amount):
                try:
                    return TransactionService.send_money(
                        sender_id=sender.id,
                        recipient_id=recipient.id,
                        amount=Decimal(str(amount)),
                        note=f'Concurrent test {amount}'
                    )
                except Exception as e:
                    return {'success': False, 'error': str(e)}
            
            # Execute 10 concurrent transactions
            start_time = time.time()
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                futures = [executor.submit(send_transaction, i + 1) for i in range(10)]
                results = [future.result() for future in concurrent.futures.as_completed(futures)]
            
            end_time = time.time()
            total_time = end_time - start_time
            
            # All transactions should complete within reasonable time
            assert total_time < 2.0  # 2 seconds for 10 concurrent transactions
            
            # Count successful transactions
            successful_transactions = sum(1 for result in results if result['success'])
            
            # Due to database locking, some transactions might fail
            # but at least some should succeed
            assert successful_transactions > 0
            
            # Verify final balances are consistent
            sender_account = Account.query.filter_by(user_id=sender.id).first()
            recipient_account = Account.query.filter_by(user_id=recipient.id).first()
            
            # Total money in system should remain constant
            total_balance = sender_account.balance + recipient_account.balance
            assert total_balance == Decimal('2000.00')
    
    def test_concurrent_transactions_different_users(self, app):
        """Test concurrent transactions between different user pairs"""
        with app.app_context():
            users, accounts = self.setup_test_users(app, 20)
            
            def send_random_transaction(user_index):
                try:
                    sender = users[user_index]
                    recipient = users[(user_index + 1) % len(users)]  # Next user in list
                    
                    return TransactionService.send_money(
                        sender_id=sender.id,
                        recipient_id=recipient.id,
                        amount=Decimal('10.00'),
                        note=f'Concurrent test from {user_index}'
                    )
                except Exception as e:
                    return {'success': False, 'error': str(e)}
            
            # Execute 20 concurrent transactions between different users
            start_time = time.time()
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
                futures = [executor.submit(send_random_transaction, i) for i in range(20)]
                results = [future.result() for future in concurrent.futures.as_completed(futures)]
            
            end_time = time.time()
            total_time = end_time - start_time
            
            # Should complete faster than same-user transactions due to less contention
            assert total_time < 3.0
            
            # Most transactions should succeed since they don't conflict
            successful_transactions = sum(1 for result in results if result['success'])
            assert successful_transactions >= 15  # At least 75% success rate
    
    def test_bulk_transaction_performance(self, app):
        """Test bulk transaction processing performance"""
        with app.app_context():
            users, accounts = self.setup_test_users(app, 51)  # 1 sender + 50 recipients
            sender = users[0]
            recipients = users[1:]
            
            # Prepare bulk transaction data
            recipient_data = [
                {
                    'recipient_id': recipient.id,
                    'amount': Decimal('5.00'),
                    'category': 'Bulk Test',
                    'note': f'Bulk payment to {recipient.name}'
                }
                for recipient in recipients
            ]
            
            # Measure bulk transaction time
            start_time = time.time()
            
            result = TransactionService.send_bulk_money(
                sender_id=sender.id,
                recipients=recipient_data
            )
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            # Bulk transaction should complete efficiently
            assert processing_time < 5.0  # 5 seconds for 50 transactions
            assert result['success'] is True
            assert result['recipient_count'] == 50
            assert result['total_amount'] == '250.00'
            
            # Verify sender balance
            sender_account = Account.query.filter_by(user_id=sender.id).first()
            assert sender_account.balance == Decimal('750.00')  # 1000 - 250
    
    def test_transaction_history_query_performance(self, app):
        """Test transaction history query performance with large dataset"""
        with app.app_context():
            users, accounts = self.setup_test_users(app, 10)
            
            # Create many transactions
            transactions = []
            for i in range(1000):
                sender = users[i % len(users)]
                recipient = users[(i + 1) % len(users)]
                
                transaction = Transaction.create_transfer(
                    sender_id=sender.id,
                    recipient_id=recipient.id,
                    amount=Decimal('1.00'),
                    note=f'Test transaction {i}'
                )
                transaction.mark_as_processed()
                transactions.append(transaction)
            
            db.session.add_all(transactions)
            db.session.commit()
            
            # Test query performance
            test_user = users[0]
            
            start_time = time.time()
            
            history = AccountService.get_transaction_history(
                user_id=test_user.id,
                limit=50,
                offset=0
            )
            
            end_time = time.time()
            query_time = end_time - start_time
            
            # Query should complete quickly even with large dataset
            assert query_time < 0.5  # 500ms
            assert len(history['transactions']) <= 50
    
    def test_balance_calculation_performance(self, app):
        """Test account balance calculation performance"""
        with app.app_context():
            users, accounts = self.setup_test_users(app, 1)
            user = users[0]
            
            # Create many transactions affecting the user's balance
            transactions = []
            for i in range(500):
                if i % 2 == 0:
                    # User receives money
                    other_user = User(
                        microsoft_id=f'sender-{i}',
                        email=f'sender{i}@test.com',
                        name=f'Sender {i}'
                    )
                    db.session.add(other_user)
                    db.session.flush()
                    
                    transaction = Transaction.create_transfer(
                        sender_id=other_user.id,
                        recipient_id=user.id,
                        amount=Decimal('2.00')
                    )
                else:
                    # User sends money
                    other_user = User(
                        microsoft_id=f'recipient-{i}',
                        email=f'recipient{i}@test.com',
                        name=f'Recipient {i}'
                    )
                    db.session.add(other_user)
                    db.session.flush()
                    
                    transaction = Transaction.create_transfer(
                        sender_id=user.id,
                        recipient_id=other_user.id,
                        amount=Decimal('1.00')
                    )
                
                transaction.mark_as_processed()
                transactions.append(transaction)
            
            db.session.add_all(transactions)
            db.session.commit()
            
            # Test balance retrieval performance
            start_time = time.time()
            
            balance = AccountService.get_account_balance(user.id)
            
            end_time = time.time()
            query_time = end_time - start_time
            
            # Balance calculation should be fast
            assert query_time < 0.1  # 100ms
            
            # Verify balance is correct
            # Started with 1000, received 500 * 2 = 1000, sent 250 * 1 = 250
            # Final balance should be 1000 + 500 - 250 = 1750
            expected_balance = Decimal('1750.00')
            assert balance == expected_balance
    
    def test_database_connection_pool_performance(self, app):
        """Test database connection pool under load"""
        with app.app_context():
            users, accounts = self.setup_test_users(app, 10)
            
            def get_balance_repeatedly(user_id, iterations=10):
                results = []
                for _ in range(iterations):
                    start = time.time()
                    balance = AccountService.get_account_balance(user_id)
                    end = time.time()
                    results.append(end - start)
                return results
            
            # Test concurrent balance queries
            start_time = time.time()
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
                futures = [
                    executor.submit(get_balance_repeatedly, user.id, 5)
                    for user in users
                ]
                all_results = [future.result() for future in concurrent.futures.as_completed(futures)]
            
            end_time = time.time()
            total_time = end_time - start_time
            
            # All queries should complete efficiently
            assert total_time < 5.0
            
            # Calculate average query time
            all_times = [time for result in all_results for time in result]
            avg_time = sum(all_times) / len(all_times)
            
            # Average query time should be reasonable
            assert avg_time < 0.1  # 100ms average
    
    def test_memory_usage_under_load(self, app):
        """Test memory usage during high transaction volume"""
        with app.app_context():
            import psutil
            import os
            
            process = psutil.Process(os.getpid())
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            users, accounts = self.setup_test_users(app, 50)
            
            # Process many transactions
            for batch in range(10):  # 10 batches of 50 transactions
                transactions = []
                
                for i in range(50):
                    sender = users[i % len(users)]
                    recipient = users[(i + 1) % len(users)]
                    
                    transaction = Transaction.create_transfer(
                        sender_id=sender.id,
                        recipient_id=recipient.id,
                        amount=Decimal('1.00'),
                        note=f'Memory test batch {batch} transaction {i}'
                    )
                    transaction.mark_as_processed()
                    transactions.append(transaction)
                
                db.session.add_all(transactions)
                db.session.commit()
                
                # Clear session to free memory
                db.session.expunge_all()
            
            final_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_increase = final_memory - initial_memory
            
            # Memory increase should be reasonable (less than 100MB)
            assert memory_increase < 100
    
    def test_transaction_validation_performance(self, app):
        """Test transaction validation performance"""
        with app.app_context():
            users, accounts = self.setup_test_users(app, 100)
            
            # Test validation performance for many transactions
            validation_times = []
            
            for i in range(100):
                sender = users[i]
                recipient = users[(i + 1) % len(users)]
                
                start_time = time.time()
                
                validation = TransactionService.validate_transaction(
                    sender_id=sender.id,
                    recipient_id=recipient.id,
                    amount=Decimal('10.00'),
                    transaction_type=TransactionType.TRANSFER
                )
                
                end_time = time.time()
                validation_times.append(end_time - start_time)
                
                assert validation['valid'] is True
            
            # Average validation time should be very fast
            avg_validation_time = sum(validation_times) / len(validation_times)
            assert avg_validation_time < 0.01  # 10ms average
            
            # Maximum validation time should also be reasonable
            max_validation_time = max(validation_times)
            assert max_validation_time < 0.05  # 50ms maximum
    
    def test_audit_logging_performance_impact(self, app):
        """Test performance impact of audit logging"""
        with app.app_context():
            users, accounts = self.setup_test_users(app, 10)
            sender, recipient = users[0], users[1]
            
            # Measure transaction time with audit logging
            start_time = time.time()
            
            for i in range(50):
                TransactionService.send_money(
                    sender_id=sender.id,
                    recipient_id=recipient.id,
                    amount=Decimal('1.00'),
                    note=f'Audit test {i}'
                )
            
            end_time = time.time()
            total_time_with_audit = end_time - start_time
            
            # Even with audit logging, performance should be acceptable
            assert total_time_with_audit < 10.0  # 10 seconds for 50 transactions
            
            # Verify audit logs were created
            from models import AuditLog
            audit_count = AuditLog.query.count()
            assert audit_count >= 50  # At least one audit log per transaction
    
    def test_concurrent_event_contributions(self, app):
        """Test concurrent event contribution performance"""
        with app.app_context():
            users, accounts = self.setup_test_users(app, 20)
            creator = users[0]
            contributors = users[1:]
            
            # Create event
            from models import EventAccount
            event = EventAccount(
                creator_id=creator.id,
                name='Performance Test Event',
                description='Testing concurrent contributions',
                target_amount=Decimal('1000.00')
            )
            db.session.add(event)
            db.session.commit()
            
            def contribute_to_event(contributor_id):
                try:
                    from services.event_service import EventService
                    return EventService.contribute_to_event(
                        user_id=contributor_id,
                        event_id=event.id,
                        amount=Decimal('10.00'),
                        note='Concurrent contribution test'
                    )
                except Exception as e:
                    return {'success': False, 'error': str(e)}
            
            # Execute concurrent contributions
            start_time = time.time()
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=19) as executor:
                futures = [
                    executor.submit(contribute_to_event, contributor.id)
                    for contributor in contributors
                ]
                results = [future.result() for future in concurrent.futures.as_completed(futures)]
            
            end_time = time.time()
            total_time = end_time - start_time
            
            # Should complete efficiently
            assert total_time < 5.0
            
            # Most contributions should succeed
            successful_contributions = sum(1 for result in results if result['success'])
            assert successful_contributions >= 15  # At least 75% success rate
            
            # Verify event total is consistent
            db.session.refresh(event)
            expected_total = Decimal(str(successful_contributions * 10))
            assert event.get_total_contributions() == expected_total