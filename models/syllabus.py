from extensions import db
from .base import TimestampMixin

class Syllabus(db.Model, TimestampMixin):
    __tablename__ = 'syllabus'
    
    id = db.Column(db.Integer, primary_key=True)
    subject = db.Column(db.Enum('Physics', 'Chemistry', 'Biology', 'Mathematics', name='subjects'), nullable=False)
    chapter = db.Column(db.String(100), nullable=False)
    topic = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    order_in_chapter = db.Column(db.Integer, nullable=True)
    
    # Constraints
    __table_args__ = (
        db.UniqueConstraint('subject', 'chapter', 'topic', name='unique_syllabus_entry'),
    )
    
    # Relationships
    progress_records = db.relationship('SyllabusProgress', backref='syllabus_item', cascade='all, delete-orphan')
    lecture_topics = db.relationship('LectureTopics', backref='syllabus_item', cascade='all, delete-orphan')
    practice_recommendations = db.relationship('PracticeRecommendation', backref='syllabus_item')
    
    def __repr__(self):
        return f'<Syllabus {self.subject} - {self.chapter} - {self.topic}>'

class LectureTopics(db.Model, TimestampMixin):
    __tablename__ = 'lecture_topics'
    
    id = db.Column(db.Integer, primary_key=True)
    lecture_id = db.Column(db.Integer, db.ForeignKey('lectures.id'), nullable=False)
    syllabus_id = db.Column(db.Integer, db.ForeignKey('syllabus.id'), nullable=False)
    
    # Constraints
    __table_args__ = (
        db.UniqueConstraint('lecture_id', 'syllabus_id', name='unique_lecture_topic'),
    )
    
    def __repr__(self):
        return f'<LectureTopics lecture={self.lecture_id} syllabus={self.syllabus_id}>'
