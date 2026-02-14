from utils.database import mysql
from datetime import datetime

class Notification:
    """Notification Model - Handles all notification operations"""
    
    # ============ CREATE OPERATIONS ============
    
    @staticmethod
    def create(user_id, notification_type, title, message, link=None, sender_id=None, class_id=None, priority='normal'):
        """Create a single notification"""
        cursor = mysql.connection.cursor()
        try:
            cursor.execute("""
                INSERT INTO notifications (user_id, type, title, message, link, sender_id, class_id, priority)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (user_id, notification_type, title, message, link, sender_id, class_id, priority))
            
            mysql.connection.commit()
            notification_id = cursor.lastrowid
            cursor.close()
            
            print(f"✅ Notification created for user {user_id}: {title}")
            return notification_id
            
        except Exception as e:
            print(f"❌ Error creating notification: {e}")
            mysql.connection.rollback()
            cursor.close()
            raise e
    
    @staticmethod
    def create_bulk(user_ids, notification_type, title, message, link=None, sender_id=None, class_id=None, priority='normal'):
        """Create notifications for multiple users"""
        cursor = mysql.connection.cursor()
        try:
            values = []
            for user_id in user_ids:
                values.append((user_id, notification_type, title, message, link, sender_id, class_id, priority))
            
            cursor.executemany("""
                INSERT INTO notifications (user_id, type, title, message, link, sender_id, class_id, priority)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, values)
            
            mysql.connection.commit()
            affected = cursor.rowcount
            cursor.close()
            
            print(f"✅ Created {affected} notifications")
            return affected
            
        except Exception as e:
            print(f"❌ Error creating bulk notifications: {e}")
            mysql.connection.rollback()
            cursor.close()
            raise e
    
    @staticmethod
    def send_to_class(class_id, sender_id, title, message, notification_type='class_announcement', link=None, priority='normal'):
        """Send notification to all students in a class/section"""
        cursor = mysql.connection.cursor()
        try:
            # Get all enrolled students in the section
            cursor.execute("""
                SELECT DISTINCT u.id 
                FROM enrollments e
                JOIN users u ON e.student_id = u.id
                WHERE e.section_id = %s AND e.status = 'approved'
            """, (class_id,))
            
            students = cursor.fetchall()
            
            if not students:
                print(f"No students found for section/class {class_id}")
                return 0
            
            print(f"Found {len(students)} students for section/class {class_id}")
            
            # Create notifications
            values = []
            for student in students:
                values.append((
                    student['id'],
                    notification_type,
                    title,
                    message,
                    link,
                    sender_id,
                    class_id,
                    priority
                ))
            
            cursor.executemany("""
                INSERT INTO notifications (user_id, type, title, message, link, sender_id, class_id, priority)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, values)
            
            mysql.connection.commit()
            affected = cursor.rowcount
            cursor.close()
            
            print(f"Successfully sent {affected} notifications to students")
            return affected
            
        except Exception as e:
            print(f"Error in send_to_class: {e}")
            mysql.connection.rollback()
            cursor.close()
            raise e
    
    @staticmethod
    def send_to_teacher_classes(teacher_user_id, sender_id, title, message, notification_type='teacher_announcement', link=None, priority='normal'):
        """Send notification to all students in all classes taught by a teacher"""
        cursor = mysql.connection.cursor()
        try:
            # Get all sections taught by teacher
            cursor.execute("""
                SELECT s.id FROM sections s
                JOIN teacher_assignments ta ON s.id = ta.section_id
                WHERE ta.teacher_id = %s
            """, (teacher_user_id,))
            
            sections = cursor.fetchall()
            
            total_sent = 0
            for section in sections:
                sent = Notification.send_to_class(
                    section['id'], 
                    sender_id, 
                    title, 
                    message, 
                    notification_type, 
                    link, 
                    priority
                )
                total_sent += sent
            
            cursor.close()
            return total_sent
            
        except Exception as e:
            cursor.close()
            raise e
    
    @staticmethod
    def send_to_all_students(sender_id, title, message, notification_type='system_announcement', link=None, priority='normal'):
        """Send notification to all students in the system (Admin only)"""
        cursor = mysql.connection.cursor()
        try:
            # Get all students
            cursor.execute("""
                SELECT u.id FROM users u
                WHERE u.role = 'student'
            """)
            
            students = cursor.fetchall()
            
            if not students:
                return 0
            
            # Create notifications
            values = []
            for student in students:
                values.append((
                    student['id'],
                    notification_type,
                    title,
                    message,
                    link,
                    sender_id,
                    None,
                    priority
                ))
            
            cursor.executemany("""
                INSERT INTO notifications (user_id, type, title, message, link, sender_id, class_id, priority)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, values)
            
            mysql.connection.commit()
            affected = cursor.rowcount
            cursor.close()
            
            return affected
            
        except Exception as e:
            mysql.connection.rollback()
            cursor.close()
            raise e
    
    # ============ READ OPERATIONS ============
    
    @staticmethod
    def get_by_user(user_id, limit=50, offset=0, unread_only=False, include_expired=False):
        """Get notifications for a user"""
        cursor = mysql.connection.cursor()
        
        query = """
            SELECT n.*, 
                   u.name as sender_name,
                   c.name as class_name
            FROM notifications n
            LEFT JOIN users u ON n.sender_id = u.id
            LEFT JOIN classes c ON n.class_id = c.id
            WHERE n.user_id = %s
        """
        params = [user_id]
        
        if not include_expired:
            query += " AND (n.expires_at IS NULL OR n.expires_at > NOW())"
        
        if unread_only:
            query += " AND n.is_read = FALSE"
        
        query += " ORDER BY n.priority DESC, n.created_at DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])
        
        cursor.execute(query, params)
        notifications = cursor.fetchall()
        cursor.close()
        
        return notifications
    
    @staticmethod
    def get_unread_count(user_id):
        """Get count of unread notifications"""
        cursor = mysql.connection.cursor()
        cursor.execute("""
            SELECT COUNT(*) as count FROM notifications 
            WHERE user_id = %s AND is_read = FALSE
            AND (expires_at IS NULL OR expires_at > NOW())
        """, (user_id,))
        count = cursor.fetchone()['count']
        cursor.close()
        return count
    
    @staticmethod
    def get_by_class(class_id, limit=50):
        """Get notifications for a specific class (for teachers)"""
        cursor = mysql.connection.cursor()
        cursor.execute("""
            SELECT n.*, u.name as sender_name
            FROM notifications n
            JOIN users u ON n.sender_id = u.id
            WHERE n.class_id = %s
            ORDER BY n.created_at DESC
            LIMIT %s
        """, (class_id, limit))
        notifications = cursor.fetchall()
        cursor.close()
        return notifications
    
    # ============ PERMISSION CHECK ============
    
    @staticmethod
    def can_delete(user_id, notification_id):
        """Check if user has permission to delete a notification"""
        cursor = mysql.connection.cursor()
        cursor.execute("""
            SELECT n.*, u.role 
            FROM notifications n
            JOIN users u ON u.id = %s
            WHERE n.id = %s
        """, (user_id, notification_id))
        
        result = cursor.fetchone()
        cursor.close()
        
        if not result:
            return False, 'Notification not found'
        
        # Admin can delete any notification
        if result['role'] == 'admin':
            return True, 'Admin can delete'
        
        # Teacher can delete only if they are the sender
        if result['role'] == 'teacher' and result['sender_id'] == user_id:
            return True, 'Teacher can delete their own notifications'
        
        # Students cannot delete any notifications
        if result['role'] == 'student':
            return False, 'Students cannot delete notifications'
        
        return False, 'Unauthorized'
    
    # ============ UPDATE OPERATIONS ============
    
    @staticmethod
    def mark_as_read(notification_id, user_id):
        """Mark a notification as read"""
        cursor = mysql.connection.cursor()
        try:
            cursor.execute("""
                UPDATE notifications 
                SET is_read = TRUE 
                WHERE id = %s AND user_id = %s
            """, (notification_id, user_id))
            mysql.connection.commit()
            affected = cursor.rowcount
            cursor.close()
            return affected > 0
        except Exception as e:
            mysql.connection.rollback()
            cursor.close()
            raise e
    
    @staticmethod
    def mark_all_as_read(user_id):
        """Mark all notifications as read"""
        cursor = mysql.connection.cursor()
        try:
            cursor.execute("""
                UPDATE notifications 
                SET is_read = TRUE 
                WHERE user_id = %s AND is_read = FALSE
            """, (user_id,))
            mysql.connection.commit()
            count = cursor.rowcount
            cursor.close()
            return count
        except Exception as e:
            mysql.connection.rollback()
            cursor.close()
            raise e
    
    # ============ DELETE OPERATIONS ============
    
    @staticmethod
    def delete(notification_id, user_id):
        """Delete a notification (after permission check)"""
        cursor = mysql.connection.cursor()
        try:
            cursor.execute("""
                DELETE FROM notifications 
                WHERE id = %s AND user_id = %s
            """, (notification_id, user_id))
            mysql.connection.commit()
            affected = cursor.rowcount
            cursor.close()
            return affected > 0
        except Exception as e:
            mysql.connection.rollback()
            cursor.close()
            raise e
    
    @staticmethod
    def clear_all(user_id):
        """Delete all notifications for a user"""
        cursor = mysql.connection.cursor()
        try:
            cursor.execute("""
                DELETE FROM notifications 
                WHERE user_id = %s
            """, (user_id,))
            mysql.connection.commit()
            count = cursor.rowcount
            cursor.close()
            return count
        except Exception as e:
            mysql.connection.rollback()
            cursor.close()
            raise e