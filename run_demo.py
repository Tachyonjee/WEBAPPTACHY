#!/usr/bin/env python3
"""
Quick demo launcher for the coaching app frontend with authentication
"""
import subprocess
import sys
import os

def main():
    print("Starting Coaching App with Authentication...")
    print("This will redirect to the integrated app with login functionality.")
    
    # Run the integrated app
    try:
        subprocess.run([sys.executable, 'integrated_app.py'], check=True)
    except KeyboardInterrupt:
        print("\nServer stopped.")
    except Exception as e:
        print(f"Error starting server: {e}")

if __name__ == '__main__':
    main()

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
    return render_template('student/practice_new.html', 
                         subjects=list(JEE_SYLLABUS.keys()),
                         syllabus=JEE_SYLLABUS)

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

# JEE Mains Syllabus Structure
JEE_SYLLABUS = {
    "Mathematics": {
        "Algebra": ["Complex Numbers", "Quadratic Equations", "Sequences and Series", "Permutations and Combinations", "Binomial Theorem", "Mathematical Induction"],
        "Trigonometry": ["Trigonometric Functions", "Inverse Trigonometric Functions", "Heights and Distances", "Trigonometric Equations"],
        "Coordinate Geometry": ["Straight Lines", "Circles", "Parabola", "Ellipse", "Hyperbola", "3D Coordinate Geometry"],
        "Calculus": ["Limits and Continuity", "Differentiation", "Applications of Derivatives", "Integration", "Applications of Integrals", "Differential Equations"],
        "Statistics and Probability": ["Statistics", "Probability", "Conditional Probability"],
        "Vector Algebra": ["Vectors", "Scalar and Vector Products", "Applications of Vectors"]
    },
    "Physics": {
        "Mechanics": ["Kinematics", "Laws of Motion", "Work Energy Power", "Rotational Motion", "Gravitation", "Properties of Matter"],
        "Heat and Thermodynamics": ["Thermal Properties", "Kinetic Theory", "Thermodynamics"],
        "Waves and Oscillations": ["Simple Harmonic Motion", "Wave Motion", "Sound Waves"],
        "Electricity and Magnetism": ["Electrostatics", "Current Electricity", "Magnetic Effects", "Electromagnetic Induction", "AC Circuits"],
        "Optics": ["Ray Optics", "Wave Optics"],
        "Modern Physics": ["Dual Nature of Matter", "Atoms and Nuclei", "Electronic Devices"]
    },
    "Chemistry": {
        "Physical Chemistry": ["Atomic Structure", "Chemical Bonding", "Thermodynamics", "Chemical Equilibrium", "Ionic Equilibrium", "Redox Reactions", "Electrochemistry"],
        "Inorganic Chemistry": ["Periodic Table", "S-Block Elements", "P-Block Elements", "D-Block Elements", "F-Block Elements", "Coordination Compounds"],
        "Organic Chemistry": ["Hydrocarbons", "Haloalkanes", "Alcohols and Ethers", "Aldehydes and Ketones", "Carboxylic Acids", "Amines", "Biomolecules"]
    }
}

# Sample Questions Database
SAMPLE_QUESTIONS = {
    "Mathematics": {
        "Complex Numbers": [
            {
                "id": 1,
                "question": "If z = 3 + 4i, find |z|",
                "options": ["5", "7", "√7", "√25"],
                "correct": "5",
                "explanation": "|z| = √(3² + 4²) = √(9 + 16) = √25 = 5"
            },
            {
                "id": 2,
                "question": "The argument of complex number -1 + i is",
                "options": ["π/4", "3π/4", "-π/4", "π/2"],
                "correct": "3π/4",
                "explanation": "arg(-1 + i) = tan⁻¹(1/-1) + π = -π/4 + π = 3π/4"
            }
        ],
        "Differentiation": [
            {
                "id": 3,
                "question": "What is the derivative of x² + 3x + 2?",
                "options": ["2x + 3", "2x + 2", "x + 3", "2x"],
                "correct": "2x + 3",
                "explanation": "d/dx(x² + 3x + 2) = 2x + 3 + 0 = 2x + 3"
            },
            {
                "id": 4,
                "question": "Find dy/dx if y = sin(2x)",
                "options": ["cos(2x)", "2cos(2x)", "-2sin(2x)", "2sin(2x)"],
                "correct": "2cos(2x)",
                "explanation": "Using chain rule: dy/dx = cos(2x) × 2 = 2cos(2x)"
            }
        ]
    },
    "Physics": {
        "Kinematics": [
            {
                "id": 5,
                "question": "A particle moves with velocity v = 3t² + 2t. Its acceleration at t = 2s is",
                "options": ["14 m/s²", "12 m/s²", "16 m/s²", "10 m/s²"],
                "correct": "14 m/s²",
                "explanation": "a = dv/dt = 6t + 2. At t = 2s, a = 6(2) + 2 = 14 m/s²"
            },
            {
                "id": 6,
                "question": "An object is thrown vertically upward with speed 20 m/s. Maximum height reached is (g = 10 m/s²)",
                "options": ["20 m", "25 m", "30 m", "40 m"],
                "correct": "20 m",
                "explanation": "h = v²/2g = 20²/(2×10) = 400/20 = 20 m"
            }
        ]
    },
    "Chemistry": {
        "Atomic Structure": [
            {
                "id": 7,
                "question": "The maximum number of electrons in d-orbital is",
                "options": ["6", "8", "10", "14"],
                "correct": "10",
                "explanation": "d-orbital has 5 subshells, each can hold 2 electrons, so 5×2 = 10 electrons"
            },
            {
                "id": 8,
                "question": "Which quantum number determines the shape of orbital?",
                "options": ["n", "l", "m", "s"],
                "correct": "l",
                "explanation": "Azimuthal quantum number (l) determines the shape of the orbital"
            }
        ]
    }
}

# === API ENDPOINTS FOR FRONTEND ===
@app.route('/api/students/profile')
def api_student_profile():
    return jsonify(DEMO_DATA)

@app.route('/api/students/doubts')
def api_student_doubts():
    return jsonify({"doubts": [], "total": 0})

@app.route('/api/syllabus/<subject>')
def api_get_syllabus(subject):
    return jsonify(JEE_SYLLABUS.get(subject, {}))

@app.route('/student/api/start-session', methods=['POST'])
@app.route('/api/practice/start', methods=['POST'])
def api_start_practice():
    data = request.get_json() or {}
    subject = data.get('subject', 'Mathematics')
    topic = data.get('topic', list(JEE_SYLLABUS.get(subject, {}).keys())[0] if subject in JEE_SYLLABUS else 'General')
    
    return jsonify({
        "session_id": 123, 
        "status": "started",
        "total_questions": 10,
        "subject": subject,
        "topic": topic,
        "subtopics": JEE_SYLLABUS.get(subject, {}).get(topic, [])
    })

@app.route('/api/practice/question/<int:session_id>')
def api_get_question(session_id):
    # Get a random question from available topics
    all_questions = []
    for subject in SAMPLE_QUESTIONS.values():
        for topic_questions in subject.values():
            all_questions.extend(topic_questions)
    
    if all_questions:
        import random
        question = random.choice(all_questions)
        return jsonify({
            "id": question["id"],
            "question_text": question["question"],
            "options": question["options"],
            "correct_answer": question["correct"],
            "explanation": question["explanation"],
            "subject": "Mathematics",
            "difficulty": "Medium"
        })
    
    return jsonify({
        "id": 1,
        "question_text": "Sample question not available",
        "options": ["A", "B", "C", "D"],
        "correct_answer": "A",
        "explanation": "This is a placeholder",
        "subject": "General",
        "difficulty": "Easy"
    })

@app.route('/api/questions/<subject>/<topic>')
def api_get_topic_questions(subject, topic):
    questions = SAMPLE_QUESTIONS.get(subject, {}).get(topic, [])
    return jsonify({"questions": questions, "total": len(questions)})

if __name__ == '__main__':
    print("Starting Coaching App Demo on port 3000...")
    app.run(host='0.0.0.0', port=3000, debug=False)