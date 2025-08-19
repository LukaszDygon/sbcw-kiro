"""
Security Audit Service for SoftBankCashWire
Provides comprehensive security monitoring, threat detection, and compliance reporting
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from decimal import Decimal
from collections import defaultdict
import json
import logging
from models import db, User, Transaction, AuditLog, MoneyRequest, EventAccount
from services.audit_service import AuditService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SecurityAuditService:
    """Service for security auditing and threat detection"""
    
    # Security event types
    SECURITY_EVENT_TYPES = {
        'AUTHENTICATION': [
            'LOGIN_FAILED',
            'LOGIN_BLOCKED',
            'MULTIPLE_FAILED_ATTEMPTS',
            'SUSPICIOUS_LOGIN_PATTERN',
            'SESSION_HIJACK_ATTEMPT',
            'TOKEN_MANIPULATION'
        ],
        'AUTHORIZATION': [
            'UNAUTHORIZED_ACCESS_ATTEMPT',
            'PRIVILEGE_ESCALATION_ATTEMPT',
            'ROLE_MANIPULATION_ATTEMPT',
            'PERMISSION_BYPASS_ATTEMPT'
        ],
        'TRANSACTION_SECURITY': [
            'TRANSACTION_BLOCKED_FRAUD',
            'UNUSUAL_TRANSACTION_PATTERN',
            'RAPID_TRANSACTION_SEQUENCE',
            'HIGH_VALUE_TRANSACTION',
            'SUSPICIOUS_RECIPIENT_PATTERN'
        ],
        'SYSTEM_SECURITY': [
            'RATE_LIMIT_EXCEEDED',
            'CSRF_TOKEN_INVALID',
            'REQUEST_INTEGRITY_FAILED',
            'SUSPICIOUS_ACTIVITY_DETECTED',
            'SQL_INJECTION_ATTEMPT',
            'XSS_ATTEMPT'
        ],
        'DATA_SECURITY': [
            'SENSITIVE_DATA_ACCESS',
            'DATA_EXPORT_LARGE_VOLUME',
            'UNAUTHORIZED_DATA_MODIFICATION',
            'DATA_INTEGRITY_VIOLATION'
        ]
    }
    
    # Risk severity levels
    RISK_SEVERITY = {
        'CRITICAL': 4,
        'HIGH': 3,
        'MEDIUM': 2,
        'LOW': 1,
        'INFO': 0
    }
    
    @classmethod
    def analyze_security_events(cls, start_date: datetime, end_date: datetime) -> Dict:
        """
        Analyze security events in the specified time period
        
        Args:
            start_date: Analysis start date
            end_date: Analysis end date
            
        Returns:
            Dictionary with security analysis results
        """
        # Get security-related audit logs
        security_logs = AuditLog.query.filter(
            AuditLog.created_at >= start_date,
            AuditLog.created_at <= end_date,
            AuditLog.action_type.in_(cls._get_all_security_event_types())
        ).all()
        
        analysis = {
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'duration_days': (end_date - start_date).days
            },
            'summary': {
                'total_security_events': len(security_logs),
                'unique_users_affected': len(set(log.user_id for log in security_logs if log.user_id)),
                'unique_ips_involved': len(set(log.ip_address for log in security_logs if log.ip_address))
            },
            'event_breakdown': cls._analyze_event_breakdown(security_logs),
            'severity_analysis': cls._analyze_severity(security_logs),
            'temporal_analysis': cls._analyze_temporal_patterns(security_logs),
            'user_analysis': cls._analyze_user_patterns(security_logs),
            'ip_analysis': cls._analyze_ip_patterns(security_logs),
            'threat_indicators': cls._identify_threat_indicators(security_logs),
            'recommendations': cls._generate_security_recommendations(security_logs)
        }
        
        return analysis
    
    @classmethod
    def detect_anomalous_behavior(cls, user_id: str, days: int = 7) -> Dict:
        """
        Detect anomalous behavior for a specific user
        
        Args:
            user_id: User ID to analyze
            days: Number of days to analyze
            
        Returns:
            Dictionary with anomaly detection results
        """
        end_date = datetime.now(datetime.UTC)
        start_date = end_date - timedelta(days=days)
        
        # Get user's activities
        user_logs = AuditLog.query.filter(
            AuditLog.user_id == user_id,
            AuditLog.created_at >= start_date,
            AuditLog.created_at <= end_date
        ).all()
        
        user_transactions = Transaction.query.filter(
            Transaction.sender_id == user_id,
            Transaction.created_at >= start_date,
            Transaction.created_at <= end_date
        ).all()
        
        anomalies = {
            'user_id': user_id,
            'analysis_period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'days': days
            },
            'behavioral_anomalies': [],
            'risk_score': 0,
            'risk_level': 'LOW'
        }
        
        # Analyze login patterns
        login_anomalies = cls._detect_login_anomalies(user_id, user_logs)
        anomalies['behavioral_anomalies'].extend(login_anomalies)
        
        # Analyze transaction patterns
        transaction_anomalies = cls._detect_transaction_anomalies(user_id, user_transactions)
        anomalies['behavioral_anomalies'].extend(transaction_anomalies)
        
        # Analyze access patterns
        access_anomalies = cls._detect_access_anomalies(user_id, user_logs)
        anomalies['behavioral_anomalies'].extend(access_anomalies)
        
        # Calculate overall risk score
        anomalies['risk_score'] = sum(a['severity_score'] for a in anomalies['behavioral_anomalies'])
        
        # Determine risk level
        if anomalies['risk_score'] >= 80:
            anomalies['risk_level'] = 'CRITICAL'
        elif anomalies['risk_score'] >= 60:
            anomalies['risk_level'] = 'HIGH'
        elif anomalies['risk_score'] >= 40:
            anomalies['risk_level'] = 'MEDIUM'
        elif anomalies['risk_score'] >= 20:
            anomalies['risk_level'] = 'LOW'
        else:
            anomalies['risk_level'] = 'MINIMAL'
        
        return anomalies
    
    @classmethod
    def generate_security_compliance_report(cls, start_date: datetime, end_date: datetime) -> Dict:
        """
        Generate security compliance report
        
        Args:
            start_date: Report start date
            end_date: Report end date
            
        Returns:
            Dictionary with compliance report data
        """
        # Get all audit logs for the period
        all_logs = AuditLog.query.filter(
            AuditLog.created_at >= start_date,
            AuditLog.created_at <= end_date
        ).all()
        
        security_logs = [log for log in all_logs if log.action_type in cls._get_all_security_event_types()]
        
        report = {
            'report_type': 'SECURITY_COMPLIANCE',
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'duration_days': (end_date - start_date).days
            },
            'compliance_metrics': {
                'audit_coverage': {
                    'total_events_logged': len(all_logs),
                    'security_events_logged': len(security_logs),
                    'coverage_percentage': (len(security_logs) / len(all_logs) * 100) if all_logs else 0
                },
                'authentication_security': cls._assess_authentication_compliance(security_logs),
                'transaction_security': cls._assess_transaction_compliance(security_logs),
                'data_protection': cls._assess_data_protection_compliance(security_logs),
                'access_control': cls._assess_access_control_compliance(security_logs)
            },
            'security_incidents': cls._categorize_security_incidents(security_logs),
            'compliance_score': 0,
            'recommendations': []
        }
        
        # Calculate overall compliance score
        metrics = report['compliance_metrics']
        scores = [
            metrics['authentication_security']['compliance_score'],
            metrics['transaction_security']['compliance_score'],
            metrics['data_protection']['compliance_score'],
            metrics['access_control']['compliance_score']
        ]
        report['compliance_score'] = sum(scores) / len(scores) if scores else 0
        
        # Generate recommendations based on compliance gaps
        report['recommendations'] = cls._generate_compliance_recommendations(report)
        
        return report
    
    @classmethod
    def monitor_real_time_threats(cls) -> Dict:
        """
        Monitor real-time security threats
        
        Returns:
            Dictionary with current threat status
        """
        now = datetime.now(datetime.UTC)
        last_hour = now - timedelta(hours=1)
        last_24h = now - timedelta(hours=24)
        
        # Get recent security events
        recent_events = AuditLog.query.filter(
            AuditLog.created_at >= last_hour,
            AuditLog.action_type.in_(cls._get_all_security_event_types())
        ).all()
        
        daily_events = AuditLog.query.filter(
            AuditLog.created_at >= last_24h,
            AuditLog.action_type.in_(cls._get_all_security_event_types())
        ).all()
        
        threat_status = {
            'timestamp': now.isoformat(),
            'threat_level': 'LOW',
            'active_threats': [],
            'recent_activity': {
                'last_hour': len(recent_events),
                'last_24h': len(daily_events)
            },
            'critical_alerts': [],
            'monitoring_status': 'ACTIVE'
        }
        
        # Analyze recent events for active threats
        threat_status['active_threats'] = cls._identify_active_threats(recent_events)
        
        # Generate critical alerts
        threat_status['critical_alerts'] = cls._generate_critical_alerts(recent_events, daily_events)
        
        # Determine overall threat level
        if threat_status['critical_alerts']:
            threat_status['threat_level'] = 'CRITICAL'
        elif len(threat_status['active_threats']) > 5:
            threat_status['threat_level'] = 'HIGH'
        elif len(threat_status['active_threats']) > 2:
            threat_status['threat_level'] = 'MEDIUM'
        
        return threat_status
    
    @classmethod
    def _get_all_security_event_types(cls) -> List[str]:
        """Get all security event types"""
        all_types = []
        for category in cls.SECURITY_EVENT_TYPES.values():
            all_types.extend(category)
        return all_types
    
    @classmethod
    def _analyze_event_breakdown(cls, security_logs: List[AuditLog]) -> Dict:
        """Analyze breakdown of security events by category"""
        breakdown = {}
        
        for category, event_types in cls.SECURITY_EVENT_TYPES.items():
            category_events = [log for log in security_logs if log.action_type in event_types]
            breakdown[category] = {
                'count': len(category_events),
                'percentage': (len(category_events) / len(security_logs) * 100) if security_logs else 0,
                'event_types': {}
            }
            
            # Break down by specific event types
            for event_type in event_types:
                type_events = [log for log in category_events if log.action_type == event_type]
                if type_events:
                    breakdown[category]['event_types'][event_type] = len(type_events)
        
        return breakdown
    
    @classmethod
    def _analyze_severity(cls, security_logs: List[AuditLog]) -> Dict:
        """Analyze security events by severity"""
        severity_counts = defaultdict(int)
        
        for log in security_logs:
            severity = getattr(log, 'severity', 'MEDIUM')
            severity_counts[severity] += 1
        
        total = len(security_logs)
        return {
            severity: {
                'count': count,
                'percentage': (count / total * 100) if total > 0 else 0
            }
            for severity, count in severity_counts.items()
        }
    
    @classmethod
    def _analyze_temporal_patterns(cls, security_logs: List[AuditLog]) -> Dict:
        """Analyze temporal patterns in security events"""
        hourly_counts = defaultdict(int)
        daily_counts = defaultdict(int)
        
        for log in security_logs:
            hour = log.created_at.hour
            day = log.created_at.strftime('%Y-%m-%d')
            
            hourly_counts[hour] += 1
            daily_counts[day] += 1
        
        return {
            'hourly_distribution': dict(hourly_counts),
            'daily_distribution': dict(daily_counts),
            'peak_hour': max(hourly_counts.items(), key=lambda x: x[1])[0] if hourly_counts else None,
            'peak_day': max(daily_counts.items(), key=lambda x: x[1])[0] if daily_counts else None
        }
    
    @classmethod
    def _analyze_user_patterns(cls, security_logs: List[AuditLog]) -> Dict:
        """Analyze user patterns in security events"""
        user_counts = defaultdict(int)
        
        for log in security_logs:
            if log.user_id:
                user_counts[log.user_id] += 1
        
        # Sort users by event count
        sorted_users = sorted(user_counts.items(), key=lambda x: x[1], reverse=True)
        
        return {
            'total_users_involved': len(user_counts),
            'top_users': sorted_users[:10],
            'users_with_multiple_events': len([u for u, c in user_counts.items() if c > 1])
        }
    
    @classmethod
    def _analyze_ip_patterns(cls, security_logs: List[AuditLog]) -> Dict:
        """Analyze IP address patterns in security events"""
        ip_counts = defaultdict(int)
        
        for log in security_logs:
            if log.ip_address:
                ip_counts[log.ip_address] += 1
        
        # Sort IPs by event count
        sorted_ips = sorted(ip_counts.items(), key=lambda x: x[1], reverse=True)
        
        return {
            'total_ips_involved': len(ip_counts),
            'top_ips': sorted_ips[:10],
            'ips_with_multiple_events': len([ip for ip, c in ip_counts.items() if c > 1])
        }
    
    @classmethod
    def _identify_threat_indicators(cls, security_logs: List[AuditLog]) -> List[Dict]:
        """Identify potential threat indicators"""
        indicators = []
        
        # Check for brute force attempts
        failed_logins = [log for log in security_logs if log.action_type == 'LOGIN_FAILED']
        if len(failed_logins) > 10:
            indicators.append({
                'type': 'BRUTE_FORCE_ATTEMPT',
                'severity': 'HIGH',
                'description': f'{len(failed_logins)} failed login attempts detected',
                'count': len(failed_logins)
            })
        
        # Check for rate limit violations
        rate_limit_events = [log for log in security_logs if log.action_type == 'RATE_LIMIT_EXCEEDED']
        if len(rate_limit_events) > 20:
            indicators.append({
                'type': 'EXCESSIVE_RATE_LIMITING',
                'severity': 'MEDIUM',
                'description': f'{len(rate_limit_events)} rate limit violations detected',
                'count': len(rate_limit_events)
            })
        
        # Check for fraud attempts
        fraud_events = [log for log in security_logs if 'FRAUD' in log.action_type]
        if fraud_events:
            indicators.append({
                'type': 'FRAUD_ATTEMPTS',
                'severity': 'CRITICAL',
                'description': f'{len(fraud_events)} fraud attempts detected',
                'count': len(fraud_events)
            })
        
        return indicators
    
    @classmethod
    def _generate_security_recommendations(cls, security_logs: List[AuditLog]) -> List[Dict]:
        """Generate security recommendations based on analysis"""
        recommendations = []
        
        # Analyze failed logins
        failed_logins = [log for log in security_logs if log.action_type == 'LOGIN_FAILED']
        if len(failed_logins) > 50:
            recommendations.append({
                'priority': 'HIGH',
                'category': 'AUTHENTICATION',
                'recommendation': 'Implement account lockout after multiple failed attempts',
                'reason': f'{len(failed_logins)} failed login attempts detected'
            })
        
        # Analyze CSRF violations
        csrf_events = [log for log in security_logs if log.action_type == 'CSRF_TOKEN_INVALID']
        if csrf_events:
            recommendations.append({
                'priority': 'MEDIUM',
                'category': 'WEB_SECURITY',
                'recommendation': 'Review CSRF protection implementation',
                'reason': f'{len(csrf_events)} CSRF token violations detected'
            })
        
        # Analyze fraud events
        fraud_events = [log for log in security_logs if 'FRAUD' in log.action_type]
        if fraud_events:
            recommendations.append({
                'priority': 'CRITICAL',
                'category': 'FRAUD_PREVENTION',
                'recommendation': 'Review and enhance fraud detection rules',
                'reason': f'{len(fraud_events)} fraud attempts detected'
            })
        
        return recommendations
    
    @classmethod
    def _detect_login_anomalies(cls, user_id: str, user_logs: List[AuditLog]) -> List[Dict]:
        """Detect login anomalies for a user"""
        anomalies = []
        
        login_logs = [log for log in user_logs if log.action_type in ['USER_LOGIN', 'LOGIN_FAILED']]
        
        if not login_logs:
            return anomalies
        
        # Check for unusual login times
        login_hours = [log.created_at.hour for log in login_logs if log.action_type == 'USER_LOGIN']
        if login_hours:
            unusual_hours = [h for h in login_hours if h < 6 or h > 22]  # Before 6 AM or after 10 PM
            if len(unusual_hours) > len(login_hours) * 0.3:
                anomalies.append({
                    'type': 'UNUSUAL_LOGIN_HOURS',
                    'severity_score': 15,
                    'description': f'{len(unusual_hours)} logins at unusual hours',
                    'details': {'unusual_hours': unusual_hours}
                })
        
        # Check for multiple IP addresses
        ip_addresses = set(log.ip_address for log in login_logs if log.ip_address)
        if len(ip_addresses) > 5:
            anomalies.append({
                'type': 'MULTIPLE_LOGIN_IPS',
                'severity_score': 20,
                'description': f'Logins from {len(ip_addresses)} different IP addresses',
                'details': {'ip_count': len(ip_addresses)}
            })
        
        # Check for failed login attempts
        failed_logins = [log for log in login_logs if log.action_type == 'LOGIN_FAILED']
        if len(failed_logins) > 3:
            anomalies.append({
                'type': 'MULTIPLE_FAILED_LOGINS',
                'severity_score': 25,
                'description': f'{len(failed_logins)} failed login attempts',
                'details': {'failed_count': len(failed_logins)}
            })
        
        return anomalies
    
    @classmethod
    def _detect_transaction_anomalies(cls, user_id: str, transactions: List[Transaction]) -> List[Dict]:
        """Detect transaction anomalies for a user"""
        anomalies = []
        
        if not transactions:
            return anomalies
        
        # Check for unusual transaction amounts
        amounts = [t.amount for t in transactions]
        if amounts:
            avg_amount = sum(amounts) / len(amounts)
            max_amount = max(amounts)
            
            large_transactions = [t for t in transactions if t.amount > avg_amount * 5]
            if large_transactions:
                anomalies.append({
                    'type': 'UNUSUAL_TRANSACTION_AMOUNTS',
                    'severity_score': 30,
                    'description': f'{len(large_transactions)} transactions significantly above average',
                    'details': {
                        'average_amount': str(avg_amount),
                        'large_transaction_count': len(large_transactions)
                    }
                })
        
        # Check for high transaction frequency
        if len(transactions) > 50:  # More than 50 transactions in analysis period
            anomalies.append({
                'type': 'HIGH_TRANSACTION_FREQUENCY',
                'severity_score': 20,
                'description': f'{len(transactions)} transactions in analysis period',
                'details': {'transaction_count': len(transactions)}
            })
        
        # Check for rapid successive transactions
        sorted_transactions = sorted(transactions, key=lambda t: t.created_at)
        rapid_transactions = 0
        
        for i in range(1, len(sorted_transactions)):
            time_diff = sorted_transactions[i].created_at - sorted_transactions[i-1].created_at
            if time_diff.total_seconds() < 60:  # Less than 1 minute apart
                rapid_transactions += 1
        
        if rapid_transactions > 5:
            anomalies.append({
                'type': 'RAPID_SUCCESSIVE_TRANSACTIONS',
                'severity_score': 25,
                'description': f'{rapid_transactions} transactions within 1 minute of each other',
                'details': {'rapid_count': rapid_transactions}
            })
        
        return anomalies
    
    @classmethod
    def _detect_access_anomalies(cls, user_id: str, user_logs: List[AuditLog]) -> List[Dict]:
        """Detect access pattern anomalies for a user"""
        anomalies = []
        
        # Check for unusual endpoint access
        endpoint_access = defaultdict(int)
        for log in user_logs:
            if hasattr(log, 'endpoint') and log.endpoint:
                endpoint_access[log.endpoint] += 1
        
        # Check for excessive admin endpoint access (if user is not admin)
        admin_endpoints = [ep for ep in endpoint_access.keys() if 'admin' in ep.lower()]
        if admin_endpoints:
            total_admin_access = sum(endpoint_access[ep] for ep in admin_endpoints)
            if total_admin_access > 10:
                anomalies.append({
                    'type': 'EXCESSIVE_ADMIN_ACCESS',
                    'severity_score': 35,
                    'description': f'{total_admin_access} accesses to admin endpoints',
                    'details': {'admin_access_count': total_admin_access}
                })
        
        return anomalies
    
    @classmethod
    def _assess_authentication_compliance(cls, security_logs: List[AuditLog]) -> Dict:
        """Assess authentication security compliance"""
        auth_events = [log for log in security_logs if log.action_type in cls.SECURITY_EVENT_TYPES['AUTHENTICATION']]
        
        failed_logins = len([log for log in auth_events if log.action_type == 'LOGIN_FAILED'])
        blocked_logins = len([log for log in auth_events if log.action_type == 'LOGIN_BLOCKED'])
        
        # Calculate compliance score based on security measures
        compliance_score = 100
        
        if failed_logins > 100:
            compliance_score -= 20  # Too many failed logins
        
        if blocked_logins == 0 and failed_logins > 10:
            compliance_score -= 30  # No blocking despite failed attempts
        
        return {
            'compliance_score': max(0, compliance_score),
            'failed_logins': failed_logins,
            'blocked_logins': blocked_logins,
            'issues': []
        }
    
    @classmethod
    def _assess_transaction_compliance(cls, security_logs: List[AuditLog]) -> Dict:
        """Assess transaction security compliance"""
        transaction_events = [log for log in security_logs if log.action_type in cls.SECURITY_EVENT_TYPES['TRANSACTION_SECURITY']]
        
        blocked_transactions = len([log for log in transaction_events if 'BLOCKED' in log.action_type])
        fraud_attempts = len([log for log in transaction_events if 'FRAUD' in log.action_type])
        
        compliance_score = 100
        
        if fraud_attempts > 0 and blocked_transactions == 0:
            compliance_score -= 40  # Fraud detected but not blocked
        
        return {
            'compliance_score': max(0, compliance_score),
            'blocked_transactions': blocked_transactions,
            'fraud_attempts': fraud_attempts,
            'issues': []
        }
    
    @classmethod
    def _assess_data_protection_compliance(cls, security_logs: List[AuditLog]) -> Dict:
        """Assess data protection compliance"""
        data_events = [log for log in security_logs if log.action_type in cls.SECURITY_EVENT_TYPES['DATA_SECURITY']]
        
        return {
            'compliance_score': 95,  # Assume good compliance unless issues found
            'data_access_events': len(data_events),
            'issues': []
        }
    
    @classmethod
    def _assess_access_control_compliance(cls, security_logs: List[AuditLog]) -> Dict:
        """Assess access control compliance"""
        access_events = [log for log in security_logs if log.action_type in cls.SECURITY_EVENT_TYPES['AUTHORIZATION']]
        
        unauthorized_attempts = len([log for log in access_events if 'UNAUTHORIZED' in log.action_type])
        
        compliance_score = 100
        if unauthorized_attempts > 10:
            compliance_score -= 25
        
        return {
            'compliance_score': max(0, compliance_score),
            'unauthorized_attempts': unauthorized_attempts,
            'issues': []
        }
    
    @classmethod
    def _categorize_security_incidents(cls, security_logs: List[AuditLog]) -> Dict:
        """Categorize security incidents by severity"""
        incidents = {
            'CRITICAL': [],
            'HIGH': [],
            'MEDIUM': [],
            'LOW': []
        }
        
        for log in security_logs:
            severity = getattr(log, 'severity', 'MEDIUM')
            if severity in incidents:
                incidents[severity].append({
                    'timestamp': log.created_at.isoformat(),
                    'event_type': log.action_type,
                    'user_id': log.user_id,
                    'ip_address': log.ip_address
                })
        
        return incidents
    
    @classmethod
    def _generate_compliance_recommendations(cls, report: Dict) -> List[Dict]:
        """Generate compliance recommendations"""
        recommendations = []
        
        compliance_score = report['compliance_score']
        
        if compliance_score < 80:
            recommendations.append({
                'priority': 'HIGH',
                'category': 'OVERALL_SECURITY',
                'recommendation': 'Comprehensive security review required',
                'reason': f'Overall compliance score is {compliance_score}%'
            })
        
        # Add specific recommendations based on metrics
        metrics = report['compliance_metrics']
        
        if metrics['authentication_security']['compliance_score'] < 80:
            recommendations.append({
                'priority': 'HIGH',
                'category': 'AUTHENTICATION',
                'recommendation': 'Strengthen authentication security measures',
                'reason': 'Authentication compliance score below threshold'
            })
        
        return recommendations
    
    @classmethod
    def _identify_active_threats(cls, recent_events: List[AuditLog]) -> List[Dict]:
        """Identify active threats from recent events"""
        threats = []
        
        # Group events by type
        event_counts = defaultdict(int)
        for event in recent_events:
            event_counts[event.action_type] += 1
        
        # Check for active brute force
        if event_counts.get('LOGIN_FAILED', 0) > 5:
            threats.append({
                'type': 'ACTIVE_BRUTE_FORCE',
                'severity': 'HIGH',
                'count': event_counts['LOGIN_FAILED'],
                'description': 'Active brute force attack detected'
            })
        
        # Check for fraud attempts
        fraud_count = sum(count for event_type, count in event_counts.items() if 'FRAUD' in event_type)
        if fraud_count > 0:
            threats.append({
                'type': 'ACTIVE_FRAUD_ATTEMPTS',
                'severity': 'CRITICAL',
                'count': fraud_count,
                'description': 'Active fraud attempts detected'
            })
        
        return threats
    
    @classmethod
    def _generate_critical_alerts(cls, recent_events: List[AuditLog], daily_events: List[AuditLog]) -> List[Dict]:
        """Generate critical security alerts"""
        alerts = []
        
        # Check for critical events in last hour
        critical_events = [e for e in recent_events if getattr(e, 'severity', 'MEDIUM') == 'CRITICAL']
        if critical_events:
            alerts.append({
                'type': 'CRITICAL_SECURITY_EVENT',
                'severity': 'CRITICAL',
                'count': len(critical_events),
                'description': f'{len(critical_events)} critical security events in the last hour',
                'timestamp': datetime.now(datetime.UTC).isoformat()
            })
        
        # Check for unusual spike in security events
        if len(recent_events) > 50:  # More than 50 security events in 1 hour
            alerts.append({
                'type': 'SECURITY_EVENT_SPIKE',
                'severity': 'HIGH',
                'count': len(recent_events),
                'description': 'Unusual spike in security events detected',
                'timestamp': datetime.now(datetime.UTC).isoformat()
            })
        
        return alerts