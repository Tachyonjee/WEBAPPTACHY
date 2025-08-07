import json
from extensions import db
from .base import TimestampMixin

class Embedding(db.Model, TimestampMixin):
    __tablename__ = 'embeddings'
    
    id = db.Column(db.Integer, primary_key=True)
    entity_type = db.Column(db.Enum('question', 'lecture', 'explanation', name='entity_types'), nullable=False)
    entity_id = db.Column(db.Integer, nullable=False)
    vector = db.Column(db.JSON, nullable=False)  # Store as JSON array
    model_name = db.Column(db.String(100), nullable=False)
    vector_dimension = db.Column(db.Integer, nullable=False)
    
    # Constraints
    __table_args__ = (
        db.UniqueConstraint('entity_type', 'entity_id', 'model_name', name='unique_entity_embedding'),
    )
    
    def set_vector(self, vector_list):
        """Set vector as JSON array"""
        self.vector = vector_list
        self.vector_dimension = len(vector_list) if vector_list else 0
    
    def get_vector(self):
        """Get vector as list"""
        if isinstance(self.vector, str):
            return json.loads(self.vector)
        return self.vector or []
    
    def __repr__(self):
        return f'<Embedding {self.entity_type}={self.entity_id} model={self.model_name}>'
