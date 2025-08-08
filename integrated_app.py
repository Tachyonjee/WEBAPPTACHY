#!/usr/bin/env python3
"""
Integrated Coaching App with Authentication
"""

import os
from flask import Flask, render_template, jsonify, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.middleware.proxy_fix import ProxyFix
from functools import wraps
import logging
from datetime import datetime
import random

# Configure logging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

# Initialize Flask app
app = Flask(__name__, static_folder='app/static', template_folder='templates')
app.secret_key = os.environ.get("SESSION_SECRET", "demo-secret-key")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Database configuration
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    'pool_pre_ping': True,
    "pool_recycle": 300,
}

db = SQLAlchemy(app, model_class=Base)

# Import extensions and models
from extensions import db, init_extensions

# Import all models
from models.user import User
from models.student import StudentProgress
from models.visitor import Visitor, VisitorMeeting
from models.admission import AdmissionApplication, AdmissionDocument, AssessmentResult
from models.academic import (Class, ClassMaterial, DailyPracticeProblem, DPPQuestion, 
                           DPPAttempt, DPPAnswerSubmission, Test, TestQuestion, 
                           TestAttempt, TestAnswerSubmission)

# ==================== AUTHENTICATION ====================
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def role_required(required_role):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                return redirect(url_for('login'))
            
            user = User.query.get(session['user_id'])
            if not user or user.role != required_role:
                flash('Access denied', 'error')
                return redirect(url_for('dashboard'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# ==================== SAMPLE DATA CREATION ====================
def create_sample_users():
    sample_users = [
        {'username': 'student1', 'password': 'student123', 'role': 'student', 'full_name': 'Rahul Sharma', 'email': 'rahul@example.com', 'goal_exam': 'JEE', 'batch_name': 'JEE 2024-A'},
        {'username': 'student2', 'password': 'student123', 'role': 'student', 'full_name': 'Priya Patel', 'email': 'priya@example.com', 'goal_exam': 'NEET', 'batch_name': 'NEET 2024-B'},
        {'username': 'student3', 'password': 'student123', 'role': 'student', 'full_name': 'Arjun Singh', 'email': 'arjun@example.com', 'goal_exam': 'JEE', 'batch_name': 'JEE 2024-C'},
        {'username': 'mentor1', 'password': 'mentor123', 'role': 'mentor', 'full_name': 'Dr. Amit Kumar', 'email': 'amit@example.com', 'specialization': 'Mathematics', 'department': 'Faculty'},
        {'username': 'mentor2', 'password': 'mentor123', 'role': 'mentor', 'full_name': 'Dr. Sneha Gupta', 'email': 'sneha@example.com', 'specialization': 'Physics', 'department': 'Faculty'},
        {'username': 'mentor3', 'password': 'mentor123', 'role': 'mentor', 'full_name': 'Prof. Rajesh Verma', 'email': 'rajesh@example.com', 'specialization': 'Chemistry', 'department': 'Faculty'},
        {'username': 'operator1', 'password': 'operator123', 'role': 'operator', 'full_name': 'Vikash Yadav', 'email': 'vikash@example.com', 'department': 'Content Team'},
        {'username': 'operator2', 'password': 'operator123', 'role': 'operator', 'full_name': 'Pooja Sharma', 'email': 'pooja@example.com', 'department': 'QC Team'},
        {'username': 'admin', 'password': 'admin123', 'role': 'admin', 'full_name': 'System Administrator', 'email': 'admin@example.com', 'department': 'IT'}
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
            user.specialization = user_data.get('specialization')
            user.department = user_data.get('department')
            user.set_password(user_data['password'])
            db.session.add(user)
            db.session.flush()
            
            if user_data['role'] == 'student':
                progress = StudentProgress()
                progress.user_id = user.id
                progress.total_points = 150 + (hash(user_data['username']) % 500)
                progress.current_streak = hash(user_data['username']) % 10
                progress.best_streak = hash(user_data['username']) % 20
                progress.questions_attempted = 50 + (hash(user_data['username']) % 200)
                progress.questions_correct = 30 + (hash(user_data['username']) % 150)
                db.session.add(progress)
    
    db.session.commit()

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
    
    if user and user.role == 'student':
        return redirect(url_for('student_dashboard'))
    elif user and user.role == 'mentor':
        return redirect(url_for('mentor_dashboard'))
    elif user and user.role == 'operator':
        return redirect(url_for('operator_dashboard'))
    elif user and user.role == 'admin':
        return redirect(url_for('admin_dashboard'))
    else:
        flash('Unknown user role', 'error')
        return redirect(url_for('logout'))

# ==================== STUDENT ROUTES ====================
@app.route('/')
@login_required
def home():
    return redirect(url_for('dashboard'))

@app.route('/student/dashboard')
@role_required('student')
def student_dashboard():
    user = User.query.get(session['user_id'])
    if not user:
        return redirect(url_for('logout'))
        
    progress = StudentProgress.query.filter_by(user_id=user.id).first()
    
    if not progress:
        progress = StudentProgress()
        progress.user_id = user.id
        db.session.add(progress)
        db.session.commit()
    
    # Create demo data for the template
    student_data = {
        'name': user.full_name,
        'goal_exam': user.goal_exam,
        'batch': user.batch_name
    }
    
    streak = {
        'current_streak': progress.current_streak,
        'best_streak': progress.best_streak
    }
    
    points = {
        'points_total': progress.total_points,
        'points_today': random.randint(10, 50)
    }
    
    today_attempts = max(1, progress.questions_attempted // 7) if progress.questions_attempted > 0 else random.randint(5, 15)
    today_correct = max(1, progress.questions_correct // 7) if progress.questions_correct > 0 else random.randint(3, 12)
    
    return render_template('student/home.html',
                         student=student_data, 
                         streak=streak,
                         points=points,
                         today_attempts=today_attempts,
                         today_correct=today_correct,
                         week_attempts=progress.questions_attempted + random.randint(20, 50),
                         pending_doubts=random.randint(0, 5), 
                         recent_badges=None)

@app.route('/practice')
@role_required('student')
def practice():
    # Dummy syllabus data for demo
    JEE_SYLLABUS = {
        "Mathematics": {"Algebra": [], "Geometry": [], "Calculus": []},
        "Physics": {"Mechanics": [], "Thermodynamics": [], "Optics": []},
        "Chemistry": {"Organic": [], "Inorganic": [], "Physical": []}
    }
    return render_template('student/practice_new.html', 
                         subjects=list(JEE_SYLLABUS.keys()),
                         syllabus=JEE_SYLLABUS)

@app.route('/progress')
@role_required('student')
def progress():
    user = User.query.get(session['user_id'])
    progress = StudentProgress.query.filter_by(user_id=user.id).first()
    
    student_data = {
        'name': user.full_name,
        'goal_exam': user.goal_exam
    }
    
    return render_template('student/progress.html', 
                         student=student_data, 
                         weekly_data={}, 
                         subject_performance={},
                         recent_sessions=[],
                         total_accuracy=75.5)

@app.route('/review')
@role_required('student')
def review():
    return render_template('student/review.html')

@app.route('/bookmarks')
@role_required('student')
def bookmarks():
    return render_template('student/bookmarks.html')

@app.route('/lectures')
@role_required('student')
def lectures():
    return render_template('student/lectures.html')

@app.route('/doubts')
@role_required('student')
def doubts():
    return render_template('student/doubts.html')

# ==================== OTHER ROLE DASHBOARDS ====================
@app.route('/mentor/dashboard')
@role_required('mentor')
def mentor_dashboard():
    user = User.query.get(session['user_id'])
    students = User.query.filter_by(role='student').limit(5).all()
    return render_template('mentor/mentor_dashboard.html', user=user, students=students)

@app.route('/operator/dashboard')
@role_required('operator')
def operator_dashboard():
    user = User.query.get(session['user_id'])
    total_questions = 240
    pending_qc = 12
    total_students = User.query.filter_by(role='student').count()
    
    return render_template('operator/operator_dashboard.html', 
                         user=user, 
                         total_questions=total_questions,
                         pending_qc=pending_qc,
                         total_students=total_students)

@app.route('/admin/dashboard')
@role_required('admin')
def admin_dashboard():
    user = User.query.get(session['user_id'])
    total_users = User.query.count()
    total_students = User.query.filter_by(role='student').count()
    total_mentors = User.query.filter_by(role='mentor').count()
    total_operators = User.query.filter_by(role='operator').count()
    
    return render_template('admin/admin_dashboard.html',
                         user=user,
                         total_users=total_users,
                         total_students=total_students,
                         total_mentors=total_mentors,
                         total_operators=total_operators)

# ==================== API ROUTES ====================
@app.route('/api/students/profile')
@login_required
def api_student_profile():
    user = User.query.get(session['user_id'])
    if not user:
        return jsonify({'error': 'User not found'}), 404
        
    progress = StudentProgress.query.filter_by(user_id=user.id).first()
    
    return jsonify({
        'id': user.id,
        'name': user.full_name,
        'email': user.email,
        'goal_exam': user.goal_exam,
        'batch': user.batch_name,
        'points': progress.total_points if progress else 0,
        'streak': progress.current_streak if progress else 0
    })

@app.route('/api/students/doubts')
@login_required
def api_student_doubts():
    return jsonify([])

# Create tables and sample users
with app.app_context():
    db.create_all()
    try:
        create_sample_users()
        print("Database initialized successfully")
    except Exception as e:
        print(f"Database already initialized: {e}")

if __name__ == '__main__':
    print("=" * 60)
    print("🎓 COACHING APP WITH AUTHENTICATION")
    print("=" * 60)
    print("Starting on http://localhost:3000")
    print("\nLogin Credentials:")
    print("Students: student1/student123, student2/student123, student3/student123")
    print("Mentors: mentor1/mentor123, mentor2/mentor123, mentor3/mentor123") 
    print("Operators: operator1/operator123, operator2/operator123")
    print("Admin: admin/admin123")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=3000, debug=False)