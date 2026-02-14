from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from utils.database import mysql
from utils.decorators import teacher_required
from utils.file_handler import save_file
from datetime import datetime

teacher_grading_bp = Blueprint('teacher_grading', __name__)

# ============ GET PENDING GRADING ============

@teacher_grading_bp.route('/pending', methods=['GET'], strict_slashes=False)
@jwt_required()
@teacher_required
def get_pending_grading():
    """Get all submissions pending grading for the teacher's sections"""
    try:
        teacher_id = get_jwt_identity()
        
        cursor = mysql.connection.cursor()
        cursor.execute("""
            SELECT 
                s.id as submission_id,
                s.submitted_at,
                s.is_late,
                s.attempt_number,
                a.id as assignment_id,
                a.title as assignment_title,
                a.due_date,
                a.points_possible,
                sec.id as section_id,
                sec.name as section_name,
                sub.id as subject_id,
                sub.code as subject_code,
                sub.name as subject_name,
                u.id as student_id,
                u.name as student_name,
                u.email as student_email,
                u.profile_pic,
                sp.student_id as student_number,
                sp.major
            FROM submissions s
            JOIN assignments a ON s.assignment_id = a.id
            JOIN sections sec ON a.section_id = sec.id
            JOIN subjects sub ON sec.subject_id = sub.id
            JOIN teacher_assignments ta ON sec.id = ta.section_id
            JOIN users u ON s.student_id = u.id
            JOIN student_profiles sp ON u.id = sp.user_id
            WHERE ta.teacher_id = %s AND s.status = 'submitted'
            ORDER BY s.submitted_at
        """, (teacher_id,))
        
        pending = cursor.fetchall()
        
        # Format datetime objects
        for item in pending:
            if item.get('submitted_at'):
                item['submitted_at'] = str(item['submitted_at'])
            if item.get('due_date'):
                item['due_date'] = str(item['due_date'])
        
        cursor.close()
        
        return jsonify({
            'total': len(pending),
            'submissions': pending
        }), 200
        
    except Exception as e:
        print(f"Error getting pending grading: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


# ============ GET SUBMISSIONS BY ASSIGNMENT ============

@teacher_grading_bp.route('/assignment/<int:assignment_id>', methods=['GET'], strict_slashes=False)
@jwt_required()
@teacher_required
def get_submissions_by_assignment(assignment_id):
    """Get all submissions for a specific assignment"""
    try:
        teacher_id = get_jwt_identity()
        
        cursor = mysql.connection.cursor()
        
        # Verify teacher owns the assignment
        cursor.execute("""
            SELECT a.* FROM assignments a
            JOIN sections sec ON a.section_id = sec.id
            JOIN teacher_assignments ta ON sec.id = ta.section_id
            WHERE a.id = %s AND ta.teacher_id = %s
        """, (assignment_id, teacher_id))
        
        assignment = cursor.fetchone()
        
        if not assignment:
            cursor.close()
            return jsonify({'error': 'Assignment not found or unauthorized'}), 404
        
        # Get all students in the section
        cursor.execute("""
            SELECT 
                u.id as student_id,
                u.name as student_name,
                u.email as student_email,
                u.profile_pic,
                sp.student_id as student_number,
                sp.major
            FROM enrollments e
            JOIN users u ON e.student_id = u.id
            JOIN student_profiles sp ON u.id = sp.user_id
            WHERE e.section_id = %s AND e.status = 'approved'
            ORDER BY u.name
        """, (assignment['section_id'],))
        
        all_students = cursor.fetchall()
        
        # Get submissions
        cursor.execute("""
            SELECT 
                s.id as submission_id,
                s.content,
                s.grade,
                s.feedback,
                s.feedback_file,
                s.status,
                s.submitted_at,
                s.is_late,
                s.attempt_number,
                u.id as student_id,
                u.name as student_name,
                u.email as student_email,
                u.profile_pic,
                sp.student_id as student_number,
                sp.major,
                (SELECT GROUP_CONCAT(a.file_path) FROM attachments a WHERE a.submission_id = s.id) as attachments,
                (SELECT GROUP_CONCAT(a.file_name) FROM attachments a WHERE a.submission_id = s.id) as file_names
            FROM submissions s
            JOIN users u ON s.student_id = u.id
            JOIN student_profiles sp ON u.id = sp.user_id
            WHERE s.assignment_id = %s
            ORDER BY s.submitted_at DESC
        """, (assignment_id,))
        
        submissions = cursor.fetchall()
        
        # Create a map of submissions by student_id
        submission_map = {s['student_id']: s for s in submissions}
        
        # Combine all students with their submissions
        results = []
        for student in all_students:
            student_data = dict(student)
            if student['student_id'] in submission_map:
                student_data.update(submission_map[student['student_id']])
                student_data['has_submitted'] = True
            else:
                student_data['has_submitted'] = False
                student_data['status'] = 'not_submitted'
            results.append(student_data)
        
        # Get assignment details
        cursor.execute("SELECT title, points_possible FROM assignments WHERE id = %s", (assignment_id,))
        assignment_details = cursor.fetchone()
        
        cursor.close()
        
        # Calculate stats
        total = len(results)
        submitted = sum(1 for s in results if s.get('has_submitted'))
        graded = sum(1 for s in results if s.get('status') == 'graded')
        pending = sum(1 for s in results if s.get('status') == 'submitted')
        
        return jsonify({
            'assignment_id': assignment_id,
            'assignment_title': assignment_details['title'],
            'points_possible': assignment_details['points_possible'],
            'total_students': total,
            'submitted': submitted,
            'graded': graded,
            'pending': pending,
            'submissions': results
        }), 200
        
    except Exception as e:
        print(f"Error getting submissions: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


# ============ GET SINGLE SUBMISSION ============

@teacher_grading_bp.route('/<int:submission_id>', methods=['GET'], strict_slashes=False)
@jwt_required()
@teacher_required
def get_submission(submission_id):
    """Get a single submission for grading"""
    try:
        teacher_id = get_jwt_identity()
        
        cursor = mysql.connection.cursor()
        
        cursor.execute("""
            SELECT 
                s.*,
                u.name as student_name,
                u.email as student_email,
                a.title as assignment_title,
                a.points_possible,
                a.instructions,
                a.due_date
            FROM submissions s
            JOIN assignments a ON s.assignment_id = a.id
            JOIN sections sec ON a.section_id = sec.id
            JOIN teacher_assignments ta ON sec.id = ta.section_id
            JOIN users u ON s.student_id = u.id
            WHERE s.id = %s AND ta.teacher_id = %s
        """, (submission_id, teacher_id))
        
        submission = cursor.fetchone()
        
        if not submission:
            cursor.close()
            return jsonify({'error': 'Submission not found or unauthorized'}), 404
        
        # Get attachments
        cursor.execute("SELECT * FROM attachments WHERE submission_id = %s", (submission_id,))
        submission['attachments'] = cursor.fetchall()
        
        cursor.close()
        
        return jsonify(submission), 200
        
    except Exception as e:
        print(f"Error getting submission: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


# ============ GRADE SUBMISSION ============

@teacher_grading_bp.route('/<int:submission_id>', methods=['PUT'], strict_slashes=False)
@jwt_required()
@teacher_required
def grade_submission(submission_id):
    """Grade a submission"""
    try:
        teacher_id = get_jwt_identity()
        data = request.get_json()
        
        if 'grade' not in data:
            return jsonify({'error': 'Grade is required'}), 400
        
        cursor = mysql.connection.cursor()
        
        # Verify teacher has access and get submission details
        cursor.execute("""
            SELECT s.*, a.title as assignment_title, a.points_possible, 
                   u.id as student_user_id, u.name as student_name,
                   sec.id as section_id
            FROM submissions s
            JOIN assignments a ON s.assignment_id = a.id
            JOIN sections sec ON a.section_id = sec.id
            JOIN teacher_assignments ta ON sec.id = ta.section_id
            JOIN users u ON s.student_id = u.id
            WHERE s.id = %s AND ta.teacher_id = %s
        """, (submission_id, teacher_id))
        
        submission = cursor.fetchone()
        
        if not submission:
            cursor.close()
            return jsonify({'error': 'Submission not found or unauthorized'}), 404
        
        # Validate grade
        if float(data['grade']) > submission['points_possible']:
            cursor.close()
            return jsonify({'error': f'Grade cannot exceed {submission["points_possible"]}'}), 400
        
        # Handle feedback file
        feedback_file = request.files.get('feedback_file')
        feedback_file_path = submission['feedback_file']
        
        if feedback_file and feedback_file.filename:
            file_info = save_file(feedback_file, subfolder=f"feedback/{submission_id}")
            if file_info and isinstance(file_info, dict):
                feedback_file_path = file_info['file_path']
        
        # Record in grade history if grade changed
        if submission['grade'] != float(data['grade']):
            cursor.execute("""
                INSERT INTO grade_history (submission_id, previous_grade, new_grade, changed_by)
                VALUES (%s, %s, %s, %s)
            """, (submission_id, submission['grade'], data['grade'], teacher_id))
        
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
        """, (
            data['grade'],
            data.get('feedback', ''),
            feedback_file_path,
            teacher_id,
            submission_id
        ))
        
        # Send notification to student
        try:
            from models.notification import Notification
            Notification.create(
                user_id=submission['student_user_id'],
                notification_type='submission_graded',
                title=f'Assignment Graded: {submission["assignment_title"]}',
                message=f'Your submission has been graded. You received {data["grade"]}/{submission["points_possible"]} points.',
                link=f'/student/assignment/{submission["assignment_id"]}',
                sender_id=teacher_id,
                class_id=submission['section_id'],
                priority='normal'
            )
            print(f"✅ Notification sent to student {submission['student_user_id']}")
        except Exception as e:
            print(f"⚠️ Failed to send notification: {e}")
        
        mysql.connection.commit()
        cursor.close()
        
        return jsonify({'message': 'Submission graded successfully'}), 200
        
    except Exception as e:
        print(f"Error grading submission: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


# ============ BULK GRADE ============

@teacher_grading_bp.route('/bulk', methods=['POST'], strict_slashes=False)
@jwt_required()
@teacher_required
def bulk_grade():
    """Grade multiple submissions at once"""
    try:
        teacher_id = get_jwt_identity()
        data = request.get_json()
        grades = data.get('grades', [])
        
        if not grades:
            return jsonify({'error': 'No grades provided'}), 400
        
        cursor = mysql.connection.cursor()
        success_count = 0
        errors = []
        
        for item in grades:
            try:
                submission_id = item.get('submission_id')
                grade = item.get('grade')
                feedback = item.get('feedback', '')
                
                if not submission_id or grade is None:
                    errors.append(f"Missing data for submission {submission_id}")
                    continue
                
                # Verify teacher has access
                cursor.execute("""
                    SELECT s.*, a.points_possible 
                    FROM submissions s
                    JOIN assignments a ON s.assignment_id = a.id
                    JOIN sections sec ON a.section_id = sec.id
                    JOIN teacher_assignments ta ON sec.id = ta.section_id
                    WHERE s.id = %s AND ta.teacher_id = %s
                """, (submission_id, teacher_id))
                
                submission = cursor.fetchone()
                
                if not submission:
                    errors.append(f"Submission {submission_id} not found or unauthorized")
                    continue
                
                if float(grade) > submission['points_possible']:
                    errors.append(f"Grade for submission {submission_id} exceeds max points")
                    continue
                
                cursor.execute("""
                    UPDATE submissions 
                    SET grade = %s,
                        feedback = %s,
                        status = 'graded',
                        graded_at = NOW(),
                        graded_by = %s
                    WHERE id = %s
                """, (grade, feedback, teacher_id, submission_id))
                
                success_count += 1
                
            except Exception as e:
                errors.append(str(e))
        
        mysql.connection.commit()
        cursor.close()
        
        return jsonify({
            'message': f'Graded {success_count} submissions',
            'success_count': success_count,
            'errors': errors
        }), 200
        
    except Exception as e:
        print(f"Error bulk grading: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


# ============ GET GRADE HISTORY ============

@teacher_grading_bp.route('/history/<int:submission_id>', methods=['GET'], strict_slashes=False)
@jwt_required()
@teacher_required
def get_grade_history(submission_id):
    """Get grade change history for a submission"""
    try:
        teacher_id = get_jwt_identity()
        
        cursor = mysql.connection.cursor()
        
        # Verify teacher has access
        cursor.execute("""
            SELECT s.id FROM submissions s
            JOIN assignments a ON s.assignment_id = a.id
            JOIN sections sec ON a.section_id = sec.id
            JOIN teacher_assignments ta ON sec.id = ta.section_id
            WHERE s.id = %s AND ta.teacher_id = %s
        """, (submission_id, teacher_id))
        
        if not cursor.fetchone():
            cursor.close()
            return jsonify({'error': 'Submission not found or unauthorized'}), 404
        
        # Get history
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

        return jsonify({
            'submission_id': submission_id,
            'history': history
        }), 200

    except Exception as e:
        print(f"Error getting grade history: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500  