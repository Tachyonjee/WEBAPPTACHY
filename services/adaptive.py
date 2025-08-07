import random
from datetime import datetime, timedelta
from sqlalchemy import and_, func, desc
from extensions import db
from models.question import Question
from models.attempt import Attempt
from models.syllabus import Syllabus
from models.performance import PerformanceSummary

class AdaptiveEngine:
    """Adaptive question selection engine for personalized learning"""
    
    def __init__(self, student_id):
        self.student_id = student_id
    
    def get_next_question(self, session_id, mode, subjects=None, chapters=None, topics=None):
        """
        Get next question based on adaptive algorithm
        
        Args:
            session_id: Current practice session ID
            mode: Practice mode (adaptive, topic, chapter, etc.)
            subjects: List of subjects to include
            chapters: List of chapters to include
            topics: List of topics to include
            
        Returns:
            Question object or None if no questions available
        """
        # Build candidate pool based on mode
        query = Question.query.filter(Question.is_active == True)
        
        if mode == 'adaptive':
            # For adaptive mode, focus on weak areas
            weak_topic = self._get_weakest_topic(subjects)
            if weak_topic:
                query = query.filter(Question.topic == weak_topic)
            elif subjects:
                query = query.filter(Question.subject.in_(subjects))
        
        elif mode == 'topic' and topics:
            query = query.filter(Question.topic.in_(topics))
        
        elif mode == 'chapter' and chapters:
            query = query.filter(Question.chapter.in_(chapters))
        
        elif mode == 'multi_chapter' and chapters:
            query = query.filter(Question.chapter.in_(chapters))
        
        elif mode == 'multi_subject' and subjects:
            query = query.filter(Question.subject.in_(subjects))
        
        elif mode == 'revision':
            # Revision mode: questions attempted but with low accuracy
            revision_questions = self._get_revision_questions(subjects, chapters, topics)
            if revision_questions:
                query = query.filter(Question.id.in_(revision_questions))
            else:
                # Fallback to normal selection
                if subjects:
                    query = query.filter(Question.subject.in_(subjects))
        
        # Exclude recently seen questions (last 30)
        recent_questions = self._get_recent_questions(30)
        if recent_questions:
            query = query.filter(~Question.id.in_(recent_questions))
        
        # Get difficulty level based on performance
        target_difficulty = self._get_target_difficulty(subjects, topics)
        
        # Prefer questions at target difficulty, but allow ±1 range
        difficulty_range = [target_difficulty]
        if target_difficulty > 1:
            difficulty_range.append(target_difficulty - 1)
        if target_difficulty < 5:
            difficulty_range.append(target_difficulty + 1)
        
        # Try to get question at preferred difficulty
        preferred_questions = query.filter(Question.difficulty.in_(difficulty_range)).all()
        
        if preferred_questions:
            return random.choice(preferred_questions)
        
        # Fallback: any available question
        all_candidates = query.all()
        if all_candidates:
            return random.choice(all_candidates)
        
        # No questions available
        return None
    
    def _get_weakest_topic(self, subjects=None):
        """Find the topic with lowest recent accuracy"""
        # Look at attempts from last 30 days
        cutoff_date = datetime.utcnow() - timedelta(days=30)
        
        # Query for topic performance
        topic_stats = db.session.query(
            Question.topic,
            func.count(Attempt.id).label('total_attempts'),
            func.sum(Attempt.is_correct.cast(db.Integer)).label('correct_attempts')
        ).join(
            Attempt, Question.id == Attempt.question_id
        ).filter(
            Attempt.student_id == self.student_id,
            Attempt.created_at >= cutoff_date
        )
        
        if subjects:
            topic_stats = topic_stats.filter(Question.subject.in_(subjects))
        
        topic_stats = topic_stats.group_by(Question.topic).having(
            func.count(Attempt.id) >= 3  # At least 3 attempts
        ).all()
        
        if not topic_stats:
            # No sufficient data, return least covered topic
            return self._get_least_covered_topic(subjects)
        
        # Calculate accuracy for each topic and find the weakest
        weakest_topic = None
        lowest_accuracy = 1.0
        
        for topic, total, correct in topic_stats:
            accuracy = (correct or 0) / total if total > 0 else 0
            if accuracy < lowest_accuracy:
                lowest_accuracy = accuracy
                weakest_topic = topic
        
        return weakest_topic
    
    def _get_least_covered_topic(self, subjects=None):
        """Get topic with least number of attempts"""
        # Count attempts per topic
        topic_counts = db.session.query(
            Question.topic,
            func.count(Attempt.id).label('attempt_count')
        ).outerjoin(
            Attempt, and_(
                Question.id == Attempt.question_id,
                Attempt.student_id == self.student_id
            )
        )
        
        if subjects:
            topic_counts = topic_counts.filter(Question.subject.in_(subjects))
        
        topic_counts = topic_counts.group_by(Question.topic).order_by('attempt_count').first()
        
        return topic_counts.topic if topic_counts else None
    
    def _get_target_difficulty(self, subjects=None, topics=None):
        """Determine target difficulty based on recent performance"""
        # Get recent attempts (last 20)
        recent_attempts = Attempt.query.join(Question).filter(
            Attempt.student_id == self.student_id
        )
        
        if subjects:
            recent_attempts = recent_attempts.filter(Question.subject.in_(subjects))
        if topics:
            recent_attempts = recent_attempts.filter(Question.topic.in_(topics))
        
        recent_attempts = recent_attempts.order_by(desc(Attempt.created_at)).limit(20).all()
        
        if not recent_attempts:
            return 2  # Default to medium difficulty
        
        # Calculate recent accuracy
        correct_count = sum(1 for attempt in recent_attempts if attempt.is_correct)
        accuracy = correct_count / len(recent_attempts)
        
        # Get average difficulty of recent questions
        avg_difficulty = sum(attempt.question.difficulty for attempt in recent_attempts) / len(recent_attempts)
        
        # Adjust difficulty based on performance
        if accuracy >= 0.8:  # High accuracy, increase difficulty
            target = min(5, int(avg_difficulty) + 1)
        elif accuracy <= 0.4:  # Low accuracy, decrease difficulty
            target = max(1, int(avg_difficulty) - 1)
        else:  # Moderate accuracy, maintain level
            target = int(avg_difficulty)
        
        return target
    
    def _get_recent_questions(self, limit=30):
        """Get IDs of recently attempted questions"""
        recent_attempts = Attempt.query.filter(
            Attempt.student_id == self.student_id
        ).order_by(desc(Attempt.created_at)).limit(limit).all()
        
        return [attempt.question_id for attempt in recent_attempts]
    
    def _get_revision_questions(self, subjects=None, chapters=None, topics=None):
        """Get questions that need revision (attempted but with low accuracy)"""
        # Questions attempted at least twice but with accuracy < 60%
        question_stats = db.session.query(
            Question.id,
            func.count(Attempt.id).label('total_attempts'),
            func.sum(Attempt.is_correct.cast(db.Integer)).label('correct_attempts')
        ).join(
            Attempt, Question.id == Attempt.question_id
        ).filter(
            Attempt.student_id == self.student_id
        )
        
        if subjects:
            question_stats = question_stats.filter(Question.subject.in_(subjects))
        if chapters:
            question_stats = question_stats.filter(Question.chapter.in_(chapters))
        if topics:
            question_stats = question_stats.filter(Question.topic.in_(topics))
        
        question_stats = question_stats.group_by(Question.id).having(
            func.count(Attempt.id) >= 2
        ).all()
        
        revision_questions = []
        for question_id, total, correct in question_stats:
            accuracy = (correct or 0) / total if total > 0 else 0
            if accuracy < 0.6:  # Less than 60% accuracy
                revision_questions.append(question_id)
        
        return revision_questions

# Utility function for controllers
def get_adaptive_question(student_id, session_id, mode, subjects=None, chapters=None, topics=None):
    """Wrapper function for getting adaptive questions"""
    engine = AdaptiveEngine(student_id)
    return engine.get_next_question(session_id, mode, subjects, chapters, topics)
