from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash
from extensions import db
from models.user import User
from models.student import Student
from services.security import security_service

operator_bp = Blueprint('operator', __name__, url_prefix="/operator")

# -------------------------------
# API ENDPOINT (JSON)
# -------------------------------
@operator_bp.route('/api/register-student', methods=['POST'])
@security_service.require_role(['operator', 'admin'])
def register_student_api():
    """Operator registers a new student + parent via API"""
    try:
        data = request.get_json()

        required_fields = [
            'full_name', 'dob', 'class_level', 'batch_type',
            'goal_exam', 'father_name', 'mother_name',
            'parent_mobile', 'student_mobile', 'address'
        ]
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400

        # Generate credentials
        student_username, student_password = User.generate_student_credentials(data['full_name'])
        parent_username, parent_password = User.generate_parent_credentials(student_username)

        # Create Student user
        student_user = User(
            username=student_username,
            email=f"{student_username}@tachyon.com",
            full_name=data['full_name'],
            phone=data['student_mobile'],
            role='student',
            is_active=True
        )
        student_user.set_password(student_password)
        db.session.add(student_user)
        db.session.flush()

        # Create Parent user
        parent_user = User(
            username=parent_username,
            email=f"{parent_username}@tachyon.com",
            full_name=f"Parent of {data['full_name']}",
            phone=data['parent_mobile'],
            role='parent',
            is_active=True,
            parent_of_student_id=student_user.id
        )
        parent_user.set_password(parent_password)
        db.session.add(parent_user)
        db.session.flush()

        # Create Student profile
        student = Student(
            user_id=student_user.id,
            full_name=data['full_name'],
            dob=data['dob'],
            class_level=data['class_level'],
            batch_type=data['batch_type'],
            goal_exam=data['goal_exam'],
            father_name=data['father_name'],
            mother_name=data['mother_name'],
            parent_mobile=data['parent_mobile'],
            student_mobile=data['student_mobile'],
            address=data['address'],
            blood_group=data.get('blood_group')
        )
        db.session.add(student)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Student registered successfully',
            'student_credentials': {
                'username': student_username,
                'password': student_password
            },
            'parent_credentials': {
                'username': parent_username,
                'password': parent_password
            }
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# -------------------------------
# UI FORM ENDPOINT (HTML)
# -------------------------------
@operator_bp.route('/register-student', methods=['GET', 'POST'])
@security_service.require_role(['operator', 'admin'])
def register_student_ui():
    """Operator UI to register a new student via HTML form"""
    if request.method == 'POST':
        try:
            data = request.form

            # Generate credentials
            student_username, student_password = User.generate_student_credentials(data['full_name'])
            parent_username, parent_password = User.generate_parent_credentials(student_username)

            # Create Student user
            student_user = User(
                username=student_username,
                email=f"{student_username}@tachyon.com",
                full_name=data['full_name'],
                phone=data['student_mobile'],
                role='student',
                is_active=True
            )
            student_user.set_password(student_password)
            db.session.add(student_user)
            db.session.flush()

            # Create Parent user
            parent_user = User(
                username=parent_username,
                email=f"{parent_username}@tachyon.com",
                full_name=f"Parent of {data['full_name']}",
                phone=data['parent_mobile'],
                role='parent',
                is_active=True,
                parent_of_student_id=student_user.id
            )
            parent_user.set_password(parent_password)
            db.session.add(parent_user)
            db.session.flush()

            # Create Student profile
            student = Student(
                user_id=student_user.id,
                full_name=data['full_name'],
                dob=data['dob'],
                class_level=data['class_level'],
                batch_type=data['batch_type'],
                goal_exam=data['goal_exam'],
                father_name=data['father_name'],
                mother_name=data['mother_name'],
                parent_mobile=data['parent_mobile'],
                student_mobile=data['student_mobile'],
                address=data['address'],
                blood_group=data.get('blood_group')
            )
            db.session.add(student)
            db.session.commit()

            flash(f"Student Registered Successfully! Student Login: {student_username}/{student_password}, Parent Login: {parent_username}/{parent_password}", "success")
            return redirect(url_for('operator.register_student_ui'))

        except Exception as e:
            db.session.rollback()
            flash(f"Error: {str(e)}", "danger")

    return render_template("operator/register_student.html")
