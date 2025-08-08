#!/usr/bin/env python3
"""
Tachyon Institute Management System
Comprehensive educational institute management with visitor management, admissions, academics, and gamification
"""

import os
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.middleware.proxy_fix import ProxyFix
from functools import wraps
import logging
from datetime import datetime
import random

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Initialize Flask app
app = Flask(__name__, static_folder='app/static', template_folder='templates')
app.secret_key = os.environ.get("SESSION_SECRET", "tachyon-institute-secret")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Database configuration
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    'pool_pre_ping': True,
    "pool_recycle": 300,
}

# Initialize extensions
from extensions import db, init_extensions
init_extensions(app)

# Import all models
with app.app_context():
    from models.user import User
    from models.student import StudentProgress, StudentBadge, StudentAttendance
    from models.visitor import Visitor, VisitorMeeting
    from models.admission import AdmissionApplication, AdmissionDocument, AssessmentResult
    from models.academic import (Class, ClassMaterial, DailyPracticeProblem, DPPQuestion, 
                               DPPAttempt, DPPAnswerSubmission, Test, TestQuestion, 
                               TestAttempt, TestAnswerSubmission)

# Register blueprints
from blueprints.visitor_management import visitor_bp
from blueprints.admission_management import admission_bp

app.register_blueprint(visitor_bp)
app.register_blueprint(admission_bp)

# ==================== AUTHENTICATION ====================
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def role_required(required_roles):
    """Decorator for role-based access control"""
    if isinstance(required_roles, str):
        required_roles = [required_roles]
    
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                return redirect(url_for('login'))
            
            user = User.query.get(session['user_id'])
            if not user or user.role not in required_roles:
                flash('Access denied', 'error')
                return redirect(url_for('dashboard'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# ==================== SAMPLE DATA CREATION ====================
def create_sample_users():
    """Create sample users for all roles in Tachyon Institute"""
    sample_users = [
        # Security Staff
        {'username': 'security1', 'password': 'security123', 'role': 'security', 'full_name': 'Rajesh Kumar', 'email': 'security@tachyon.edu', 'department': 'Security'},
        
        # Reception Staff
        {'username': 'reception1', 'password': 'reception123', 'role': 'reception', 'full_name': 'Priya Sharma', 'email': 'reception@tachyon.edu', 'department': 'Administration'},
        
        # Counsellors
        {'username': 'counsellor1', 'password': 'counsellor123', 'role': 'counsellor', 'full_name': 'Dr. Amit Verma', 'email': 'amit.verma@tachyon.edu', 'specialization': 'Career Counselling'},
        
        # Coordinators
        {'username': 'admin_coord1', 'password': 'admin123', 'role': 'admin_coordinator', 'full_name': 'Sneha Gupta', 'email': 'sneha.gupta@tachyon.edu', 'department': 'Administration'},
        {'username': 'academic_coord1', 'password': 'academic123', 'role': 'academic_coordinator', 'full_name': 'Prof. Rajesh Singh', 'email': 'rajesh.singh@tachyon.edu', 'department': 'Academics'},
        
        # Management
        {'username': 'principal', 'password': 'principal123', 'role': 'principal', 'full_name': 'Dr. Meera Joshi', 'email': 'principal@tachyon.edu', 'department': 'Management'},
        {'username': 'director', 'password': 'director123', 'role': 'director', 'full_name': 'Dr. Vikram Patel', 'email': 'director@tachyon.edu', 'department': 'Management'},
        
        # Students
        {'username': 'rahul2025', 'password': 'rahul2025123', 'role': 'student', 'full_name': 'Rahul Sharma', 'email': 'rahul@example.com', 'goal_exam': 'JEE', 'batch_name': 'JEE-2025-A', 'class_level': 'Class 12'},
        {'username': 'priya2025', 'password': 'priya2025123', 'role': 'student', 'full_name': 'Priya Patel', 'email': 'priya@example.com', 'goal_exam': 'NEET', 'batch_name': 'NEET-2025-B', 'class_level': 'Class 12'},
        {'username': 'arjun2026', 'password': 'arjun2026123', 'role': 'student', 'full_name': 'Arjun Singh', 'email': 'arjun@example.com', 'goal_exam': 'JEE', 'batch_name': 'JEE-2026-A', 'class_level': 'Class 11'},
        
        # Parents
        {'username': 'p_rahul2025', 'password': 'p_rahul2025123', 'role': 'parent', 'full_name': 'Mr. Suresh Sharma', 'email': 'suresh.sharma@example.com', 'parent_of_student_id': None},
        {'username': 'p_priya2025', 'password': 'p_priya2025123', 'role': 'parent', 'full_name': 'Mrs. Sunita Patel', 'email': 'sunita.patel@example.com', 'parent_of_student_id': None},
        
        # Mentors
        {'username': 'mentor_physics', 'password': 'mentor123', 'role': 'mentor', 'full_name': 'Dr. Anil Kumar', 'email': 'anil.kumar@tachyon.edu', 'specialization': 'Physics', 'department': 'Faculty'},
        {'username': 'mentor_chemistry', 'password': 'mentor123', 'role': 'mentor', 'full_name': 'Dr. Pooja Agarwal', 'email': 'pooja.agarwal@tachyon.edu', 'specialization': 'Chemistry', 'department': 'Faculty'},
        {'username': 'mentor_math', 'password': 'mentor123', 'role': 'mentor', 'full_name': 'Prof. Ravi Jain', 'email': 'ravi.jain@tachyon.edu', 'specialization': 'Mathematics', 'department': 'Faculty'},
        
        # System Admin
        {'username': 'admin', 'password': 'admin123', 'role': 'admin', 'full_name': 'System Administrator', 'email': 'admin@tachyon.edu', 'department': 'IT'}
    ]
    
    for user_data in sample_users:
        existing_user = User.query.filter_by(username=user_data['username']).first()
        if not existing_user:
            user = User()
            user.username = user_data['username']
            user.email = user_data['email']
            user.role = user_data['role']
            user.full_name = user_data['full_name']
            user.phone = user_data.get('phone')
            user.goal_exam = user_data.get('goal_exam')
            user.batch_name = user_data.get('batch_name')
            user.class_level = user_data.get('class_level')
            user.specialization = user_data.get('specialization')
            user.department = user_data.get('department')
            user.parent_of_student_id = user_data.get('parent_of_student_id')
            user.set_password(user_data['password'])
            db.session.add(user)
            db.session.flush()
            
            # Create student progress for students
            if user_data['role'] == 'student':
                progress = StudentProgress()
                progress.user_id = user.id
                progress.current_class = user_data.get('class_level')
                progress.current_batch = user_data.get('goal_exam')
                progress.total_points = 100 + (hash(user_data['username']) % 500)
                progress.current_streak = hash(user_data['username']) % 15
                progress.best_streak = hash(user_data['username']) % 25
                progress.total_questions_attempted = 20 + (hash(user_data['username']) % 100)
                progress.total_questions_correct = 15 + (hash(user_data['username']) % 80)
                db.session.add(progress)
    
    # Update parent-student relationships
    rahul = User.query.filter_by(username='rahul2025').first()
    priya = User.query.filter_by(username='priya2025').first()
    
    if rahul:
        parent_rahul = User.query.filter_by(username='p_rahul2025').first()
        if parent_rahul:
            parent_rahul.parent_of_student_id = rahul.id
    
    if priya:
        parent_priya = User.query.filter_by(username='p_priya2025').first()
        if parent_priya:
            parent_priya.parent_of_student_id = priya.id
    
    db.session.commit()
    print("Sample users created successfully!")

# ==================== LOGIN ROUTES ====================
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        if not username or not password:
            flash('Username and password are required', 'error')
            return render_template('auth/login.html')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password) and user.is_active:
            session['user_id'] = user.id
            session['user_role'] = user.role
            session['user_name'] = user.full_name
            user.update_last_login()
            flash(f'Welcome back, {user.full_name}!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'error')
            return render_template('auth/login.html')
    
    return render_template('auth/login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out successfully', 'info')
    return redirect(url_for('login'))

@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    user = User.query.get(session['user_id'])
    
    if user.role == 'student':
        return redirect(url_for('student_dashboard'))
    elif user.role == 'parent':
        return redirect(url_for('parent_dashboard'))
    elif user.role in ['security', 'reception']:
        return redirect(url_for('staff_dashboard'))
    elif user.role in ['counsellor', 'admin_coordinator', 'academic_coordinator']:
        return redirect(url_for('coordinator_dashboard'))
    elif user.role in ['principal', 'director']:
        return redirect(url_for('management_dashboard'))
    elif user.role == 'mentor':
        return redirect(url_for('mentor_dashboard'))
    elif user.role == 'admin':
        return redirect(url_for('admin_dashboard'))
    else:
        flash('Unknown user role', 'error')
        return redirect(url_for('logout'))

# ==================== ROLE-SPECIFIC DASHBOARDS ====================
@app.route('/')
@login_required
def home():
    return redirect(url_for('dashboard'))

@app.route('/student/dashboard')
@role_required('student')
def student_dashboard():
    user = User.query.get(session['user_id'])
    progress = StudentProgress.query.filter_by(user_id=user.id).first()
    
    if not progress:
        progress = StudentProgress(user_id=user.id, current_class=user.class_level, current_batch=user.goal_exam)
        db.session.add(progress)
        db.session.commit()
    
    performance_summary = progress.get_performance_summary()
    
    return render_template('student/dashboard.html',
                         user=user,
                         progress=progress,
                         performance=performance_summary)

@app.route('/parent/dashboard')
@role_required('parent')
def parent_dashboard():
    user = User.query.get(session['user_id'])
    
    # Get student information
    if user.parent_of_student_id:
        student = User.query.get(user.parent_of_student_id)
        student_progress = StudentProgress.query.filter_by(user_id=student.id).first() if student else None
    else:
        student = None
        student_progress = None
    
    return render_template('parent/dashboard.html',
                         user=user,
                         student=student,
                         student_progress=student_progress)

@app.route('/staff/dashboard')
@role_required(['security', 'reception'])
def staff_dashboard():
    user = User.query.get(session['user_id'])
    
    # Get today's visitor statistics
    today = datetime.now().date()
    today_visitors = Visitor.query.filter(
        db.func.date(Visitor.time_in) == today
    ).count()
    
    pending_visitors = Visitor.query.filter(
        Visitor.status == 'checked_in'
    ).count()
    
    return render_template('staff/dashboard.html',
                         user=user,
                         today_visitors=today_visitors,
                         pending_visitors=pending_visitors)

@app.route('/coordinator/dashboard')
@role_required(['counsellor', 'admin_coordinator', 'academic_coordinator'])
def coordinator_dashboard():
    user = User.query.get(session['user_id'])
    
    # Get pending tasks based on role
    pending_follow_ups = VisitorMeeting.query.filter(
        VisitorMeeting.follow_up_required == True,
        VisitorMeeting.follow_up_completed == False
    ).count()
    
    pending_admissions = AdmissionApplication.query.filter(
        AdmissionApplication.status.in_(['enquiry', 'application_submitted'])
    ).count()
    
    return render_template('coordinator/dashboard.html',
                         user=user,
                         pending_follow_ups=pending_follow_ups,
                         pending_admissions=pending_admissions)

@app.route('/management/dashboard')
@role_required(['principal', 'director'])
def management_dashboard():
    user = User.query.get(session['user_id'])
    
    # Get overall statistics
    total_students = User.query.filter_by(role='student').count()
    total_visitors_today = Visitor.query.filter(
        db.func.date(Visitor.time_in) == datetime.now().date()
    ).count()
    pending_admissions = AdmissionApplication.query.filter(
        AdmissionApplication.status.in_(['enquiry', 'application_submitted'])
    ).count()
    
    return render_template('management/dashboard.html',
                         user=user,
                         total_students=total_students,
                         total_visitors_today=total_visitors_today,
                         pending_admissions=pending_admissions)

@app.route('/mentor/dashboard')
@role_required('mentor')
def mentor_dashboard():
    user = User.query.get(session['user_id'])
    
    # Get students in mentor's specialization
    students = User.query.filter(
        User.role == 'student',
        User.goal_exam.contains(user.specialization) if user.specialization else True
    ).limit(10).all()
    
    return render_template('mentor/dashboard.html',
                         user=user,
                         students=students)

@app.route('/admin/dashboard')
@role_required('admin')
def admin_dashboard():
    user = User.query.get(session['user_id'])
    
    # System statistics
    total_users = User.query.count()
    total_students = User.query.filter_by(role='student').count()
    total_staff = User.query.filter(User.role.notin_(['student', 'parent'])).count()
    total_visitors = Visitor.query.count()
    
    return render_template('admin/dashboard.html',
                         user=user,
                         total_users=total_users,
                         total_students=total_students,
                         total_staff=total_staff,
                         total_visitors=total_visitors)

# ==================== API ENDPOINTS ====================
@app.route('/api/student/progress')
@login_required
def api_student_progress():
    if session.get('user_role') not in ['student', 'parent']:
        return jsonify({'error': 'Access denied'}), 403
    
    user = User.query.get(session['user_id'])
    
    # For parents, get their student's progress
    if user.role == 'parent' and user.parent_of_student_id:
        progress = StudentProgress.query.filter_by(user_id=user.parent_of_student_id).first()
    else:
        progress = StudentProgress.query.filter_by(user_id=user.id).first()
    
    if not progress:
        return jsonify({'error': 'Progress not found'}), 404
    
    return jsonify(progress.get_performance_summary())

# Create tables and sample users
with app.app_context():
    db.create_all()
    try:
        create_sample_users()
        print("Database initialized successfully")
    except Exception as e:
        print(f"Database already initialized: {e}")

if __name__ == '__main__':
    print("=" * 80)
    print("🏫 TACHYON INSTITUTE MANAGEMENT SYSTEM")
    print("=" * 80)
    print("Starting on http://localhost:3000")
    print("\nLogin Credentials:")
    print("🔒 Security: security1/security123")
    print("📞 Reception: reception1/reception123")
    print("👨‍💼 Admin Coordinator: admin_coord1/admin123")
    print("🎓 Academic Coordinator: academic_coord1/academic123")
    print("👩‍🏫 Principal: principal/principal123")
    print("👨‍💼 Director: director/director123")
    print("👨‍🎓 Students: rahul2025/rahul2025123, priya2025/priya2025123")
    print("👨‍👩‍👧‍👦 Parents: p_rahul2025/p_rahul2025123, p_priya2025/p_priya2025123")
    print("👩‍🏫 Mentors: mentor_physics/mentor123, mentor_chemistry/mentor123")
    print("⚙️ Admin: admin/admin123")
    print("=" * 80)
    
    app.run(host='0.0.0.0', port=3000, debug=False)