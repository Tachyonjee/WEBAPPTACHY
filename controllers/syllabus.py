from flask import Blueprint, request, jsonify
from extensions import db
from models import Syllabus, SyllabusProgress, Student, Batch
from services.security import security_service

syllabus_bp = Blueprint('syllabus', __name__)

@syllabus_bp.route('/', methods=['GET'])
def get_syllabus():
    """Get syllabus topics with optional filtering"""
    try:
        subject = request.args.get('subject')
        chapter = request.args.get('chapter')
        
        # Build query
        query = Syllabus.query
        
        if subject:
            query = query.filter(Syllabus.subject == subject)
        if chapter:
            query = query.filter(Syllabus.chapter == chapter)
        
        syllabus_topics = query.order_by(
            Syllabus.subject,
            Syllabus.chapter,
            Syllabus.topic
        ).all()
        
        # Group by subject and chapter
        organized_syllabus = {}
        for topic in syllabus_topics:
            if topic.subject not in organized_syllabus:
                organized_syllabus[topic.subject] = {}
            
            if topic.chapter not in organized_syllabus[topic.subject]:
                organized_syllabus[topic.subject][topic.chapter] = []
            
            organized_syllabus[topic.subject][topic.chapter].append({
                'id': topic.id,
                'topic': topic.topic,
                'created_at': topic.created_at.isoformat()
            })
        
        return jsonify({
            'success': True,
            'syllabus': organized_syllabus
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@syllabus_bp.route('/progress', methods=['GET'])
@security_service.require_role(['student', 'mentor', 'admin'])
def get_syllabus_progress():
    """Get syllabus progress for student/batch/mentor"""
    try:
        owner_type = request.args.get('owner_type')  # student, batch, mentor
        owner_id = request.args.get('owner_id', type=int)
        subject = request.args.get('subject')
        
        if not owner_type or not owner_id:
            return jsonify({'error': 'owner_type and owner_id are required'}), 400
        
        # Validate owner_type
        if owner_type not in ['student', 'batch', 'mentor']:
            return jsonify({'error': 'Invalid owner_type'}), 400
        
        # Check authorization
        current_user = security_service.get_current_user()
        if not current_user:
            return jsonify({'error': 'Authentication required'}), 401
        
        # Students can only view their own progress
        if current_user.role == 'student':
            if owner_type != 'student' or (current_user.student_profile and owner_id != current_user.student_profile.id):
                return jsonify({'error': 'Access denied'}), 403
        
        # Build progress query
        progress_query = db.session.query(
            SyllabusProgress, Syllabus
        ).join(
            Syllabus, SyllabusProgress.syllabus_id == Syllabus.id
        ).filter(
            SyllabusProgress.owner_type == owner_type,
            SyllabusProgress.owner_id == owner_id
        )
        
        if subject:
            progress_query = progress_query.filter(Syllabus.subject == subject)
        
        progress_data = progress_query.all()
        
        # Organize progress by subject and chapter
        progress_organized = {}
        for progress, syllabus_topic in progress_data:
            subject_name = syllabus_topic.subject
            chapter_name = syllabus_topic.chapter
            
            if subject_name not in progress_organized:
                progress_organized[subject_name] = {}
            
            if chapter_name not in progress_organized[subject_name]:
                progress_organized[subject_name][chapter_name] = []
            
            progress_organized[subject_name][chapter_name].append({
                'topic_id': syllabus_topic.id,
                'topic': syllabus_topic.topic,
                'status': progress.status,
                'last_updated': progress.last_updated.isoformat()
            })
        
        # Calculate summary statistics
        total_topics = len(progress_data)
        completed_topics = len([p for p, _ in progress_data if p.status == 'completed'])
        in_progress_topics = len([p for p, _ in progress_data if p.status == 'in_progress'])
        
        completion_percentage = (completed_topics / total_topics * 100) if total_topics > 0 else 0
        
        return jsonify({
            'success': True,
            'progress': progress_organized,
            'summary': {
                'total_topics': total_topics,
                'completed_topics': completed_topics,
                'in_progress_topics': in_progress_topics,
                'completion_percentage': round(completion_percentage, 1)
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@syllabus_bp.route('/progress', methods=['PATCH'])
@security_service.require_role(['student', 'mentor', 'admin'])
def update_syllabus_progress():
    """Update progress status for a topic"""
    try:
        data = request.get_json()
        
        syllabus_id = data.get('syllabus_id')
        owner_type = data.get('owner_type')
        owner_id = data.get('owner_id')
        status = data.get('status')
        
        # Validate required fields
        if not all([syllabus_id, owner_type, owner_id, status]):
            return jsonify({'error': 'All fields are required'}), 400
        
        # Validate status
        valid_statuses = ['not_started', 'in_progress', 'completed']
        if status not in valid_statuses:
            return jsonify({'error': f'Status must be one of: {", ".join(valid_statuses)}'}), 400
        
        # Check authorization
        current_user = security_service.get_current_user()
        if not current_user:
            return jsonify({'error': 'Authentication required'}), 401
        
        # Students can only update their own progress
        if current_user.role == 'student':
            if owner_type != 'student' or (current_user.student_profile and owner_id != current_user.student_profile.id):
                return jsonify({'error': 'Access denied'}), 403
        
        # Verify syllabus topic exists
        syllabus_topic = Syllabus.query.get(syllabus_id)
        if not syllabus_topic:
            return jsonify({'error': 'Syllabus topic not found'}), 404
        
        # Find or create progress record
        progress = SyllabusProgress.query.filter_by(
            syllabus_id=syllabus_id,
            owner_type=owner_type,
            owner_id=owner_id
        ).first()
        
        if progress:
            # Update existing progress
            progress.update_status(status)
        else:
            # Create new progress record
            progress = SyllabusProgress(
                syllabus_id=syllabus_id,
                owner_type=owner_type,
                owner_id=owner_id,
                status=status
            )
            progress.save()
        
        return jsonify({
            'success': True,
            'message': 'Progress updated successfully',
            'progress': {
                'syllabus_id': progress.syllabus_id,
                'status': progress.status,
                'last_updated': progress.last_updated.isoformat()
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@syllabus_bp.route('/topics', methods=['POST'])
@security_service.require_role(['operator', 'admin'])
def create_syllabus_topic():
    """Create a new syllabus topic"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['subject', 'chapter', 'topic']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        # Validate subject
        valid_subjects = ['Physics', 'Chemistry', 'Biology', 'Mathematics']
        if data['subject'] not in valid_subjects:
            return jsonify({'error': f'Subject must be one of: {", ".join(valid_subjects)}'}), 400
        
        # Check if topic already exists
        existing = Syllabus.query.filter_by(
            subject=data['subject'],
            chapter=data['chapter'],
            topic=data['topic']
        ).first()
        
        if existing:
            return jsonify({'error': 'Topic already exists in syllabus'}), 409
        
        # Create new topic
        topic = Syllabus(
            subject=data['subject'],
            chapter=data['chapter'],
            topic=data['topic']
        )
        
        topic.save()
        
        return jsonify({
            'success': True,
            'message': 'Syllabus topic created successfully',
            'topic_id': topic.id
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@syllabus_bp.route('/coverage')
@security_service.require_role(['mentor', 'admin'])
def get_syllabus_coverage():
    """Get syllabus coverage statistics"""
    try:
        # Get all syllabus topics
        total_topics = Syllabus.query.count()
        
        # Coverage by subject
        subject_coverage = db.session.query(
            Syllabus.subject,
            db.func.count(Syllabus.id).label('total_topics'),
            db.func.count(SyllabusProgress.id).label('topics_with_progress'),
            db.func.sum(
                db.case(
                    (SyllabusProgress.status == 'completed', 1),
                    else_=0
                )
            ).label('completed_topics')
        ).outerjoin(
            SyllabusProgress, Syllabus.id == SyllabusProgress.syllabus_id
        ).group_by(
            Syllabus.subject
        ).all()
        
        coverage_data = []
        for subject, total, with_progress, completed in subject_coverage:
            coverage_percentage = (completed / total * 100) if total > 0 and completed else 0
            
            coverage_data.append({
                'subject': subject,
                'total_topics': total,
                'topics_with_progress': with_progress or 0,
                'completed_topics': completed or 0,
                'coverage_percentage': round(coverage_percentage, 1)
            })
        
        # Get batch-wise coverage if requested
        batch_coverage = []
        if request.args.get('include_batches') == 'true':
            batches = Batch.query.filter_by(is_active=True).all()
            
            for batch in batches:
                batch_progress = db.session.query(
                    db.func.count(SyllabusProgress.id).label('total_progress'),
                    db.func.sum(
                        db.case(
                            (SyllabusProgress.status == 'completed', 1),
                            else_=0
                        )
                    ).label('completed_progress')
                ).filter(
                    SyllabusProgress.owner_type == 'batch',
                    SyllabusProgress.owner_id == batch.id
                ).first()
                
                total_progress = batch_progress.total_progress or 0
                completed_progress = batch_progress.completed_progress or 0
                
                batch_percentage = (completed_progress / total_progress * 100) if total_progress > 0 else 0
                
                batch_coverage.append({
                    'batch_id': batch.id,
                    'batch_name': batch.name,
                    'course': batch.course,
                    'total_progress_records': total_progress,
                    'completed_topics': completed_progress,
                    'completion_percentage': round(batch_percentage, 1)
                })
        
        return jsonify({
            'success': True,
            'coverage': {
                'total_topics': total_topics,
                'subject_coverage': coverage_data,
                'batch_coverage': batch_coverage
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@syllabus_bp.route('/initialize-progress', methods=['POST'])
@security_service.require_role(['mentor', 'admin'])
def initialize_progress():
    """Initialize progress records for a student or batch"""
    try:
        data = request.get_json()
        
        owner_type = data.get('owner_type')
        owner_id = data.get('owner_id')
        subjects = data.get('subjects', [])
        
        if not owner_type or not owner_id:
            return jsonify({'error': 'owner_type and owner_id are required'}), 400
        
        if owner_type not in ['student', 'batch']:
            return jsonify({'error': 'owner_type must be student or batch'}), 400
        
        # Verify owner exists
        if owner_type == 'student':
            owner = Student.query.get(owner_id)
        else:
            owner = Batch.query.get(owner_id)
        
        if not owner:
            return jsonify({'error': f'{owner_type.title()} not found'}), 404
        
        # Get syllabus topics to initialize
        query = Syllabus.query
        if subjects:
            query = query.filter(Syllabus.subject.in_(subjects))
        
        topics = query.all()
        
        created_count = 0
        for topic in topics:
            # Check if progress already exists
            existing = SyllabusProgress.query.filter_by(
                syllabus_id=topic.id,
                owner_type=owner_type,
                owner_id=owner_id
            ).first()
            
            if not existing:
                progress = SyllabusProgress(
                    syllabus_id=topic.id,
                    owner_type=owner_type,
                    owner_id=owner_id,
                    status='not_started'
                )
                progress.save()
                created_count += 1
        
        return jsonify({
            'success': True,
            'message': f'Initialized progress for {created_count} topics',
            'created_records': created_count
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
