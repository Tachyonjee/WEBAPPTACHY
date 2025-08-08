"""
Admission Management Blueprint
Handles admission applications, document verification, and student/parent account creation
"""

from flask import Blueprint, render_template, request, jsonify, session, flash, redirect, url_for
from datetime import datetime, date
from functools import wraps
import os
from werkzeug.utils import secure_filename
from extensions import db
from models.user import User
from models.student import StudentProgress
from models.admission import AdmissionApplication, AdmissionDocument, AssessmentResult, AdmissionStatus

admission_bp = Blueprint('admission', __name__, url_prefix='/admission')

def role_required(*allowed_roles):
    """Decorator to check if user has required role for admission management"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                return jsonify({'error': 'Authentication required'}), 401
            
            user = User.query.get(session['user_id'])
            if not user or user.role not in allowed_roles:
                return jsonify({'error': 'Access denied'}), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# ============= ADMISSION APPLICATION ROUTES =============

@admission_bp.route('/apply', methods=['GET', 'POST'])
def apply():
    """Public admission application form - accessible by parents/reception"""
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        
        # Create admission application
        application = AdmissionApplication(
            application_number=AdmissionApplication.generate_application_number(),
            student_name=data.get('student_name'),
            class_applied=data.get('class_applied'),
            batch_type=data.get('batch_type'),
            date_of_birth=datetime.strptime(data.get('date_of_birth'), '%Y-%m-%d').date(),
            father_name=data.get('father_name'),
            mother_name=data.get('mother_name'),
            parent_mobile=data.get('parent_mobile'),
            parent_email=data.get('parent_email'),
            student_mobile=data.get('student_mobile'),
            address=data.get('address'),
            blood_group=data.get('blood_group'),
            created_by_id=session.get('user_id', 1)  # Default to system user if no session
        )
        
        db.session.add(application)
        db.session.commit()
        
        if request.is_json:
            return jsonify({
                'success': True,
                'application_number': application.application_number,
                'application_id': application.id,
                'message': f'Application submitted successfully. Application Number: {application.application_number}'
            })
        else:
            flash(f'Application submitted successfully. Application Number: {application.application_number}', 'success')
            return redirect(url_for('admission.application_status', app_number=application.application_number))
    
    return render_template('admission/apply.html')

@admission_bp.route('/status/<app_number>')
def application_status(app_number):
    """Check application status"""
    application = AdmissionApplication.query.filter_by(application_number=app_number).first_or_404()
    
    return render_template('admission/status.html', application=application)

# ============= RECEPTION MANAGEMENT =============

@admission_bp.route('/reception/dashboard')
@role_required('reception', 'admin_coordinator', 'admin')
def reception_dashboard():
    """Reception dashboard for admission management"""
    # Get recent applications
    recent_applications = AdmissionApplication.query.order_by(
        AdmissionApplication.application_date.desc()
    ).limit(10).all()
    
    # Get applications by status
    pending_applications = AdmissionApplication.query.filter(
        AdmissionApplication.status.in_([AdmissionStatus.ENQUIRY, AdmissionStatus.APPLICATION_SUBMITTED])
    ).count()
    
    return render_template('admission/reception_dashboard.html',
                         recent_applications=recent_applications,
                         pending_applications=pending_applications)

@admission_bp.route('/reception/process/<int:application_id>', methods=['GET', 'POST'])
@role_required('reception', 'admin_coordinator', 'admin')
def process_application(application_id):
    """Process admission application"""
    application = AdmissionApplication.query.get_or_404(application_id)
    
    if request.method == 'POST':
        data = request.get_json()
        action = data.get('action')
        
        if action == 'approve_documents':
            application.status = AdmissionStatus.DOCUMENTS_VERIFIED
            application.processed_by_id = session['user_id']
            
        elif action == 'request_documents':
            application.status = AdmissionStatus.DOCUMENTS_PENDING
            
        elif action == 'admit_student':
            # Create student and parent accounts
            student_username, student_password = User.generate_student_credentials(application.student_name)
            parent_username, parent_password = User.generate_parent_credentials(student_username)
            
            # Create student user
            student_user = User(
                username=student_username,
                email=application.parent_email,  # Use parent email initially
                full_name=application.student_name,
                phone=application.student_mobile,
                role='student',
                goal_exam=application.batch_type,
                batch_name=f"{application.class_applied}-{application.batch_type}",
                class_level=application.class_applied,
                address=application.address
            )
            student_user.set_password(student_password)
            
            # Create parent user
            parent_user = User(
                username=parent_username,
                email=application.parent_email,
                full_name=f"Parent of {application.student_name}",
                phone=application.parent_mobile,
                role='parent',
                parent_of_student_id=None,  # Will be updated after student is created
                address=application.address
            )
            parent_user.set_password(parent_password)
            
            db.session.add(student_user)
            db.session.add(parent_user)
            db.session.flush()  # Get IDs
            
            # Update parent reference
            parent_user.parent_of_student_id = student_user.id
            
            # Create student progress record
            progress = StudentProgress(
                user_id=student_user.id,
                current_class=application.class_applied,
                current_batch=application.batch_type,
                enrollment_date=datetime.now()
            )
            
            db.session.add(progress)
            
            # Update application
            application.student_user_id = student_user.id
            application.parent_user_id = parent_user.id
            application.status = AdmissionStatus.ADMITTED
            application.admission_date = datetime.now()
            application.processed_by_id = session['user_id']
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Student admitted successfully',
                'student_credentials': {
                    'username': student_username,
                    'password': student_password
                },
                'parent_credentials': {
                    'username': parent_username,
                    'password': parent_password
                }
            })
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Application status updated to {application.status.value}'
        })
    
    return render_template('admission/process_application.html', application=application)

# ============= DOCUMENT MANAGEMENT =============

@admission_bp.route('/documents/upload/<int:application_id>', methods=['POST'])
def upload_document(application_id):
    """Upload documents for admission application"""
    application = AdmissionApplication.query.get_or_404(application_id)
    
    if 'document' not in request.files:
        return jsonify({'error': 'No document file provided'}), 400
    
    file = request.files['document']
    document_type = request.form.get('document_type')
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    # Save file
    filename = secure_filename(file.filename)
    upload_path = os.path.join('uploads/documents', str(application_id))
    os.makedirs(upload_path, exist_ok=True)
    
    file_path = os.path.join(upload_path, f"{document_type}_{filename}")
    file.save(file_path)
    
    # Create document record
    document = AdmissionDocument(
        application_id=application_id,
        document_type=document_type,
        file_path=file_path,
        original_filename=filename,
        uploaded_by_id=session.get('user_id')
    )
    
    db.session.add(document)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': f'{document_type} uploaded successfully',
        'document_id': document.id
    })

@admission_bp.route('/documents/verify/<int:document_id>', methods=['POST'])
@role_required('reception', 'admin_coordinator', 'admin')
def verify_document(document_id):
    """Verify uploaded document"""
    document = AdmissionDocument.query.get_or_404(document_id)
    
    document.verified = True
    document.verified_at = datetime.now()
    document.verified_by_id = session['user_id']
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': f'{document.document_type} verified successfully'
    })

# ============= ASSESSMENT MANAGEMENT =============

@admission_bp.route('/assessment/conduct/<int:application_id>', methods=['GET', 'POST'])
@role_required('academic_coordinator', 'mentor', 'admin')
def conduct_assessment(application_id):
    """Conduct scientific assessment for admitted student"""
    application = AdmissionApplication.query.get_or_404(application_id)
    
    if request.method == 'POST':
        data = request.get_json()
        
        # Save assessment results
        for assessment_type, result in data.get('results', {}).items():
            assessment = AssessmentResult(
                application_id=application_id,
                assessment_type=assessment_type,
                score=result['score'],
                max_score=result['max_score'],
                percentage=round((result['score'] / result['max_score']) * 100, 2),
                conducted_by_id=session['user_id'],
                notes=result.get('notes')
            )
            db.session.add(assessment)
        
        application.assessment_completed = True
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Assessment completed successfully'
        })
    
    return render_template('admission/conduct_assessment.html', application=application)

# ============= API ENDPOINTS =============

@admission_bp.route('/api/applications')
@role_required('reception', 'admin_coordinator', 'academic_coordinator', 'admin')
def api_applications():
    """API endpoint for admission applications"""
    status_filter = request.args.get('status')
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 20))
    
    query = AdmissionApplication.query
    
    if status_filter:
        query = query.filter(AdmissionApplication.status == AdmissionStatus(status_filter))
    
    applications = query.order_by(AdmissionApplication.application_date.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'applications': [{
            'id': app.id,
            'application_number': app.application_number,
            'student_name': app.student_name,
            'class_applied': app.class_applied,
            'batch_type': app.batch_type,
            'parent_mobile': app.parent_mobile,
            'status': app.status.value,
            'application_date': app.application_date.strftime('%Y-%m-%d'),
            'admission_date': app.admission_date.strftime('%Y-%m-%d') if app.admission_date else None
        } for app in applications.items],
        'total': applications.total,
        'pages': applications.pages,
        'current_page': page
    })

@admission_bp.route('/api/statistics')
@role_required('admin_coordinator', 'principal', 'director', 'admin')
def api_admission_statistics():
    """API endpoint for admission statistics"""
    today = datetime.now().date()
    this_month = datetime.now().replace(day=1).date()
    
    stats = {
        'total_applications': AdmissionApplication.query.count(),
        'today_applications': AdmissionApplication.query.filter(
            db.func.date(AdmissionApplication.application_date) == today
        ).count(),
        'this_month_applications': AdmissionApplication.query.filter(
            AdmissionApplication.application_date >= this_month
        ).count(),
        'admitted_students': AdmissionApplication.query.filter(
            AdmissionApplication.status == AdmissionStatus.ADMITTED
        ).count(),
        'pending_applications': AdmissionApplication.query.filter(
            AdmissionApplication.status.in_([
                AdmissionStatus.ENQUIRY,
                AdmissionStatus.APPLICATION_SUBMITTED,
                AdmissionStatus.DOCUMENTS_PENDING
            ])
        ).count()
    }
    
    return jsonify(stats)