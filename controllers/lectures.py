from flask import Blueprint, request, jsonify
from datetime import datetime, date
from extensions import db
from models import Lecture, LectureTopics, Syllabus, Student, PracticeRecommendation, Question
from services.security import security_service
from services.storage import storage_service
from services.recommendations import recommendation_service
import re

lectures_bp = Blueprint('lectures', __name__)

@lectures_bp.route('/', methods=['GET'])
def get_lectures():
    """Get lectures with filtering and pagination"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 50)
        subject = request.args.get('subject')
        date_filter = request.args.get('date')
        search = request.args.get('search', '').strip()
        
        # Build query
        query = Lecture.query.filter_by(is_active=True)
        
        if subject:
            query = query.filter(Lecture.subject == subject)
        
        if date_filter:
            try:
                filter_date = datetime.strptime(date_filter, '%Y-%m-%d').date()
                query = query.filter(Lecture.date == filter_date)
            except ValueError:
                return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
        
        if search:
            query = query.filter(
                db.or_(
                    Lecture.title.contains(search),
                    Lecture.notes.contains(search)
                )
            )
        
        # Paginate
        lectures = query.order_by(Lecture.date.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        # Prepare response data
        lectures_data = []
        for lecture in lectures.items:
            lecture_dict = lecture.to_dict()
            
            # Add creator info
            lecture_dict['creator_name'] = lecture.creator.name
            
            # Add attached topics
            topics = db.session.query(LectureTopics, Syllabus).join(
                Syllabus, LectureTopics.syllabus_id == Syllabus.id
            ).filter(LectureTopics.lecture_id == lecture.id).all()
            
            lecture_dict['topics'] = [
                {
                    'id': syllabus.id,
                    'subject': syllabus.subject,
                    'chapter': syllabus.chapter,
                    'topic': syllabus.topic
                }
                for _, syllabus in topics
            ]
            
            # Add embed URL for YouTube videos
            if lecture.resource_type == 'youtube':
                lecture_dict['embed_url'] = lecture.get_youtube_embed_url()
            
            lectures_data.append(lecture_dict)
        
        return jsonify({
            'success': True,
            'lectures': lectures_data,
            'pagination': {
                'page': lectures.page,
                'pages': lectures.pages,
                'per_page': lectures.per_page,
                'total': lectures.total,
                'has_next': lectures.has_next,
                'has_prev': lectures.has_prev
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@lectures_bp.route('/', methods=['POST'])
@security_service.require_role(['operator', 'admin'])
def create_lecture():
    """Create a new lecture"""
    try:
        # Handle both JSON and form data
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form.to_dict()
        
        # Validate required fields
        required_fields = ['title', 'date', 'subject', 'resource_type']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        # Validate subject
        valid_subjects = ['Physics', 'Chemistry', 'Biology', 'Mathematics']
        if data['subject'] not in valid_subjects:
            return jsonify({'error': f'Subject must be one of: {", ".join(valid_subjects)}'}), 400
        
        # Validate resource type
        if data['resource_type'] not in ['youtube', 'video']:
            return jsonify({'error': 'Resource type must be youtube or video'}), 400
        
        # Parse date
        try:
            lecture_date = datetime.strptime(data['date'], '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
        
        # Handle resource URL
        resource_url = data.get('resource_url', '').strip()
        
        if data['resource_type'] == 'youtube':
            if not resource_url:
                return jsonify({'error': 'YouTube URL is required'}), 400
            
            # Validate YouTube URL
            if not _is_valid_youtube_url(resource_url):
                return jsonify({'error': 'Invalid YouTube URL'}), 400
                
        elif data['resource_type'] == 'video':
            # Handle file upload
            if 'video_file' in request.files:
                video_file = request.files['video_file']
                if video_file.filename:
                    # Upload video file
                    upload_result = storage_service.save_file(video_file, 'videos')
                    if upload_result['success']:
                        resource_url = upload_result['url']
                    else:
                        return jsonify({'error': upload_result['error']}), 500
            elif not resource_url:
                return jsonify({'error': 'Video file or URL is required'}), 400
        
        # Get current user
        current_user = security_service.get_current_user()
        
        # Create lecture
        lecture = Lecture(
            title=data['title'],
            date=lecture_date,
            subject=data['subject'],
            resource_type=data['resource_type'],
            resource_url=resource_url,
            notes=data.get('notes', '').strip(),
            created_by=current_user.id,
            duration_minutes=data.get('duration_minutes', type=int),
            thumbnail_url=data.get('thumbnail_url', '').strip()
        )
        
        lecture.save()
        
        return jsonify({
            'success': True,
            'message': 'Lecture created successfully',
            'lecture_id': lecture.id
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@lectures_bp.route('/<int:lecture_id>', methods=['GET'])
def get_lecture(lecture_id):
    """Get a specific lecture"""
    try:
        lecture = Lecture.query.get_or_404(lecture_id)
        
        if not lecture.is_active:
            return jsonify({'error': 'Lecture not found'}), 404
        
        lecture_data = lecture.to_dict()
        
        # Add creator info
        lecture_data['creator_name'] = lecture.creator.name
        
        # Add attached topics
        topics = db.session.query(LectureTopics, Syllabus).join(
            Syllabus, LectureTopics.syllabus_id == Syllabus.id
        ).filter(LectureTopics.lecture_id == lecture.id).all()
        
        lecture_data['topics'] = [
            {
                'id': syllabus.id,
                'subject': syllabus.subject,
                'chapter': syllabus.chapter,
                'topic': syllabus.topic
            }
            for _, syllabus in topics
        ]
        
        # Add embed URL for YouTube videos
        if lecture.resource_type == 'youtube':
            lecture_data['embed_url'] = lecture.get_youtube_embed_url()
        
        # Get practice recommendations count
        recommendations_count = PracticeRecommendation.query.filter_by(
            lecture_id=lecture.id
        ).count()
        
        lecture_data['practice_recommendations_count'] = recommendations_count
        
        return jsonify({
            'success': True,
            'lecture': lecture_data
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@lectures_bp.route('/<int:lecture_id>', methods=['PUT'])
@security_service.require_role(['operator', 'admin'])
def update_lecture(lecture_id):
    """Update a lecture"""
    try:
        lecture = Lecture.query.get_or_404(lecture_id)
        
        # Handle both JSON and form data
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form.to_dict()
        
        # Update allowed fields
        updateable_fields = ['title', 'date', 'subject', 'notes', 'duration_minutes', 'thumbnail_url']
        
        for field in updateable_fields:
            if field in data:
                if field == 'date':
                    try:
                        lecture.date = datetime.strptime(data['date'], '%Y-%m-%d').date()
                    except ValueError:
                        return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
                elif field == 'subject':
                    valid_subjects = ['Physics', 'Chemistry', 'Biology', 'Mathematics']
                    if data['subject'] not in valid_subjects:
                        return jsonify({'error': f'Subject must be one of: {", ".join(valid_subjects)}'}), 400
                    lecture.subject = data['subject']
                elif field == 'duration_minutes':
                    try:
                        lecture.duration_minutes = int(data['duration_minutes']) if data['duration_minutes'] else None
                    except ValueError:
                        return jsonify({'error': 'Duration must be a number'}), 400
                else:
                    setattr(lecture, field, data[field])
        
        # Handle resource URL update
        if 'resource_url' in data and data['resource_url'].strip():
            new_url = data['resource_url'].strip()
            if lecture.resource_type == 'youtube' and not _is_valid_youtube_url(new_url):
                return jsonify({'error': 'Invalid YouTube URL'}), 400
            lecture.resource_url = new_url
        
        # Handle video file upload
        if 'video_file' in request.files:
            video_file = request.files['video_file']
            if video_file.filename:
                upload_result = storage_service.save_file(video_file, 'videos')
                if upload_result['success']:
                    lecture.resource_url = upload_result['url']
                    lecture.resource_type = 'video'
                else:
                    return jsonify({'error': upload_result['error']}), 500
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Lecture updated successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@lectures_bp.route('/<int:lecture_id>', methods=['DELETE'])
@security_service.require_role(['admin'])
def delete_lecture(lecture_id):
    """Delete a lecture (admin only)"""
    try:
        lecture = Lecture.query.get_or_404(lecture_id)
        
        # Soft delete
        lecture.is_active = False
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Lecture deleted successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@lectures_bp.route('/<int:lecture_id>/topics', methods=['POST'])
@security_service.require_role(['operator', 'admin'])
def attach_topics_to_lecture(lecture_id):
    """Attach syllabus topics to a lecture"""
    try:
        lecture = Lecture.query.get_or_404(lecture_id)
        data = request.get_json()
        
        syllabus_ids = data.get('syllabus_ids', [])
        if not syllabus_ids:
            return jsonify({'error': 'At least one syllabus topic ID is required'}), 400
        
        # Validate all syllabus IDs exist
        valid_topics = Syllabus.query.filter(Syllabus.id.in_(syllabus_ids)).all()
        if len(valid_topics) != len(syllabus_ids):
            return jsonify({'error': 'Some syllabus topic IDs are invalid'}), 400
        
        # Remove existing topic associations
        LectureTopics.query.filter_by(lecture_id=lecture_id).delete()
        
        # Add new associations
        for syllabus_id in syllabus_ids:
            lecture_topic = LectureTopics(
                lecture_id=lecture_id,
                syllabus_id=syllabus_id
            )
            db.session.add(lecture_topic)
        
        db.session.commit()
        
        # Generate practice recommendations
        recommendation_service.generate_lecture_recommendations(lecture_id)
        
        return jsonify({
            'success': True,
            'message': f'Attached {len(syllabus_ids)} topics to lecture',
            'attached_topics': len(syllabus_ids)
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@lectures_bp.route('/<int:lecture_id>/recommendations')
def get_lecture_recommendations(lecture_id):
    """Get practice recommendations for a lecture"""
    try:
        lecture = Lecture.query.get_or_404(lecture_id)
        
        # Get current user (if student)
        current_user = security_service.get_current_user()
        student_id = None
        if current_user and current_user.role == 'student' and current_user.student_profile:
            student_id = current_user.student_profile.id
        
        # Build query for recommendations
        query = db.session.query(PracticeRecommendation, Question).join(
            Question, PracticeRecommendation.question_id == Question.id
        ).filter(
            PracticeRecommendation.lecture_id == lecture_id,
            Question.is_active == True
        )
        
        # Filter by student if applicable
        if student_id:
            query = query.filter(
                db.or_(
                    PracticeRecommendation.student_id == student_id,
                    PracticeRecommendation.student_id.is_(None)
                )
            )
        
        recommendations = query.order_by(
            PracticeRecommendation.difficulty_level.asc(),
            PracticeRecommendation.created_at.desc()
        ).all()
        
        # Organize by topic
        recommendations_by_topic = {}
        for recommendation, question in recommendations:
            topic = recommendation.topic
            if topic not in recommendations_by_topic:
                recommendations_by_topic[topic] = []
            
            recommendations_by_topic[topic].append({
                'recommendation_id': recommendation.id,
                'question_id': question.id,
                'question_text': question.question_text[:200] + '...' if len(question.question_text) > 200 else question.question_text,
                'difficulty': recommendation.difficulty_level,
                'subject': recommendation.subject,
                'is_completed': recommendation.is_completed,
                'completed_at': recommendation.completed_at.isoformat() if recommendation.completed_at else None
            })
        
        return jsonify({
            'success': True,
            'lecture_id': lecture_id,
            'lecture_title': lecture.title,
            'recommendations': recommendations_by_topic
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@lectures_bp.route('/subjects')
def get_lecture_subjects():
    """Get list of subjects with lectures"""
    try:
        subjects = db.session.query(Lecture.subject.distinct()).filter_by(
            is_active=True
        ).all()
        
        return jsonify({
            'success': True,
            'subjects': [subject[0] for subject in subjects]
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@lectures_bp.route('/dates')
def get_lecture_dates():
    """Get list of dates with lectures"""
    try:
        dates = db.session.query(Lecture.date.distinct()).filter_by(
            is_active=True
        ).order_by(Lecture.date.desc()).limit(30).all()
        
        return jsonify({
            'success': True,
            'dates': [date[0].isoformat() for date in dates]
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def _is_valid_youtube_url(url):
    """Validate YouTube URL format"""
    youtube_patterns = [
        r'https?://(?:www\.)?youtube\.com/watch\?v=[\w-]+',
        r'https?://youtu\.be/[\w-]+',
        r'https?://(?:www\.)?youtube\.com/embed/[\w-]+'
    ]
    
    return any(re.match(pattern, url) for pattern in youtube_patterns)
