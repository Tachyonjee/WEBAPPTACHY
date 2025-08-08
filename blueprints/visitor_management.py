"""
Visitor & Enquiry Management Blueprint
Handles visitor check-in/out, meeting management, and follow-ups
"""

from flask import Blueprint, render_template, request, jsonify, session, flash, redirect, url_for
from datetime import datetime, timedelta
from functools import wraps
from extensions import db
from models.user import User
from models.visitor import Visitor, VisitorMeeting

visitor_bp = Blueprint('visitor', __name__, url_prefix='/visitor')

def role_required(*allowed_roles):
    """Decorator to check if user has required role for visitor management"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                return jsonify({'error': 'Authentication required'}), 401
            
            user = User.query.get(session['user_id'])
            if not user or user.role not in allowed_roles:
                return jsonify({'error': 'Access denied'}), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# ============= VISITOR CHECK-IN/OUT ROUTES =============

@visitor_bp.route('/check-in', methods=['GET', 'POST'])
@role_required('security', 'reception', 'admin')
def check_in():
    """Security logs visitor face, name, purpose, and time-in"""
    if request.method == 'POST':
        data = request.get_json()
        
        # Create new visitor record
        visitor = Visitor(
            name=data.get('name'),
            phone=data.get('phone'),
            email=data.get('email'),
            purpose=data.get('purpose'),
            id_type=data.get('id_type'),
            id_number=data.get('id_number'),
            face_image_path=data.get('face_image_path'),  # Uploaded by security
            logged_by_user_id=session['user_id'],
            status='checked_in'
        )
        
        # Auto-assign to appropriate role based on purpose
        purpose_lower = data.get('purpose', '').lower()
        if 'admission' in purpose_lower or 'enquiry' in purpose_lower:
            visitor.assigned_to_role = 'counsellor'
        elif 'academic' in purpose_lower or 'class' in purpose_lower:
            visitor.assigned_to_role = 'academic_coordinator'
        elif 'fee' in purpose_lower or 'payment' in purpose_lower:
            visitor.assigned_to_role = 'admin_coordinator'
        else:
            visitor.assigned_to_role = 'reception'
        
        db.session.add(visitor)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'visitor_id': visitor.id,
            'assigned_to': visitor.assigned_to_role,
            'message': f'Visitor {visitor.name} checked in successfully'
        })
    
    return render_template('visitor/check_in.html')

@visitor_bp.route('/check-out/<int:visitor_id>', methods=['POST'])
@role_required('security', 'reception', 'admin')
def check_out(visitor_id):
    """Check out visitor"""
    visitor = Visitor.query.get_or_404(visitor_id)
    
    visitor.time_out = datetime.now()
    visitor.status = 'checked_out'
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': f'Visitor {visitor.name} checked out successfully'
    })

# ============= RECEPTION MANAGEMENT =============

@visitor_bp.route('/reception/dashboard')
@role_required('reception', 'admin')
def reception_dashboard():
    """Reception dashboard with pending visitors and notifications"""
    # Get visitors waiting for reception
    pending_visitors = Visitor.query.filter(
        Visitor.status == 'checked_in',
        Visitor.assigned_to_role.in_(['reception', 'counsellor', 'admin_coordinator', 'academic_coordinator'])
    ).order_by(Visitor.time_in.desc()).all()
    
    # Get today's visitor statistics
    today = datetime.now().date()
    today_visitors = Visitor.query.filter(
        db.func.date(Visitor.time_in) == today
    ).count()
    
    return render_template('visitor/reception_dashboard.html',
                         pending_visitors=pending_visitors,
                         today_visitors=today_visitors)

@visitor_bp.route('/reception/update-visitor/<int:visitor_id>', methods=['POST'])
@role_required('reception', 'admin')
def update_visitor_details(visitor_id):
    """Reception updates visitor details after ID scan"""
    visitor = Visitor.query.get_or_404(visitor_id)
    data = request.get_json()
    
    # Update visitor details
    visitor.phone = data.get('phone', visitor.phone)
    visitor.email = data.get('email', visitor.email)
    visitor.id_type = data.get('id_type', visitor.id_type)
    visitor.id_number = data.get('id_number', visitor.id_number)
    
    # Forward to appropriate role
    new_assignment = data.get('assigned_to_role')
    if new_assignment:
        visitor.assigned_to_role = new_assignment
        
        # Optionally assign to specific user
        assigned_user_id = data.get('assigned_to_user_id')
        if assigned_user_id:
            visitor.assigned_to_user_id = assigned_user_id
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': f'Visitor {visitor.name} details updated and forwarded to {visitor.assigned_to_role}'
    })

# ============= MEETING MANAGEMENT =============

@visitor_bp.route('/meeting/start/<int:visitor_id>', methods=['POST'])
@role_required('counsellor', 'admin_coordinator', 'academic_coordinator', 'principal', 'director', 'admin')
def start_meeting(visitor_id):
    """Start meeting with visitor"""
    visitor = Visitor.query.get_or_404(visitor_id)
    
    # Update visitor status
    visitor.status = 'in_meeting'
    
    # Create meeting record
    meeting = VisitorMeeting(
        visitor_id=visitor_id,
        conducted_by_id=session['user_id'],
        meeting_time=datetime.now()
    )
    
    db.session.add(meeting)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'meeting_id': meeting.id,
        'message': f'Meeting started with {visitor.name}'
    })

@visitor_bp.route('/meeting/complete/<int:meeting_id>', methods=['POST'])
@role_required('counsellor', 'admin_coordinator', 'academic_coordinator', 'principal', 'director', 'admin')
def complete_meeting(meeting_id):
    """Complete meeting and add notes"""
    meeting = VisitorMeeting.query.get_or_404(meeting_id)
    data = request.get_json()
    
    # Update meeting details
    meeting.notes = data.get('notes')
    meeting.outcome = data.get('outcome')  # interested, not_interested, follow_up_required
    
    # Handle follow-up requirements
    if data.get('follow_up_required'):
        meeting.follow_up_required = True
        meeting.follow_up_deadline = datetime.strptime(
            data.get('follow_up_deadline'), '%Y-%m-%d %H:%M'
        ) if data.get('follow_up_deadline') else datetime.now() + timedelta(days=7)
        meeting.follow_up_notes = data.get('follow_up_notes')
    
    # Update visitor status
    meeting.visitor.status = 'checked_in'  # Back to checked_in, ready for checkout
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': f'Meeting with {meeting.visitor.name} completed'
    })

# ============= FOLLOW-UP MANAGEMENT =============

@visitor_bp.route('/follow-ups')
@role_required('counsellor', 'admin_coordinator', 'academic_coordinator', 'principal', 'director', 'admin')
def view_follow_ups():
    """View pending follow-ups"""
    user = User.query.get(session['user_id'])
    
    # Get follow-ups assigned to current user or their role
    pending_follow_ups = VisitorMeeting.query.filter(
        VisitorMeeting.follow_up_required == True,
        VisitorMeeting.follow_up_completed == False,
        db.or_(
            VisitorMeeting.conducted_by_id == user.id,
            db.and_(
                VisitorMeeting.conducted_by_id.is_(None),
                Visitor.assigned_to_role == user.role
            )
        )
    ).join(Visitor).order_by(VisitorMeeting.follow_up_deadline.asc()).all()
    
    return render_template('visitor/follow_ups.html',
                         follow_ups=pending_follow_ups)

@visitor_bp.route('/follow-up/complete/<int:meeting_id>', methods=['POST'])
@role_required('counsellor', 'admin_coordinator', 'academic_coordinator', 'principal', 'director', 'admin')
def complete_follow_up(meeting_id):
    """Mark follow-up as completed"""
    meeting = VisitorMeeting.query.get_or_404(meeting_id)
    data = request.get_json()
    
    meeting.follow_up_completed = True
    meeting.follow_up_completed_at = datetime.now()
    meeting.follow_up_notes = data.get('completion_notes', meeting.follow_up_notes)
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Follow-up marked as completed'
    })

# ============= API ENDPOINTS =============

@visitor_bp.route('/api/visitors/today')
@role_required('security', 'reception', 'counsellor', 'admin_coordinator', 'academic_coordinator', 'principal', 'director', 'admin')
def api_today_visitors():
    """API endpoint for today's visitors"""
    today = datetime.now().date()
    visitors = Visitor.query.filter(
        db.func.date(Visitor.time_in) == today
    ).order_by(Visitor.time_in.desc()).all()
    
    return jsonify([{
        'id': v.id,
        'name': v.name,
        'purpose': v.purpose,
        'time_in': v.time_in.strftime('%H:%M'),
        'time_out': v.time_out.strftime('%H:%M') if v.time_out else None,
        'status': v.status,
        'assigned_to_role': v.assigned_to_role
    } for v in visitors])

@visitor_bp.route('/api/visitors/statistics')
@role_required('principal', 'director', 'admin')
def api_visitor_statistics():
    """API endpoint for visitor statistics"""
    today = datetime.now().date()
    this_week = datetime.now() - timedelta(days=7)
    this_month = datetime.now() - timedelta(days=30)
    
    stats = {
        'today': Visitor.query.filter(db.func.date(Visitor.time_in) == today).count(),
        'this_week': Visitor.query.filter(Visitor.time_in >= this_week).count(),
        'this_month': Visitor.query.filter(Visitor.time_in >= this_month).count(),
        'pending_follow_ups': VisitorMeeting.query.filter(
            VisitorMeeting.follow_up_required == True,
            VisitorMeeting.follow_up_completed == False
        ).count()
    }
    
    return jsonify(stats)