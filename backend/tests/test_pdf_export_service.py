"""
Tests for PDF export service functionality
"""
import pytest
from datetime import datetime, timedelta
from services.pdf_export_service import PDFExportService
from decimal import Decimal
import io

class TestPDFExportService:
    """Test cases for PDFExportService"""
    
    @pytest.fixture
    def sample_transaction_summary_data(self):
        """Sample transaction summary report data"""
        return {
            'report_type': 'TRANSACTION_SUMMARY',
            'period': {
                'start_date': '2024-01-01T00:00:00',
                'end_date': '2024-01-31T23:59:59',
                'duration_days': 31
            },
            'user_id': None,
            'summary': {
                'total_transactions': 150,
                'total_volume': '15000.00',
                'average_transaction_amount': '100.00',
                'transfer_count': 120,
                'event_contribution_count': 30,
                'average_transfer_amount': '95.00',
                'average_contribution_amount': '125.00'
            },
            'category_breakdown': [
                {
                    'category': 'Food & Dining',
                    'transaction_count': 45,
                    'total_amount': '4500.00',
                    'average_amount': '100.00',
                    'percentage_of_volume': 30.0
                },
                {
                    'category': 'Entertainment',
                    'transaction_count': 30,
                    'total_amount': '3000.00',
                    'average_amount': '100.00',
                    'percentage_of_volume': 20.0
                }
            ],
            'generated_at': '2024-02-01T10:00:00'
        }
    
    @pytest.fixture
    def sample_user_activity_data(self):
        """Sample user activity report data"""
        return {
            'report_type': 'USER_ACTIVITY',
            'period': {
                'start_date': '2024-01-01T00:00:00',
                'end_date': '2024-01-31T23:59:59',
                'duration_days': 31
            },
            'summary': {
                'total_users': 25,
                'active_users': 20
            },
            'user_activities': [
                {
                    'user_id': 'user-1',
                    'user_name': 'John Doe',
                    'user_email': 'john.doe@example.com',
                    'user_role': 'EMPLOYEE',
                    'current_balance': '150.00',
                    'transaction_activity': {
                        'total_transactions': 15,
                        'sent_count': 8,
                        'received_count': 7,
                        'total_sent': '800.00',
                        'total_received': '700.00',
                        'net_amount': '-100.00'
                    },
                    'request_activity': {
                        'sent_requests': 3,
                        'received_requests': 2
                    },
                    'event_activity': {
                        'created_events': 1,
                        'event_contributions': 5
                    },
                    'last_login': '2024-01-30T15:30:00'
                }
            ],
            'generated_at': '2024-02-01T10:00:00'
        }
    
    @pytest.fixture
    def sample_event_account_data(self):
        """Sample event account report data"""
        return {
            'report_type': 'EVENT_ACCOUNT',
            'period': {
                'start_date': '2024-01-01T00:00:00',
                'end_date': '2024-01-31T23:59:59',
                'duration_days': 31
            },
            'summary': {
                'total_events': 10,
                'active_events': 6,
                'completed_events': 3,
                'expired_events': 1,
                'total_target_amount': '5000.00',
                'total_raised_amount': '3500.00',
                'overall_progress_percentage': 70.0
            },
            'events': [
                {
                    'event_id': 'event-1',
                    'event_name': 'Team Building Event',
                    'event_description': 'Annual team building activities',
                    'creator_id': 'user-1',
                    'creator_name': 'John Doe',
                    'status': 'ACTIVE',
                    'target_amount': '1000.00',
                    'current_amount': '750.00',
                    'remaining_amount': '250.00',
                    'progress_percentage': 75.0,
                    'contribution_count': 15,
                    'unique_contributors': 12,
                    'average_contribution': '50.00',
                    'created_at': '2024-01-15T10:00:00',
                    'deadline': '2024-02-15T23:59:59',
                    'is_expired': False
                }
            ],
            'generated_at': '2024-02-01T10:00:00'
        }
    
    @pytest.fixture
    def sample_personal_analytics_data(self):
        """Sample personal analytics report data"""
        return {
            'report_type': 'PERSONAL_ANALYTICS',
            'user_id': 'user-1',
            'user_name': 'John Doe',
            'period': {
                'start_date': '2024-01-01T00:00:00',
                'end_date': '2024-01-31T23:59:59',
                'duration_days': 31
            },
            'summary': {
                'total_transactions': 25,
                'total_sent': '1200.00',
                'total_received': '800.00',
                'net_amount': '-400.00',
                'current_balance': '150.00'
            },
            'spending_analysis': {
                'categories': [
                    {
                        'category': 'Food & Dining',
                        'amount': '600.00',
                        'percentage': 50.0
                    },
                    {
                        'category': 'Entertainment',
                        'amount': '400.00',
                        'percentage': 33.3
                    }
                ],
                'monthly_trends': [
                    {
                        'month': '2024-01',
                        'sent': '1200.00',
                        'received': '800.00',
                        'net': '-400.00'
                    }
                ]
            },
            'money_requests': {
                'sent_count': 5,
                'received_count': 3,
                'approved_sent': 4,
                'approved_received': 2
            },
            'event_participation': {
                'created_events': 1,
                'contributions_count': 8,
                'total_contributed': '400.00'
            },
            'generated_at': '2024-02-01T10:00:00'
        }
    
    def test_generate_transaction_summary_pdf(self, sample_transaction_summary_data):
        """Test transaction summary PDF generation"""
        pdf_bytes = PDFExportService.generate_transaction_summary_pdf(sample_transaction_summary_data)
        
        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 0
        assert pdf_bytes.startswith(b'%PDF')  # PDF file signature
        
        # Test that PDF contains expected content (basic check)
        pdf_content = pdf_bytes.decode('latin-1', errors='ignore')
        assert 'Transaction Summary Report' in pdf_content
        assert '15000.00' in pdf_content  # Total volume
        assert 'Food & Dining' in pdf_content  # Category
    
    def test_generate_user_activity_pdf(self, sample_user_activity_data):
        """Test user activity PDF generation"""
        pdf_bytes = PDFExportService.generate_user_activity_pdf(sample_user_activity_data)
        
        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 0
        assert pdf_bytes.startswith(b'%PDF')
        
        # Test that PDF contains expected content
        pdf_content = pdf_bytes.decode('latin-1', errors='ignore')
        assert 'User Activity Report' in pdf_content
        assert 'John Doe' in pdf_content
        assert 'john.doe@example.com' in pdf_content
    
    def test_generate_event_account_pdf(self, sample_event_account_data):
        """Test event account PDF generation"""
        pdf_bytes = PDFExportService.generate_event_account_pdf(sample_event_account_data)
        
        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 0
        assert pdf_bytes.startswith(b'%PDF')
        
        # Test that PDF contains expected content
        pdf_content = pdf_bytes.decode('latin-1', errors='ignore')
        assert 'Event Account Report' in pdf_content
        assert 'Team Building Event' in pdf_content
        assert '5000.00' in pdf_content  # Total target amount
    
    def test_generate_personal_analytics_pdf(self, sample_personal_analytics_data):
        """Test personal analytics PDF generation"""
        pdf_bytes = PDFExportService.generate_personal_analytics_pdf(sample_personal_analytics_data)
        
        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 0
        assert pdf_bytes.startswith(b'%PDF')
        
        # Test that PDF contains expected content
        pdf_content = pdf_bytes.decode('latin-1', errors='ignore')
        assert 'Personal Analytics Report' in pdf_content
        assert 'John Doe' in pdf_content
        assert '1200.00' in pdf_content  # Total sent
    
    def test_format_currency(self):
        """Test currency formatting"""
        # Test with string input
        assert PDFExportService._format_currency('100.00') == '£100.00'
        assert PDFExportService._format_currency('1234.56') == '£1,234.56'
        
        # Test with large numbers
        assert PDFExportService._format_currency('1000000.00') == '£1,000,000.00'
        
        # Test with invalid input
        result = PDFExportService._format_currency('invalid')
        assert result.startswith('£')
        assert 'invalid' in result
    
    def test_create_header(self):
        """Test PDF header creation"""
        elements = PDFExportService._create_header("Test Title", "Test Subtitle")
        
        assert len(elements) > 0
        # Should contain title, subtitle, horizontal rule, and spacer
        assert len(elements) >= 4
    
    def test_create_footer(self):
        """Test PDF footer creation"""
        elements = PDFExportService._create_footer()
        
        assert len(elements) > 0
        # Should contain spacer, horizontal rule, spacer, and footer text
        assert len(elements) >= 4
    
    def test_pdf_generation_with_empty_data(self):
        """Test PDF generation with minimal data"""
        minimal_data = {
            'report_type': 'TRANSACTION_SUMMARY',
            'period': {
                'start_date': '2024-01-01T00:00:00',
                'end_date': '2024-01-31T23:59:59',
                'duration_days': 31
            },
            'summary': {
                'total_transactions': 0,
                'total_volume': '0.00',
                'average_transaction_amount': '0.00',
                'transfer_count': 0,
                'event_contribution_count': 0,
                'average_transfer_amount': '0.00',
                'average_contribution_amount': '0.00'
            },
            'category_breakdown': [],
            'generated_at': '2024-02-01T10:00:00'
        }
        
        pdf_bytes = PDFExportService.generate_transaction_summary_pdf(minimal_data)
        
        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 0
        assert pdf_bytes.startswith(b'%PDF')
    
    def test_pdf_generation_with_large_dataset(self):
        """Test PDF generation with large dataset"""
        # Create large user activity data
        large_user_data = {
            'report_type': 'USER_ACTIVITY',
            'period': {
                'start_date': '2024-01-01T00:00:00',
                'end_date': '2024-01-31T23:59:59',
                'duration_days': 31
            },
            'summary': {
                'total_users': 100,
                'active_users': 80
            },
            'user_activities': [],
            'generated_at': '2024-02-01T10:00:00'
        }
        
        # Generate 50 users to test pagination
        for i in range(50):
            user_data = {
                'user_id': f'user-{i}',
                'user_name': f'User {i}',
                'user_email': f'user{i}@example.com',
                'user_role': 'EMPLOYEE',
                'current_balance': f'{100 + i}.00',
                'transaction_activity': {
                    'total_transactions': i * 2,
                    'sent_count': i,
                    'received_count': i,
                    'total_sent': f'{i * 50}.00',
                    'total_received': f'{i * 40}.00',
                    'net_amount': f'{i * -10}.00'
                },
                'request_activity': {
                    'sent_requests': i // 5,
                    'received_requests': i // 7
                },
                'event_activity': {
                    'created_events': i // 10,
                    'event_contributions': i // 3
                },
                'last_login': '2024-01-30T15:30:00'
            }
            large_user_data['user_activities'].append(user_data)
        
        pdf_bytes = PDFExportService.generate_user_activity_pdf(large_user_data)
        
        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 0
        assert pdf_bytes.startswith(b'%PDF')
        
        # Should be larger due to more content
        assert len(pdf_bytes) > 10000  # Reasonable size for 50 users
    
    def test_pdf_generation_error_handling(self):
        """Test PDF generation with invalid data"""
        invalid_data = {
            'report_type': 'TRANSACTION_SUMMARY',
            # Missing required fields
        }
        
        with pytest.raises(Exception):
            PDFExportService.generate_transaction_summary_pdf(invalid_data)
    
    def test_pdf_with_special_characters(self):
        """Test PDF generation with special characters"""
        data_with_special_chars = {
            'report_type': 'TRANSACTION_SUMMARY',
            'period': {
                'start_date': '2024-01-01T00:00:00',
                'end_date': '2024-01-31T23:59:59',
                'duration_days': 31
            },
            'summary': {
                'total_transactions': 1,
                'total_volume': '100.00',
                'average_transaction_amount': '100.00',
                'transfer_count': 1,
                'event_contribution_count': 0,
                'average_transfer_amount': '100.00',
                'average_contribution_amount': '0.00'
            },
            'category_breakdown': [
                {
                    'category': 'Café & Dining™',  # Special characters
                    'transaction_count': 1,
                    'total_amount': '100.00',
                    'average_amount': '100.00',
                    'percentage_of_volume': 100.0
                }
            ],
            'generated_at': '2024-02-01T10:00:00'
        }
        
        pdf_bytes = PDFExportService.generate_transaction_summary_pdf(data_with_special_chars)
        
        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 0
        assert pdf_bytes.startswith(b'%PDF')