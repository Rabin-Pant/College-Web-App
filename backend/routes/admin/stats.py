from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required
from utils.database import mysql
from utils.decorators import admin_required
from datetime import datetime

admin_stats_bp = Blueprint('admin_stats', __name__)

@admin_stats_bp.route('/', methods=['GET'], strict_slashes=False)
@jwt_required()
@admin_required
def get_system_stats():
    """Get system statistics"""
    try:
        cursor = mysql.connection.cursor()
        
        # User counts by role
        cursor.execute("SELECT role, COUNT(*) as count FROM users GROUP BY role")
        user_rows = cursor.fetchall()
        user_stats = {'admin': 0, 'teacher': 0, 'student': 0}
        for row in user_rows:
            user_stats[row['role']] = row['count']
        
        # Course counts
        cursor.execute("SELECT COUNT(*) as count FROM courses")
        total_courses = cursor.fetchone()['count']
        
        # Subject counts
        cursor.execute("SELECT COUNT(*) as count FROM subjects")
        total_subjects = cursor.fetchone()['count']
        
        # Section counts
        cursor.execute("SELECT COUNT(*) as count FROM sections")
        total_sections = cursor.fetchone()['count']
        
        # Enrollment counts
        cursor.execute("SELECT COUNT(*) as count FROM enrollments WHERE status = 'approved'")
        total_enrollments = cursor.fetchone()['count']
        
        # Pending enrollments
        cursor.execute("SELECT COUNT(*) as count FROM enrollments WHERE status = 'pending'")
        pending_enrollments = cursor.fetchone()['count']
        
        # Teacher assignments
        cursor.execute("SELECT COUNT(*) as count FROM teacher_assignments")
        total_assignments = cursor.fetchone()['count']
        
        cursor.close()
        
        return jsonify({
            'users': user_stats,
            'total_users': sum(user_stats.values()),
            'total_courses': total_courses,
            'total_subjects': total_subjects,
            'total_sections': total_sections,
            'total_enrollments': total_enrollments,
            'pending_enrollments': pending_enrollments,
            'total_assignments': total_assignments
        }), 200
        
    except Exception as e:
        print(f"Error getting stats: {e}")
        return jsonify({'error': str(e)}), 500


@admin_stats_bp.route('/classes', methods=['GET'], strict_slashes=False)
@jwt_required()
@admin_required
def get_class_stats():
    """Get class statistics"""
    try:
        cursor = mysql.connection.cursor()
        
        cursor.execute("""
            SELECT 
                c.id,
                c.name,
                c.code,
                COUNT(DISTINCT s.id) as sections,
                COUNT(DISTINCT sub.id) as subjects,
                COUNT(DISTINCT e.id) as enrollments
            FROM courses c
            LEFT JOIN subjects sub ON c.id = sub.course_id
            LEFT JOIN sections s ON sub.id = s.subject_id
            LEFT JOIN enrollments e ON s.id = e.section_id AND e.status = 'approved'
            GROUP BY c.id
            ORDER BY c.name
        """)
        
        class_stats = cursor.fetchall()
        cursor.close()
        
        return jsonify({
            'classes': class_stats
        }), 200
        
    except Exception as e:
        print(f"Error getting class stats: {e}")
        return jsonify({'error': str(e)}), 500