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
        
        # Convert timedelta objects to strings
        formatted_items = []
        for item in schedule_items:
            formatted_item = dict(item)
            # Convert time fields to string
            if 'start_time' in formatted_item and formatted_item['start_time']:
                formatted_item['start_time'] = str(formatted_item['start_time'])
            if 'end_time' in formatted_item and formatted_item['end_time']:
                formatted_item['end_time'] = str(formatted_item['end_time'])
            formatted_items.append(formatted_item)
        
        # Group by day
        days = {}
        for item in formatted_items:
            day = item['day']
            if day not in days:
                days[day] = []
            days[day].append(item)
        
        cursor.close()
        
        return jsonify({
            'schedule': days,
            'raw': formatted_items
        }), 200
        
    except Exception as e:
        print(f"Error getting teacher schedule: {e}")
        return jsonify({'error': str(e)}), 500