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
                INSERT INTO notifications (user_id, type, title, message, link, sender_id, class_id, priority, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())
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
                INSERT INTO notifications (user_id, type, title, message, link, sender_id, class_id, priority, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())
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
            print(f"\n{'📌'*60}")
            print(f"📌 SEND_TO_CLASS CALLED - Section ID: {class_id}")
            print(f"{'📌'*60}")
            print(f"   ├─ sender_id: {sender_id}")
            print(f"   ├─ title: {title}")
            print(f"   ├─ message: {message[:50]}..." if len(message) > 50 else f"   ├─ message: {message}")
            print(f"   ├─ type: {notification_type}")
            print(f"   └─ priority: {priority}")
            
            # Check if section exists
            cursor.execute("SELECT id, name FROM sections WHERE id = %s", (class_id,))
            section = cursor.fetchone()
            if not section:
                print(f"   ❌ Section {class_id} NOT FOUND!")
                cursor.close()
                return 0
            print(f"   ✅ Section found: {section['name']} (ID: {section['id']})")
            
            # Get all enrolled students
            print(f"   🔍 Querying for students in section {class_id}...")
            cursor.execute("""
                SELECT u.id, u.email, u.name
                FROM enrollments e
                JOIN users u ON e.student_id = u.id
                WHERE e.section_id = %s AND e.status = 'approved'
            """, (class_id,))
            
            students = cursor.fetchall()
            print(f"   📊 Found {len(students)} students:")
            if students:
                for i, s in enumerate(students):
                    print(f"      {i+1}. ID: {s['id']}, Email: {s['email']}, Name: {s['name']}")
            else:
                print(f"      ⚠️ No students found in section {class_id}")
                cursor.close()
                return 0
            
            # Create notifications
            print(f"   📨 Creating notifications...")
            success_count = 0
            for student in students:
                try:
                    cursor.execute("""
                        INSERT INTO notifications (
                            user_id, type, title, message, link, 
                            sender_id, class_id, priority, created_at
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())
                    """, (
                        student['id'],
                        notification_type,
                        title,
                        message,
                        link,
                        sender_id,
                        class_id,
                        priority
                    ))
                    print(f"      ✅ Created for {student['email']}")
                    success_count += 1
                except Exception as e:
                    print(f"      ❌ Failed for {student['email']}: {e}")
            
            mysql.connection.commit()
            print(f"   {'✅'*40}")
            print(f"   ✅ SUCCESS: {success_count}/{len(students)} notifications created")
            print(f"   {'✅'*40}\n")
            cursor.close()
            return success_count
            
        except Exception as e:
            print(f"   ❌ ERROR in send_to_class: {e}")
            import traceback
            traceback.print_exc()
            mysql.connection.rollback()
            cursor.close()
            raise e
    
    @staticmethod
    def send_to_teacher_classes(teacher_user_id, sender_id, title, message, notification_type='teacher_announcement', link=None, priority='normal'):
        """Send notification to all students in all classes taught by a teacher"""
        cursor = mysql.connection.cursor()
        try:
            print(f"\n{'🔥'*60}")
            print(f"🔥 SEND_TO_TEACHER_CLASSES STARTED")
            print(f"{'🔥'*60}")
            print(f"   ├─ teacher_user_id: {teacher_user_id}")
            print(f"   ├─ sender_id: {sender_id}")
            print(f"   ├─ title: {title}")
            print(f"   ├─ message: {message[:50]}..." if len(message) > 50 else f"   ├─ message: {message}")
            print(f"   ├─ type: {notification_type}")
            print(f"   └─ priority: {priority}")
            
            # Get all sections taught by teacher
            print(f"   🔍 Querying sections for teacher {teacher_user_id}...")
            cursor.execute("""
                SELECT s.id, s.name 
                FROM sections s
                JOIN teacher_assignments ta ON s.id = ta.section_id
                WHERE ta.teacher_id = %s
            """, (teacher_user_id,))
            
            sections = cursor.fetchall()
            print(f"   📊 Found {len(sections)} sections for teacher {teacher_user_id}:")
            if sections:
                for i, s in enumerate(sections):
                    print(f"      {i+1}. Section ID: {s['id']}, Name: {s['name']}")
            else:
                print(f"      ⚠️ No sections found for this teacher!")
                cursor.close()
                return 0
            
            total_sent = 0
            for section in sections:
                print(f"\n   {'─'*50}")
                print(f"   ▶ Processing section {section['id']} ({section['name']})...")
                sent = Notification.send_to_class(
                    section['id'], 
                    sender_id, 
                    title, 
                    message, 
                    notification_type, 
                    link, 
                    priority
                )
                print(f"   ◀ Section {section['id']} returned {sent} notifications")
                total_sent += sent
            
            print(f"\n   {'🎉'*50}")
            print(f"   🎉 TOTAL: {total_sent} notifications sent across all sections")
            print(f"   {'🎉'*50}\n")
            cursor.close()
            return total_sent
            
        except Exception as e:
            print(f"   ❌ ERROR in send_to_teacher_classes: {e}")
            import traceback
            traceback.print_exc()
            cursor.close()
            raise e
    
    @staticmethod
    def send_to_all_students(sender_id, title, message, notification_type='system_announcement', link=None, priority='normal'):
        """Send notification to all students in the system (Admin only)"""
        cursor = mysql.connection.cursor()
        try:
            print(f"\n{'🌍'*60}")
            print(f"🌍 SEND_TO_ALL_STUDENTS")
            print(f"{'🌍'*60}")
            print(f"   sender_id: {sender_id}")
            print(f"   title: {title}")
            
            cursor.execute("SELECT u.id, u.email FROM users u WHERE u.role = 'student'")
            students = cursor.fetchall()
            print(f"   📊 Found {len(students)} students in system")
            
            if not students:
                return 0
            
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
                INSERT INTO notifications (user_id, type, title, message, link, sender_id, class_id, priority, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())
            """, values)
            
            mysql.connection.commit()
            affected = cursor.rowcount
            cursor.close()
            
            print(f"   ✅ Created {affected} notifications")
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
        
        print(f"\n🔍 Getting notifications for user {user_id}, limit={limit}, unread_only={unread_only}")
        
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
        
        print(f"📊 Found {len(notifications)} notifications for user {user_id}")
        for i, n in enumerate(notifications):
            print(f"   {i+1}. ID: {n['id']}, Title: {n['title']}, Read: {n['is_read']}")
        
        cursor.close()
        return notifications
    
    @staticmethod
    def get_unread_count(user_id):
        """Get count of unread notifications"""
        cursor = mysql.connection.cursor()
        try:
            cursor.execute("""
                SELECT COUNT(*) as count FROM notifications 
                WHERE user_id = %s AND is_read = FALSE
                AND (expires_at IS NULL OR expires_at > NOW())
            """, (user_id,))
            
            result = cursor.fetchone()
            count = result['count'] if result else 0
            cursor.close()
            return count
        except Exception as e:
            print(f"❌ Error in get_unread_count: {e}")
            cursor.close()
            return 0
    
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
        
        if result['role'] == 'admin':
            return True, 'Admin can delete'
        
        if result['role'] == 'teacher' and result['sender_id'] == user_id:
            return True, 'Teacher can delete their own notifications'
        
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