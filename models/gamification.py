from datetime import date
from extensions import db
from .base import TimestampMixin

class Streak(db.Model, TimestampMixin):
    __tablename__ = 'streaks'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False, unique=True)
    current_streak = db.Column(db.Integer, default=0, nullable=False)
    best_streak = db.Column(db.Integer, default=0, nullable=False)
    last_active_date = db.Column(db.Date, nullable=True)
    
    def update_streak(self, activity_date=None):
        """Update streak based on activity date"""
        if activity_date is None:
            activity_date = date.today()
        
        if self.last_active_date is None:
            # First activity
            self.current_streak = 1
            self.last_active_date = activity_date
        elif activity_date == self.last_active_date:
            # Same day, no change
            return
        elif (activity_date - self.last_active_date).days == 1:
            # Consecutive day
            self.current_streak += 1
            self.last_active_date = activity_date
        else:
            # Streak broken
            self.current_streak = 1
            self.last_active_date = activity_date
        
        # Update best streak
        if self.current_streak > self.best_streak:
            self.best_streak = self.current_streak
    
    def __repr__(self):
        return f'<Streak student={self.student_id} current={self.current_streak} best={self.best_streak}>'

class Points(db.Model, TimestampMixin):
    __tablename__ = 'points'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False, unique=True)
    points_total = db.Column(db.Integer, default=0, nullable=False)
    points_this_week = db.Column(db.Integer, default=0, nullable=False)
    points_this_month = db.Column(db.Integer, default=0, nullable=False)
    last_points_reset = db.Column(db.Date, nullable=True)
    
    def add_points(self, points):
        """Add points to student's total"""
        self.points_total += points
        self.points_this_week += points
        self.points_this_month += points
    
    def reset_weekly_points(self):
        """Reset weekly points (called by scheduler)"""
        self.points_this_week = 0
    
    def reset_monthly_points(self):
        """Reset monthly points (called by scheduler)"""
        self.points_this_month = 0
    
    def __repr__(self):
        return f'<Points student={self.student_id} total={self.points_total}>'

class Badges(db.Model, TimestampMixin):
    __tablename__ = 'badges'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    badge_code = db.Column(db.String(50), nullable=False)
    badge_name = db.Column(db.String(100), nullable=False)
    badge_description = db.Column(db.String(200), nullable=True)
    awarded_at = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp())
    
    # Badge codes: 7D_STREAK, 30D_STREAK, 100_Q_SOLVED, TOPIC_MASTER_<topic>, FAST_SOLVER
    
    # Constraints
    __table_args__ = (
        db.UniqueConstraint('student_id', 'badge_code', name='unique_student_badge'),
    )
    
    @staticmethod
    def award_badge(student_id, badge_code, badge_name, badge_description=None):
        """Award a badge to student if not already awarded"""
        existing = Badges.query.filter_by(student_id=student_id, badge_code=badge_code).first()
        if not existing:
            badge = Badges(
                student_id=student_id,
                badge_code=badge_code,
                badge_name=badge_name,
                badge_description=badge_description
            )
            db.session.add(badge)
            return badge
        return existing
    
    def __repr__(self):
        return f'<Badge student={self.student_id} code={self.badge_code}>'
