from datetime import datetime, timedelta
from extensions import db
from .base import TimestampMixin
from werkzeug.security import generate_password_hash, check_password_hash
import secrets

class User(db.Model, TimestampMixin):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(15), unique=True, nullable=True)
    role = db.Column(db.Enum('student', 'operator', 'mentor', 'admin', name='user_roles'), nullable=False)
    password_hash = db.Column(db.String(256), nullable=True)  # nullable for OTP-only users
    last_login = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    # Relationships
    student_profile = db.relationship('Student', backref='user', uselist=False, cascade='all, delete-orphan')
    mentor_assignments = db.relationship('MentorAssignment', backref='mentor', foreign_keys='MentorAssignment.mentor_user_id')
    
    def set_password(self, password):
        """Set password hash"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check password against hash"""
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)
    
    def update_last_login(self):
        """Update last login timestamp"""
        self.last_login = datetime.utcnow()
        db.session.commit()
    
    def __repr__(self):
        return f'<User {self.email}>'

class OTPVerification(db.Model, TimestampMixin):
    __tablename__ = 'otp_verifications'
    
    id = db.Column(db.Integer, primary_key=True)
    identifier = db.Column(db.String(120), nullable=False)  # email or phone
    otp_hash = db.Column(db.String(256), nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    attempts = db.Column(db.Integer, default=0, nullable=False)
    is_verified = db.Column(db.Boolean, default=False, nullable=False)
    
    @staticmethod
    def generate_otp():
        """Generate 6-digit OTP"""
        return f"{secrets.randbelow(1000000):06d}"
    
    def set_otp(self, otp):
        """Set OTP hash with 5-minute expiry"""
        self.otp_hash = generate_password_hash(otp)
        self.expires_at = datetime.utcnow() + timedelta(minutes=5)
    
    def verify_otp(self, otp):
        """Verify OTP against hash"""
        if self.expires_at < datetime.utcnow():
            return False
        if self.attempts >= 3:
            return False
        
        self.attempts += 1
        is_valid = check_password_hash(self.otp_hash, otp)
        
        if is_valid:
            self.is_verified = True
        
        db.session.commit()
        return is_valid
    
    def is_expired(self):
        """Check if OTP is expired"""
        return datetime.utcnow() > self.expires_at
