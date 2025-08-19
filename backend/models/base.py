"""
Base database configuration and utilities
"""
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import MetaData
import uuid
from datetime import datetime

# Define naming convention for constraints
convention = {
    "ix": 'ix_%(column_0_label)s',
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

metadata = MetaData(naming_convention=convention)
db = SQLAlchemy(metadata=metadata)

def generate_uuid():
    """Generate a UUID string for primary keys"""
    return str(uuid.uuid4())

def utc_now():
    """Get current UTC timestamp"""
    return datetime.utcnow()