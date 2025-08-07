from flask import Blueprint, request, jsonify, render_template, redirect, url_for, session, flash
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from extensions import db
from models.user import User, OTPVerification
from models.student import Student
from services.otp import otp_service
from services.security import SecurityService
import logging

logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login')
def login():
    """Render login page"""
    return render_template('auth/login.html')

@auth_bp.route('/otp')
def otp_page():
    """Render OTP verification page"""
    identifier = request.args.get('identifier')
    if not identifier:
        flash('No identifier provided', 'error')
        return redirect(url_for('auth.login'))
    return render_template('auth/otp.html', identifier=identifier)

@auth_bp.route('/request-otp', methods=['POST'])
def request_otp():
    """Request OTP for login"""
    try:
        data = request.get_json() or request.form
        identifier = data.get('identifier', '').strip()
        
        if not identifier:
            return jsonify({
                'success': False,
                'message': 'Email or phone number is required'
            }), 400
        
        # Determine if it's email or phone
        delivery_method = 'email' if '@' in identifier else 'sms'
        
        # Check if user exists, if not create a new student user
        user = User.query.filter(
            (User.email == identifier) | (User.phone == identifier)
        ).first()
        
        if not user:
            # Create new student user
            user = User(
                name=f"Student {identifier.split('@')[0] if '@' in identifier else identifier[-4:]}",
                email=identifier if '@' in identifier else '',
                phone=identifier if '@' not in identifier else None,
                role='student'
            )
            db.session.add(user)
            db.session.flush()  # Get the user ID
            
            # Create student profile
            student = Student(
                user_id=user.id,
                goal_exam='JEE'  # Default exam
            )
            db.session.add(student)
            db.session.commit()
        
        # Send OTP
        result = otp_service.send_otp(identifier, delivery_method)
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': result['message'],
                'redirect_url': url_for('auth.otp_page', identifier=identifier)
            })
        else:
            return jsonify({
                'success': False,
                'message': result['message']
            }), 400
    
    except Exception as e:
        logger.error(f"Error in request_otp: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An error occurred. Please try again.'
        }), 500

@auth_bp.route('/verify-otp', methods=['POST'])
def verify_otp():
    """Verify OTP and log in user"""
    try:
        data = request.get_json() or request.form
        identifier = data.get('identifier', '').strip()
        otp_code = data.get('otp_code', '').strip()
        
        if not identifier or not otp_code:
            return jsonify({
                'success': False,
                'message': 'Identifier and OTP code are required'
            }), 400
        
        # Verify OTP
        result = otp_service.verify_otp(identifier, otp_code)
        
        if result['success']:
            # Find user
            user = User.query.filter(
                (User.email == identifier) | (User.phone == identifier)
            ).first()
            
            if not user:
                return jsonify({
                    'success': False,
                    'message': 'User not found'
                }), 404
            
            # Update last login
            user.update_last_login()
            
            # Create JWT token
            access_token = create_access_token(identity=user.id)
            
            # Set session data
            session['user_id'] = user.id
            session['user_role'] = user.role
            
            # Determine redirect URL based on role
            redirect_urls = {
                'student': url_for('student_home'),
                'operator': url_for('operator_home'),
                'mentor': url_for('mentor_insights'),
                'admin': url_for('admin_overview')
            }
            
            return jsonify({
                'success': True,
                'message': 'Login successful',
                'access_token': access_token,
                'user': {
                    'id': user.id,
                    'name': user.name,
                    'email': user.email,
                    'role': user.role
                },
                'redirect_url': redirect_urls.get(user.role, url_for('student_home'))
            })
        else:
            return jsonify({
                'success': False,
                'message': result['message'],
                'attempts_remaining': result.get('attempts_remaining', 0)
            }), 400
    
    except Exception as e:
        logger.error(f"Error in verify_otp: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An error occurred. Please try again.'
        }), 500

@auth_bp.route('/logout', methods=['POST'])
def logout():
    """Log out user"""
    try:
        # Clear session
        session.clear()
        
        return jsonify({
            'success': True,
            'message': 'Logged out successfully',
            'redirect_url': url_for('auth.login')
        })
    
    except Exception as e:
        logger.error(f"Error in logout: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An error occurred during logout'
        }), 500

@auth_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """Get current user profile"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({
                'success': False,
                'message': 'User not found'
            }), 404
        
        profile_data = {
            'id': user.id,
            'name': user.name,
            'email': user.email,
            'phone': user.phone,
            'role': user.role,
            'last_login': user.last_login.isoformat() if user.last_login else None
        }
        
        # Add student-specific data if user is a student
        if user.role == 'student' and user.student_profile:
            profile_data['student'] = {
                'batch': user.student_profile.batch,
                'goal_exam': user.student_profile.goal_exam
            }
        
        return jsonify({
            'success': True,
            'profile': profile_data
        })
    
    except Exception as e:
        logger.error(f"Error in get_profile: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An error occurred'
        }), 500

@auth_bp.route('/update-profile', methods=['POST'])
@jwt_required()
def update_profile():
    """Update user profile"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({
                'success': False,
                'message': 'User not found'
            }), 404
        
        data = request.get_json() or request.form
        
        # Update basic profile data
        if 'name' in data:
            user.name = data['name'].strip()
        
        # Update student-specific data
        if user.role == 'student' and user.student_profile:
            if 'goal_exam' in data:
                user.student_profile.goal_exam = data['goal_exam']
            if 'batch' in data:
                user.student_profile.batch = data['batch']
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Profile updated successfully'
        })
    
    except Exception as e:
        logger.error(f"Error in update_profile: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': 'An error occurred while updating profile'
        }), 500

@auth_bp.route('/check-session', methods=['GET'])
def check_session():
    """Check if user has valid session"""
    try:
        if 'user_id' in session and 'user_role' in session:
            user = User.query.get(session['user_id'])
            if user and user.is_active:
                return jsonify({
                    'authenticated': True,
                    'user': {
                        'id': user.id,
                        'name': user.name,
                        'role': user.role
                    }
                })
        
        return jsonify({'authenticated': False})
    
    except Exception as e:
        logger.error(f"Error in check_session: {str(e)}")
        return jsonify({'authenticated': False})

# Password-based auth for operators/admins (optional)
@auth_bp.route('/password-login', methods=['POST'])
def password_login():
    """Password-based login for operators and admins"""
    try:
        data = request.get_json() or request.form
        email = data.get('email', '').strip()
        password = data.get('password', '').strip()
        
        if not email or not password:
            return jsonify({
                'success': False,
                'message': 'Email and password are required'
            }), 400
        
        # Find user
        user = User.query.filter_by(email=email).first()
        
        if not user or not user.check_password(password):
            return jsonify({
                'success': False,
                'message': 'Invalid email or password'
            }), 401
        
        if user.role not in ['operator', 'mentor', 'admin']:
            return jsonify({
                'success': False,
                'message': 'Password login not allowed for this user type'
            }), 403
        
        # Update last login
        user.update_last_login()
        
        # Create JWT token
        access_token = create_access_token(identity=user.id)
        
        # Set session data
        session['user_id'] = user.id
        session['user_role'] = user.role
        
        # Determine redirect URL
        redirect_urls = {
            'operator': url_for('operator_home'),
            'mentor': url_for('mentor_insights'),
            'admin': url_for('admin_overview')
        }
        
        return jsonify({
            'success': True,
            'message': 'Login successful',
            'access_token': access_token,
            'user': {
                'id': user.id,
                'name': user.name,
                'email': user.email,
                'role': user.role
            },
            'redirect_url': redirect_urls.get(user.role, url_for('admin_overview'))
        })
    
    except Exception as e:
        logger.error(f"Error in password_login: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An error occurred. Please try again.'
        }), 500
