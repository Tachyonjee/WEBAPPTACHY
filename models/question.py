import json
from extensions import db
from .base import TimestampMixin

class Question(db.Model, TimestampMixin):
    __tablename__ = 'questions'
    
    id = db.Column(db.Integer, primary_key=True)
    subject = db.Column(db.Enum('Physics', 'Chemistry', 'Biology', 'Mathematics', name='subjects'), nullable=False)
    chapter = db.Column(db.String(100), nullable=False)
    topic = db.Column(db.String(100), nullable=False)
    difficulty = db.Column(db.Integer, nullable=False)  # 1-5
    question_text = db.Column(db.Text, nullable=False)
    options = db.Column(db.JSON, nullable=True)  # For MCQs
    correct_answer = db.Column(db.Text, nullable=False)
    hint = db.Column(db.Text, nullable=True)
    source = db.Column(db.String(100), nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    # Validation constraints
    __table_args__ = (
        db.CheckConstraint('difficulty >= 1 AND difficulty <= 5', name='check_difficulty_range'),
    )
    
    # Relationships
    attempts = db.relationship('Attempt', backref='question', cascade='all, delete-orphan')
    bookmarks = db.relationship('Bookmark', backref='question', cascade='all, delete-orphan')
    doubts = db.relationship('Doubt', backref='question')
    practice_recommendations = db.relationship('PracticeRecommendation', backref='question')
    
    def set_options(self, option_a, option_b, option_c, option_d):
        """Set options from individual values"""
        self.options = {
            'A': option_a,
            'B': option_b,
            'C': option_c,
            'D': option_d
        }
    
    def get_options(self):
        """Get options as dictionary"""
        if isinstance(self.options, str):
            return json.loads(self.options)
        return self.options or {}
    
    def __repr__(self):
        return f'<Question {self.id}: {self.subject} - {self.topic}>'
