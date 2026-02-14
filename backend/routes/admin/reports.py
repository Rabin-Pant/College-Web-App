from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from utils.database import mysql
from utils.decorators import admin_required
from datetime import datetime

admin_reports_bp = Blueprint('admin_reports', __name__)

@admin_reports_bp.route('/classes', methods=['GET'], strict_slashes=False)
@jwt_required()
@admin_required
def get_class_report():
    """Generate class report"""
    try:
        cursor = mysql.connection.cursor()
        
        cursor.execute("""
            SELECT 
                c.id,
                c.name as course_name,
                c.code as course_code,
                COUNT(DISTINCT sub.id) as total_subjects,
                COUNT(DISTINCT s.id) as total_sections,
                COUNT(DISTINCT e.id) as total_enrollments,
                COUNT(DISTINCT ta.teacher_id) as total_teachers
            FROM courses c
            LEFT JOIN subjects sub ON c.id = sub.course_id
            LEFT JOIN sections s ON sub.id = s.subject_id
            LEFT JOIN enrollments e ON s.id = e.section_id AND e.status = 'approved'
            LEFT JOIN teacher_assignments ta ON s.id = ta.section_id
            GROUP BY c.id
            ORDER BY c.name
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


@admin_reports_bp.route('/users', methods=['GET'], strict_slashes=False)
@jwt_required()
@admin_required
def get_user_report():
    """Generate user report"""
    try:
        cursor = mysql.connection.cursor()
        
        # Users by role
        cursor.execute("""
            SELECT 
                role,
                COUNT(*) as count,
                SUM(CASE WHEN email_verified = TRUE THEN 1 ELSE 0 END) as verified,
                DATE_FORMAT(MIN(created_at), '%Y-%m-%d') as earliest_join,
                DATE_FORMAT(MAX(created_at), '%Y-%m-%d') as latest_join
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


@admin_reports_bp.route('/enrollments', methods=['GET'], strict_slashes=False)
@jwt_required()
@admin_required
def get_enrollment_report():
    """Generate enrollment report"""
    try:
        cursor = mysql.connection.cursor()
        
        cursor.execute("""
            SELECT 
                c.name as course_name,
                sub.name as subject_name,
                s.name as section_name,
                s.academic_year,
                s.semester,
                COUNT(e.id) as enrolled_count,
                s.capacity
            FROM sections s
            JOIN subjects sub ON s.subject_id = sub.id
            JOIN courses c ON sub.course_id = c.id
            LEFT JOIN enrollments e ON s.id = e.section_id AND e.status = 'approved'
            GROUP BY s.id
            ORDER BY c.name, sub.name, s.name
        """)
        
        enrollments = cursor.fetchall()
        cursor.close()
        
        return jsonify({
            'generated_at': datetime.now().isoformat(),
            'total_sections': len(enrollments),
            'enrollments': enrollments
        }), 200
        
    except Exception as e:
        print(f"Error generating enrollment report: {e}")
        return jsonify({'error': str(e)}), 500