from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
from extensions import db
from models import User, Student, Question, Attempt, Batch, Lecture, Doubt
from services.security import security_service
from services.analytics import analytics_service

admin_api_bp = Blueprint('admin_api', __name__)

@admin_api_bp.route('/metrics/overview')
@security_service.require_role(['admin'])
def get_overview_metrics():
    """Get overview metrics for admin dashboard"""
    try:
        metrics = analytics_service.get_overview_metrics()
        return jsonify({
            'success': True,
            'metrics': metrics
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_api_bp.route('/batch-compare')
@security_service.require_role(['admin'])
def get_batch_comparison():
    """Get batch comparison data"""
    try:
        metric = request.args.get('metric', 'accuracy')
        valid_metrics = ['accuracy', 'engagement', 'avg_time']
        
        if metric not in valid_metrics:
            return jsonify({'error': f'Invalid metric. Must be one of: {", ".join(valid_metrics)}'}), 400
        
        comparison_data = analytics_service.get_batch_comparison(metric)
        
        return jsonify({
            'success': True,
            'comparison': comparison_data,
            'metric': metric
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_api_bp.route('/students/<int:student_id>/analytics')
@security_service.require_role(['admin'])
def get_student_analytics(student_id):
    """Get comprehensive analytics for a student"""
    try:
        analytics = analytics_service.get_student_analytics(student_id)
        
        if not analytics:
            return jsonify({'error': 'Student not found'}), 404
        
        return jsonify({
            'success': True,
            'analytics': analytics
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_api_bp.route('/content-health')
@security_service.require_role(['admin'])
def get_content_health():
    """Get content health metrics"""
    try:
        health_data = analytics_service.get_content_health()
        
        return jsonify({
            'success': True,
            'content_health': health_data
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_api_bp.route('/users', methods=['POST'])
@security_service.require_role(['admin'])
def create_user():
    """Create a new user (operator/mentor/student)"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['name', 'email', 'role']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        # Validate role
        valid_roles = ['student', 'operator', 'mentor']
        if data['role'] not in valid_roles:
            return jsonify({'error': f'Role must be one of: {", ".join(valid_roles)}'}), 400
        
        # Check if email already exists
        existing_user = User.query.filter_by(email=data['email']).first()
        if existing_user:
            return jsonify({'error': 'Email already exists'}), 400
        
        # Create user
        user = User(
            name=data['name'],
            email=data['email'],
            phone=data.get('phone'),
            role=data['role']
        )
        
        # Set password if provided (for operator/mentor)
        if data.get('password') and data['role'] in ['operator', 'mentor']:
            user.set_password(data['password'])
        
        user.save()
        
        # Create student profile if role is student
        if data['role'] == 'student':
            student = Student(
                user_id=user.id,
                batch=data.get('batch'),
                goal_exam=data.get('goal_exam', 'JEE')
            )
            student.save()
        
        return jsonify({
            'success': True,
            'message': 'User created successfully',
            'user_id': user.id
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_api_bp.route('/users')
@security_service.require_role(['admin'])
def get_users():
    """Get list of users with pagination"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        role_filter = request.args.get('role')
        search = request.args.get('search', '').strip()
        
        # Build query
        query = User.query
        
        if role_filter:
            query = query.filter(User.role == role_filter)
        
        if search:
            query = query.filter(
                db.or_(
                    User.name.contains(search),
                    User.email.contains(search)
                )
            )
        
        # Paginate
        users = query.order_by(User.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'success': True,
            'users': [
                {
                    **user.to_dict(),
                    'last_login': user.last_login.isoformat() if user.last_login else None
                }
                for user in users.items
            ],
            'pagination': {
                'page': users.page,
                'pages': users.pages,
                'per_page': users.per_page,
                'total': users.total,
                'has_next': users.has_next,
                'has_prev': users.has_prev
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_api_bp.route('/users/<int:user_id>', methods=['PUT'])
@security_service.require_role(['admin'])
def update_user(user_id):
    """Update user details"""
    try:
        user = User.query.get_or_404(user_id)
        data = request.get_json()
        
        # Update allowed fields
        updateable_fields = ['name', 'email', 'phone', 'is_active']
        
        for field in updateable_fields:
            if field in data:
                if field == 'email':
                    # Check if new email already exists
                    existing = User.query.filter_by(email=data['email']).first()
                    if existing and existing.id != user_id:
                        return jsonify({'error': 'Email already exists'}), 400
                
                setattr(user, field, data[field])
        
        # Update password if provided
        if data.get('password'):
            user.set_password(data['password'])
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'User updated successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@admin_api_bp.route('/impersonate', methods=['POST'])
@security_service.require_role(['admin'])
def impersonate_user():
    """Create impersonation token for viewing as another user"""
    try:
        data = request.get_json()
        target_user_id = data.get('user_id')
        
        if not target_user_id:
            return jsonify({'error': 'User ID is required'}), 400
        
        target_user = User.query.get(target_user_id)
        if not target_user:
            return jsonify({'error': 'Target user not found'}), 404
        
        # Create short-lived token (1 hour) with special claims
        from flask_jwt_extended import create_access_token
        from datetime import timedelta
        
        impersonation_token = create_access_token(
            identity=target_user_id,
            expires_delta=timedelta(hours=1),
            additional_claims={
                'impersonated': True,
                'impersonator_id': security_service.get_current_user().id,
                'read_only': True
            }
        )
        
        return jsonify({
            'success': True,
            'impersonation_token': impersonation_token,
            'target_user': {
                'id': target_user.id,
                'name': target_user.name,
                'email': target_user.email,
                'role': target_user.role
            },
            'expires_in': 3600  # 1 hour
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_api_bp.route('/dashboard-data')
@security_service.require_role(['admin'])
def get_dashboard_data():
    """Get comprehensive dashboard data"""
    try:
        today = datetime.utcnow().date()
        week_ago = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)
        
        # User counts
        total_users = User.query.filter_by(is_active=True).count()
        total_students = User.query.filter_by(role='student', is_active=True).count()
        total_operators = User.query.filter_by(role='operator', is_active=True).count()
        total_mentors = User.query.filter_by(role='mentor', is_active=True).count()
        
        # Activity metrics
        dau = db.session.query(db.func.count(db.func.distinct(Attempt.student_id))).filter(
            db.func.date(Attempt.timestamp) == today
        ).scalar() or 0
        
        wau = db.session.query(db.func.count(db.func.distinct(Attempt.student_id))).filter(
            db.func.date(Attempt.timestamp) >= week_ago
        ).scalar() or 0
        
        # Content metrics
        total_questions = Question.query.filter_by(is_active=True).count()
        total_lectures = Lecture.query.filter_by(is_active=True).count()
        
        # Engagement metrics
        questions_today = Attempt.query.filter(
            db.func.date(Attempt.timestamp) == today
        ).count()
        
        questions_week = Attempt.query.filter(
            db.func.date(Attempt.timestamp) >= week_ago
        ).count()
        
        # Doubt metrics
        open_doubts = Doubt.query.filter_by(status='open').count()
        resolved_doubts_week = Doubt.query.filter(
            Doubt.status == 'resolved',
            db.func.date(Doubt.resolved_at) >= week_ago
        ).count()
        
        # Weekly trend data
        weekly_attempts = []
        for i in range(7):
            date = today - timedelta(days=i)
            attempts = Attempt.query.filter(
                db.func.date(Attempt.timestamp) == date
            ).count()
            weekly_attempts.append({
                'date': date.isoformat(),
                'attempts': attempts
            })
        
        return jsonify({
            'success': True,
            'dashboard': {
                'user_counts': {
                    'total_users': total_users,
                    'students': total_students,
                    'operators': total_operators,
                    'mentors': total_mentors
                },
                'activity': {
                    'dau': dau,
                    'wau': wau
                },
                'content': {
                    'total_questions': total_questions,
                    'total_lectures': total_lectures
                },
                'engagement': {
                    'questions_today': questions_today,
                    'questions_week': questions_week
                },
                'support': {
                    'open_doubts': open_doubts,
                    'resolved_doubts_week': resolved_doubts_week
                },
                'trends': {
                    'weekly_attempts': weekly_attempts
                }
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_api_bp.route('/batches')
@security_service.require_role(['admin'])
def get_batches():
    """Get all batches"""
    try:
        batches = Batch.query.filter_by(is_active=True).all()
        
        return jsonify({
            'success': True,
            'batches': [batch.to_dict() for batch in batches]
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_api_bp.route('/batches', methods=['POST'])
@security_service.require_role(['admin'])
def create_batch():
    """Create a new batch"""
    try:
        data = request.get_json()
        
        required_fields = ['name', 'course']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        # Check if batch name already exists
        existing = Batch.query.filter_by(name=data['name']).first()
        if existing:
            return jsonify({'error': 'Batch name already exists'}), 400
        
        batch = Batch(
            name=data['name'],
            course=data['course'],
            description=data.get('description')
        )
        
        batch.save()
        
        return jsonify({
            'success': True,
            'message': 'Batch created successfully',
            'batch_id': batch.id
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_api_bp.route('/system-health')
@security_service.require_role(['admin'])
def get_system_health():
    """Get system health metrics"""
    try:
        # Database health
        try:
            db.session.execute(db.text('SELECT 1'))
            db_status = 'healthy'
        except:
            db_status = 'unhealthy'
        
        # Recent errors (would need error logging system)
        recent_errors = 0  # Placeholder
        
        # Storage usage (basic check)
        import os
        from config import Config
        
        storage_used = 0
        upload_folder = Config.UPLOAD_FOLDER
        if os.path.exists(upload_folder):
            for root, dirs, files in os.walk(upload_folder):
                for file in files:
                    try:
                        storage_used += os.path.getsize(os.path.join(root, file))
                    except:
                        pass
        
        storage_used_mb = round(storage_used / (1024 * 1024), 2)
        
        return jsonify({
            'success': True,
            'health': {
                'database': db_status,
                'storage_used_mb': storage_used_mb,
                'recent_errors': recent_errors,
                'uptime': 'Available',  # Would need proper uptime tracking
                'timestamp': datetime.utcnow().isoformat()
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
