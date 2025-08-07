import random
from datetime import datetime, timedelta
from sqlalchemy import and_, func, desc
from extensions import db
from models.question import Question
from models.lecture import Lecture
from models.practice_recommendation import PracticeRecommendation
from models.syllabus import Syllabus, LectureTopics
from models.attempt import Attempt
from models.performance import PerformanceSummary
from services.embeddings import embedding_service

class RecommendationService:
    """Service for generating practice recommendations"""
    
    def __init__(self):
        pass
    
    def generate_lecture_recommendations(self, lecture_id):
        """
        Generate practice recommendations after a lecture
        
        Args:
            lecture_id: Lecture ID
            
        Returns:
            int: Number of recommendations created
        """
        try:
            lecture = Lecture.query.get(lecture_id)
            if not lecture:
                return 0
            
            # Get topics covered in the lecture
            lecture_topics = LectureTopics.query.filter_by(lecture_id=lecture_id).all()
            
            if not lecture_topics:
                # If no specific topics, use general subject-based recommendations
                return self._generate_subject_recommendations(lecture)
            
            recommendations_created = 0
            
            for lecture_topic in lecture_topics:
                syllabus_item = lecture_topic.syllabus_item
                
                # Find questions for this topic
                questions = Question.query.filter_by(
                    subject=syllabus_item.subject,
                    chapter=syllabus_item.chapter,
                    topic=syllabus_item.topic,
                    is_active=True
                ).filter(
                    Question.difficulty.between(2, 3)  # Medium difficulty for post-lecture practice
                ).limit(5).all()
                
                # Create recommendations for each question
                for question in questions:
                    recommendation = PracticeRecommendation(
                        lecture_id=lecture_id,
                        subject=syllabus_item.subject,
                        topic=syllabus_item.topic,
                        question_id=question.id,
                        syllabus_id=syllabus_item.id,
                        priority=1  # High priority for post-lecture practice
                    )
                    
                    db.session.add(recommendation)
                    recommendations_created += 1
            
            db.session.commit()
            return recommendations_created
        
        except Exception as e:
            db.session.rollback()
            return 0
    
    def get_personalized_recommendations(self, student_id, limit=10):
        """
        Get personalized practice recommendations for a student
        
        Args:
            student_id: Student ID
            limit: Maximum number of recommendations
            
        Returns:
            list: List of recommended questions with metadata
        """
        try:
            recommendations = []
            
            # Get weak topics for the student
            weak_topics = self._get_student_weak_topics(student_id)
            
            # Get recent lecture recommendations
            lecture_recs = self._get_lecture_recommendations(student_id, limit // 2)
            recommendations.extend(lecture_recs)
            
            # Get weak topic recommendations
            remaining_limit = limit - len(recommendations)
            if remaining_limit > 0 and weak_topics:
                weak_topic_recs = self._get_weak_topic_recommendations(
                    student_id, weak_topics, remaining_limit
                )
                recommendations.extend(weak_topic_recs)
            
            # Fill remaining slots with general recommendations
            remaining_limit = limit - len(recommendations)
            if remaining_limit > 0:
                general_recs = self._get_general_recommendations(
                    student_id, remaining_limit
                )
                recommendations.extend(general_recs)
            
            return recommendations[:limit]
        
        except Exception as e:
            return []
    
    def get_revision_recommendations(self, student_id, limit=10):
        """
        Get revision recommendations based on previous mistakes
        
        Args:
            student_id: Student ID
            limit: Maximum number of recommendations
            
        Returns:
            list: List of questions to revise
        """
        try:
            # Get questions attempted incorrectly in the last 30 days
            cutoff_date = datetime.utcnow() - timedelta(days=30)
            
            incorrect_questions = db.session.query(
                Question.id,
                Question.subject,
                Question.chapter,
                Question.topic,
                Question.difficulty,
                func.count(Attempt.id).label('attempt_count'),
                func.max(Attempt.created_at).label('last_attempt')
            ).join(
                Attempt, Question.id == Attempt.question_id
            ).filter(
                Attempt.student_id == student_id,
                Attempt.is_correct == False,
                Attempt.created_at >= cutoff_date
            ).group_by(Question.id).order_by(
                desc('last_attempt')
            ).limit(limit).all()
            
            revision_recommendations = []
            
            for q_id, subject, chapter, topic, difficulty, attempts, last_attempt in incorrect_questions:
                # Check if student has since answered correctly
                recent_correct = Attempt.query.filter_by(
                    student_id=student_id,
                    question_id=q_id,
                    is_correct=True
                ).filter(
                    Attempt.created_at > last_attempt
                ).first()
                
                if not recent_correct:  # Still needs revision
                    revision_recommendations.append({
                        'question_id': q_id,
                        'subject': subject,
                        'chapter': chapter,
                        'topic': topic,
                        'difficulty': difficulty,
                        'type': 'revision',
                        'reason': f'Incorrect {attempts} time(s)',
                        'priority': min(attempts, 3),  # Higher attempts = higher priority
                        'last_attempted': last_attempt.isoformat() if last_attempt else None
                    })
            
            return revision_recommendations
        
        except Exception as e:
            return []
    
    def get_similar_questions_recommendation(self, question_id, student_id, limit=5):
        """
        Get recommendations for questions similar to a given question
        
        Args:
            question_id: Base question ID
            student_id: Student ID
            limit: Maximum number of recommendations
            
        Returns:
            list: List of similar questions
        """
        try:
            # First try using embeddings for semantic similarity
            similar_question_ids = embedding_service.find_similar_questions(question_id, limit * 2)
            
            # Filter out already attempted questions
            attempted_question_ids = set(
                attempt.question_id for attempt in 
                Attempt.query.filter_by(student_id=student_id).all()
            )
            
            similar_recommendations = []
            
            for similar_id in similar_question_ids:
                if similar_id not in attempted_question_ids and len(similar_recommendations) < limit:
                    question = Question.query.get(similar_id)
                    if question and question.is_active:
                        similar_recommendations.append({
                            'question_id': similar_id,
                            'subject': question.subject,
                            'chapter': question.chapter,
                            'topic': question.topic,
                            'difficulty': question.difficulty,
                            'type': 'similar',
                            'reason': 'Similar to your recent practice',
                            'priority': 2
                        })
            
            # If not enough similar questions found, use topic-based similarity
            if len(similar_recommendations) < limit:
                original_question = Question.query.get(question_id)
                if original_question:
                    topic_questions = Question.query.filter_by(
                        subject=original_question.subject,
                        topic=original_question.topic,
                        is_active=True
                    ).filter(
                        Question.id != question_id,
                        ~Question.id.in_(attempted_question_ids)
                    ).limit(limit - len(similar_recommendations)).all()
                    
                    for question in topic_questions:
                        similar_recommendations.append({
                            'question_id': question.id,
                            'subject': question.subject,
                            'chapter': question.chapter,
                            'topic': question.topic,
                            'difficulty': question.difficulty,
                            'type': 'topic_similar',
                            'reason': f'Same topic: {question.topic}',
                            'priority': 2
                        })
            
            return similar_recommendations[:limit]
        
        except Exception as e:
            return []
    
    def _generate_subject_recommendations(self, lecture):
        """Generate recommendations based on lecture subject"""
        try:
            questions = Question.query.filter_by(
                subject=lecture.subject,
                is_active=True
            ).filter(
                Question.difficulty.between(2, 3)
            ).limit(10).all()
            
            recommendations_created = 0
            
            for question in questions:
                recommendation = PracticeRecommendation(
                    lecture_id=lecture.id,
                    subject=lecture.subject,
                    topic=question.topic,
                    question_id=question.id,
                    priority=2  # Medium priority
                )
                
                db.session.add(recommendation)
                recommendations_created += 1
            
            return recommendations_created
        
        except Exception:
            return 0
    
    def _get_student_weak_topics(self, student_id):
        """Get weak topics for a student"""
        try:
            # Look at attempts from last 30 days
            cutoff_date = datetime.utcnow() - timedelta(days=30)
            
            topic_stats = db.session.query(
                Question.subject,
                Question.topic,
                func.count(Attempt.id).label('total_attempts'),
                func.sum(Attempt.is_correct.cast(db.Integer)).label('correct_attempts')
            ).join(
                Attempt, Question.id == Attempt.question_id
            ).filter(
                Attempt.student_id == student_id,
                Attempt.created_at >= cutoff_date
            ).group_by(
                Question.subject, Question.topic
            ).having(
                func.count(Attempt.id) >= 3  # At least 3 attempts
            ).all()
            
            weak_topics = []
            for subject, topic, total, correct in topic_stats:
                accuracy = (correct or 0) / total if total > 0 else 0
                if accuracy < 0.6:  # Less than 60% accuracy
                    weak_topics.append({
                        'subject': subject,
                        'topic': topic,
                        'accuracy': accuracy,
                        'attempts': total
                    })
            
            # Sort by accuracy (lowest first)
            weak_topics.sort(key=lambda x: x['accuracy'])
            return weak_topics
        
        except Exception:
            return []
    
    def _get_lecture_recommendations(self, student_id, limit):
        """Get recommendations from recent lectures"""
        try:
            # Get uncompleted lecture recommendations
            lecture_recs = PracticeRecommendation.query.filter_by(
                student_id=None,  # General recommendations
                is_completed=False
            ).join(
                Question, PracticeRecommendation.question_id == Question.id
            ).filter(
                Question.is_active == True
            ).order_by(
                PracticeRecommendation.priority,
                desc(PracticeRecommendation.created_at)
            ).limit(limit).all()
            
            recommendations = []
            
            for rec in lecture_recs:
                # Check if student has already attempted this question
                attempt = Attempt.query.filter_by(
                    student_id=student_id,
                    question_id=rec.question_id
                ).first()
                
                if not attempt:  # Not yet attempted
                    question = rec.question
                    recommendations.append({
                        'question_id': question.id,
                        'subject': question.subject,
                        'chapter': question.chapter,
                        'topic': question.topic,
                        'difficulty': question.difficulty,
                        'type': 'lecture_followup',
                        'reason': 'Follow-up practice from recent lecture',
                        'priority': rec.priority,
                        'lecture_id': rec.lecture_id
                    })
            
            return recommendations
        
        except Exception:
            return []
    
    def _get_weak_topic_recommendations(self, student_id, weak_topics, limit):
        """Get recommendations for weak topics"""
        try:
            recommendations = []
            
            # Get questions from weak topics that haven't been attempted
            attempted_question_ids = set(
                attempt.question_id for attempt in 
                Attempt.query.filter_by(student_id=student_id).all()
            )
            
            for weak_topic in weak_topics[:3]:  # Focus on top 3 weak topics
                if len(recommendations) >= limit:
                    break
                
                questions = Question.query.filter_by(
                    subject=weak_topic['subject'],
                    topic=weak_topic['topic'],
                    is_active=True
                ).filter(
                    ~Question.id.in_(attempted_question_ids)
                ).order_by(Question.difficulty).limit(3).all()
                
                for question in questions:
                    if len(recommendations) >= limit:
                        break
                    
                    recommendations.append({
                        'question_id': question.id,
                        'subject': question.subject,
                        'chapter': question.chapter,
                        'topic': question.topic,
                        'difficulty': question.difficulty,
                        'type': 'weak_topic',
                        'reason': f'Weak topic (accuracy: {weak_topic["accuracy"]:.1%})',
                        'priority': 1  # High priority for weak topics
                    })
            
            return recommendations
        
        except Exception:
            return []
    
    def _get_general_recommendations(self, student_id, limit):
        """Get general recommendations when no specific weak areas"""
        try:
            # Get student's recent subjects
            recent_subjects = db.session.query(Question.subject).join(
                Attempt, Question.id == Attempt.question_id
            ).filter(
                Attempt.student_id == student_id
            ).distinct().limit(2).all()
            
            subjects = [subject[0] for subject in recent_subjects] if recent_subjects else ['Physics', 'Chemistry']
            
            # Get unattempted questions from these subjects
            attempted_question_ids = set(
                attempt.question_id for attempt in 
                Attempt.query.filter_by(student_id=student_id).all()
            )
            
            questions = Question.query.filter(
                Question.subject.in_(subjects),
                Question.is_active == True,
                ~Question.id.in_(attempted_question_ids)
            ).filter(
                Question.difficulty.between(2, 3)  # Medium difficulty
            ).order_by(func.random()).limit(limit).all()
            
            recommendations = []
            
            for question in questions:
                recommendations.append({
                    'question_id': question.id,
                    'subject': question.subject,
                    'chapter': question.chapter,
                    'topic': question.topic,
                    'difficulty': question.difficulty,
                    'type': 'general',
                    'reason': 'Explore new topics',
                    'priority': 3  # Low priority
                })
            
            return recommendations
        
        except Exception:
            return []

# Singleton instance
recommendation_service = RecommendationService()

def generate_lecture_recommendations(lecture_id):
    """Wrapper function for generating lecture recommendations"""
    return recommendation_service.generate_lecture_recommendations(lecture_id)

def get_personalized_recommendations(student_id, limit=10):
    """Wrapper function for getting personalized recommendations"""
    return recommendation_service.get_personalized_recommendations(student_id, limit)

def get_revision_recommendations(student_id, limit=10):
    """Wrapper function for getting revision recommendations"""
    return recommendation_service.get_revision_recommendations(student_id, limit)

def get_similar_questions_recommendation(question_id, student_id, limit=5):
    """Wrapper function for getting similar question recommendations"""
    return recommendation_service.get_similar_questions_recommendation(question_id, student_id, limit)
