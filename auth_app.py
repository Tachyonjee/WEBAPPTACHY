#!/usr/bin/env python3
"""
Coaching App with Role-Based Authentication System
"""
import os
import logging
import hashlib
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.middleware.proxy_fix import ProxyFix

# Configure logging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

# Initialize Flask app
app = Flask(__name__, template_folder='auth_templates', static_folder='app/static')
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-coaching-app")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Database configuration
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    'pool_pre_ping': True,
    "pool_recycle": 300,
}

db = SQLAlchemy(app, model_class=Base)

# ==================== MODELS ====================
class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # student, mentor, operator, admin
    full_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(15))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    last_login = db.Column(db.DateTime)
    
    # Additional role-specific data
    goal_exam = db.Column(db.String(20))  # For students: JEE, NEET
    batch_name = db.Column(db.String(50))  # For students
    specialization = db.Column(db.String(50))  # For mentors: Math, Physics, etc.
    department = db.Column(db.String(50))  # For operators/admin
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def update_last_login(self):
        self.last_login = datetime.now()
        db.session.commit()

class StudentProgress(db.Model):
    __tablename__ = 'student_progress'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    total_points = db.Column(db.Integer, default=0)
    current_streak = db.Column(db.Integer, default=0)
    best_streak = db.Column(db.Integer, default=0)
    questions_attempted = db.Column(db.Integer, default=0)
    questions_correct = db.Column(db.Integer, default=0)
    last_activity = db.Column(db.DateTime, default=datetime.now)
    
    user = db.relationship('User', backref='progress')

# ==================== HELPER FUNCTIONS ====================
def create_sample_users():
    """Create sample users for all roles"""
    sample_users = [
        # Students
        {
            'username': 'student1', 'password': 'student123', 'role': 'student',
            'email': 'student1@coaching.com', 'full_name': 'Rahul Sharma',
            'phone': '9876543210', 'goal_exam': 'JEE', 'batch_name': 'JEE Mains 2025'
        },
        {
            'username': 'student2', 'password': 'student123', 'role': 'student', 
            'email': 'student2@coaching.com', 'full_name': 'Priya Patel',
            'phone': '9876543211', 'goal_exam': 'NEET', 'batch_name': 'NEET 2025'
        },
        {
            'username': 'student3', 'password': 'student123', 'role': 'student',
            'email': 'student3@coaching.com', 'full_name': 'Arjun Singh', 
            'phone': '9876543212', 'goal_exam': 'JEE', 'batch_name': 'JEE Advanced 2025'
        },
        
        # Mentors
        {
            'username': 'mentor1', 'password': 'mentor123', 'role': 'mentor',
            'email': 'mentor1@coaching.com', 'full_name': 'Dr. Amit Kumar',
            'phone': '9876543220', 'specialization': 'Mathematics', 'department': 'Academic'
        },
        {
            'username': 'mentor2', 'password': 'mentor123', 'role': 'mentor',
            'email': 'mentor2@coaching.com', 'full_name': 'Dr. Kavita Rao',
            'phone': '9876543221', 'specialization': 'Physics', 'department': 'Academic'
        },
        {
            'username': 'mentor3', 'password': 'mentor123', 'role': 'mentor',
            'email': 'mentor3@coaching.com', 'full_name': 'Dr. Suresh Gupta',
            'phone': '9876543222', 'specialization': 'Chemistry', 'department': 'Academic'
        },
        
        # Operators
        {
            'username': 'operator1', 'password': 'operator123', 'role': 'operator',
            'email': 'operator1@coaching.com', 'full_name': 'Neha Agarwal',
            'phone': '9876543230', 'department': 'Content Management'
        },
        {
            'username': 'operator2', 'password': 'operator123', 'role': 'operator',
            'email': 'operator2@coaching.com', 'full_name': 'Vikash Jain',
            'phone': '9876543231', 'department': 'Quality Control'
        },
        
        # Admin
        {
            'username': 'admin', 'password': 'admin123', 'role': 'admin',
            'email': 'admin@coaching.com', 'full_name': 'Director Admin',
            'phone': '9876543240', 'department': 'Administration'
        }
    ]
    
    for user_data in sample_users:
        # Check if user already exists
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
            db.session.flush()  # Flush to get the user.id
            
            # Create progress record for students
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
    print("Sample users created successfully!")

def login_required(f):
    """Decorator to require login for routes"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def role_required(required_role):
    """Decorator to require specific role"""
    def decorator(f):
        from functools import wraps
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                return redirect(url_for('login'))
            
            user = User.query.get(session['user_id'])
            if not user or user.role != required_role:
                flash('Access denied. Insufficient permissions.', 'error')
                return redirect(url_for('dashboard'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# ==================== ROUTES ====================

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password) and user.is_active:
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role
            session['full_name'] = user.full_name
            
            user.update_last_login()
            flash(f'Welcome back, {user.full_name}!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out successfully', 'info')
    return redirect(url_for('login'))

@app.route('/dashboard')
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
    
    return render_template('student_dashboard.html', user=user, progress=progress)

@app.route('/student/practice')
@role_required('student')
def student_practice():
    return render_template('student_practice.html')

@app.route('/student/progress')
@role_required('student')
def student_progress():
    user = User.query.get(session['user_id'])
    if not user:
        return redirect(url_for('logout'))
        
    progress = StudentProgress.query.filter_by(user_id=user.id).first()
    return render_template('student_progress.html', user=user, progress=progress)

@app.route('/student/doubts')
@role_required('student')
def student_doubts():
    return render_template('student_doubts.html')

# ==================== MENTOR ROUTES ====================
@app.route('/mentor/dashboard')
@role_required('mentor')
def mentor_dashboard():
    user = User.query.get(session['user_id'])
    # Get students assigned to this mentor
    students = User.query.filter_by(role='student').limit(10).all()
    return render_template('mentor_dashboard.html', user=user, students=students)

@app.route('/mentor/students')
@role_required('mentor')
def mentor_students():
    students = User.query.filter_by(role='student').all()
    return render_template('mentor_students.html', students=students)

@app.route('/mentor/analytics')
@role_required('mentor')
def mentor_analytics():
    return render_template('mentor_analytics.html')

# ==================== OPERATOR ROUTES ====================
@app.route('/operator/dashboard')
@role_required('operator')
def operator_dashboard():
    user = User.query.get(session['user_id'])
    
    # Get some stats
    total_students = User.query.filter_by(role='student').count()
    total_questions = 250  # Placeholder
    pending_qc = 12       # Placeholder
    
    return render_template('operator_dashboard.html', 
                         user=user, 
                         total_students=total_students,
                         total_questions=total_questions,
                         pending_qc=pending_qc)

@app.route('/operator/questions')
@role_required('operator')
def operator_questions():
    return render_template('operator_questions.html')

@app.route('/operator/uploads')
@role_required('operator')
def operator_uploads():
    return render_template('operator_uploads.html')

# ==================== ADMIN ROUTES ====================
@app.route('/admin/dashboard')
@role_required('admin')
def admin_dashboard():
    user = User.query.get(session['user_id'])
    
    # Get platform statistics
    total_users = User.query.count()
    total_students = User.query.filter_by(role='student').count()
    total_mentors = User.query.filter_by(role='mentor').count()
    total_operators = User.query.filter_by(role='operator').count()
    
    return render_template('admin_dashboard.html', 
                         user=user,
                         total_users=total_users,
                         total_students=total_students, 
                         total_mentors=total_mentors,
                         total_operators=total_operators)

@app.route('/admin/users')
@role_required('admin')
def admin_users():
    users = User.query.all()
    return render_template('admin_users.html', users=users)

@app.route('/admin/reports')
@role_required('admin')
def admin_reports():
    return render_template('admin_reports.html')

# ==================== API ROUTES ====================
@app.route('/api/profile')
@login_required
def api_profile():
    user = User.query.get(session['user_id'])
    if user:
        return jsonify({
            'id': user.id,
            'username': user.username,
            'role': user.role,
            'full_name': user.full_name,
            'email': user.email
        })
    return jsonify({'error': 'User not found'}), 404

# ==================== ERROR HANDLERS ====================
@app.errorhandler(404)
def not_found_error(error):
    return render_template('error.html', error_code=404, 
                         error_message="Page not found"), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('error.html', error_code=500,
                         error_message="Internal server error"), 500

# ==================== INITIALIZATION ====================
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        create_sample_users()
        print("=== Coaching App Authentication System ===")
        print("Sample Login Credentials:")
        print("Students: student1/student123, student2/student123, student3/student123")
        print("Mentors: mentor1/mentor123, mentor2/mentor123, mentor3/mentor123") 
        print("Operators: operator1/operator123, operator2/operator123")
        print("Admin: admin/admin123")
        print("==========================================")
        app.run(host='0.0.0.0', port=5000, debug=True)