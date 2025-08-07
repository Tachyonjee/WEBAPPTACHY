#!/usr/bin/env python3
"""
Quick demo launcher for the coaching app frontend
"""
import os
import sys
from flask import Flask, render_template, jsonify, session, request, redirect

# Simple demo app
app = Flask(__name__, template_folder='templates', static_folder='app/static')
app.secret_key = 'demo-key-123'

# Demo data
DEMO_DATA = {
    "id": 1, "name": "Demo Student", "email": "demo@example.com",
    "streak": {"current_streak": 7, "best_streak": 15}, 
    "points": {"points_total": 1250, "points_today": 45},
    "today_stats": {"attempts": 12, "correct": 9},
    "week_stats": {"attempts": 68, "correct": 51}
}

# Operator demo data
OPERATOR_DATA = {
    "name": "Demo Operator", "role": "operator",
    "total_questions": 250, "pending_qc": 12,
    "active_students": 45, "recent_uploads": 3
}

@app.before_request
def setup():
    # Check if role switch is requested
    role = request.args.get('role', session.get('user_role', 'student'))
    
    if role == 'operator':
        session.update({
            'user_id': 2, 'user_role': 'operator',
            'user_name': 'Demo Operator', 'user_email': 'operator@example.com'
        })
    else:
        session.update({
            'user_id': 1, 'user_role': 'student', 
            'user_name': 'Demo Student', 'user_email': 'demo@example.com'
        })

@app.route('/')
def home():
    # Add goal_exam and batch to demo data for template
    student_data = DEMO_DATA.copy()
    student_data['goal_exam'] = 'JEE'
    student_data['batch'] = 'Demo Batch 2024'
    
    return render_template('student/home.html',
                         student=student_data, streak=DEMO_DATA['streak'],
                         points=DEMO_DATA['points'],
                         today_attempts=DEMO_DATA['today_stats']['attempts'],
                         today_correct=DEMO_DATA['today_stats']['correct'],
                         week_attempts=DEMO_DATA['week_stats']['attempts'],
                         pending_doubts=2, recent_badges=None)

@app.route('/practice')
def practice():
    return render_template('student/practice.html', subjects=["Mathematics", "Physics", "Chemistry", "Biology"])

@app.route('/progress')
def progress():
    return render_template('student/progress.html', 
                         student=DEMO_DATA, 
                         weekly_data={}, 
                         subject_performance={},
                         recent_sessions=[],
                         total_accuracy=75.5)

@app.route('/review')
def review():
    return render_template('student/review.html', subjects=["Mathematics", "Physics", "Chemistry"])

@app.route('/submit_attempt', methods=['POST'])
def submit_attempt():
    return jsonify({'status': 'success', 'message': 'Answer submitted'})

@app.route('/practice_question/<int:session_id>')
def practice_question(session_id):
    return render_template('student/practice_question.html', session_id=session_id)

@app.route('/auth/login')
def login():
    return render_template('auth/login.html')

@app.route('/api/test')
def api_test():
    return jsonify({'status': 'working', 'app': 'coaching-demo'})

# === OPERATOR INTERFACE ROUTES ===
@app.route('/operator')
@app.route('/operator/dashboard')
def operator_dashboard():
    subjects_stats = {
        'Mathematics': 75, 'Physics': 65, 'Chemistry': 58, 'Biology': 42
    }
    return render_template('operator/dashboard.html', 
                         total_questions=250, pending_qc=12, 
                         active_students=45, recent_uploads=3,
                         subjects_stats=subjects_stats, 
                         recent_activities=[], pending_doubts=8)

@app.route('/operator/bank')
def question_bank():
    return render_template('operator/bank.html', 
                         questions=[], subjects=["Mathematics", "Physics", "Chemistry", "Biology"])

@app.route('/operator/add_question')
def add_question():
    return render_template('operator/add_question.html', 
                         subjects=["Mathematics", "Physics", "Chemistry", "Biology"])

@app.route('/operator/bulk_upload')
def bulk_upload():
    return render_template('operator/bulk_upload.html')

@app.route('/operator/qc')
def quality_control():
    return render_template('operator/qc.html', pending_questions=[])

@app.route('/operator/edit_question/<int:question_id>')
def edit_question(question_id):
    return render_template('operator/edit_question.html', question_id=question_id)

# === ADDITIONAL STUDENT ROUTES ===
@app.route('/doubts')
def doubts():
    return render_template('student/doubts.html', doubts=[])

@app.route('/bookmarks')
def bookmarks():
    return render_template('student/bookmarks.html', bookmarks=[])

@app.route('/lectures')
def lectures():
    return render_template('student/lectures.html', lectures=[])

# === ROLE SWITCHING FOR DEMO ===
@app.route('/switch_role/<role>')
def switch_role(role):
    session['user_role'] = role
    if role == 'operator':
        return redirect('/operator')
    else:
        return redirect('/')

# === API ENDPOINTS FOR FRONTEND ===
@app.route('/api/students/profile')
def api_student_profile():
    return jsonify(DEMO_DATA)

@app.route('/api/students/doubts')
def api_student_doubts():
    return jsonify({"doubts": [], "total": 0})

@app.route('/api/practice/start', methods=['POST'])
def api_start_practice():
    data = request.get_json() or {}
    return jsonify({
        "session_id": 123, 
        "status": "started",
        "total_questions": 10,
        "subject": data.get('subject', 'Mathematics')
    })

@app.route('/api/practice/question/<int:session_id>')
def api_get_question(session_id):
    return jsonify({
        "id": 1,
        "question_text": "What is the derivative of x²?",
        "options": ["2x", "x", "2", "x²"],
        "correct_answer": "2x",
        "subject": "Mathematics",
        "topic": "Calculus",
        "difficulty": "Easy"
    })

if __name__ == '__main__':
    print("Starting Coaching App Demo on port 3000...")
    app.run(host='0.0.0.0', port=3000, debug=False)