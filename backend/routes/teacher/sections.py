from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from utils.database import mysql
from utils.decorators import teacher_required

teacher_sections_bp = Blueprint('teacher_sections', __name__)

@teacher_sections_bp.route('/', methods=['GET'], strict_slashes=False)
@jwt_required()
@teacher_required
def get_my_sections():
    """Get all sections assigned to the current teacher"""
    try:
        teacher_id = get_jwt_identity()
        academic_year = request.args.get('academic_year')
        semester = request.args.get('semester')
        
        cursor = mysql.connection.cursor()
        query = """
            SELECT 
                ta.id as assignment_id,
                s.id as section_id,
                s.name as section_name,
                s.academic_year,
                s.semester,
                s.capacity,
                s.enrolled_count,
                s.room,
                sub.id as subject_id,
                sub.code as subject_code,
                sub.name as subject_name,
                sub.credits,
                sub.semester as subject_semester,
                c.id as course_id,
                c.name as course_name,
                c.code as course_code,
                (SELECT COUNT(*) FROM enrollments e WHERE e.section_id = s.id AND e.status = 'approved') as student_count,
                (SELECT COUNT(*) FROM assignments a WHERE a.section_id = s.id) as assignment_count,
                (SELECT COUNT(*) FROM materials m WHERE m.section_id = s.id) as material_count,
                (SELECT COUNT(*) FROM zoom_meetings zm WHERE zm.section_id = s.id AND zm.meeting_date >= CURDATE()) as upcoming_meetings
            FROM teacher_assignments ta
            JOIN sections s ON ta.section_id = s.id
            JOIN subjects sub ON s.subject_id = sub.id
            JOIN courses c ON sub.course_id = c.id
            WHERE ta.teacher_id = %s
        """
        params = [teacher_id]
        
        if academic_year:
            query += " AND s.academic_year = %s"
            params.append(academic_year)
        if semester:
            query += " AND s.semester = %s"
            params.append(semester)
            
        query += " ORDER BY c.name, sub.semester, s.name"
        
        cursor.execute(query, params)
        sections = cursor.fetchall()
        cursor.close()
        
        return jsonify({
            'total': len(sections),
            'sections': sections
        }), 200
        
    except Exception as e:
        print(f"Error getting teacher sections: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@teacher_sections_bp.route('/<int:section_id>', methods=['GET'], strict_slashes=False)
@jwt_required()
@teacher_required
def get_section_details(section_id):
    """Get detailed information about a specific section"""
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
        
        # Get section details with safe column names
        cursor.execute("""
            SELECT 
                s.id as section_id,
                s.name as section_name,
                s.academic_year,
                s.semester,
                s.capacity,
                s.enrolled_count,
                s.room,
                s.is_active,
                sub.id as subject_id,
                sub.code as subject_code,
                sub.name as subject_name,
                sub.credits,
                sub.semester as subject_semester,
                c.id as course_id,
                c.name as course_name,
                c.code as course_code
            FROM sections s
            JOIN subjects sub ON s.subject_id = sub.id
            JOIN courses c ON sub.course_id = c.id
            WHERE s.id = %s
        """, (section_id,))
        
        section = cursor.fetchone()
        
        if not section:
            cursor.close()
            return jsonify({'error': 'Section not found'}), 404
        
        # Get schedule
        cursor.execute("""
            SELECT 
                id,
                day,
               TIME_FORMAT(start_time, '%%H:%%i') as start_time,
               TIME_FORMAT(end_time, '%%H:%%i') as end_time,
                room
            FROM schedules 
            WHERE section_id = %s 
            ORDER BY FIELD(day, 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'), start_time
        """, (section_id,))
        schedule = cursor.fetchall()
        
        # Get enrolled students
        cursor.execute("""
            SELECT 
                u.id,
                u.name,
                u.email,
                u.profile_pic,
                sp.student_id,
                sp.major,
                e.enrollment_date,
                e.status
            FROM enrollments e
            JOIN users u ON e.student_id = u.id
            JOIN student_profiles sp ON u.id = sp.user_id
            WHERE e.section_id = %s AND e.status = 'approved'
            ORDER BY u.name
        """, (section_id,))
        students = cursor.fetchall()
        
        # Get pending enrollments
        cursor.execute("""
            SELECT 
                e.id as enrollment_id,
                u.id as student_id,
                u.name as student_name,
                u.email as student_email,
                sp.student_id,
                sp.major,
                e.enrollment_date
            FROM enrollments e
            JOIN users u ON e.student_id = u.id
            JOIN student_profiles sp ON u.id = sp.user_id
            WHERE e.section_id = %s AND e.status = 'pending'
            ORDER BY e.enrollment_date
        """, (section_id,))
        pending = cursor.fetchall()
        
        cursor.close()
        
        return jsonify({
            'section': section,
            'schedule': schedule,
            'students': students,
            'students_count': len(students),
            'pending_enrollments': pending,
            'pending_count': len(pending)
        }), 200
        
    except Exception as e:
        print(f"Error getting section details: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@teacher_sections_bp.route('/stats', methods=['GET'], strict_slashes=False)
@jwt_required()
@teacher_required
def get_teaching_stats():
    """Get teaching statistics for dashboard"""
    try:
        teacher_id = get_jwt_identity()
        
        cursor = mysql.connection.cursor()
        
        # Total sections
        cursor.execute("""
            SELECT COUNT(*) as count FROM teacher_assignments 
            WHERE teacher_id = %s
        """, (teacher_id,))
        total_sections = cursor.fetchone()['count']
        
        # Total students across all sections
        cursor.execute("""
            SELECT COUNT(DISTINCT e.student_id) as count
            FROM teacher_assignments ta
            JOIN sections s ON ta.section_id = s.id
            JOIN enrollments e ON s.id = e.section_id
            WHERE ta.teacher_id = %s AND e.status = 'approved'
        """, (teacher_id,))
        total_students = cursor.fetchone()['count']
        
        # Total assignments
        cursor.execute("""
            SELECT COUNT(DISTINCT a.id) as count
            FROM teacher_assignments ta
            JOIN sections s ON ta.section_id = s.id
            LEFT JOIN assignments a ON s.id = a.section_id
            WHERE ta.teacher_id = %s
        """, (teacher_id,))
        total_assignments = cursor.fetchone()['count']
        
        # Total materials
        cursor.execute("""
            SELECT COUNT(DISTINCT m.id) as count
            FROM teacher_assignments ta
            JOIN sections s ON ta.section_id = s.id
            LEFT JOIN materials m ON s.id = m.section_id
            WHERE ta.teacher_id = %s
        """, (teacher_id,))
        total_materials = cursor.fetchone()['count']
        
        # Pending enrollments
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM teacher_assignments ta
            JOIN sections s ON ta.section_id = s.id
            JOIN enrollments e ON s.id = e.section_id
            WHERE ta.teacher_id = %s AND e.status = 'pending'
        """, (teacher_id,))
        pending_enrollments = cursor.fetchone()['count']
        
        # Upcoming meetings
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM zoom_meetings zm
            JOIN teacher_assignments ta ON zm.section_id = ta.section_id
            WHERE ta.teacher_id = %s AND zm.meeting_date >= CURDATE()
        """, (teacher_id,))
        upcoming_meetings = cursor.fetchone()['count']
        
        # Pending grading
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM submissions s
            JOIN assignments a ON s.assignment_id = a.id
            JOIN teacher_assignments ta ON a.section_id = ta.section_id
            WHERE ta.teacher_id = %s AND s.status = 'submitted'
        """, (teacher_id,))
        pending_grading = cursor.fetchone()['count']
        
        cursor.close()
        
        return jsonify({
            'total_sections': total_sections,
            'total_students': total_students,
            'total_assignments': total_assignments,
            'total_materials': total_materials,
            'pending_enrollments': pending_enrollments,
            'upcoming_meetings': upcoming_meetings,
            'pending_grading': pending_grading
        }), 200
        
    except Exception as e:
        print(f"Error getting teaching stats: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500