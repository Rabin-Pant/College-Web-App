from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import random
import string
from datetime import datetime, timedelta
from flask import current_app

def hash_password(password):
    """Hash a password using bcrypt"""
    return generate_password_hash(password)

def check_password(password_hash, password):
    """Verify a password against its hash"""
    return check_password_hash(password_hash, password)

def generate_token(data, expires_delta=timedelta(hours=24), secret_key=None):
    """Generate JWT token"""
    if secret_key is None:
        secret_key = current_app.config.get('SECRET_KEY', 'dev-secret-key')
    
    payload = {
        **data,
        'exp': datetime.utcnow() + expires_delta,
        'iat': datetime.utcnow()
    }
    return jwt.encode(payload, secret_key, algorithm='HS256')

def verify_token(token, secret_key=None):
    """Verify JWT token"""
    if secret_key is None:
        secret_key = current_app.config.get('SECRET_KEY', 'dev-secret-key')
    
    try:
        payload = jwt.decode(token, secret_key, algorithms=['HS256'])
        return payload, None
    except jwt.ExpiredSignatureError:
        return None, 'Token has expired'
    except jwt.InvalidTokenError:
        return None, 'Invalid token'

def generate_class_code(length=6):
    """Generate unique 6-digit class code"""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

def generate_verification_token():
    """Generate email verification token"""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=50))

def generate_reset_token():
    """Generate password reset token"""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=50))

def generate_student_id():
    """Generate unique student ID"""
    return ''.join(random.choices(string.digits, k=8))

def generate_employee_id():
    """Generate unique employee ID"""
    return ''.join(random.choices(string.digits, k=6))