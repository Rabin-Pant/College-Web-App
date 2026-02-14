from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from utils.database import mysql
from utils.decorators import admin_required, role_required
from utils.auth_helpers import generate_employee_id, generate_student_id
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta

admin_bp = Blueprint('admin', __name__)

# ============ USER MANAGEMENT ============

@admin_bp.route('/users', methods=['GET'])
@jwt_required()
@admin_required
def get_all_users():
    """Get all users with filtering (Admin only)"""
    try:
        role = request.args.get('role')
        verified = request.args.get('verified')
        search = request.args.get('search')
        limit = request.args.get('limit', 100)
        offset = request.args.get('offset', 0)
        
        cursor = mysql.connection.cursor()
        
        query = """
            SELECT 
                u.id, u.email, u.name, u.role, 
                u.profile_pic, u.email_verified, u.created_at,
                tp.employee_id,
                sp.student_id,
                sp.major,
                sp.enrollment_year
            FROM users u
            LEFT JOIN teacher_profiles tp ON u.id = tp.user_id
            LEFT JOIN student_profiles sp ON u.id = sp.user_id
            WHERE 1=1
        """
        params = []
        
        if role:
            query += " AND u.role = %s"
            params.append(role)
        
        if verified is not None:
            query += " AND u.email_verified = %s"
            params.append(verified.lower() == 'true')
        
        if search:
            query += " AND (u.name LIKE %s OR u.email LIKE %s)"
            params.append(f'%{search}%')
            params.append(f'%{search}%')
        
        query += " ORDER BY u.created_at DESC LIMIT %s OFFSET %s"
        params.extend([int(limit), int(offset)])
        
        cursor.execute(query, params)
        users = cursor.fetchall()
        
        # Get total count
        cursor.execute("SELECT COUNT(*) as count FROM users")
        total = cursor.fetchone()['count']
        
        cursor.close()
        
        return jsonify({
            'total': total,
            'users': users
        }), 200
        
    except Exception as e:
        print(f"Error getting users: {e}")
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/users/<int:user_id>', methods=['GET'])
@jwt_required()
@admin_required
def get_user_details(user_id):
    """Get detailed user information (Admin only)"""
    try:
        cursor = mysql.connection.cursor()
        
        # Get base user info
        cursor.execute("""
            SELECT id, email, name, role, profile_pic, bio, 
                   department, email_verified, created_at, updated_at
            FROM users WHERE id = %s
        """, (user_id,))
        
        user = cursor.fetchone()
        
        if not user:
            cursor.close()
            return jsonify({'error': 'User not found'}), 404
        
        # Get role-specific profile
        if user['role'] == 'teacher':
            cursor.execute("""
                SELECT employee_id, department, office_hours, qualifications
                FROM teacher_profiles WHERE user_id = %s
            """, (user_id,))
            profile = cursor.fetchone()
            if profile:
                user.update(profile)
                
        elif user['role'] == 'student':
            cursor.execute("""
                SELECT student_id, enrollment_year, major, minor, current_semester, advisor_name
                FROM student_profiles WHERE user_id = %s
            """, (user_id,))
            profile = cursor.fetchone()
            if profile:
                user.update(profile)
        
        # Get user stats
        if user['role'] == 'teacher':
            cursor.execute("""
                SELECT 
                    COUNT(DISTINCT c.id) as total_classes,
                    COUNT(DISTINCT ce.student_id) as total_students,
                    COUNT(DISTINCT a.id) as total_assignments
                FROM teacher_profiles tp
                LEFT JOIN classes c ON tp.id = c.teacher_id
                LEFT JOIN class_enrollments ce ON c.id = ce.class_id AND ce.status = 'approved'
                LEFT JOIN assignments a ON c.id = a.class_id
                WHERE tp.user_id = %s
            """, (user_id,))
            stats = cursor.fetchone()
            user['stats'] = stats
            
        elif user['role'] == 'student':
            cursor.execute("""
                SELECT 
                    COUNT(DISTINCT ce.class_id) as enrolled_classes,
                    COUNT(DISTINCT s.id) as total_submissions,
                    AVG(s.grade) as average_grade
                FROM student_profiles sp
                LEFT JOIN class_enrollments ce ON sp.id = ce.student_id AND ce.status = 'approved'
                LEFT JOIN submissions s ON s.student_id = sp.user_id
                WHERE sp.user_id = %s
            """, (user_id,))
            stats = cursor.fetchone()
            user['stats'] = stats
        
        cursor.close()
        return jsonify(user), 200
        
    except Exception as e:
        print(f"Error getting user details: {e}")
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/users/<int:user_id>/verify', methods=['PUT'])
@jwt_required()
@admin_required
def verify_teacher(user_id):
    """Verify a teacher account (Admin only)"""
    try:
        admin_id = get_jwt_identity()
        cursor = mysql.connection.cursor()
        
        # Check if user is teacher
        cursor.execute("SELECT role, name FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        
        if not user:
            cursor.close()
            return jsonify({'error': 'User not found'}), 404
        
        if user['role'] != 'teacher':
            cursor.close()
            return jsonify({'error': 'User is not a teacher'}), 400
        
        # Verify teacher
        cursor.execute("""
            UPDATE users 
            SET email_verified = TRUE 
            WHERE id = %s
        """, (user_id,))
        
        mysql.connection.commit()
        
        # Log the action
        print(f"Admin {admin_id} verified teacher {user_id} - {user['name']}")
        
        cursor.close()
        
        return jsonify({'message': f'Teacher {user["name"]} verified successfully'}), 200
        
    except Exception as e:
        print(f"Error verifying teacher: {e}")
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/users/<int:user_id>', methods=['DELETE'])
@jwt_required()
@admin_required
def delete_user(user_id):
    """Delete a user (Admin only)"""
    try:
        admin_id = get_jwt_identity()
        
        # Don't allow deleting yourself
        if admin_id == user_id:
            return jsonify({'error': 'Cannot delete your own account'}), 400
        
        cursor = mysql.connection.cursor()
        
        # Get user info before deletion
        cursor.execute("SELECT name, role, email FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        
        if not user:
            cursor.close()
            return jsonify({'error': 'User not found'}), 404
        
        # Delete user (cascades to profiles)
        cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
        mysql.connection.commit()
        
        print(f"Admin {admin_id} deleted user {user_id} - {user['name']} ({user['role']})")
        
        cursor.close()
        
        return jsonify({
            'message': f'User {user["name"]} deleted successfully',
            'deleted_user': user
        }), 200
        
    except Exception as e:
        print(f"Error deleting user: {e}")
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/users', methods=['POST'])
@jwt_required()
@admin_required
def create_user():
    """Create a new user (Admin only)"""
    try:
        data = request.get_json()
        
        required_fields = ['email', 'password', 'name', 'role']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        cursor = mysql.connection.cursor()
        
        # Check if email exists
        cursor.execute("SELECT id FROM users WHERE email = %s", (data['email'],))
        if cursor.fetchone():
            cursor.close()
            return jsonify({'error': 'Email already registered'}), 400
        
        # Hash password
        hashed_password = generate_password_hash(data['password'])
        
        # Create user
        cursor.execute("""
            INSERT INTO users (email, password, name, role, email_verified, college_email, department, bio)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            data['email'],
            hashed_password,
            data['name'],
            data['role'],
            data.get('email_verified', True),
            data.get('college_email', data['email']),
            data.get('department'),
            data.get('bio')
        ))
        
        user_id = cursor.lastrowid
        
        # Create role-specific profile
        if data['role'] == 'teacher':
            employee_id = data.get('employee_id', generate_employee_id())
            cursor.execute("""
                INSERT INTO teacher_profiles (user_id, employee_id, department, office_hours, qualifications)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                user_id,
                employee_id,
                data.get('department', 'General'),
                data.get('office_hours'),
                data.get('qualifications')
            ))
            
        elif data['role'] == 'student':
            student_id = data.get('student_id', generate_student_id())
            cursor.execute("""
                INSERT INTO student_profiles (user_id, student_id, enrollment_year, major, minor, current_semester)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                user_id,
                student_id,
                data.get('enrollment_year', datetime.now().year),
                data.get('major', 'Undeclared'),
                data.get('minor'),
                data.get('current_semester', 1)
            ))
        
        mysql.connection.commit()
        cursor.close()
        
        return jsonify({
            'message': 'User created successfully',
            'user_id': user_id
        }), 201
        
    except Exception as e:
        print(f"Error creating user: {e}")
        return jsonify({'error': str(e)}), 500


# ============ CLASS MANAGEMENT ============

@admin_bp.route('/classes', methods=['GET'])
@jwt_required()
@admin_required
def get_all_classes():
    """Get all classes in the system (Admin only)"""
    try:
        cursor = mysql.connection.cursor()
        
        # Get all classes with teacher info and stats
        cursor.execute("""
            SELECT 
                c.*,
                u.name as teacher_name,
                u.email as teacher_email,
                tp.employee_id as teacher_employee_id,
                COUNT(DISTINCT ce.student_id) as student_count,
                COUNT(DISTINCT a.id) as assignment_count,
                COUNT(DISTINCT m.id) as material_count
            FROM classes c
            JOIN teacher_profiles tp ON c.teacher_id = tp.id
            JOIN users u ON tp.user_id = u.id
            LEFT JOIN class_enrollments ce ON c.id = ce.class_id AND ce.status = 'approved'
            LEFT JOIN assignments a ON c.id = a.class_id
            LEFT JOIN materials m ON c.id = m.class_id
            GROUP BY c.id
            ORDER BY c.created_at DESC
        """)
        
        classes = cursor.fetchall()
        cursor.close()
        
        return jsonify({
            'total': len(classes),
            'classes': classes
        }), 200
        
    except Exception as e:
        print(f"Error getting all classes: {e}")
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/classes/<int:class_id>', methods=['GET'])
@jwt_required()
@admin_required
def admin_get_class_details(class_id):
    """Get detailed information about a specific class (Admin only)"""
    try:
        cursor = mysql.connection.cursor()
        
        # Get class details with teacher info
        cursor.execute("""
            SELECT 
                c.*,
                u.name as teacher_name,
                u.email as teacher_email,
                u.id as teacher_user_id,
                tp.employee_id as teacher_employee_id,
                tp.office_hours as teacher_office_hours
            FROM classes c
            JOIN teacher_profiles tp ON c.teacher_id = tp.id
            JOIN users u ON tp.user_id = u.id
            WHERE c.id = %s
        """, (class_id,))
        
        class_data = cursor.fetchone()
        
        if not class_data:
            cursor.close()
            return jsonify({'error': 'Class not found'}), 404
        
        # Get enrolled students
        cursor.execute("""
            SELECT 
                u.id,
                u.name,
                u.email,
                sp.student_id,
                sp.major,
                ce.joined_at
            FROM class_enrollments ce
            JOIN student_profiles sp ON ce.student_id = sp.id
            JOIN users u ON sp.user_id = u.id
            WHERE ce.class_id = %s AND ce.status = 'approved'
            ORDER BY ce.joined_at DESC
        """, (class_id,))
        
        students = cursor.fetchall()
        
        # Get assignments
        cursor.execute("""
            SELECT 
                id, title, due_date, points_possible, is_published,
                (SELECT COUNT(*) FROM submissions s WHERE s.assignment_id = a.id) as submission_count
            FROM assignments a
            WHERE class_id = %s
            ORDER BY due_date DESC
        """, (class_id,))
        
        assignments = cursor.fetchall()
        
        cursor.close()
        
        return jsonify({
            'class': class_data,
            'students': students,
            'students_count': len(students),
            'assignments': assignments,
            'assignments_count': len(assignments)
        }), 200
        
    except Exception as e:
        print(f"Error getting class details: {e}")
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/classes/<int:class_id>', methods=['DELETE'])
@jwt_required()
@admin_required
def admin_delete_class(class_id):
    """Delete any class (Admin only)"""
    try:
        admin_id = get_jwt_identity()
        cursor = mysql.connection.cursor()
        
        # Check if class exists
        cursor.execute("SELECT * FROM classes WHERE id = %s", (class_id,))
        class_data = cursor.fetchone()
        
        if not class_data:
            cursor.close()
            return jsonify({'error': 'Class not found'}), 404
        
        # Get class info for logging
        class_name = class_data['name']
        teacher_id = class_data['teacher_id']
        
        # Delete the class (cascades to assignments, materials, enrollments)
        cursor.execute("DELETE FROM classes WHERE id = %s", (class_id,))
        mysql.connection.commit()
        
        # Log the action
        print(f"Admin {admin_id} deleted class '{class_name}' (ID: {class_id}) taught by teacher {teacher_id}")
        
        cursor.close()
        
        return jsonify({
            'message': f'Class "{class_name}" deleted successfully',
            'class_id': class_id
        }), 200
        
    except Exception as e:
        print(f"Error deleting class: {e}")
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/classes/stats', methods=['GET'])
@jwt_required()
@admin_required
def admin_class_stats():
    """Get class statistics (Admin only)"""
    try:
        cursor = mysql.connection.cursor()
        
        # Total classes
        cursor.execute("SELECT COUNT(*) as total FROM classes")
        total_classes = cursor.fetchone()['total']
        
        # Active classes
        cursor.execute("SELECT COUNT(*) as active FROM classes WHERE is_active = TRUE")
        active_classes = cursor.fetchone()['active']
        
        # Classes by semester
        cursor.execute("""
            SELECT semester, COUNT(*) as count 
            FROM classes 
            GROUP BY semester 
            ORDER BY semester DESC
            LIMIT 5
        """)
        classes_by_semester = cursor.fetchall()
        
        # Top teachers by class count
        cursor.execute("""
            SELECT 
                u.name,
                u.email,
                COUNT(c.id) as class_count,
                COUNT(DISTINCT ce.student_id) as total_students
            FROM users u
            JOIN teacher_profiles tp ON u.id = tp.user_id
            LEFT JOIN classes c ON tp.id = c.teacher_id
            LEFT JOIN class_enrollments ce ON c.id = ce.class_id AND ce.status = 'approved'
            WHERE u.role = 'teacher'
            GROUP BY u.id, u.name, u.email
            ORDER BY class_count DESC
            LIMIT 5
        """)
        top_teachers = cursor.fetchall()
        
        cursor.close()
        
        return jsonify({
            'total_classes': total_classes,
            'active_classes': active_classes,
            'inactive_classes': total_classes - active_classes,
            'classes_by_semester': classes_by_semester,
            'top_teachers': top_teachers
        }), 200
        
    except Exception as e:
        print(f"Error getting class stats: {e}")
        return jsonify({'error': str(e)}), 500


# ============ SYSTEM STATISTICS ============

@admin_bp.route('/stats', methods=['GET'])
@jwt_required()
@admin_required
def get_system_stats():
    """Get system statistics (Admin only)"""
    try:
        cursor = mysql.connection.cursor()
        
        # User counts by role
        cursor.execute("SELECT role, COUNT(*) as count FROM users GROUP BY role")
        user_stats_raw = cursor.fetchall()
        user_stats = {stat['role']: stat['count'] for stat in user_stats_raw}
        
        # Class counts
        cursor.execute("SELECT COUNT(*) as count FROM classes")
        total_classes = cursor.fetchone()['count']
        
        # Assignment counts
        cursor.execute("SELECT COUNT(*) as count FROM assignments")
        total_assignments = cursor.fetchone()['count']
        
        # Material counts
        cursor.execute("SELECT COUNT(*) as count FROM materials")
        total_materials = cursor.fetchone()['count']
        
        # Submission counts
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN status = 'submitted' THEN 1 ELSE 0 END) as pending,
                SUM(CASE WHEN status = 'graded' THEN 1 ELSE 0 END) as graded,
                SUM(CASE WHEN is_late = TRUE THEN 1 ELSE 0 END) as late
            FROM submissions
        """)
        submission_stats = cursor.fetchone()
        
        # Active users (last 7 days)
        cursor.execute("""
            SELECT COUNT(DISTINCT user_id) as count 
            FROM notifications 
            WHERE created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
        """)
        active_users_7d = cursor.fetchone()['count']
        
        # New users this month
        cursor.execute("""
            SELECT COUNT(*) as count 
            FROM users 
            WHERE created_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)
        """)
        new_users_30d = cursor.fetchone()['count']
        
        # Recent activity
        cursor.execute("""
            (SELECT 'user' as type, 'New user registered' as action, created_at as date
             FROM users ORDER BY created_at DESC LIMIT 5)
            UNION
            (SELECT 'class' as type, 'Class created' as action, created_at as date
             FROM classes ORDER BY created_at DESC LIMIT 5)
            UNION
            (SELECT 'assignment' as type, 'Assignment created' as action, created_at as date
             FROM assignments ORDER BY created_at DESC LIMIT 5)
            UNION
            (SELECT 'submission' as type, 'Assignment submitted' as action, submitted_at as date
             FROM submissions ORDER BY submitted_at DESC LIMIT 5)
            ORDER BY date DESC
            LIMIT 10
        """)
        recent_activity = cursor.fetchall()
        
        cursor.close()
        
        return jsonify({
            'users': {
                'admin': user_stats.get('admin', 0),
                'teacher': user_stats.get('teacher', 0),
                'student': user_stats.get('student', 0),
                'total': sum(user_stats.values())
            },
            'total_classes': total_classes,
            'total_assignments': total_assignments,
            'total_materials': total_materials,
            'submissions': {
                'total': submission_stats['total'] or 0,
                'pending': submission_stats['pending'] or 0,
                'graded': submission_stats['graded'] or 0,
                'late': submission_stats['late'] or 0
            },
            'active_users_7d': active_users_7d,
            'new_users_30d': new_users_30d,
            'recent_activity': recent_activity
        }), 200
        
    except Exception as e:
        print(f"Error getting system stats: {e}")
        return jsonify({'error': str(e)}), 500


# ============ SYSTEM ANNOUNCEMENTS ============

@admin_bp.route('/announcements', methods=['POST'])
@jwt_required()
@admin_required
def system_announcement():
    """Create system-wide announcement (Admin only)"""
    try:
        admin_id = get_jwt_identity()
        data = request.get_json()
        
        if not data.get('title') or not data.get('message'):
            return jsonify({'error': 'Title and message are required'}), 400
        
        cursor = mysql.connection.cursor()
        
        # Get all users
        cursor.execute("SELECT id FROM users")
        users = cursor.fetchall()
        
        # Create notification for all users
        for user in users:
            cursor.execute("""
                INSERT INTO notifications 
                (user_id, type, title, message, link)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                user['id'],
                'system_announcement',
                f"[SYSTEM] {data['title']}",
                data['message'],
                data.get('link', '/')
            ))
        
        mysql.connection.commit()
        
        print(f"Admin {admin_id} sent system announcement: {data['title']}")
        
        cursor.close()
        
        return jsonify({
            'message': f'System announcement sent to {len(users)} users',
            'recipients': len(users)
        }), 201
        
    except Exception as e:
        print(f"Error sending announcement: {e}")
        return jsonify({'error': str(e)}), 500


# ============ REPORTS ============

@admin_bp.route('/reports/classes', methods=['GET'])
@jwt_required()
@admin_required
def class_report():
    """Generate class report (Admin only)"""
    try:
        cursor = mysql.connection.cursor()
        
        cursor.execute("""
            SELECT 
                c.id,
                c.name,
                c.course_code,
                c.semester,
                u.name as teacher_name,
                u.email as teacher_email,
                COUNT(DISTINCT ce.student_id) as student_count,
                COUNT(DISTINCT a.id) as assignment_count,
                COUNT(DISTINCT m.id) as material_count,
                COUNT(DISTINCT s.id) as submission_count,
                AVG(s.grade) as average_grade,
                c.created_at
            FROM classes c
            JOIN teacher_profiles tp ON c.teacher_id = tp.id
            JOIN users u ON tp.user_id = u.id
            LEFT JOIN class_enrollments ce ON c.id = ce.class_id AND ce.status = 'approved'
            LEFT JOIN assignments a ON c.id = a.class_id
            LEFT JOIN materials m ON c.id = m.class_id
            LEFT JOIN submissions s ON a.id = s.assignment_id
            GROUP BY c.id
            ORDER BY c.created_at DESC
        """)
        
        classes = cursor.fetchall()
        cursor.close()
        
        return jsonify({
            'generated_at': datetime.now().isoformat(),
            'total_classes': len(classes),
            'classes': classes
        }), 200
        
    except Exception as e:
        print(f"Error generating class report: {e}")
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/reports/users', methods=['GET'])
@jwt_required()
@admin_required
def user_report():
    """Generate user report (Admin only)"""
    try:
        cursor = mysql.connection.cursor()
        
        # Users by role
        cursor.execute("""
            SELECT 
                role,
                COUNT(*) as count,
                SUM(CASE WHEN email_verified = TRUE THEN 1 ELSE 0 END) as verified,
                AVG(TIMESTAMPDIFF(DAY, created_at, NOW())) as avg_days_since_join
            FROM users
            GROUP BY role
        """)
        users_by_role = cursor.fetchall()
        
        # New users over time (last 6 months)
        cursor.execute("""
            SELECT 
                DATE_FORMAT(created_at, '%Y-%m') as month,
                COUNT(*) as count
            FROM users
            WHERE created_at >= DATE_SUB(NOW(), INTERVAL 6 MONTH)
            GROUP BY DATE_FORMAT(created_at, '%Y-%m')
            ORDER BY month DESC
        """)
        new_users_timeline = cursor.fetchall()
        
        cursor.close()
        
        return jsonify({
            'generated_at': datetime.now().isoformat(),
            'users_by_role': users_by_role,
            'new_users_timeline': new_users_timeline
        }), 200
        
    except Exception as e:
        print(f"Error generating user report: {e}")
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/reports/export', methods=['POST'])
@jwt_required()
@admin_required
def export_report():
    """Export report as CSV/JSON (Admin only)"""
    try:
        data = request.get_json()
        report_type = data.get('type', 'classes')
        format_type = data.get('format', 'json')
        
        cursor = mysql.connection.cursor()
        
        if report_type == 'classes':
            cursor.execute("""
                SELECT 
                    c.id, c.name, c.course_code, c.section, c.semester,
                    u.name as teacher_name, u.email as teacher_email,
                    COUNT(DISTINCT ce.student_id) as students,
                    COUNT(DISTINCT a.id) as assignments
                FROM classes c
                JOIN teacher_profiles tp ON c.teacher_id = tp.id
                JOIN users u ON tp.user_id = u.id
                LEFT JOIN class_enrollments ce ON c.id = ce.class_id AND ce.status = 'approved'
                LEFT JOIN assignments a ON c.id = a.class_id
                GROUP BY c.id
            """)
            results = cursor.fetchall()
            
        elif report_type == 'users':
            cursor.execute("""
                SELECT 
                    id, email, name, role, email_verified,
                    DATE_FORMAT(created_at, '%Y-%m-%d') as join_date
                FROM users
                ORDER BY created_at DESC
            """)
            results = cursor.fetchall()
            
        elif report_type == 'assignments':
            cursor.execute("""
                SELECT 
                    a.id, a.title, a.due_date, a.points_possible,
                    c.name as class_name, c.course_code,
                    COUNT(s.id) as submissions,
                    AVG(s.grade) as average_grade
                FROM assignments a
                JOIN classes c ON a.class_id = c.id
                LEFT JOIN submissions s ON a.id = s.assignment_id
                GROUP BY a.id
                ORDER BY a.due_date DESC
            """)
            results = cursor.fetchall()
            
        else:
            cursor.close()
            return jsonify({'error': 'Invalid report type'}), 400
        
        cursor.close()
        
        return jsonify({
            'generated_at': datetime.now().isoformat(),
            'type': report_type,
            'format': format_type,
            'count': len(results),
            'data': results
        }), 200
        
    except Exception as e:
        print(f"Error exporting report: {e}")
        return jsonify({'error': str(e)}), 500


# ============ HEALTH CHECK ============

@admin_bp.route('/health', methods=['GET'])
@jwt_required()
@admin_required
def admin_health():
    """Admin health check"""
    return jsonify({
        'status': 'healthy',
        'service': 'admin',
        'timestamp': datetime.now().isoformat()
    }), 200