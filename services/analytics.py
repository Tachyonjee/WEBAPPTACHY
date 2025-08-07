from datetime import datetime, timedelta
from sqlalchemy import func, desc, and_
from extensions import db
from models.student import Student
from models.user import User
from models.attempt import Attempt
from models.question import Question
from models.practice_session import PracticeSession
from models.doubt import Doubt
from models.performance import PerformanceSummary
from models.gamification import Streak, Points, Badges

class AnalyticsService:
    """Service for generating analytics and insights"""
    
    @staticmethod
    def get_daily_active_users(date=None):
        """Get count of daily active users"""
        if date is None:
            date = datetime.utcnow().date()
        
        # Count users who attempted questions on the given date
        return db.session.query(func.count(func.distinct(Attempt.student_id))).filter(
            func.date(Attempt.created_at) == date
        ).scalar() or 0
    
    @staticmethod
    def get_questions_solved_today():
        """Get total questions solved today"""
        today = datetime.utcnow().date()
        return Attempt.query.filter(
            func.date(Attempt.created_at) == today
        ).count()
    
    @staticmethod
    def get_questions_solved_this_week():
        """Get total questions solved this week"""
        week_start = datetime.utcnow().date() - timedelta(days=datetime.utcnow().weekday())
        return Attempt.query.filter(
            Attempt.created_at >= week_start
        ).count()
    
    @staticmethod
    def get_accuracy_trend(days=30):
        """Get accuracy trend over the last N days"""
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=days)
        
        daily_stats = db.session.query(
            func.date(Attempt.created_at).label('date'),
            func.count(Attempt.id).label('total_attempts'),
            func.sum(Attempt.is_correct.cast(db.Integer)).label('correct_attempts')
        ).filter(
            Attempt.created_at >= start_date
        ).group_by(func.date(Attempt.created_at)).order_by('date').all()
        
        trend_data = []
        for date, total, correct in daily_stats:
            accuracy = (correct or 0) / total if total > 0 else 0
            trend_data.append({
                'date': date.isoformat(),
                'accuracy': round(accuracy, 3),
                'total_attempts': total
            })
        
        return trend_data
    
    @staticmethod
    def get_average_time_trend(days=30):
        """Get average time per question trend"""
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=days)
        
        daily_stats = db.session.query(
            func.date(Attempt.created_at).label('date'),
            func.avg(Attempt.time_taken).label('avg_time')
        ).filter(
            Attempt.created_at >= start_date
        ).group_by(func.date(Attempt.created_at)).order_by('date').all()
        
        trend_data = []
        for date, avg_time in daily_stats:
            trend_data.append({
                'date': date.isoformat(),
                'avg_time': round(avg_time or 0, 1)
            })
        
        return trend_data
    
    @staticmethod
    def get_top_weak_chapters(limit=10):
        """Get chapters with lowest accuracy across all students"""
        chapter_stats = db.session.query(
            Question.subject,
            Question.chapter,
            func.count(Attempt.id).label('total_attempts'),
            func.sum(Attempt.is_correct.cast(db.Integer)).label('correct_attempts')
        ).join(
            Attempt, Question.id == Attempt.question_id
        ).group_by(
            Question.subject, Question.chapter
        ).having(
            func.count(Attempt.id) >= 10  # At least 10 attempts
        ).all()
        
        weak_chapters = []
        for subject, chapter, total, correct in chapter_stats:
            accuracy = (correct or 0) / total if total > 0 else 0
            weak_chapters.append({
                'subject': subject,
                'chapter': chapter,
                'accuracy': round(accuracy, 3),
                'total_attempts': total
            })
        
        # Sort by accuracy (ascending)
        weak_chapters.sort(key=lambda x: x['accuracy'])
        return weak_chapters[:limit]
    
    @staticmethod
    def get_student_analytics(student_id, days=30):
        """Get comprehensive analytics for a specific student"""
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=days)
        
        # Basic stats
        total_attempts = Attempt.query.filter(
            Attempt.student_id == student_id,
            Attempt.created_at >= start_date
        ).count()
        
        correct_attempts = Attempt.query.filter(
            Attempt.student_id == student_id,
            Attempt.created_at >= start_date,
            Attempt.is_correct == True
        ).count()
        
        overall_accuracy = correct_attempts / total_attempts if total_attempts > 0 else 0
        
        # Average time
        avg_time = db.session.query(func.avg(Attempt.time_taken)).filter(
            Attempt.student_id == student_id,
            Attempt.created_at >= start_date
        ).scalar() or 0
        
        # Subject-wise performance
        subject_stats = db.session.query(
            Question.subject,
            func.count(Attempt.id).label('total'),
            func.sum(Attempt.is_correct.cast(db.Integer)).label('correct'),
            func.avg(Attempt.time_taken).label('avg_time')
        ).join(
            Attempt, Question.id == Attempt.question_id
        ).filter(
            Attempt.student_id == student_id,
            Attempt.created_at >= start_date
        ).group_by(Question.subject).all()
        
        subject_performance = []
        for subject, total, correct, avg_time in subject_stats:
            accuracy = (correct or 0) / total if total > 0 else 0
            subject_performance.append({
                'subject': subject,
                'accuracy': round(accuracy, 3),
                'total_attempts': total,
                'avg_time': round(avg_time or 0, 1)
            })
        
        # Weak topics
        weak_topics = AnalyticsService.get_student_weak_topics(student_id, days)
        
        # Streak and points
        streak = Streak.query.filter_by(student_id=student_id).first()
        points = Points.query.filter_by(student_id=student_id).first()
        badges_count = Badges.query.filter_by(student_id=student_id).count()
        
        # Recent doubts
        recent_doubts = Doubt.query.filter(
            Doubt.student_id == student_id,
            Doubt.created_at >= start_date
        ).count()
        
        return {
            'overall_accuracy': round(overall_accuracy, 3),
            'total_attempts': total_attempts,
            'avg_time': round(avg_time, 1),
            'subject_performance': subject_performance,
            'weak_topics': weak_topics,
            'current_streak': streak.current_streak if streak else 0,
            'best_streak': streak.best_streak if streak else 0,
            'total_points': points.points_total if points else 0,
            'badges_earned': badges_count,
            'recent_doubts': recent_doubts
        }
    
    @staticmethod
    def get_student_weak_topics(student_id, days=30):
        """Get weak topics for a specific student"""
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=days)
        
        topic_stats = db.session.query(
            Question.subject,
            Question.topic,
            func.count(Attempt.id).label('total'),
            func.sum(Attempt.is_correct.cast(db.Integer)).label('correct')
        ).join(
            Attempt, Question.id == Attempt.question_id
        ).filter(
            Attempt.student_id == student_id,
            Attempt.created_at >= start_date
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
                    'accuracy': round(accuracy, 3),
                    'total_attempts': total
                })
        
        # Sort by accuracy (ascending)
        weak_topics.sort(key=lambda x: x['accuracy'])
        return weak_topics
    
    @staticmethod
    def get_batch_comparison(metric='accuracy'):
        """Get batch comparison data"""
        # This is a simplified version - would need actual batch assignment logic
        batch_stats = db.session.query(
            Student.batch,
            func.count(func.distinct(Attempt.student_id)).label('active_students'),
            func.count(Attempt.id).label('total_attempts'),
            func.sum(Attempt.is_correct.cast(db.Integer)).label('correct_attempts'),
            func.avg(Attempt.time_taken).label('avg_time')
        ).join(
            Attempt, Student.id == Attempt.student_id
        ).filter(
            Student.batch.isnot(None)
        ).group_by(Student.batch).all()
        
        comparison_data = []
        for batch, students, total, correct, avg_time in batch_stats:
            accuracy = (correct or 0) / total if total > 0 else 0
            engagement = total / students if students > 0 else 0
            
            comparison_data.append({
                'batch': batch,
                'active_students': students,
                'accuracy': round(accuracy, 3),
                'engagement': round(engagement, 1),
                'avg_time': round(avg_time or 0, 1)
            })
        
        # Sort by the requested metric
        if metric == 'accuracy':
            comparison_data.sort(key=lambda x: x['accuracy'], reverse=True)
        elif metric == 'engagement':
            comparison_data.sort(key=lambda x: x['engagement'], reverse=True)
        elif metric == 'avg_time':
            comparison_data.sort(key=lambda x: x['avg_time'])
        
        return comparison_data
    
    @staticmethod
    def get_content_health():
        """Analyze content health - identify problematic questions"""
        question_stats = db.session.query(
            Question.id,
            Question.subject,
            Question.chapter,
            Question.topic,
            Question.difficulty,
            func.count(Attempt.id).label('total_attempts'),
            func.sum(Attempt.is_correct.cast(db.Integer)).label('correct_attempts')
        ).join(
            Attempt, Question.id == Attempt.question_id
        ).group_by(Question.id).having(
            func.count(Attempt.id) >= 10  # At least 10 attempts
        ).all()
        
        problematic_questions = []
        for q_id, subject, chapter, topic, difficulty, total, correct in question_stats:
            accuracy = (correct or 0) / total if total > 0 else 0
            
            # Flag questions where difficulty doesn't match performance
            expected_accuracy = {1: 0.8, 2: 0.7, 3: 0.6, 4: 0.4, 5: 0.3}
            expected = expected_accuracy.get(difficulty, 0.6)
            
            if accuracy < expected - 0.2:  # Significantly lower than expected
                problematic_questions.append({
                    'question_id': q_id,
                    'subject': subject,
                    'chapter': chapter,
                    'topic': topic,
                    'difficulty': difficulty,
                    'accuracy': round(accuracy, 3),
                    'expected_accuracy': expected,
                    'total_attempts': total,
                    'issue': 'too_difficult'
                })
            elif accuracy > expected + 0.2:  # Significantly higher than expected
                problematic_questions.append({
                    'question_id': q_id,
                    'subject': subject,
                    'chapter': chapter,
                    'topic': topic,
                    'difficulty': difficulty,
                    'accuracy': round(accuracy, 3),
                    'expected_accuracy': expected,
                    'total_attempts': total,
                    'issue': 'too_easy'
                })
        
        return problematic_questions
