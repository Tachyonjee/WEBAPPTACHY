from extensions import db
from .base import TimestampMixin

class MentorAssignment(db.Model, TimestampMixin):
    __tablename__ = 'mentor_assignments'
    
    id = db.Column(db.Integer, primary_key=True)
    mentor_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    batch_id = db.Column(db.Integer, db.ForeignKey('batches.id'), nullable=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=True)
    assignment_type = db.Column(db.Enum('batch', 'individual', name='assignment_types'), nullable=False)
    
    # Constraints: either batch_id or student_id should be set, not both
    __table_args__ = (
        db.CheckConstraint(
            '(batch_id IS NOT NULL AND student_id IS NULL) OR (batch_id IS NULL AND student_id IS NOT NULL)',
            name='check_assignment_type'
        ),
    )
    
    def __repr__(self):
        if self.batch_id:
            return f'<MentorAssignment mentor={self.mentor_user_id} batch={self.batch_id}>'
        else:
            return f'<MentorAssignment mentor={self.mentor_user_id} student={self.student_id}>'
