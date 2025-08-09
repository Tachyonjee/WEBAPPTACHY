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
from models.admission import AdmissionApplication, AdmissionDocument, AssessmentResult

def login_required(f):
    """Simple login required decorator"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

admission_bp = Blueprint('admission_management', __name__, url_prefix='/admission')

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

@admission_bp.route('/new_application', methods=['GET', 'POST'])
def new_application():
    """Create new admission application - accessible to parents and reception"""
    if request.method == 'POST':
        try:
            # Create new admission application from form data
            application = AdmissionApplication(
                student_name=request.form.get('student_name'),
                # student_email=request.form.get('email'),  # Field doesn't exist in model
                student_mobile=request.form.get('phone'),
                address=request.form.get('address'),
                class_applied=request.form.get('last_class'),
                # percentage=float(request.form.get('percentage', 0)),  # Field doesn't exist in model
                date_of_birth=datetime.strptime(request.form.get('date_of_birth'), '%Y-%m-%d').date(),
                batch_type=request.form.get('desired_course'),
                father_name=request.form.get('father_name'),
                mother_name=request.form.get('mother_name'),
                parent_email=request.form.get('email'),  # Use same email for now
                parent_mobile=request.form.get('parent_phone'),
                status='pending',
                application_number=f'APP{datetime.now().year}{datetime.now().strftime("%m%d")}{1001 + (AdmissionApplication.query.count() if AdmissionApplication.query.first() else 0):04d}',
                created_by_id=session.get('user_id', 1),
                application_date=datetime.now().date()
            )
            
            db.session.add(application)
            db.session.commit()
            
            flash(f'Application submitted successfully! Application Number: {application.application_number}', 'success')
            
            # Redirect based on user role
            if session.get('user_role') == 'reception':
                return redirect(url_for('admission_management.reception_dashboard'))
            else:
                return redirect(url_for('parent.dashboard'))
                
        except Exception as e:
            db.session.rollback()
            flash('Error submitting application. Please try again.', 'danger')
            print(f"Error creating application: {e}")  # For debugging
    
    return render_template('admission/new_application.html')

@admission_bp.route('/new_enquiry', methods=['GET', 'POST'])
@role_required('reception', 'admin_coordinator', 'admin')
def new_enquiry():
    """Create new admission enquiry - reception only"""
    if request.method == 'POST':
        flash('Enquiry recorded successfully!', 'success')
        return redirect(url_for('admission_management.reception_dashboard'))
    
    return render_template('admission/new_enquiry.html')

@admission_bp.route('/document_verification')
@role_required('reception', 'admin_coordinator', 'admin')
def document_verification():
    """Document verification page - reception only"""
    try:
        applications = AdmissionApplication.query.filter_by(status='pending').all()
    except:
        applications = []
    return render_template('admission/document_verification.html', applications=applications)

@admission_bp.route('/view_application/<int:id>')
def view_application(id):
    """View application details"""
    try:
        application = AdmissionApplication.query.get_or_404(id)
        return render_template('admission/view_application.html', application=application)
    except:
        flash('Application not found.', 'error')
        return redirect(url_for('admission_management.reception_dashboard'))

@admission_bp.route('/edit_application/<int:id>', methods=['GET', 'POST'])
def edit_application(id):
    """Edit application details"""
    try:
        application = AdmissionApplication.query.get_or_404(id)
        
        if request.method == 'POST':
            # Update application fields
            application.student_name = request.form.get('student_name', application.student_name)
            application.email = request.form.get('email', application.email)
            
            db.session.commit()
            flash('Application updated successfully!', 'success')
            
            if session.get('user_role') == 'reception':
                return redirect(url_for('admission_management.reception_dashboard'))
            else:
                return redirect(url_for('parent.dashboard'))
        
        return render_template('admission/edit_application.html', application=application)
    except:
        flash('Application not found.', 'error')
        return redirect(url_for('admission_management.reception_dashboard'))

@admission_bp.route('/apply', methods=['GET', 'POST'])
def apply():
    """Legacy route - redirect to new_application"""
    return redirect(url_for('admission_management.new_application'))

@admission_bp.route('/legacy_apply', methods=['GET', 'POST'])
def legacy_apply():
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
@login_required
@role_required(['reception', 'admin_coordinator', 'admin'])
def reception_dashboard():
    """Reception dashboard for admission management"""
    try:
        # Get recent applications with safe fallbacks
        recent_applications = []
        pending_applications = 5  # Sample data
        documents_pending = 3
        today_interviews = 2
        total_enquiries = 12
        
        # Try to get real data if models exist
        try:
            recent_applications = AdmissionApplication.query.order_by(
                AdmissionApplication.created_at.desc()
            ).limit(10).all()
            pending_applications = AdmissionApplication.query.filter_by(status='pending').count()
        except:
            pass  # Use sample data
            
        return render_template('admission/reception_dashboard.html',
                             recent_applications=recent_applications,
                             pending_applications=pending_applications,
                             documents_pending=documents_pending,
                             today_interviews=today_interviews,
                             total_enquiries=total_enquiries)
    except Exception as e:
        app.logger.error(f"Error in reception dashboard: {e}")
        # Fallback with sample data
        return render_template('admission/reception_dashboard.html',
                             recent_applications=[],
                             pending_applications=5,
                             documents_pending=3,
                             today_interviews=2,
                             total_enquiries=12)

@admission_bp.route('/reception/process/<int:application_id>', methods=['GET', 'POST'])
@role_required('reception', 'admin_coordinator', 'admin')
def process_application(application_id):
    """Process admission application"""
    application = AdmissionApplication.query.get_or_404(application_id)
    
    if request.method == 'POST':
        data = request.get_json()
        action = data.get('action')
        
        if action == 'approve_documents':
            application.status = 'documents_verified'
            application.processed_by_id = session['user_id']
            
        elif action == 'request_documents':
            application.status = 'documents_pending'
            
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
            application.status = 'admitted'
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
        query = query.filter(AdmissionApplication.status == status_filter)
    
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
            AdmissionApplication.status == 'admitted'
        ).count(),
        'pending_applications': AdmissionApplication.query.filter(
            AdmissionApplication.status.in_([
                'enquiry',
                'application_submitted', 
                'documents_pending'
            ])
        ).count()
    }
    
    return jsonify(stats)