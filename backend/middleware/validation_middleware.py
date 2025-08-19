"""
Validation middleware for SoftBankCashWire API endpoints
Provides comprehensive input validation and sanitization
"""
from functools import wraps
from flask import request, jsonify
from decimal import Decimal, InvalidOperation
from datetime import datetime
import re
import html

class ValidationError(Exception):
    """Custom validation error"""
    def __init__(self, message, code='VALIDATION_ERROR'):
        self.message = message
        self.code = code
        super().__init__(self.message)

class InputValidator:
    """Input validation utilities"""
    
    # Common regex patterns
    EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    UUID_PATTERN = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$')
    PHONE_PATTERN = re.compile(r'^\+?[1-9]\d{1,14}$')
    
    @staticmethod
    def validate_string(value, field_name, min_length=0, max_length=None, required=True, pattern=None):
        """Validate string input"""
        if value is None or value == '':
            if required:
                raise ValidationError(f'{field_name} is required', 'MISSING_FIELD')
            return None
        
        if not isinstance(value, str):
            raise ValidationError(f'{field_name} must be a string', 'INVALID_TYPE')
        
        # Sanitize HTML
        value = html.escape(value.strip())
        
        if len(value) < min_length:
            raise ValidationError(f'{field_name} must be at least {min_length} characters', 'TOO_SHORT')
        
        if max_length and len(value) > max_length:
            raise ValidationError(f'{field_name} cannot exceed {max_length} characters', 'TOO_LONG')
        
        if pattern and not pattern.match(value):
            raise ValidationError(f'{field_name} format is invalid', 'INVALID_FORMAT')
        
        return value
    
    @staticmethod
    def validate_decimal(value, field_name, min_value=None, max_value=None, required=True, decimal_places=2):
        """Validate decimal/monetary input"""
        if value is None:
            if required:
                raise ValidationError(f'{field_name} is required', 'MISSING_FIELD')
            return None
        
        try:
            if isinstance(value, str):
                decimal_value = Decimal(value)
            elif isinstance(value, (int, float)):
                decimal_value = Decimal(str(value))
            else:
                raise ValidationError(f'{field_name} must be a number', 'INVALID_TYPE')
        except (InvalidOperation, ValueError):
            raise ValidationError(f'{field_name} must be a valid number', 'INVALID_NUMBER')
        
        # Round to specified decimal places
        decimal_value = decimal_value.quantize(Decimal('0.' + '0' * decimal_places))
        
        if min_value is not None and decimal_value < min_value:
            raise ValidationError(f'{field_name} must be at least {min_value}', 'TOO_SMALL')
        
        if max_value is not None and decimal_value > max_value:
            raise ValidationError(f'{field_name} cannot exceed {max_value}', 'TOO_LARGE')
        
        return decimal_value
    
    @staticmethod
    def validate_integer(value, field_name, min_value=None, max_value=None, required=True):
        """Validate integer input"""
        if value is None:
            if required:
                raise ValidationError(f'{field_name} is required', 'MISSING_FIELD')
            return None
        
        try:
            int_value = int(value)
        except (ValueError, TypeError):
            raise ValidationError(f'{field_name} must be an integer', 'INVALID_INTEGER')
        
        if min_value is not None and int_value < min_value:
            raise ValidationError(f'{field_name} must be at least {min_value}', 'TOO_SMALL')
        
        if max_value is not None and int_value > max_value:
            raise ValidationError(f'{field_name} cannot exceed {max_value}', 'TOO_LARGE')
        
        return int_value
    
    @staticmethod
    def validate_boolean(value, field_name, required=True):
        """Validate boolean input"""
        if value is None:
            if required:
                raise ValidationError(f'{field_name} is required', 'MISSING_FIELD')
            return None
        
        if not isinstance(value, bool):
            raise ValidationError(f'{field_name} must be true or false', 'INVALID_BOOLEAN')
        
        return value
    
    @staticmethod
    def validate_datetime(value, field_name, required=True, future_only=False, past_only=False):
        """Validate datetime input"""
        if value is None:
            if required:
                raise ValidationError(f'{field_name} is required', 'MISSING_FIELD')
            return None
        
        if isinstance(value, str):
            try:
                dt_value = datetime.fromisoformat(value.replace('Z', '+00:00'))
            except ValueError:
                raise ValidationError(f'{field_name} must be a valid ISO format datetime', 'INVALID_DATETIME')
        elif isinstance(value, datetime):
            dt_value = value
        else:
            raise ValidationError(f'{field_name} must be a datetime', 'INVALID_TYPE')
        
        now = datetime.now(datetime.UTC)
        
        if future_only and dt_value <= now:
            raise ValidationError(f'{field_name} must be in the future', 'MUST_BE_FUTURE')
        
        if past_only and dt_value >= now:
            raise ValidationError(f'{field_name} must be in the past', 'MUST_BE_PAST')
        
        return dt_value
    
    @staticmethod
    def validate_email(value, field_name, required=True):
        """Validate email input"""
        if value is None or value == '':
            if required:
                raise ValidationError(f'{field_name} is required', 'MISSING_FIELD')
            return None
        
        if not isinstance(value, str):
            raise ValidationError(f'{field_name} must be a string', 'INVALID_TYPE')
        
        value = value.strip().lower()
        
        if not InputValidator.EMAIL_PATTERN.match(value):
            raise ValidationError(f'{field_name} must be a valid email address', 'INVALID_EMAIL')
        
        return value
    
    @staticmethod
    def validate_uuid(value, field_name, required=True):
        """Validate UUID input"""
        if value is None or value == '':
            if required:
                raise ValidationError(f'{field_name} is required', 'MISSING_FIELD')
            return None
        
        if not isinstance(value, str):
            raise ValidationError(f'{field_name} must be a string', 'INVALID_TYPE')
        
        value = value.strip().lower()
        
        if not InputValidator.UUID_PATTERN.match(value):
            raise ValidationError(f'{field_name} must be a valid UUID', 'INVALID_UUID')
        
        return value
    
    @staticmethod
    def validate_list(value, field_name, min_items=0, max_items=None, required=True, item_validator=None):
        """Validate list input"""
        if value is None:
            if required:
                raise ValidationError(f'{field_name} is required', 'MISSING_FIELD')
            return None
        
        if not isinstance(value, list):
            raise ValidationError(f'{field_name} must be a list', 'INVALID_TYPE')
        
        if len(value) < min_items:
            raise ValidationError(f'{field_name} must have at least {min_items} items', 'TOO_FEW_ITEMS')
        
        if max_items and len(value) > max_items:
            raise ValidationError(f'{field_name} cannot have more than {max_items} items', 'TOO_MANY_ITEMS')
        
        # Validate each item if validator provided
        if item_validator:
            validated_items = []
            for i, item in enumerate(value):
                try:
                    validated_item = item_validator(item, f'{field_name}[{i}]')
                    validated_items.append(validated_item)
                except ValidationError as e:
                    raise ValidationError(f'{field_name}[{i}]: {e.message}', e.code)
            return validated_items
        
        return value
    
    @staticmethod
    def validate_choice(value, field_name, choices, required=True):
        """Validate choice from predefined options"""
        if value is None:
            if required:
                raise ValidationError(f'{field_name} is required', 'MISSING_FIELD')
            return None
        
        if value not in choices:
            raise ValidationError(f'{field_name} must be one of: {", ".join(map(str, choices))}', 'INVALID_CHOICE')
        
        return value

def validate_json_input(validation_schema):
    """
    Decorator to validate JSON input against a schema
    
    Args:
        validation_schema: Dictionary defining validation rules
        
    Example:
        @validate_json_input({
            'amount': {'type': 'decimal', 'min_value': 0.01, 'max_value': 10000},
            'recipient_id': {'type': 'uuid', 'required': True},
            'note': {'type': 'string', 'max_length': 500, 'required': False}
        })
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not request.is_json:
                return jsonify({
                    'error': {
                        'code': 'INVALID_CONTENT_TYPE',
                        'message': 'Content-Type must be application/json'
                    }
                }), 400
            
            try:
                data = request.get_json()
                if not data:
                    return jsonify({
                        'error': {
                            'code': 'MISSING_DATA',
                            'message': 'Request body is required'
                        }
                    }), 400
                
                validated_data = {}
                
                for field_name, rules in validation_schema.items():
                    field_type = rules.get('type', 'string')
                    value = data.get(field_name)
                    
                    try:
                        if field_type == 'string':
                            validated_data[field_name] = InputValidator.validate_string(
                                value, field_name,
                                min_length=rules.get('min_length', 0),
                                max_length=rules.get('max_length'),
                                required=rules.get('required', True),
                                pattern=rules.get('pattern')
                            )
                        
                        elif field_type == 'decimal':
                            validated_data[field_name] = InputValidator.validate_decimal(
                                value, field_name,
                                min_value=rules.get('min_value'),
                                max_value=rules.get('max_value'),
                                required=rules.get('required', True),
                                decimal_places=rules.get('decimal_places', 2)
                            )
                        
                        elif field_type == 'integer':
                            validated_data[field_name] = InputValidator.validate_integer(
                                value, field_name,
                                min_value=rules.get('min_value'),
                                max_value=rules.get('max_value'),
                                required=rules.get('required', True)
                            )
                        
                        elif field_type == 'boolean':
                            validated_data[field_name] = InputValidator.validate_boolean(
                                value, field_name,
                                required=rules.get('required', True)
                            )
                        
                        elif field_type == 'datetime':
                            validated_data[field_name] = InputValidator.validate_datetime(
                                value, field_name,
                                required=rules.get('required', True),
                                future_only=rules.get('future_only', False),
                                past_only=rules.get('past_only', False)
                            )
                        
                        elif field_type == 'email':
                            validated_data[field_name] = InputValidator.validate_email(
                                value, field_name,
                                required=rules.get('required', True)
                            )
                        
                        elif field_type == 'uuid':
                            validated_data[field_name] = InputValidator.validate_uuid(
                                value, field_name,
                                required=rules.get('required', True)
                            )
                        
                        elif field_type == 'list':
                            validated_data[field_name] = InputValidator.validate_list(
                                value, field_name,
                                min_items=rules.get('min_items', 0),
                                max_items=rules.get('max_items'),
                                required=rules.get('required', True),
                                item_validator=rules.get('item_validator')
                            )
                        
                        elif field_type == 'choice':
                            validated_data[field_name] = InputValidator.validate_choice(
                                value, field_name,
                                choices=rules.get('choices', []),
                                required=rules.get('required', True)
                            )
                        
                        else:
                            raise ValidationError(f'Unknown validation type: {field_type}', 'INVALID_VALIDATION_TYPE')
                    
                    except ValidationError as e:
                        return jsonify({
                            'error': {
                                'code': e.code,
                                'message': e.message,
                                'field': field_name
                            }
                        }), 400
                
                # Replace request data with validated data
                request.validated_data = validated_data
                
                return f(*args, **kwargs)
                
            except Exception as e:
                return jsonify({
                    'error': {
                        'code': 'VALIDATION_ERROR',
                        'message': f'Validation failed: {str(e)}'
                    }
                }), 400
        
        return decorated_function
    return decorator

def validate_query_params(validation_schema):
    """
    Decorator to validate query parameters
    
    Args:
        validation_schema: Dictionary defining validation rules for query params
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                validated_params = {}
                
                for param_name, rules in validation_schema.items():
                    param_type = rules.get('type', 'string')
                    value = request.args.get(param_name)
                    
                    try:
                        if param_type == 'string':
                            validated_params[param_name] = InputValidator.validate_string(
                                value, param_name,
                                min_length=rules.get('min_length', 0),
                                max_length=rules.get('max_length'),
                                required=rules.get('required', False),
                                pattern=rules.get('pattern')
                            )
                        
                        elif param_type == 'integer':
                            validated_params[param_name] = InputValidator.validate_integer(
                                value, param_name,
                                min_value=rules.get('min_value'),
                                max_value=rules.get('max_value'),
                                required=rules.get('required', False)
                            )
                        
                        elif param_type == 'boolean':
                            if value is not None:
                                value = value.lower() in ('true', '1', 'yes', 'on')
                            validated_params[param_name] = InputValidator.validate_boolean(
                                value, param_name,
                                required=rules.get('required', False)
                            )
                        
                        elif param_type == 'datetime':
                            validated_params[param_name] = InputValidator.validate_datetime(
                                value, param_name,
                                required=rules.get('required', False),
                                future_only=rules.get('future_only', False),
                                past_only=rules.get('past_only', False)
                            )
                        
                        elif param_type == 'choice':
                            validated_params[param_name] = InputValidator.validate_choice(
                                value, param_name,
                                choices=rules.get('choices', []),
                                required=rules.get('required', False)
                            )
                        
                        else:
                            raise ValidationError(f'Unknown validation type: {param_type}', 'INVALID_VALIDATION_TYPE')
                    
                    except ValidationError as e:
                        return jsonify({
                            'error': {
                                'code': e.code,
                                'message': e.message,
                                'parameter': param_name
                            }
                        }), 400
                
                # Add validated params to request
                request.validated_params = validated_params
                
                return f(*args, **kwargs)
                
            except Exception as e:
                return jsonify({
                    'error': {
                        'code': 'VALIDATION_ERROR',
                        'message': f'Parameter validation failed: {str(e)}'
                    }
                }), 400
        
        return decorated_function
    return decorator

def sanitize_output(data):
    """
    Sanitize output data to prevent XSS and data leakage
    
    Args:
        data: Data to sanitize (dict, list, or primitive)
        
    Returns:
        Sanitized data
    """
    if isinstance(data, dict):
        sanitized = {}
        for key, value in data.items():
            # Skip sensitive fields
            if key.lower() in ['password', 'secret', 'token', 'key']:
                continue
            sanitized[key] = sanitize_output(value)
        return sanitized
    
    elif isinstance(data, list):
        return [sanitize_output(item) for item in data]
    
    elif isinstance(data, str):
        # HTML escape strings
        return html.escape(data)
    
    else:
        return data