"""
Simple Flask app startup for frontend development
"""
import os
from flask import Flask, render_template, request, jsonify, session
from extensions import db
from demo_data import *

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-12345")

# Configure database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Initialize database
db.init_app(app)

# Set up demo session data
@app.before_request
def setup_demo_session():
    if not session.get('user_id'):
        session['user_id'] = 1
        session['user_role'] = 'student'
        session['user_name'] = 'Demo Student'
        session['user_email'] = 'demo@example.com'

# Routes for testing
@app.route('/')
def home():
    demo_data = get_demo_student_profile()
    return render_template('student/home.html', 
                         student=demo_data,
                         streak=demo_data['streak'],
                         points=demo_data['points'],
                         today_attempts=demo_data['today_stats']['attempts'],
                         today_correct=demo_data['today_stats']['correct'],
                         week_attempts=demo_data['week_stats']['attempts'],
                         pending_doubts=2,
                         recent_badges=None)

@app.route('/auth/login')
def login():
    return render_template('auth/login.html')

@app.route('/student')
def student_home():
    return home()

@app.route('/practice')
def practice():
    subjects = get_demo_subjects()
    return render_template('student/practice.html', subjects=subjects)

@app.route('/student/practice')
def student_practice():
    return practice()

# API endpoints for demo
@app.route('/api/test')
def api_test():
    return jsonify({'status': 'working', 'message': 'API is functional'})

@app.route('/api/students/profile')
def api_student_profile():
    return jsonify(get_demo_student_profile())

@app.route('/api/questions/subjects')
def api_subjects():
    return jsonify({'subjects': get_demo_subjects()})

@app.route('/api/questions/topics')
def api_topics():
    subjects = request.args.get('subjects', '').split(',') if request.args.get('subjects') else None
    topics = get_demo_topics(subjects)
    return jsonify({'topics': topics})

@app.route('/api/students/practice/start', methods=['POST'])
def api_start_practice():
    data = request.get_json()
    return jsonify({
        'session_id': 'demo-session-123',
        'message': 'Practice session started successfully'
    })

@app.route('/api/students/practice/<session_id>/next')
def api_next_question(session_id):
    question = get_demo_question()
    return jsonify({'question': question})

@app.route('/api/students/practice/<session_id>/attempt', methods=['POST'])
def api_submit_answer(session_id):
    data = request.get_json()
    question_id = data.get('question_id')
    chosen_answer = data.get('chosen_answer')
    
    question = get_demo_question(question_id)
    if question:
        is_correct = chosen_answer == question['correct_answer']
        return jsonify({
            'is_correct': is_correct,
            'correct_answer': question['correct_answer'],
            'solution': question['solution'] if not is_correct else None
        })
    
    return jsonify({'error': 'Question not found'}), 404

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
def api_toggle_bookmark(question_id):
    # Simulate bookmark toggle
    import random
    bookmarked = random.choice([True, False])
    return jsonify({'bookmarked': bookmarked})

@app.route('/api/students/doubts', methods=['GET', 'POST'])
def api_doubts():
    if request.method == 'POST':
        return jsonify({'message': 'Doubt submitted successfully', 'id': 123})
    else:
        status = request.args.get('status', 'all')
        doubts = [] if status == 'open' else [
            {'id': 1, 'message': 'How to solve this calculus problem?', 'status': 'answered'},
            {'id': 2, 'message': 'Clarification on organic chemistry', 'status': 'pending'}
        ]
        return jsonify({'doubts': doubts})

@app.route('/api/auth/send-otp', methods=['POST'])
def api_send_otp():
    return jsonify({'message': 'OTP sent successfully'})

@app.route('/api/auth/verify-otp', methods=['POST'])
def api_verify_otp():
    return jsonify({
        'access_token': 'demo-access-token',
        'refresh_token': 'demo-refresh-token',
        'user': {
            'id': 1,
            'name': 'Demo Student',
            'email': 'demo@example.com',
            'role': 'student'
        }
    })

# Static file routes
@app.route('/static/<path:filename>')
def static_files(filename):
    return app.send_static_file(filename)

if __name__ == '__main__':
    with app.app_context():
        # Create tables if needed
        try:
            db.create_all()
        except:
            pass  # Ignore database errors for demo
    
    print("🎓 Starting Coaching App Demo Server...")
    print("📱 PWA features enabled")
    print("🧠 Interactive practice mode ready") 
    print("📊 Charts and analytics loaded")
    print("🔄 Auto-refresh functionality active")
    
    app.run(host='0.0.0.0', port=5000, debug=True)