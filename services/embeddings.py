import json
import logging
from extensions import db
from models.embedding import Embedding
from models.question import Question
from models.lecture import Lecture

logger = logging.getLogger(__name__)

class EmbeddingService:
    """Service for creating and managing embeddings for semantic search"""
    
    def __init__(self):
        from config import Config
        self.api_key = Config.OPENAI_API_KEY
        self.enabled = Config.LLM_ENABLED
        
        if self.enabled and self.api_key:
            try:
                from openai import OpenAI
                self.client = OpenAI(api_key=self.api_key)
                self.model_name = "text-embedding-3-small"  # Latest embedding model
            except ImportError:
                logger.warning("OpenAI package not installed. Embedding features disabled.")
                self.enabled = False
        else:
            self.client = None
            self.model_name = "text-embedding-3-small"
    
    def create_question_embedding(self, question_id):
        """
        Create embedding for a question
        
        Args:
            question_id: Question ID
            
        Returns:
            bool: True if successful
        """
        try:
            question = Question.query.get(question_id)
            if not question:
                return False
            
            # Create text to embed
            text_to_embed = self._prepare_question_text(question)
            
            # Generate embedding
            embedding_vector = self._generate_embedding(text_to_embed)
            if not embedding_vector:
                return False
            
            # Save or update embedding
            existing = Embedding.query.filter_by(
                entity_type='question',
                entity_id=question_id,
                model_name=self.model_name
            ).first()
            
            if existing:
                existing.set_vector(embedding_vector)
            else:
                embedding = Embedding(
                    entity_type='question',
                    entity_id=question_id,
                    model_name=self.model_name
                )
                embedding.set_vector(embedding_vector)
                db.session.add(embedding)
            
            db.session.commit()
            return True
        
        except Exception as e:
            logger.error(f"Error creating question embedding: {str(e)}")
            return False
    
    def create_lecture_embedding(self, lecture_id):
        """
        Create embedding for a lecture
        
        Args:
            lecture_id: Lecture ID
            
        Returns:
            bool: True if successful
        """
        try:
            lecture = Lecture.query.get(lecture_id)
            if not lecture:
                return False
            
            # Create text to embed
            text_to_embed = self._prepare_lecture_text(lecture)
            
            # Generate embedding
            embedding_vector = self._generate_embedding(text_to_embed)
            if not embedding_vector:
                return False
            
            # Save or update embedding
            existing = Embedding.query.filter_by(
                entity_type='lecture',
                entity_id=lecture_id,
                model_name=self.model_name
            ).first()
            
            if existing:
                existing.set_vector(embedding_vector)
            else:
                embedding = Embedding(
                    entity_type='lecture',
                    entity_id=lecture_id,
                    model_name=self.model_name
                )
                embedding.set_vector(embedding_vector)
                db.session.add(embedding)
            
            db.session.commit()
            return True
        
        except Exception as e:
            logger.error(f"Error creating lecture embedding: {str(e)}")
            return False
    
    def find_similar_questions(self, question_id, limit=5):
        """
        Find questions similar to the given question
        
        Args:
            question_id: Question ID to find similar questions for
            limit: Maximum number of similar questions to return
            
        Returns:
            list: List of similar question IDs
        """
        try:
            # Get embedding for the question
            question_embedding = Embedding.query.filter_by(
                entity_type='question',
                entity_id=question_id,
                model_name=self.model_name
            ).first()
            
            if not question_embedding:
                return []
            
            # Get all question embeddings
            all_embeddings = Embedding.query.filter_by(
                entity_type='question',
                model_name=self.model_name
            ).filter(Embedding.entity_id != question_id).all()
            
            if not all_embeddings:
                return []
            
            # Calculate similarities (cosine similarity)
            similarities = []
            question_vector = question_embedding.get_vector()
            
            for embedding in all_embeddings:
                other_vector = embedding.get_vector()
                similarity = self._cosine_similarity(question_vector, other_vector)
                similarities.append((embedding.entity_id, similarity))
            
            # Sort by similarity and return top results
            similarities.sort(key=lambda x: x[1], reverse=True)
            return [entity_id for entity_id, _ in similarities[:limit]]
        
        except Exception as e:
            logger.error(f"Error finding similar questions: {str(e)}")
            return []
    
    def find_related_lectures(self, question_id, limit=3):
        """
        Find lectures related to a question
        
        Args:
            question_id: Question ID
            limit: Maximum number of related lectures to return
            
        Returns:
            list: List of related lecture IDs
        """
        try:
            # Get embedding for the question
            question_embedding = Embedding.query.filter_by(
                entity_type='question',
                entity_id=question_id,
                model_name=self.model_name
            ).first()
            
            if not question_embedding:
                return []
            
            # Get all lecture embeddings
            lecture_embeddings = Embedding.query.filter_by(
                entity_type='lecture',
                model_name=self.model_name
            ).all()
            
            if not lecture_embeddings:
                return []
            
            # Calculate similarities
            similarities = []
            question_vector = question_embedding.get_vector()
            
            for embedding in lecture_embeddings:
                lecture_vector = embedding.get_vector()
                similarity = self._cosine_similarity(question_vector, lecture_vector)
                similarities.append((embedding.entity_id, similarity))
            
            # Sort by similarity and return top results
            similarities.sort(key=lambda x: x[1], reverse=True)
            return [entity_id for entity_id, _ in similarities[:limit]]
        
        except Exception as e:
            logger.error(f"Error finding related lectures: {str(e)}")
            return []
    
    def batch_create_embeddings(self, entity_type='question', batch_size=100):
        """
        Create embeddings for all entities of a given type
        
        Args:
            entity_type: 'question' or 'lecture'
            batch_size: Number of entities to process at once
            
        Returns:
            dict: Summary of the operation
        """
        try:
            created_count = 0
            error_count = 0
            
            if entity_type == 'question':
                # Get all questions without embeddings
                questions = Question.query.filter(
                    ~Question.id.in_(
                        db.session.query(Embedding.entity_id).filter_by(
                            entity_type='question',
                            model_name=self.model_name
                        )
                    )
                ).limit(batch_size).all()
                
                for question in questions:
                    if self.create_question_embedding(question.id):
                        created_count += 1
                    else:
                        error_count += 1
            
            elif entity_type == 'lecture':
                # Get all lectures without embeddings
                lectures = Lecture.query.filter(
                    ~Lecture.id.in_(
                        db.session.query(Embedding.entity_id).filter_by(
                            entity_type='lecture',
                            model_name=self.model_name
                        )
                    )
                ).limit(batch_size).all()
                
                for lecture in lectures:
                    if self.create_lecture_embedding(lecture.id):
                        created_count += 1
                    else:
                        error_count += 1
            
            return {
                'created_count': created_count,
                'error_count': error_count,
                'total_processed': created_count + error_count
            }
        
        except Exception as e:
            logger.error(f"Error in batch embedding creation: {str(e)}")
            return {
                'created_count': 0,
                'error_count': 0,
                'total_processed': 0,
                'error': str(e)
            }
    
    def _generate_embedding(self, text):
        """Generate embedding vector for text"""
        try:
            if not self.enabled or not self.client:
                # Return a dummy embedding for development
                return [0.0] * 1536  # Standard embedding dimension
            
            response = self.client.embeddings.create(
                model=self.model_name,
                input=text
            )
            
            return response.data[0].embedding
        
        except Exception as e:
            logger.error(f"Error generating embedding: {str(e)}")
            return None
    
    def _prepare_question_text(self, question):
        """Prepare question text for embedding"""
        text_parts = [
            f"Subject: {question.subject}",
            f"Chapter: {question.chapter}",
            f"Topic: {question.topic}",
            f"Question: {question.question_text}"
        ]
        
        if question.options:
            options = question.get_options()
            for key, value in options.items():
                text_parts.append(f"Option {key}: {value}")
        
        return " ".join(text_parts)
    
    def _prepare_lecture_text(self, lecture):
        """Prepare lecture text for embedding"""
        text_parts = [
            f"Subject: {lecture.subject}",
            f"Title: {lecture.title}",
        ]
        
        if lecture.notes:
            text_parts.append(f"Notes: {lecture.notes}")
        
        # Add topic information if available
        for topic_link in lecture.topics:
            syllabus_item = topic_link.syllabus_item
            text_parts.append(f"Topic: {syllabus_item.chapter} - {syllabus_item.topic}")
        
        return " ".join(text_parts)
    
    def _cosine_similarity(self, vec1, vec2):
        """Calculate cosine similarity between two vectors"""
        try:
            import math
            
            # Dot product
            dot_product = sum(a * b for a, b in zip(vec1, vec2))
            
            # Magnitudes
            magnitude1 = math.sqrt(sum(a * a for a in vec1))
            magnitude2 = math.sqrt(sum(a * a for a in vec2))
            
            if magnitude1 == 0 or magnitude2 == 0:
                return 0
            
            return dot_product / (magnitude1 * magnitude2)
        
        except Exception:
            return 0

# Singleton instance
embedding_service = EmbeddingService()

def create_question_embedding(question_id):
    """Wrapper function for creating question embeddings"""
    return embedding_service.create_question_embedding(question_id)

def create_lecture_embedding(lecture_id):
    """Wrapper function for creating lecture embeddings"""
    return embedding_service.create_lecture_embedding(lecture_id)

def find_similar_questions(question_id, limit=5):
    """Wrapper function for finding similar questions"""
    return embedding_service.find_similar_questions(question_id, limit)

def find_related_lectures(question_id, limit=3):
    """Wrapper function for finding related lectures"""
    return embedding_service.find_related_lectures(question_id, limit)
