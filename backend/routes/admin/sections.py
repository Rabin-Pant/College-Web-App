from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from utils.database import mysql
from utils.decorators import admin_required
from models.section import Section
from models.subject import Subject
from models.teacher_assignment import TeacherAssignment

admin_sections_bp = Blueprint('admin_sections', __name__)

# ============ GET ALL SECTIONS ============

@admin_sections_bp.route('/', methods=['GET'], strict_slashes=False)
@jwt_required()
@admin_required
def get_all_sections():
    """Get all sections with filters"""
    try:
        academic_year = request.args.get('academic_year')
        semester = request.args.get('semester')
        subject_id = request.args.get('subject_id', type=int)
        course_id = request.args.get('course_id', type=int)
        limit = request.args.get('limit', type=int)
        
        cursor = mysql.connection.cursor()
        query = """
            SELECT 
                s.id as section_id,
                s.name as section_name,
                s.academic_year,
                s.semester as academic_semester,
                s.capacity,
                s.enrolled_count,
                s.room,
                s.is_active,
                s.created_at,
                sub.id as subject_id,
                sub.code as subject_code,
                sub.name as subject_name,
                sub.credits,
                sub.semester as subject_semester,
                c.id as course_id,
                c.name as course_name,
                c.code as course_code,
                (SELECT GROUP_CONCAT(u.name SEPARATOR ', ') 
                 FROM teacher_assignments ta 
                 JOIN users u ON ta.teacher_id = u.id 
                 WHERE ta.section_id = s.id) as teachers
            FROM sections s
            JOIN subjects sub ON s.subject_id = sub.id
            JOIN courses c ON sub.course_id = c.id
            WHERE 1=1
        """
        params = []
        
        if academic_year:
            query += " AND s.academic_year = %s"
            params.append(academic_year)
        if semester:
            query += " AND s.semester = %s"
            params.append(semester)
        if subject_id:
            query += " AND s.subject_id = %s"
            params.append(subject_id)
        if course_id:
            query += " AND c.id = %s"
            params.append(course_id)
            
        query += " ORDER BY c.name, sub.semester, s.name"
        
        cursor.execute(query, params)
        sections = cursor.fetchall()
        
        # Apply limit if specified
        if limit and limit > 0:
            sections = sections[:limit]
        
        cursor.close()
        
        return jsonify({
            'total': len(sections),
            'sections': sections
        }), 200
        
    except Exception as e:
        print(f"Error getting sections: {e}")
        return jsonify({'error': str(e)}), 500


@admin_sections_bp.route('/<int:section_id>', methods=['GET'], strict_slashes=False)
@jwt_required()
@admin_required
def get_section(section_id):
    """Get section by ID with details"""
    try:
        section = Section.get_by_id(section_id)
        if not section:
            return jsonify({'error': 'Section not found'}), 404
        
        # Get teachers assigned to this section
        teachers = TeacherAssignment.get_by_section(section_id)
        
        # Get schedule
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM schedules WHERE section_id = %s ORDER BY day, start_time", (section_id,))
        schedule = cursor.fetchall()
        
        # Get enrolled students
        cursor.execute("""
            SELECT 
                u.id,
                u.name,
                u.email,
                sp.student_id,
                e.enrollment_date,
                e.status
            FROM enrollments e
            JOIN users u ON e.student_id = u.id
            JOIN student_profiles sp ON u.id = sp.user_id
            WHERE e.section_id = %s AND e.status = 'approved'
            ORDER BY u.name
        """, (section_id,))
        students = cursor.fetchall()
        
        cursor.close()
        
        return jsonify({
            'section': section,
            'teachers': teachers,
            'schedule': schedule,
            'students': students,
            'students_count': len(students)
        }), 200
        
    except Exception as e:
        print(f"Error getting section: {e}")
        return jsonify({'error': str(e)}), 500


@admin_sections_bp.route('/', methods=['POST'], strict_slashes=False)
@jwt_required()
@admin_required
def create_section():
    """Create a new section"""
    try:
        data = request.get_json()
        
        required_fields = ['subject_id', 'name', 'academic_year', 'semester']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Verify subject exists
        subject = Subject.get_by_id(data['subject_id'])
        if not subject:
            return jsonify({'error': 'Subject not found'}), 404
        
        section_id = Section.create(
            subject_id=data['subject_id'],
            name=data['name'].upper(),
            academic_year=data['academic_year'],
            semester=data['semester'],
            capacity=data.get('capacity', 30),
            room=data.get('room')
        )
        
        return jsonify({
            'message': 'Section created successfully',
            'section_id': section_id
        }), 201
        
    except Exception as e:
        print(f"Error creating section: {e}")
        return jsonify({'error': str(e)}), 500


@admin_sections_bp.route('/<int:section_id>', methods=['PUT'], strict_slashes=False)
@jwt_required()
@admin_required
def update_section(section_id):
    """Update a section"""
    try:
        data = request.get_json()
        
        section = Section.get_by_id(section_id)
        if not section:
            return jsonify({'error': 'Section not found'}), 404
        
        Section.update(section_id, **data)
        
        return jsonify({'message': 'Section updated successfully'}), 200
        
    except Exception as e:
        print(f"Error updating section: {e}")
        return jsonify({'error': str(e)}), 500


@admin_sections_bp.route('/<int:section_id>', methods=['DELETE'], strict_slashes=False)
@jwt_required()
@admin_required
def delete_section(section_id):
    """Delete a section"""
    try:
        section = Section.get_by_id(section_id)
        if not section:
            return jsonify({'error': 'Section not found'}), 404
        
        # Check if section has enrollments
        cursor = mysql.connection.cursor()
        cursor.execute("""
            SELECT COUNT(*) as count FROM enrollments 
            WHERE section_id = %s AND status = 'approved'
        """, (section_id,))
        result = cursor.fetchone()
        cursor.close()
        
        if result['count'] > 0:
            return jsonify({'error': 'Cannot delete section with enrolled students'}), 400
        
        Section.delete(section_id)
        
        return jsonify({'message': 'Section deleted successfully'}), 200
        
    except Exception as e:
        print(f"Error deleting section: {e}")
        return jsonify({'error': str(e)}), 500


@admin_sections_bp.route('/available', methods=['GET'], strict_slashes=False)
@jwt_required()
@admin_required
def get_available_sections():
    """Get sections with available seats"""
    try:
        academic_year = request.args.get('academic_year')
        semester = request.args.get('semester')
        
        sections = Section.get_available(academic_year, semester)
        
        return jsonify({
            'total': len(sections),
            'sections': sections
        }), 200
        
    except Exception as e:
        print(f"Error getting available sections: {e}")
        return jsonify({'error': str(e)}), 500


@admin_sections_bp.route('/<int:section_id>/enrollments', methods=['GET'], strict_slashes=False)
@jwt_required()
@admin_required
def get_section_enrollments(section_id):
    """Get all enrollments for a section"""
    try:
        cursor = mysql.connection.cursor()
        cursor.execute("""
            SELECT 
                e.id as enrollment_id,
                e.student_id,
                e.status,
                e.enrollment_date,
                u.name as student_name,
                u.email as student_email,
                sp.student_id as student_number,
                sp.major
            FROM enrollments e
            JOIN users u ON e.student_id = u.id
            JOIN student_profiles sp ON u.id = sp.user_id
            WHERE e.section_id = %s
            ORDER BY e.enrollment_date DESC
        """, (section_id,))
        
        enrollments = cursor.fetchall()
        cursor.close()
        
        return jsonify({
            'section_id': section_id,
            'total': len(enrollments),
            'enrollments': enrollments
        }), 200
        
    except Exception as e:
        print(f"Error getting section enrollments: {e}")
        return jsonify({'error': str(e)}), 500


@admin_sections_bp.route('/stats', methods=['GET'], strict_slashes=False)
@jwt_required()
@admin_required
def get_sections_stats():
    """Get statistics about sections"""
    try:
        cursor = mysql.connection.cursor()
        
        # Total sections
        cursor.execute("SELECT COUNT(*) as count FROM sections")
        total_sections = cursor.fetchone()['count']
        
        # Active sections
        cursor.execute("SELECT COUNT(*) as count FROM sections WHERE is_active = TRUE")
        active_sections = cursor.fetchone()['count']
        
        # Sections by semester
        cursor.execute("""
            SELECT semester, COUNT(*) as count 
            FROM sections 
            GROUP BY semester 
            ORDER BY semester DESC
        """)
        by_semester = cursor.fetchall()
        
        # Total capacity vs enrolled
        cursor.execute("""
            SELECT 
                SUM(capacity) as total_capacity,
                SUM(enrolled_count) as total_enrolled
            FROM sections
        """)
        capacity_stats = cursor.fetchone()
        
        cursor.close()
        
        return jsonify({
            'total_sections': total_sections,
            'active_sections': active_sections,
            'inactive_sections': total_sections - active_sections,
            'by_semester': by_semester,
            'total_capacity': capacity_stats['total_capacity'] or 0,
            'total_enrolled': capacity_stats['total_enrolled'] or 0,
            'utilization': round((capacity_stats['total_enrolled'] or 0) / (capacity_stats['total_capacity'] or 1) * 100, 2)
        }), 200
        
    except Exception as e:
        print(f"Error getting sections stats: {e}")
        return jsonify({'error': str(e)}), 500


@admin_sections_bp.route('/<int:section_id>/schedule', methods=['GET'], strict_slashes=False)
@jwt_required()
@admin_required
def get_section_schedule(section_id):
    """Get schedule for a section"""
    try:
        cursor = mysql.connection.cursor()
        cursor.execute("""
            SELECT * FROM schedules 
            WHERE section_id = %s 
            ORDER BY FIELD(day, 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'), start_time
        """, (section_id,))
        
        schedule = cursor.fetchall()
        cursor.close()
        
        return jsonify({
            'section_id': section_id,
            'schedule': schedule
        }), 200
        
    except Exception as e:
        print(f"Error getting section schedule: {e}")
        return jsonify({'error': str(e)}), 500


@admin_sections_bp.route('/<int:section_id>/schedule', methods=['POST'], strict_slashes=False)
@jwt_required()
@admin_required
def add_schedule_entry(section_id):
    """Add a schedule entry for a section"""
    try:
        data = request.get_json()
        
        required_fields = ['day', 'start_time', 'end_time']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        cursor = mysql.connection.cursor()
        
        # Check for conflicts
        cursor.execute("""
            SELECT id FROM schedules 
            WHERE section_id = %s AND day = %s 
            AND (
                (start_time <= %s AND end_time > %s) OR
                (start_time < %s AND end_time >= %s)
            )
        """, (section_id, data['day'], data['start_time'], data['start_time'], data['end_time'], data['end_time']))
        
        if cursor.fetchone():
            cursor.close()
            return jsonify({'error': 'Schedule conflict detected'}), 400
        
        cursor.execute("""
            INSERT INTO schedules (section_id, day, start_time, end_time, room)
            VALUES (%s, %s, %s, %s, %s)
        """, (section_id, data['day'], data['start_time'], data['end_time'], data.get('room')))
        
        mysql.connection.commit()
        schedule_id = cursor.lastrowid
        cursor.close()
        
        return jsonify({
            'message': 'Schedule added successfully',
            'schedule_id': schedule_id
        }), 201
        
    except Exception as e:
        print(f"Error adding schedule: {e}")
        return jsonify({'error': str(e)}), 500


@admin_sections_bp.route('/schedule/<int:schedule_id>', methods=['DELETE'], strict_slashes=False)
@jwt_required()
@admin_required
def delete_schedule_entry(schedule_id):
    """Delete a schedule entry"""
    try:
        cursor = mysql.connection.cursor()
        cursor.execute("DELETE FROM schedules WHERE id = %s", (schedule_id,))
        mysql.connection.commit()
        affected = cursor.rowcount
        cursor.close()
        
        if affected:
            return jsonify({'message': 'Schedule deleted successfully'}), 200
        else:
            return jsonify({'error': 'Schedule not found'}), 404
            
    except Exception as e:
        print(f"Error deleting schedule: {e}")
        return jsonify({'error': str(e)}), 500