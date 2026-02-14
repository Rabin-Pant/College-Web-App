from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from utils.database import mysql
from utils.decorators import admin_required
from models.course import Course
from models.subject import Subject

courses_bp = Blueprint('courses', __name__)

# ============ PUBLIC ENDPOINTS ============

@courses_bp.route('/', methods=['GET'])
def get_courses():
    """Get all courses - PUBLIC for registration"""
    try:
        include_inactive = request.args.get('include_inactive', 'false').lower() == 'true'
        courses = Course.get_all(include_inactive)
        
        # Add stats for each course
        cursor = mysql.connection.cursor()
        for course in courses:
            # Count subjects
            cursor.execute("SELECT COUNT(*) as count FROM subjects WHERE course_id = %s", (course['id'],))
            course['subjects_count'] = cursor.fetchone()['count']
            
            # Count sections
            cursor.execute("""
                SELECT COUNT(DISTINCT s.id) as count
                FROM sections s
                JOIN subjects sub ON s.subject_id = sub.id
                WHERE sub.course_id = %s
            """, (course['id'],))
            course['sections_count'] = cursor.fetchone()['count']
        
        cursor.close()
        
        return jsonify({
            'total': len(courses),
            'courses': courses
        }), 200
        
    except Exception as e:
        print(f"Error getting courses: {e}")
        return jsonify({'error': str(e)}), 500


@courses_bp.route('/<int:course_id>', methods=['GET'])
def get_course(course_id):
    """Get course by ID - PUBLIC"""
    try:
        course = Course.get_by_id(course_id)
        if not course:
            return jsonify({'error': 'Course not found'}), 404
        
        # Get subjects in this course
        subjects = Subject.get_by_course(course_id)
        
        # Get sections count
        cursor = mysql.connection.cursor()
        cursor.execute("""
            SELECT COUNT(DISTINCT s.id) as sections_count
            FROM sections s
            JOIN subjects sub ON s.subject_id = sub.id
            WHERE sub.course_id = %s
        """, (course_id,))
        course['sections_count'] = cursor.fetchone()['sections_count']
        
        cursor.close()
        
        return jsonify({
            'course': course,
            'subjects': subjects
        }), 200
        
    except Exception as e:
        print(f"Error getting course: {e}")
        return jsonify({'error': str(e)}), 500


@courses_bp.route('/code/<string:code>', methods=['GET'])
def get_course_by_code(code):
    """Get course by code - PUBLIC"""
    try:
        course = Course.get_by_code(code.upper())
        if not course:
            return jsonify({'error': 'Course not found'}), 404
        return jsonify(course), 200
    except Exception as e:
        print(f"Error getting course: {e}")
        return jsonify({'error': str(e)}), 500


# ============ PROTECTED ENDPOINTS (ADMIN ONLY) ============

@courses_bp.route('/', methods=['POST'])
@jwt_required()
@admin_required
def create_course():
    """Create a new course (Admin only)"""
    try:
        data = request.get_json()
        
        required_fields = ['name', 'code']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Check if course code already exists
        existing = Course.get_by_code(data['code'].upper())
        if existing:
            return jsonify({'error': 'Course code already exists'}), 400
        
        course_id = Course.create(
            name=data['name'],
            code=data['code'].upper(),
            description=data.get('description'),
            department=data.get('department'),
            duration_years=data.get('duration_years', 4),
            total_credits=data.get('total_credits', 120)
        )
        
        return jsonify({
            'message': 'Course created successfully',
            'course_id': course_id
        }), 201
        
    except Exception as e:
        print(f"Error creating course: {e}")
        return jsonify({'error': str(e)}), 500


@courses_bp.route('/<int:course_id>', methods=['PUT'])
@jwt_required()
@admin_required
def update_course(course_id):
    """Update a course (Admin only)"""
    try:
        data = request.get_json()
        
        course = Course.get_by_id(course_id)
        if not course:
            return jsonify({'error': 'Course not found'}), 404
        
        Course.update(course_id, **data)
        
        return jsonify({'message': 'Course updated successfully'}), 200
        
    except Exception as e:
        print(f"Error updating course: {e}")
        return jsonify({'error': str(e)}), 500


@courses_bp.route('/<int:course_id>', methods=['DELETE'])
@jwt_required()
@admin_required
def delete_course(course_id):
    """Delete a course (Admin only)"""
    try:
        course = Course.get_by_id(course_id)
        if not course:
            return jsonify({'error': 'Course not found'}), 404
        
        # Check if course has subjects
        subjects = Subject.get_by_course(course_id)
        if subjects:
            return jsonify({'error': 'Cannot delete course with existing subjects. Delete subjects first.'}), 400
        
        Course.delete(course_id)
        
        return jsonify({'message': 'Course deleted successfully'}), 200
        
    except Exception as e:
        print(f"Error deleting course: {e}")
        return jsonify({'error': str(e)}), 500


@courses_bp.route('/<int:course_id>/toggle-status', methods=['POST'])
@jwt_required()
@admin_required
def toggle_course_status(course_id):
    """Activate/deactivate a course (Admin only)"""
    try:
        data = request.get_json()
        is_active = data.get('is_active', True)
        
        course = Course.get_by_id(course_id)
        if not course:
            return jsonify({'error': 'Course not found'}), 404
        
        Course.update(course_id, is_active=is_active)
        
        status = 'activated' if is_active else 'deactivated'
        return jsonify({'message': f'Course {status} successfully'}), 200
        
    except Exception as e:
        print(f"Error toggling course status: {e}")
        return jsonify({'error': str(e)}), 500