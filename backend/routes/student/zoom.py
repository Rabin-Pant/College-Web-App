from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from utils.database import mysql
from utils.decorators import student_required
from datetime import datetime

student_zoom_bp = Blueprint('student_zoom', __name__)

@student_zoom_bp.route('/section/<int:section_id>', methods=['GET'], strict_slashes=False)
@jwt_required()
@student_required
def get_section_zoom_meetings(section_id):
    """Get all Zoom meetings for a section"""
    try:
        student_id = get_jwt_identity()
        
        # Verify student is enrolled in this section
        cursor = mysql.connection.cursor()
        cursor.execute("""
            SELECT id FROM enrollments 
            WHERE student_id = %s AND section_id = %s AND status = 'approved'
        """, (student_id, section_id))
        
        if not cursor.fetchone():
            cursor.close()
            return jsonify({'error': 'You are not enrolled in this section'}), 403
        
        # Get upcoming meetings
        cursor.execute("""
            SELECT 
                zm.id,
                zm.teacher_id,
                zm.topic,
                zm.description,
                zm.meeting_date,
                zm.start_time,
                zm.duration_minutes,
                zm.meeting_link,
                zm.meeting_id,
                zm.password,
                zm.recording_link,
                zm.created_at,
                u.name as teacher_name,
                u.email as teacher_email
            FROM zoom_meetings zm
            JOIN users u ON zm.teacher_id = u.id
            WHERE zm.section_id = %s 
                AND CONCAT(zm.meeting_date, ' ', zm.start_time) >= NOW()
            ORDER BY zm.meeting_date, zm.start_time
        """, (section_id,))
        
        meetings = cursor.fetchall()
        
        # Convert time objects to strings
        for meeting in meetings:
            if meeting.get('start_time'):
                meeting['start_time'] = str(meeting['start_time'])
            if meeting.get('meeting_date'):
                meeting['meeting_date'] = str(meeting['meeting_date'])
        
        cursor.close()
        
        return jsonify({'meetings': meetings}), 200
        
    except Exception as e:
        print(f"❌ Error getting zoom meetings: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@student_zoom_bp.route('/upcoming', methods=['GET'], strict_slashes=False)
@jwt_required()
@student_required
def get_upcoming_meetings():
    """Get all upcoming meetings for the student across all sections"""
    try:
        student_id = get_jwt_identity()
        
        cursor = mysql.connection.cursor()
        cursor.execute("""
            SELECT 
                zm.*,
                s.name as section_name,
                sub.code as subject_code,
                sub.name as subject_name,
                c.name as course_name,
                u.name as teacher_name
            FROM zoom_meetings zm
            JOIN sections s ON zm.section_id = s.id
            JOIN subjects sub ON s.subject_id = sub.id
            JOIN courses c ON sub.course_id = c.id
            JOIN enrollments e ON s.id = e.section_id
            JOIN users u ON zm.teacher_id = u.id
            WHERE e.student_id = %s AND e.status = 'approved'
                AND CONCAT(zm.meeting_date, ' ', zm.start_time) >= NOW()
            ORDER BY zm.meeting_date, zm.start_time
            LIMIT 20
        """, (student_id,))
        
        meetings = cursor.fetchall()
        
        # Convert time objects to strings
        for meeting in meetings:
            if meeting.get('start_time'):
                meeting['start_time'] = str(meeting['start_time'])
            if meeting.get('meeting_date'):
                meeting['meeting_date'] = str(meeting['meeting_date'])
        
        cursor.close()
        
        return jsonify({
            'total': len(meetings),
            'meetings': meetings
        }), 200
        
    except Exception as e:
        print(f"Error getting upcoming meetings: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500