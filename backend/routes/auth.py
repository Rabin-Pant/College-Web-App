from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from utils.database import mysql
from utils.auth_helpers import generate_verification_token, generate_student_id, generate_employee_id
from utils.validators import validate_email, validate_college_email, validate_password, validate_required_fields
from utils.email import send_verification_email
import random
import string
import re
from datetime import timedelta

auth_bp = Blueprint('auth', __name__)

# ============ HELPER FUNCTIONS ============

def generate_class_code(length=6):
    """Generate unique 6-digit class code"""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

# ============ PUBLIC ENDPOINTS ============

@auth_bp.route('/register', methods=['POST'])
def register():
    """Register new user (student or teacher) with auto-verify in development"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['email', 'password', 'name', 'role']
        is_valid, missing_fields = validate_required_fields(data, required_fields)
        if not is_valid:
            return jsonify({'error': f'Missing required fields: {", ".join(missing_fields)}'}), 400
        
        # Validate email format
        if not validate_email(data['email']):
            return jsonify({'error': 'Invalid email format'}), 400
        
        # Validate college email domain
        college_domain = current_app.config.get('COLLEGE_EMAIL_DOMAIN', '@yourcollege.edu')
        if not validate_college_email(data['email'], college_domain):
            return jsonify({'error': f'Must use college email {college_domain}'}), 400
        
        # Validate password strength
        is_valid, password_errors = validate_password(data['password'])
        if not is_valid:
            return jsonify({'error': password_errors[0] if password_errors else 'Invalid password'}), 400
        
        # Check if email already exists
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM users WHERE email = %s", (data['email'],))
        existing_user = cursor.fetchone()
        
        if existing_user:
            cursor.close()
            return jsonify({'error': 'Email already registered'}), 400
        
        # Hash password
        hashed_password = generate_password_hash(data['password'])
        
        # Generate verification token (still create it even if we auto-verify)
        verification_token = generate_verification_token()
        
        # Check if email verification is enabled
        email_verification_enabled = current_app.config.get('ENABLE_EMAIL_VERIFICATION', True)
        
        # In development, auto-verify emails. In production, require verification.
        email_verified = not email_verification_enabled  # Auto-verify if disabled
        
        # Insert user
        cursor.execute("""
            INSERT INTO users (
                email, password, role, name, college_email, 
                verification_token, email_verified, department, profile_pic, bio
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            data['email'],
            hashed_password,
            data['role'],
            data['name'],
            data['email'],
            verification_token,
            email_verified,  # Auto-verified in development
            data.get('department'),
            data.get('profile_pic'),
            data.get('bio')
        ))
        
        mysql.connection.commit()
        user_id = cursor.lastrowid
        
        # Create role-specific profile
        if data['role'] == 'teacher':
            employee_id = generate_employee_id()
            cursor.execute("""
                INSERT INTO teacher_profiles (
                    user_id, employee_id, department, office_hours, qualifications
                ) VALUES (%s, %s, %s, %s, %s)
            """, (
                user_id,
                employee_id,
                data.get('department', 'General'),
                data.get('office_hours'),
                data.get('qualifications')
            ))
            
        elif data['role'] == 'student':
            student_id = generate_student_id()
            enrollment_year = data.get('enrollment_year', 2024)
            cursor.execute("""
                INSERT INTO student_profiles (
                    user_id, student_id, enrollment_year, major, minor, current_semester
                ) VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                user_id,
                student_id,
                enrollment_year,
                data.get('major', 'Undeclared'),
                data.get('minor'),
                data.get('current_semester', 1)
            ))
        
        mysql.connection.commit()
        cursor.close()
        
        # Send verification email only if email verification is enabled
        if email_verification_enabled:
            try:
                send_verification_email(data['email'], data['name'], verification_token)
                email_status = "Verification email sent"
            except Exception as e:
                print(f"Failed to send verification email: {e}")
                email_status = "Failed to send verification email"
        else:
            email_status = "Email auto-verified (development mode)"
        
        response_data = {
            'message': 'Registration successful!',
            'user_id': user_id,
            'email_verified': email_verified
        }
        
        # Only include verification token in development
        if current_app.config.get('FLASK_ENV') == 'development':
            response_data['verification_token'] = verification_token
            response_data['email_status'] = email_status
        
        return jsonify(response_data), 201
        
    except Exception as e:
        print(f"Registration error: {e}")
        return jsonify({'error': 'Registration failed. Please try again.'}), 500


@auth_bp.route('/login', methods=['POST'])
def login():
    """Login user and return JWT tokens"""
    try:
        data = request.get_json()
        
        if not data or not data.get('email') or not data.get('password'):
            return jsonify({'error': 'Email and password required'}), 400
        
        cursor = mysql.connection.cursor()
        cursor.execute("""
            SELECT id, email, password, name, role, profile_pic, email_verified 
            FROM users WHERE email = %s
        """, (data['email'],))
        user = cursor.fetchone()
        cursor.close()
        
        if not user:
            return jsonify({'error': 'Invalid email or password'}), 401
        
        # Check password
        if not check_password_hash(user['password'], data['password']):
            return jsonify({'error': 'Invalid email or password'}), 401
        
        # Check if email is verified
        if not user['email_verified']:
            return jsonify({
                'error': 'Email not verified. Please check your inbox for verification link.',
                'needs_verification': True
            }), 401
        
        # Create tokens
        access_token = create_access_token(
            identity=user['id'],
            additional_claims={
                'role': user['role'],
                'name': user['name'],
                'email': user['email']
            },
            expires_delta=timedelta(hours=1)
        )
        
        refresh_token = create_refresh_token(
            identity=user['id'],
            expires_delta=timedelta(days=30)
        )
        
        # Get role-specific profile info
        profile_data = {}
        
        if user['role'] == 'teacher':
            cursor = mysql.connection.cursor()
            cursor.execute("""
                SELECT employee_id, department, office_hours 
                FROM teacher_profiles WHERE user_id = %s
            """, (user['id'],))
            profile = cursor.fetchone()
            cursor.close()
            if profile:
                profile_data = profile
                
        elif user['role'] == 'student':
            cursor = mysql.connection.cursor()
            cursor.execute("""
                SELECT student_id, enrollment_year, major, current_semester
                FROM student_profiles WHERE user_id = %s
            """, (user['id'],))
            profile = cursor.fetchone()
            cursor.close()
            if profile:
                profile_data = profile
        
        return jsonify({
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': {
                'id': user['id'],
                'email': user['email'],
                'name': user['name'],
                'role': user['role'],
                'profile_pic': user['profile_pic'],
                **profile_data
            }
        }), 200
        
    except Exception as e:
        print(f"Login error: {e}")
        return jsonify({'error': 'Login failed. Please try again.'}), 500


@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """Get new access token using refresh token"""
    try:
        current_user_id = get_jwt_identity()
        
        # Get user role for additional claims
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT role, name, email FROM users WHERE id = %s", (current_user_id,))
        user = cursor.fetchone()
        cursor.close()
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        access_token = create_access_token(
            identity=current_user_id,
            additional_claims={
                'role': user['role'],
                'name': user['name'],
                'email': user['email']
            }
        )
        
        return jsonify({'access_token': access_token}), 200
        
    except Exception as e:
        print(f"Refresh error: {e}")
        return jsonify({'error': 'Token refresh failed'}), 500


@auth_bp.route('/verify/<token>', methods=['GET'])
def verify_email(token):
    """Verify user email with token"""
    try:
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM users WHERE verification_token = %s", (token,))
        user = cursor.fetchone()
        
        if not user:
            cursor.close()
            return jsonify({'error': 'Invalid or expired verification token'}), 404
        
        # Check if already verified
        if user['email_verified']:
            cursor.close()
            return jsonify({'message': 'Email already verified. You can login now.'}), 200
        
        # Verify email
        cursor.execute("""
            UPDATE users 
            SET email_verified = TRUE, verification_token = NULL 
            WHERE id = %s
        """, (user['id'],))
        
        mysql.connection.commit()
        cursor.close()
        
        return jsonify({'message': 'Email verified successfully! You can now login.'}), 200
        
    except Exception as e:
        print(f"Verification error: {e}")
        return jsonify({'error': 'Email verification failed'}), 500


@auth_bp.route('/resend-verification', methods=['POST'])
def resend_verification():
    """Resend verification email"""
    try:
        data = request.get_json()
        
        if not data or not data.get('email'):
            return jsonify({'error': 'Email required'}), 400
        
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM users WHERE email = %s", (data['email'],))
        user = cursor.fetchone()
        
        if not user:
            cursor.close()
            return jsonify({'error': 'User not found'}), 404
        
        if user['email_verified']:
            cursor.close()
            return jsonify({'message': 'Email already verified'}), 200
        
        # Generate new token
        new_token = generate_verification_token()
        cursor.execute("UPDATE users SET verification_token = %s WHERE id = %s", 
                      (new_token, user['id']))
        mysql.connection.commit()
        cursor.close()
        
        # Send email
        try:
            send_verification_email(user['email'], user['name'], new_token)
            return jsonify({'message': 'Verification email sent'}), 200
        except Exception as e:
            return jsonify({'error': 'Failed to send verification email'}), 500
        
    except Exception as e:
        print(f"Resend verification error: {e}")
        return jsonify({'error': 'Failed to resend verification'}), 500


# ============ PROTECTED ENDPOINTS ============

@auth_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """Get current user profile"""
    try:
        user_id = get_jwt_identity()
        cursor = mysql.connection.cursor()
        
        # Get base user info
        cursor.execute("""
            SELECT id, email, name, role, profile_pic, bio, department, 
                   email_verified, created_at
            FROM users WHERE id = %s
        """, (user_id,))
        user = cursor.fetchone()
        
        if not user:
            cursor.close()
            return jsonify({'error': 'User not found'}), 404
        
        # Get role-specific profile
        if user['role'] == 'teacher':
            cursor.execute("""
                SELECT employee_id, department, office_hours, qualifications
                FROM teacher_profiles WHERE user_id = %s
            """, (user_id,))
            profile = cursor.fetchone()
            if profile:
                user.update(profile)
                
        elif user['role'] == 'student':
            cursor.execute("""
                SELECT student_id, enrollment_year, major, minor, current_semester
                FROM student_profiles WHERE user_id = %s
            """, (user_id,))
            profile = cursor.fetchone()
            if profile:
                user.update(profile)
        
        cursor.close()
        return jsonify(user), 200
        
    except Exception as e:
        print(f"Profile fetch error: {e}")
        return jsonify({'error': 'Failed to fetch profile'}), 500


@auth_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    """Update user profile"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        cursor = mysql.connection.cursor()
        
        # Update user table
        update_fields = []
        update_values = []
        
        allowed_fields = ['name', 'bio', 'profile_pic', 'department']
        for field in allowed_fields:
            if field in data:
                update_fields.append(f"{field} = %s")
                update_values.append(data[field])
        
        if update_fields:
            query = f"UPDATE users SET {', '.join(update_fields)} WHERE id = %s"
            update_values.append(user_id)
            cursor.execute(query, tuple(update_values))
        
        # Update role-specific profile
        cursor.execute("SELECT role FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        
        if user['role'] == 'teacher':
            teacher_fields = []
            teacher_values = []
            if 'office_hours' in data:
                teacher_fields.append("office_hours = %s")
                teacher_values.append(data['office_hours'])
            if 'qualifications' in data:
                teacher_fields.append("qualifications = %s")
                teacher_values.append(data['qualifications'])
            if teacher_fields:
                query = f"UPDATE teacher_profiles SET {', '.join(teacher_fields)} WHERE user_id = %s"
                teacher_values.append(user_id)
                cursor.execute(query, tuple(teacher_values))
                
        elif user['role'] == 'student':
            student_fields = []
            student_values = []
            if 'major' in data:
                student_fields.append("major = %s")
                student_values.append(data['major'])
            if 'minor' in data:
                student_fields.append("minor = %s")
                student_values.append(data['minor'])
            if 'current_semester' in data:
                student_fields.append("current_semester = %s")
                student_values.append(data['current_semester'])
            if student_fields:
                query = f"UPDATE student_profiles SET {', '.join(student_fields)} WHERE user_id = %s"
                student_values.append(user_id)
                cursor.execute(query, tuple(student_values))
        
        mysql.connection.commit()
        cursor.close()
        
        return jsonify({'message': 'Profile updated successfully'}), 200
        
    except Exception as e:
        print(f"Profile update error: {e}")
        return jsonify({'error': 'Failed to update profile'}), 500


@auth_bp.route('/change-password', methods=['PUT'])
@jwt_required()
def change_password():
    """Change user password"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data.get('current_password') or not data.get('new_password'):
            return jsonify({'error': 'Current password and new password required'}), 400
        
        # Verify current password
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT password FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        
        if not check_password_hash(user['password'], data['current_password']):
            cursor.close()
            return jsonify({'error': 'Current password is incorrect'}), 401
        
        # Validate new password
        is_valid, password_errors = validate_password(data['new_password'])
        if not is_valid:
            cursor.close()
            return jsonify({'error': password_errors[0] if password_errors else 'Invalid password'}), 400
        
        # Update password
        hashed_password = generate_password_hash(data['new_password'])
        cursor.execute("UPDATE users SET password = %s WHERE id = %s", 
                      (hashed_password, user_id))
        
        mysql.connection.commit()
        cursor.close()
        
        return jsonify({'message': 'Password changed successfully'}), 200
        
    except Exception as e:
        print(f"Password change error: {e}")
        return jsonify({'error': 'Failed to change password'}), 500


@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """Logout user (client must discard token)"""
    # JWT is stateless, so we just return success
    # Client should delete the token
    return jsonify({'message': 'Logged out successfully'}), 200


@auth_bp.route('/delete-account', methods=['DELETE'])
@jwt_required()
def delete_account():
    """Delete user account"""
    try:
        user_id = get_jwt_identity()
        
        cursor = mysql.connection.cursor()
        cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
        mysql.connection.commit()
        cursor.close()
        
        return jsonify({'message': 'Account deleted successfully'}), 200
        
    except Exception as e:
        print(f"Account deletion error: {e}")
        return jsonify({'error': 'Failed to delete account'}), 500