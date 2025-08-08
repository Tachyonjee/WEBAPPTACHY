from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey, Date
from sqlalchemy.orm import relationship
from extensions import db

class AdmissionApplication(db.Model):
    __tablename__ = 'admission_applications'
    
    id = Column(Integer, primary_key=True)
    application_number = Column(String(20), unique=True, nullable=False)
    
    # Student Information
    student_name = Column(String(100), nullable=False)
    class_applied = Column(String(20), nullable=False)  # Class 11, 12, etc.
    batch_type = Column(String(50), nullable=False)  # JEE, NEET, Foundation
    date_of_birth = Column(Date, nullable=False)
    blood_group = Column(String(5))
    
    # Contact Information
    student_mobile = Column(String(15))
    address = Column(Text, nullable=False)
    
    # Parent Information
    father_name = Column(String(100), nullable=False)
    mother_name = Column(String(100), nullable=False)
    parent_mobile = Column(String(15), nullable=False)
    parent_email = Column(String(120))
    
    # Application Status
    status = Column(String(30), default='enquiry')
    application_date = Column(DateTime, default=datetime.now)
    admission_date = Column(DateTime)
    
    # Generated Accounts
    student_user_id = Column(Integer, ForeignKey('users.id'))
    parent_user_id = Column(Integer, ForeignKey('users.id'))
    student_user = relationship("User", foreign_keys=[student_user_id])
    parent_user = relationship("User", foreign_keys=[parent_user_id])
    
    # Processing Information
    created_by_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    created_by = relationship("User", foreign_keys=[created_by_id])
    processed_by_id = Column(Integer, ForeignKey('users.id'))
    processed_by = relationship("User", foreign_keys=[processed_by_id])
    
    # Documents and Additional Info
    documents = relationship("AdmissionDocument", back_populates="application", cascade="all, delete-orphan")
    digital_signature_path = Column(String(255))
    
    # Assessment Results
    assessment_completed = Column(Boolean, default=False)
    assessment_results = relationship("AssessmentResult", back_populates="application", cascade="all, delete-orphan")
    
    @staticmethod
    def generate_application_number():
        from datetime import datetime
        current_year = datetime.now().year
        last_app = AdmissionApplication.query.filter(
            AdmissionApplication.application_number.like(f'{current_year}%')
        ).order_by(AdmissionApplication.id.desc()).first()
        
        if last_app:
            last_number = int(last_app.application_number.split('-')[1])
            new_number = last_number + 1
        else:
            new_number = 1
            
        return f"{current_year}-{new_number:04d}"
    
    def __repr__(self):
        return f'<AdmissionApplication {self.application_number}: {self.student_name}>'

class AdmissionDocument(db.Model):
    __tablename__ = 'admission_documents'
    
    id = Column(Integer, primary_key=True)
    application_id = Column(Integer, ForeignKey('admission_applications.id'), nullable=False)
    application = relationship("AdmissionApplication", back_populates="documents")
    
    document_type = Column(String(50), nullable=False)  # birth_certificate, marksheet, photo, etc.
    file_path = Column(String(255), nullable=False)
    original_filename = Column(String(255))
    
    uploaded_at = Column(DateTime, default=datetime.now)
    uploaded_by_id = Column(Integer, ForeignKey('users.id'))
    # uploaded_by = relationship("User")
    
    verified = Column(Boolean, default=False)
    verified_at = Column(DateTime)
    verified_by_id = Column(Integer, ForeignKey('users.id'))
    # verified_by = relationship("User", foreign_keys=[verified_by_id])
    
    def __repr__(self):
        return f'<AdmissionDocument {self.document_type} for {self.application.student_name}>'

class AssessmentResult(db.Model):
    __tablename__ = 'assessment_results'
    
    id = Column(Integer, primary_key=True)
    application_id = Column(Integer, ForeignKey('admission_applications.id'), nullable=False)
    application = relationship("AdmissionApplication", back_populates="assessment_results")
    
    assessment_type = Column(String(50), nullable=False)  # listening, reading, math, physics, etc.
    score = Column(Integer, nullable=False)
    max_score = Column(Integer, nullable=False)
    percentage = Column(Integer)
    
    conducted_at = Column(DateTime, default=datetime.now)
    conducted_by_id = Column(Integer, ForeignKey('users.id'))
    # conducted_by = relationship("User")
    
    notes = Column(Text)
    
    def __repr__(self):
        return f'<AssessmentResult {self.assessment_type}: {self.score}/{self.max_score}>'