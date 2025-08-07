from extensions import db
from .base import TimestampMixin

class PracticeRecommendation(db.Model, TimestampMixin):
    __tablename__ = 'practice_recommendations'
    
    id = db.Column(db.Integer, primary_key=True)
    lecture_id = db.Column(db.Integer, db.ForeignKey('lectures.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=True)  # null means for all students
    subject = db.Column(db.Enum('Physics', 'Chemistry', 'Biology', 'Mathematics', name='subjects'), nullable=False)
    topic = db.Column(db.String(100), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id'), nullable=False)
    syllabus_id = db.Column(db.Integer, db.ForeignKey('syllabus.id'), nullable=True)
    priority = db.Column(db.Integer, default=1, nullable=False)  # 1=high, 2=medium, 3=low
    is_completed = db.Column(db.Boolean, default=False, nullable=False)
    completed_at = db.Column(db.DateTime, nullable=True)
    
    # Constraints
    __table_args__ = (
        db.CheckConstraint('priority >= 1 AND priority <= 3', name='check_priority_range'),
    )
    
    def mark_completed(self):
        """Mark recommendation as completed"""
        self.is_completed = True
        self.completed_at = db.func.current_timestamp()
    
    def __repr__(self):
        return f'<PracticeRecommendation lecture={self.lecture_id} question={self.question_id}>'
