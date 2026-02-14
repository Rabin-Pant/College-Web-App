from utils.database import mysql

class Schedule:
    """Schedule Model - Manages class timetables"""
    
    DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    
    @staticmethod
    def create(section_id, day, start_time, end_time, room=None):
        """Create a schedule entry"""
        cursor = mysql.connection.cursor()
        try:
            if day not in Schedule.DAYS:
                raise Exception(f"Invalid day. Must be one of: {', '.join(Schedule.DAYS)}")
            
            cursor.execute("""
                INSERT INTO schedules (section_id, day, start_time, end_time, room)
                VALUES (%s, %s, %s, %s, %s)
            """, (section_id, day, start_time, end_time, room))
            
            mysql.connection.commit()
            schedule_id = cursor.lastrowid
            cursor.close()
            return schedule_id
        except Exception as e:
            mysql.connection.rollback()
            cursor.close()
            raise e

    @staticmethod
    def get_by_section(section_id):
        """Get schedule for a section"""
        cursor = mysql.connection.cursor()
        cursor.execute("""
            SELECT * FROM schedules 
            WHERE section_id = %s 
            ORDER BY FIELD(day, 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'), start_time
        """, (section_id,))
        schedules = cursor.fetchall()
        cursor.close()
        return schedules

    @staticmethod
    def get_by_teacher(teacher_id, day=None):
        """Get schedule for a teacher's classes"""
        cursor = mysql.connection.cursor()
        query = """
            SELECT 
                sch.*,
                s.id as section_id,
                s.name as section_name,
                sub.code as subject_code,
                sub.name as subject_name,
                c.name as course_name
            FROM schedules sch
            JOIN sections s ON sch.section_id = s.id
            JOIN subjects sub ON s.subject_id = sub.id
            JOIN courses c ON sub.course_id = c.id
            JOIN teacher_assignments ta ON s.id = ta.section_id
            WHERE ta.teacher_id = %s
        """
        params = [teacher_id]
        
        if day:
            query += " AND sch.day = %s"
            params.append(day)
            
        query += " ORDER BY FIELD(sch.day, 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'), sch.start_time"
        
        cursor.execute(query, params)
        schedules = cursor.fetchall()
        cursor.close()
        return schedules

    @staticmethod
    def get_by_student(student_id, day=None):
        """Get schedule for a student's enrolled classes"""
        cursor = mysql.connection.cursor()
        query = """
            SELECT 
                sch.*,
                s.id as section_id,
                s.name as section_name,
                sub.code as subject_code,
                sub.name as subject_name,
                c.name as course_name,
                u.name as teacher_name
            FROM schedules sch
            JOIN sections s ON sch.section_id = s.id
            JOIN subjects sub ON s.subject_id = sub.id
            JOIN courses c ON sub.course_id = c.id
            JOIN enrollments e ON s.id = e.section_id
            LEFT JOIN teacher_assignments ta ON s.id = ta.section_id
            LEFT JOIN users u ON ta.teacher_id = u.id
            WHERE e.student_id = %s AND e.status = 'approved'
        """
        params = [student_id]
        
        if day:
            query += " AND sch.day = %s"
            params.append(day)
            
        query += " ORDER BY FIELD(sch.day, 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'), sch.start_time"
        
        cursor.execute(query, params)
        schedules = cursor.fetchall()
        cursor.close()
        return schedules

    @staticmethod
    def update(schedule_id, **kwargs):
        """Update a schedule entry"""
        cursor = mysql.connection.cursor()
        try:
            update_fields = []
            values = []
            
            allowed_fields = ['day', 'start_time', 'end_time', 'room']
            for field in allowed_fields:
                if field in kwargs:
                    if field == 'day' and kwargs[field] not in Schedule.DAYS:
                        raise Exception(f"Invalid day. Must be one of: {', '.join(Schedule.DAYS)}")
                    update_fields.append(f"{field} = %s")
                    values.append(kwargs[field])
            
            if update_fields:
                query = f"UPDATE schedules SET {', '.join(update_fields)} WHERE id = %s"
                values.append(schedule_id)
                cursor.execute(query, tuple(values))
                mysql.connection.commit()
            
            cursor.close()
            return True
        except Exception as e:
            mysql.connection.rollback()
            cursor.close()
            raise e

    @staticmethod
    def delete(schedule_id):
        """Delete a schedule entry"""
        cursor = mysql.connection.cursor()
        try:
            cursor.execute("DELETE FROM schedules WHERE id = %s", (schedule_id,))
            mysql.connection.commit()
            affected = cursor.rowcount
            cursor.close()
            return affected > 0
        except Exception as e:
            mysql.connection.rollback()
            cursor.close()
            raise e

    @staticmethod
    def check_conflict(section_id, day, start_time, end_time, exclude_id=None):
        """Check if there's a scheduling conflict"""
        cursor = mysql.connection.cursor()
        query = """
            SELECT COUNT(*) as count FROM schedules 
            WHERE section_id = %s AND day = %s 
            AND (
                (start_time <= %s AND end_time > %s) OR
                (start_time < %s AND end_time >= %s) OR
                (start_time >= %s AND end_time <= %s)
            )
        """
        params = [section_id, day, start_time, start_time, end_time, end_time, start_time, end_time]
        
        if exclude_id:
            query += " AND id != %s"
            params.append(exclude_id)
            
        cursor.execute(query, params)
        result = cursor.fetchone()
        cursor.close()
        return result['count'] > 0