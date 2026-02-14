from flask import Blueprint, request, jsonify, send_file, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from utils.database import mysql
from utils.decorators import role_required
from utils.file_handler import save_file, delete_file, get_file_size
import os
from datetime import datetime

assignment_bp = Blueprint('assignments', __name__)

# ============ TEACHER ENDPOINTS ============

@assignment_bp.route('/', methods=['POST'])
@jwt_required()
@role_required(['teacher'])
def create_assignment():
    """Create a new assignment"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['title', 'class_id', 'due_date', 'points_possible']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Verify teacher owns the class
        cursor = mysql.connection.cursor()
        cursor.execute("""
            SELECT c.* FROM classes c
            JOIN teacher_profiles tp ON c.teacher_id = tp.id
            WHERE c.id = %s AND tp.user_id = %s
        """, (data['class_id'], user_id))
        
        if not cursor.fetchone():
            cursor.close()
            return jsonify({'error': 'Class not found or unauthorized'}), 403
        
        # Create assignment
        cursor.execute("""
            INSERT INTO assignments (
                title, instructions, due_date, points_possible,
                class_id, late_policy, late_penalty, rubric, 
                is_published, allow_late, max_file_size, allowed_file_types
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            data['title'],
            data.get('instructions', ''),
            data['due_date'],
            data['points_possible'],
            data['class_id'],
            data.get('late_policy', 'no_submissions'),
            data.get('late_penalty', 0),
            data.get('rubric', None),
            data.get('is_published', False),
            data.get('allow_late', False),
            data.get('max_file_size', 10485760),
            data.get('allowed_file_types', '.pdf,.doc,.docx,.zip,.jpg,.png')
        ))
        
        mysql.connection.commit()
        assignment_id = cursor.lastrowid
        cursor.close()
        
        # TODO: Send notifications to all enrolled students
        
        return jsonify({
            'message': 'Assignment created successfully',
            'assignment_id': assignment_id
        }), 201
        
    except Exception as e:
        print(f"Error creating assignment: {e}")
        return jsonify({'error': str(e)}), 500


@assignment_bp.route('/<int:assignment_id>/attachments', methods=['POST'])
@jwt_required()
@role_required(['teacher'])
def upload_assignment_attachments(assignment_id):
    """Upload attachments for an assignment"""
    try:
        user_id = get_jwt_identity()
        
        # Verify teacher owns the assignment
        cursor = mysql.connection.cursor()
        cursor.execute("""
            SELECT a.* FROM assignments a
            JOIN classes c ON a.class_id = c.id
            JOIN teacher_profiles tp ON c.teacher_id = tp.id
            WHERE a.id = %s AND tp.user_id = %s
        """, (assignment_id, user_id))
        
        if not cursor.fetchone():
            cursor.close()
            return jsonify({'error': 'Assignment not found or unauthorized'}), 404
        
        # Get uploaded files
        files = request.files.getlist('files')
        
        if not files:
            cursor.close()
            return jsonify({'error': 'No files uploaded'}), 400
        
        # Save each file
        saved_files = []
        for file in files:
            if file and file.filename:
                file_path = save_file(file, subfolder=f"assignments/{assignment_id}")
                if file_path:
                    # Get file info
                    filename = file.filename
                    _, ext = os.path.splitext(filename)
                    file_size = get_file_size(file)
                    
                    # Save to database
                    cursor.execute("""
                        INSERT INTO attachments (file_name, file_path, file_type, file_size, assignment_id, uploaded_by)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (
                        filename,
                        file_path,
                        ext[1:].lower() if ext else 'unknown',
                        file_size,
                        assignment_id,
                        user_id
                    ))
                    saved_files.append({
                        'file_name': filename,
                        'file_path': file_path,
                        'file_type': ext[1:].lower() if ext else 'unknown',
                        'file_size': file_size
                    })
        
        mysql.connection.commit()
        cursor.close()
        
        return jsonify({
            'message': f'{len(saved_files)} file(s) uploaded successfully',
            'files': saved_files
        }), 201
        
    except Exception as e:
        print(f"Error uploading attachments: {e}")
        return jsonify({'error': str(e)}), 500


@assignment_bp.route('/<int:assignment_id>/attachments', methods=['GET'])
@jwt_required()
def get_assignment_attachments(assignment_id):
    """Get all attachments for an assignment"""
    try:
        cursor = mysql.connection.cursor()
        cursor.execute("""
            SELECT * FROM attachments 
            WHERE assignment_id = %s
        """, (assignment_id,))
        
        attachments = cursor.fetchall()
        cursor.close()
        
        return jsonify({'attachments': attachments}), 200
        
    except Exception as e:
        print(f"Error getting attachments: {e}")
        return jsonify({'error': str(e)}), 500


@assignment_bp.route('/<int:assignment_id>', methods=['PUT'])
@jwt_required()
@role_required(['teacher'])
def update_assignment(assignment_id):
    """Update an assignment"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        cursor = mysql.connection.cursor()
        
        # Verify teacher owns the assignment
        cursor.execute("""
            SELECT a.* FROM assignments a
            JOIN classes c ON a.class_id = c.id
            JOIN teacher_profiles tp ON c.teacher_id = tp.id
            WHERE a.id = %s AND tp.user_id = %s
        """, (assignment_id, user_id))
        
        if not cursor.fetchone():
            cursor.close()
            return jsonify({'error': 'Assignment not found or unauthorized'}), 404
        
        # Update assignment
        update_fields = []
        update_values = []
        
        allowed_fields = [
            'title', 'instructions', 'due_date', 'points_possible',
            'late_policy', 'late_penalty', 'rubric', 'is_published',
            'allow_late', 'max_file_size', 'allowed_file_types'
        ]
        
        for field in allowed_fields:
            if field in data:
                update_fields.append(f"{field} = %s")
                update_values.append(data[field])
        
        if update_fields:
            query = f"UPDATE assignments SET {', '.join(update_fields)} WHERE id = %s"
            update_values.append(assignment_id)
            cursor.execute(query, tuple(update_values))
            mysql.connection.commit()
        
        cursor.close()
        
        return jsonify({'message': 'Assignment updated successfully'}), 200
        
    except Exception as e:
        print(f"Error updating assignment: {e}")
        return jsonify({'error': str(e)}), 500


@assignment_bp.route('/<int:assignment_id>', methods=['DELETE'])
@jwt_required()
@role_required(['teacher'])
def delete_assignment(assignment_id):
    """Delete an assignment"""
    try:
        user_id = get_jwt_identity()
        
        cursor = mysql.connection.cursor()
        
        # Verify teacher owns the assignment
        cursor.execute("""
            SELECT a.* FROM assignments a
            JOIN classes c ON a.class_id = c.id
            JOIN teacher_profiles tp ON c.teacher_id = tp.id
            WHERE a.id = %s AND tp.user_id = %s
        """, (assignment_id, user_id))
        
        if not cursor.fetchone():
            cursor.close()
            return jsonify({'error': 'Assignment not found or unauthorized'}), 404
        
        # Delete assignment (cascades to submissions)
        cursor.execute("DELETE FROM assignments WHERE id = %s", (assignment_id,))
        mysql.connection.commit()
        cursor.close()
        
        return jsonify({'message': 'Assignment deleted successfully'}), 200
        
    except Exception as e:
        print(f"Error deleting assignment: {e}")
        return jsonify({'error': str(e)}), 500


@assignment_bp.route('/<int:assignment_id>/publish', methods=['POST'])
@jwt_required()
@role_required(['teacher'])
def publish_assignment(assignment_id):
    """Publish/unpublish assignment"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        cursor = mysql.connection.cursor()
        
        # Verify teacher owns the assignment
        cursor.execute("""
            SELECT a.* FROM assignments a
            JOIN classes c ON a.class_id = c.id
            JOIN teacher_profiles tp ON c.teacher_id = tp.id
            WHERE a.id = %s AND tp.user_id = %s
        """, (assignment_id, user_id))
        
        if not cursor.fetchone():
            cursor.close()
            return jsonify({'error': 'Assignment not found or unauthorized'}), 404
        
        is_published = data.get('is_published', True)
        
        cursor.execute("""
            UPDATE assignments 
            SET is_published = %s 
            WHERE id = %s
        """, (is_published, assignment_id))
        
        mysql.connection.commit()
        cursor.close()
        
        status = 'published' if is_published else 'unpublished'
        return jsonify({'message': f'Assignment {status} successfully'}), 200
        
    except Exception as e:
        print(f"Error publishing assignment: {e}")
        return jsonify({'error': str(e)}), 500


# ============ STUDENT ENDPOINTS ============

@assignment_bp.route('/<int:assignment_id>/submit', methods=['POST'])
@jwt_required()
@role_required(['student'])
def submit_assignment(assignment_id):
    """Submit assignment work"""
    try:
        user_id = get_jwt_identity()
        
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
        
        # Get student profile
        cursor.execute("SELECT id FROM student_profiles WHERE user_id = %s", (user_id,))
        student = cursor.fetchone()
        
        if not student:
            cursor.close()
            return jsonify({'error': 'Student profile not found'}), 404
        
        # Check if student is enrolled in the class
        cursor.execute("""
            SELECT ce.* FROM class_enrollments ce
            WHERE ce.class_id = %s AND ce.student_id = %s AND ce.status = 'approved'
        """, (assignment['class_id'], student['id']))
        
        if not cursor.fetchone():
            cursor.close()
            return jsonify({'error': 'You are not enrolled in this class'}), 403
        
        # Check if already submitted
        cursor.execute("""
            SELECT * FROM submissions 
            WHERE assignment_id = %s AND student_id = %s
        """, (assignment_id, user_id))
        
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
                SET content = %s, updated_at = NOW(), is_late = %s, status = 'submitted'
                WHERE id = %s
            """, (text_entry, is_late, existing['id']))
            submission_id = existing['id']
        else:
            # Create new submission
            cursor.execute("""
                INSERT INTO submissions (
                    assignment_id, student_id, content, status, is_late
                ) VALUES (%s, %s, %s, %s, %s)
            """, (assignment_id, user_id, text_entry, 'submitted', is_late))
            submission_id = cursor.lastrowid
        
        # Save file attachments
        saved_files = []
        if files:
            for file in files:
                if file and file.filename:
                    file_path = save_file(file, subfolder=f"submissions/{assignment_id}/{user_id}")
                    if file_path:
                        filename = file.filename
                        _, ext = os.path.splitext(filename)
                        file_size = get_file_size(file)
                        
                        cursor.execute("""
                            INSERT INTO attachments (file_name, file_path, file_type, file_size, submission_id)
                            VALUES (%s, %s, %s, %s, %s)
                        """, (
                            filename,
                            file_path,
                            ext[1:].lower() if ext else 'unknown',
                            file_size,
                            submission_id
                        ))
                        saved_files.append(filename)
        
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
        return jsonify({'error': str(e)}), 500


@assignment_bp.route('/<int:assignment_id>/submissions', methods=['GET'])
@jwt_required()
def get_my_submission(assignment_id):
    """Get current student's submission for an assignment"""
    try:
        user_id = get_jwt_identity()
        
        cursor = mysql.connection.cursor()
        cursor.execute("""
            SELECT s.*, 
                   GROUP_CONCAT(a.file_path) as attachments,
                   GROUP_CONCAT(a.file_name) as file_names
            FROM submissions s
            LEFT JOIN attachments a ON s.id = a.submission_id
            WHERE s.assignment_id = %s AND s.student_id = %s
            GROUP BY s.id
        """, (assignment_id, user_id))
        
        submission = cursor.fetchone()
        cursor.close()
        
        if not submission:
            return jsonify({'submission': None}), 200
        
        return jsonify({'submission': submission}), 200
        
    except Exception as e:
        print(f"Error getting submission: {e}")
        return jsonify({'error': str(e)}), 500


# ============ GRADING ENDPOINTS ============

@assignment_bp.route('/submissions/<int:submission_id>/grade', methods=['PUT'])
@jwt_required()
@role_required(['teacher'])
def grade_submission(submission_id):
    """Grade a student submission"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if 'grade' not in data:
            return jsonify({'error': 'Grade is required'}), 400
        
        cursor = mysql.connection.cursor()
        
        # Verify teacher owns the assignment
        cursor.execute("""
            SELECT s.* FROM submissions s
            JOIN assignments a ON s.assignment_id = a.id
            JOIN classes c ON a.class_id = c.id
            JOIN teacher_profiles tp ON c.teacher_id = tp.id
            WHERE s.id = %s AND tp.user_id = %s
        """, (submission_id, user_id))
        
        submission = cursor.fetchone()
        if not submission:
            cursor.close()
            return jsonify({'error': 'Submission not found or unauthorized'}), 404
        
        # Handle feedback file upload
        feedback_file = request.files.get('feedback_file')
        feedback_file_path = None
        
        if feedback_file and feedback_file.filename:
            feedback_file_path = save_file(feedback_file, subfolder=f"feedback/{submission_id}")
        
        # Update submission with grade and feedback
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
            user_id,
            submission_id
        ))
        
        mysql.connection.commit()
        cursor.close()
        
        # TODO: Send notification to student
        
        return jsonify({'message': 'Submission graded successfully'}), 200
        
    except Exception as e:
        print(f"Error grading submission: {e}")
        return jsonify({'error': str(e)}), 500


@assignment_bp.route('/<int:assignment_id>/submissions/all', methods=['GET'])
@jwt_required()
@role_required(['teacher'])
def get_all_submissions(assignment_id):
    """Get all submissions for an assignment (teacher only)"""
    try:
        user_id = get_jwt_identity()
        
        cursor = mysql.connection.cursor()
        
        # Verify teacher owns the assignment
        cursor.execute("""
            SELECT a.* FROM assignments a
            JOIN classes c ON a.class_id = c.id
            JOIN teacher_profiles tp ON c.teacher_id = tp.id
            WHERE a.id = %s AND tp.user_id = %s
        """, (assignment_id, user_id))
        
        if not cursor.fetchone():
            cursor.close()
            return jsonify({'error': 'Assignment not found or unauthorized'}), 404
        
        # Get all submissions with student info
        cursor.execute("""
            SELECT 
                s.*,
                u.name as student_name,
                u.email as student_email,
                u.profile_pic,
                sp.student_id,
                GROUP_CONCAT(a.file_path) as attachments,
                GROUP_CONCAT(a.file_name) as file_names
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
        
        # Calculate statistics
        total = len(submissions)
        graded = sum(1 for s in submissions if s['status'] == 'graded')
        pending = sum(1 for s in submissions if s['status'] == 'submitted')
        average_grade = None
        
        grades = [s['grade'] for s in submissions if s['grade']]
        if grades:
            average_grade = sum(grades) / len(grades)
        
        return jsonify({
            'assignment_id': assignment_id,
            'total_submissions': total,
            'graded': graded,
            'pending': pending,
            'average_grade': average_grade,
            'submissions': submissions
        }), 200
        
    except Exception as e:
        print(f"Error getting submissions: {e}")
        return jsonify({'error': str(e)}), 500


@assignment_bp.route('/submissions/<int:submission_id>/download', methods=['GET'])
@jwt_required()
def download_submission(submission_id):
    """Download submission files"""
    try:
        user_id = get_jwt_identity()
        
        cursor = mysql.connection.cursor()
        
        # Check authorization
        cursor.execute("""
            SELECT s.*, u.role FROM submissions s
            JOIN users u ON %s = u.id
            WHERE s.id = %s
        """, (user_id, submission_id))
        
        result = cursor.fetchone()
        
        if not result:
            cursor.close()
            return jsonify({'error': 'Submission not found'}), 404
        
        # Get attachment
        cursor.execute("""
            SELECT * FROM attachments 
            WHERE submission_id = %s
        """, (submission_id,))
        
        attachment = cursor.fetchone()
        cursor.close()
        
        if not attachment:
            return jsonify({'error': 'No files found'}), 404
        
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], attachment['file_path'])
        
        if not os.path.exists(file_path):
            return jsonify({'error': 'File not found'}), 404
        
        return send_file(
            file_path,
            as_attachment=True,
            download_name=attachment['file_name']
        )
        
    except Exception as e:
        print(f"Error downloading submission: {e}")
        return jsonify({'error': str(e)}), 500


# ============ PUBLIC ENDPOINTS ============

@assignment_bp.route('/class/<int:class_id>', methods=['GET'])
@jwt_required()
def get_class_assignments(class_id):
    """Get all assignments for a class"""
    try:
        user_id = get_jwt_identity()
        
        cursor = mysql.connection.cursor()
        
        # Check if user has access to this class
        cursor.execute("SELECT role FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        
        has_access = False
        
        if user['role'] == 'teacher':
            cursor.execute("""
                SELECT c.* FROM classes c
                JOIN teacher_profiles tp ON c.teacher_id = tp.id
                WHERE c.id = %s AND tp.user_id = %s
            """, (class_id, user_id))
            has_access = cursor.fetchone() is not None
            
        elif user['role'] == 'student':
            cursor.execute("""
                SELECT sp.id FROM student_profiles sp
                WHERE sp.user_id = %s
            """, (user_id,))
            student = cursor.fetchone()
            
            if student:
                cursor.execute("""
                    SELECT status FROM class_enrollments
                    WHERE class_id = %s AND student_id = %s
                """, (class_id, student['id']))
                enrollment = cursor.fetchone()
                has_access = enrollment and enrollment['status'] == 'approved'
        
        if not has_access:
            cursor.close()
            return jsonify({'error': 'Access denied'}), 403
        
        # Get assignments
        cursor.execute("""
            SELECT a.*, 
                   (SELECT COUNT(*) FROM submissions s 
                    WHERE s.assignment_id = a.id) as submission_count,
                   (SELECT COUNT(*) FROM submissions s 
                    WHERE s.assignment_id = a.id AND s.status = 'graded') as graded_count,
                   (SELECT COUNT(*) FROM submissions s 
                    WHERE s.assignment_id = a.id AND s.status = 'submitted') as pending_submissions
            FROM assignments a
            WHERE a.class_id = %s
            ORDER BY a.due_date ASC
        """, (class_id,))
        
        assignments = cursor.fetchall()
        cursor.close()
        
        return jsonify({'assignments': assignments}), 200
        
    except Exception as e:
        print(f"Error getting class assignments: {e}")
        return jsonify({'error': str(e)}), 500


@assignment_bp.route('/<int:assignment_id>', methods=['GET'])
@jwt_required()
def get_assignment_details(assignment_id):
    """Get detailed assignment information"""
    try:
        user_id = get_jwt_identity()
        
        cursor = mysql.connection.cursor()
        
        # Get assignment details
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
        
        if not assignment:
            cursor.close()
            return jsonify({'error': 'Assignment not found'}), 404
        
        # If student, get their submission
        cursor.execute("SELECT role FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        
        if user['role'] == 'student':
            cursor.execute("""
                SELECT * FROM submissions 
                WHERE assignment_id = %s AND student_id = %s
            """, (assignment_id, user_id))
            submission = cursor.fetchone()
            assignment['my_submission'] = submission
        
        cursor.close()
        
        return jsonify({'assignment': assignment}), 200
        
    except Exception as e:
        print(f"Error getting assignment details: {e}")
        return jsonify({'error': str(e)}), 500


@assignment_bp.route('/submissions/<int:submission_id>/feedback', methods=['GET'])
@jwt_required()
def download_feedback(submission_id):
    """Download feedback file"""
    try:
        user_id = get_jwt_identity()
        
        cursor = mysql.connection.cursor()
        
        # Check authorization
        cursor.execute("""
            SELECT s.*, u.role FROM submissions s
            JOIN users u ON %s = u.id
            WHERE s.id = %s
        """, (user_id, submission_id))
        
        result = cursor.fetchone()
        
        if not result:
            cursor.close()
            return jsonify({'error': 'Submission not found'}), 404
        
        if not result['feedback_file']:
            cursor.close()
            return jsonify({'error': 'No feedback file found'}), 404
        
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], result['feedback_file'])
        cursor.close()
        
        if not os.path.exists(file_path):
            return jsonify({'error': 'File not found'}), 404
        
        return send_file(
            file_path,
            as_attachment=True,
            download_name=os.path.basename(file_path)
        )
        
    except Exception as e:
        print(f"Error downloading feedback: {e}")
        return jsonify({'error': str(e)}), 500