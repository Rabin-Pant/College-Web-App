from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from utils.database import mysql
from utils.decorators import teacher_required
from datetime import datetime, timedelta

teacher_bp = Blueprint('teacher', __name__)

@teacher_bp.route('/dashboard', methods=['GET'])
@jwt_required()
@teacher_required
def get_dashboard():
    """Get teacher dashboard with overview of all sections"""
    try:
        teacher_id = get_jwt_identity()
        
        cursor = mysql.connection.cursor()
        
        # Get teaching stats
        cursor.execute("""
            SELECT 
                COUNT(DISTINCT ta.section_id) as total_sections,
                COUNT(DISTINCT e.student_id) as total_students,
                COUNT(DISTINCT a.id) as total_assignments,
                COUNT(DISTINCT m.id) as total_materials,
                COUNT(DISTINCT zm.id) as total_meetings,
                (SELECT COUNT(*) FROM submissions s
                 JOIN assignments a ON s.assignment_id = a.id
                 JOIN teacher_assignments ta ON a.section_id = ta.section_id
                 WHERE ta.teacher_id = %s AND s.status = 'submitted') as pending_grading
            FROM teacher_assignments ta
            LEFT JOIN sections s ON ta.section_id = s.id
            LEFT JOIN enrollments e ON s.id = e.section_id AND e.status = 'approved'
            LEFT JOIN assignments a ON s.id = a.section_id
            LEFT JOIN materials m ON s.id = m.section_id
            LEFT JOIN zoom_meetings zm ON s.id = zm.section_id
            WHERE ta.teacher_id = %s
        """, (teacher_id, teacher_id))
        
        stats = cursor.fetchone()
        
        # Get recent sections
        cursor.execute("""
            SELECT 
                s.id as section_id,
                s.name as section_name,
                s.academic_year,
                s.semester,
                sub.code as subject_code,
                sub.name as subject_name,
                c.name as course_name,
                (SELECT COUNT(*) FROM enrollments e WHERE e.section_id = s.id AND e.status = 'approved') as student_count,
                (SELECT COUNT(*) FROM assignments a WHERE a.section_id = s.id) as assignment_count
            FROM teacher_assignments ta
            JOIN sections s ON ta.section_id = s.id
            JOIN subjects sub ON s.subject_id = sub.id
            JOIN courses c ON sub.course_id = c.id
            WHERE ta.teacher_id = %s
            ORDER BY s.academic_year DESC, s.semester DESC
            LIMIT 5
        """, (teacher_id,))
        
        recent_sections = cursor.fetchall()
        
        # Get upcoming deadlines (next 7 days)
        cursor.execute("""
            SELECT 
                a.id as assignment_id,
                a.title,
                a.due_date,
                a.points_possible,
                s.id as section_id,
                s.name as section_name,
                sub.code as subject_code,
                sub.name as subject_name,
                (SELECT COUNT(*) FROM submissions sub WHERE sub.assignment_id = a.id) as total_submissions,
                (SELECT COUNT(*) FROM submissions sub WHERE sub.assignment_id = a.id AND sub.status = 'submitted') as pending
            FROM assignments a
            JOIN sections s ON a.section_id = s.id
            JOIN subjects sub ON s.subject_id = sub.id
            JOIN teacher_assignments ta ON s.id = ta.section_id
            WHERE ta.teacher_id = %s 
                AND a.due_date BETWEEN NOW() AND DATE_ADD(NOW(), INTERVAL 7 DAY)
                AND a.is_published = TRUE
            ORDER BY a.due_date
        """, (teacher_id,))
        
        upcoming_deadlines = cursor.fetchall()
        
        # Get pending enrollments
        cursor.execute("""
            SELECT 
                e.id as enrollment_id,
                e.enrollment_date,
                u.id as student_id,
                u.name as student_name,
                u.email as student_email,
                s.id as section_id,
                s.name as section_name,
                sub.code as subject_code,
                sub.name as subject_name
            FROM enrollments e
            JOIN sections s ON e.section_id = s.id
            JOIN subjects sub ON s.subject_id = sub.id
            JOIN teacher_assignments ta ON s.id = ta.section_id
            JOIN users u ON e.student_id = u.id
            WHERE ta.teacher_id = %s AND e.status = 'pending'
            ORDER BY e.enrollment_date
        """, (teacher_id,))
        
        pending_enrollments = cursor.fetchall()
        
        cursor.close()
        
        return jsonify({
            'stats': stats,
            'recent_sections': recent_sections,
            'upcoming_deadlines': upcoming_deadlines,
            'pending_enrollments': pending_enrollments
        }), 200
        
    except Exception as e:
        print(f"Error getting teacher dashboard: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@teacher_bp.route('/sections', methods=['GET'])
@jwt_required()
@teacher_required
def get_all_sections():
    """Get all sections taught by the teacher"""
    try:
        teacher_id = get_jwt_identity()
        academic_year = request.args.get('academic_year')
        semester = request.args.get('semester')
        
        cursor = mysql.connection.cursor()
        query = """
            SELECT 
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
                (SELECT COUNT(*) FROM assignments a WHERE a.section_id = s.id) as assignment_count
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


@teacher_bp.route('/schedule', methods=['GET'])
@jwt_required()
@teacher_required
def get_weekly_schedule():
    """Get teacher's weekly schedule"""
    try:
        teacher_id = get_jwt_identity()
        
        cursor = mysql.connection.cursor()
        cursor.execute("""
            SELECT 
                sch.*,
                s.id as section_id,
                s.name as section_name,
                sub.code as subject_code,
                sub.name as subject_name,
                c.name as course_name,
                c.code as course_code
            FROM schedules sch
            JOIN sections s ON sch.section_id = s.id
            JOIN subjects sub ON s.subject_id = sub.id
            JOIN courses c ON sub.course_id = c.id
            JOIN teacher_assignments ta ON s.id = ta.section_id
            WHERE ta.teacher_id = %s
            ORDER BY FIELD(sch.day, 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'), sch.start_time
        """, (teacher_id,))
        
        schedule_items = cursor.fetchall()
        
        # Convert time objects to strings
        for item in schedule_items:
            if item.get('start_time'):
                item['start_time'] = str(item['start_time'])
            if item.get('end_time'):
                item['end_time'] = str(item['end_time'])
        
        # Group by day
        days = {}
        for item in schedule_items:
            day = item['day']
            if day not in days:
                days[day] = []
            days[day].append(item)
        
        cursor.close()
        
        return jsonify({
            'schedule': days,
            'raw': schedule_items
        }), 200
        
    except Exception as e:
        print(f"Error getting schedule: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500