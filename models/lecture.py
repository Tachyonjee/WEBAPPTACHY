from extensions import db
from .base import TimestampMixin

class Lecture(db.Model, TimestampMixin):
    __tablename__ = 'lectures'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    date = db.Column(db.Date, nullable=False)
    subject = db.Column(db.Enum('Physics', 'Chemistry', 'Biology', 'Mathematics', name='subjects'), nullable=False)
    resource_type = db.Column(db.Enum('youtube', 'video', name='resource_types'), nullable=False)
    resource_url = db.Column(db.String(500), nullable=False)
    notes = db.Column(db.Text, nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    duration_minutes = db.Column(db.Integer, nullable=True)
    thumbnail_url = db.Column(db.String(500), nullable=True)
    
    # Relationships
    creator = db.relationship('User', backref='created_lectures')
    topics = db.relationship('LectureTopics', backref='lecture', cascade='all, delete-orphan')
    practice_recommendations = db.relationship('PracticeRecommendation', backref='lecture', cascade='all, delete-orphan')
    
    def get_youtube_embed_url(self):
        """Convert YouTube URL to embed format"""
        if self.resource_type == 'youtube' and 'youtube.com/watch?v=' in self.resource_url:
            video_id = self.resource_url.split('watch?v=')[1].split('&')[0]
            return f"https://www.youtube.com/embed/{video_id}"
        elif self.resource_type == 'youtube' and 'youtu.be/' in self.resource_url:
            video_id = self.resource_url.split('youtu.be/')[1].split('?')[0]
            return f"https://www.youtube.com/embed/{video_id}"
        return self.resource_url
    
    def __repr__(self):
        return f'<Lecture {self.id}: {self.title}>'
