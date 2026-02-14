from utils.database import mysql
from datetime import date

class TeacherAssignment:
    """Teacher Assignment Model - Assigns teachers to sections"""
    
    @staticmethod
    def create(teacher_id, section_id, is_primary=True):
        """Assign a teacher to a section"""
        cursor = mysql.connection.cursor()
        try:
            cursor.execute("""
                INSERT INTO teacher_assignments (teacher_id, section_id, is_primary, assigned_date)
                VALUES (%s, %s, %s, %s)
            """, (teacher_id, section_id, is_primary, date.today()))
            
            mysql.connection.commit()
            assignment_id = cursor.lastrowid
            cursor.close()
            return assignment_id
        except Exception as e:
            mysql.connection.rollback()
            cursor.close()
            raise e

    @staticmethod
    def get_by_teacher(teacher_id, academic_year=None, semester=None):
        """Get all sections assigned to a teacher"""
        cursor = mysql.connection.cursor()
        query = """
            SELECT 
                ta.*,
                s.id as section_id,
                s.name as section_name,
                s.academic_year,
                s.semester as academic_semester,
                s.capacity,
                s.enrolled_count,
                s.room,
                sub.id as subject_id,
                sub.code as subject_code,
                sub.name as subject_name,
                sub.credits,
                sub.semester,
                c.id as course_id,
                c.name as course_name,
                c.code as course_code,
                (SELECT COUNT(*) FROM enrollments e WHERE e.section_id = s.id AND e.status = 'approved') as student_count
            FROM teacher_assignments ta
            JOIN sections s ON ta.section_id = s.id
            JOIN subjects sub ON s.subject_id = sub.id
            JOIN courses c ON sub.course_id = c.id
            WHERE ta.teacher_id = %s
        """
        params = [teacher_id]
        
        if academic_year:
            query += " AND s.academic_year = %s"
            params.append(academic_year)
        if semester:
            query += " AND s.semester = %s"
            params.append(semester)
            
        query += " ORDER BY c.name, sub.semester"
        
        cursor.execute(query, params)
        assignments = cursor.fetchall()
        cursor.close()
        return assignments

    @staticmethod
    def get_by_section(section_id):
        """Get teacher assigned to a section"""
        cursor = mysql.connection.cursor()
        cursor.execute("""
            SELECT 
                ta.*,
                u.id as teacher_id,
                u.name as teacher_name,
                u.email as teacher_email,
                tp.employee_id
            FROM teacher_assignments ta
            JOIN users u ON ta.teacher_id = u.id
            JOIN teacher_profiles tp ON u.id = tp.user_id
            WHERE ta.section_id = %s
        """, (section_id,))
        teachers = cursor.fetchall()
        cursor.close()
        return teachers

    @staticmethod
    def remove(assignment_id):
        """Remove a teacher assignment"""
        cursor = mysql.connection.cursor()
        try:
            cursor.execute("DELETE FROM teacher_assignments WHERE id = %s", (assignment_id,))
            mysql.connection.commit()
            affected = cursor.rowcount
            cursor.close()
            return affected > 0
        except Exception as e:
            mysql.connection.rollback()
            cursor.close()
            raise e

    @staticmethod
    def get_unassigned_sections(academic_year=None, semester=None):
        """Get sections without a teacher assigned"""
        cursor = mysql.connection.cursor()
        query = """
            SELECT 
                s.*,
                sub.code as subject_code,
                sub.name as subject_name,
                c.name as course_name
            FROM sections s
            JOIN subjects sub ON s.subject_id = sub.id
            JOIN courses c ON sub.course_id = c.id
            WHERE NOT EXISTS (
                SELECT 1 FROM teacher_assignments ta WHERE ta.section_id = s.id
            )
        """
        params = []
        
        if academic_year:
            query += " AND s.academic_year = %s"
            params.append(academic_year)
        if semester:
            query += " AND s.semester = %s"
            params.append(semester)
            
        cursor.execute(query, params)
        sections = cursor.fetchall()
        cursor.close()
        return sections