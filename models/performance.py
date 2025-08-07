import json
from extensions import db
from .base import TimestampMixin

class PerformanceSummary(db.Model, TimestampMixin):
    __tablename__ = 'performance_summaries'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False, unique=True)
    subject = db.Column(db.Enum('Physics', 'Chemistry', 'Biology', 'Mathematics', name='subjects'), nullable=False)
    accuracy = db.Column(db.Float, nullable=False, default=0.0)
    avg_time = db.Column(db.Float, nullable=False, default=0.0)  # average time per question in seconds
    total_attempts = db.Column(db.Integer, nullable=False, default=0)
    correct_attempts = db.Column(db.Integer, nullable=False, default=0)
    weak_topics = db.Column(db.JSON, nullable=True)  # List of topics where accuracy < 60%
    last_updated = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp())
    
    # Constraints
    __table_args__ = (
        db.UniqueConstraint('student_id', 'subject', name='unique_student_subject_performance'),
        db.CheckConstraint('accuracy >= 0.0 AND accuracy <= 1.0', name='check_accuracy_range'),
    )
    
    def set_weak_topics(self, topics_list):
        """Set weak topics as JSON"""
        self.weak_topics = topics_list
    
    def get_weak_topics(self):
        """Get weak topics as list"""
        if isinstance(self.weak_topics, str):
            return json.loads(self.weak_topics)
        return self.weak_topics or []
    
    def update_performance(self, new_attempt_correct, new_attempt_time):
        """Update performance metrics with new attempt"""
        self.total_attempts += 1
        if new_attempt_correct:
            self.correct_attempts += 1
        
        # Recalculate accuracy
        self.accuracy = self.correct_attempts / self.total_attempts if self.total_attempts > 0 else 0.0
        
        # Update average time (weighted average)
        if self.total_attempts == 1:
            self.avg_time = new_attempt_time
        else:
            self.avg_time = ((self.avg_time * (self.total_attempts - 1)) + new_attempt_time) / self.total_attempts
        
        self.last_updated = db.func.current_timestamp()
    
    def __repr__(self):
        return f'<PerformanceSummary student={self.student_id} subject={self.subject} accuracy={self.accuracy:.2f}>'
