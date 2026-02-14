from utils.database import mysql
from datetime import date

class Attendance:
    """Attendance Model - Manages student attendance"""
    
    STATUSES = ['present', 'absent', 'late', 'excused']
    
    @staticmethod
    def mark(section_id, student_id, status, marked_by, attendance_date=None):
        """Mark attendance for a student"""
        if attendance_date is None:
            attendance_date = date.today()
            
        if status not in Attendance.STATUSES:
            raise Exception(f"Invalid status. Must be one of: {', '.join(Attendance.STATUSES)}")
        
        cursor = mysql.connection.cursor()
        try:
            # Check if student is enrolled in the section
            cursor.execute("""
                SELECT id FROM enrollments 
                WHERE section_id = %s AND student_id = %s AND status = 'approved'
            """, (section_id, student_id))
            
            if not cursor.fetchone():
                cursor.close()
                raise Exception("Student is not enrolled in this section")
            
            # Insert or update attendance
            cursor.execute("""
                INSERT INTO attendance (section_id, student_id, date, status, marked_by)
                VALUES (%s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE status = %s, marked_by = %s
            """, (section_id, student_id, attendance_date, status, marked_by, status, marked_by))
            
            mysql.connection.commit()
            affected = cursor.rowcount
            cursor.close()
            return affected > 0
        except Exception as e:
            mysql.connection.rollback()
            cursor.close()
            raise e

    @staticmethod
    def mark_bulk(section_id, attendance_list, marked_by, attendance_date=None):
        """Mark attendance for multiple students"""
        if attendance_date is None:
            attendance_date = date.today()
            
        cursor = mysql.connection.cursor()
        try:
            success_count = 0
            for item in attendance_list:
                student_id = item.get('student_id')
                status = item.get('status')
                
                if status not in Attendance.STATUSES:
                    continue
                
                try:
                    cursor.execute("""
                        INSERT INTO attendance (section_id, student_id, date, status, marked_by)
                        VALUES (%s, %s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE status = %s, marked_by = %s
                    """, (section_id, student_id, attendance_date, status, marked_by, status, marked_by))
                    success_count += 1
                except:
                    pass
            
            mysql.connection.commit()
            cursor.close()
            return success_count
        except Exception as e:
            mysql.connection.rollback()
            cursor.close()
            raise e

    @staticmethod
    def get_by_section_and_date(section_id, attendance_date=None):
        """Get attendance for a section on a specific date"""
        if attendance_date is None:
            attendance_date = date.today()
            
        cursor = mysql.connection.cursor()
        cursor.execute("""
            SELECT 
                a.*,
                u.id as student_id,
                u.name as student_name,
                u.email as student_email,
                sp.student_id as student_number
            FROM attendance a
            JOIN users u ON a.student_id = u.id
            JOIN student_profiles sp ON u.id = sp.user_id
            WHERE a.section_id = %s AND a.date = %s
            ORDER BY u.name
        """, (section_id, attendance_date))
        attendance = cursor.fetchall()
        cursor.close()
        return attendance

    @staticmethod
    def get_by_student(student_id, section_id=None, start_date=None, end_date=None):
        """Get attendance for a student"""
        cursor = mysql.connection.cursor()
        query = """
            SELECT 
                a.*,
                s.name as section_name,
                sub.code as subject_code,
                sub.name as subject_name
            FROM attendance a
            JOIN sections s ON a.section_id = s.id
            JOIN subjects sub ON s.subject_id = sub.id
            WHERE a.student_id = %s
        """
        params = [student_id]
        
        if section_id:
            query += " AND a.section_id = %s"
            params.append(section_id)
        if start_date:
            query += " AND a.date >= %s"
            params.append(start_date)
        if end_date:
            query += " AND a.date <= %s"
            params.append(end_date)
            
        query += " ORDER BY a.date DESC"
        
        cursor.execute(query, params)
        attendance = cursor.fetchall()
        cursor.close()
        return attendance

    @staticmethod
    def get_summary_by_section(section_id, start_date=None, end_date=None):
        """Get attendance summary for a section"""
        cursor = mysql.connection.cursor()
        query = """
            SELECT 
                a.date,
                COUNT(*) as total,
                SUM(CASE WHEN a.status = 'present' THEN 1 ELSE 0 END) as present,
                SUM(CASE WHEN a.status = 'absent' THEN 1 ELSE 0 END) as absent,
                SUM(CASE WHEN a.status = 'late' THEN 1 ELSE 0 END) as late,
                SUM(CASE WHEN a.status = 'excused' THEN 1 ELSE 0 END) as excused
            FROM attendance a
            WHERE a.section_id = %s
        """
        params = [section_id]
        
        if start_date:
            query += " AND a.date >= %s"
            params.append(start_date)
        if end_date:
            query += " AND a.date <= %s"
            params.append(end_date)
            
        query += " GROUP BY a.date ORDER BY a.date DESC"
        
        cursor.execute(query, params)
        summary = cursor.fetchall()
        cursor.close()
        return summary

    @staticmethod
    def get_student_summary(student_id, section_id=None):
        """Get attendance summary for a student"""
        cursor = mysql.connection.cursor()
        query = """
            SELECT 
                COUNT(*) as total_classes,
                SUM(CASE WHEN status = 'present' THEN 1 ELSE 0 END) as present,
                SUM(CASE WHEN status = 'absent' THEN 1 ELSE 0 END) as absent,
                SUM(CASE WHEN status = 'late' THEN 1 ELSE 0 END) as late,
                SUM(CASE WHEN status = 'excused' THEN 1 ELSE 0 END) as excused,
                ROUND(AVG(CASE WHEN status = 'present' THEN 100 
                          WHEN status = 'late' THEN 50 
                          ELSE 0 END), 2) as attendance_percentage
            FROM attendance
            WHERE student_id = %s
        """
        params = [student_id]
        
        if section_id:
            query += " AND section_id = %s"
            params.append(section_id)
            
        cursor.execute(query, params)
        summary = cursor.fetchone()
        cursor.close()
        return summary