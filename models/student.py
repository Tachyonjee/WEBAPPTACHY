from extensions import db
from .base import TimestampMixin

class Student(db.Model, TimestampMixin):
    __tablename__ = 'students'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    batch = db.Column(db.String(50), nullable=True)
    goal_exam = db.Column(db.Enum('JEE', 'NEET', 'Other', name='exam_types'), nullable=False)
    
    # Relationships
    attempts = db.relationship('Attempt', backref='student', cascade='all, delete-orphan')
    doubts = db.relationship('Doubt', backref='student', cascade='all, delete-orphan')
    bookmarks = db.relationship('Bookmark', backref='student', cascade='all, delete-orphan')
    practice_sessions = db.relationship('PracticeSession', backref='student', cascade='all, delete-orphan')
    performance_summaries = db.relationship('PerformanceSummary', backref='student', cascade='all, delete-orphan')
    streak = db.relationship('Streak', backref='student', uselist=False, cascade='all, delete-orphan')
    points = db.relationship('Points', backref='student', uselist=False, cascade='all, delete-orphan')
    badges = db.relationship('Badges', backref='student', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Student {self.id}>'
