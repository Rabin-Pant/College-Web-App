from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from utils.database import mysql
from utils.decorators import admin_required
from models.schedule import Schedule
from models.section import Section

admin_schedules_bp = Blueprint('admin_schedules', __name__)

@admin_schedules_bp.route('/', methods=['GET'])
@jwt_required()
@admin_required
def get_all_schedules():
    """Get all schedules with filters"""
    try:
        section_id = request.args.get('section_id', type=int)
        day = request.args.get('day')
        
        cursor = mysql.connection.cursor()
        query = """
            SELECT 
                sch.*,
                s.id as section_id,
                s.name as section_name,
                sub.id as subject_id,
                sub.code as subject_code,
                sub.name as subject_name,
                c.id as course_id,
                c.name as course_name,
                u.id as teacher_id,
                u.name as teacher_name
            FROM schedules sch
            JOIN sections s ON sch.section_id = s.id
            JOIN subjects sub ON s.subject_id = sub.id
            JOIN courses c ON sub.course_id = c.id
            LEFT JOIN teacher_assignments ta ON s.id = ta.section_id
            LEFT JOIN users u ON ta.teacher_id = u.id
            WHERE 1=1
        """
        params = []
        
        if section_id:
            query += " AND sch.section_id = %s"
            params.append(section_id)
        if day:
            query += " AND sch.day = %s"
            params.append(day)
            
        query += " ORDER BY sch.day, sch.start_time"
        
        cursor.execute(query, params)
        schedules = cursor.fetchall()
        cursor.close()
        
        return jsonify({
            'total': len(schedules),
            'schedules': schedules
        }), 200
        
    except Exception as e:
        print(f"Error getting schedules: {e}")
        return jsonify({'error': str(e)}), 500


@admin_schedules_bp.route('/section/<int:section_id>', methods=['GET'])
@jwt_required()
@admin_required
def get_section_schedule(section_id):
    """Get schedule for a specific section"""
    try:
        schedules = Schedule.get_by_section(section_id)
        
        return jsonify({
            'section_id': section_id,
            'schedules': schedules
        }), 200
        
    except Exception as e:
        print(f"Error getting section schedule: {e}")
        return jsonify({'error': str(e)}), 500


@admin_schedules_bp.route('/', methods=['POST'])
@jwt_required()
@admin_required
def create_schedule():
    """Create a new schedule entry"""
    try:
        data = request.get_json()
        
        required_fields = ['section_id', 'day', 'start_time', 'end_time']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Verify section exists
        section = Section.get_by_id(data['section_id'])
        if not section:
            return jsonify({'error': 'Section not found'}), 404
        
        # Check for scheduling conflict
        if Schedule.check_conflict(
            data['section_id'],
            data['day'],
            data['start_time'],
            data['end_time']
        ):
            return jsonify({'error': 'Scheduling conflict detected'}), 400
        
        schedule_id = Schedule.create(
            section_id=data['section_id'],
            day=data['day'],
            start_time=data['start_time'],
            end_time=data['end_time'],
            room=data.get('room')
        )
        
        return jsonify({
            'message': 'Schedule created successfully',
            'schedule_id': schedule_id
        }), 201
        
    except Exception as e:
        print(f"Error creating schedule: {e}")
        return jsonify({'error': str(e)}), 500


@admin_schedules_bp.route('/bulk', methods=['POST'])
@jwt_required()
@admin_required
def bulk_create_schedules():
    """Create multiple schedule entries at once"""
    try:
        data = request.get_json()
        schedules = data.get('schedules', [])
        
        if not schedules:
            return jsonify({'error': 'No schedules provided'}), 400
        
        created_ids = []
        errors = []
        
        for idx, item in enumerate(schedules):
            try:
                required_fields = ['section_id', 'day', 'start_time', 'end_time']
                if not all(field in item for field in required_fields):
                    errors.append(f"Row {idx+1}: Missing required fields")
                    continue
                
                # Check conflict
                if Schedule.check_conflict(
                    item['section_id'],
                    item['day'],
                    item['start_time'],
                    item['end_time']
                ):
                    errors.append(f"Row {idx+1}: Scheduling conflict")
                    continue
                
                schedule_id = Schedule.create(
                    section_id=item['section_id'],
                    day=item['day'],
                    start_time=item['start_time'],
                    end_time=item['end_time'],
                    room=item.get('room')
                )
                created_ids.append(schedule_id)
                
            except Exception as e:
                errors.append(f"Row {idx+1}: {str(e)}")
        
        return jsonify({
            'message': f'Created {len(created_ids)} schedule entries',
            'created_ids': created_ids,
            'errors': errors
        }), 201
        
    except Exception as e:
        print(f"Error bulk creating schedules: {e}")
        return jsonify({'error': str(e)}), 500


@admin_schedules_bp.route('/<int:schedule_id>', methods=['PUT'])
@jwt_required()
@admin_required
def update_schedule(schedule_id):
    """Update a schedule entry"""
    try:
        data = request.get_json()
        
        # Check for conflict if time/day changed
        if 'day' in data or 'start_time' in data or 'end_time' in data:
            cursor = mysql.connection.cursor()
            cursor.execute("SELECT section_id, day, start_time, end_time FROM schedules WHERE id = %s", (schedule_id,))
            current = cursor.fetchone()
            cursor.close()
            
            if current:
                section_id = current['section_id']
                day = data.get('day', current['day'])
                start_time = data.get('start_time', current['start_time'])
                end_time = data.get('end_time', current['end_time'])
                
                if Schedule.check_conflict(section_id, day, start_time, end_time, schedule_id):
                    return jsonify({'error': 'Scheduling conflict detected'}), 400
        
        Schedule.update(schedule_id, **data)
        
        return jsonify({'message': 'Schedule updated successfully'}), 200
        
    except Exception as e:
        print(f"Error updating schedule: {e}")
        return jsonify({'error': str(e)}), 500


@admin_schedules_bp.route('/<int:schedule_id>', methods=['DELETE'])
@jwt_required()
@admin_required
def delete_schedule(schedule_id):
    """Delete a schedule entry"""
    try:
        success = Schedule.delete(schedule_id)
        
        if success:
            return jsonify({'message': 'Schedule deleted successfully'}), 200
        else:
            return jsonify({'error': 'Schedule not found'}), 404
            
    except Exception as e:
        print(f"Error deleting schedule: {e}")
        return jsonify({'error': str(e)}), 500


@admin_schedules_bp.route('/by-day', methods=['GET'])
@jwt_required()
@admin_required
def get_schedule_by_day():
    """Get all schedules grouped by day"""
    try:
        cursor = mysql.connection.cursor()
        cursor.execute("""
            SELECT 
                sch.day,
                COUNT(*) as class_count,
                GROUP_CONCAT(DISTINCT s.id) as section_ids
            FROM schedules sch
            JOIN sections s ON sch.section_id = s.id
            GROUP BY sch.day
            ORDER BY FIELD(sch.day, 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday')
        """)
        by_day = cursor.fetchall()
        cursor.close()
        
        return jsonify({'by_day': by_day}), 200
        
    except Exception as e:
        print(f"Error getting schedule by day: {e}")
        return jsonify({'error': str(e)}), 500


@admin_schedules_bp.route('/check-conflict', methods=['POST'])
@jwt_required()
@admin_required
def check_conflict():
    """Check if a schedule would conflict"""
    try:
        data = request.get_json()
        
        required_fields = ['section_id', 'day', 'start_time', 'end_time']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        has_conflict = Schedule.check_conflict(
            data['section_id'],
            data['day'],
            data['start_time'],
            data['end_time'],
            data.get('exclude_id')
        )
        
        return jsonify({
            'has_conflict': has_conflict,
            'message': 'Conflict detected' if has_conflict else 'No conflict'
        }), 200
        
    except Exception as e:
        print(f"Error checking conflict: {e}")
        return jsonify({'error': str(e)}), 500