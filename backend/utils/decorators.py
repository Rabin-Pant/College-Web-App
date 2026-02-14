from functools import wraps
from flask import jsonify
from flask_jwt_extended import get_jwt_identity
from utils.database import mysql

def role_required(allowed_roles):
    """Decorator to restrict access based on user role"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                # Get current user ID from JWT token
                current_user_id = get_jwt_identity()
                
                if not current_user_id:
                    return jsonify({'error': 'Authentication required'}), 401
                
                # Get user role from database
                cursor = mysql.connection.cursor()
                cursor.execute("SELECT role FROM users WHERE id = %s", (current_user_id,))
                user = cursor.fetchone()
                cursor.close()
                
                if not user:
                    return jsonify({'error': 'User not found'}), 404
                
                # Check if user role is allowed
                if user['role'] not in allowed_roles:
                    return jsonify({'error': 'Access denied. Insufficient permissions.'}), 403
                
                return f(*args, **kwargs)
                
            except Exception as e:
                return jsonify({'error': str(e)}), 500
                
        return decorated_function
    return decorator

def teacher_required(f):
    """Decorator for teacher-only routes"""
    return role_required(['teacher', 'admin'])(f)

def student_required(f):
    """Decorator for student-only routes"""
    return role_required(['student', 'admin'])(f)

def admin_required(f):
    """Decorator for admin-only routes"""
    return role_required(['admin'])(f)

def jwt_optional(f):
    """Decorator for routes that can work with or without JWT"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            current_user_id = get_jwt_identity()
        except:
            current_user_id = None
        return f(current_user_id=current_user_id, *args, **kwargs)
    return decorated_function