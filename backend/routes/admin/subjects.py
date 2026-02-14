from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from utils.database import mysql
from utils.decorators import admin_required
from models.subject import Subject
from models.course import Course

admin_subjects_bp = Blueprint('admin_subjects', __name__)

# ============ GET ALL SUBJECTS ============

@admin_subjects_bp.route('/', methods=['GET'], strict_slashes=False)
@jwt_required()
@admin_required
def get_all_subjects():
    """Get all subjects"""
    try:
        include_inactive = request.args.get('include_inactive', 'false').lower() == 'true'
        course_id = request.args.get('course_id', type=int)
        limit = request.args.get('limit', type=int)
        
        if course_id:
            subjects = Subject.get_by_course(course_id, include_inactive)
        else:
            subjects = Subject.get_all(include_inactive)
        
        # Apply limit if specified
        if limit and limit > 0:
            subjects = subjects[:limit]
        
        return jsonify({
            'total': len(subjects),
            'subjects': subjects
        }), 200
        
    except Exception as e:
        print(f"Error getting subjects: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@admin_subjects_bp.route('/for-selection', methods=['GET'], strict_slashes=False)
@jwt_required()
@admin_required
def get_subjects_for_selection():
    """Get subjects formatted for dropdown selection"""
    try:
        subjects = Subject.get_for_selection()
        return jsonify({'subjects': subjects}), 200
    except Exception as e:
        print(f"Error getting subjects: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@admin_subjects_bp.route('/<int:subject_id>', methods=['GET'], strict_slashes=False)
@jwt_required()
@admin_required
def get_subject(subject_id):
    """Get subject by ID"""
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
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@admin_subjects_bp.route('/', methods=['POST'], strict_slashes=False)
@jwt_required()
@admin_required
def create_subject():
    """Create a new subject"""
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
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@admin_subjects_bp.route('/<int:subject_id>', methods=['PUT'], strict_slashes=False)
@jwt_required()
@admin_required
def update_subject(subject_id):
    """Update a subject"""
    try:
        data = request.get_json()
        print(f"📡 Updating subject {subject_id} with data: {data}")
        
        # Check if subject exists
        subject = Subject.get_by_id(subject_id)
        if not subject:
            print(f"❌ Subject {subject_id} not found")
            return jsonify({'error': 'Subject not found'}), 404
        
        print(f"✅ Found subject: {subject}")
        
        # If code is being changed, check for duplicates
        if 'code' in data and data['code'] != subject['code']:
            print(f"🔍 Checking for duplicate code: {data['code']}")
            existing = Subject.get_by_code(subject['course_id'], data['code'].upper())
            if existing and existing['id'] != subject_id:
                print(f"❌ Duplicate code found: {existing}")
                return jsonify({'error': 'Subject code already exists for this course'}), 400
        
        # Update the subject
        print(f"📝 Updating subject with fields: {list(data.keys())}")
        Subject.update(subject_id, **data)
        
        return jsonify({'message': 'Subject updated successfully'}), 200
        
    except Exception as e:
        print(f"❌ Error updating subject: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@admin_subjects_bp.route('/<int:subject_id>', methods=['DELETE'], strict_slashes=False)
@jwt_required()
@admin_required
def delete_subject(subject_id):
    """Delete a subject"""
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
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@admin_subjects_bp.route('/bulk', methods=['POST'], strict_slashes=False)
@jwt_required()
@admin_required
def bulk_create_subjects():
    """Create multiple subjects at once"""
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
                
                # Check if subject code already exists
                existing = Subject.get_by_code(subject_data['course_id'], subject_data['code'].upper())
                if existing:
                    errors.append(f"Row {idx+1}: Subject code already exists")
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
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500