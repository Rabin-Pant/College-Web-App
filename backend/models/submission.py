from utils.database import mysql
from datetime import datetime

class Submission:
    """Submission Model - Handles all submission-related database operations"""
    
    # ============ CREATE/UPDATE OPERATIONS ============
    
    @staticmethod
    def submit(assignment_id, student_user_id, text_entry=None, is_late=False):
        """Create or update a submission"""
        cursor = mysql.connection.cursor()
        try:
            # Check if submission exists
            cursor.execute("""
                SELECT * FROM submissions 
                WHERE assignment_id = %s AND student_id = %s
            """, (assignment_id, student_user_id))
            
            existing = cursor.fetchone()
            
            if existing:
                # Update existing submission
                cursor.execute("""
                    UPDATE submissions 
                    SET content = %s, 
                        updated_at = NOW(), 
                        status = %s,
                        is_late = %s,
                        attempt_number = attempt_number + 1
                    WHERE id = %s
                """, (
                    text_entry,
                    'submitted',
                    is_late,
                    existing['id']
                ))
                submission_id = existing['id']
            else:
                # Create new submission
                cursor.execute("""
                    INSERT INTO submissions (
                        assignment_id, student_id, content, status, is_late
                    ) VALUES (%s, %s, %s, %s, %s)
                """, (
                    assignment_id,
                    student_user_id,
                    text_entry,
                    'submitted',
                    is_late
                ))
                submission_id = cursor.lastrowid
            
            mysql.connection.commit()
            cursor.close()
            
            return submission_id
            
        except Exception as e:
            mysql.connection.rollback()
            cursor.close()
            raise e
    
    @staticmethod
    def grade(submission_id, grader_user_id, grade, feedback=None, feedback_file=None):
        """Grade a submission"""
        cursor = mysql.connection.cursor()
        try:
            # Get current submission for history
            cursor.execute("""
                SELECT grade, feedback FROM submissions WHERE id = %s
            """, (submission_id,))
            
            current = cursor.fetchone()
            
            # Update submission
            cursor.execute("""
                UPDATE submissions 
                SET grade = %s,
                    feedback = %s,
                    feedback_file = %s,
                    status = 'graded',
                    graded_at = NOW(),
                    graded_by = %s
                WHERE id = %s
            """, (grade, feedback, feedback_file, grader_user_id, submission_id))
            
            # Record in grade history
            if current and (current['grade'] != grade or current['feedback'] != feedback):
                cursor.execute("""
                    INSERT INTO grade_history (
                        submission_id, previous_grade, new_grade,
                        previous_feedback, new_feedback, changed_by
                    ) VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    submission_id,
                    current['grade'],
                    grade,
                    current['feedback'],
                    feedback,
                    grader_user_id
                ))
            
            mysql.connection.commit()
            cursor.close()
            
            return True
            
        except Exception as e:
            mysql.connection.rollback()
            cursor.close()
            raise e
    
    # ============ READ OPERATIONS ============
    
    @staticmethod
    def find_by_id(submission_id):
        """Find submission by ID with student info"""
        cursor = mysql.connection.cursor()
        cursor.execute("""
            SELECT 
                s.*,
                u.name as student_name,
                u.email as student_email,
                u.profile_pic,
                a.title as assignment_title,
                a.points_possible,
                c.name as class_name
            FROM submissions s
            JOIN users u ON s.student_id = u.id
            JOIN assignments a ON s.assignment_id = a.id
            JOIN classes c ON a.class_id = c.id
            WHERE s.id = %s
        """, (submission_id,))
        submission = cursor.fetchone()
        cursor.close()
        return submission
    
    @staticmethod
    def get_by_assignment(assignment_id):
        """Get all submissions for an assignment"""
        cursor = mysql.connection.cursor()
        cursor.execute("""
            SELECT 
                s.*,
                u.name as student_name,
                u.email as student_email,
                sp.student_id,
                GROUP_CONCAT(a.file_path) as attachments
            FROM submissions s
            JOIN users u ON s.student_id = u.id
            JOIN student_profiles sp ON u.id = sp.user_id
            LEFT JOIN attachments a ON s.id = a.submission_id
            WHERE s.assignment_id = %s
            GROUP BY s.id
            ORDER BY s.submitted_at DESC
        """, (assignment_id,))
        submissions = cursor.fetchall()
        cursor.close()
        return submissions
    
    @staticmethod
    def get_by_student(student_user_id, assignment_id=None):
        """Get submissions by student"""
        cursor = mysql.connection.cursor()
        
        query = """
            SELECT 
                s.*,
                a.title as assignment_title,
                a.due_date,
                a.points_possible,
                c.name as class_name,
                c.course_code
            FROM submissions s
            JOIN assignments a ON s.assignment_id = a.id
            JOIN classes c ON a.class_id = c.id
            WHERE s.student_id = %s
        """
        params = [student_user_id]
        
        if assignment_id:
            query += " AND s.assignment_id = %s"
            params.append(assignment_id)
        
        query += " ORDER BY s.submitted_at DESC"
        
        cursor.execute(query, params)
        submissions = cursor.fetchall()
        cursor.close()
        
        return submissions
    
    @staticmethod
    def get_grade_history(submission_id):
        """Get grade change history for a submission"""
        cursor = mysql.connection.cursor()
        cursor.execute("""
            SELECT 
                gh.*,
                u.name as changed_by_name
            FROM grade_history gh
            JOIN users u ON gh.changed_by = u.id
            WHERE gh.submission_id = %s
            ORDER BY gh.changed_at DESC
        """, (submission_id,))
        history = cursor.fetchall()
        cursor.close()
        return history
    
    # ============ DELETE OPERATIONS ============
    
    @staticmethod
    def delete(submission_id, student_user_id):
        """Delete a submission (only if not graded)"""
        cursor = mysql.connection.cursor()
        try:
            # Check if submission exists and is not graded
            cursor.execute("""
                SELECT * FROM submissions 
                WHERE id = %s AND student_id = %s AND status != 'graded'
            """, (submission_id, student_user_id))
            
            if not cursor.fetchone():
                raise Exception('Submission not found, unauthorized, or already graded')
            
            cursor.execute("DELETE FROM submissions WHERE id = %s", (submission_id,))
            mysql.connection.commit()
            cursor.close()
            
            return True
            
        except Exception as e:
            mysql.connection.rollback()
            cursor.close()
            raise e