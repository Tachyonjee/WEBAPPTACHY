from extensions import db
from .base import TimestampMixin

class SyllabusProgress(db.Model, TimestampMixin):
    __tablename__ = 'syllabus_progress'
    
    id = db.Column(db.Integer, primary_key=True)
    owner_type = db.Column(db.Enum('student', 'batch', 'mentor', name='owner_types'), nullable=False)
    owner_id = db.Column(db.Integer, nullable=False)  # student_id, batch_id, or mentor_user_id
    syllabus_id = db.Column(db.Integer, db.ForeignKey('syllabus.id'), nullable=False)
    status = db.Column(db.Enum('not_started', 'in_progress', 'completed', name='progress_status'), default='not_started', nullable=False)
    completion_percentage = db.Column(db.Float, default=0.0, nullable=False)
    last_updated = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp())
    notes = db.Column(db.Text, nullable=True)
    
    # Constraints
    __table_args__ = (
        db.UniqueConstraint('owner_type', 'owner_id', 'syllabus_id', name='unique_owner_syllabus_progress'),
        db.CheckConstraint('completion_percentage >= 0.0 AND completion_percentage <= 100.0', name='check_completion_percentage'),
    )
    
    def update_progress(self, percentage, status=None):
        """Update progress percentage and optionally status"""
        self.completion_percentage = max(0.0, min(100.0, percentage))
        
        if status:
            self.status = status
        elif percentage == 0.0:
            self.status = 'not_started'
        elif percentage == 100.0:
            self.status = 'completed'
        else:
            self.status = 'in_progress'
        
        self.last_updated = db.func.current_timestamp()
    
    def __repr__(self):
        return f'<SyllabusProgress {self.owner_type}={self.owner_id} syllabus={self.syllabus_id} {self.completion_percentage}%>'
