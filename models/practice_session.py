import json
from extensions import db
from .base import TimestampMixin

class PracticeSession(db.Model, TimestampMixin):
    __tablename__ = 'practice_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    mode = db.Column(db.Enum('adaptive', 'topic', 'chapter', 'multi_chapter', 'multi_subject', 'revision', name='practice_modes'), nullable=False)
    subjects = db.Column(db.JSON, nullable=True)  # List of subjects
    chapters = db.Column(db.JSON, nullable=True)  # List of chapters
    topics = db.Column(db.JSON, nullable=True)    # List of topics
    started_at = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp())
    ended_at = db.Column(db.DateTime, nullable=True)
    device_type = db.Column(db.Enum('kiosk', 'personal', name='device_types'), nullable=False, default='personal')
    total_questions = db.Column(db.Integer, default=0, nullable=False)
    correct_answers = db.Column(db.Integer, default=0, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    # Relationships
    attempts = db.relationship('Attempt', backref='session', cascade='all, delete-orphan')
    
    def set_subjects(self, subjects_list):
        """Set subjects as JSON"""
        self.subjects = subjects_list
    
    def get_subjects(self):
        """Get subjects as list"""
        if isinstance(self.subjects, str):
            return json.loads(self.subjects)
        return self.subjects or []
    
    def set_chapters(self, chapters_list):
        """Set chapters as JSON"""
        self.chapters = chapters_list
    
    def get_chapters(self):
        """Get chapters as list"""
        if isinstance(self.chapters, str):
            return json.loads(self.chapters)
        return self.chapters or []
    
    def set_topics(self, topics_list):
        """Set topics as JSON"""
        self.topics = topics_list
    
    def get_topics(self):
        """Get topics as list"""
        if isinstance(self.topics, str):
            return json.loads(self.topics)
        return self.topics or []
    
    def end_session(self):
        """End the practice session"""
        self.ended_at = db.func.current_timestamp()
        self.is_active = False
        
        # Calculate final stats
        self.total_questions = len(self.attempts)
        self.correct_answers = sum(1 for attempt in self.attempts if attempt.is_correct)
    
    def get_accuracy(self):
        """Get session accuracy"""
        if self.total_questions == 0:
            return 0.0
        return self.correct_answers / self.total_questions
    
    def __repr__(self):
        return f'<PracticeSession {self.id}: {self.mode} - student={self.student_id}>'
