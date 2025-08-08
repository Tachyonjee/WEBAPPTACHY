from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey, Float, JSON
from sqlalchemy.orm import relationship
from extensions import db

class Class(db.Model):
    __tablename__ = 'classes'
    
    id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    subject = Column(String(50), nullable=False)
    class_level = Column(String(20), nullable=False)  # Class 11, 12, etc.
    batch_type = Column(String(50), nullable=False)  # JEE, NEET, Foundation
    
    # Scheduling
    scheduled_at = Column(DateTime, nullable=False)
    duration_minutes = Column(Integer, default=60)
    
    # Content
    recording_path = Column(String(255))  # Path to recorded class
    materials = relationship("ClassMaterial", back_populates="class_session", cascade="all, delete-orphan")
    
    # Instructor
    instructor_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    instructor = relationship("User")
    
    # Status
    status = Column(String(20), default='scheduled')  # scheduled, ongoing, completed, cancelled
    
    # Generated DPPs
    dpps = relationship("DailyPracticeProblem", back_populates="class_session", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<Class {self.title}>'

class ClassMaterial(db.Model):
    __tablename__ = 'class_materials'
    
    id = Column(Integer, primary_key=True)
    class_id = Column(Integer, ForeignKey('classes.id'), nullable=False)
    class_session = relationship("Class", back_populates="materials")
    
    title = Column(String(200), nullable=False)
    material_type = Column(String(50), nullable=False)  # pdf, video, image, link
    file_path = Column(String(255))
    external_url = Column(String(500))
    
    uploaded_at = Column(DateTime, default=datetime.now)
    uploaded_by_id = Column(Integer, ForeignKey('users.id'))
    uploaded_by = relationship("User")
    
    def __repr__(self):
        return f'<ClassMaterial {self.title}>'

class DailyPracticeProblem(db.Model):
    __tablename__ = 'daily_practice_problems'
    
    id = Column(Integer, primary_key=True)
    class_id = Column(Integer, ForeignKey('classes.id'))
    class_session = relationship("Class", back_populates="dpps")
    
    title = Column(String(200), nullable=False)
    description = Column(Text)
    subject = Column(String(50), nullable=False)
    difficulty_level = Column(String(20), default='medium')  # easy, medium, hard
    
    # Generation info
    generated_from_llm = Column(Boolean, default=False)
    llm_prompt_used = Column(Text)
    
    # Assignment
    assigned_to_batch = Column(String(50))  # JEE, NEET, Foundation
    assigned_to_class = Column(String(20))  # Class 11, 12
    due_date = Column(DateTime)
    
    # Content
    questions = relationship("DPPQuestion", back_populates="dpp", cascade="all, delete-orphan")
    
    # Tracking
    created_at = Column(DateTime, default=datetime.now)
    created_by_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    created_by = relationship("User")
    
    # Results
    attempts = relationship("DPPAttempt", back_populates="dpp", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<DPP {self.title}>'

class DPPQuestion(db.Model):
    __tablename__ = 'dpp_questions'
    
    id = Column(Integer, primary_key=True)
    dpp_id = Column(Integer, ForeignKey('daily_practice_problems.id'), nullable=False)
    dpp = relationship("DailyPracticeProblem", back_populates="questions")
    
    question_text = Column(Text, nullable=False)
    question_type = Column(String(20), default='mcq')  # mcq, numerical, subjective
    
    # MCQ Options
    option_a = Column(Text)
    option_b = Column(Text)
    option_c = Column(Text)
    option_d = Column(Text)
    correct_option = Column(String(1))  # A, B, C, D
    
    # Numerical Answer
    numerical_answer = Column(Float)
    tolerance = Column(Float, default=0.01)
    
    # Common fields
    explanation = Column(Text)
    marks = Column(Integer, default=1)
    
    def __repr__(self):
        return f'<DPPQuestion {self.id}>'

class DPPAttempt(db.Model):
    __tablename__ = 'dpp_attempts'
    
    id = Column(Integer, primary_key=True)
    dpp_id = Column(Integer, ForeignKey('daily_practice_problems.id'), nullable=False)
    dpp = relationship("DailyPracticeProblem", back_populates="attempts")
    
    student_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    student = relationship("User")
    
    # Attempt details
    started_at = Column(DateTime, default=datetime.now)
    submitted_at = Column(DateTime)
    time_taken_minutes = Column(Integer)
    
    # Results
    total_questions = Column(Integer, nullable=False)
    attempted_questions = Column(Integer, default=0)
    correct_answers = Column(Integer, default=0)
    score = Column(Float, default=0.0)
    percentage = Column(Float, default=0.0)
    
    # Individual answers
    answers = relationship("DPPAnswerSubmission", back_populates="attempt", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<DPPAttempt {self.student.username} - {self.dpp.title}>'

class DPPAnswerSubmission(db.Model):
    __tablename__ = 'dpp_answer_submissions'
    
    id = Column(Integer, primary_key=True)
    attempt_id = Column(Integer, ForeignKey('dpp_attempts.id'), nullable=False)
    attempt = relationship("DPPAttempt", back_populates="answers")
    
    question_id = Column(Integer, ForeignKey('dpp_questions.id'), nullable=False)
    question = relationship("DPPQuestion")
    
    # Student's answer
    selected_option = Column(String(1))  # For MCQ
    numerical_answer = Column(Float)  # For numerical
    text_answer = Column(Text)  # For subjective
    
    # Evaluation
    is_correct = Column(Boolean, default=False)
    marks_awarded = Column(Float, default=0.0)
    
    def __repr__(self):
        return f'<DPPAnswerSubmission Q{self.question_id}>'

class Test(db.Model):
    __tablename__ = 'tests'
    
    id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    
    # Test configuration
    test_type = Column(String(50), nullable=False)  # weekly, monthly, mock, assessment
    subject = Column(String(50))
    class_level = Column(String(20))
    batch_type = Column(String(50))
    
    # Scheduling
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    duration_minutes = Column(Integer, nullable=False)
    
    # Configuration
    shuffle_questions = Column(Boolean, default=True)
    show_results_immediately = Column(Boolean, default=False)
    negative_marking = Column(Boolean, default=False)
    negative_marks_per_question = Column(Float, default=0.25)
    
    # Questions
    questions = relationship("TestQuestion", back_populates="test", cascade="all, delete-orphan")
    
    # Results
    attempts = relationship("TestAttempt", back_populates="test", cascade="all, delete-orphan")
    
    # Tracking
    created_at = Column(DateTime, default=datetime.now)
    created_by_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    created_by = relationship("User")
    
    def __repr__(self):
        return f'<Test {self.title}>'

class TestQuestion(db.Model):
    __tablename__ = 'test_questions'
    
    id = Column(Integer, primary_key=True)
    test_id = Column(Integer, ForeignKey('tests.id'), nullable=False)
    test = relationship("Test", back_populates="questions")
    
    question_text = Column(Text, nullable=False)
    question_type = Column(String(20), default='mcq')
    
    # Options and answers (similar to DPPQuestion)
    option_a = Column(Text)
    option_b = Column(Text)
    option_c = Column(Text)
    option_d = Column(Text)
    correct_option = Column(String(1))
    
    numerical_answer = Column(Float)
    tolerance = Column(Float, default=0.01)
    
    explanation = Column(Text)
    marks = Column(Integer, default=1)
    
    # Question order for shuffling
    question_order = Column(Integer)
    
    def __repr__(self):
        return f'<TestQuestion {self.id}>'

class TestAttempt(db.Model):
    __tablename__ = 'test_attempts'
    
    id = Column(Integer, primary_key=True)
    test_id = Column(Integer, ForeignKey('tests.id'), nullable=False)
    test = relationship("Test", back_populates="attempts")
    
    student_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    student = relationship("User")
    
    # Device and session info
    device_info = Column(JSON)  # Store device details for tablet-based tests
    session_token = Column(String(100))  # Unique session for security
    
    # Attempt timing
    started_at = Column(DateTime, default=datetime.now)
    submitted_at = Column(DateTime)
    time_taken_minutes = Column(Integer)
    
    # Results
    total_questions = Column(Integer, nullable=False)
    attempted_questions = Column(Integer, default=0)
    correct_answers = Column(Integer, default=0)
    wrong_answers = Column(Integer, default=0)
    unattempted = Column(Integer, default=0)
    
    score = Column(Float, default=0.0)
    percentage = Column(Float, default=0.0)
    rank = Column(Integer)
    
    # Individual answers
    answers = relationship("TestAnswerSubmission", back_populates="attempt", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<TestAttempt {self.student.username} - {self.test.title}>'

class TestAnswerSubmission(db.Model):
    __tablename__ = 'test_answer_submissions'
    
    id = Column(Integer, primary_key=True)
    attempt_id = Column(Integer, ForeignKey('test_attempts.id'), nullable=False)
    attempt = relationship("TestAttempt", back_populates="answers")
    
    question_id = Column(Integer, ForeignKey('test_questions.id'), nullable=False)
    question = relationship("TestQuestion")
    
    selected_option = Column(String(1))
    numerical_answer = Column(Float)
    text_answer = Column(Text)
    
    is_correct = Column(Boolean, default=False)
    marks_awarded = Column(Float, default=0.0)
    
    # Timing for each question
    time_spent_seconds = Column(Integer, default=0)
    
    def __repr__(self):
        return f'<TestAnswerSubmission Q{self.question_id}>'