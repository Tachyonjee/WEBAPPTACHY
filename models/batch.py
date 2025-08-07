from extensions import db
from .base import TimestampMixin

class Batch(db.Model, TimestampMixin):
    __tablename__ = 'batches'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    course = db.Column(db.Enum('JEE', 'NEET', 'Other', name='course_types'), nullable=False)
    description = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    # Relationships
    mentor_assignments = db.relationship('MentorAssignment', backref='batch', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Batch {self.name}>'
