from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from utils.database import mysql
from utils.decorators import admin_required
from models.subject import Subject
from models.course import Course

subjects_bp = Blueprint('subjects', __name__)

# ============ PUBLIC ENDPOINTS ============

@subjects_bp.route('/', methods=['GET'])
def get_all_subjects():
    """Get all subjects - PUBLIC for registration"""
    try:
        include_inactive = request.args.get('include_inactive', 'false').lower() == 'true'
        course_id = request.args.get('course_id', type=int)
        
        if course_id:
            subjects = Subject.get_by_course(course_id, include_inactive)
        else:
            subjects = Subject.get_all(include_inactive)
        
        return jsonify({
            'total': len(subjects),
            'subjects': subjects
        }), 200
        
    except Exception as e:
        print(f"Error getting subjects: {e}")
        return jsonify({'error': str(e)}), 500


@subjects_bp.route('/for-selection', methods=['GET'])
def get_subjects_for_selection():
    """Get subjects formatted for dropdown - PUBLIC"""
    try:
        subjects = Subject.get_for_selection()
        return jsonify({'subjects': subjects}), 200
    except Exception as e:
        print(f"Error getting subjects: {e}")
        return jsonify({'error': str(e)}), 500


@subjects_bp.route('/course/<int:course_id>', methods=['GET'])
def get_subjects_by_course(course_id):
    """Get subjects by course - PUBLIC"""
    try:
        include_inactive = request.args.get('include_inactive', 'false').lower() == 'true'
        subjects = Subject.get_by_course(course_id, include_inactive)
        return jsonify({'subjects': subjects}), 200
    except Exception as e:
        print(f"Error getting subjects: {e}")
        return jsonify({'error': str(e)}), 500


@subjects_bp.route('/<int:subject_id>', methods=['GET'])
def get_subject(subject_id):
    """Get subject by ID - PUBLIC"""
    try:
        subject = Subject.get_by_id(subject_id)
        if not subject:
            return jsonify({'error': 'Subject not found'}), 404
        
        # Get sections for this subject
        cursor = mysql.connection.cursor()
        cursor.execute("""
            SELECT s.*, 
                   COUNT(DISTINCT e.id) as enrolled_count,
                   (SELECT COUNT(*) FROM teacher_assignments ta WHERE ta.section_id = s.id) as teacher_count
            FROM sections s
            LEFT JOIN enrollments e ON s.id = e.section_id AND e.status = 'approved'
            WHERE s.subject_id = %s
            GROUP BY s.id
            ORDER BY s.academic_year DESC, s.semester, s.name
        """, (subject_id,))
        sections = cursor.fetchall()
        cursor.close()
        
        return jsonify({
            'subject': subject,
            'sections': sections
        }), 200
        
    except Exception as e:
        print(f"Error getting subject: {e}")
        return jsonify({'error': str(e)}), 500


# ============ PROTECTED ENDPOINTS (ADMIN ONLY) ============

@subjects_bp.route('/', methods=['POST'])
@jwt_required()
@admin_required
def create_subject():
    """Create a new subject (Admin only)"""
    try:
        data = request.get_json()
        
        required_fields = ['course_id', 'code', 'name']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Verify course exists
        course = Course.get_by_id(data['course_id'])
        if not course:
            return jsonify({'error': 'Course not found'}), 404
        
        # Check if subject code already exists for this course
        existing = Subject.get_by_code(data['course_id'], data['code'].upper())
        if existing:
            return jsonify({'error': 'Subject code already exists for this course'}), 400
        
        subject_id = Subject.create(
            course_id=data['course_id'],
            code=data['code'].upper(),
            name=data['name'],
            description=data.get('description'),
            credits=data.get('credits', 3),
            semester=data.get('semester'),
            is_core=data.get('is_core', True)
        )
        
        return jsonify({
            'message': 'Subject created successfully',
            'subject_id': subject_id
        }), 201
        
    except Exception as e:
        print(f"Error creating subject: {e}")
        return jsonify({'error': str(e)}), 500


@subjects_bp.route('/<int:subject_id>', methods=['PUT'])
@jwt_required()
@admin_required
def update_subject(subject_id):
    """Update a subject (Admin only)"""
    try:
        data = request.get_json()
        
        subject = Subject.get_by_id(subject_id)
        if not subject:
            return jsonify({'error': 'Subject not found'}), 404
        
        Subject.update(subject_id, **data)
        
        return jsonify({'message': 'Subject updated successfully'}), 200
        
    except Exception as e:
        print(f"Error updating subject: {e}")
        return jsonify({'error': str(e)}), 500


@subjects_bp.route('/<int:subject_id>', methods=['DELETE'])
@jwt_required()
@admin_required
def delete_subject(subject_id):
    """Delete a subject (Admin only)"""
    try:
        subject = Subject.get_by_id(subject_id)
        if not subject:
            return jsonify({'error': 'Subject not found'}), 404
        
        # Check if subject has sections
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT id FROM sections WHERE subject_id = %s LIMIT 1", (subject_id,))
        if cursor.fetchone():
            cursor.close()
            return jsonify({'error': 'Cannot delete subject with existing sections'}), 400
        cursor.close()
        
        Subject.delete(subject_id)
        
        return jsonify({'message': 'Subject deleted successfully'}), 200
        
    except Exception as e:
        print(f"Error deleting subject: {e}")
        return jsonify({'error': str(e)}), 500


@subjects_bp.route('/bulk', methods=['POST'])
@jwt_required()
@admin_required
def bulk_create_subjects():
    """Create multiple subjects at once (Admin only)"""
    try:
        data = request.get_json()
        subjects = data.get('subjects', [])
        
        if not subjects:
            return jsonify({'error': 'No subjects provided'}), 400
        
        created_ids = []
        errors = []
        
        for idx, subject_data in enumerate(subjects):
            try:
                required_fields = ['course_id', 'code', 'name']
                if not all(field in subject_data for field in required_fields):
                    errors.append(f"Row {idx+1}: Missing required fields")
                    continue
                
                subject_id = Subject.create(
                    course_id=subject_data['course_id'],
                    code=subject_data['code'].upper(),
                    name=subject_data['name'],
                    description=subject_data.get('description'),
                    credits=subject_data.get('credits', 3),
                    semester=subject_data.get('semester'),
                    is_core=subject_data.get('is_core', True)
                )
                created_ids.append(subject_id)
                
            except Exception as e:
                errors.append(f"Row {idx+1}: {str(e)}")
        
        return jsonify({
            'message': f'Created {len(created_ids)} subjects',
            'created_ids': created_ids,
            'errors': errors
        }), 201
        
    except Exception as e:
        print(f"Error bulk creating subjects: {e}")
        return jsonify({'error': str(e)}), 500