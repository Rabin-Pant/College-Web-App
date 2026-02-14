from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from utils.database import mysql
from utils.decorators import admin_required
from utils.auth_helpers import generate_employee_id, generate_student_id
from werkzeug.security import generate_password_hash
from datetime import datetime

admin_users_bp = Blueprint('admin_users', __name__)

# ============ GET ALL USERS ============

@admin_users_bp.route('/', methods=['GET'], strict_slashes=False)
@jwt_required()
@admin_required
def get_all_users():
    """Get all users with filtering"""
    try:
        role = request.args.get('role')
        verified = request.args.get('verified')
        search = request.args.get('search')
        limit = request.args.get('limit', 100)
        offset = request.args.get('offset', 0)
        
        cursor = mysql.connection.cursor()
        
        query = """
            SELECT 
                u.id, u.email, u.name, u.role, 
                u.profile_pic, u.email_verified, u.created_at,
                tp.employee_id,
                sp.student_id,
                sp.major,
                sp.enrollment_year
            FROM users u
            LEFT JOIN teacher_profiles tp ON u.id = tp.user_id
            LEFT JOIN student_profiles sp ON u.id = sp.user_id
            WHERE 1=1
        """
        params = []
        
        if role:
            query += " AND u.role = %s"
            params.append(role)
        
        if verified is not None:
            query += " AND u.email_verified = %s"
            params.append(verified.lower() == 'true')
        
        if search:
            query += " AND (u.name LIKE %s OR u.email LIKE %s)"
            params.append(f'%{search}%')
            params.append(f'%{search}%')
        
        query += " ORDER BY u.created_at DESC LIMIT %s OFFSET %s"
        params.extend([int(limit), int(offset)])
        
        cursor.execute(query, params)
        users = cursor.fetchall()
        
        # Get total count
        cursor.execute("SELECT COUNT(*) as count FROM users")
        total = cursor.fetchone()['count']
        
        cursor.close()
        
        return jsonify({
            'total': total,
            'users': users
        }), 200
        
    except Exception as e:
        print(f"Error getting users: {e}")
        return jsonify({'error': str(e)}), 500


@admin_users_bp.route('/<int:user_id>', methods=['GET'], strict_slashes=False)
@jwt_required()
@admin_required
def get_user_details(user_id):
    """Get detailed user information"""
    try:
        cursor = mysql.connection.cursor()
        
        cursor.execute("""
            SELECT id, email, name, role, profile_pic, bio, 
                   department, email_verified, created_at, updated_at
            FROM users WHERE id = %s
        """, (user_id,))
        
        user = cursor.fetchone()
        
        if not user:
            cursor.close()
            return jsonify({'error': 'User not found'}), 404
        
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
        print(f"Error getting user details: {e}")
        return jsonify({'error': str(e)}), 500


@admin_users_bp.route('/<int:user_id>/verify', methods=['PUT'], strict_slashes=False)
@jwt_required()
@admin_required
def verify_teacher(user_id):
    """Verify a teacher account"""
    try:
        admin_id = get_jwt_identity()
        cursor = mysql.connection.cursor()
        
        cursor.execute("SELECT role, name FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        
        if not user:
            cursor.close()
            return jsonify({'error': 'User not found'}), 404
        
        if user['role'] != 'teacher':
            cursor.close()
            return jsonify({'error': 'User is not a teacher'}), 400
        
        cursor.execute("""
            UPDATE users 
            SET email_verified = TRUE 
            WHERE id = %s
        """, (user_id,))
        
        mysql.connection.commit()
        cursor.close()
        
        return jsonify({'message': f'Teacher {user["name"]} verified successfully'}), 200
        
    except Exception as e:
        print(f"Error verifying teacher: {e}")
        return jsonify({'error': str(e)}), 500


@admin_users_bp.route('/<int:user_id>', methods=['DELETE'], strict_slashes=False)
@jwt_required()
@admin_required
def delete_user(user_id):
    """Delete a user"""
    try:
        admin_id = get_jwt_identity()
        
        if admin_id == user_id:
            return jsonify({'error': 'Cannot delete your own account'}), 400
        
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT name, role FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        
        if not user:
            cursor.close()
            return jsonify({'error': 'User not found'}), 404
        
        cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
        mysql.connection.commit()
        cursor.close()
        
        return jsonify({
            'message': f'User {user["name"]} deleted successfully'
        }), 200
        
    except Exception as e:
        print(f"Error deleting user: {e}")
        return jsonify({'error': str(e)}), 500


@admin_users_bp.route('/', methods=['POST'], strict_slashes=False)
@jwt_required()
@admin_required
def create_user():
    """Create a new user"""
    try:
        data = request.get_json()
        
        required_fields = ['email', 'password', 'name', 'role']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT id FROM users WHERE email = %s", (data['email'],))
        if cursor.fetchone():
            cursor.close()
            return jsonify({'error': 'Email already registered'}), 400
        
        hashed_password = generate_password_hash(data['password'])
        
        cursor.execute("""
            INSERT INTO users (email, password, name, role, email_verified, college_email, department, bio)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            data['email'],
            hashed_password,
            data['name'],
            data['role'],
            data.get('email_verified', True),
            data.get('college_email', data['email']),
            data.get('department'),
            data.get('bio')
        ))
        
        user_id = cursor.lastrowid
        
        if data['role'] == 'teacher':
            employee_id = data.get('employee_id', generate_employee_id())
            cursor.execute("""
                INSERT INTO teacher_profiles (user_id, employee_id, department, office_hours, qualifications)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                user_id,
                employee_id,
                data.get('department', 'General'),
                data.get('office_hours'),
                data.get('qualifications')
            ))
            
        elif data['role'] == 'student':
            student_id = data.get('student_id', generate_student_id())
            cursor.execute("""
                INSERT INTO student_profiles (user_id, student_id, enrollment_year, major, minor, current_semester)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                user_id,
                student_id,
                data.get('enrollment_year', datetime.now().year),
                data.get('major', 'Undeclared'),
                data.get('minor'),
                data.get('current_semester', 1)
            ))
        
        mysql.connection.commit()
        cursor.close()
        
        return jsonify({
            'message': 'User created successfully',
            'user_id': user_id
        }), 201
        
    except Exception as e:
        print(f"Error creating user: {e}")
        return jsonify({'error': str(e)}), 500