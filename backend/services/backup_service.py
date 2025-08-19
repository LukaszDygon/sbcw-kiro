"""
Backup and data export service for SoftBankCashWire
Handles database backups, data retention, and recovery procedures
"""
import os
import shutil
import sqlite3
import gzip
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path
from cryptography.fernet import Fernet
from models import db
from config import Config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BackupService:
    """Service for database backup and recovery operations"""
    
    BACKUP_DIR = "backups"
    RETENTION_DAYS = 30  # Keep backups for 30 days
    ENCRYPTION_KEY_FILE = "backup_encryption.key"
    
    @classmethod
    def _ensure_backup_directory(cls) -> Path:
        """Ensure backup directory exists"""
        backup_path = Path(cls.BACKUP_DIR)
        backup_path.mkdir(exist_ok=True)
        return backup_path
    
    @classmethod
    def _get_encryption_key(cls) -> bytes:
        """Get or create encryption key for backups"""
        key_path = Path(cls.ENCRYPTION_KEY_FILE)
        
        if key_path.exists():
            with open(key_path, 'rb') as key_file:
                return key_file.read()
        else:
            # Generate new key
            key = Fernet.generate_key()
            with open(key_path, 'wb') as key_file:
                key_file.write(key)
            logger.info("Generated new backup encryption key")
            return key
    
    @classmethod
    def create_database_backup(cls, backup_name: str = None) -> Dict[str, Any]:
        """
        Create encrypted backup of the database
        
        Args:
            backup_name: Optional custom backup name
            
        Returns:
            Dictionary with backup information
        """
        try:
            backup_dir = cls._ensure_backup_directory()
            timestamp = datetime.now(datetime.UTC).strftime("%Y%m%d_%H%M%S")
            
            if backup_name:
                backup_filename = f"{backup_name}_{timestamp}.db.gz.enc"
            else:
                backup_filename = f"backup_{timestamp}.db.gz.enc"
            
            backup_path = backup_dir / backup_filename
            
            # Get database path from config
            db_path = Config.SQLALCHEMY_DATABASE_URI.replace('sqlite:///', '')
            
            if not os.path.exists(db_path):
                raise FileNotFoundError(f"Database file not found: {db_path}")
            
            # Create compressed backup
            temp_backup_path = backup_dir / f"temp_{timestamp}.db"
            shutil.copy2(db_path, temp_backup_path)
            
            # Compress the backup
            compressed_path = backup_dir / f"temp_{timestamp}.db.gz"
            with open(temp_backup_path, 'rb') as f_in:
                with gzip.open(compressed_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            # Encrypt the compressed backup
            encryption_key = cls._get_encryption_key()
            fernet = Fernet(encryption_key)
            
            with open(compressed_path, 'rb') as f_in:
                encrypted_data = fernet.encrypt(f_in.read())
            
            with open(backup_path, 'wb') as f_out:
                f_out.write(encrypted_data)
            
            # Clean up temporary files
            temp_backup_path.unlink()
            compressed_path.unlink()
            
            # Get backup file size
            backup_size = backup_path.stat().st_size
            
            # Create backup metadata
            metadata = {
                'backup_id': timestamp,
                'filename': backup_filename,
                'created_at': datetime.now(datetime.UTC).isoformat(),
                'size_bytes': backup_size,
                'size_mb': round(backup_size / (1024 * 1024), 2),
                'encrypted': True,
                'compressed': True,
                'database_path': db_path,
                'backup_type': 'full'
            }
            
            # Save metadata
            metadata_path = backup_dir / f"metadata_{timestamp}.json"
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            logger.info(f"Database backup created: {backup_filename} ({metadata['size_mb']} MB)")
            
            return {
                'success': True,
                'backup_info': metadata
            }
            
        except Exception as e:
            logger.error(f"Failed to create database backup: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    @classmethod
    def restore_database_backup(cls, backup_id: str, target_path: str = None) -> Dict[str, Any]:
        """
        Restore database from backup
        
        Args:
            backup_id: Backup ID to restore
            target_path: Optional target path for restored database
            
        Returns:
            Dictionary with restoration information
        """
        try:
            backup_dir = Path(cls.BACKUP_DIR)
            
            # Find backup files
            backup_file = None
            metadata_file = None
            
            for file_path in backup_dir.glob(f"*{backup_id}*"):
                if file_path.name.endswith('.db.gz.enc'):
                    backup_file = file_path
                elif file_path.name.startswith(f'metadata_{backup_id}'):
                    metadata_file = file_path
            
            if not backup_file or not metadata_file:
                raise FileNotFoundError(f"Backup files not found for ID: {backup_id}")
            
            # Load metadata
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
            
            # Decrypt backup
            encryption_key = cls._get_encryption_key()
            fernet = Fernet(encryption_key)
            
            with open(backup_file, 'rb') as f:
                encrypted_data = f.read()
            
            decrypted_data = fernet.decrypt(encrypted_data)
            
            # Decompress backup
            decompressed_data = gzip.decompress(decrypted_data)
            
            # Determine target path
            if not target_path:
                target_path = f"restored_database_{backup_id}.db"
            
            # Write restored database
            with open(target_path, 'wb') as f:
                f.write(decompressed_data)
            
            # Verify restored database
            try:
                conn = sqlite3.connect(target_path)
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = cursor.fetchall()
                conn.close()
                
                if not tables:
                    raise ValueError("Restored database appears to be empty")
                
            except Exception as e:
                os.remove(target_path)
                raise ValueError(f"Restored database is corrupted: {str(e)}")
            
            logger.info(f"Database restored from backup {backup_id} to {target_path}")
            
            return {
                'success': True,
                'restored_path': target_path,
                'backup_metadata': metadata,
                'tables_count': len(tables)
            }
            
        except Exception as e:
            logger.error(f"Failed to restore database backup: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    @classmethod
    def list_backups(cls) -> List[Dict[str, Any]]:
        """
        List all available backups
        
        Returns:
            List of backup information dictionaries
        """
        try:
            backup_dir = Path(cls.BACKUP_DIR)
            
            if not backup_dir.exists():
                return []
            
            backups = []
            
            for metadata_file in backup_dir.glob("metadata_*.json"):
                try:
                    with open(metadata_file, 'r') as f:
                        metadata = json.load(f)
                    
                    # Check if backup file still exists
                    backup_file = backup_dir / metadata['filename']
                    if backup_file.exists():
                        metadata['file_exists'] = True
                        metadata['current_size_mb'] = round(backup_file.stat().st_size / (1024 * 1024), 2)
                    else:
                        metadata['file_exists'] = False
                        metadata['current_size_mb'] = 0
                    
                    backups.append(metadata)
                    
                except Exception as e:
                    logger.warning(f"Failed to read backup metadata {metadata_file}: {str(e)}")
                    continue
            
            # Sort by creation date (newest first)
            backups.sort(key=lambda x: x['created_at'], reverse=True)
            
            return backups
            
        except Exception as e:
            logger.error(f"Failed to list backups: {str(e)}")
            return []
    
    @classmethod
    def cleanup_old_backups(cls) -> Dict[str, Any]:
        """
        Clean up backups older than retention period
        
        Returns:
            Dictionary with cleanup information
        """
        try:
            backup_dir = Path(cls.BACKUP_DIR)
            
            if not backup_dir.exists():
                return {'success': True, 'cleaned_count': 0, 'freed_mb': 0}
            
            cutoff_date = datetime.now(datetime.UTC) - timedelta(days=cls.RETENTION_DAYS)
            cleaned_count = 0
            freed_bytes = 0
            
            for metadata_file in backup_dir.glob("metadata_*.json"):
                try:
                    with open(metadata_file, 'r') as f:
                        metadata = json.load(f)
                    
                    backup_date = datetime.fromisoformat(metadata['created_at'])
                    
                    if backup_date < cutoff_date:
                        # Remove backup file
                        backup_file = backup_dir / metadata['filename']
                        if backup_file.exists():
                            freed_bytes += backup_file.stat().st_size
                            backup_file.unlink()
                        
                        # Remove metadata file
                        freed_bytes += metadata_file.stat().st_size
                        metadata_file.unlink()
                        
                        cleaned_count += 1
                        logger.info(f"Cleaned up old backup: {metadata['filename']}")
                        
                except Exception as e:
                    logger.warning(f"Failed to process backup metadata {metadata_file}: {str(e)}")
                    continue
            
            freed_mb = round(freed_bytes / (1024 * 1024), 2)
            
            logger.info(f"Backup cleanup completed: {cleaned_count} backups removed, {freed_mb} MB freed")
            
            return {
                'success': True,
                'cleaned_count': cleaned_count,
                'freed_mb': freed_mb,
                'retention_days': cls.RETENTION_DAYS
            }
            
        except Exception as e:
            logger.error(f"Failed to cleanup old backups: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    @classmethod
    def verify_backup_integrity(cls, backup_id: str) -> Dict[str, Any]:
        """
        Verify backup file integrity
        
        Args:
            backup_id: Backup ID to verify
            
        Returns:
            Dictionary with verification results
        """
        try:
            backup_dir = Path(cls.BACKUP_DIR)
            
            # Find backup files
            backup_file = None
            metadata_file = None
            
            for file_path in backup_dir.glob(f"*{backup_id}*"):
                if file_path.name.endswith('.db.gz.enc'):
                    backup_file = file_path
                elif file_path.name.startswith(f'metadata_{backup_id}'):
                    metadata_file = file_path
            
            if not backup_file or not metadata_file:
                return {
                    'success': False,
                    'error': f"Backup files not found for ID: {backup_id}"
                }
            
            # Load metadata
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
            
            # Check file size
            current_size = backup_file.stat().st_size
            expected_size = metadata['size_bytes']
            
            if current_size != expected_size:
                return {
                    'success': False,
                    'error': f"File size mismatch: expected {expected_size}, got {current_size}"
                }
            
            # Try to decrypt and decompress
            encryption_key = cls._get_encryption_key()
            fernet = Fernet(encryption_key)
            
            with open(backup_file, 'rb') as f:
                encrypted_data = f.read()
            
            try:
                decrypted_data = fernet.decrypt(encrypted_data)
                decompressed_data = gzip.decompress(decrypted_data)
                
                # Basic SQLite header check
                if not decompressed_data.startswith(b'SQLite format 3'):
                    return {
                        'success': False,
                        'error': "Backup does not contain valid SQLite database"
                    }
                
            except Exception as e:
                return {
                    'success': False,
                    'error': f"Failed to decrypt/decompress backup: {str(e)}"
                }
            
            return {
                'success': True,
                'backup_id': backup_id,
                'file_size_mb': round(current_size / (1024 * 1024), 2),
                'metadata': metadata,
                'integrity_check': 'passed'
            }
            
        except Exception as e:
            logger.error(f"Failed to verify backup integrity: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    @classmethod
    def get_backup_statistics(cls) -> Dict[str, Any]:
        """
        Get backup system statistics
        
        Returns:
            Dictionary with backup statistics
        """
        try:
            backups = cls.list_backups()
            
            if not backups:
                return {
                    'total_backups': 0,
                    'total_size_mb': 0,
                    'oldest_backup': None,
                    'newest_backup': None,
                    'average_size_mb': 0
                }
            
            total_size_mb = sum(backup['current_size_mb'] for backup in backups if backup['file_exists'])
            average_size_mb = round(total_size_mb / len(backups), 2) if backups else 0
            
            oldest_backup = min(backups, key=lambda x: x['created_at'])
            newest_backup = max(backups, key=lambda x: x['created_at'])
            
            return {
                'total_backups': len(backups),
                'total_size_mb': round(total_size_mb, 2),
                'oldest_backup': {
                    'id': oldest_backup['backup_id'],
                    'created_at': oldest_backup['created_at'],
                    'size_mb': oldest_backup['current_size_mb']
                },
                'newest_backup': {
                    'id': newest_backup['backup_id'],
                    'created_at': newest_backup['created_at'],
                    'size_mb': newest_backup['current_size_mb']
                },
                'average_size_mb': average_size_mb,
                'retention_days': cls.RETENTION_DAYS
            }
            
        except Exception as e:
            logger.error(f"Failed to get backup statistics: {str(e)}")
            return {
                'error': str(e)
            }