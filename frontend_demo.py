#!/usr/bin/env python3
"""
Frontend Demo Server for Coaching App
Minimal Flask server to showcase frontend functionality
"""

from flask import Flask, render_template, jsonify, session, request, send_from_directory
import json
import random
import os

app = Flask(__name__, 
            template_folder='templates',
            static_folder='app/static')
app.secret_key = 'demo-secret-key-for-frontend-testing'

# Demo data
DEMO_STUDENT = {
    "id": 1,
    "name": "Demo Student",
    "email": "demo@example.com",
    "goal_exam": "JEE",
    "batch": "Demo Batch 2024",
    "streak": {"current_streak": 7, "best_streak": 15},
    "points": {"points_total": 1250, "points_today": 45},
    "today_stats": {"attempts": 12, "correct": 9},
    "week_stats": {"attempts": 68, "correct": 51}
}

DEMO_QUESTIONS = [
    {
        "id": 1,
        "question_text": "What is the derivative of sin(x)?",
        "options": {"A": "cos(x)", "B": "-cos(x)", "C": "sin(x)", "D": "-sin(x)"},
        "correct_answer": "A",
        "subject": "Mathematics",
        "topic": "Calculus",
        "difficulty": 1,
        "hint": "Basic trigonometric derivative",
        "solution": "The derivative of sin(x) is cos(x)"
    },
    {
        "id": 2,
        "question_text": "Which is NOT a greenhouse gas?",
        "options": {"A": "CO₂", "B": "CH₄", "C": "O₂", "D": "N₂O"},
        "correct_answer": "C",
        "subject": "Physics",
        "topic": "Environmental Physics",
        "difficulty": 2,
        "hint": "Think about heat absorption",
        "solution": "Oxygen doesn't absorb infrared radiation significantly"
    }
]

SUBJECTS = ["Mathematics", "Physics", "Chemistry", "Biology"]

@app.before_request
def setup_session():
    if not session.get('user_id'):
        session.update({
            'user_id': 1,
            'user_role': 'student',
            'user_name': 'Demo Student',
            'user_email': 'demo@example.com'
        })

@app.route('/')
def home():
    return render_template('student/home.html',
                         student=DEMO_STUDENT,
                         streak=DEMO_STUDENT['streak'],
                         points=DEMO_STUDENT['points'],
                         today_attempts=DEMO_STUDENT['today_stats']['attempts'],
                         today_correct=DEMO_STUDENT['today_stats']['correct'],
                         week_attempts=DEMO_STUDENT['week_stats']['attempts'],
                         pending_doubts=2,
                         recent_badges=None)

@app.route('/auth/login')
def login():
    return render_template('auth/login.html')

@app.route('/student')
def student_home():
    return home()

@app.route('/practice')
@app.route('/student/practice')
def practice():
    return render_template('student/practice.html', subjects=SUBJECTS)

# API routes
@app.route('/api/test')
def api_test():
    return jsonify({'status': 'working', 'message': 'Frontend demo API functional'})

@app.route('/api/students/profile')
def api_profile():
    return jsonify(DEMO_STUDENT)

@app.route('/api/questions/subjects')
def api_subjects():
    return jsonify({'subjects': SUBJECTS})

@app.route('/api/questions/topics')
def api_topics():
    topics = ["Calculus", "Algebra", "Mechanics", "Optics", "Organic Chemistry", "Cell Biology"]
    return jsonify({'topics': topics})

@app.route('/api/students/practice/start', methods=['POST'])
def api_start_practice():
    return jsonify({'session_id': 'demo-123', 'message': 'Session started'})

@app.route('/api/students/practice/<session_id>/next')
def api_next_question(session_id):
    question = random.choice(DEMO_QUESTIONS)
    return jsonify({'question': question})

@app.route('/api/students/practice/<session_id>/attempt', methods=['POST'])
def api_submit_answer(session_id):
    data = request.get_json()
    question_id = data.get('question_id', 1)
    chosen_answer = data.get('chosen_answer')
    
    question = next((q for q in DEMO_QUESTIONS if q['id'] == question_id), DEMO_QUESTIONS[0])
    is_correct = chosen_answer == question['correct_answer']
    
    return jsonify({
        'is_correct': is_correct,
        'correct_answer': question['correct_answer'],
        'solution': question['solution'] if not is_correct else None
    })

@app.route('/api/students/practice/<session_id>/end', methods=['POST'])
def api_end_session(session_id):
    return jsonify({
        'stats': {
            'total_questions': 5,
            'correct_answers': 4,
            'accuracy': 80.0,
            'time_spent': 300
        }
    })

@app.route('/api/students/bookmarks/<question_id>', methods=['POST'])
def api_bookmark(question_id):
    return jsonify({'bookmarked': random.choice([True, False])})

@app.route('/api/students/doubts', methods=['GET', 'POST'])
def api_doubts():
    if request.method == 'POST':
        return jsonify({'message': 'Doubt submitted', 'id': 123})
    return jsonify({'doubts': []})

@app.route('/api/auth/send-otp', methods=['POST'])
def api_send_otp():
    return jsonify({'message': 'OTP sent successfully'})

@app.route('/api/auth/verify-otp', methods=['POST'])
def api_verify_otp():
    return jsonify({
        'access_token': 'demo-token',
        'refresh_token': 'demo-refresh',
        'user': {'id': 1, 'name': 'Demo Student', 'role': 'student'}
    })

if __name__ == '__main__':
    print("🎓 Coaching App Frontend Demo")
    print("📱 Features: PWA, Interactive Practice, Charts, Gamification")
    print("🚀 Starting server on http://localhost:5000")
    
    app.run(host='0.0.0.0', port=5000, debug=True)