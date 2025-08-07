from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from datetime import datetime, timedelta
from extensions import db
from models import User, Student, MentorAssignment, Batch, Attempt, Question, Doubt, PracticeSession
from services.security import security_service

mentor_bp = Blueprint('mentor', __name__)

def require_mentor_auth():
    """Check if user is authenticated as mentor"""
    user_id = session.get('user_id')
    user_role = session.get('user_role')
    
    if not user_id or user_role != 'mentor':
        return redirect(url_for('auth.login'))
    
    return User.query.get(user_id)

@mentor_bp.route('/insights')
def insights():
    """Mentor insights dashboard"""
    user = require_mentor_auth()
    if isinstance(user, type(redirect(url_for('auth.login')))):
        return user
    
    # Get mentor's assigned batches and students
    assignments = MentorAssignment.query.filter_by(
        mentor_user_id=user.id,
        is_active=True
    ).all()
    
    assigned_batches = []
    assigned_students = []
    
    for assignment in assignments:
        if assignment.batch_id:
            batch = Batch.query.get(assignment.batch_id)
            if batch:
                assigned_batches.append(batch)
        elif assignment.student_id:
            student = Student.query.get(assignment.student_id)
            if student:
                assigned_students.append(student)
    
    return render_template('mentor/insights.html',
                         mentor=user,
                         assigned_batches=assigned_batches,
                         assigned_students=assigned_students)

@mentor_bp.route('/students')
def students():
    """Mentor students view"""
    user = require_mentor_auth()
    if isinstance(user, type(redirect(url_for('auth.login')))):
        return user
    
    # Get all students assigned to this mentor
    all_students = _get_mentor_students(user.id)
    
    return render_template('mentor/students.html',
                         mentor=user,
                         students=all_students)

# API Routes

@mentor_bp.route('/api/insights')
@security_service.require_role(['mentor'])
def get_insights():
    """Get mentor insights data"""
    try:
        current_user = security_service.get_current_user()
        batch_id = request.args.get('batch_id', type=int)
        
        # Get students under this mentor
        students = _get_mentor_students(current_user.id, batch_id)
        student_ids = [s.id for s in students]
        
        if not student_ids:
            return jsonify({
                'success': True,
                'insights': _get_empty_insights()
            })
        
        # Date ranges
        today = datetime.utcnow().date()
        week_ago = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)
        
        # Overall metrics
        total_students = len(students)
        
        # Active students (attempted questions in last week)
        active_students = db.session.query(
            db.func.count(db.func.distinct(Attempt.student_id))
        ).filter(
            Attempt.student_id.in_(student_ids),
            db.func.date(Attempt.timestamp) >= week_ago
        ).scalar() or 0
        
        # Total attempts this week
        week_attempts = Attempt.query.filter(
            Attempt.student_id.in_(student_ids),
            db.func.date(Attempt.timestamp) >= week_ago
        ).count()
        
        # Average accuracy this week
        week_accuracy = db.session.query(
            db.func.avg(db.cast(Attempt.is_correct, db.Float))
        ).filter(
            Attempt.student_id.in_(student_ids),
            db.func.date(Attempt.timestamp) >= week_ago
        ).scalar() or 0
        
        # Subject-wise performance
        subject_performance = db.session.query(
            Question.subject,
            db.func.count(Attempt.id).label('attempts'),
            db.func.avg(db.cast(Attempt.is_correct, db.Float)).label('accuracy'),
            db.func.avg(Attempt.time_taken).label('avg_time')
        ).join(
            Attempt, Question.id == Attempt.question_id
        ).filter(
            Attempt.student_id.in_(student_ids),
            db.func.date(Attempt.timestamp) >= week_ago
        ).group_by(
            Question.subject
        ).all()
        
        # Daily activity trend (last 7 days)
        daily_activity = []
        for i in range(7):
            date = today - timedelta(days=i)
            attempts = Attempt.query.filter(
                Attempt.student_id.in_(student_ids),
                db.func.date(Attempt.timestamp) == date
            ).count()
            
            active_count = db.session.query(
                db.func.count(db.func.distinct(Attempt.student_id))
            ).filter(
                Attempt.student_id.in_(student_ids),
                db.func.date(Attempt.timestamp) == date
            ).scalar() or 0
            
            daily_activity.append({
                'date': date.isoformat(),
                'attempts': attempts,
                'active_students': active_count
            })
        
        # Top performing students
        top_students = db.session.query(
            Student.id,
            User.name,
            db.func.count(Attempt.id).label('attempts'),
            db.func.avg(db.cast(Attempt.is_correct, db.Float)).label('accuracy')
        ).join(
            User, Student.user_id == User.id
        ).join(
            Attempt, Student.id == Attempt.student_id
        ).filter(
            Student.id.in_(student_ids),
            db.func.date(Attempt.timestamp) >= week_ago
        ).group_by(
            Student.id, User.name
        ).having(
            db.func.count(Attempt.id) >= 5  # Minimum attempts
        ).order_by(
            db.func.avg(db.cast(Attempt.is_correct, db.Float)).desc()
        ).limit(5).all()
        
        # Students needing attention (low accuracy or no activity)
        students_needing_attention = db.session.query(
            Student.id,
            User.name,
            db.func.count(Attempt.id).label('attempts'),
            db.func.avg(db.cast(Attempt.is_correct, db.Float)).label('accuracy')
        ).join(
            User, Student.user_id == User.id
        ).outerjoin(
            Attempt, db.and_(
                Student.id == Attempt.student_id,
                db.func.date(Attempt.timestamp) >= week_ago
            )
        ).filter(
            Student.id.in_(student_ids)
        ).group_by(
            Student.id, User.name
        ).having(
            db.or_(
                db.func.count(Attempt.id) == 0,  # No attempts
                db.func.avg(db.cast(Attempt.is_correct, db.Float)) < 0.5  # Low accuracy
            )
        ).limit(5).all()
        
        # Open doubts from students
        open_doubts = Doubt.query.filter(
            Doubt.student_id.in_(student_ids),
            Doubt.status == 'open'
        ).count()
        
        return jsonify({
            'success': True,
            'insights': {
                'overview': {
                    'total_students': total_students,
                    'active_students': active_students,
                    'week_attempts': week_attempts,
                    'week_accuracy': round(week_accuracy * 100, 1),
                    'open_doubts': open_doubts
                },
                'subject_performance': [
                    {
                        'subject': subject,
                        'attempts': attempts,
                        'accuracy': round(accuracy * 100, 1),
                        'avg_time': round(avg_time, 1)
                    }
                    for subject, attempts, accuracy, avg_time in subject_performance
                ],
                'daily_activity': daily_activity,
                'top_students': [
                    {
                        'student_id': student_id,
                        'name': name,
                        'attempts': attempts,
                        'accuracy': round(accuracy * 100, 1)
                    }
                    for student_id, name, attempts, accuracy in top_students
                ],
                'students_needing_attention': [
                    {
                        'student_id': student_id,
                        'name': name,
                        'attempts': attempts,
                        'accuracy': round(accuracy * 100, 1) if accuracy else 0
                    }
                    for student_id, name, attempts, accuracy in students_needing_attention
                ]
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@mentor_bp.route('/api/students')
@security_service.require_role(['mentor'])
def get_mentor_students():
    """Get students assigned to mentor"""
    try:
        current_user = security_service.get_current_user()
        batch_id = request.args.get('batch_id', type=int)
        
        students = _get_mentor_students(current_user.id, batch_id)
        
        # Get additional data for each student
        students_data = []
        for student in students:
            # Recent activity
            recent_attempts = Attempt.query.filter_by(
                student_id=student.id
            ).order_by(Attempt.timestamp.desc()).limit(5).all()
            
            # Last week stats
            week_ago = datetime.utcnow().date() - timedelta(days=7)
            week_attempts = Attempt.query.filter(
                Attempt.student_id == student.id,
                db.func.date(Attempt.timestamp) >= week_ago
            ).count()
            
            week_correct = Attempt.query.filter(
                Attempt.student_id == student.id,
                db.func.date(Attempt.timestamp) >= week_ago,
                Attempt.is_correct == True
            ).count()
            
            week_accuracy = (week_correct / week_attempts * 100) if week_attempts > 0 else 0
            
            # Open doubts
            open_doubts = Doubt.query.filter_by(
                student_id=student.id,
                status='open'
            ).count()
            
            # Last login
            last_login = student.user.last_login
            
            students_data.append({
                'id': student.id,
                'name': student.user.name,
                'email': student.user.email,
                'batch': student.batch,
                'goal_exam': student.goal_exam,
                'last_login': last_login.isoformat() if last_login else None,
                'week_stats': {
                    'attempts': week_attempts,
                    'accuracy': round(week_accuracy, 1)
                },
                'open_doubts': open_doubts,
                'recent_activity': len(recent_attempts) > 0
            })
        
        return jsonify({
            'success': True,
            'students': students_data
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@mentor_bp.route('/api/student/<int:student_id>/details')
@security_service.require_role(['mentor'])
def get_student_details(student_id):
    """Get detailed information about a specific student"""
    try:
        current_user = security_service.get_current_user()
        
        # Verify mentor has access to this student
        student = Student.query.get_or_404(student_id)
        if not _mentor_has_access_to_student(current_user.id, student_id):
            return jsonify({'error': 'Access denied'}), 403
        
        # Get comprehensive student data
        from services.analytics import analytics_service
        analytics = analytics_service.get_student_analytics(student_id)
        
        return jsonify({
            'success': True,
            'student_details': analytics
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@mentor_bp.route('/api/doubts')
@security_service.require_role(['mentor'])
def get_student_doubts():
    """Get doubts from assigned students"""
    try:
        current_user = security_service.get_current_user()
        status_filter = request.args.get('status', 'open')
        
        # Get students under this mentor
        students = _get_mentor_students(current_user.id)
        student_ids = [s.id for s in students]
        
        if not student_ids:
            return jsonify({
                'success': True,
                'doubts': []
            })
        
        # Build query
        query = db.session.query(Doubt, Student, User).join(
            Student, Doubt.student_id == Student.id
        ).join(
            User, Student.user_id == User.id
        ).filter(
            Doubt.student_id.in_(student_ids)
        )
        
        if status_filter != 'all':
            query = query.filter(Doubt.status == status_filter)
        
        doubts = query.order_by(Doubt.created_at.desc()).limit(50).all()
        
        doubts_data = []
        for doubt, student, user in doubts:
            doubt_dict = doubt.to_dict()
            doubt_dict['student_name'] = user.name
            doubt_dict['student_batch'] = student.batch
            
            # Add question info if applicable
            if doubt.question_id:
                question = Question.query.get(doubt.question_id)
                if question:
                    doubt_dict['question_info'] = {
                        'subject': question.subject,
                        'topic': question.topic,
                        'difficulty': question.difficulty
                    }
            
            doubts_data.append(doubt_dict)
        
        return jsonify({
            'success': True,
            'doubts': doubts_data
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@mentor_bp.route('/api/doubts/<int:doubt_id>/resolve', methods=['POST'])
@security_service.require_role(['mentor'])
def resolve_doubt(doubt_id):
    """Resolve a student doubt"""
    try:
        current_user = security_service.get_current_user()
        data = request.get_json()
        
        response_text = data.get('response', '').strip()
        if not response_text:
            return jsonify({'error': 'Response is required'}), 400
        
        # Get doubt and verify access
        doubt = Doubt.query.get_or_404(doubt_id)
        
        if not _mentor_has_access_to_student(current_user.id, doubt.student_id):
            return jsonify({'error': 'Access denied'}), 403
        
        # Resolve doubt
        doubt.mark_resolved(current_user.id, response_text)
        
        return jsonify({
            'success': True,
            'message': 'Doubt resolved successfully'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Helper functions

def _get_mentor_students(mentor_user_id, batch_id=None):
    """Get all students assigned to a mentor"""
    query = db.session.query(Student).join(
        MentorAssignment,
        db.or_(
            db.and_(
                MentorAssignment.student_id == Student.id,
                MentorAssignment.mentor_user_id == mentor_user_id
            ),
            db.and_(
                MentorAssignment.batch_id == Student.batch,
                MentorAssignment.mentor_user_id == mentor_user_id
            )
        )
    ).filter(
        MentorAssignment.is_active == True
    )
    
    if batch_id:
        query = query.filter(Student.batch == batch_id)
    
    return query.distinct().all()

def _mentor_has_access_to_student(mentor_user_id, student_id):
    """Check if mentor has access to a specific student"""
    students = _get_mentor_students(mentor_user_id)
    return any(s.id == student_id for s in students)

def _get_empty_insights():
    """Return empty insights structure"""
    return {
        'overview': {
            'total_students': 0,
            'active_students': 0,
            'week_attempts': 0,
            'week_accuracy': 0,
            'open_doubts': 0
        },
        'subject_performance': [],
        'daily_activity': [],
        'top_students': [],
        'students_needing_attention': []
    }
