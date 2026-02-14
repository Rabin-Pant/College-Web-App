from utils.database import mysql
from datetime import datetime

class ZoomMeeting:
    """Zoom Meeting Model - Manages online classes"""
    
    @staticmethod
    def create(teacher_id, section_id, topic, meeting_date, start_time, 
               duration_minutes=60, description=None, meeting_link=None, 
               meeting_id=None, password=None):
        """Create a new Zoom meeting"""
        cursor = mysql.connection.cursor()
        try:
            cursor.execute("""
                INSERT INTO zoom_meetings (
                    teacher_id, section_id, topic, description, 
                    meeting_date, start_time, duration_minutes,
                    meeting_link, meeting_id, password
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (teacher_id, section_id, topic, description, 
                  meeting_date, start_time, duration_minutes,
                  meeting_link, meeting_id, password))
            
            mysql.connection.commit()
            meeting_id_db = cursor.lastrowid
            cursor.close()
            return meeting_id_db
        except Exception as e:
            mysql.connection.rollback()
            cursor.close()
            raise e

    @staticmethod
    def get_by_id(meeting_id):
        """Get meeting by ID"""
        cursor = mysql.connection.cursor()
        cursor.execute("""
            SELECT 
                zm.*,
                u.name as teacher_name,
                u.email as teacher_email,
                s.name as section_name,
                sub.code as subject_code,
                sub.name as subject_name,
                c.name as course_name
            FROM zoom_meetings zm
            JOIN users u ON zm.teacher_id = u.id
            JOIN sections s ON zm.section_id = s.id
            JOIN subjects sub ON s.subject_id = sub.id
            JOIN courses c ON sub.course_id = c.id
            WHERE zm.id = %s
        """, (meeting_id,))
        meeting = cursor.fetchone()
        cursor.close()
        return meeting

    @staticmethod
    def get_by_section(section_id, upcoming_only=True):
        """Get meetings for a section"""
        cursor = mysql.connection.cursor()
        query = """
            SELECT * FROM zoom_meetings 
            WHERE section_id = %s
        """
        params = [section_id]
        
        if upcoming_only:
            query += " AND CONCAT(meeting_date, ' ', start_time) >= NOW()"
            
        query += " ORDER BY meeting_date, start_time"
        
        cursor.execute(query, params)
        meetings = cursor.fetchall()
        cursor.close()
        return meetings

    @staticmethod
    def get_by_teacher(teacher_id, upcoming_only=True):
        """Get meetings created by a teacher"""
        cursor = mysql.connection.cursor()
        query = """
            SELECT 
                zm.*,
                s.name as section_name,
                sub.code as subject_code,
                sub.name as subject_name
            FROM zoom_meetings zm
            JOIN sections s ON zm.section_id = s.id
            JOIN subjects sub ON s.subject_id = sub.id
            WHERE zm.teacher_id = %s
        """
        params = [teacher_id]
        
        if upcoming_only:
            query += " AND CONCAT(zm.meeting_date, ' ', zm.start_time) >= NOW()"
            
        query += " ORDER BY zm.meeting_date, zm.start_time"
        
        cursor.execute(query, params)
        meetings = cursor.fetchall()
        cursor.close()
        return meetings

    @staticmethod
    def get_by_student(student_id, upcoming_only=True):
        """Get meetings for a student's enrolled sections"""
        cursor = mysql.connection.cursor()
        query = """
            SELECT 
                zm.*,
                u.name as teacher_name,
                s.name as section_name,
                sub.code as subject_code,
                sub.name as subject_name
            FROM zoom_meetings zm
            JOIN sections s ON zm.section_id = s.id
            JOIN subjects sub ON s.subject_id = sub.id
            JOIN enrollments e ON s.id = e.section_id
            JOIN users u ON zm.teacher_id = u.id
            WHERE e.student_id = %s AND e.status = 'approved'
        """
        params = [student_id]
        
        if upcoming_only:
            query += " AND CONCAT(zm.meeting_date, ' ', zm.start_time) >= NOW()"
            
        query += " ORDER BY zm.meeting_date, zm.start_time"
        
        cursor.execute(query, params)
        meetings = cursor.fetchall()
        cursor.close()
        return meetings

    @staticmethod
    def update(meeting_id, **kwargs):
        """Update meeting details"""
        cursor = mysql.connection.cursor()
        try:
            update_fields = []
            values = []
            
            allowed_fields = ['topic', 'description', 'meeting_date', 'start_time', 
                            'duration_minutes', 'meeting_link', 'meeting_id', 
                            'password', 'recording_link']
            
            for field in allowed_fields:
                if field in kwargs:
                    update_fields.append(f"{field} = %s")
                    values.append(kwargs[field])
            
            if update_fields:
                query = f"UPDATE zoom_meetings SET {', '.join(update_fields)} WHERE id = %s"
                values.append(meeting_id)
                cursor.execute(query, tuple(values))
                mysql.connection.commit()
            
            cursor.close()
            return True
        except Exception as e:
            mysql.connection.rollback()
            cursor.close()
            raise e

    @staticmethod
    def delete(meeting_id, teacher_id):
        """Delete a meeting"""
        cursor = mysql.connection.cursor()
        try:
            cursor.execute("""
                DELETE FROM zoom_meetings 
                WHERE id = %s AND teacher_id = %s
            """, (meeting_id, teacher_id))
            mysql.connection.commit()
            affected = cursor.rowcount
            cursor.close()
            return affected > 0
        except Exception as e:
            mysql.connection.rollback()
            cursor.close()
            raise e

    @staticmethod
    def add_recording(meeting_id, recording_link):
        """Add recording link after meeting"""
        cursor = mysql.connection.cursor()
        try:
            cursor.execute("""
                UPDATE zoom_meetings 
                SET recording_link = %s 
                WHERE id = %s
            """, (recording_link, meeting_id))
            mysql.connection.commit()
            cursor.close()
            return True
        except Exception as e:
            mysql.connection.rollback()
            cursor.close()
            raise e