from utils.database import mysql
from datetime import datetime, date

class Enrollment:
    """Enrollment Model - Manages student enrollments in sections"""
    
    @staticmethod
    def create(student_id, section_id):
        """Create a new enrollment request"""
        cursor = mysql.connection.cursor()
        try:
            # Check if section has available seats
            cursor.execute("""
                SELECT capacity, enrolled_count FROM sections 
                WHERE id = %s AND is_active = TRUE
            """, (section_id,))
            section = cursor.fetchone()
            
            if not section:
                cursor.close()
                raise Exception("Section not found")
            
            if section['enrolled_count'] >= section['capacity']:
                cursor.close()
                raise Exception("Section is full")
            
            # Check if already enrolled
            cursor.execute("""
                SELECT id FROM enrollments 
                WHERE student_id = %s AND section_id = %s
            """, (student_id, section_id))
            
            if cursor.fetchone():
                cursor.close()
                raise Exception("Already enrolled or pending")
            
            # Create enrollment
            cursor.execute("""
                INSERT INTO enrollments (student_id, section_id, status, enrollment_date)
                VALUES (%s, %s, 'pending', %s)
            """, (student_id, section_id, date.today()))
            
            mysql.connection.commit()
            enrollment_id = cursor.lastrowid
            cursor.close()
            return enrollment_id
        except Exception as e:
            mysql.connection.rollback()
            cursor.close()
            raise e

    @staticmethod
    def approve(enrollment_id, approved_by):
        """Approve a pending enrollment"""
        cursor = mysql.connection.cursor()
        try:
            # Get enrollment details
            cursor.execute("""
                SELECT e.*, s.capacity, s.enrolled_count 
                FROM enrollments e
                JOIN sections s ON e.section_id = s.id
                WHERE e.id = %s
            """, (enrollment_id,))
            enrollment = cursor.fetchone()
            
            if not enrollment:
                cursor.close()
                raise Exception("Enrollment not found")
            
            if enrollment['status'] != 'pending':
                cursor.close()
                raise Exception("Enrollment is not pending")
            
            if enrollment['enrolled_count'] >= enrollment['capacity']:
                cursor.close()
                raise Exception("Section is full")
            
            # Update enrollment status
            cursor.execute("""
                UPDATE enrollments 
                SET status = 'approved', approved_by = %s, approved_date = %s
                WHERE id = %s
            """, (approved_by, date.today(), enrollment_id))
            
            # Increment section enrolled count
            cursor.execute("""
                UPDATE sections 
                SET enrolled_count = enrolled_count + 1 
                WHERE id = %s
            """, (enrollment['section_id'],))
            
            mysql.connection.commit()
            cursor.close()
            return True
        except Exception as e:
            mysql.connection.rollback()
            cursor.close()
            raise e

    @staticmethod
    def reject(enrollment_id, approved_by):
        """Reject a pending enrollment"""
        cursor = mysql.connection.cursor()
        try:
            cursor.execute("""
                UPDATE enrollments 
                SET status = 'rejected', approved_by = %s, approved_date = %s
                WHERE id = %s AND status = 'pending'
            """, (approved_by, date.today(), enrollment_id))
            
            mysql.connection.commit()
            affected = cursor.rowcount
            cursor.close()
            return affected > 0
        except Exception as e:
            mysql.connection.rollback()
            cursor.close()
            raise e

    @staticmethod
    def drop(enrollment_id, student_id):
        """Drop an approved enrollment"""
        cursor = mysql.connection.cursor()
        try:
            # Get section_id before deleting
            cursor.execute("SELECT section_id FROM enrollments WHERE id = %s AND student_id = %s", 
                         (enrollment_id, student_id))
            enrollment = cursor.fetchone()
            
            if not enrollment:
                cursor.close()
                raise Exception("Enrollment not found")
            
            # Update status to dropped
            cursor.execute("""
                UPDATE enrollments 
                SET status = 'dropped' 
                WHERE id = %s
            """, (enrollment_id,))
            
            # Decrement section enrolled count
            cursor.execute("""
                UPDATE sections 
                SET enrolled_count = enrolled_count - 1 
                WHERE id = %s AND enrolled_count > 0
            """, (enrollment['section_id'],))
            
            mysql.connection.commit()
            cursor.close()
            return True
        except Exception as e:
            mysql.connection.rollback()
            cursor.close()
            raise e

    @staticmethod
    def get_by_student(student_id, status=None):
        """Get all enrollments for a student"""
        cursor = mysql.connection.cursor()
        query = """
            SELECT 
                e.*,
                s.id as section_id,
                s.name as section_name,
                s.academic_year,
                s.semester as academic_semester,
                sub.id as subject_id,
                sub.code as subject_code,
                sub.name as subject_name,
                sub.credits,
                c.id as course_id,
                c.name as course_name,
                c.code as course_code,
                u.id as teacher_id,
                u.name as teacher_name
            FROM enrollments e
            JOIN sections s ON e.section_id = s.id
            JOIN subjects sub ON s.subject_id = sub.id
            JOIN courses c ON sub.course_id = c.id
            LEFT JOIN teacher_assignments ta ON s.id = ta.section_id
            LEFT JOIN users u ON ta.teacher_id = u.id
            WHERE e.student_id = %s
        """
        params = [student_id]
        
        if status:
            query += " AND e.status = %s"
            params.append(status)
            
        query += " ORDER BY e.created_at DESC"
        
        cursor.execute(query, params)
        enrollments = cursor.fetchall()
        cursor.close()
        return enrollments

    @staticmethod
    def get_by_section(section_id, status='approved'):
        """Get all students in a section"""
        cursor = mysql.connection.cursor()
        cursor.execute("""
            SELECT 
                e.id as enrollment_id,
                e.enrollment_date,
                e.status,
                u.id as student_id,
                u.name as student_name,
                u.email as student_email,
                u.profile_pic,
                sp.student_id as student_number,
                sp.major
            FROM enrollments e
            JOIN users u ON e.student_id = u.id
            JOIN student_profiles sp ON u.id = sp.user_id
            WHERE e.section_id = %s AND e.status = %s
            ORDER BY u.name
        """, (section_id, status))
        students = cursor.fetchall()
        cursor.close()
        return students

    @staticmethod
    def get_pending_by_teacher(teacher_id):
        """Get all pending enrollments for sections taught by a teacher"""
        cursor = mysql.connection.cursor()
        cursor.execute("""
            SELECT 
                e.id as enrollment_id,
                e.enrollment_date,
                u.id as student_id,
                u.name as student_name,
                u.email as student_email,
                sp.student_id,
                s.id as section_id,
                s.name as section_name,
                sub.id as subject_id,
                sub.code as subject_code,
                sub.name as subject_name,
                c.name as course_name
            FROM enrollments e
            JOIN sections s ON e.section_id = s.id
            JOIN subjects sub ON s.subject_id = sub.id
            JOIN courses c ON sub.course_id = c.id
            JOIN users u ON e.student_id = u.id
            JOIN student_profiles sp ON u.id = sp.user_id
            JOIN teacher_assignments ta ON s.id = ta.section_id
            WHERE ta.teacher_id = %s AND e.status = 'pending'
            ORDER BY e.enrollment_date
        """, (teacher_id,))
        pending = cursor.fetchall()
        cursor.close()
        return pending

    @staticmethod
    def get_pending_by_admin():
        """Get all pending enrollments (admin view)"""
        cursor = mysql.connection.cursor()
        cursor.execute("""
            SELECT 
                e.id as enrollment_id,
                e.enrollment_date,
                u.id as student_id,
                u.name as student_name,
                u.email as student_email,
                sp.student_id,
                s.id as section_id,
                s.name as section_name,
                sub.id as subject_id,
                sub.code as subject_code,
                sub.name as subject_name,
                c.name as course_name,
                tea.teacher_id,
                t.name as teacher_name
            FROM enrollments e
            JOIN sections s ON e.section_id = s.id
            JOIN subjects sub ON s.subject_id = sub.id
            JOIN courses c ON sub.course_id = c.id
            JOIN users u ON e.student_id = u.id
            JOIN student_profiles sp ON u.id = sp.user_id
            LEFT JOIN teacher_assignments ta ON s.id = ta.section_id
            LEFT JOIN users t ON ta.teacher_id = t.id
            WHERE e.status = 'pending'
            ORDER BY e.enrollment_date
        """)
        pending = cursor.fetchall()
        cursor.close()
        return pending