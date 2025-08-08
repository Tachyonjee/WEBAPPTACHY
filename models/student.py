from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Float, ForeignKey, Text
from sqlalchemy.orm import relationship
from extensions import db

class StudentProgress(db.Model):
    __tablename__ = 'student_progress'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, unique=True)
    user = relationship("User", backref="progress")
    
    # Academic Progress
    current_class = Column(String(20))  # Class 11, 12, etc.
    current_batch = Column(String(50))  # JEE, NEET, Foundation
    enrollment_date = Column(DateTime, default=datetime.now)
    
    # Gamification Points
    total_points = Column(Integer, default=0)
    points_this_week = Column(Integer, default=0)
    points_this_month = Column(Integer, default=0)
    
    # Streaks
    current_streak = Column(Integer, default=0)
    best_streak = Column(Integer, default=0)
    last_activity_date = Column(DateTime, default=datetime.now)
    
    # Practice Statistics
    total_questions_attempted = Column(Integer, default=0)
    total_questions_correct = Column(Integer, default=0)
    total_dpps_completed = Column(Integer, default=0)
    total_tests_taken = Column(Integer, default=0)
    
    # Performance Metrics
    average_accuracy = Column(Float, default=0.0)
    improvement_rate = Column(Float, default=0.0)  # Percentage improvement over time
    
    # Subject-wise progress (JSON or separate table)
    physics_accuracy = Column(Float, default=0.0)
    chemistry_accuracy = Column(Float, default=0.0)
    mathematics_accuracy = Column(Float, default=0.0)
    biology_accuracy = Column(Float, default=0.0)
    
    # Difficulty progression
    current_difficulty_level = Column(String(20), default='easy')  # easy, medium, hard, expert
    unlocked_difficulties = Column(String(100), default='easy')  # Comma-separated list
    
    # Attendance and engagement
    classes_attended = Column(Integer, default=0)
    total_study_hours = Column(Float, default=0.0)
    
    # Last updated
    last_updated = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    def update_streak(self):
        """Update streak based on activity"""
        today = datetime.now().date()
        if self.last_activity_date:
            last_activity = self.last_activity_date.date()
            if last_activity == today:
                # Already updated today
                return
            elif (today - last_activity).days == 1:
                # Consecutive day, increment streak
                self.current_streak += 1
                if self.current_streak > self.best_streak:
                    self.best_streak = self.current_streak
            else:
                # Streak broken
                self.current_streak = 1
        else:
            # First activity
            self.current_streak = 1
            
        self.last_activity_date = datetime.now()
        self.last_updated = datetime.now()
    
    def add_points(self, points, activity_type='general'):
        """Add points for various activities"""
        self.total_points += points
        self.points_this_week += points
        self.points_this_month += points
        self.last_updated = datetime.now()
        
        # Update activity streak
        self.update_streak()
    
    def calculate_accuracy(self):
        """Calculate overall accuracy percentage"""
        if self.total_questions_attempted > 0:
            self.average_accuracy = (self.total_questions_correct / self.total_questions_attempted) * 100
        else:
            self.average_accuracy = 0.0
        
        return self.average_accuracy
    
    def update_subject_accuracy(self, subject, correct, total):
        """Update subject-specific accuracy"""
        if total > 0:
            accuracy = (correct / total) * 100
            
            if subject.lower() == 'physics':
                self.physics_accuracy = accuracy
            elif subject.lower() == 'chemistry':
                self.chemistry_accuracy = accuracy
            elif subject.lower() == 'mathematics':
                self.mathematics_accuracy = accuracy
            elif subject.lower() == 'biology':
                self.biology_accuracy = accuracy
                
        self.last_updated = datetime.now()
    
    def check_difficulty_unlock(self):
        """Check if student can unlock higher difficulty levels"""
        current_accuracy = self.calculate_accuracy()
        unlocked = self.unlocked_difficulties.split(',')
        
        # Unlock medium if accuracy > 70% and completed at least 10 questions
        if (current_accuracy >= 70 and self.total_questions_attempted >= 10 
            and 'medium' not in unlocked):
            unlocked.append('medium')
            self.current_difficulty_level = 'medium'
        
        # Unlock hard if accuracy > 80% and completed at least 50 questions
        if (current_accuracy >= 80 and self.total_questions_attempted >= 50 
            and 'hard' not in unlocked):
            unlocked.append('hard')
            self.current_difficulty_level = 'hard'
            
        # Unlock expert if accuracy > 90% and completed at least 100 questions
        if (current_accuracy >= 90 and self.total_questions_attempted >= 100 
            and 'expert' not in unlocked):
            unlocked.append('expert')
            self.current_difficulty_level = 'expert'
            
        self.unlocked_difficulties = ','.join(unlocked)
    
    def get_performance_summary(self):
        """Get a summary of student performance"""
        return {
            'total_points': self.total_points,
            'current_streak': self.current_streak,
            'best_streak': self.best_streak,
            'accuracy': round(self.average_accuracy, 2),
            'questions_attempted': self.total_questions_attempted,
            'questions_correct': self.total_questions_correct,
            'dpps_completed': self.total_dpps_completed,
            'tests_taken': self.total_tests_taken,
            'current_difficulty': self.current_difficulty_level,
            'subject_accuracy': {
                'physics': round(self.physics_accuracy, 2),
                'chemistry': round(self.chemistry_accuracy, 2),
                'mathematics': round(self.mathematics_accuracy, 2),
                'biology': round(self.biology_accuracy, 2)
            }
        }
    
    def __repr__(self):
        return f'<StudentProgress {self.user.username}: {self.total_points} points>'

class StudentBadge(db.Model):
    __tablename__ = 'student_badges'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    user = relationship("User", backref="badges")
    
    badge_type = Column(String(50), nullable=False)  # streak_master, accuracy_king, etc.
    badge_name = Column(String(100), nullable=False)
    badge_description = Column(Text)
    badge_icon = Column(String(100))  # Icon class or image path
    
    # Achievement criteria
    criteria_met = Column(Text)  # Description of what was achieved
    points_awarded = Column(Integer, default=0)
    
    # Timestamps
    earned_at = Column(DateTime, default=datetime.now)
    
    def __repr__(self):
        return f'<StudentBadge {self.badge_name} for {self.user.username}>'

class StudentAttendance(db.Model):
    __tablename__ = 'student_attendance'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    user = relationship("User", foreign_keys=[user_id], backref="attendance_records")
    
    class_id = Column(Integer, ForeignKey('classes.id'), nullable=False)
    # class_session = relationship("Class", backref="attendance_records")
    
    # Attendance status
    status = Column(String(20), default='present')  # present, absent, late
    marked_at = Column(DateTime, default=datetime.now)
    marked_by_id = Column(Integer, ForeignKey('users.id'))
    marked_by = relationship("User", foreign_keys=[marked_by_id])
    
    # Additional notes
    notes = Column(Text)
    
    def __repr__(self):
        return f'<StudentAttendance {self.user.username}: {self.status}>'