from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from utils.database import mysql
from utils.decorators import admin_required
from models.course import Course
from models.subject import Subject

admin_courses_bp = Blueprint('admin_courses', __name__)

# ============ GET ALL COURSES ============

@admin_courses_bp.route('/', methods=['GET'], strict_slashes=False)
@jwt_required()
@admin_required
def get_all_courses():
    """Get all courses"""
    try:
        include_inactive = request.args.get('include_inactive', 'false').lower() == 'true'
        limit = request.args.get('limit', type=int)
        
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
        
        # Apply limit if specified
        if limit and limit > 0:
            courses = courses[:limit]
        
        return jsonify({
            'total': len(courses),
            'courses': courses
        }), 200
        
    except Exception as e:
        print(f"Error getting courses: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@admin_courses_bp.route('/<int:course_id>', methods=['GET'], strict_slashes=False)
@jwt_required()
@admin_required
def get_course(course_id):
    """Get course by ID with details"""
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
        
        # Get teachers count
        cursor.execute("""
            SELECT COUNT(DISTINCT ta.teacher_id) as teachers_count
            FROM teacher_assignments ta
            JOIN sections s ON ta.section_id = s.id
            JOIN subjects sub ON s.subject_id = sub.id
            WHERE sub.course_id = %s
        """, (course_id,))
        course['teachers_count'] = cursor.fetchone()['teachers_count']
        
        # Get students count
        cursor.execute("""
            SELECT COUNT(DISTINCT e.student_id) as students_count
            FROM enrollments e
            JOIN sections s ON e.section_id = s.id
            JOIN subjects sub ON s.subject_id = sub.id
            WHERE sub.course_id = %s AND e.status = 'approved'
        """, (course_id,))
        course['students_count'] = cursor.fetchone()['students_count']
        
        cursor.close()
        
        return jsonify({
            'course': course,
            'subjects': subjects
        }), 200
        
    except Exception as e:
        print(f"Error getting course: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@admin_courses_bp.route('/', methods=['POST'], strict_slashes=False)
@jwt_required()
@admin_required
def create_course():
    """Create a new course"""
    try:
        data = request.get_json()
        print(f"📡 Creating course with data: {data}")
        
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
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@admin_courses_bp.route('/<int:course_id>', methods=['PUT'], strict_slashes=False)
@jwt_required()
@admin_required
def update_course(course_id):
    """Update a course"""
    try:
        data = request.get_json()
        print(f"📡 Updating course {course_id} with data: {data}")
        
        # Check if course exists
        course = Course.get_by_id(course_id)
        if not course:
            print(f"❌ Course {course_id} not found")
            return jsonify({'error': 'Course not found'}), 404
        
        print(f"✅ Found course: {course}")
        
        # If code is being changed, check for duplicates
        if 'code' in data and data['code'] != course['code']:
            print(f"🔍 Checking for duplicate code: {data['code']}")
            existing = Course.get_by_code(data['code'].upper())
            if existing and existing['id'] != course_id:
                print(f"❌ Duplicate code found: {existing}")
                return jsonify({'error': 'Course code already exists'}), 400
        
        # Update the course
        print(f"📝 Updating course with fields: {list(data.keys())}")
        Course.update(course_id, **data)
        
        return jsonify({'message': 'Course updated successfully'}), 200
        
    except Exception as e:
        print(f"❌ Error updating course: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@admin_courses_bp.route('/<int:course_id>', methods=['DELETE'], strict_slashes=False)
@jwt_required()
@admin_required
def delete_course(course_id):
    """Delete a course"""
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
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@admin_courses_bp.route('/<int:course_id>/toggle-status', methods=['POST'], strict_slashes=False)
@jwt_required()
@admin_required
def toggle_course_status(course_id):
    """Activate/deactivate a course"""
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
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500