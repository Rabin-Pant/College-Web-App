from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from utils.database import mysql
from utils.decorators import role_required, teacher_required, admin_required
from models.notification import Notification
from datetime import datetime

notification_bp = Blueprint('notifications', __name__)

# ============ SENDING NOTIFICATIONS ============

@notification_bp.route('/send-to-class/<int:class_id>', methods=['POST'], strict_slashes=False)
@jwt_required()
@role_required(['teacher', 'admin'])
def send_notification_to_class(class_id):
    """Send notification to all students in a class/section"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        print("="*50)
        print(f"📡 SEND NOTIFICATION TO CLASS {class_id}")
        print(f"👤 User ID: {user_id}")
        print(f"📦 Request data: {data}")
        print("="*50)
        
        if not data.get('title') or not data.get('message'):
            return jsonify({'error': 'Title and message are required'}), 400
        
        # Get user role and info
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT id, name, role FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        
        if not user:
            cursor.close()
            return jsonify({'error': 'User not found'}), 404
        
        print(f"👤 User: {user['name']} ({user['role']})")
        
        # If teacher, verify they are assigned to this section
        if user['role'] == 'teacher':
            cursor.execute("""
                SELECT ta.id FROM teacher_assignments ta
                WHERE ta.teacher_id = %s AND ta.section_id = %s
            """, (user_id, class_id))
            
            if not cursor.fetchone():
                cursor.close()
                print(f"❌ Teacher {user_id} not assigned to section {class_id}")
                return jsonify({'error': 'You are not assigned to this section'}), 403
            else:
                print(f"✅ Teacher verified for section {class_id}")
        
        cursor.close()
        
        # Use the model method
        recipients = Notification.send_to_teacher_classes(
    teacher_user_id=user_id,
    sender_id=user_id,
    title=data['title'],
    message=data['message'],
    notification_type='class_announcement',  
    link=data.get('link'),
    priority=data.get('priority', 'normal')
)
        
        print(f"✅ Successfully sent to {recipients} students")
        
        return jsonify({
            'message': f'Notification sent to {recipients} students',
            'recipients': recipients
        }), 200
        
    except Exception as e:
        print(f"❌ Error in send_notification_to_class: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@notification_bp.route('/send-to-all-classes', methods=['POST'], strict_slashes=False)
@jwt_required()
@role_required(['teacher', 'admin'])
def send_notification_to_all_classes():
    """Send notification to all students in all classes taught by teacher"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        print("\n" + "="*60)
        print("📡 SEND TO ALL CLASSES CALLED")
        print("="*60)
        print(f"👤 user_id: {user_id}")
        print(f"📦 data: {data}")
        print("="*60)
        
        if not data.get('title') or not data.get('message'):
            return jsonify({'error': 'Title and message are required'}), 400
        
        # Get user role
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT role FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        cursor.close()
        
        print(f"👤 user role: {user['role']}")
        
        recipients = 0
        
        if user['role'] == 'teacher':
            print("📨 Calling send_to_teacher_classes...")
            recipients = Notification.send_to_teacher_classes(
                teacher_user_id=user_id,
                sender_id=user_id,
                title=data['title'],
                message=data['message'],
                notification_type=data.get('type', 'teacher_announcement'),
                link=data.get('link'),
                priority=data.get('priority', 'normal')
            )
            print(f"✅ send_to_teacher_classes returned: {recipients}")
        else:  # admin
            print("📨 Admin sending to all students...")
            recipients = Notification.send_to_all_students(
                sender_id=user_id,
                title=data['title'],
                message=data['message'],
                notification_type='system_announcement',
                link=data.get('link'),
                priority=data.get('priority', 'high')
            )
        
        print(f"🎉 Total recipients: {recipients}")
        print("="*60 + "\n")
        
        return jsonify({
            'message': f'Notification sent to {recipients} students',
            'recipients': recipients
        }), 200
        
    except Exception as e:
        print(f"❌ Error sending notification: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@notification_bp.route('/send-to-all-students', methods=['POST'], strict_slashes=False)
@jwt_required()
@admin_required
def send_notification_to_all_students():
    """Send notification to all students in the system (Admin only)"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data.get('title') or not data.get('message'):
            return jsonify({'error': 'Title and message are required'}), 400
        
        recipients = Notification.send_to_all_students(
            sender_id=user_id,
            title=data['title'],
            message=data['message'],
            notification_type='system_announcement',
            link=data.get('link'),
            priority=data.get('priority', 'high')
        )
        
        return jsonify({
            'message': f'System announcement sent to {recipients} students',
            'recipients': recipients
        }), 200
        
    except Exception as e:
        print(f"Error sending notification: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@notification_bp.route('/send-to-all-teachers', methods=['POST'], strict_slashes=False)
@jwt_required()
@admin_required
def send_notification_to_all_teachers():
    """Send notification to all teachers in the system (Admin only)"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data.get('title') or not data.get('message'):
            return jsonify({'error': 'Title and message are required'}), 400
        
        cursor = mysql.connection.cursor()
        
        # Get all teachers
        cursor.execute("""
            SELECT u.id FROM users u
            WHERE u.role = 'teacher'
        """)
        
        teachers = cursor.fetchall()
        cursor.close()
        
        if not teachers:
            return jsonify({'message': 'No teachers found', 'recipients': 0}), 200
        
        # Create notifications for all teachers
        recipients = 0
        for teacher in teachers:
            try:
                Notification.create(
                    user_id=teacher['id'],
                    notification_type='system_announcement',
                    title=data['title'],
                    message=data['message'],
                    link=data.get('link'),
                    sender_id=user_id,
                    priority=data.get('priority', 'normal')
                )
                recipients += 1
            except Exception as e:
                print(f"Error sending to teacher {teacher['id']}: {e}")
        
        return jsonify({
            'message': f'Notification sent to {recipients} teachers',
            'recipients': recipients
        }), 200
        
    except Exception as e:
        print(f"Error sending notification to teachers: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@notification_bp.route('/send-to-all-users', methods=['POST'], strict_slashes=False)
@jwt_required()
@admin_required
def send_notification_to_all_users():
    """Send notification to all users (Admin only)"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data.get('title') or not data.get('message'):
            return jsonify({'error': 'Title and message are required'}), 400
        
        cursor = mysql.connection.cursor()
        
        # Get all users
        cursor.execute("SELECT id FROM users")
        users = cursor.fetchall()
        cursor.close()
        
        if not users:
            return jsonify({'message': 'No users found', 'recipients': 0}), 200
        
        recipients = 0
        for user in users:
            try:
                Notification.create(
                    user_id=user['id'],
                    notification_type='system_announcement',
                    title=data['title'],
                    message=data['message'],
                    link=data.get('link'),
                    sender_id=user_id,
                    priority=data.get('priority', 'high')
                )
                recipients += 1
            except Exception as e:
                print(f"Error sending to user {user['id']}: {e}")
        
        return jsonify({
            'message': f'Notification sent to {recipients} users',
            'recipients': recipients
        }), 200
        
    except Exception as e:
        print(f"Error sending notification to all users: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@notification_bp.route('/send-to-user/<int:target_user_id>', methods=['POST'], strict_slashes=False)
@jwt_required()
@admin_required
def send_notification_to_user(target_user_id):
    """Send notification to a specific user (Admin only)"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data.get('title') or not data.get('message'):
            return jsonify({'error': 'Title and message are required'}), 400
        
        # Check if user exists
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT id, name, email FROM users WHERE id = %s", (target_user_id,))
        user = cursor.fetchone()
        cursor.close()
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        notification_id = Notification.create(
            user_id=target_user_id,
            notification_type='system_announcement',
            title=data['title'],
            message=data['message'],
            link=data.get('link'),
            sender_id=user_id,
            priority=data.get('priority', 'normal')
        )
        
        return jsonify({
            'message': f'Notification sent to {user["name"]}',
            'notification_id': notification_id,
            'recipient': user
        }), 200
        
    except Exception as e:
        print(f"Error sending notification to user: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


# ============ GETTING NOTIFICATIONS ============

@notification_bp.route('/', methods=['GET'], strict_slashes=False)
@jwt_required()
def get_notifications():
    """Get all notifications for current user"""
    try:
        user_id = get_jwt_identity()
        
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)
        unread_only = request.args.get('unread_only', 'false').lower() == 'true'
        
        notifications = Notification.get_by_user(
            user_id=user_id,
            limit=limit,
            offset=offset,
            unread_only=unread_only
        )
        
        unread_count = Notification.get_unread_count(user_id)
        
        return jsonify({
            'notifications': notifications,
            'unread_count': unread_count,
            'total': len(notifications)
        }), 200
        
    except Exception as e:
        print(f"Error getting notifications: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@notification_bp.route('/unread-count', methods=['GET'], strict_slashes=False)
@jwt_required()
def get_unread_count():
    """Get unread notifications count"""
    try:
        user_id = get_jwt_identity()
        count = Notification.get_unread_count(user_id)
        return jsonify({'unread_count': count}), 200
    except Exception as e:
        print(f"Error getting unread count: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@notification_bp.route('/class/<int:class_id>', methods=['GET'], strict_slashes=False)
@jwt_required()
@role_required(['teacher', 'admin'])
def get_class_notifications(class_id):
    """Get notifications for a specific class (teacher view)"""
    try:
        user_id = get_jwt_identity()
        
        # Verify teacher owns the class
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT role FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        
        if user['role'] == 'teacher':
            cursor.execute("""
                SELECT ta.id FROM teacher_assignments ta
                WHERE ta.teacher_id = %s AND ta.section_id = %s
            """, (user_id, class_id))
            
            if not cursor.fetchone():
                cursor.close()
                return jsonify({'error': 'Unauthorized'}), 403
        
        cursor.close()
        
        notifications = Notification.get_by_class(class_id)
        
        return jsonify({'notifications': notifications}), 200
        
    except Exception as e:
        print(f"Error getting class notifications: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@notification_bp.route('/stats', methods=['GET'], strict_slashes=False)
@jwt_required()
def get_notification_stats():
    """Get notification statistics for current user"""
    try:
        user_id = get_jwt_identity()
        
        cursor = mysql.connection.cursor()
        
        # Total count
        cursor.execute("""
            SELECT COUNT(*) as total FROM notifications 
            WHERE user_id = %s
        """, (user_id,))
        total = cursor.fetchone()['total']
        
        # Unread count
        cursor.execute("""
            SELECT COUNT(*) as unread FROM notifications 
            WHERE user_id = %s AND is_read = FALSE
        """, (user_id,))
        unread = cursor.fetchone()['unread']
        
        # Count by type
        cursor.execute("""
            SELECT type, COUNT(*) as count 
            FROM notifications 
            WHERE user_id = %s 
            GROUP BY type
        """, (user_id,))
        by_type = cursor.fetchall()
        
        # Recent activity (last 7 days)
        cursor.execute("""
            SELECT DATE(created_at) as date, COUNT(*) as count
            FROM notifications
            WHERE user_id = %s AND created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
            GROUP BY DATE(created_at)
            ORDER BY date DESC
        """, (user_id,))
        recent = cursor.fetchall()
        
        cursor.close()
        
        return jsonify({
            'total': total,
            'unread': unread,
            'read': total - unread,
            'by_type': by_type,
            'recent_activity': recent
        }), 200
        
    except Exception as e:
        print(f"Error getting notification stats: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


# ============ MANAGING NOTIFICATIONS ============

@notification_bp.route('/<int:notification_id>/read', methods=['PUT'], strict_slashes=False)
@jwt_required()
def mark_as_read(notification_id):
    """Mark a notification as read"""
    try:
        user_id = get_jwt_identity()
        Notification.mark_as_read(notification_id, user_id)
        return jsonify({'message': 'Notification marked as read'}), 200
    except Exception as e:
        print(f"Error marking notification as read: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@notification_bp.route('/read-all', methods=['PUT'], strict_slashes=False)
@jwt_required()
def mark_all_as_read():
    """Mark all notifications as read"""
    try:
        user_id = get_jwt_identity()
        count = Notification.mark_all_as_read(user_id)
        return jsonify({
            'message': f'{count} notifications marked as read',
            'count': count
        }), 200
    except Exception as e:
        print(f"Error marking all as read: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@notification_bp.route('/<int:notification_id>', methods=['DELETE'], strict_slashes=False)
@jwt_required()
def delete_notification(notification_id):
    """Delete a notification (Admin/Teacher only)"""
    try:
        user_id = get_jwt_identity()
        
        # Check if user has permission to delete
        can_delete, message = Notification.can_delete(user_id, notification_id)
        
        if not can_delete:
            return jsonify({'error': message}), 403
        
        # Proceed with deletion
        Notification.delete(notification_id, user_id)
        return jsonify({'message': 'Notification deleted'}), 200
        
    except Exception as e:
        print(f"Error deleting notification: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@notification_bp.route('/clear-all', methods=['DELETE'], strict_slashes=False)
@jwt_required()
def clear_all_notifications():
    """Delete all notifications for current user (Students cannot use this)"""
    try:
        user_id = get_jwt_identity()
        
        # Check user role
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT role FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        cursor.close()
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Students cannot clear all notifications
        if user['role'] == 'student':
            return jsonify({'error': 'Students cannot clear all notifications'}), 403
        
        # Admin and Teacher can clear all
        count = Notification.clear_all(user_id)
        
        return jsonify({
            'message': f'{count} notifications cleared',
            'count': count
        }), 200
        
    except Exception as e:
        print(f"Error clearing notifications: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


# ============ BULK OPERATIONS ============

@notification_bp.route('/bulk-mark-read', methods=['POST'], strict_slashes=False)
@jwt_required()
def bulk_mark_read():
    """Mark multiple notifications as read"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        notification_ids = data.get('notification_ids', [])
        
        if not notification_ids:
            return jsonify({'error': 'No notification IDs provided'}), 400
        
        cursor = mysql.connection.cursor()
        placeholders = ', '.join(['%s'] * len(notification_ids))
        query = f"""
            UPDATE notifications 
            SET is_read = TRUE 
            WHERE id IN ({placeholders}) AND user_id = %s
        """
        params = notification_ids + [user_id]
        
        cursor.execute(query, params)
        mysql.connection.commit()
        count = cursor.rowcount
        cursor.close()
        
        return jsonify({
            'message': f'{count} notifications marked as read',
            'count': count
        }), 200
        
    except Exception as e:
        print(f"Error bulk marking notifications: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@notification_bp.route('/bulk-delete', methods=['POST'], strict_slashes=False)
@jwt_required()
def bulk_delete():
    """Delete multiple notifications"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        notification_ids = data.get('notification_ids', [])
        
        if not notification_ids:
            return jsonify({'error': 'No notification IDs provided'}), 400
        
        cursor = mysql.connection.cursor()
        placeholders = ', '.join(['%s'] * len(notification_ids))
        query = f"""
            DELETE FROM notifications 
            WHERE id IN ({placeholders}) AND user_id = %s
        """
        params = notification_ids + [user_id]
        
        cursor.execute(query, params)
        mysql.connection.commit()
        count = cursor.rowcount
        cursor.close()
        
        return jsonify({
            'message': f'{count} notifications deleted',
            'count': count
        }), 200
        
    except Exception as e:
        print(f"Error bulk deleting notifications: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


# ============ TEST ENDPOINT ============

@notification_bp.route('/test', methods=['GET'], strict_slashes=False)
@jwt_required()
def test_notification():
    """Test endpoint to send a test notification"""
    try:
        user_id = get_jwt_identity()
        
        # Create a test notification
        notification_id = Notification.create(
            user_id=user_id,
            notification_type='system_announcement',
            title='Test Notification',
            message='This is a test notification to verify the system is working.',
            link='/dashboard',
            sender_id=user_id,
            priority='normal'
        )
        
        return jsonify({
            'message': 'Test notification sent',
            'notification_id': notification_id
        }), 200
        
    except Exception as e:
        print(f"Error sending test notification: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500