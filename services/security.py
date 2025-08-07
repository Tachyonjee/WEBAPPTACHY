import os
import secrets
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, g
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from extensions import db
from models.user import User, OTPVerification

class SecurityService:
    """Service for handling security-related operations"""
    
    # Rate limiting storage (in production, use Redis)
    _rate_limit_storage = {}
    
    @staticmethod
    def generate_secure_token(length=32):
        """Generate a secure random token"""
        return secrets.token_urlsafe(length)
    
    @staticmethod
    def check_otp_rate_limit(identifier):
        """
        Check if identifier (email/phone) has exceeded OTP rate limits
        Returns (is_allowed, remaining_hourly, remaining_daily)
        """
        now = datetime.utcnow()
        hour_key = f"otp_hourly_{identifier}_{now.strftime('%Y%m%d%H')}"
        day_key = f"otp_daily_{identifier}_{now.strftime('%Y%m%d')}"
        
        # Get current counts
        hourly_count = SecurityService._rate_limit_storage.get(hour_key, 0)
        daily_count = SecurityService._rate_limit_storage.get(day_key, 0)
        
        # Check limits (from config)
        from config import Config
        hourly_limit = Config.OTP_RATE_LIMIT_HOURLY
        daily_limit = Config.OTP_RATE_LIMIT_DAILY
        
        if hourly_count >= hourly_limit or daily_count >= daily_limit:
            return False, hourly_limit - hourly_count, daily_limit - daily_count
        
        return True, hourly_limit - hourly_count, daily_limit - daily_count
    
    @staticmethod
    def increment_otp_rate_limit(identifier):
        """Increment OTP rate limit counters"""
        now = datetime.utcnow()
        hour_key = f"otp_hourly_{identifier}_{now.strftime('%Y%m%d%H')}"
        day_key = f"otp_daily_{identifier}_{now.strftime('%Y%m%d')}"
        
        SecurityService._rate_limit_storage[hour_key] = SecurityService._rate_limit_storage.get(hour_key, 0) + 1
        SecurityService._rate_limit_storage[day_key] = SecurityService._rate_limit_storage.get(day_key, 0) + 1
    
    @staticmethod
    def clean_expired_otp_records():
        """Clean up expired OTP verification records"""
        expired_cutoff = datetime.utcnow() - timedelta(hours=1)
        OTPVerification.query.filter(
            OTPVerification.expires_at < expired_cutoff
        ).delete()
        db.session.commit()
    
    @staticmethod
    def validate_file_upload(file, allowed_extensions, max_size_mb=50):
        """
        Validate uploaded file
        
        Args:
            file: Flask file object
            allowed_extensions: List of allowed extensions (e.g., ['.csv', '.xlsx'])
            max_size_mb: Maximum file size in MB
            
        Returns:
            (is_valid, error_message)
        """
        if not file or not file.filename:
            return False, "No file selected"
        
        # Check extension
        file_ext = os.path.splitext(file.filename)[1].lower()
        if file_ext not in allowed_extensions:
            return False, f"File type not allowed. Allowed types: {', '.join(allowed_extensions)}"
        
        # Check file size (this is a basic check, actual size checking needs different approach)
        file.seek(0, 2)  # Seek to end
        size = file.tell()
        file.seek(0)  # Reset to beginning
        
        max_size_bytes = max_size_mb * 1024 * 1024
        if size > max_size_bytes:
            return False, f"File too large. Maximum size: {max_size_mb}MB"
        
        return True, None
    
    @staticmethod
    def sanitize_filename(filename):
        """Sanitize filename for safe storage"""
        # Remove path components
        filename = os.path.basename(filename)
        
        # Replace dangerous characters
        dangerous_chars = ['<', '>', ':', '"', '|', '?', '*', '/', '\\']
        for char in dangerous_chars:
            filename = filename.replace(char, '_')
        
        # Limit length
        if len(filename) > 255:
            name, ext = os.path.splitext(filename)
            filename = name[:255-len(ext)] + ext
        
        return filename

def role_required(*roles):
    """Decorator to require specific roles"""
    def decorator(f):
        @wraps(f)
        @jwt_required()
        def decorated_function(*args, **kwargs):
            current_user_id = get_jwt_identity()
            user = User.query.get(current_user_id)
            
            if not user or user.role not in roles:
                return jsonify({'message': 'Insufficient permissions'}), 403
            
            g.current_user = user
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator

def admin_required(f):
    """Decorator to require admin role"""
    return role_required('admin')(f)

def operator_required(f):
    """Decorator to require operator or admin role"""
    return role_required('operator', 'admin')(f)

def mentor_required(f):
    """Decorator to require mentor or admin role"""
    return role_required('mentor', 'admin')(f)

def student_required(f):
    """Decorator to require student role"""
    return role_required('student')(f)

def get_current_user():
    """Get current user from JWT token"""
    try:
        current_user_id = get_jwt_identity()
        return User.query.get(current_user_id)
    except:
        return None

def log_security_event(event_type, user_id=None, details=None):
    """Log security-related events (placeholder for future security logging)"""
    # In production, this would log to a security log file or service
    print(f"SECURITY EVENT: {event_type} - User: {user_id} - Details: {details}")
