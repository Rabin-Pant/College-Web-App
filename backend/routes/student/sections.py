from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from utils.database import mysql
from utils.decorators import student_required

student_sections_bp = Blueprint('student_sections', __name__)

# ============ GET STUDENT'S ENROLLED SECTIONS ============

@student_sections_bp.route('/', methods=['GET'], strict_slashes=False)
@jwt_required()
@student_required
def get_my_sections():
    """Get sections the student is enrolled in"""
    try:
        student_id = get_jwt_identity()
        
        cursor = mysql.connection.cursor()
        cursor.execute("""
            SELECT 
                e.id as enrollment_id,
                s.id as section_id,
                s.name as section_name,
                s.academic_year,
                s.semester,
                s.room,
                sub.id as subject_id,
                sub.code as subject_code,
                sub.name as subject_name,
                sub.credits,
                c.id as course_id,
                c.name as course_name,
                c.code as course_code,
                u.id as teacher_id,
                u.name as teacher_name,
                sch.day,
                sch.start_time,
                sch.end_time
            FROM enrollments e
            JOIN sections s ON e.section_id = s.id
            JOIN subjects sub ON s.subject_id = sub.id
            JOIN courses c ON sub.course_id = c.id
            LEFT JOIN teacher_assignments ta ON s.id = ta.section_id
            LEFT JOIN users u ON ta.teacher_id = u.id
            LEFT JOIN schedules sch ON s.id = sch.section_id
            WHERE e.student_id = %s AND e.status = 'approved'
            ORDER BY c.name, sub.semester
        """, (student_id,))
        
        rows = cursor.fetchall()
        
        # Convert timedelta objects to strings for JSON serialization
        sections = []
        for row in rows:
            section_dict = dict(row)
            # Convert time fields to strings if they exist
            if section_dict.get('start_time'):
                section_dict['start_time'] = str(section_dict['start_time'])
            if section_dict.get('end_time'):
                section_dict['end_time'] = str(section_dict['end_time'])
            sections.append(section_dict)
        
        cursor.close()
        
        return jsonify({'sections': sections}), 200
        
    except Exception as e:
        print(f"Error getting student sections: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


# ============ GET SINGLE SECTION DETAILS ============

@student_sections_bp.route('/<int:section_id>', methods=['GET'], strict_slashes=False)
@jwt_required()
@student_required
def get_section_details(section_id):
    """Get detailed information about a specific section"""
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
        
        # Get section details
        cursor.execute("""
            SELECT 
                s.id as section_id,
                s.name as section_name,
                s.academic_year,
                s.semester,
                s.room,
                sub.id as subject_id,
                sub.code as subject_code,
                sub.name as subject_name,
                sub.credits,
                c.id as course_id,
                c.name as course_name,
                c.code as course_code,
                u.id as teacher_id,
                u.name as teacher_name,
                u.email as teacher_email
            FROM sections s
            JOIN subjects sub ON s.subject_id = sub.id
            JOIN courses c ON sub.course_id = c.id
            LEFT JOIN teacher_assignments ta ON s.id = ta.section_id
            LEFT JOIN users u ON ta.teacher_id = u.id
            WHERE s.id = %s
        """, (section_id,))
        
        section = cursor.fetchone()
        
        # Get schedule
        cursor.execute("""
            SELECT 
                id,
                day,
                start_time,
                end_time,
                room
            FROM schedules 
            WHERE section_id = %s 
            ORDER BY FIELD(day, 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'), start_time
        """, (section_id,))
        
        schedule_rows = cursor.fetchall()
        
        # Convert timedelta objects to strings in schedule
        schedule = []
        for row in schedule_rows:
            schedule_dict = dict(row)
            if schedule_dict.get('start_time'):
                schedule_dict['start_time'] = str(schedule_dict['start_time'])
            if schedule_dict.get('end_time'):
                schedule_dict['end_time'] = str(schedule_dict['end_time'])
            schedule.append(schedule_dict)
        
        cursor.close()
        
        return jsonify({
            'section': section,
            'schedule': schedule
        }), 200
        
    except Exception as e:
        print(f"Error getting section details: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


# ============ GET AVAILABLE SECTIONS FOR ENROLLMENT ============

@student_sections_bp.route('/available', methods=['GET'], strict_slashes=False)
@jwt_required()
@student_required
def get_available_sections():
    """Get sections available for enrollment"""
    try:
        student_id = get_jwt_identity()
        academic_year = request.args.get('academic_year')
        semester = request.args.get('semester')
        course_id = request.args.get('course_id', type=int)
        
        cursor = mysql.connection.cursor()
        
        # Get sections the student is already enrolled in or has pending requests
        cursor.execute("""
            SELECT section_id FROM enrollments 
            WHERE student_id = %s AND status IN ('approved', 'pending')
        """, (student_id,))
        enrolled_sections = [row['section_id'] for row in cursor.fetchall()]
        
        # Build query for available sections
        query = """
            SELECT 
                s.id as section_id,
                s.name as section_name,
                s.academic_year,
                s.semester,
                s.capacity,
                s.enrolled_count,
                (s.capacity - s.enrolled_count) as available_seats,
                s.room,
                sub.id as subject_id,
                sub.code as subject_code,
                sub.name as subject_name,
                sub.credits,
                sub.semester as subject_semester,
                c.id as course_id,
                c.name as course_name,
                c.code as course_code,
                u.id as teacher_id,
                u.name as teacher_name
            FROM sections s
            JOIN subjects sub ON s.subject_id = sub.id
            JOIN courses c ON sub.course_id = c.id
            LEFT JOIN teacher_assignments ta ON s.id = ta.section_id
            LEFT JOIN users u ON ta.teacher_id = u.id
            WHERE s.is_active = TRUE 
                AND s.enrolled_count < s.capacity
        """
        params = []
        
        # Exclude sections the student is already enrolled in or has pending
        if enrolled_sections:
            placeholders = ','.join(['%s'] * len(enrolled_sections))
            query += f" AND s.id NOT IN ({placeholders})"
            params.extend(enrolled_sections)
        
        if academic_year:
            query += " AND s.academic_year = %s"
            params.append(academic_year)
        if semester:
            query += " AND s.semester = %s"
            params.append(semester)
        if course_id:
            query += " AND c.id = %s"
            params.append(course_id)
            
        query += " ORDER BY c.name, sub.semester, s.name"
        
        cursor.execute(query, params)
        sections = cursor.fetchall()
        cursor.close()
        
        return jsonify({
            'total': len(sections),
            'sections': sections
        }), 200
        
    except Exception as e:
        print(f"Error getting available sections: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


# ============ GET SECTIONS BY COURSE ============

@student_sections_bp.route('/course/<int:course_id>', methods=['GET'], strict_slashes=False)
@jwt_required()
@student_required
def get_sections_by_course(course_id):
    """Get available sections for a specific course"""
    try:
        student_id = get_jwt_identity()
        academic_year = request.args.get('academic_year')
        semester = request.args.get('semester')
        
        cursor = mysql.connection.cursor()
        
        # Get sections the student is already enrolled in
        cursor.execute("""
            SELECT section_id FROM enrollments 
            WHERE student_id = %s AND status IN ('approved', 'pending')
        """, (student_id,))
        enrolled_sections = [row['section_id'] for row in cursor.fetchall()]
        
        query = """
            SELECT 
                s.id as section_id,
                s.name as section_name,
                s.academic_year,
                s.semester,
                s.capacity,
                s.enrolled_count,
                (s.capacity - s.enrolled_count) as available_seats,
                s.room,
                sub.id as subject_id,
                sub.code as subject_code,
                sub.name as subject_name,
                sub.credits,
                sub.semester as subject_semester,
                u.id as teacher_id,
                u.name as teacher_name
            FROM sections s
            JOIN subjects sub ON s.subject_id = sub.id
            LEFT JOIN teacher_assignments ta ON s.id = ta.section_id
            LEFT JOIN users u ON ta.teacher_id = u.id
            WHERE s.is_active = TRUE 
                AND s.enrolled_count < s.capacity
                AND sub.course_id = %s
        """
        params = [course_id]
        
        if enrolled_sections:
            placeholders = ','.join(['%s'] * len(enrolled_sections))
            query += f" AND s.id NOT IN ({placeholders})"
            params.extend(enrolled_sections)
        
        if academic_year:
            query += " AND s.academic_year = %s"
            params.append(academic_year)
        if semester:
            query += " AND s.semester = %s"
            params.append(semester)
            
        query += " ORDER BY sub.semester, s.name"
        
        cursor.execute(query, params)
        sections = cursor.fetchall()
        cursor.close()
        
        return jsonify({
            'course_id': course_id,
            'total': len(sections),
            'sections': sections
        }), 200
        
    except Exception as e:
        print(f"Error getting sections by course: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


# ============ SEARCH SECTIONS ============

@student_sections_bp.route('/search', methods=['GET'], strict_slashes=False)
@jwt_required()
@student_required
def search_sections():
    """Search for sections by keyword"""
    try:
        student_id = get_jwt_identity()
        keyword = request.args.get('q', '')
        
        if not keyword or len(keyword) < 2:
            return jsonify({'sections': [], 'total': 0}), 200
        
        cursor = mysql.connection.cursor()
        
        # Get sections the student is already enrolled in
        cursor.execute("""
            SELECT section_id FROM enrollments 
            WHERE student_id = %s AND status IN ('approved', 'pending')
        """, (student_id,))
        enrolled_sections = [row['section_id'] for row in cursor.fetchall()]
        
        search_term = f"%{keyword}%"
        query = """
            SELECT 
                s.id as section_id,
                s.name as section_name,
                s.academic_year,
                s.semester,
                s.capacity,
                s.enrolled_count,
                (s.capacity - s.enrolled_count) as available_seats,
                s.room,
                sub.id as subject_id,
                sub.code as subject_code,
                sub.name as subject_name,
                sub.credits,
                sub.semester as subject_semester,
                c.id as course_id,
                c.name as course_name,
                c.code as course_code,
                u.id as teacher_id,
                u.name as teacher_name
            FROM sections s
            JOIN subjects sub ON s.subject_id = sub.id
            JOIN courses c ON sub.course_id = c.id
            LEFT JOIN teacher_assignments ta ON s.id = ta.section_id
            LEFT JOIN users u ON ta.teacher_id = u.id
            WHERE s.is_active = TRUE 
                AND s.enrolled_count < s.capacity
                AND (
                    sub.name LIKE %s 
                    OR sub.code LIKE %s 
                    OR c.name LIKE %s 
                    OR c.code LIKE %s
                    OR u.name LIKE %s
                )
        """
        params = [search_term, search_term, search_term, search_term, search_term]
        
        if enrolled_sections:
            placeholders = ','.join(['%s'] * len(enrolled_sections))
            query += f" AND s.id NOT IN ({placeholders})"
            params.extend(enrolled_sections)
            
        query += " ORDER BY c.name, sub.semester, s.name LIMIT 20"
        
        cursor.execute(query, params)
        sections = cursor.fetchall()
        cursor.close()
        
        return jsonify({
            'total': len(sections),
            'sections': sections
        }), 200
        
    except Exception as e:
        print(f"Error searching sections: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500