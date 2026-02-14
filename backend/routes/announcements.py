from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from utils.database import mysql
from utils.decorators import role_required
from datetime import datetime

announcement_bp = Blueprint('announcements', __name__)

@announcement_bp.route('/', methods=['POST'])
@jwt_required()
@role_required(['teacher'])
def create_announcement():
    """Create a class announcement"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        required_fields = ['class_id', 'title', 'content']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        cursor = mysql.connection.cursor()
        
        # Verify teacher owns the class
        cursor.execute("""
            SELECT c.* FROM classes c
            JOIN teacher_profiles tp ON c.teacher_id = tp.id
            WHERE c.id = %s AND tp.user_id = %s
        """, (data['class_id'], user_id))
        
        if not cursor.fetchone():
            cursor.close()
            return jsonify({'error': 'Class not found or unauthorized'}), 403
        
        # Create announcement
        cursor.execute("""
            INSERT INTO announcements (
                title, content, class_id, posted_by, 
                is_pinned, expiry_date
            ) VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            data['title'],
            data['content'],
            data['class_id'],
            user_id,
            data.get('is_pinned', False),
            data.get('expiry_date')
        ))
        
        mysql.connection.commit()
        announcement_id = cursor.lastrowid
        cursor.close()
        
        # TODO: Send notifications to all enrolled students
        
        return jsonify({
            'message': 'Announcement created successfully',
            'announcement_id': announcement_id
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@announcement_bp.route('/class/<int:class_id>', methods=['GET'])
@jwt_required()
def get_class_announcements(class_id):
    """Get all announcements for a class"""
    try:
        user_id = get_jwt_identity()
        
        cursor = mysql.connection.cursor()
        
        # Check access
        cursor.execute("SELECT role FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        
        has_access = False
        
        if user['role'] == 'teacher':
            cursor.execute("""
                SELECT c.* FROM classes c
                JOIN teacher_profiles tp ON c.teacher_id = tp.id
                WHERE c.id = %s AND tp.user_id = %s
            """, (class_id, user_id))
            has_access = cursor.fetchone() is not None
            
        elif user['role'] == 'student':
            cursor.execute("""
                SELECT sp.id FROM student_profiles sp
                WHERE sp.user_id = %s
            """, (user_id,))
            student = cursor.fetchone()
            
            if student:
                cursor.execute("""
                    SELECT status FROM class_enrollments
                    WHERE class_id = %s AND student_id = %s
                """, (class_id, student['id']))
                enrollment = cursor.fetchone()
                has_access = enrollment and enrollment['status'] == 'approved'
        
        if not has_access:
            cursor.close()
            return jsonify({'error': 'Access denied'}), 403
        
        # Get announcements
        cursor.execute("""
            SELECT 
                a.*,
                u.name as posted_by_name,
                (a.expiry_date IS NULL OR a.expiry_date > NOW()) as is_active
            FROM announcements a
            JOIN users u ON a.posted_by = u.id
            WHERE a.class_id = %s
            ORDER BY a.is_pinned DESC, a.created_at DESC
        """, (class_id,))
        
        announcements = cursor.fetchall()
        cursor.close()
        
        return jsonify({'announcements': announcements}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@announcement_bp.route('/<int:announcement_id>', methods=['PUT'])
@jwt_required()
@role_required(['teacher'])
def update_announcement(announcement_id):
    """Update an announcement"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        cursor = mysql.connection.cursor()
        
        # Verify teacher owns the announcement
        cursor.execute("""
            SELECT a.* FROM announcements a
            WHERE a.id = %s AND a.posted_by = %s
        """, (announcement_id, user_id))
        
        if not cursor.fetchone():
            cursor.close()
            return jsonify({'error': 'Announcement not found or unauthorized'}), 404
        
        # Update fields
        update_fields = []
        update_values = []
        
        allowed_fields = ['title', 'content', 'is_pinned', 'expiry_date']
        for field in allowed_fields:
            if field in data:
                update_fields.append(f"{field} = %s")
                update_values.append(data[field])
        
        if update_fields:
            query = f"UPDATE announcements SET {', '.join(update_fields)} WHERE id = %s"
            update_values.append(announcement_id)
            cursor.execute(query, tuple(update_values))
            mysql.connection.commit()
        
        cursor.close()
        
        return jsonify({'message': 'Announcement updated successfully'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@announcement_bp.route('/<int:announcement_id>', methods=['DELETE'])
@jwt_required()
@role_required(['teacher'])
def delete_announcement(announcement_id):
    """Delete an announcement"""
    try:
        user_id = get_jwt_identity()
        
        cursor = mysql.connection.cursor()
        
        # Verify teacher owns the announcement
        cursor.execute("""
            SELECT a.* FROM announcements a
            WHERE a.id = %s AND a.posted_by = %s
        """, (announcement_id, user_id))
        
        if not cursor.fetchone():
            cursor.close()
            return jsonify({'error': 'Announcement not found or unauthorized'}), 404
        
        cursor.execute("DELETE FROM announcements WHERE id = %s", (announcement_id,))
        mysql.connection.commit()
        cursor.close()
        
        return jsonify({'message': 'Announcement deleted successfully'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@announcement_bp.route('/<int:announcement_id>/pin', methods=['POST'])
@jwt_required()
@role_required(['teacher'])
def toggle_pin(announcement_id):
    """Pin or unpin an announcement"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        cursor = mysql.connection.cursor()
        
        # Verify teacher owns the announcement
        cursor.execute("""
            SELECT a.* FROM announcements a
            WHERE a.id = %s AND a.posted_by = %s
        """, (announcement_id, user_id))
        
        announcement = cursor.fetchone()
        
        if not announcement:
            cursor.close()
            return jsonify({'error': 'Announcement not found or unauthorized'}), 404
        
        is_pinned = data.get('is_pinned', not announcement['is_pinned'])
        
        cursor.execute("""
            UPDATE announcements 
            SET is_pinned = %s 
            WHERE id = %s
        """, (is_pinned, announcement_id))
        
        mysql.connection.commit()
        cursor.close()
        
        status = 'pinned' if is_pinned else 'unpinned'
        return jsonify({'message': f'Announcement {status} successfully'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500