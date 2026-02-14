from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from utils.database import mysql
from utils.decorators import teacher_required
from utils.file_handler import save_file
import os

teacher_assignments_bp = Blueprint('teacher_assignments', __name__)

# ============ GET ASSIGNMENTS BY SECTION ============

@teacher_assignments_bp.route('/section/<int:section_id>', methods=['GET'], strict_slashes=False)
@jwt_required()
@teacher_required
def get_section_assignments(section_id):
    """Get all assignments for a section"""
    try:
        teacher_id = get_jwt_identity()
        
        cursor = mysql.connection.cursor()
        
        # Verify teacher is assigned to this section
        cursor.execute("""
            SELECT ta.id FROM teacher_assignments ta
            WHERE ta.teacher_id = %s AND ta.section_id = %s
        """, (teacher_id, section_id))
        
        if not cursor.fetchone():
            cursor.close()
            return jsonify({'error': 'You are not assigned to this section'}), 403
        
        # Get total students in section
        cursor.execute("""
            SELECT COUNT(*) as total_students
            FROM enrollments
            WHERE section_id = %s AND status = 'approved'
        """, (section_id,))
        
        total_students = cursor.fetchone()['total_students']
        
        # Get assignments with submission counts
        cursor.execute("""
            SELECT 
                a.id,
                a.title,
                a.instructions,
                a.due_date,
                a.points_possible,
                a.late_policy,
                a.late_penalty,
                a.rubric,
                a.is_published,
                a.allow_late,
                a.max_file_size,
                a.allowed_file_types,
                a.created_at,
                a.updated_at,
                (SELECT COUNT(*) FROM submissions s WHERE s.assignment_id = a.id) as total_submissions,
                (SELECT COUNT(*) FROM submissions s WHERE s.assignment_id = a.id AND s.status = 'graded') as graded_submissions,
                (SELECT COUNT(*) FROM submissions s WHERE s.assignment_id = a.id AND s.status = 'submitted') as pending_submissions
            FROM assignments a
            WHERE a.section_id = %s
            ORDER BY a.due_date DESC
        """, (section_id,))
        
        assignments = cursor.fetchall()
        
        # Add completion rate to each assignment
        for assignment in assignments:
            if total_students > 0:
                assignment['submission_rate'] = round((assignment['total_submissions'] or 0) / total_students * 100, 2)
            else:
                assignment['submission_rate'] = 0
        
        cursor.close()
        
        return jsonify({
            'section_id': section_id,
            'total_assignments': len(assignments),
            'total_students': total_students,
            'assignments': assignments
        }), 200
        
    except Exception as e:
        print(f"Error getting assignments: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


# ============ GET SINGLE ASSIGNMENT ============

@teacher_assignments_bp.route('/<int:assignment_id>', methods=['GET'], strict_slashes=False)
@jwt_required()
@teacher_required
def get_assignment(assignment_id):
    """Get a single assignment by ID"""
    try:
        teacher_id = get_jwt_identity()
        
        cursor = mysql.connection.cursor()
        
        # Verify teacher owns this assignment
        cursor.execute("""
            SELECT a.*, s.name as section_name, sub.name as subject_name, c.name as course_name
            FROM assignments a
            JOIN sections s ON a.section_id = s.id
            JOIN subjects sub ON s.subject_id = sub.id
            JOIN courses c ON sub.course_id = c.id
            JOIN teacher_assignments ta ON s.id = ta.section_id
            WHERE a.id = %s AND ta.teacher_id = %s
        """, (assignment_id, teacher_id))
        
        assignment = cursor.fetchone()
        
        if not assignment:
            cursor.close()
            return jsonify({'error': 'Assignment not found or unauthorized'}), 404
        
        # Get attachments
        cursor.execute("""
            SELECT id, file_name, file_path, file_type, file_size, uploaded_at
            FROM attachments 
            WHERE assignment_id = %s
        """, (assignment_id,))
        
        attachments = cursor.fetchall()
        assignment['attachments'] = attachments
        
        cursor.close()
        
        return jsonify(assignment), 200
        
    except Exception as e:
        print(f"Error getting assignment: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


# ============ CREATE ASSIGNMENT ============

@teacher_assignments_bp.route('/', methods=['POST'], strict_slashes=False)
@jwt_required()
@teacher_required
def create_assignment():
    """Create a new assignment for a section"""
    try:
        teacher_id = get_jwt_identity()
        data = request.get_json()
        
        required_fields = ['title', 'section_id', 'due_date', 'points_possible']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        cursor = mysql.connection.cursor()
        
        # Verify teacher is assigned to this section
        cursor.execute("""
            SELECT ta.id FROM teacher_assignments ta
            WHERE ta.teacher_id = %s AND ta.section_id = %s
        """, (teacher_id, data['section_id']))
        
        if not cursor.fetchone():
            cursor.close()
            return jsonify({'error': 'You are not assigned to this section'}), 403
        
        # Create assignment
        cursor.execute("""
            INSERT INTO assignments (
                title, instructions, due_date, points_possible,
                section_id, late_policy, late_penalty, rubric,
                is_published, allow_late, max_file_size, allowed_file_types
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            data['title'],
            data.get('instructions', ''),
            data['due_date'],
            data['points_possible'],
            data['section_id'],
            data.get('late_policy', 'no_submissions'),
            data.get('late_penalty', 0),
            data.get('rubric'),
            data.get('is_published', False),
            data.get('allow_late', False),
            data.get('max_file_size', 10485760),
            data.get('allowed_file_types', '.pdf,.doc,.docx,.zip,.jpg,.png')
        ))
        
        mysql.connection.commit()
        assignment_id = cursor.lastrowid
        cursor.close()
        
        return jsonify({
            'message': 'Assignment created successfully',
            'assignment_id': assignment_id
        }), 201
        
    except Exception as e:
        print(f"Error creating assignment: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


# ============ UPLOAD ASSIGNMENT ATTACHMENTS ============

@teacher_assignments_bp.route('/<int:assignment_id>/attachments', methods=['POST'], strict_slashes=False)
@jwt_required()
@teacher_required
def upload_assignment_attachments(assignment_id):
    """Upload attachments for an assignment"""
    try:
        teacher_id = get_jwt_identity()
        
        cursor = mysql.connection.cursor()
        
        # Verify teacher owns this assignment
        cursor.execute("""
            SELECT a.* FROM assignments a
            JOIN sections s ON a.section_id = s.id
            JOIN teacher_assignments ta ON s.id = ta.section_id
            WHERE a.id = %s AND ta.teacher_id = %s
        """, (assignment_id, teacher_id))
        
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
                file_info = save_file(file, subfolder=f"assignments/{assignment_id}")
                
                # Check if file_info is a dictionary (success) or string (error)
                if file_info and isinstance(file_info, dict):
                    cursor.execute("""
                        INSERT INTO attachments (
                            file_name, file_path, file_type, file_size, 
                            assignment_id, uploaded_by
                        ) VALUES (%s, %s, %s, %s, %s, %s)
                    """, (
                        file_info['file_name'],
                        file_info['file_path'],
                        file_info['file_type'],
                        file_info['file_size'],
                        assignment_id,
                        teacher_id
                    ))
                    saved_files.append(file_info)
                    print(f"✅ File saved: {file_info['file_name']}")
                else:
                    print(f"⚠️ Failed to save file: {file.filename}")
        
        mysql.connection.commit()
        cursor.close()
        
        return jsonify({
            'message': f'{len(saved_files)} file(s) uploaded successfully',
            'files': saved_files
        }), 201
        
    except Exception as e:
        print(f"Error uploading attachments: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


# ============ UPDATE ASSIGNMENT ============

@teacher_assignments_bp.route('/<int:assignment_id>', methods=['PUT'], strict_slashes=False)
@jwt_required()
@teacher_required
def update_assignment(assignment_id):
    """Update an assignment"""
    try:
        teacher_id = get_jwt_identity()
        data = request.get_json()
        
        cursor = mysql.connection.cursor()
        
        # Verify teacher owns this assignment
        cursor.execute("""
            SELECT a.* FROM assignments a
            JOIN sections s ON a.section_id = s.id
            JOIN teacher_assignments ta ON s.id = ta.section_id
            WHERE a.id = %s AND ta.teacher_id = %s
        """, (assignment_id, teacher_id))
        
        if not cursor.fetchone():
            cursor.close()
            return jsonify({'error': 'Assignment not found or unauthorized'}), 404
        
        # Build update query
        update_fields = []
        values = []
        
        allowed_fields = [
            'title', 'instructions', 'due_date', 'points_possible',
            'late_policy', 'late_penalty', 'rubric', 'is_published',
            'allow_late', 'max_file_size', 'allowed_file_types'
        ]
        
        for field in allowed_fields:
            if field in data:
                update_fields.append(f"{field} = %s")
                values.append(data[field])
        
        if update_fields:
            query = f"UPDATE assignments SET {', '.join(update_fields)} WHERE id = %s"
            values.append(assignment_id)
            cursor.execute(query, tuple(values))
            mysql.connection.commit()
        
        cursor.close()
        
        return jsonify({'message': 'Assignment updated successfully'}), 200
        
    except Exception as e:
        print(f"Error updating assignment: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


# ============ DELETE ASSIGNMENT ============

@teacher_assignments_bp.route('/<int:assignment_id>', methods=['DELETE'], strict_slashes=False)
@jwt_required()
@teacher_required
def delete_assignment(assignment_id):
    """Delete an assignment"""
    try:
        teacher_id = get_jwt_identity()
        
        cursor = mysql.connection.cursor()
        
        # Verify teacher owns this assignment
        cursor.execute("""
            SELECT a.* FROM assignments a
            JOIN sections s ON a.section_id = s.id
            JOIN teacher_assignments ta ON s.id = ta.section_id
            WHERE a.id = %s AND ta.teacher_id = %s
        """, (assignment_id, teacher_id))
        
        assignment = cursor.fetchone()
        
        if not assignment:
            cursor.close()
            return jsonify({'error': 'Assignment not found or unauthorized'}), 404
        
        # Delete assignment (cascades to submissions and attachments)
        cursor.execute("DELETE FROM assignments WHERE id = %s", (assignment_id,))
        mysql.connection.commit()
        cursor.close()
        
        return jsonify({'message': 'Assignment deleted successfully'}), 200
        
    except Exception as e:
        print(f"Error deleting assignment: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


# ============ PUBLISH/UNPUBLISH ASSIGNMENT ============

@teacher_assignments_bp.route('/<int:assignment_id>/publish', methods=['POST'], strict_slashes=False)
@jwt_required()
@teacher_required
def publish_assignment(assignment_id):
    """Publish or unpublish an assignment"""
    try:
        teacher_id = get_jwt_identity()
        data = request.get_json()
        
        cursor = mysql.connection.cursor()
        
        # Verify teacher owns this assignment
        cursor.execute("""
            SELECT a.* FROM assignments a
            JOIN sections s ON a.section_id = s.id
            JOIN teacher_assignments ta ON s.id = ta.section_id
            WHERE a.id = %s AND ta.teacher_id = %s
        """, (assignment_id, teacher_id))
        
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
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


# ============ GET ASSIGNMENT STATS ============

@teacher_assignments_bp.route('/<int:assignment_id>/stats', methods=['GET'], strict_slashes=False)
@jwt_required()
@teacher_required
def get_assignment_stats(assignment_id):
    """Get statistics for an assignment"""
    try:
        teacher_id = get_jwt_identity()
        
        cursor = mysql.connection.cursor()
        
        # Verify teacher owns this assignment
        cursor.execute("""
            SELECT a.* FROM assignments a
            JOIN sections s ON a.section_id = s.id
            JOIN teacher_assignments ta ON s.id = ta.section_id
            WHERE a.id = %s AND ta.teacher_id = %s
        """, (assignment_id, teacher_id))
        
        assignment = cursor.fetchone()
        
        if not assignment:
            cursor.close()
            return jsonify({'error': 'Assignment not found or unauthorized'}), 404
        
        # Get submission stats
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
        
        stats = cursor.fetchone()
        
        # Get total students in section
        cursor.execute("""
            SELECT COUNT(*) as total_students
            FROM enrollments
            WHERE section_id = %s AND status = 'approved'
        """, (assignment['section_id'],))
        
        total_students = cursor.fetchone()['total_students']
        
        cursor.close()
        
        return jsonify({
            'assignment_id': assignment_id,
            'title': assignment['title'],
            'total_students': total_students,
            'submitted': stats['total_submissions'] or 0,
            'pending': stats['pending'] or 0,
            'graded': stats['graded'] or 0,
            'late': stats['late'] or 0,
            'average_grade': round(stats['average_grade'], 2) if stats['average_grade'] else None,
            'min_grade': stats['min_grade'],
            'max_grade': stats['max_grade'],
            'submission_rate': round((stats['total_submissions'] or 0) / total_students * 100, 2) if total_students > 0 else 0
        }), 200
        
    except Exception as e:
        print(f"Error getting assignment stats: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500