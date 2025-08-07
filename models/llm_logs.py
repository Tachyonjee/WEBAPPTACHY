import json
from extensions import db
from .base import TimestampMixin

class LLMEvent(db.Model, TimestampMixin):
    __tablename__ = 'llm_events'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=True)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id'), nullable=True)
    event_type = db.Column(db.Enum('solution_request', 'solution_response', 'gen_question_request', 'gen_question_response', name='llm_event_types'), nullable=False)
    payload = db.Column(db.JSON, nullable=True)
    response_time_ms = db.Column(db.Integer, nullable=True)
    success = db.Column(db.Boolean, default=True, nullable=False)
    error_message = db.Column(db.Text, nullable=True)
    
    def set_payload(self, data):
        """Set payload as JSON"""
        self.payload = data
    
    def get_payload(self):
        """Get payload as dictionary"""
        if isinstance(self.payload, str):
            return json.loads(self.payload)
        return self.payload or {}
    
    def __repr__(self):
        return f'<LLMEvent {self.event_type} student={self.student_id}>'
