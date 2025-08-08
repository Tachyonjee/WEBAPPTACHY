from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from extensions import db

class Visitor(db.Model):
    __tablename__ = 'visitors'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    phone = Column(String(15))
    email = Column(String(120))
    purpose = Column(String(200), nullable=False)
    id_type = Column(String(20))  # Aadhaar, PAN, etc.
    id_number = Column(String(50))
    face_image_path = Column(String(255))  # Path to captured face image
    
    # Timestamps
    time_in = Column(DateTime, default=datetime.now, nullable=False)
    time_out = Column(DateTime)
    
    # Status tracking
    status = Column(String(20), default='checked_in')  # checked_in, in_meeting, checked_out
    
    # Assignment tracking
    assigned_to_role = Column(String(50))  # counsellor, admin_coordinator, etc.
    assigned_to_user_id = Column(Integer, ForeignKey('users.id'))
    assigned_to = relationship("User", foreign_keys=[assigned_to_user_id])
    
    # Entry tracking
    logged_by_user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    logged_by = relationship("User", foreign_keys=[logged_by_user_id])
    
    # Meeting notes and follow-ups
    meetings = relationship("VisitorMeeting", back_populates="visitor", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<Visitor {self.name}>'

class VisitorMeeting(db.Model):
    __tablename__ = 'visitor_meetings'
    
    id = Column(Integer, primary_key=True)
    visitor_id = Column(Integer, ForeignKey('visitors.id'), nullable=False)
    visitor = relationship("Visitor", back_populates="meetings")
    
    conducted_by_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    conducted_by = relationship("User")
    
    meeting_time = Column(DateTime, default=datetime.now)
    notes = Column(Text)
    outcome = Column(String(100))  # interested, not_interested, follow_up_required
    
    # Follow-up tracking
    follow_up_required = Column(Boolean, default=False)
    follow_up_deadline = Column(DateTime)
    follow_up_notes = Column(Text)
    follow_up_completed = Column(Boolean, default=False)
    follow_up_completed_at = Column(DateTime)
    
    def __repr__(self):
        return f'<VisitorMeeting {self.visitor.name} by {self.conducted_by.username}>'