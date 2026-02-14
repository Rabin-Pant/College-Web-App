from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from utils.database import mysql
from utils.decorators import teacher_required

teacher_schedule_bp = Blueprint('teacher_schedule', __name__)

@teacher_schedule_bp.route('/', methods=['GET'], strict_slashes=False)
@jwt_required()
@teacher_required
def get_teacher_schedule():
    """Get teacher's weekly schedule"""
    try:
        teacher_id = get_jwt_identity()
        
        cursor = mysql.connection.cursor()
        cursor.execute("""
            SELECT 
                sch.*,
                s.id as section_id,
                s.name as section_name,
                sub.id as subject_id,
                sub.code as subject_code,
                sub.name as subject_name,
                sub.credits,
                c.id as course_id,
                c.name as course_name,
                c.code as course_code
            FROM schedules sch
            JOIN sections s ON sch.section_id = s.id
            JOIN subjects sub ON s.subject_id = sub.id
            JOIN courses c ON sub.course_id = c.id
            JOIN teacher_assignments ta ON s.id = ta.section_id
            WHERE ta.teacher_id = %s
            ORDER BY FIELD(sch.day, 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'), sch.start_time
        """, (teacher_id,))
        
        schedule_items = cursor.fetchall()
        
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
        print(f"Error getting teacher schedule: {e}")
        return jsonify({'error': str(e)}), 500


@teacher_schedule_bp.route('/today', methods=['GET'], strict_slashes=False)
@jwt_required()
@teacher_required
def get_today_schedule():
    """Get teacher's schedule for today"""
    try:
        teacher_id = get_jwt_identity()
        from datetime import datetime
        today = datetime.now().strftime('%A')  # Monday, Tuesday, etc.
        
        cursor = mysql.connection.cursor()
        cursor.execute("""
            SELECT 
                sch.*,
                s.id as section_id,
                s.name as section_name,
                sub.id as subject_id,
                sub.code as subject_code,
                sub.name as subject_name,
                c.id as course_id,
                c.name as course_name,
                c.code as course_code
            FROM schedules sch
            JOIN sections s ON sch.section_id = s.id
            JOIN subjects sub ON s.subject_id = sub.id
            JOIN courses c ON sub.course_id = c.id
            JOIN teacher_assignments ta ON s.id = ta.section_id
            WHERE ta.teacher_id = %s AND sch.day = %s
            ORDER BY sch.start_time
        """, (teacher_id, today))
        
        schedule = cursor.fetchall()
        cursor.close()
        
        return jsonify({
            'day': today,
            'schedule': schedule
        }), 200
        
    except Exception as e:
        print(f"Error getting today's schedule: {e}")
        return jsonify({'error': str(e)}), 500


@teacher_schedule_bp.route('/week/<string:date>', methods=['GET'], strict_slashes=False)
@jwt_required()
@teacher_required
def get_week_schedule(date):
    """Get schedule for a specific week"""
    try:
        teacher_id = get_jwt_identity()
        
        # This would need more complex logic to get week starting from date
        # For now, return all schedule
        return get_teacher_schedule()
        
    except Exception as e:
        print(f"Error getting week schedule: {e}")
        return jsonify({'error': str(e)}), 500