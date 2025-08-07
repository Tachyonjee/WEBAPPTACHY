from flask import Blueprint, request, jsonify, render_template
from extensions import db
from models import Question, Syllabus, Attempt
from services.security import SecurityService, role_required
from services.csv_importer import CSVImporter
from services.llm import get_solution
import json

# Create service instances
security_service = SecurityService()
csv_importer = CSVImporter()

questions_bp = Blueprint('questions', __name__)

@questions_bp.route('/', methods=['GET'])
@role_required('operator', 'admin')
def get_questions():
    """Get questions with filtering and pagination"""
    try:
        # Get query parameters
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        subject = request.args.get('subject')
        chapter = request.args.get('chapter')
        topic = request.args.get('topic')
        difficulty = request.args.get('difficulty', type=int)
        search = request.args.get('search', '').strip()
        
        # Build query
        query = Question.query.filter_by(is_active=True)
        
        if subject:
            query = query.filter(Question.subject == subject)
        if chapter:
            query = query.filter(Question.chapter == chapter)
        if topic:
            query = query.filter(Question.topic == topic)
        if difficulty:
            query = query.filter(Question.difficulty == difficulty)
        if search:
            query = query.filter(Question.question_text.contains(search))
        
        # Paginate
        questions = query.order_by(Question.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'success': True,
            'questions': [q.to_dict() for q in questions.items],
            'pagination': {
                'page': questions.page,
                'pages': questions.pages,
                'per_page': questions.per_page,
                'total': questions.total,
                'has_next': questions.has_next,
                'has_prev': questions.has_prev
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@questions_bp.route('/', methods=['POST'])
@role_required('operator', 'admin')
def create_question():
    """Create a new question"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['subject', 'chapter', 'topic', 'difficulty', 'question_text', 'correct_answer']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        # Validate difficulty
        if data['difficulty'] not in [1, 2, 3, 4, 5]:
            return jsonify({'error': 'Difficulty must be between 1 and 5'}), 400
        
        # Validate subject
        valid_subjects = ['Physics', 'Chemistry', 'Biology', 'Mathematics']
        if data['subject'] not in valid_subjects:
            return jsonify({'error': f'Subject must be one of: {", ".join(valid_subjects)}'}), 400
        
        # Process options if provided
        options = None
        if data.get('options'):
            if isinstance(data['options'], dict):
                options = data['options']
            else:
                try:
                    options = json.loads(data['options'])
                except:
                    return jsonify({'error': 'Invalid options format'}), 400
        
        # Create question
        question = Question()
        question.subject = data['subject']
        question.chapter = data['chapter']
        question.topic = data['topic']
        question.difficulty = data['difficulty']
        question.question_text = data['question_text']
        question.correct_answer = data['correct_answer']
        question.options = options
        question.hint = data.get('hint')
        question.source = data.get('source')
        
        db.session.add(question)
        db.session.commit()
        
        # Ensure syllabus entry exists
        _ensure_syllabus_entry(data['subject'], data['chapter'], data['topic'])
        
        return jsonify({
            'success': True,
            'message': 'Question created successfully',
            'question_id': question.id
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@questions_bp.route('/<int:question_id>', methods=['GET'])
@role_required('operator', 'admin', 'mentor')
def get_question(question_id):
    """Get a specific question"""
    try:
        question = Question.query.get_or_404(question_id)
        
        # Get question statistics
        stats = {
            'total_attempts': question.get_attempt_count(),
            'accuracy_rate': round(question.get_accuracy_rate() * 100, 1),
            'avg_time': round(question.get_avg_time_taken(), 1)
        }
        
        question_data = question.to_dict()
        question_data['stats'] = stats
        
        return jsonify({
            'success': True,
            'question': question_data
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@questions_bp.route('/<int:question_id>', methods=['PUT'])
@role_required('operator', 'admin')
def update_question(question_id):
    """Update a question"""
    try:
        question = Question.query.get_or_404(question_id)
        data = request.get_json()
        
        # Update fields if provided
        updateable_fields = ['subject', 'chapter', 'topic', 'difficulty', 'question_text', 'correct_answer', 'hint', 'source']
        
        for field in updateable_fields:
            if field in data:
                if field == 'difficulty':
                    if data[field] not in [1, 2, 3, 4, 5]:
                        return jsonify({'error': 'Difficulty must be between 1 and 5'}), 400
                elif field == 'subject':
                    valid_subjects = ['Physics', 'Chemistry', 'Biology', 'Mathematics']
                    if data[field] not in valid_subjects:
                        return jsonify({'error': f'Subject must be one of: {", ".join(valid_subjects)}'}), 400
                
                setattr(question, field, data[field])
        
        # Update options if provided
        if 'options' in data:
            if isinstance(data['options'], dict):
                question.options = data['options']
            else:
                try:
                    question.options = json.loads(data['options'])
                except:
                    return jsonify({'error': 'Invalid options format'}), 400
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Question updated successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@questions_bp.route('/<int:question_id>', methods=['DELETE'])
@role_required('admin')
def delete_question(question_id):
    """Delete a question (admin only)"""
    try:
        question = Question.query.get_or_404(question_id)
        
        # Soft delete - just mark as inactive
        question.is_active = False
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Question deleted successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@questions_bp.route('/bulk-upload', methods=['POST'])
@role_required('operator', 'admin')
def bulk_upload_questions():
    """Bulk upload questions from CSV/XLSX"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Validate file
        allowed_extensions = ['.csv', '.xlsx']
        filename = file.filename or ''
        if not any(filename.lower().endswith(ext) for ext in allowed_extensions):
            return jsonify({'error': 'Only CSV and XLSX files are allowed'}), 400
        
        # Save file temporarily
        from services.storage import storage_service
        save_result = storage_service.save_file(file, 'temp')
        
        if not save_result['success']:
            return jsonify({'error': save_result['error']}), 500
        
        file_path = save_result['file_path']
        
        try:
            # Get dry_run parameter
            dry_run = request.form.get('dry_run', 'false').lower() == 'true'
            
            if dry_run:
                # Validate only
                result = csv_importer.validate_file(file_path)
            else:
                # Import questions
                result = csv_importer.import_questions(file_path, dry_run=False)
            
            # Clean up temp file
            storage_service.delete_file(file_path)
            
            return jsonify(result)
            
        except Exception as e:
            # Clean up temp file on error
            storage_service.delete_file(file_path)
            raise e
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@questions_bp.route('/template')
@role_required('operator', 'admin')
def download_template():
    """Download CSV template for bulk upload"""
    try:
        template_content = csv_importer.get_template_csv()
        
        from flask import Response
        return Response(
            template_content,
            mimetype='text/csv',
            headers={'Content-Disposition': 'attachment; filename=questions_template.csv'}
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@questions_bp.route('/subjects')
def get_subjects():
    """Get list of subjects"""
    subjects = ['Physics', 'Chemistry', 'Biology', 'Mathematics']
    return jsonify({
        'success': True,
        'subjects': subjects
    })

@questions_bp.route('/chapters')
def get_chapters():
    """Get chapters for a subject"""
    subject = request.args.get('subject')
    if not subject:
        return jsonify({'error': 'Subject is required'}), 400
    
    chapters = db.session.query(Question.chapter.distinct()).filter_by(
        subject=subject, is_active=True
    ).all()
    
    return jsonify({
        'success': True,
        'chapters': [chapter[0] for chapter in chapters]
    })

@questions_bp.route('/topics')
def get_topics():
    """Get topics for a chapter"""
    subject = request.args.get('subject')
    chapter = request.args.get('chapter')
    
    if not subject:
        return jsonify({'error': 'Subject is required'}), 400
    
    query = Question.query.filter_by(subject=subject, is_active=True)
    if chapter:
        query = query.filter_by(chapter=chapter)
    
    topics = query.with_entities(Question.topic.distinct()).all()
    
    return jsonify({
        'success': True,
        'topics': [topic[0] for topic in topics]
    })

@questions_bp.route('/<int:question_id>/solution')
@role_required('student', 'operator', 'admin', 'mentor')
def get_question_solution(question_id):
    """Get AI-generated solution for a question"""
    try:
        question = Question.query.get_or_404(question_id)
        
        # Get current user for logging
        from services.security import get_current_user
        current_user = get_current_user()
        student_id = None
        if current_user and current_user.role == 'student' and current_user.student_profile:
            student_id = current_user.student_profile.id
        
        # Generate solution
        solution = get_solution(question, student_id)
        
        return jsonify(solution)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@questions_bp.route('/stats')
@role_required('operator', 'admin')
def get_question_stats():
    """Get question statistics"""
    try:
        # Overall stats
        total_questions = Question.query.filter_by(is_active=True).count()
        
        # Subject distribution
        subject_dist = db.session.query(
            Question.subject,
            db.func.count(Question.id).label('count')
        ).filter_by(is_active=True).group_by(Question.subject).all()
        
        # Difficulty distribution
        difficulty_dist = db.session.query(
            Question.difficulty,
            db.func.count(Question.id).label('count')
        ).filter_by(is_active=True).group_by(Question.difficulty).all()
        
        # Questions needing review (low accuracy) - simplified for now
        problem_questions = 0  # TODO: Implement based on actual attempt statistics
        
        return jsonify({
            'success': True,
            'stats': {
                'total_questions': total_questions,
                'subject_distribution': [
                    {'subject': subject, 'count': count}
                    for subject, count in subject_dist
                ],
                'difficulty_distribution': [
                    {'difficulty': diff, 'count': count}
                    for diff, count in difficulty_dist
                ],
                'problem_questions': problem_questions
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def _ensure_syllabus_entry(subject, chapter, topic):
    """Ensure syllabus entry exists for the topic"""
    existing = Syllabus.query.filter_by(
        subject=subject,
        chapter=chapter,
        topic=topic
    ).first()
    
    if not existing:
        syllabus_entry = Syllabus()
        syllabus_entry.subject = subject
        syllabus_entry.chapter = chapter
        syllabus_entry.topic = topic
        db.session.add(syllabus_entry)
        db.session.commit()
