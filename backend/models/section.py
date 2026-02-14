from utils.database import mysql
from datetime import datetime

class Section:
    """Section Model - Manages class sections (A, B, C) with capacity"""
    
    @staticmethod
    def create(subject_id, name, academic_year, semester, capacity=30, room=None):
        """Create a new section"""
        cursor = mysql.connection.cursor()
        try:
            cursor.execute("""
                INSERT INTO sections (subject_id, name, academic_year, semester, capacity, room)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (subject_id, name, academic_year, semester, capacity, room))
            
            mysql.connection.commit()
            section_id = cursor.lastrowid
            cursor.close()
            return section_id
        except Exception as e:
            mysql.connection.rollback()
            cursor.close()
            raise e

    @staticmethod
    def get_by_id(section_id):
        """Get section by ID with related info"""
        cursor = mysql.connection.cursor()
        cursor.execute("""
            SELECT 
                s.*,
                sub.id as subject_id,
                sub.code as subject_code,
                sub.name as subject_name,
                sub.credits,
                sub.semester as subject_semester,
                c.id as course_id,
                c.name as course_name,
                c.code as course_code,
                (SELECT COUNT(*) FROM enrollments e WHERE e.section_id = s.id AND e.status = 'approved') as enrolled_count
            FROM sections s
            JOIN subjects sub ON s.subject_id = sub.id
            JOIN courses c ON sub.course_id = c.id
            WHERE s.id = %s
        """, (section_id,))
        section = cursor.fetchone()
        cursor.close()
        return section

    @staticmethod
    def get_by_subject(subject_id, academic_year=None, semester=None):
        """Get all sections for a subject"""
        cursor = mysql.connection.cursor()
        query = "SELECT * FROM sections WHERE subject_id = %s"
        params = [subject_id]
        
        if academic_year:
            query += " AND academic_year = %s"
            params.append(academic_year)
        if semester:
            query += " AND semester = %s"
            params.append(semester)
            
        query += " ORDER BY name"
        cursor.execute(query, params)
        sections = cursor.fetchall()
        cursor.close()
        return sections

    @staticmethod
    def get_available(academic_year=None, semester=None):
        """Get all sections with available seats"""
        cursor = mysql.connection.cursor()
        query = """
            SELECT 
                s.*,
                sub.id as subject_id,
                sub.code as subject_code,
                sub.name as subject_name,
                sub.credits,
                c.id as course_id,
                c.name as course_name,
                c.code as course_code,
                (s.capacity - s.enrolled_count) as available_seats,
                u.id as teacher_id,
                u.name as teacher_name
            FROM sections s
            JOIN subjects sub ON s.subject_id = sub.id
            JOIN courses c ON sub.course_id = c.id
            LEFT JOIN teacher_assignments ta ON s.id = ta.section_id
            LEFT JOIN users u ON ta.teacher_id = u.id
            WHERE s.is_active = TRUE AND s.enrolled_count < s.capacity
        """
        params = []
        
        if academic_year:
            query += " AND s.academic_year = %s"
            params.append(academic_year)
        if semester:
            query += " AND s.semester = %s"
            params.append(semester)
            
        query += " ORDER BY c.name, sub.semester, s.name"
        cursor.execute(query, params)
        sections = cursor.fetchall()
        cursor.close()
        return sections

    @staticmethod
    def update(section_id, **kwargs):
        """Update section information"""
        cursor = mysql.connection.cursor()
        try:
            update_fields = []
            values = []
            
            allowed_fields = ['name', 'capacity', 'room', 'is_active']
            for field in allowed_fields:
                if field in kwargs:
                    update_fields.append(f"{field} = %s")
                    values.append(kwargs[field])
            
            if update_fields:
                query = f"UPDATE sections SET {', '.join(update_fields)} WHERE id = %s"
                values.append(section_id)
                cursor.execute(query, tuple(values))
                mysql.connection.commit()
            
            cursor.close()
            return True
        except Exception as e:
            mysql.connection.rollback()
            cursor.close()
            raise e

    @staticmethod
    def increment_enrollment(section_id):
        """Increase enrolled count by 1"""
        cursor = mysql.connection.cursor()
        try:
            cursor.execute("""
                UPDATE sections 
                SET enrolled_count = enrolled_count + 1 
                WHERE id = %s AND enrolled_count < capacity
            """, (section_id,))
            mysql.connection.commit()
            affected = cursor.rowcount
            cursor.close()
            return affected > 0
        except Exception as e:
            mysql.connection.rollback()
            cursor.close()
            raise e

    @staticmethod
    def decrement_enrollment(section_id):
        """Decrease enrolled count by 1"""
        cursor = mysql.connection.cursor()
        try:
            cursor.execute("""
                UPDATE sections 
                SET enrolled_count = enrolled_count - 1 
                WHERE id = %s AND enrolled_count > 0
            """, (section_id,))
            mysql.connection.commit()
            affected = cursor.rowcount
            cursor.close()
            return affected > 0
        except Exception as e:
            mysql.connection.rollback()
            cursor.close()
            raise e

    @staticmethod
    def delete(section_id):
        """Delete a section (only if no enrollments)"""
        cursor = mysql.connection.cursor()
        try:
            # Check if there are any approved enrollments
            cursor.execute("""
                SELECT COUNT(*) as count FROM enrollments 
                WHERE section_id = %s AND status = 'approved'
            """, (section_id,))
            result = cursor.fetchone()
            
            if result['count'] > 0:
                cursor.close()
                raise Exception("Cannot delete section with enrolled students")
            
            cursor.execute("DELETE FROM sections WHERE id = %s", (section_id,))
            mysql.connection.commit()
            cursor.close()
            return True
        except Exception as e:
            mysql.connection.rollback()
            cursor.close()
            raise e