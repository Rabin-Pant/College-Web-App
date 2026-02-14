# Makes utils a Python package
from utils.database import mysql, get_db, test_connection, init_db
from utils.auth_helpers import (
    hash_password, check_password, generate_token, 
    verify_token, generate_class_code, generate_verification_token
)
from utils.file_handler import (
    save_file, delete_file, get_file_url, 
    allowed_file, human_readable_size
)
from utils.email import send_verification_email, send_password_reset_email
from utils.validators import (
    validate_email, validate_college_email, validate_password,
    validate_class_code, validate_date, sanitize_input
)
from utils.decorators import role_required, teacher_required, student_required, admin_required

__all__ = [
    # Database
    'mysql', 'get_db', 'test_connection', 'init_db',
    
    # Auth
    'hash_password', 'check_password', 'generate_token', 
    'verify_token', 'generate_class_code', 'generate_verification_token',
    
    # File
    'save_file', 'delete_file', 'get_file_url', 
    'allowed_file', 'human_readable_size',
    
    # Email
    'send_verification_email', 'send_password_reset_email',
    
    # Validation
    'validate_email', 'validate_college_email', 'validate_password',
    'validate_class_code', 'validate_date', 'sanitize_input',
    
    # Decorators
    'role_required', 'teacher_required', 'student_required', 'admin_required'
]