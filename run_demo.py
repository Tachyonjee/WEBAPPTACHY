#!/usr/bin/env python3
"""
Quick demo launcher for the coaching app frontend
"""
import os
import sys
from flask import Flask, render_template, jsonify, session

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

@app.before_request
def setup():
    session.update({
        'user_id': 1, 'user_role': 'student', 
        'user_name': 'Demo Student', 'user_email': 'demo@example.com'
    })

@app.route('/')
def home():
    return render_template('student/home.html',
                         student=DEMO_DATA, streak=DEMO_DATA['streak'],
                         points=DEMO_DATA['points'],
                         today_attempts=DEMO_DATA['today_stats']['attempts'],
                         today_correct=DEMO_DATA['today_stats']['correct'],
                         week_attempts=DEMO_DATA['week_stats']['attempts'],
                         pending_doubts=2, recent_badges=None)

@app.route('/practice')
def practice():
    return render_template('student/practice.html', subjects=["Mathematics", "Physics", "Chemistry", "Biology"])

@app.route('/auth/login')
def login():
    return render_template('auth/login.html')

@app.route('/api/test')
def api_test():
    return jsonify({'status': 'working', 'app': 'coaching-demo'})

if __name__ == '__main__':
    print("Starting Coaching App Demo on port 5000...")
    app.run(host='0.0.0.0', port=5000, debug=False)