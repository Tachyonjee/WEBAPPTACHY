from extensions import db
from .base import TimestampMixin

class Doubt(db.Model, TimestampMixin):
    __tablename__ = 'doubts'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id'), nullable=True)
    message = db.Column(db.Text, nullable=False)
    status = db.Column(db.Enum('open', 'resolved', name='doubt_status'), default='open', nullable=False)
    response = db.Column(db.Text, nullable=True)
    resolved_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    resolved_at = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    resolver = db.relationship('User', foreign_keys=[resolved_by])
    
    def mark_resolved(self, response, resolved_by_user_id):
        """Mark doubt as resolved"""
        self.status = 'resolved'
        self.response = response
        self.resolved_by = resolved_by_user_id
        self.resolved_at = db.func.current_timestamp()
    
    def __repr__(self):
        return f'<Doubt {self.id}: {self.status}>'
