from utils.database import mysql

class Course:
    """Course Model - Handles all course-related database operations"""
    
    @staticmethod
    def get_all(include_inactive=False):
        """Get all courses"""
        cursor = mysql.connection.cursor()
        query = "SELECT * FROM courses"
        if not include_inactive:
            query += " WHERE is_active = TRUE"
        query += " ORDER BY name"
        cursor.execute(query)
        courses = cursor.fetchall()
        cursor.close()
        return courses
    
    @staticmethod
    def get_by_id(course_id):
        """Get course by ID"""
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM courses WHERE id = %s", (course_id,))
        course = cursor.fetchone()
        cursor.close()
        return course
    
    @staticmethod
    def get_by_code(code):
        """Get course by code"""
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM courses WHERE code = %s", (code,))
        course = cursor.fetchone()
        cursor.close()
        return course
    
    @staticmethod
    def create(name, code, description=None, department=None, duration_years=None, total_credits=None):
        """Create a new course"""
        cursor = mysql.connection.cursor()
        try:
            cursor.execute("""
                INSERT INTO courses (name, code, description, department, duration_years, total_credits)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (name, code, description, department, duration_years, total_credits))
            mysql.connection.commit()
            course_id = cursor.lastrowid
            cursor.close()
            return course_id
        except Exception as e:
            mysql.connection.rollback()
            cursor.close()
            raise e
    
    @staticmethod
    def update(course_id, **kwargs):
        """Update course information"""
        cursor = mysql.connection.cursor()
        try:
            update_fields = []
            values = []
            
            allowed_fields = ['name', 'code', 'description', 'department', 'duration_years', 'total_credits', 'is_active']
            for field in allowed_fields:
                if field in kwargs:
                    update_fields.append(f"{field} = %s")
                    values.append(kwargs[field])
            
            if update_fields:
                query = f"UPDATE courses SET {', '.join(update_fields)} WHERE id = %s"
                values.append(course_id)
                print(f"Executing query: {query} with values: {values}")
                cursor.execute(query, tuple(values))
                mysql.connection.commit()
                print(f"✅ Updated {cursor.rowcount} rows")
            else:
                print("⚠️ No fields to update")
            
            cursor.close()
            return True
        except Exception as e:
            print(f"❌ Error in update method: {e}")
            mysql.connection.rollback()
            cursor.close()
            raise e
    
    @staticmethod
    def delete(course_id):
        """Delete a course"""
        cursor = mysql.connection.cursor()
        try:
            cursor.execute("DELETE FROM courses WHERE id = %s", (course_id,))
            mysql.connection.commit()
            affected = cursor.rowcount
            cursor.close()
            return affected > 0
        except Exception as e:
            mysql.connection.rollback()
            cursor.close()
            raise e
    
    @staticmethod
    def get_classes(course_id):
        """Get all classes in a course"""
        cursor = mysql.connection.cursor()
        cursor.execute("""
            SELECT c.*, u.name as teacher_name 
            FROM classes c
            JOIN teacher_profiles tp ON c.teacher_id = tp.id
            JOIN users u ON tp.user_id = u.id
            WHERE c.course_id = %s
            ORDER BY c.semester DESC, c.name
        """, (course_id,))
        classes = cursor.fetchall()
        cursor.close()
        return classes
    
    @staticmethod
    def get_stats(course_id):
        """Get statistics for a course"""
        cursor = mysql.connection.cursor()
        
        # Total classes
        cursor.execute("SELECT COUNT(*) as count FROM classes WHERE course_id = %s", (course_id,))
        total_classes = cursor.fetchone()['count']
        
        # Total students enrolled in this course's classes
        cursor.execute("""
            SELECT COUNT(DISTINCT ce.student_id) as count
            FROM class_enrollments ce
            JOIN classes c ON ce.class_id = c.id
            WHERE c.course_id = %s AND ce.status = 'approved'
        """, (course_id,))
        total_students = cursor.fetchone()['count']
        
        # Total teachers teaching in this course
        cursor.execute("""
            SELECT COUNT(DISTINCT c.teacher_id) as count
            FROM classes c
            WHERE c.course_id = %s
        """, (course_id,))
        total_teachers = cursor.fetchone()['count']
        
        cursor.close()
        
        return {
            'total_classes': total_classes,
            'total_students': total_students,
            'total_teachers': total_teachers
        }