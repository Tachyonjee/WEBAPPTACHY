import os
import logging
from flask import Flask, render_template, request, redirect, url_for, session
from flask_migrate import Migrate
from werkzeug.middleware.proxy_fix import ProxyFix

from config import Config
from extensions import db, jwt, migrate

# Configure logging
logging.basicConfig(level=logging.DEBUG)

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-change-in-production")
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
    
    # Initialize extensions
    db.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)
    
    # Import models to ensure they're registered
    from models import (
        user, student, batch, mentor_assignment, question, attempt,
        doubt, performance, bookmark, practice_session, syllabus,
        syllabus_progress, lecture, practice_recommendation,
        gamification, llm_logs, embedding
    )
    
    # Register blueprints
    from controllers.auth import auth_bp
    from controllers.students import students_bp
    from controllers.questions import questions_bp
    from controllers.admin_api import admin_api_bp
    from controllers.uploads import uploads_bp
    from controllers.syllabus import syllabus_bp
    from controllers.lectures import lectures_bp
    from controllers.mentor import mentor_bp
    from controllers.operator import operator_bp 
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(students_bp, url_prefix='/api/students')
    app.register_blueprint(questions_bp, url_prefix='/api/questions')
    app.register_blueprint(admin_api_bp, url_prefix='/api/admin')
    app.register_blueprint(uploads_bp, url_prefix='/api/uploads')
    app.register_blueprint(syllabus_bp, url_prefix='/api/syllabus')
    app.register_blueprint(lectures_bp, url_prefix='/api/lectures')
    app.register_blueprint(mentor_bp, url_prefix='/api/mentor')
    app.register_blueprint(operator_bp, url_prefix='/api/operator')
    
    # Main routes
    @app.route('/')
    def index():
        return redirect(url_for('auth.login'))
    
    @app.route('/student')
    def student_home():
        return render_template('student/home.html')
    
    @app.route('/student/practice')
    def student_practice():
        return render_template('student/practice.html')
    
    @app.route('/student/review')
    def student_review():
        return render_template('student/review.html')
    
    @app.route('/student/progress')
    def student_progress():
        return render_template('student/progress.html')
    
    @app.route('/student/bookmarks')
    def student_bookmarks():
        return render_template('student/bookmarks.html')
    
    @app.route('/student/doubts')
    def student_doubts():
        return render_template('student/doubts.html')
    
    @app.route('/student/lectures')
    def student_lectures():
        return render_template('student/lectures.html')
    
    @app.route('/operator')
    def operator_home():
        return render_template('operator/add_question.html')
    
    @app.route('/operator/questions/add')
    def operator_add_question():
        return render_template('operator/add_question.html')
    
    @app.route('/operator/questions/bulk')
    def operator_bulk_upload():
        return render_template('operator/bulk_upload.html')
    
    @app.route('/operator/questions/bank')
    def operator_question_bank():
        return render_template('operator/bank.html')
    
    @app.route('/operator/qc')
    def operator_qc():
        return render_template('operator/qc.html')
    
    @app.route('/operator/lectures')
    def operator_lectures():
        return render_template('operator/lectures.html')
    
    @app.route('/mentor/insights')
    def mentor_insights():
        return render_template('mentor/insights.html')
    
    @app.route('/mentor/students')
    def mentor_students():
        return render_template('mentor/students.html')
    
    @app.route('/admin')
    def admin_overview():
        return render_template('admin_html/overview.html')
    
    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('errors/500.html'), 500
    
    # Create tables
    with app.app_context():
        db.create_all()
    
    return app

app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
