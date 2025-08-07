from extensions import db
from .base import TimestampMixin

class Attempt(db.Model, TimestampMixin):
    __tablename__ = 'attempts'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id'), nullable=False)
    session_id = db.Column(db.Integer, db.ForeignKey('practice_sessions.id'), nullable=True)
    chosen_answer = db.Column(db.Text, nullable=False)
    is_correct = db.Column(db.Boolean, nullable=False)
    time_taken = db.Column(db.Integer, nullable=False)  # seconds
    attempt_no = db.Column(db.Integer, default=1, nullable=False)  # 1 or 2
    seconds_elapsed = db.Column(db.Integer, nullable=False)  # total time spent
    timestamp = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp())
    
    # Constraints
    __table_args__ = (
        db.CheckConstraint('attempt_no >= 1 AND attempt_no <= 2', name='check_attempt_no_range'),
        db.Index('idx_student_question_session', 'student_id', 'question_id', 'session_id'),
    )
    
    def __repr__(self):
        return f'<Attempt student={self.student_id} question={self.question_id} correct={self.is_correct}>'
