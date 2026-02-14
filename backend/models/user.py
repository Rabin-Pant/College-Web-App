from utils.database import mysql
from werkzeug.security import generate_password_hash, check_password_hash
import random
import string
from datetime import datetime, timedelta

class User:
    """User Model - Handles all user-related database operations"""
    
    # ============ CREATE OPERATIONS ============
    
    @staticmethod
    def create(email, password, name, role, **kwargs):
        """Create a new user"""
        cursor = mysql.connection.cursor()
        try:
            # Hash password
            hashed_password = generate_password_hash(password)
            
            # Generate verification token
            verification_token = ''.join(random.choices(string.ascii_letters + string.digits, k=50))
            
            # Insert user
            cursor.execute("""
                INSERT INTO users (
                    email, password, role, name, college_email, 
                    verification_token, department, profile_pic, bio
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                email,
                hashed_password,
                role,
                name,
                kwargs.get('college_email', email),
                verification_token,
                kwargs.get('department'),
                kwargs.get('profile_pic'),
                kwargs.get('bio')
            ))
            
            mysql.connection.commit()
            user_id = cursor.lastrowid
            
            # Create role-specific profile
            if role == 'teacher':
                employee_id = ''.join(random.choices(string.digits, k=6))
                cursor.execute("""
                    INSERT INTO teacher_profiles (user_id, employee_id, department, office_hours, qualifications)
                    VALUES (%s, %s, %s, %s, %s)
                """, (
                    user_id,
                    employee_id,
                    kwargs.get('department', 'General'),
                    kwargs.get('office_hours'),
                    kwargs.get('qualifications')
                ))
                
            elif role == 'student':
                student_id = ''.join(random.choices(string.digits, k=8))
                cursor.execute("""
                    INSERT INTO student_profiles (
                        user_id, student_id, enrollment_year, major, minor, current_semester
                    ) VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    user_id,
                    student_id,
                    kwargs.get('enrollment_year', datetime.now().year),
                    kwargs.get('major', 'Undeclared'),
                    kwargs.get('minor'),
                    kwargs.get('current_semester', 1)
                ))
            
            mysql.connection.commit()
            cursor.close()
            
            return {
                'user_id': user_id,
                'verification_token': verification_token,
                'email': email,
                'name': name,
                'role': role
            }
            
        except Exception as e:
            mysql.connection.rollback()
            cursor.close()
            raise e
    
    # ============ READ OPERATIONS ============
    
    @staticmethod
    def find_by_id(user_id):
        """Find user by ID"""
        cursor = mysql.connection.cursor()
        cursor.execute("""
            SELECT id, email, name, role, profile_pic, bio, 
                   department, email_verified, created_at
            FROM users WHERE id = %s
        """, (user_id,))
        user = cursor.fetchone()
        cursor.close()
        return user
    
    @staticmethod
    def find_by_email(email):
        """Find user by email"""
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        cursor.close()
        return user
    
    @staticmethod
    def find_by_verification_token(token):
        """Find user by verification token"""
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM users WHERE verification_token = %s", (token,))
        user = cursor.fetchone()
        cursor.close()
        return user
    
    @staticmethod
    def find_by_reset_token(token):
        """Find user by password reset token"""
        cursor = mysql.connection.cursor()
        cursor.execute("""
            SELECT * FROM users 
            WHERE reset_token = %s AND reset_token_expiry > NOW()
        """, (token,))
        user = cursor.fetchone()
        cursor.close()
        return user
    
    @staticmethod
    def get_all(filters=None, limit=100, offset=0):
        """Get all users with optional filters"""
        cursor = mysql.connection.cursor()
        
        query = """
            SELECT 
                u.id, u.email, u.name, u.role, u.profile_pic,
                u.email_verified, u.created_at,
                tp.employee_id,
                sp.student_id, sp.major
            FROM users u
            LEFT JOIN teacher_profiles tp ON u.id = tp.user_id
            LEFT JOIN student_profiles sp ON u.id = sp.user_id
            WHERE 1=1
        """
        params = []
        
        if filters:
            if filters.get('role'):
                query += " AND u.role = %s"
                params.append(filters['role'])
            
            if filters.get('verified') is not None:
                query += " AND u.email_verified = %s"
                params.append(filters['verified'])
            
            if filters.get('search'):
                query += " AND (u.name LIKE %s OR u.email LIKE %s)"
                params.append(f'%{filters["search"]}%')
                params.append(f'%{filters["search"]}%')
        
        query += " ORDER BY u.created_at DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])
        
        cursor.execute(query, params)
        users = cursor.fetchall()
        cursor.close()
        
        return users
    
    @staticmethod
    def count(filters=None):
        """Count total users with filters"""
        cursor = mysql.connection.cursor()
        
        query = "SELECT COUNT(*) as count FROM users u WHERE 1=1"
        params = []
        
        if filters:
            if filters.get('role'):
                query += " AND u.role = %s"
                params.append(filters['role'])
            
            if filters.get('verified') is not None:
                query += " AND u.email_verified = %s"
                params.append(filters['verified'])
        
        cursor.execute(query, params)
        count = cursor.fetchone()['count']
        cursor.close()
        
        return count
    
    # ============ UPDATE OPERATIONS ============
    
    @staticmethod
    def update(user_id, **kwargs):
        """Update user information"""
        cursor = mysql.connection.cursor()
        try:
            update_fields = []
            values = []
            
            allowed_fields = ['name', 'bio', 'profile_pic', 'department']
            for field in allowed_fields:
                if field in kwargs:
                    update_fields.append(f"{field} = %s")
                    values.append(kwargs[field])
            
            if update_fields:
                query = f"UPDATE users SET {', '.join(update_fields)} WHERE id = %s"
                values.append(user_id)
                cursor.execute(query, tuple(values))
                mysql.connection.commit()
            
            cursor.close()
            return True
            
        except Exception as e:
            mysql.connection.rollback()
            cursor.close()
            raise e
    
    @staticmethod
    def verify_email(user_id):
        """Mark email as verified"""
        cursor = mysql.connection.cursor()
        try:
            cursor.execute("""
                UPDATE users 
                SET email_verified = TRUE, verification_token = NULL 
                WHERE id = %s
            """, (user_id,))
            mysql.connection.commit()
            cursor.close()
            return True
        except Exception as e:
            mysql.connection.rollback()
            cursor.close()
            raise e
    
    @staticmethod
    def change_password(user_id, new_password):
        """Change user password"""
        cursor = mysql.connection.cursor()
        try:
            hashed_password = generate_password_hash(new_password)
            cursor.execute("""
                UPDATE users 
                SET password = %s, reset_token = NULL, reset_token_expiry = NULL
                WHERE id = %s
            """, (hashed_password, user_id))
            mysql.connection.commit()
            cursor.close()
            return True
        except Exception as e:
            mysql.connection.rollback()
            cursor.close()
            raise e
    
    @staticmethod
    def set_reset_token(email):
        """Generate and set password reset token"""
        cursor = mysql.connection.cursor()
        try:
            # Generate token
            reset_token = ''.join(random.choices(string.ascii_letters + string.digits, k=50))
            expiry = datetime.now() + timedelta(hours=24)
            
            cursor.execute("""
                UPDATE users 
                SET reset_token = %s, reset_token_expiry = %s
                WHERE email = %s
            """, (reset_token, expiry, email))
            
            mysql.connection.commit()
            cursor.close()
            
            return reset_token
            
        except Exception as e:
            mysql.connection.rollback()
            cursor.close()
            raise e
    
    # ============ DELETE OPERATIONS ============
    
    @staticmethod
    def delete(user_id):
        """Delete a user"""
        cursor = mysql.connection.cursor()
        try:
            cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
            mysql.connection.commit()
            cursor.close()
            return True
        except Exception as e:
            mysql.connection.rollback()
            cursor.close()
            raise e
    
    # ============ AUTHENTICATION ============
    
    @staticmethod
    def authenticate(email, password):
        """Verify user credentials"""
        user = User.find_by_email(email)
        
        if user and check_password_hash(user['password'], password):
            if user['email_verified']:
                return user
            else:
                raise Exception('Email not verified')
        return None
    
    # ============ ROLE-SPECIFIC METHODS ============
    
    @staticmethod
    def get_teacher_profile(user_id):
        """Get teacher profile with user info"""
        cursor = mysql.connection.cursor()
        cursor.execute("""
            SELECT 
                u.id, u.email, u.name, u.profile_pic, u.bio,
                tp.employee_id, tp.department, tp.office_hours, tp.qualifications,
                tp.created_at as profile_created
            FROM users u
            JOIN teacher_profiles tp ON u.id = tp.user_id
            WHERE u.id = %s AND u.role = 'teacher'
        """, (user_id,))
        profile = cursor.fetchone()
        cursor.close()
        return profile
    
    @staticmethod
    def get_student_profile(user_id):
        """Get student profile with user info"""
        cursor = mysql.connection.cursor()
        cursor.execute("""
            SELECT 
                u.id, u.email, u.name, u.profile_pic, u.bio,
                sp.student_id, sp.enrollment_year, sp.major, sp.minor,
                sp.current_semester, sp.advisor_name
            FROM users u
            JOIN student_profiles sp ON u.id = sp.user_id
            WHERE u.id = %s AND u.role = 'student'
        """, (user_id,))
        profile = cursor.fetchone()
        cursor.close()
        return profile
    
    @staticmethod
    def update_teacher_profile(user_id, **kwargs):
        """Update teacher profile"""
        cursor = mysql.connection.cursor()
        try:
            update_fields = []
            values = []
            
            allowed_fields = ['office_hours', 'qualifications', 'department']
            for field in allowed_fields:
                if field in kwargs:
                    update_fields.append(f"{field} = %s")
                    values.append(kwargs[field])
            
            if update_fields:
                query = f"UPDATE teacher_profiles SET {', '.join(update_fields)} WHERE user_id = %s"
                values.append(user_id)
                cursor.execute(query, tuple(values))
                mysql.connection.commit()
            
            cursor.close()
            return True
            
        except Exception as e:
            mysql.connection.rollback()
            cursor.close()
            raise e
    
    @staticmethod
    def update_student_profile(user_id, **kwargs):
        """Update student profile"""
        cursor = mysql.connection.cursor()
        try:
            update_fields = []
            values = []
            
            allowed_fields = ['major', 'minor', 'current_semester', 'advisor_name']
            for field in allowed_fields:
                if field in kwargs:
                    update_fields.append(f"{field} = %s")
                    values.append(kwargs[field])
            
            if update_fields:
                query = f"UPDATE student_profiles SET {', '.join(update_fields)} WHERE user_id = %s"
                values.append(user_id)
                cursor.execute(query, tuple(values))
                mysql.connection.commit()
            
            cursor.close()
            return True
            
        except Exception as e:
            mysql.connection.rollback()
            cursor.close()
            raise e