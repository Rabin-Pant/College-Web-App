import re
from datetime import datetime

def validate_email(email):
    """Validate email format"""
    if not email or not isinstance(email, str):
        return False
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def validate_college_email(email, domain='@yourcollege.edu'):
    """Validate college email domain"""
    if not email or not isinstance(email, str):
        return False
    return email.lower().endswith(domain.lower())

def validate_password(password):
    """Validate password strength"""
    errors = []
    
    if not password or not isinstance(password, str):
        errors.append("Password is required")
        return False, errors
    
    if len(password) < 8:
        errors.append("Password must be at least 8 characters long")
    
    if not re.search(r'[A-Z]', password):
        errors.append("Password must contain at least one uppercase letter")
    
    if not re.search(r'[a-z]', password):
        errors.append("Password must contain at least one lowercase letter")
    
    if not re.search(r'[0-9]', password):
        errors.append("Password must contain at least one number")
    
    return len(errors) == 0, errors

def validate_class_code(code):
    """Validate 6-digit class code"""
    if not code or not isinstance(code, str):
        return False
    return bool(re.match(r'^[A-Z0-9]{6}$', code.upper()))

def validate_date(date_string):
    """Validate date format (YYYY-MM-DD)"""
    if not date_string or not isinstance(date_string, str):
        return False
    try:
        datetime.strptime(date_string, '%Y-%m-%d')
        return True
    except ValueError:
        return False

def validate_datetime(datetime_string):
    """Validate datetime format"""
    if not datetime_string or not isinstance(datetime_string, str):
        return False
    try:
        datetime.fromisoformat(datetime_string.replace('Z', '+00:00'))
        return True
    except ValueError:
        return False

def sanitize_input(text):
    """Basic input sanitization - remove HTML tags and special chars"""
    if not text or not isinstance(text, str):
        return text
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    # Remove dangerous characters
    text = re.sub(r'[<>"\']', '', text)
    return text.strip()

def validate_required_fields(data, required_fields):
    """Check if all required fields are present"""
    missing = []
    for field in required_fields:
        if field not in data or data[field] is None or data[field] == '':
            missing.append(field)
    return len(missing) == 0, missing

def validate_file_size(file_size, max_size_mb=10):
    """Validate file size"""
    max_size_bytes = max_size_mb * 1024 * 1024
    return file_size <= max_size_bytes

def validate_role(role):
    """Validate user role"""
    valid_roles = ['admin', 'teacher', 'student']
    return role in valid_roles