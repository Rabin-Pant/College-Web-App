from utils.database import mysql

class Subject:
    """Subject Model - Handles pre-defined subjects/classes"""
    
    @staticmethod
    def get_all(include_inactive=False):
        """Get all subjects"""
        cursor = mysql.connection.cursor()
        query = """
            SELECT s.*, c.name as course_name, c.code as course_code
            FROM subjects s
            JOIN courses c ON s.course_id = c.id
        """
        if not include_inactive:
            query += " WHERE s.is_active = TRUE"
        query += " ORDER BY c.id, s.semester, s.code"
        cursor.execute(query)
        subjects = cursor.fetchall()
        cursor.close()
        return subjects
    
    @staticmethod
    def get_by_course(course_id, include_inactive=False):
        """Get subjects by course"""
        cursor = mysql.connection.cursor()
        query = "SELECT * FROM subjects WHERE course_id = %s"
        if not include_inactive:
            query += " AND is_active = TRUE"
        query += " ORDER BY semester, code"
        cursor.execute(query, (course_id,))
        subjects = cursor.fetchall()
        cursor.close()
        return subjects
    
    @staticmethod
    def get_by_id(subject_id):
        """Get subject by ID"""
        cursor = mysql.connection.cursor()
        cursor.execute("""
            SELECT s.*, c.name as course_name, c.code as course_code
            FROM subjects s
            JOIN courses c ON s.course_id = c.id
            WHERE s.id = %s
        """, (subject_id,))
        subject = cursor.fetchone()
        cursor.close()
        return subject
    
    @staticmethod
    def get_by_code(course_id, code):
        """Get subject by course and code"""
        cursor = mysql.connection.cursor()
        cursor.execute("""
            SELECT * FROM subjects 
            WHERE course_id = %s AND code = %s
        """, (course_id, code))
        subject = cursor.fetchone()
        cursor.close()
        return subject
    
    @staticmethod
    def get_for_selection():
        """Get subjects formatted for dropdown selection"""
        cursor = mysql.connection.cursor()
        cursor.execute("""
            SELECT 
                s.id,
                CONCAT(c.code, ' - ', c.name, ' > ', s.code, ' - ', s.name) as display_name,
                c.id as course_id,
                c.code as course_code,
                c.name as course_name,
                s.code as subject_code,
                s.name as subject_name,
                s.credits,
                s.semester
            FROM subjects s
            JOIN courses c ON s.course_id = c.id
            WHERE s.is_active = TRUE AND c.is_active = TRUE
            ORDER BY c.id, s.semester, s.code
        """)
        subjects = cursor.fetchall()
        cursor.close()
        return subjects
    
    @staticmethod
    def create(course_id, code, name, description=None, credits=3, semester=None, is_core=True):
        """Create a new subject"""
        cursor = mysql.connection.cursor()
        try:
            cursor.execute("""
                INSERT INTO subjects (course_id, code, name, description, credits, semester, is_core)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (course_id, code, name, description, credits, semester, is_core))
            
            mysql.connection.commit()
            subject_id = cursor.lastrowid
            cursor.close()
            return subject_id
        except Exception as e:
            mysql.connection.rollback()
            cursor.close()
            raise e
    
    @staticmethod
    def update(subject_id, **kwargs):
        """Update subject information"""
        cursor = mysql.connection.cursor()
        try:
            update_fields = []
            values = []
            
            allowed_fields = ['code', 'name', 'description', 'credits', 'semester', 'is_core', 'is_active']
            for field in allowed_fields:
                if field in kwargs:
                    update_fields.append(f"{field} = %s")
                    values.append(kwargs[field])
            
            if update_fields:
                query = f"UPDATE subjects SET {', '.join(update_fields)} WHERE id = %s"
                values.append(subject_id)
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
    def delete(subject_id):
        """Delete a subject"""
        cursor = mysql.connection.cursor()
        try:
            cursor.execute("DELETE FROM subjects WHERE id = %s", (subject_id,))
            mysql.connection.commit()
            affected = cursor.rowcount
            cursor.close()
            return affected > 0
        except Exception as e:
            mysql.connection.rollback()
            cursor.close()
            raise e