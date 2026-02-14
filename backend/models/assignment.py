from utils.database import mysql
from datetime import datetime

class Assignment:
    """Assignment Model - Handles all assignment-related database operations"""
    
    # ============ CREATE OPERATIONS ============
    
    @staticmethod
    def create(teacher_user_id, assignment_data):
        """Create a new assignment"""
        cursor = mysql.connection.cursor()
        try:
            # Verify teacher owns the class
            cursor.execute("""
                SELECT c.* FROM classes c
                JOIN teacher_profiles tp ON c.teacher_id = tp.id
                WHERE c.id = %s AND tp.user_id = %s
            """, (assignment_data['class_id'], teacher_user_id))
            
            if not cursor.fetchone():
                raise Exception('Class not found or unauthorized')
            
            # Insert assignment
            cursor.execute("""
                INSERT INTO assignments (
                    title, instructions, due_date, points_possible,
                    class_id, late_policy, late_penalty, rubric,
                    is_published, allow_late, max_file_size, allowed_file_types
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                assignment_data['title'],
                assignment_data.get('instructions', ''),
                assignment_data['due_date'],
                assignment_data['points_possible'],
                assignment_data['class_id'],
                assignment_data.get('late_policy', 'no_submissions'),
                assignment_data.get('late_penalty', 0),
                assignment_data.get('rubric'),
                assignment_data.get('is_published', False),
                assignment_data.get('allow_late', False),
                assignment_data.get('max_file_size', 10485760),
                assignment_data.get('allowed_file_types', '.pdf,.doc,.docx,.zip,.jpg,.png')
            ))
            
            mysql.connection.commit()
            assignment_id = cursor.lastrowid
            cursor.close()
            
            return assignment_id
            
        except Exception as e:
            mysql.connection.rollback()
            cursor.close()
            raise e
    
    # ============ READ OPERATIONS ============
    
    @staticmethod
    def find_by_id(assignment_id):
        """Find assignment by ID with class info"""
        cursor = mysql.connection.cursor()
        cursor.execute("""
            SELECT 
                a.*,
                c.name as class_name,
                c.course_code,
                u.name as teacher_name
            FROM assignments a
            JOIN classes c ON a.class_id = c.id
            JOIN teacher_profiles tp ON c.teacher_id = tp.id
            JOIN users u ON tp.user_id = u.id
            WHERE a.id = %s
        """, (assignment_id,))
        assignment = cursor.fetchone()
        cursor.close()
        return assignment
    
    @staticmethod
    def get_by_class(class_id, include_unpublished=False):
        """Get all assignments for a class"""
        cursor = mysql.connection.cursor()
        
        query = """
            SELECT 
                a.*,
                (SELECT COUNT(*) FROM submissions s 
                 WHERE s.assignment_id = a.id) as total_submissions,
                (SELECT COUNT(*) FROM submissions s 
                 WHERE s.assignment_id = a.id AND s.status = 'graded') as graded_submissions
            FROM assignments a
            WHERE a.class_id = %s
        """
        
        if not include_unpublished:
            query += " AND a.is_published = TRUE"
        
        query += " ORDER BY a.due_date ASC"
        
        cursor.execute(query, (class_id,))
        assignments = cursor.fetchall()
        cursor.close()
        
        return assignments
    
    @staticmethod
    def get_upcoming_for_student(student_user_id, days=7):
        """Get upcoming assignments for a student"""
        cursor = mysql.connection.cursor()
        
        cursor.execute("""
            SELECT 
                a.id,
                a.title,
                a.due_date,
                a.points_possible,
                c.id as class_id,
                c.name as class_name,
                c.course_code,
                (SELECT status FROM submissions 
                 WHERE assignment_id = a.id AND student_id = %s) as submission_status
            FROM assignments a
            JOIN classes c ON a.class_id = c.id
            JOIN class_enrollments ce ON c.id = ce.class_id
            JOIN student_profiles sp ON ce.student_id = sp.id
            WHERE sp.user_id = %s 
            AND ce.status = 'approved'
            AND a.is_published = TRUE
            AND a.due_date BETWEEN NOW() AND DATE_ADD(NOW(), INTERVAL %s DAY)
            ORDER BY a.due_date ASC
        """, (student_user_id, student_user_id, days))
        
        assignments = cursor.fetchall()
        cursor.close()
        
        return assignments
    
    @staticmethod
    def get_pending_grading(teacher_user_id):
        """Get all ungraded submissions for a teacher"""
        cursor = mysql.connection.cursor()
        
        cursor.execute("""
            SELECT 
                s.id as submission_id,
                s.submitted_at,
                s.is_late,
                a.id as assignment_id,
                a.title as assignment_title,
                a.due_date,
                a.points_possible,
                c.id as class_id,
                c.name as class_name,
                u.id as student_id,
                u.name as student_name,
                u.email as student_email
            FROM submissions s
            JOIN assignments a ON s.assignment_id = a.id
            JOIN classes c ON a.class_id = c.id
            JOIN teacher_profiles tp ON c.teacher_id = tp.id
            JOIN users u ON s.student_id = u.id
            WHERE tp.user_id = %s 
            AND s.status = 'submitted'
            ORDER BY s.submitted_at ASC
        """, (teacher_user_id,))
        
        submissions = cursor.fetchall()
        cursor.close()
        
        return submissions
    
    # ============ UPDATE OPERATIONS ============
    
    @staticmethod
    def update(assignment_id, teacher_user_id, **kwargs):
        """Update an assignment"""
        cursor = mysql.connection.cursor()
        try:
            # Verify teacher owns the assignment
            cursor.execute("""
                SELECT a.* FROM assignments a
                JOIN classes c ON a.class_id = c.id
                JOIN teacher_profiles tp ON c.teacher_id = tp.id
                WHERE a.id = %s AND tp.user_id = %s
            """, (assignment_id, teacher_user_id))
            
            if not cursor.fetchone():
                raise Exception('Assignment not found or unauthorized')
            
            # Update fields
            update_fields = []
            values = []
            
            allowed_fields = [
                'title', 'instructions', 'due_date', 'points_possible',
                'late_policy', 'late_penalty', 'rubric', 'is_published',
                'allow_late', 'max_file_size', 'allowed_file_types'
            ]
            
            for field in allowed_fields:
                if field in kwargs:
                    update_fields.append(f"{field} = %s")
                    values.append(kwargs[field])
            
            if update_fields:
                query = f"UPDATE assignments SET {', '.join(update_fields)} WHERE id = %s"
                values.append(assignment_id)
                cursor.execute(query, tuple(values))
                mysql.connection.commit()
            
            cursor.close()
            return True
            
        except Exception as e:
            mysql.connection.rollback()
            cursor.close()
            raise e
    
    @staticmethod
    def publish(assignment_id, teacher_user_id, publish=True):
        """Publish or unpublish an assignment"""
        cursor = mysql.connection.cursor()
        try:
            # Verify teacher owns the assignment
            cursor.execute("""
                SELECT a.* FROM assignments a
                JOIN classes c ON a.class_id = c.id
                JOIN teacher_profiles tp ON c.teacher_id = tp.id
                WHERE a.id = %s AND tp.user_id = %s
            """, (assignment_id, teacher_user_id))
            
            if not cursor.fetchone():
                raise Exception('Assignment not found or unauthorized')
            
            cursor.execute("""
                UPDATE assignments 
                SET is_published = %s 
                WHERE id = %s
            """, (publish, assignment_id))
            
            mysql.connection.commit()
            cursor.close()
            
            return True
            
        except Exception as e:
            mysql.connection.rollback()
            cursor.close()
            raise e
    
    # ============ DELETE OPERATIONS ============
    
    @staticmethod
    def delete(assignment_id, teacher_user_id):
        """Delete an assignment"""
        cursor = mysql.connection.cursor()
        try:
            # Verify teacher owns the assignment
            cursor.execute("""
                SELECT a.* FROM assignments a
                JOIN classes c ON a.class_id = c.id
                JOIN teacher_profiles tp ON c.teacher_id = tp.id
                WHERE a.id = %s AND tp.user_id = %s
            """, (assignment_id, teacher_user_id))
            
            if not cursor.fetchone():
                raise Exception('Assignment not found or unauthorized')
            
            cursor.execute("DELETE FROM assignments WHERE id = %s", (assignment_id,))
            mysql.connection.commit()
            cursor.close()
            
            return True
            
        except Exception as e:
            mysql.connection.rollback()
            cursor.close()
            raise e
    
    # ============ STATISTICS ============
    
    @staticmethod
    def get_stats(assignment_id, teacher_user_id):
        """Get assignment statistics"""
        cursor = mysql.connection.cursor()
        try:
            # Verify teacher owns the assignment
            cursor.execute("""
                SELECT a.* FROM assignments a
                JOIN classes c ON a.class_id = c.id
                JOIN teacher_profiles tp ON c.teacher_id = tp.id
                WHERE a.id = %s AND tp.user_id = %s
            """, (assignment_id, teacher_user_id))
            
            if not cursor.fetchone():
                raise Exception('Assignment not found or unauthorized')
            
            stats = {}
            
            # Total enrolled students
            cursor.execute("""
                SELECT COUNT(DISTINCT ce.student_id) as count
                FROM class_enrollments ce
                JOIN assignments a ON ce.class_id = a.class_id
                WHERE a.id = %s AND ce.status = 'approved'
            """, (assignment_id,))
            stats['total_students'] = cursor.fetchone()['count']
            
            # Submission stats
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_submissions,
                    SUM(CASE WHEN status = 'submitted' THEN 1 ELSE 0 END) as pending,
                    SUM(CASE WHEN status = 'graded' THEN 1 ELSE 0 END) as graded,
                    SUM(CASE WHEN is_late = TRUE THEN 1 ELSE 0 END) as late,
                    AVG(grade) as average_grade,
                    MIN(grade) as min_grade,
                    MAX(grade) as max_grade
                FROM submissions
                WHERE assignment_id = %s
            """, (assignment_id,))
            
            submission_stats = cursor.fetchone()
            stats.update(submission_stats)
            
            cursor.close()
            return stats
            
        except Exception as e:
            cursor.close()
            raise e