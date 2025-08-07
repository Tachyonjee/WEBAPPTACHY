from extensions import db
from .base import TimestampMixin

class Bookmark(db.Model, TimestampMixin):
    __tablename__ = 'bookmarks'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id'), nullable=False)
    
    # Constraints
    __table_args__ = (
        db.UniqueConstraint('student_id', 'question_id', name='unique_student_question_bookmark'),
    )
    
    def __repr__(self):
        return f'<Bookmark student={self.student_id} question={self.question_id}>'
