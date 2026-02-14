from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from utils.database import mysql
from utils.decorators import teacher_required
from datetime import datetime

teacher_zoom_bp = Blueprint('teacher_zoom', __name__)

# ============ CREATE ZOOM MEETING ============

@teacher_zoom_bp.route('/', methods=['POST'], strict_slashes=False)
@jwt_required()
@teacher_required
def create_meeting():
    """Create a new Zoom meeting for a section"""
    try:
        teacher_id = get_jwt_identity()
        data = request.get_json()
        
        print(f"📡 Creating zoom meeting with data: {data}")
        
        required_fields = ['section_id', 'topic', 'meeting_date', 'start_time']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Verify teacher is assigned to this section
        cursor = mysql.connection.cursor()
        cursor.execute("""
            SELECT ta.id FROM teacher_assignments ta
            WHERE ta.teacher_id = %s AND ta.section_id = %s
        """, (teacher_id, data['section_id']))
        
        if not cursor.fetchone():
            cursor.close()
            return jsonify({'error': 'You are not assigned to this section'}), 403
        
        # Insert meeting
        cursor.execute("""
            INSERT INTO zoom_meetings (
                teacher_id, section_id, topic, description,
                meeting_date, start_time, duration_minutes,
                meeting_link, meeting_id, password
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            teacher_id,
            data['section_id'],
            data['topic'],
            data.get('description'),
            data['meeting_date'],
            data['start_time'],
            data.get('duration_minutes', 60),
            data.get('meeting_link'),
            data.get('meeting_id'),
            data.get('password')
        ))
        
        mysql.connection.commit()
        meeting_id = cursor.lastrowid
        cursor.close()
        
        return jsonify({
            'message': 'Meeting created successfully',
            'meeting_id': meeting_id
        }), 201
        
    except Exception as e:
        print(f"❌ Error creating meeting: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


# ============ GET UPCOMING MEETINGS FOR TEACHER ============

@teacher_zoom_bp.route('/upcoming', methods=['GET'], strict_slashes=False)
@jwt_required()
@teacher_required
def get_upcoming_meetings():
    """Get all upcoming meetings for the teacher"""
    try:
        teacher_id = get_jwt_identity()
        
        cursor = mysql.connection.cursor()
        cursor.execute("""
            SELECT 
                zm.*,
                s.name as section_name,
                sub.code as subject_code,
                sub.name as subject_name,
                c.name as course_name
            FROM zoom_meetings zm
            JOIN sections s ON zm.section_id = s.id
            JOIN subjects sub ON s.subject_id = sub.id
            JOIN courses c ON sub.course_id = c.id
            WHERE zm.teacher_id = %s 
                AND CONCAT(zm.meeting_date, ' ', zm.start_time) >= NOW()
            ORDER BY zm.meeting_date, zm.start_time
            LIMIT 10
        """, (teacher_id,))
        
        meetings = cursor.fetchall()
        
        # Convert time objects to strings
        for meeting in meetings:
            if meeting.get('start_time'):
                meeting['start_time'] = str(meeting['start_time'])
        
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


# ============ GET MEETINGS BY SECTION ============

@teacher_zoom_bp.route('/section/<int:section_id>', methods=['GET'], strict_slashes=False)
@jwt_required()
@teacher_required
def get_section_meetings(section_id):
    """Get all meetings for a specific section"""
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
        
        # Get meetings
        cursor.execute("""
            SELECT * FROM zoom_meetings 
            WHERE section_id = %s
            ORDER BY meeting_date DESC, start_time DESC
        """, (section_id,))
        
        meetings = cursor.fetchall()
        
        # Convert time objects to strings
        for meeting in meetings:
            if meeting.get('start_time'):
                meeting['start_time'] = str(meeting['start_time'])
        
        cursor.close()
        
        return jsonify({
            'section_id': section_id,
            'total': len(meetings),
            'meetings': meetings
        }), 200
        
    except Exception as e:
        print(f"Error getting section meetings: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


# ============ UPDATE MEETING ============

@teacher_zoom_bp.route('/<int:meeting_id>', methods=['PUT'], strict_slashes=False)
@jwt_required()
@teacher_required
def update_meeting(meeting_id):
    """Update a meeting"""
    try:
        teacher_id = get_jwt_identity()
        data = request.get_json()
        
        cursor = mysql.connection.cursor()
        
        # Verify teacher owns the meeting
        cursor.execute("""
            SELECT id FROM zoom_meetings 
            WHERE id = %s AND teacher_id = %s
        """, (meeting_id, teacher_id))
        
        if not cursor.fetchone():
            cursor.close()
            return jsonify({'error': 'Meeting not found or unauthorized'}), 404
        
        # Build update query
        update_fields = []
        values = []
        
        allowed_fields = ['topic', 'description', 'meeting_date', 'start_time', 
                         'duration_minutes', 'meeting_link', 'meeting_id', 'password']
        
        for field in allowed_fields:
            if field in data:
                update_fields.append(f"{field} = %s")
                values.append(data[field])
        
        if update_fields:
            query = f"UPDATE zoom_meetings SET {', '.join(update_fields)} WHERE id = %s"
            values.append(meeting_id)
            cursor.execute(query, tuple(values))
            mysql.connection.commit()
        
        cursor.close()
        
        return jsonify({'message': 'Meeting updated successfully'}), 200
        
    except Exception as e:
        print(f"Error updating meeting: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


# ============ ADD RECORDING LINK ============

@teacher_zoom_bp.route('/<int:meeting_id>/recording', methods=['PUT'], strict_slashes=False)
@jwt_required()
@teacher_required
def add_recording(meeting_id):
    """Add recording link after meeting"""
    try:
        teacher_id = get_jwt_identity()
        data = request.get_json()
        
        if 'recording_link' not in data:
            return jsonify({'error': 'Recording link is required'}), 400
        
        cursor = mysql.connection.cursor()
        
        # Verify teacher owns the meeting
        cursor.execute("""
            UPDATE zoom_meetings 
            SET recording_link = %s 
            WHERE id = %s AND teacher_id = %s
        """, (data['recording_link'], meeting_id, teacher_id))
        
        mysql.connection.commit()
        affected = cursor.rowcount
        cursor.close()
        
        if affected:
            return jsonify({'message': 'Recording added successfully'}), 200
        else:
            return jsonify({'error': 'Meeting not found or unauthorized'}), 404
            
    except Exception as e:
        print(f"Error adding recording: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


# ============ DELETE MEETING ============

@teacher_zoom_bp.route('/<int:meeting_id>', methods=['DELETE'], strict_slashes=False)
@jwt_required()
@teacher_required
def delete_meeting(meeting_id):
    """Delete a meeting"""
    try:
        teacher_id = get_jwt_identity()
        
        cursor = mysql.connection.cursor()
        cursor.execute("""
            DELETE FROM zoom_meetings 
            WHERE id = %s AND teacher_id = %s
        """, (meeting_id, teacher_id))
        
        mysql.connection.commit()
        affected = cursor.rowcount
        cursor.close()
        
        if affected:
            return jsonify({'message': 'Meeting deleted successfully'}), 200
        else:
            return jsonify({'error': 'Meeting not found or unauthorized'}), 404
            
    except Exception as e:
        print(f"Error deleting meeting: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500