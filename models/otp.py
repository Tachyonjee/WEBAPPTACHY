from extensions import db
from .base import BaseModel
from datetime import datetime, timedelta
import secrets
import hashlib

class OTPVerification(BaseModel):
    __tablename__ = 'otp_verifications'
    
    id = db.Column(db.Integer, primary_key=True)
    phone_email = db.Column(db.String(120), nullable=False)  # Phone or email
    otp_hash = db.Column(db.String(256), nullable=False)  # Hashed OTP
    expires_at = db.Column(db.DateTime, nullable=False)
    attempts = db.Column(db.Integer, default=0)
    is_verified = db.Column(db.Boolean, default=False)
    verification_type = db.Column(db.Enum('login', 'password_reset', name='verification_types'), default='login')
    
    @staticmethod
    def generate_otp():
        """Generate a 6-digit OTP"""
        return ''.join([str(secrets.randbelow(10)) for _ in range(6)])
    
    @staticmethod
    def hash_otp(otp):
        """Hash OTP for secure storage"""
        return hashlib.sha256(otp.encode()).hexdigest()
    
    def verify_otp(self, otp):
        """Verify if the provided OTP is correct"""
        if self.expires_at < datetime.utcnow():
            return False
        if self.attempts >= 3:
            return False
        
        self.attempts += 1
        if self.otp_hash == self.hash_otp(otp):
            self.is_verified = True
            return True
        return False
    
    @classmethod
    def create_otp_record(cls, phone_email, verification_type='login'):
        """Create a new OTP verification record"""
        otp = cls.generate_otp()
        record = cls(
            phone_email=phone_email,
            otp_hash=cls.hash_otp(otp),
            expires_at=datetime.utcnow() + timedelta(minutes=5),
            verification_type=verification_type
        )
        return record, otp
    
    def __repr__(self):
        return f'<OTPVerification {self.phone_email} - {self.verification_type}>'
