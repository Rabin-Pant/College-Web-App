from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from utils.database import mysql
from utils.decorators import role_required
import random
import string
from datetime import datetime

class_bp = Blueprint('classes', __name__)

# ==================== HELPER FUNCTIONS ====================

def generate_class_code(length=6):
    """Generate unique 6-digit class code"""
    while True:
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))
        
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT id FROM classes WHERE class_code = %s", (code,))
        existing = cursor.fetchone()
        cursor.close()
        
        if not existing:
            return code

def get_teacher_id(user_id):
    """Get teacher profile ID from user ID"""
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT id FROM teacher_profiles WHERE user_id = %s", (user_id,))
    teacher = cursor.fetchone()
    cursor.close()
    return teacher['id'] if teacher else None

def get_student_id(user_id):
    """Get student profile ID from user ID"""
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT id FROM student_profiles WHERE user_id = %s", (user_id,))
    student = cursor.fetchone()
    cursor.close()
    return student['id'] if student else None

# ==================== TEACHER ROUTES ====================

@class_bp.route('/', methods=['POST'])
@jwt_required()
@role_required(['teacher'])
def create_class():
    """Create a new class (Teacher only)"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        # Validate required fields - ADDED course_id
        required_fields = ['name', 'course_code', 'semester', 'course_id']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Get teacher profile id
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT id FROM teacher_profiles WHERE user_id = %s", (user_id,))
        teacher = cursor.fetchone()
        
        if not teacher:
            cursor.close()
            return jsonify({'error': 'Teacher profile not found'}), 404
        
        # Verify course exists
        cursor.execute("SELECT id FROM courses WHERE id = %s", (data['course_id'],))
        if not cursor.fetchone():
            cursor.close()
            return jsonify({'error': 'Course not found'}), 404
        
        # Generate unique class code
        class_code = generate_class_code()
        
        # Create class - ADDED course_id
        cursor.execute("""
            INSERT INTO classes (
                course_id, name, course_code, section, semester, description, 
                cover_image, class_code, teacher_id, allow_pending
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            data['course_id'],  # NEW FIELD
            data['name'],
            data['course_code'],
            data.get('section', ''),
            data['semester'],
            data.get('description', ''),
            data.get('cover_image'),
            class_code,
            teacher['id'],
            data.get('allow_pending', False)
        ))
        
        mysql.connection.commit()
        class_id = cursor.lastrowid
        cursor.close()
        
        return jsonify({
            'message': 'Class created successfully',
            'class': {
                'id': class_id,
                'name': data['name'],
                'course_code': data['course_code'],
                'class_code': class_code,
                'course_id': data['course_id']
            }
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@class_bp.route('/teaching', methods=['GET'])
@jwt_required()
@role_required(['teacher'])
def get_teaching_classes():
    """Get all classes taught by current teacher"""
    try:
        user_id = get_jwt_identity()
        teacher_id = get_teacher_id(user_id)
        
        if not teacher_id:
            return jsonify({'error': 'Teacher profile not found'}), 404
        
        cursor = mysql.connection.cursor()
        cursor.execute("""
            SELECT 
                c.*,
                COUNT(DISTINCT ce.student_id) as student_count,
                COUNT(DISTINCT a.id) as assignment_count
            FROM classes c
            LEFT JOIN class_enrollments ce ON c.id = ce.class_id AND ce.status = 'approved'
            LEFT JOIN assignments a ON c.id = a.class_id
            WHERE c.teacher_id = %s AND c.is_active = TRUE
            GROUP BY c.id
            ORDER BY c.created_at DESC
        """, (teacher_id,))
        
        classes = cursor.fetchall()
        cursor.close()
        
        return jsonify({'classes': classes}), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to get classes: {str(e)}'}), 500


@class_bp.route('/<int:class_id>', methods=['PUT'])
@jwt_required()
@role_required(['teacher'])
def update_class(class_id):
    """Update class details (Teacher only)"""
    try:
        user_id = get_jwt_identity()
        teacher_id = get_teacher_id(user_id)
        data = request.get_json()
        
        # Verify ownership
        cursor = mysql.connection.cursor()
        cursor.execute("""
            SELECT id FROM classes 
            WHERE id = %s AND teacher_id = %s
        """, (class_id, teacher_id))
        
        class_exists = cursor.fetchone()
        if not class_exists:
            cursor.close()
            return jsonify({'error': 'Class not found or unauthorized'}), 404
        
        # Build update query
        update_fields = []
        values = []
        
        updatable_fields = ['name', 'description', 'section', 'semester', 'cover_image', 'is_active']
        for field in updatable_fields:
            if field in data:
                update_fields.append(f"{field} = %s")
                values.append(data[field])
        
        if not update_fields:
            cursor.close()
            return jsonify({'error': 'No fields to update'}), 400
        
        values.append(class_id)
        query = f"UPDATE classes SET {', '.join(update_fields)} WHERE id = %s"
        cursor.execute(query, tuple(values))
        mysql.connection.commit()
        cursor.close()
        
        return jsonify({'message': 'Class updated successfully'}), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to update class: {str(e)}'}), 500


@class_bp.route('/<int:class_id>', methods=['DELETE'])
@jwt_required()
@role_required(['teacher'])
def delete_class(class_id):
    """Delete class (Teacher only)"""
    try:
        user_id = get_jwt_identity()
        teacher_id = get_teacher_id(user_id)
        
        cursor = mysql.connection.cursor()
        cursor.execute("""
            DELETE FROM classes 
            WHERE id = %s AND teacher_id = %s
        """, (class_id, teacher_id))
        
        mysql.connection.commit()
        deleted = cursor.rowcount > 0
        cursor.close()
        
        if not deleted:
            return jsonify({'error': 'Class not found or unauthorized'}), 404
        
        return jsonify({'message': 'Class deleted successfully'}), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to delete class: {str(e)}'}), 500


@class_bp.route('/<int:class_id>/code', methods=['POST'])
@jwt_required()
@role_required(['teacher'])
def regenerate_class_code(class_id):
    """Generate new class code"""
    try:
        user_id = get_jwt_identity()
        teacher_id = get_teacher_id(user_id)
        
        # Verify ownership
        cursor = mysql.connection.cursor()
        cursor.execute("""
            SELECT id FROM classes 
            WHERE id = %s AND teacher_id = %s
        """, (class_id, teacher_id))
        
        if not cursor.fetchone():
            cursor.close()
            return jsonify({'error': 'Class not found or unauthorized'}), 404
        
        # Generate new unique code
        new_code = generate_class_code()
        
        cursor.execute("""
            UPDATE classes SET class_code = %s 
            WHERE id = %s
        """, (new_code, class_id))
        
        mysql.connection.commit()
        cursor.close()
        
        return jsonify({
            'message': 'Class code regenerated successfully',
            'class_code': new_code
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to regenerate code: {str(e)}'}), 500


@class_bp.route('/<int:class_id>/roster', methods=['GET'])
@jwt_required()
@role_required(['teacher'])
def get_class_roster(class_id):
    """Get all students enrolled in class"""
    try:
        user_id = get_jwt_identity()
        teacher_id = get_teacher_id(user_id)
        
        cursor = mysql.connection.cursor()
        
        # Verify ownership
        cursor.execute("""
            SELECT id FROM classes 
            WHERE id = %s AND teacher_id = %s
        """, (class_id, teacher_id))
        
        if not cursor.fetchone():
            cursor.close()
            return jsonify({'error': 'Class not found or unauthorized'}), 404
        
        # Get enrolled students
        cursor.execute("""
            SELECT 
                u.id,
                u.name,
                u.email,
                u.profile_pic,
                sp.student_id,
                sp.major,
                sp.enrollment_year,
                ce.joined_at,
                ce.status
            FROM class_enrollments ce
            JOIN student_profiles sp ON ce.student_id = sp.id
            JOIN users u ON sp.user_id = u.id
            WHERE ce.class_id = %s
            ORDER BY ce.joined_at DESC
        """, (class_id,))
        
        students = cursor.fetchall()
        cursor.close()
        
        return jsonify({
            'class_id': class_id,
            'total_students': len(students),
            'students': students
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to get roster: {str(e)}'}), 500


@class_bp.route('/<int:class_id>/students/<int:student_id>', methods=['DELETE'])
@jwt_required()
@role_required(['teacher'])
def remove_student(class_id, student_id):
    """Remove student from class"""
    try:
        user_id = get_jwt_identity()
        teacher_id = get_teacher_id(user_id)
        
        cursor = mysql.connection.cursor()
        
        # Verify ownership
        cursor.execute("""
            SELECT id FROM classes 
            WHERE id = %s AND teacher_id = %s
        """, (class_id, teacher_id))
        
        if not cursor.fetchone():
            cursor.close()
            return jsonify({'error': 'Class not found or unauthorized'}), 404
        
        # Remove student
        cursor.execute("""
            DELETE FROM class_enrollments 
            WHERE class_id = %s AND student_id = %s
        """, (class_id, student_id))
        
        mysql.connection.commit()
        removed = cursor.rowcount > 0
        cursor.close()
        
        if not removed:
            return jsonify({'error': 'Student not found in class'}), 404
        
        return jsonify({'message': 'Student removed from class'}), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to remove student: {str(e)}'}), 500


# ==================== STUDENT ROUTES ====================

@class_bp.route('/join', methods=['POST'])
@jwt_required()
@role_required(['student'])
def join_class():
    """Join a class using class code"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data.get('class_code'):
            return jsonify({'error': 'Class code required'}), 400
        
        class_code = data['class_code'].strip().upper()
        
        # Get student profile ID
        student_id = get_student_id(user_id)
        if not student_id:
            return jsonify({'error': 'Student profile not found'}), 404
        
        cursor = mysql.connection.cursor()
        
        # Find class by code
        cursor.execute("""
            SELECT id, name, course_code, teacher_id 
            FROM classes 
            WHERE class_code = %s AND is_active = TRUE
        """, (class_code,))
        
        class_data = cursor.fetchone()
        if not class_data:
            cursor.close()
            return jsonify({'error': 'Invalid class code'}), 404
        
        # Check if already enrolled
        cursor.execute("""
            SELECT id, status FROM class_enrollments 
            WHERE student_id = %s AND class_id = %s
        """, (student_id, class_data['id']))
        
        existing = cursor.fetchone()
        if existing:
            cursor.close()
            if existing['status'] == 'pending':
                return jsonify({'error': 'Enrollment already pending approval'}), 400
            elif existing['status'] == 'approved':
                return jsonify({'error': 'Already enrolled in this class'}), 400
            elif existing['status'] == 'rejected':
                return jsonify({'error': 'Your enrollment was rejected'}), 400
        
        # Enroll student (auto-approved or pending based on class settings)
        # Default to auto-approved for now
        cursor.execute("""
            INSERT INTO class_enrollments (student_id, class_id, status)
            VALUES (%s, %s, 'approved')
        """, (student_id, class_data['id']))
        
        mysql.connection.commit()
        cursor.close()
        
        return jsonify({
            'message': 'Successfully joined class!',
            'class': {
                'id': class_data['id'],
                'name': class_data['name'],
                'course_code': class_data['course_code']
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to join class: {str(e)}'}), 500


@class_bp.route('/enrolled', methods=['GET'])
@jwt_required()
@role_required(['student'])
def get_enrolled_classes():
    """Get all classes current student is enrolled in"""
    try:
        user_id = get_jwt_identity()
        student_id = get_student_id(user_id)
        
        if not student_id:
            return jsonify({'error': 'Student profile not found'}), 404
        
        cursor = mysql.connection.cursor()
        cursor.execute("""
            SELECT 
                c.*,
                u.name as teacher_name,
                tp.employee_id as teacher_id,
                ce.joined_at as enrolled_date,
                (
                    SELECT COUNT(*) FROM assignments a 
                    WHERE a.class_id = c.id AND a.due_date > NOW()
                ) as pending_assignments,
                (
                    SELECT COUNT(*) FROM materials m 
                    WHERE m.class_id = c.id
                ) as materials_count
            FROM class_enrollments ce
            JOIN classes c ON ce.class_id = c.id
            JOIN teacher_profiles tp ON c.teacher_id = tp.id
            JOIN users u ON tp.user_id = u.id
            WHERE ce.student_id = %s AND ce.status = 'approved' AND c.is_active = TRUE
            ORDER BY ce.joined_at DESC
        """, (student_id,))
        
        classes = cursor.fetchall()
        cursor.close()
        
        return jsonify({'classes': classes}), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to get enrolled classes: {str(e)}'}), 500


# ==================== COMMON ROUTES ====================

@class_bp.route('/<int:class_id>', methods=['GET'])
@jwt_required()
def get_class_details(class_id):
    """Get detailed class information"""
    try:
        user_id = get_jwt_identity()
        
        cursor = mysql.connection.cursor()
        
        # Get class details with teacher info - REMOVED the problematic view
        cursor.execute("""
            SELECT 
                c.*,
                u.name as teacher_name,
                u.email as teacher_email
            FROM classes c
            JOIN teacher_profiles tp ON c.teacher_id = tp.id
            JOIN users u ON tp.user_id = u.id
            WHERE c.id = %s
        """, (class_id,))
        
        class_data = cursor.fetchone()
        
        if not class_data:
            cursor.close()
            return jsonify({'error': 'Class not found'}), 404
        
        # Check if user has access
        cursor.execute("SELECT role FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        
        has_access = False
        enrollment_status = None
        
        if user['role'] == 'teacher':
            # Check if teacher owns this class
            cursor.execute("""
                SELECT tp.id FROM teacher_profiles tp
                WHERE tp.user_id = %s AND tp.id = %s
            """, (user_id, class_data['teacher_id']))
            has_access = cursor.fetchone() is not None
            
        elif user['role'] == 'student':
            # Check if student is enrolled
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
                if enrollment:
                    has_access = enrollment['status'] == 'approved'
                    enrollment_status = enrollment['status']
        
        cursor.close()
        
        return jsonify({
            'class': class_data,
            'has_access': has_access,
            'enrollment_status': enrollment_status
        }), 200
        
    except Exception as e:
        print(f"Error in get_class_details: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@class_bp.route('/<int:class_id>/stats', methods=['GET'])
@jwt_required()
def get_class_stats(class_id):
    """Get class statistics"""
    try:
        user_id = get_jwt_identity()
        
        cursor = mysql.connection.cursor()
        
        # Check access
        cursor.execute("SELECT role FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        
        if user['role'] == 'teacher':
            teacher_id = get_teacher_id(user_id)
            cursor.execute("""
                SELECT id FROM classes 
                WHERE id = %s AND teacher_id = %s
            """, (class_id, teacher_id))
            
            if not cursor.fetchone():
                cursor.close()
                return jsonify({'error': 'Unauthorized'}), 403
                
        elif user['role'] == 'student':
            student_id = get_student_id(user_id)
            cursor.execute("""
                SELECT id FROM class_enrollments 
                WHERE class_id = %s AND student_id = %s AND status = 'approved'
            """, (class_id, student_id))
            
            if not cursor.fetchone():
                cursor.close()
                return jsonify({'error': 'Unauthorized'}), 403
        
        # Get comprehensive stats
        cursor.execute("""
            SELECT 
                -- Student counts
                COUNT(DISTINCT ce.student_id) as total_students,
                COUNT(DISTINCT CASE WHEN ce.status = 'pending' THEN ce.student_id END) as pending_students,
                
                -- Assignment stats
                COUNT(DISTINCT a.id) as total_assignments,
                COUNT(DISTINCT CASE WHEN a.due_date > NOW() THEN a.id END) as upcoming_assignments,
                AVG(a.points_possible) as avg_points_possible,
                
                -- Submission stats
                COUNT(DISTINCT s.id) as total_submissions,
                COUNT(DISTINCT CASE WHEN s.status = 'graded' THEN s.id END) as graded_submissions,
                AVG(s.grade) as average_grade,
                
                -- Material stats
                COUNT(DISTINCT m.id) as total_materials
                
            FROM classes c
            LEFT JOIN class_enrollments ce ON c.id = ce.class_id
            LEFT JOIN assignments a ON c.id = a.class_id
            LEFT JOIN submissions s ON a.id = s.assignment_id
            LEFT JOIN materials m ON c.id = m.class_id
            WHERE c.id = %s
            GROUP BY c.id
        """, (class_id,))
        
        stats = cursor.fetchone()
        cursor.close()
        
        return jsonify(stats), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to get class stats: {str(e)}'}), 500