"""
Tests for EventService
"""
import pytest
from decimal import Decimal
from datetime import datetime, timedelta
from services.event_service import EventService
from models import (
    db, User, UserRole, AccountStatus, Account, 
    EventAccount, EventStatus, Transaction, TransactionType
)

class TestEventService:
    """Test cases for EventService"""
    
    def test_create_event_account_success(self, app):
        """Test successful event account creation"""
        with app.app_context():
            # Create creator user
            creator = User(microsoft_id='creator', email='creator@test.com', name='Creator')
            db.session.add(creator)
            db.session.flush()
            
            creator_account = Account(user_id=creator.id, balance=Decimal('100.00'))
            db.session.add(creator_account)
            db.session.commit()
            
            # Test event creation
            event_data = {
                'name': 'Team Lunch',
                'description': 'Monthly team lunch gathering',
                'target_amount': Decimal('200.00'),
                'deadline': datetime.now(datetime.UTC) + timedelta(days=7)
            }
            
            result = EventService.create_event_account(
                creator_id=creator.id,
                event_data=event_data
            )
            
            assert result['success'] is True
            assert result['event']['name'] == 'Team Lunch'
            assert result['event']['description'] == 'Monthly team lunch gathering'
            assert result['event']['target_amount'] == '200.00'
            assert result['event']['status'] == EventStatus.ACTIVE.value
            assert result['event']['creator_name'] == 'Creator'
    
    def test_create_event_account_invalid_creator(self, app):
        """Test event creation with invalid creator"""
        with app.app_context():
            event_data = {
                'name': 'Test Event',
                'description': 'Test description'
            }
            
            with pytest.raises(ValueError, match="Creator not found or inactive"):
                EventService.create_event_account(
                    creator_id='invalid-id',
                    event_data=event_data
                )
    
    def test_create_event_account_missing_name(self, app):
        """Test event creation with missing name"""
        with app.app_context():
            # Create creator user
            creator = User(microsoft_id='creator', email='creator@test.com', name='Creator')
            db.session.add(creator)
            db.session.flush()
            
            creator_account = Account(user_id=creator.id, balance=Decimal('100.00'))
            db.session.add(creator_account)
            db.session.commit()
            
            # Test event creation without name
            event_data = {
                'description': 'Test description'
            }
            
            with pytest.raises(ValueError, match="Event name is required"):
                EventService.create_event_account(
                    creator_id=creator.id,
                    event_data=event_data
                )
    
    def test_contribute_to_event_success(self, app):
        """Test successful event contribution"""
        with app.app_context():
            # Create users and accounts
            creator = User(microsoft_id='creator', email='creator@test.com', name='Creator')
            contributor = User(microsoft_id='contributor', email='contributor@test.com', name='Contributor')
            db.session.add_all([creator, contributor])
            db.session.flush()
            
            creator_account = Account(user_id=creator.id, balance=Decimal('100.00'))
            contributor_account = Account(user_id=contributor.id, balance=Decimal('150.00'))
            db.session.add_all([creator_account, contributor_account])
            db.session.flush()
            
            # Create event
            event = EventAccount(
                creator_id=creator.id,
                name='Team Event',
                description='Test event',
                target_amount=Decimal('200.00')
            )
            db.session.add(event)
            db.session.commit()
            
            # Test contribution
            result = EventService.contribute_to_event(
                user_id=contributor.id,
                event_id=event.id,
                amount=Decimal('50.00'),
                note='Happy to contribute!'
            )
            
            assert result['success'] is True
            assert result['contribution']['amount'] == '50.00'
            assert result['contribution']['contributor_name'] == 'Contributor'
            assert result['contributor_balance'] == Decimal('100.00')
            assert result['event_total'] == Decimal('50.00')
    
    def test_contribute_to_event_insufficient_funds(self, app):
        """Test event contribution with insufficient funds"""
        with app.app_context():
            # Create users and accounts
            creator = User(microsoft_id='creator', email='creator@test.com', name='Creator')
            contributor = User(microsoft_id='contributor', email='contributor@test.com', name='Contributor')
            db.session.add_all([creator, contributor])
            db.session.flush()
            
            creator_account = Account(user_id=creator.id, balance=Decimal('100.00'))
            contributor_account = Account(user_id=contributor.id, balance=Decimal('10.00'))
            db.session.add_all([creator_account, contributor_account])
            db.session.flush()
            
            # Create event
            event = EventAccount(
                creator_id=creator.id,
                name='Team Event',
                description='Test event'
            )
            db.session.add(event)
            db.session.commit()
            
            # Test contribution that would exceed overdraft
            with pytest.raises(ValueError, match="Contributor validation failed"):
                EventService.contribute_to_event(
                    user_id=contributor.id,
                    event_id=event.id,
                    amount=Decimal('300.00')
                )
    
    def test_contribute_to_event_closed(self, app):
        """Test contribution to closed event"""
        with app.app_context():
            # Create users and accounts
            creator = User(microsoft_id='creator', email='creator@test.com', name='Creator')
            contributor = User(microsoft_id='contributor', email='contributor@test.com', name='Contributor')
            db.session.add_all([creator, contributor])
            db.session.flush()
            
            creator_account = Account(user_id=creator.id, balance=Decimal('100.00'))
            contributor_account = Account(user_id=contributor.id, balance=Decimal('150.00'))
            db.session.add_all([creator_account, contributor_account])
            db.session.flush()
            
            # Create closed event
            event = EventAccount(
                creator_id=creator.id,
                name='Team Event',
                description='Test event',
                status=EventStatus.CLOSED
            )
            db.session.add(event)
            db.session.commit()
            
            # Test contribution to closed event
            with pytest.raises(ValueError, match="Event is not active"):
                EventService.contribute_to_event(
                    user_id=contributor.id,
                    event_id=event.id,
                    amount=Decimal('50.00')
                )
    
    def test_close_event_account_success(self, app):
        """Test successful event closure"""
        with app.app_context():
            # Create users and accounts
            creator = User(microsoft_id='creator', email='creator@test.com', name='Creator')
            finance_user = User(
                microsoft_id='finance', 
                email='finance@test.com', 
                name='Finance User',
                role=UserRole.FINANCE
            )
            db.session.add_all([creator, finance_user])
            db.session.flush()
            
            creator_account = Account(user_id=creator.id, balance=Decimal('100.00'))
            finance_account = Account(user_id=finance_user.id, balance=Decimal('200.00'))
            db.session.add_all([creator_account, finance_account])
            db.session.flush()
            
            # Create event with contributions
            event = EventAccount(
                creator_id=creator.id,
                name='Team Event',
                description='Test event',
                target_amount=Decimal('100.00')
            )
            db.session.add(event)
            db.session.commit()
            
            # Test event closure
            result = EventService.close_event_account(
                event_id=event.id,
                closer_id=finance_user.id,
                closure_reason='Event completed successfully'
            )
            
            assert result['success'] is True
            assert result['event']['status'] == EventStatus.CLOSED.value
            assert result['event']['closed_by'] == 'Finance User'
            assert 'closed_at' in result['event']
    
    def test_close_event_account_unauthorized(self, app):
        """Test event closure by unauthorized user"""
        with app.app_context():
            # Create users and accounts
            creator = User(microsoft_id='creator', email='creator@test.com', name='Creator')
            regular_user = User(microsoft_id='regular', email='regular@test.com', name='Regular User')
            db.session.add_all([creator, regular_user])
            db.session.flush()
            
            creator_account = Account(user_id=creator.id, balance=Decimal('100.00'))
            regular_account = Account(user_id=regular_user.id, balance=Decimal('150.00'))
            db.session.add_all([creator_account, regular_account])
            db.session.flush()
            
            # Create event
            event = EventAccount(
                creator_id=creator.id,
                name='Team Event',
                description='Test event'
            )
            db.session.add(event)
            db.session.commit()
            
            # Test unauthorized closure
            with pytest.raises(ValueError, match="Only event creator or finance team can close events"):
                EventService.close_event_account(
                    event_id=event.id,
                    closer_id=regular_user.id
                )
    
    def test_get_event_contributions(self, app):
        """Test getting event contributions"""
        with app.app_context():
            # Create users and accounts
            creator = User(microsoft_id='creator', email='creator@test.com', name='Creator')
            contributor1 = User(microsoft_id='cont1', email='cont1@test.com', name='Contributor 1')
            contributor2 = User(microsoft_id='cont2', email='cont2@test.com', name='Contributor 2')
            db.session.add_all([creator, contributor1, contributor2])
            db.session.flush()
            
            creator_account = Account(user_id=creator.id, balance=Decimal('100.00'))
            cont1_account = Account(user_id=contributor1.id, balance=Decimal('150.00'))
            cont2_account = Account(user_id=contributor2.id, balance=Decimal('200.00'))
            db.session.add_all([creator_account, cont1_account, cont2_account])
            db.session.flush()
            
            # Create event
            event = EventAccount(
                creator_id=creator.id,
                name='Team Event',
                description='Test event'
            )
            db.session.add(event)
            db.session.flush()
            
            # Create contributions
            contribution1 = Transaction.create_event_contribution(
                contributor_id=contributor1.id,
                event_id=event.id,
                amount=Decimal('25.00'),
                note='First contribution'
            )
            contribution2 = Transaction.create_event_contribution(
                contributor_id=contributor2.id,
                event_id=event.id,
                amount=Decimal('35.00'),
                note='Second contribution'
            )
            db.session.add_all([contribution1, contribution2])
            db.session.commit()
            
            # Test getting contributions
            contributions = EventService.get_event_contributions(event.id)
            
            assert len(contributions) == 2
            assert contributions[0]['amount'] in ['25.00', '35.00']
            assert contributions[1]['amount'] in ['25.00', '35.00']
            assert any(c['contributor_name'] == 'Contributor 1' for c in contributions)
            assert any(c['contributor_name'] == 'Contributor 2' for c in contributions)
    
    def test_get_active_events(self, app):
        """Test getting active events"""
        with app.app_context():
            # Create users and accounts
            creator1 = User(microsoft_id='creator1', email='creator1@test.com', name='Creator 1')
            creator2 = User(microsoft_id='creator2', email='creator2@test.com', name='Creator 2')
            db.session.add_all([creator1, creator2])
            db.session.flush()
            
            creator1_account = Account(user_id=creator1.id, balance=Decimal('100.00'))
            creator2_account = Account(user_id=creator2.id, balance=Decimal('150.00'))
            db.session.add_all([creator1_account, creator2_account])
            db.session.flush()
            
            # Create events
            active_event = EventAccount(
                creator_id=creator1.id,
                name='Active Event',
                description='Active event description',
                status=EventStatus.ACTIVE
            )
            closed_event = EventAccount(
                creator_id=creator2.id,
                name='Closed Event',
                description='Closed event description',
                status=EventStatus.CLOSED
            )
            db.session.add_all([active_event, closed_event])
            db.session.commit()
            
            # Test getting active events
            active_events = EventService.get_active_events()
            
            assert len(active_events) == 1
            assert active_events[0]['name'] == 'Active Event'
            assert active_events[0]['status'] == EventStatus.ACTIVE.value
    
    def test_get_event_statistics(self, app):
        """Test getting event statistics"""
        with app.app_context():
            # Create users and accounts
            creator = User(microsoft_id='creator', email='creator@test.com', name='Creator')
            contributor1 = User(microsoft_id='cont1', email='cont1@test.com', name='Contributor 1')
            contributor2 = User(microsoft_id='cont2', email='cont2@test.com', name='Contributor 2')
            db.session.add_all([creator, contributor1, contributor2])
            db.session.flush()
            
            creator_account = Account(user_id=creator.id, balance=Decimal('100.00'))
            cont1_account = Account(user_id=contributor1.id, balance=Decimal('150.00'))
            cont2_account = Account(user_id=contributor2.id, balance=Decimal('200.00'))
            db.session.add_all([creator_account, cont1_account, cont2_account])
            db.session.flush()
            
            # Create event
            event = EventAccount(
                creator_id=creator.id,
                name='Team Event',
                description='Test event',
                target_amount=Decimal('100.00')
            )
            db.session.add(event)
            db.session.flush()
            
            # Create contributions
            contribution1 = Transaction.create_event_contribution(
                contributor_id=contributor1.id,
                event_id=event.id,
                amount=Decimal('30.00')
            )
            contribution2 = Transaction.create_event_contribution(
                contributor_id=contributor2.id,
                event_id=event.id,
                amount=Decimal('45.00')
            )
            contribution1.mark_as_processed()
            contribution2.mark_as_processed()
            db.session.add_all([contribution1, contribution2])
            db.session.commit()
            
            # Test getting statistics
            stats = EventService.get_event_statistics(event.id)
            
            assert stats['total_contributions'] == '75.00'
            assert stats['target_amount'] == '100.00'
            assert stats['progress_percentage'] == 75.0
            assert stats['contributor_count'] == 2
            assert stats['average_contribution'] == '37.50'
    
    def test_search_events(self, app):
        """Test searching events"""
        with app.app_context():
            # Create users and accounts
            creator1 = User(microsoft_id='creator1', email='creator1@test.com', name='Creator 1')
            creator2 = User(microsoft_id='creator2', email='creator2@test.com', name='Creator 2')
            db.session.add_all([creator1, creator2])
            db.session.flush()
            
            creator1_account = Account(user_id=creator1.id, balance=Decimal('100.00'))
            creator2_account = Account(user_id=creator2.id, balance=Decimal('150.00'))
            db.session.add_all([creator1_account, creator2_account])
            db.session.flush()
            
            # Create events
            lunch_event = EventAccount(
                creator_id=creator1.id,
                name='Team Lunch',
                description='Monthly team lunch gathering'
            )
            party_event = EventAccount(
                creator_id=creator2.id,
                name='Office Party',
                description='End of year celebration'
            )
            db.session.add_all([lunch_event, party_event])
            db.session.commit()
            
            # Test searching by name
            lunch_results = EventService.search_events(query='lunch')
            assert len(lunch_results) == 1
            assert lunch_results[0]['name'] == 'Team Lunch'
            
            # Test searching by description
            party_results = EventService.search_events(query='celebration')
            assert len(party_results) == 1
            assert party_results[0]['name'] == 'Office Party'
            
            # Test searching with no results
            no_results = EventService.search_events(query='nonexistent')
            assert len(no_results) == 0
    
    def test_validate_event_deadline(self, app):
        """Test event deadline validation"""
        with app.app_context():
            # Create creator user
            creator = User(microsoft_id='creator', email='creator@test.com', name='Creator')
            db.session.add(creator)
            db.session.flush()
            
            creator_account = Account(user_id=creator.id, balance=Decimal('100.00'))
            db.session.add(creator_account)
            db.session.commit()
            
            # Test event creation with past deadline
            past_deadline = datetime.now(datetime.UTC) - timedelta(days=1)
            event_data = {
                'name': 'Past Event',
                'description': 'Event with past deadline',
                'deadline': past_deadline
            }
            
            with pytest.raises(ValueError, match="Event deadline cannot be in the past"):
                EventService.create_event_account(
                    creator_id=creator.id,
                    event_data=event_data
                )
    
    def test_get_user_event_contributions(self, app):
        """Test getting user's event contributions"""
        with app.app_context():
            # Create users and accounts
            creator = User(microsoft_id='creator', email='creator@test.com', name='Creator')
            contributor = User(microsoft_id='contributor', email='contributor@test.com', name='Contributor')
            db.session.add_all([creator, contributor])
            db.session.flush()
            
            creator_account = Account(user_id=creator.id, balance=Decimal('100.00'))
            contributor_account = Account(user_id=contributor.id, balance=Decimal('200.00'))
            db.session.add_all([creator_account, contributor_account])
            db.session.flush()
            
            # Create events
            event1 = EventAccount(
                creator_id=creator.id,
                name='Event 1',
                description='First event'
            )
            event2 = EventAccount(
                creator_id=creator.id,
                name='Event 2',
                description='Second event'
            )
            db.session.add_all([event1, event2])
            db.session.flush()
            
            # Create contributions
            contribution1 = Transaction.create_event_contribution(
                contributor_id=contributor.id,
                event_id=event1.id,
                amount=Decimal('25.00')
            )
            contribution2 = Transaction.create_event_contribution(
                contributor_id=contributor.id,
                event_id=event2.id,
                amount=Decimal('35.00')
            )
            contribution1.mark_as_processed()
            contribution2.mark_as_processed()
            db.session.add_all([contribution1, contribution2])
            db.session.commit()
            
            # Test getting user contributions
            user_contributions = EventService.get_user_event_contributions(contributor.id)
            
            assert len(user_contributions) == 2
            assert sum(Decimal(c['amount']) for c in user_contributions) == Decimal('60.00')
            event_names = [c['event_name'] for c in user_contributions]
            assert 'Event 1' in event_names
            assert 'Event 2' in event_names