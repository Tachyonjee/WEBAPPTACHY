from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text
from sqlalchemy.orm import relationship
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db

class User(db.Model):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(80), unique=True, nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    password_hash = Column(String(256), nullable=False)
    full_name = Column(String(100), nullable=False)
    phone = Column(String(15))
    
    # Role-based access control
    # Roles: security, reception, counsellor, admin_coordinator, academic_coordinator, 
    #        principal, director, student, parent, mentor, operator, admin
    role = Column(String(30), nullable=False)
    
    # Status and timestamps
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    last_login = Column(DateTime)
    
    # Role-specific fields
    goal_exam = Column(String(20))  # For students: JEE, NEET, Foundation
    batch_name = Column(String(50))  # For students
    class_level = Column(String(20))  # Class 11, 12, etc.
    specialization = Column(String(50))  # For mentors: Math, Physics, Chemistry, etc.
    department = Column(String(50))  # For staff: Academic, Admin, Security, etc.
    
    # Parent-Student relationship
    parent_of_student_id = Column(Integer)  # If this user is a parent, student ID
    
    # Additional profile information
    address = Column(Text)
    emergency_contact = Column(String(15))
    
    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check if provided password matches hash"""
        return check_password_hash(self.password_hash, password)
    
    def update_last_login(self):
        """Update last login timestamp"""
        self.last_login = datetime.now()
        db.session.commit()
    
    def is_student(self):
        """Check if user is a student"""
        return self.role == 'student'
    
    def is_parent(self):
        """Check if user is a parent"""
        return self.role == 'parent'
    
    def is_staff(self):
        """Check if user is staff (any non-student/parent role)"""
        return self.role not in ['student', 'parent']
    
    def can_access_visitor_management(self):
        """Check if user can access visitor management features"""
        return self.role in ['security', 'reception', 'counsellor', 'admin_coordinator', 
                           'academic_coordinator', 'principal', 'director', 'admin']
    
    def can_manage_admissions(self):
        """Check if user can manage admissions"""
        return self.role in ['reception', 'admin_coordinator', 'academic_coordinator', 
                           'principal', 'director', 'admin']
    
    def can_conduct_classes(self):
        """Check if user can conduct classes"""
        return self.role in ['mentor', 'academic_coordinator', 'principal', 'director']
    
    @staticmethod
    def generate_student_credentials(student_name, admission_year=None):
        """Generate student login credentials"""
        if not admission_year:
            admission_year = datetime.now().year
        
        # Create username: first name + year + sequence
        first_name = student_name.split()[0].lower()
        base_username = f"{first_name}{admission_year}"
        
        # Find next available sequence number
        existing_users = User.query.filter(
            User.username.like(f"{base_username}%")
        ).all()
        
        sequence = len(existing_users) + 1
        username = f"{base_username}{sequence:02d}"
        
        # Generate simple password: username + "123"
        password = f"{username}123"
        
        return username, password
    
    @staticmethod
    def generate_parent_credentials(student_username):
        """Generate parent login credentials based on student username"""
        parent_username = f"p_{student_username}"
        parent_password = f"{parent_username}123"
        
        return parent_username, parent_password
    
    def __repr__(self):
        return f'<User {self.username}: {self.role}>'