from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from utils.database import mysql
from utils.decorators import student_required
from utils.file_handler import save_file
from datetime import datetime
import os

student_assignments_bp = Blueprint('student_assignments', __name__)

# ============ GET UPCOMING ASSIGNMENTS (for dashboard) ============

@student_assignments_bp.route('/upcoming', methods=['GET'], strict_slashes=False)
@jwt_required()
@student_required
def get_upcoming_assignments():
    """Get upcoming assignments for the student"""
    try:
        student_id = get_jwt_identity()
        
        cursor = mysql.connection.cursor()
        cursor.execute("""
            SELECT 
                a.id,
                a.title,
                a.due_date,
                a.points_possible,
                s.id as section_id,
                s.name as section_name,
                sub.id as subject_id,
                sub.code as subject_code,
                sub.name as subject_name,
                c.id as course_id,
                c.name as course_name,
                c.code as course_code,
                (SELECT status FROM submissions WHERE assignment_id = a.id AND student_id = %s) as submission_status
            FROM assignments a
            JOIN sections s ON a.section_id = s.id
            JOIN subjects sub ON s.subject_id = sub.id
            JOIN courses c ON sub.course_id = c.id
            JOIN enrollments e ON s.id = e.section_id
            WHERE e.student_id = %s AND e.status = 'approved'
                AND a.due_date > NOW()
                AND a.is_published = TRUE
            ORDER BY a.due_date
            LIMIT 10
        """, (student_id, student_id))
        
        rows = cursor.fetchall()
        
        # Convert datetime objects to strings
        assignments = []
        for row in rows:
            assignment_dict = dict(row)
            if assignment_dict.get('due_date'):
                assignment_dict['due_date'] = str(assignment_dict['due_date'])
            assignments.append(assignment_dict)
        
        cursor.close()
        
        return jsonify({'assignments': assignments}), 200
        
    except Exception as e:
        print(f"Error getting upcoming assignments: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


# ============ GET ASSIGNMENTS BY SECTION ============

@student_assignments_bp.route('/section/<int:section_id>', methods=['GET'], strict_slashes=False)
@jwt_required()
@student_required
def get_section_assignments(section_id):
    """Get all assignments for a section"""
    try:
        student_id = get_jwt_identity()
        
        cursor = mysql.connection.cursor()
        
        # Verify student is enrolled in this section
        cursor.execute("""
            SELECT id FROM enrollments 
            WHERE student_id = %s AND section_id = %s AND status = 'approved'
        """, (student_id, section_id))
        
        if not cursor.fetchone():
            cursor.close()
            return jsonify({'error': 'You are not enrolled in this section'}), 403
        
        # Get assignments
        cursor.execute("""
            SELECT 
                a.id,
                a.title,
                a.instructions,
                a.due_date,
                a.points_possible,
                a.late_policy,
                a.late_penalty,
                a.allow_late,
                a.is_published,
                a.created_at,
                (SELECT status FROM submissions 
                 WHERE assignment_id = a.id AND student_id = %s) as submission_status,
                (SELECT grade FROM submissions 
                 WHERE assignment_id = a.id AND student_id = %s) as grade,
                (SELECT feedback FROM submissions 
                 WHERE assignment_id = a.id AND student_id = %s) as feedback
            FROM assignments a
            WHERE a.section_id = %s AND a.is_published = TRUE
            ORDER BY a.due_date
        """, (student_id, student_id, student_id, section_id))
        
        rows = cursor.fetchall()
        
        # Convert datetime objects
        assignments = []
        for row in rows:
            assignment_dict = dict(row)
            if assignment_dict.get('due_date'):
                assignment_dict['due_date'] = str(assignment_dict['due_date'])
            assignments.append(assignment_dict)
        
        cursor.close()
        
        return jsonify({'assignments': assignments}), 200
        
    except Exception as e:
        print(f"Error getting assignments: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


# ============ GET SINGLE ASSIGNMENT DETAILS ============

@student_assignments_bp.route('/<int:assignment_id>', methods=['GET'], strict_slashes=False)
@jwt_required()
@student_required
def get_assignment(assignment_id):
    """Get detailed assignment information"""
    try:
        student_id = get_jwt_identity()
        
        cursor = mysql.connection.cursor()
        
        # Get assignment details with enrollment check
        cursor.execute("""
            SELECT 
                a.*,
                s.id as section_id,
                s.name as section_name,
                sub.id as subject_id,
                sub.code as subject_code,
                sub.name as subject_name,
                c.id as course_id,
                c.name as course_name,
                c.code as course_code,
                u.id as teacher_id,
                u.name as teacher_name,
                u.email as teacher_email
            FROM assignments a
            JOIN sections s ON a.section_id = s.id
            JOIN subjects sub ON s.subject_id = sub.id
            JOIN courses c ON sub.course_id = c.id
            JOIN teacher_assignments ta ON s.id = ta.section_id
            JOIN users u ON ta.teacher_id = u.id
            JOIN enrollments e ON s.id = e.section_id
            WHERE a.id = %s AND e.student_id = %s AND e.status = 'approved'
        """, (assignment_id, student_id))
        
        assignment = cursor.fetchone()
        
        if not assignment:
            cursor.close()
            return jsonify({'error': 'Assignment not found or you do not have access'}), 404
        
        # Get attachments
        cursor.execute("""
            SELECT id, file_name, file_path, file_type, file_size, uploaded_at
            FROM attachments 
            WHERE assignment_id = %s
        """, (assignment_id,))
        
        attachments = cursor.fetchall()
        assignment['attachments'] = attachments
        
        cursor.close()
        
        return jsonify({'assignment': assignment}), 200
        
    except Exception as e:
        print(f"Error getting assignment: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


# ============ GET STUDENT'S SUBMISSION FOR AN ASSIGNMENT ============

@student_assignments_bp.route('/<int:assignment_id>/submissions', methods=['GET'], strict_slashes=False)
@jwt_required()
@student_required
def get_my_submission(assignment_id):
    """Get current student's submission for an assignment"""
    try:
        student_id = get_jwt_identity()
        
        cursor = mysql.connection.cursor()
        
        # Get submission using only columns that exist
        cursor.execute("""
            SELECT 
                s.id,
                s.content,
                s.grade,
                s.feedback,
                s.feedback_file,
                s.status,
                s.submitted_at,
                s.updated_at,
                s.is_late,
                s.attempt_number
            FROM submissions s
            WHERE s.assignment_id = %s AND s.student_id = %s
        """, (assignment_id, student_id))
        
        submission = cursor.fetchone()
        
        if submission:
            # Get attachments
            cursor.execute("""
                SELECT 
                    id,
                    file_name,
                    file_path,
                    file_type,
                    file_size,
                    uploaded_at
                FROM attachments 
                WHERE submission_id = %s
            """, (submission['id'],))
            
            attachments = cursor.fetchall()
            submission['attachments'] = attachments
            submission['file_names'] = [a['file_name'] for a in attachments] if attachments else []
        
        cursor.close()
        
        if not submission:
            return jsonify({'submission': None}), 200
        
        return jsonify({'submission': submission}), 200
        
    except Exception as e:
        print(f"Error getting submission: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

# ============ SUBMIT ASSIGNMENT ============

@student_assignments_bp.route('/<int:assignment_id>/submit', methods=['POST'], strict_slashes=False)
@jwt_required()
@student_required
def submit_assignment(assignment_id):
    """Submit assignment work"""
    try:
        student_id = get_jwt_identity()
        
        # Check if assignment exists and is published
        cursor = mysql.connection.cursor()
        cursor.execute("""
            SELECT a.* FROM assignments a
            WHERE a.id = %s AND a.is_published = TRUE
        """, (assignment_id,))
        
        assignment = cursor.fetchone()
        
        if not assignment:
            cursor.close()
            return jsonify({'error': 'Assignment not found or not published'}), 404
        
        # Check if student is enrolled in the section
        cursor.execute("""
            SELECT e.id FROM enrollments e
            WHERE e.section_id = %s AND e.student_id = %s AND e.status = 'approved'
        """, (assignment['section_id'], student_id))
        
        if not cursor.fetchone():
            cursor.close()
            return jsonify({'error': 'You are not enrolled in this section'}), 403
        
        # Check if already submitted and if resubmission is allowed
        cursor.execute("""
            SELECT * FROM submissions 
            WHERE assignment_id = %s AND student_id = %s
        """, (assignment_id, student_id))
        
        existing = cursor.fetchone()
        
        # Handle text entry
        text_entry = request.form.get('text_entry', '')
        
        # Handle file uploads
        files = request.files.getlist('files')
        
        # Check if submission is late
        is_late = datetime.now() > assignment['due_date']
        
        submission_id = None
        
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
                student_id,
                text_entry,
                'submitted',
                is_late
            ))
            submission_id = cursor.lastrowid
        
        # Save file attachments
        saved_files = []
        if files:
            for file in files:
                if file and file.filename:
                    file_info = save_file(file, subfolder=f"submissions/{assignment_id}/{student_id}")
                    if file_info and isinstance(file_info, dict):
                        cursor.execute("""
                            INSERT INTO attachments (
                                file_name, file_path, file_type, file_size, submission_id
                            ) VALUES (%s, %s, %s, %s, %s)
                        """, (
                            file_info['file_name'],
                            file_info['file_path'],
                            file_info['file_type'],
                            file_info['file_size'],
                            submission_id
                        ))
                        saved_files.append(file_info['file_name'])
        
        mysql.connection.commit()
        cursor.close()
        
        return jsonify({
            'message': 'Assignment submitted successfully',
            'submission_id': submission_id,
            'is_late': is_late,
            'files_uploaded': len(saved_files)
        }), 200
        
    except Exception as e:
        print(f"Error submitting assignment: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


# ============ UPDATE SUBMISSION (EDIT BEFORE DEADLINE) ============

@student_assignments_bp.route('/<int:assignment_id>/submissions/<int:submission_id>', methods=['PUT'], strict_slashes=False)
@jwt_required()
@student_required
def update_submission(assignment_id, submission_id):
    """Update submission before deadline"""
    try:
        student_id = get_jwt_identity()
        
        cursor = mysql.connection.cursor()
        
        # Check if submission belongs to student and assignment
        cursor.execute("""
            SELECT s.*, a.due_date 
            FROM submissions s
            JOIN assignments a ON s.assignment_id = a.id
            WHERE s.id = %s AND s.student_id = %s AND s.assignment_id = %s
        """, (submission_id, student_id, assignment_id))
        
        submission = cursor.fetchone()
        
        if not submission:
            cursor.close()
            return jsonify({'error': 'Submission not found'}), 404
        
        # Check if deadline has passed
        if datetime.now() > submission['due_date']:
            cursor.close()
            return jsonify({'error': 'Cannot edit submission after deadline'}), 400
        
        # Check if already graded
        if submission['status'] == 'graded':
            cursor.close()
            return jsonify({'error': 'Cannot edit graded submission'}), 400
        
        # Update text entry
        text_entry = request.form.get('text_entry', '')
        
        cursor.execute("""
            UPDATE submissions 
            SET content = %s, updated_at = NOW()
            WHERE id = %s
        """, (text_entry, submission_id))
        
        mysql.connection.commit()
        cursor.close()
        
        return jsonify({'message': 'Submission updated successfully'}), 200
        
    except Exception as e:
        print(f"Error updating submission: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


# ============ DELETE SUBMISSION (DRAFT) ============

@student_assignments_bp.route('/<int:assignment_id>/submissions/<int:submission_id>', methods=['DELETE'], strict_slashes=False)
@jwt_required()
@student_required
def delete_submission(assignment_id, submission_id):
    """Delete a submission (only if not graded)"""
    try:
        student_id = get_jwt_identity()
        
        cursor = mysql.connection.cursor()
        
        # Check if submission exists and is not graded
        cursor.execute("""
            SELECT * FROM submissions 
            WHERE id = %s AND student_id = %s AND assignment_id = %s AND status != 'graded'
        """, (submission_id, student_id, assignment_id))
        
        if not cursor.fetchone():
            cursor.close()
            return jsonify({'error': 'Submission not found, unauthorized, or already graded'}), 404
        
        cursor.execute("DELETE FROM submissions WHERE id = %s", (submission_id,))
        mysql.connection.commit()
        cursor.close()
        
        return jsonify({'message': 'Submission deleted successfully'}), 200
        
    except Exception as e:
        print(f"Error deleting submission: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500