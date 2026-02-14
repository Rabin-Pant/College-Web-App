from utils.database import mysql
import random
import string
from datetime import datetime

class Class:
    """Class Model - Handles all class-related database operations"""
    
    # ============ HELPER METHODS ============
    
    @staticmethod
    def _generate_class_code(length=6):
        """Generate unique 6-digit class code"""
        while True:
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))
            cursor = mysql.connection.cursor()
            cursor.execute("SELECT id FROM classes WHERE class_code = %s", (code,))
            existing = cursor.fetchone()
            cursor.close()
            if not existing:
                return code
    
    # ============ CREATE OPERATIONS ============
    
    @staticmethod
    def create(teacher_user_id, class_data):
        """Create a new class"""
        cursor = mysql.connection.cursor()
        try:
            # Get teacher profile id
            cursor.execute("""
                SELECT id FROM teacher_profiles 
                WHERE user_id = %s
            """, (teacher_user_id,))
            
            teacher = cursor.fetchone()
            if not teacher:
                raise Exception('Teacher profile not found')
            
            # Generate unique class code
            class_code = Class._generate_class_code()
            
            # Insert class
            cursor.execute("""
                INSERT INTO classes (
                    name, course_code, section, semester, description,
                    cover_image, class_code, teacher_id, allow_pending
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                class_data['name'],
                class_data['course_code'],
                class_data.get('section', ''),
                class_data['semester'],
                class_data.get('description', ''),
                class_data.get('cover_image'),
                class_code,
                teacher['id'],
                class_data.get('allow_pending', False)
            ))
            
            mysql.connection.commit()
            class_id = cursor.lastrowid
            cursor.close()
            
            return {
                'id': class_id,
                'class_code': class_code,
                'name': class_data['name'],
                'course_code': class_data['course_code']
            }
            
        except Exception as e:
            mysql.connection.rollback()
            cursor.close()
            raise e
    
    # ============ READ OPERATIONS ============
    
    @staticmethod
    def find_by_id(class_id):
        """Find class by ID"""
        cursor = mysql.connection.cursor()
        cursor.execute("""
            SELECT 
                c.*,
                u.name as teacher_name,
                u.email as teacher_email,
                tp.employee_id as teacher_employee_id
            FROM classes c
            JOIN teacher_profiles tp ON c.teacher_id = tp.id
            JOIN users u ON tp.user_id = u.id
            WHERE c.id = %s
        """, (class_id,))
        class_data = cursor.fetchone()
        cursor.close()
        return class_data
    
    @staticmethod
    def find_by_code(class_code):
        """Find class by join code"""
        cursor = mysql.connection.cursor()
        cursor.execute("""
            SELECT 
                c.*,
                u.name as teacher_name
            FROM classes c
            JOIN teacher_profiles tp ON c.teacher_id = tp.id
            JOIN users u ON tp.user_id = u.id
            WHERE c.class_code = %s AND c.is_active = TRUE
        """, (class_code,))
        class_data = cursor.fetchone()
        cursor.close()
        return class_data
    
    @staticmethod
    def get_by_teacher(teacher_user_id, include_inactive=False):
        """Get all classes taught by a teacher"""
        cursor = mysql.connection.cursor()
        
        query = """
            SELECT 
                c.*,
                (SELECT COUNT(*) FROM class_enrollments ce 
                 WHERE ce.class_id = c.id AND ce.status = 'approved') as student_count,
                (SELECT COUNT(*) FROM assignments a 
                 WHERE a.class_id = c.id) as assignment_count
            FROM classes c
            JOIN teacher_profiles tp ON c.teacher_id = tp.id
            WHERE tp.user_id = %s
        """
        
        if not include_inactive:
            query += " AND c.is_active = TRUE"
        
        query += " ORDER BY c.created_at DESC"
        
        cursor.execute(query, (teacher_user_id,))
        classes = cursor.fetchall()
        cursor.close()
        
        return classes
    
    @staticmethod
    def get_by_student(student_user_id):
        """Get all classes a student is enrolled in"""
        cursor = mysql.connection.cursor()
        
        cursor.execute("""
            SELECT 
                c.*,
                u.name as teacher_name,
                ce.status as enrollment_status,
                ce.joined_at,
                (SELECT COUNT(*) FROM assignments a 
                 WHERE a.class_id = c.id 
                 AND a.due_date > NOW() 
                 AND a.is_published = TRUE) as pending_assignments
            FROM class_enrollments ce
            JOIN classes c ON ce.class_id = c.id
            JOIN teacher_profiles tp ON c.teacher_id = tp.id
            JOIN users u ON tp.user_id = u.id
            JOIN student_profiles sp ON ce.student_id = sp.id
            WHERE sp.user_id = %s AND ce.status = 'approved'
            ORDER BY ce.joined_at DESC
        """, (student_user_id,))
        
        classes = cursor.fetchall()
        cursor.close()
        
        return classes
    
    @staticmethod
    def get_pending_enrollments(teacher_user_id):
        """Get all pending enrollment requests for a teacher"""
        cursor = mysql.connection.cursor()
        
        cursor.execute("""
            SELECT 
                ce.id as enrollment_id,
                ce.joined_at as requested_at,
                u.id as student_user_id,
                u.name as student_name,
                u.email as student_email,
                sp.student_id,
                sp.major,
                c.id as class_id,
                c.name as class_name,
                c.course_code,
                c.section
            FROM class_enrollments ce
            JOIN classes c ON ce.class_id = c.id
            JOIN teacher_profiles tp ON c.teacher_id = tp.id
            JOIN student_profiles sp ON ce.student_id = sp.id
            JOIN users u ON sp.user_id = u.id
            WHERE tp.user_id = %s AND ce.status = 'pending'
            ORDER BY ce.joined_at DESC
        """, (teacher_user_id,))
        
        pending = cursor.fetchall()
        cursor.close()
        
        return pending
    
    # ============ UPDATE OPERATIONS ============
    
    @staticmethod
    def update(class_id, teacher_user_id, **kwargs):
        """Update class information"""
        cursor = mysql.connection.cursor()
        try:
            # Verify teacher owns the class
            cursor.execute("""
                SELECT c.* FROM classes c
                JOIN teacher_profiles tp ON c.teacher_id = tp.id
                WHERE c.id = %s AND tp.user_id = %s
            """, (class_id, teacher_user_id))
            
            if not cursor.fetchone():
                raise Exception('Unauthorized or class not found')
            
            # Update fields
            update_fields = []
            values = []
            
            allowed_fields = [
                'name', 'section', 'description', 'cover_image', 
                'is_active', 'allow_pending'
            ]
            
            for field in allowed_fields:
                if field in kwargs:
                    update_fields.append(f"{field} = %s")
                    values.append(kwargs[field])
            
            if update_fields:
                query = f"UPDATE classes SET {', '.join(update_fields)} WHERE id = %s"
                values.append(class_id)
                cursor.execute(query, tuple(values))
                mysql.connection.commit()
            
            cursor.close()
            return True
            
        except Exception as e:
            mysql.connection.rollback()
            cursor.close()
            raise e
    
    @staticmethod
    def regenerate_code(class_id, teacher_user_id):
        """Generate new class code"""
        cursor = mysql.connection.cursor()
        try:
            # Verify teacher owns the class
            cursor.execute("""
                SELECT c.* FROM classes c
                JOIN teacher_profiles tp ON c.teacher_id = tp.id
                WHERE c.id = %s AND tp.user_id = %s
            """, (class_id, teacher_user_id))
            
            if not cursor.fetchone():
                raise Exception('Unauthorized or class not found')
            
            new_code = Class._generate_class_code()
            
            cursor.execute("""
                UPDATE classes 
                SET class_code = %s 
                WHERE id = %s
            """, (new_code, class_id))
            
            mysql.connection.commit()
            cursor.close()
            
            return new_code
            
        except Exception as e:
            mysql.connection.rollback()
            cursor.close()
            raise e
    
    # ============ DELETE OPERATIONS ============
    
    @staticmethod
    def delete(class_id, teacher_user_id):
        """Delete a class"""
        cursor = mysql.connection.cursor()
        try:
            # Verify teacher owns the class
            cursor.execute("""
                SELECT c.* FROM classes c
                JOIN teacher_profiles tp ON c.teacher_id = tp.id
                WHERE c.id = %s AND tp.user_id = %s
            """, (class_id, teacher_user_id))
            
            if not cursor.fetchone():
                raise Exception('Unauthorized or class not found')
            
            cursor.execute("DELETE FROM classes WHERE id = %s", (class_id,))
            mysql.connection.commit()
            cursor.close()
            
            return True
            
        except Exception as e:
            mysql.connection.rollback()
            cursor.close()
            raise e
    
    # ============ ENROLLMENT OPERATIONS ============
    
    @staticmethod
    def enroll_student(class_code, student_user_id):
        """Enroll a student in a class"""
        cursor = mysql.connection.cursor()
        try:
            # Find class by code
            cursor.execute("""
                SELECT * FROM classes 
                WHERE class_code = %s AND is_active = TRUE
            """, (class_code,))
            
            class_data = cursor.fetchone()
            if not class_data:
                raise Exception('Invalid class code')
            
            # Get student profile id
            cursor.execute("""
                SELECT id FROM student_profiles 
                WHERE user_id = %s
            """, (student_user_id,))
            
            student = cursor.fetchone()
            if not student:
                raise Exception('Student profile not found')
            
            # Check if already enrolled
            cursor.execute("""
                SELECT * FROM class_enrollments 
                WHERE student_id = %s AND class_id = %s
            """, (student['id'], class_data['id']))
            
            if cursor.fetchone():
                raise Exception('Already enrolled in this class')
            
            # Determine enrollment status
            status = 'approved' if not class_data['allow_pending'] else 'pending'
            
            # Enroll student
            cursor.execute("""
                INSERT INTO class_enrollments (student_id, class_id, status)
                VALUES (%s, %s, %s)
            """, (student['id'], class_data['id'], status))
            
            mysql.connection.commit()
            cursor.close()
            
            return {
                'class_id': class_data['id'],
                'class_name': class_data['name'],
                'status': status
            }
            
        except Exception as e:
            mysql.connection.rollback()
            cursor.close()
            raise e
    
    @staticmethod
    def approve_enrollment(enrollment_id, teacher_user_id):
        """Approve a pending enrollment"""
        cursor = mysql.connection.cursor()
        try:
            # Verify teacher owns the class
            cursor.execute("""
                SELECT ce.* FROM class_enrollments ce
                JOIN classes c ON ce.class_id = c.id
                JOIN teacher_profiles tp ON c.teacher_id = tp.id
                WHERE ce.id = %s AND tp.user_id = %s
            """, (enrollment_id, teacher_user_id))
            
            if not cursor.fetchone():
                raise Exception('Unauthorized or enrollment not found')
            
            cursor.execute("""
                UPDATE class_enrollments 
                SET status = 'approved' 
                WHERE id = %s
            """, (enrollment_id,))
            
            mysql.connection.commit()
            cursor.close()
            
            return True
            
        except Exception as e:
            mysql.connection.rollback()
            cursor.close()
            raise e
    
    @staticmethod
    def reject_enrollment(enrollment_id, teacher_user_id):
        """Reject a pending enrollment"""
        cursor = mysql.connection.cursor()
        try:
            # Verify teacher owns the class
            cursor.execute("""
                SELECT ce.* FROM class_enrollments ce
                JOIN classes c ON ce.class_id = c.id
                JOIN teacher_profiles tp ON c.teacher_id = tp.id
                WHERE ce.id = %s AND tp.user_id = %s
            """, (enrollment_id, teacher_user_id))
            
            if not cursor.fetchone():
                raise Exception('Unauthorized or enrollment not found')
            
            cursor.execute("""
                UPDATE class_enrollments 
                SET status = 'rejected' 
                WHERE id = %s
            """, (enrollment_id,))
            
            mysql.connection.commit()
            cursor.close()
            
            return True
            
        except Exception as e:
            mysql.connection.rollback()
            cursor.close()
            raise e
    
    @staticmethod
    def remove_student(class_id, student_user_id, teacher_user_id):
        """Remove a student from class"""
        cursor = mysql.connection.cursor()
        try:
            # Verify teacher owns the class
            cursor.execute("""
                SELECT c.* FROM classes c
                JOIN teacher_profiles tp ON c.teacher_id = tp.id
                WHERE c.id = %s AND tp.user_id = %s
            """, (class_id, teacher_user_id))
            
            if not cursor.fetchone():
                raise Exception('Unauthorized or class not found')
            
            # Get student profile id
            cursor.execute("""
                SELECT id FROM student_profiles 
                WHERE user_id = %s
            """, (student_user_id,))
            
            student = cursor.fetchone()
            if not student:
                raise Exception('Student not found')
            
            # Remove enrollment
            cursor.execute("""
                DELETE FROM class_enrollments 
                WHERE class_id = %s AND student_id = %s
            """, (class_id, student['id']))
            
            mysql.connection.commit()
            cursor.close()
            
            return True
            
        except Exception as e:
            mysql.connection.rollback()
            cursor.close()
            raise e
    
    # ============ STATISTICS ============
    
    @staticmethod
    def get_stats(class_id, teacher_user_id):
        """Get class statistics"""
        cursor = mysql.connection.cursor()
        try:
            # Verify teacher owns the class
            cursor.execute("""
                SELECT c.* FROM classes c
                JOIN teacher_profiles tp ON c.teacher_id = tp.id
                WHERE c.id = %s AND tp.user_id = %s
            """, (class_id, teacher_user_id))
            
            if not cursor.fetchone():
                raise Exception('Unauthorized or class not found')
            
            stats = {}
            
            # Student count
            cursor.execute("""
                SELECT COUNT(*) as count FROM class_enrollments
                WHERE class_id = %s AND status = 'approved'
            """, (class_id,))
            stats['total_students'] = cursor.fetchone()['count']
            
            # Assignment stats
            cursor.execute("""
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN due_date > NOW() THEN 1 ELSE 0 END) as upcoming,
                    SUM(CASE WHEN is_published = TRUE THEN 1 ELSE 0 END) as published
                FROM assignments
                WHERE class_id = %s
            """, (class_id,))
            assignment_stats = cursor.fetchone()
            stats['assignments'] = assignment_stats
            
            # Submission stats
            cursor.execute("""
                SELECT 
                    COUNT(DISTINCT s.id) as total,
                    SUM(CASE WHEN s.status = 'submitted' THEN 1 ELSE 0 END) as pending,
                    SUM(CASE WHEN s.status = 'graded' THEN 1 ELSE 0 END) as graded,
                    AVG(s.grade) as average_grade
                FROM submissions s
                JOIN assignments a ON s.assignment_id = a.id
                WHERE a.class_id = %s
            """, (class_id,))
            stats['submissions'] = cursor.fetchone()
            
            # Material count
            cursor.execute("""
                SELECT COUNT(*) as count FROM materials
                WHERE class_id = %s
            """, (class_id,))
            stats['materials'] = cursor.fetchone()['count']
            
            cursor.close()
            return stats
            
        except Exception as e:
            cursor.close()
            raise e
    
    @staticmethod
    def get_roster(class_id, teacher_user_id):
        """Get full class roster with student details"""
        cursor = mysql.connection.cursor()
        try:
            # Verify teacher owns the class
            cursor.execute("""
                SELECT c.* FROM classes c
                JOIN teacher_profiles tp ON c.teacher_id = tp.id
                WHERE c.id = %s AND tp.user_id = %s
            """, (class_id, teacher_user_id))
            
            if not cursor.fetchone():
                raise Exception('Unauthorized or class not found')
            
            cursor.execute("""
                SELECT 
                    u.id,
                    u.name,
                    u.email,
                    u.profile_pic,
                    sp.student_id,
                    sp.major,
                    sp.enrollment_year,
                    ce.status,
                    ce.joined_at,
                    (SELECT COUNT(*) FROM submissions s
                     JOIN assignments a ON s.assignment_id = a.id
                     WHERE a.class_id = %s AND s.student_id = u.id) as submissions_made,
                    (SELECT AVG(s.grade) FROM submissions s
                     JOIN assignments a ON s.assignment_id = a.id
                     WHERE a.class_id = %s AND s.student_id = u.id) as average_grade
                FROM class_enrollments ce
                JOIN student_profiles sp ON ce.student_id = sp.id
                JOIN users u ON sp.user_id = u.id
                WHERE ce.class_id = %s
                ORDER BY ce.status, u.name
            """, (class_id, class_id, class_id))
            
            students = cursor.fetchall()
            cursor.close()
            
            return students
            
        except Exception as e:
            cursor.close()
            raise e