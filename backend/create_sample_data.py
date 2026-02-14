from app import app
from utils.database import mysql
from werkzeug.security import generate_password_hash
import random

with app.app_context():
    cursor = mysql.connection.cursor()
    
    print("="*50)
    print("📊 CREATING SAMPLE DATA")
    print("="*50)
    
    # 1. Get or create teacher
    cursor.execute("SELECT id FROM users WHERE email = 'teacher@yourcollege.edu'")
    teacher = cursor.fetchone()
    
    if not teacher:
        hashed_pw = generate_password_hash('Test@123')
        cursor.execute("""
            INSERT INTO users (email, password, name, role, email_verified, college_email)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, ('teacher@yourcollege.edu', hashed_pw, 'Dr. John Smith', 'teacher', True, 'teacher@yourcollege.edu'))
        teacher_id = cursor.lastrowid
        
        cursor.execute("""
            INSERT INTO teacher_profiles (user_id, employee_id, department, office_hours)
            VALUES (%s, %s, %s, %s)
        """, (teacher_id, 'T2024001', 'Computer Science', 'Mon/Wed 2-4 PM'))
        print(f"✅ Teacher created with ID: {teacher_id}")
    else:
        teacher_id = teacher['id']
        print(f"✅ Teacher exists with ID: {teacher_id}")
    
    # 2. Get or create student
    cursor.execute("SELECT id FROM users WHERE email = 'student@yourcollege.edu'")
    student = cursor.fetchone()
    
    if not student:
        hashed_pw = generate_password_hash('Test@123')
        cursor.execute("""
            INSERT INTO users (email, password, name, role, email_verified, college_email)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, ('student@yourcollege.edu', hashed_pw, 'Jane Doe', 'student', True, 'student@yourcollege.edu'))
        student_id = cursor.lastrowid
        
        cursor.execute("""
            INSERT INTO student_profiles (user_id, student_id, enrollment_year, major)
            VALUES (%s, %s, %s, %s)
        """, (student_id, 'S2024001', 2024, 'Computer Science'))
        print(f"✅ Student created with ID: {student_id}")
    else:
        student_id = student['id']
        print(f"✅ Student exists with ID: {student_id}")
    
    # 3. Get courses and subjects
    cursor.execute("SELECT id FROM courses LIMIT 1")
    course = cursor.fetchone()
    
    if not course:
        print("❌ No courses found! Please run new_schema.sql first.")
        cursor.close()
        exit()
    
    cursor.execute("SELECT id FROM subjects WHERE course_id = %s LIMIT 1", (course['id'],))
    subject = cursor.fetchone()
    
    if not subject:
        # Create a sample subject
        cursor.execute("""
            INSERT INTO subjects (course_id, code, name, credits, semester)
            VALUES (%s, %s, %s, %s, %s)
        """, (course['id'], 'CS101', 'Introduction to Programming', 3, 1))
        subject_id = cursor.lastrowid
        print(f"✅ Sample subject created with ID: {subject_id}")
    else:
        subject_id = subject['id']
        print(f"✅ Subject exists with ID: {subject_id}")
    
    # 4. Create a section
    cursor.execute("""
        INSERT INTO sections (subject_id, name, academic_year, semester, capacity, room)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (subject_id, 'A', '2024-2025', 'Fall 2024', 30, '101'))
    section_id = cursor.lastrowid
    print(f"✅ Section created with ID: {section_id}")
    
    # 5. Assign teacher to section
    cursor.execute("""
        INSERT INTO teacher_assignments (teacher_id, section_id, is_primary)
        VALUES (%s, %s, %s)
    """, (teacher_id, section_id, True))
    print(f"✅ Teacher assigned to section {section_id}")
    
    # 6. Enroll student in section
    cursor.execute("""
        INSERT INTO enrollments (student_id, section_id, status, enrollment_date)
        VALUES (%s, %s, %s, %s)
    """, (student_id, section_id, 'approved', '2024-01-15'))
    print(f"✅ Student enrolled in section {section_id}")
    
    # 7. Update section enrolled count
    cursor.execute("""
        UPDATE sections SET enrolled_count = 1 WHERE id = %s
    """, (section_id,))
    
    # 8. Create a schedule
    days = ['Monday', 'Wednesday']
    for day in days:
        cursor.execute("""
            INSERT INTO schedules (section_id, day, start_time, end_time, room)
            VALUES (%s, %s, %s, %s, %s)
        """, (section_id, day, '10:00:00', '11:30:00', '101'))
    print(f"✅ Schedule created for section {section_id}")
    
    # 9. Create a sample assignment
    cursor.execute("""
        INSERT INTO assignments (title, instructions, due_date, points_possible, section_id, is_published)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, ('Assignment 1', 'Complete the exercises', '2024-02-15 23:59:00', 100, section_id, True))
    assignment_id = cursor.lastrowid
    print(f"✅ Assignment created with ID: {assignment_id}")
    
    # 10. Upload sample material
    cursor.execute("""
        INSERT INTO materials (title, description, type, section_id, uploaded_by)
        VALUES (%s, %s, %s, %s, %s)
    """, ('Lecture 1 Slides', 'Introduction to the course', 'pdf', section_id, teacher_id))
    print(f"✅ Material uploaded")
    
    mysql.connection.commit()
    print("="*50)
    print("✅ ALL SAMPLE DATA CREATED SUCCESSFULLY!")
    print("="*50)
    print(f"Teacher Email: teacher@yourcollege.edu")
    print(f"Student Email: student@yourcollege.edu")
    print(f"Password for both: Test@123")
    print("="*50)
    
    cursor.close()
