from flask import Blueprint, request, jsonify, g
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta
from sqlalchemy import desc, func
from extensions import db
from models.user import User
from models.student import Student
from models.question import Question
from models.attempt import Attempt
from models.doubt import Doubt
from models.bookmark import Bookmark
from models.practice_session import PracticeSession
from models.performance import PerformanceSummary
from models.gamification import Streak, Points, Badges
from services.adaptive import get_adaptive_question
from services.analytics import AnalyticsService
from services.recommendations import get_personalized_recommendations, get_revision_recommendations
from services.security import student_required, get_current_user
from services.llm import get_solution, is_llm_enabled
import logging

logger = logging.getLogger(__name__)

students_bp = Blueprint('students', __name__)

# Practice Session Management

@students_bp.route('/sessions', methods=['POST'])
@student_required
def start_practice_session():
    """Start a new practice session"""
    try:
        current_user = get_current_user()
        student = current_user.student_profile
        
        data = request.get_json()
        mode = data.get('mode', 'adaptive')
        subjects = data.get('subjects', [])
        chapters = data.get('chapters', [])
        topics = data.get('topics', [])
        device_type = data.get('device_type', 'personal')
        
        # Validate mode
        valid_modes = ['adaptive', 'topic', 'chapter', 'multi_chapter', 'multi_subject', 'revision']
        if mode not in valid_modes:
            return jsonify({
                'success': False,
                'message': f'Invalid mode. Valid modes: {", ".join(valid_modes)}'
            }), 400
        
        # End any active session
        active_session = PracticeSession.query.filter_by(
            student_id=student.id,
            is_active=True
        ).first()
        
        if active_session:
            active_session.end_session()
            db.session.commit()
        
        # Create new session
        session = PracticeSession()
        session.student_id = student.id
        session.mode = mode
        session.device_type = device_type
        
        session.set_subjects(subjects)
        session.set_chapters(chapters)
        session.set_topics(topics)
        
        db.session.add(session)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'session_id': session.id,
            'mode': mode,
            'message': 'Practice session started successfully'
        })
    
    except Exception as e:
        logger.error(f"Error starting practice session: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': 'Failed to start practice session'
        }), 500

@students_bp.route('/sessions/<int:session_id>/end', methods=['PATCH'])
@student_required
def end_practice_session(session_id):
    """End a practice session"""
    try:
        current_user = get_current_user()
        student = current_user.student_profile
        
        session = PracticeSession.query.filter_by(
            id=session_id,
            student_id=student.id
        ).first()
        
        if not session:
            return jsonify({
                'success': False,
                'message': 'Session not found'
            }), 404
        
        if not session.is_active:
            return jsonify({
                'success': False,
                'message': 'Session is already ended'
            }), 400
        
        # End the session
        session.end_session()
        db.session.commit()
        
        # Calculate session summary
        summary = {
            'total_questions': session.total_questions,
            'correct_answers': session.correct_answers,
            'accuracy': session.get_accuracy(),
            'duration_minutes': int((session.ended_at - session.started_at).total_seconds() / 60)
        }
        
        return jsonify({
            'success': True,
            'message': 'Session ended successfully',
            'summary': summary
        })
    
    except Exception as e:
        logger.error(f"Error ending practice session: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': 'Failed to end practice session'
        }), 500

# Question Delivery

@students_bp.route('/next-question', methods=['GET'])
@student_required
def get_next_question():
    """Get next question for practice"""
    try:
        current_user = get_current_user()
        student = current_user.student_profile
        
        session_id = request.args.get('session_id', type=int)
        
        if not session_id:
            return jsonify({
                'success': False,
                'message': 'Session ID is required'
            }), 400
        
        # Get session
        session = PracticeSession.query.filter_by(
            id=session_id,
            student_id=student.id,
            is_active=True
        ).first()
        
        if not session:
            return jsonify({
                'success': False,
                'message': 'Active session not found'
            }), 404
        
        # Get adaptive question
        question = get_adaptive_question(
            student.id,
            session_id,
            session.mode,
            session.get_subjects(),
            session.get_chapters(),
            session.get_topics()
        )
        
        if not question:
            return jsonify({
                'success': False,
                'message': 'No more questions available for this session'
            }), 404
        
        # Check how many attempts student has made on this question in this session
        attempts_count = Attempt.query.filter_by(
            student_id=student.id,
            question_id=question.id,
            session_id=session_id
        ).count()
        
        return jsonify({
            'success': True,
            'question': {
                'id': question.id,
                'subject': question.subject,
                'chapter': question.chapter,
                'topic': question.topic,
                'difficulty': question.difficulty,
                'question_text': question.question_text,
                'options': question.get_options() if question.options else None,
                'hint_available': bool(question.hint),
                'attempts_made': attempts_count,
                'max_attempts': 2
            }
        })
    
    except Exception as e:
        logger.error(f"Error getting next question: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to get next question'
        }), 500

@students_bp.route('/attempts', methods=['POST'])
@student_required
def submit_attempt():
    """Submit answer attempt"""
    try:
        current_user = get_current_user()
        student = current_user.student_profile
        
        data = request.get_json()
        question_id = data.get('question_id')
        chosen_answer = data.get('chosen_answer', '').strip()
        time_taken = data.get('time_taken', 0)
        session_id = data.get('session_id')
        
        if not all([question_id, chosen_answer, session_id]):
            return jsonify({
                'success': False,
                'message': 'Question ID, answer, and session ID are required'
            }), 400
        
        # Get question
        question = Question.query.get(question_id)
        if not question:
            return jsonify({
                'success': False,
                'message': 'Question not found'
            }), 404
        
        # Check session
        session = PracticeSession.query.filter_by(
            id=session_id,
            student_id=student.id,
            is_active=True
        ).first()
        
        if not session:
            return jsonify({
                'success': False,
                'message': 'Active session not found'
            }), 404
        
        # Check if maximum attempts reached
        existing_attempts = Attempt.query.filter_by(
            student_id=student.id,
            question_id=question_id,
            session_id=session_id
        ).count()
        
        if existing_attempts >= 2:
            return jsonify({
                'success': False,
                'message': 'Maximum attempts (2) reached for this question'
            }), 400
        
        # Check if answer is correct
        is_correct = chosen_answer.strip().upper() == question.correct_answer.strip().upper()
        
        # Create attempt
        attempt = Attempt()
        attempt.student_id = student.id
        attempt.question_id = question_id
        attempt.session_id = session_id
        attempt.chosen_answer = chosen_answer
        attempt.is_correct = is_correct
        attempt.time_taken = time_taken
        attempt.attempt_no = existing_attempts + 1
        attempt.seconds_elapsed = time_taken
        
        db.session.add(attempt)
        
        # Update gamification
        _update_gamification(student.id, is_correct, existing_attempts == 0, time_taken)
        
        # Update performance summary
        _update_performance_summary(student.id, question.subject, is_correct, time_taken)
        
        db.session.commit()
        
        # Prepare response
        response_data = {
            'success': True,
            'correct': is_correct,
            'attempt_no': attempt.attempt_no,
            'attempts_remaining': 2 - attempt.attempt_no
        }
        
        # Add solution/hint based on attempt result
        if not is_correct:
            if attempt.attempt_no == 1 and question.hint:
                # First attempt wrong, show hint
                response_data['hint'] = question.hint
                response_data['message'] = 'Incorrect answer. Here\'s a hint to help you.'
            elif attempt.attempt_no == 2:
                # Second attempt wrong, show solution
                if is_llm_enabled():
                    solution = get_solution(question, student.id)
                    response_data['solution'] = solution
                else:
                    response_data['solution'] = {
                        'success': True,
                        'solution': question.correct_answer,
                        'explanation': question.hint or 'Solution explanation not available'
                    }
                response_data['message'] = 'Incorrect answer. Here\'s the detailed solution.'
        else:
            response_data['message'] = 'Correct answer! Well done.'
            if attempt.attempt_no == 2:
                response_data['message'] = 'Correct answer on second attempt! Good job.'
        
        return jsonify(response_data)
    
    except Exception as e:
        logger.error(f"Error submitting attempt: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': 'Failed to submit attempt'
        }), 500

# Bookmarks

@students_bp.route('/bookmarks', methods=['GET'])
@student_required
def get_bookmarks():
    """Get student's bookmarks"""
    try:
        current_user = get_current_user()
        student = current_user.student_profile
        
        subject = request.args.get('subject')
        chapter = request.args.get('chapter')
        topic = request.args.get('topic')
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        # Build query
        query = db.session.query(Bookmark, Question).join(
            Question, Bookmark.question_id == Question.id
        ).filter(
            Bookmark.student_id == student.id,
            Question.is_active.is_(True)
        )
        
        if subject:
            query = query.filter(Question.subject == subject)
        if chapter:
            query = query.filter(Question.chapter == chapter)
        if topic:
            query = query.filter(Question.topic == topic)
        
        # Paginate - note: SQLAlchemy 2.x paginate might not work on joined queries
        from sqlalchemy import desc as desc_func
        total_count = query.count()
        bookmarks_raw = query.order_by(desc_func(Bookmark.created_at)).offset((page-1)*per_page).limit(per_page).all()
        
        # Create a mock pagination object
        class PaginationResult:
            def __init__(self, items, page, per_page, total):
                self.items = items
                self.page = page
                self.per_page = per_page
                self.total = total
                self.pages = (total + per_page - 1) // per_page
                self.has_next = page < self.pages
                self.has_prev = page > 1
        
        bookmarks = PaginationResult(bookmarks_raw, page, per_page, total_count)
        
        # Format response
        bookmark_list = []
        for bookmark, question in bookmarks.items:
            bookmark_list.append({
                'id': bookmark.id,
                'question': {
                    'id': question.id,
                    'subject': question.subject,
                    'chapter': question.chapter,
                    'topic': question.topic,
                    'difficulty': question.difficulty,
                    'question_text': question.question_text[:200] + '...' if len(question.question_text) > 200 else question.question_text
                },
                'created_at': bookmark.created_at.isoformat()
            })
        
        return jsonify({
            'success': True,
            'bookmarks': bookmark_list,
            'pagination': {
                'current_page': bookmarks.page,
                'total_pages': bookmarks.pages,
                'total_items': bookmarks.total,
                'has_next': bookmarks.has_next,
                'has_prev': bookmarks.has_prev
            }
        })
    
    except Exception as e:
        logger.error(f"Error getting bookmarks: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to get bookmarks'
        }), 500

@students_bp.route('/bookmarks', methods=['POST'])
@student_required
def add_bookmark():
    """Add question to bookmarks"""
    try:
        current_user = get_current_user()
        student = current_user.student_profile
        
        data = request.get_json()
        question_id = data.get('question_id')
        
        if not question_id:
            return jsonify({
                'success': False,
                'message': 'Question ID is required'
            }), 400
        
        # Check if question exists
        question = Question.query.get(question_id)
        if not question:
            return jsonify({
                'success': False,
                'message': 'Question not found'
            }), 404
        
        # Check if already bookmarked
        existing = Bookmark.query.filter_by(
            student_id=student.id,
            question_id=question_id
        ).first()
        
        if existing:
            return jsonify({
                'success': False,
                'message': 'Question already bookmarked'
            }), 400
        
        # Create bookmark
        bookmark = Bookmark()
        bookmark.student_id = student.id
        bookmark.question_id = question_id
        
        db.session.add(bookmark)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Question bookmarked successfully'
        })
    
    except Exception as e:
        logger.error(f"Error adding bookmark: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': 'Failed to add bookmark'
        }), 500

@students_bp.route('/bookmarks/<int:bookmark_id>', methods=['DELETE'])
@student_required
def remove_bookmark(bookmark_id):
    """Remove bookmark"""
    try:
        current_user = get_current_user()
        student = current_user.student_profile
        
        bookmark = Bookmark.query.filter_by(
            id=bookmark_id,
            student_id=student.id
        ).first()
        
        if not bookmark:
            return jsonify({
                'success': False,
                'message': 'Bookmark not found'
            }), 404
        
        db.session.delete(bookmark)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Bookmark removed successfully'
        })
    
    except Exception as e:
        logger.error(f"Error removing bookmark: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': 'Failed to remove bookmark'
        }), 500

# Doubts

@students_bp.route('/<int:student_id>/doubts', methods=['GET'])
@student_required
def get_doubts(student_id):
    """Get student's doubts"""
    try:
        current_user = get_current_user()
        
        # Students can only see their own doubts
        if current_user.role == 'student' and current_user.student_profile.id != student_id:
            return jsonify({
                'success': False,
                'message': 'Access denied'
            }), 403
        
        status = request.args.get('status')
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        # Build query
        query = Doubt.query.filter_by(student_id=student_id)
        
        if status:
            query = query.filter(Doubt.status == status)
        
        # Paginate
        doubts = query.order_by(desc(Doubt.created_at)).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        # Format response
        doubt_list = []
        for doubt in doubts.items:
            doubt_data = {
                'id': doubt.id,
                'message': doubt.message,
                'status': doubt.status,
                'created_at': doubt.created_at.isoformat(),
                'question_id': doubt.question_id
            }
            
            if doubt.status == 'resolved':
                doubt_data['response'] = doubt.response
                doubt_data['resolved_at'] = doubt.resolved_at.isoformat() if doubt.resolved_at else None
                if doubt.resolver:
                    doubt_data['resolved_by'] = doubt.resolver.name
            
            doubt_list.append(doubt_data)
        
        return jsonify({
            'success': True,
            'doubts': doubt_list,
            'pagination': {
                'current_page': doubts.page,
                'total_pages': doubts.pages,
                'total_items': doubts.total,
                'has_next': doubts.has_next,
                'has_prev': doubts.has_prev
            }
        })
    
    except Exception as e:
        logger.error(f"Error getting doubts: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to get doubts'
        }), 500

@students_bp.route('/<int:student_id>/doubts', methods=['POST'])
@student_required
def create_doubt(student_id):
    """Create a new doubt"""
    try:
        current_user = get_current_user()
        
        # Students can only create doubts for themselves
        if current_user.role == 'student' and current_user.student_profile.id != student_id:
            return jsonify({
                'success': False,
                'message': 'Access denied'
            }), 403
        
        data = request.get_json()
        message = data.get('message', '').strip()
        question_id = data.get('question_id')
        
        if not message:
            return jsonify({
                'success': False,
                'message': 'Doubt message is required'
            }), 400
        
        # Create doubt
        doubt = Doubt()
        doubt.student_id = student_id
        doubt.question_id = question_id
        doubt.message = message
        
        db.session.add(doubt)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Doubt submitted successfully',
            'doubt_id': doubt.id
        })
    
    except Exception as e:
        logger.error(f"Error creating doubt: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': 'Failed to submit doubt'
        }), 500

# Analytics and Progress

@students_bp.route('/<int:student_id>/progress', methods=['GET'])
@student_required
def get_student_progress(student_id):
    """Get student progress analytics"""
    try:
        current_user = get_current_user()
        
        # Students can only see their own progress
        if current_user.role == 'student' and current_user.student_profile.id != student_id:
            return jsonify({
                'success': False,
                'message': 'Access denied'
            }), 403
        
        days = request.args.get('days', 30, type=int)
        
        # Get comprehensive analytics
        analytics = AnalyticsService.get_student_analytics(student_id, days)
        
        return jsonify({
            'success': True,
            'analytics': analytics
        })
    
    except Exception as e:
        logger.error(f"Error getting student progress: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to get progress data'
        }), 500

@students_bp.route('/weak-topics', methods=['GET'])
@student_required
def get_weak_topics():
    """Get student's weak topics"""
    try:
        current_user = get_current_user()
        student = current_user.student_profile
        
        window = request.args.get('window', '30d')
        days = int(window.replace('d', '')) if window.endswith('d') else 30
        
        weak_topics = AnalyticsService.get_student_weak_topics(student.id, days)
        
        return jsonify({
            'success': True,
            'weak_topics': weak_topics
        })
    
    except Exception as e:
        logger.error(f"Error getting weak topics: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to get weak topics'
        }), 500

# Recommendations

@students_bp.route('/recommendations', methods=['GET'])
@student_required
def get_recommendations():
    """Get personalized practice recommendations"""
    try:
        current_user = get_current_user()
        student = current_user.student_profile
        
        rec_type = request.args.get('type', 'personalized')
        limit = request.args.get('limit', 10, type=int)
        
        if rec_type == 'personalized':
            recommendations = get_personalized_recommendations(student.id, limit)
        elif rec_type == 'revision':
            recommendations = get_revision_recommendations(student.id, limit)
        else:
            return jsonify({
                'success': False,
                'message': 'Invalid recommendation type'
            }), 400
        
        return jsonify({
            'success': True,
            'recommendations': recommendations,
            'type': rec_type
        })
    
    except Exception as e:
        logger.error(f"Error getting recommendations: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to get recommendations'
        }), 500

# Helper methods

def _update_gamification(student_id, is_correct, is_first_attempt, time_taken):
    """Update gamification metrics"""
    try:
        # Update streak
        streak = Streak.query.filter_by(student_id=student_id).first()
        if not streak:
            streak = Streak()
            streak.student_id = student_id
            db.session.add(streak)
        
        streak.update_streak()
        
        # Update points
        points = Points.query.filter_by(student_id=student_id).first()
        if not points:
            points = Points()
            points.student_id = student_id
            db.session.add(points)
        
        # Award points
        if is_first_attempt:
            points.add_points(2)  # Points for attempt
        
        if is_correct:
            if is_first_attempt:
                points.add_points(5)  # Bonus for correct answer
            else:
                points.add_points(3)  # Points for correct on second attempt
        
        # Check for badges
        _check_and_award_badges(student_id, is_correct, time_taken)
        
    except Exception as e:
        logger.error(f"Error updating gamification: {str(e)}")

def _update_performance_summary(student_id, subject, is_correct, time_taken):
    """Update performance summary"""
    try:
        summary = PerformanceSummary.query.filter_by(
            student_id=student_id,
            subject=subject
        ).first()
        
        if not summary:
            summary = PerformanceSummary()
            summary.student_id = student_id
            summary.subject = subject
            db.session.add(summary)
        
        summary.update_performance(is_correct, time_taken)
        
    except Exception as e:
        logger.error(f"Error updating performance summary: {str(e)}")

def _check_and_award_badges(student_id, is_correct, time_taken):
    """Check and award badges"""
    try:
        # Check streak badges
        streak = Streak.query.filter_by(student_id=student_id).first()
        if streak:
            if streak.current_streak == 7:
                Badges.award_badge(student_id, '7D_STREAK', '7-Day Streak', 'Practiced for 7 consecutive days')
            elif streak.current_streak == 30:
                Badges.award_badge(student_id, '30D_STREAK', '30-Day Streak', 'Practiced for 30 consecutive days')
        
        # Check total questions solved
        total_attempts = Attempt.query.filter_by(student_id=student_id).count()
        if total_attempts == 100:
            Badges.award_badge(student_id, '100_Q_SOLVED', 'Century', 'Solved 100 questions')
        
        # Check fast solver (average < 40s over last 20 correct answers)
        if is_correct and time_taken < 40:
            recent_correct = Attempt.query.filter_by(
                student_id=student_id,
                is_correct=True
            ).order_by(desc(Attempt.created_at)).limit(20).all()
            
            if len(recent_correct) == 20:
                avg_time = sum(a.time_taken for a in recent_correct) / 20
                if avg_time < 40:
                    Badges.award_badge(student_id, 'FAST_SOLVER', 'Speed Demon', 'Average solving time under 40 seconds')
        
    except Exception as e:
        logger.error(f"Error checking badges: {str(e)}")
