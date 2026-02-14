from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from utils.database import mysql
from utils.decorators import role_required
from datetime import datetime, timedelta

student_bp = Blueprint('student', __name__)

@student_bp.route('/dashboard', methods=['GET'])
@jwt_required()
@role_required(['student'])
def get_dashboard():
    """Get student dashboard"""
    try:
        user_id = get_jwt_identity()
        
        cursor = mysql.connection.cursor()
        
        # Get student profile
        cursor.execute("SELECT id FROM student_profiles WHERE user_id = %s", (user_id,))
        student = cursor.fetchone()
        
        if not student:
            cursor.close()
            return jsonify({'error': 'Student profile not found'}), 404
        
        # Get enrolled classes count
        cursor.execute("""
            SELECT COUNT(*) as count FROM class_enrollments
            WHERE student_id = %s AND status = 'approved'
        """, (student['id'],))
        enrolled_classes = cursor.fetchone()['count']
        
        # Get upcoming assignments (next 7 days)
        cursor.execute("""
            SELECT 
                a.id,
                a.title,
                a.due_date,
                a.points_possible,
                c.id as class_id,
                c.name as class_name,
                c.course_code,
                (SELECT status FROM submissions 
                 WHERE assignment_id = a.id AND student_id = %s) as submission_status
            FROM assignments a
            JOIN classes c ON a.class_id = c.id
            JOIN class_enrollments ce ON c.id = ce.class_id
            WHERE ce.student_id = %s 
            AND ce.status = 'approved'
            AND a.is_published = TRUE
            AND a.due_date BETWEEN NOW() AND DATE_ADD(NOW(), INTERVAL 7 DAY)
            ORDER BY a.due_date ASC
        """, (user_id, student['id']))
        
        upcoming = cursor.fetchall()
        
        # Get recent grades
        cursor.execute("""
            SELECT 
                s.grade,
                s.feedback,
                s.graded_at,
                a.title as assignment_title,
                a.points_possible,
                c.name as class_name
            FROM submissions s
            JOIN assignments a ON s.assignment_id = a.id
            JOIN classes c ON a.class_id = c.id
            WHERE s.student_id = %s 
            AND s.status = 'graded'
            ORDER BY s.graded_at DESC
            LIMIT 5
        """, (user_id,))
        
        recent_grades = cursor.fetchall()
        
        # Get recent announcements
        cursor.execute("""
            SELECT 
                an.title,
                an.content,
                an.created_at,
                u.name as teacher_name,
                c.name as class_name
            FROM announcements an
            JOIN classes c ON an.class_id = c.id
            JOIN class_enrollments ce ON c.id = ce.class_id
            JOIN teacher_profiles tp ON c.teacher_id = tp.id
            JOIN users u ON tp.user_id = u.id
            WHERE ce.student_id = %s AND ce.status = 'approved'
            ORDER BY an.created_at DESC
            LIMIT 5
        """, (student['id'],))
        
        announcements = cursor.fetchall()
        
        cursor.close()
        
        return jsonify({
            'stats': {
                'enrolled_classes': enrolled_classes,
                'upcoming_assignments': len(upcoming)
            },
            'upcoming_assignments': upcoming,
            'recent_grades': recent_grades,
            'recent_announcements': announcements
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@student_bp.route('/grades', methods=['GET'])
@jwt_required()
@role_required(['student'])
def get_all_grades():
    """Get all grades for current student"""
    try:
        user_id = get_jwt_identity()
        
        cursor = mysql.connection.cursor()
        
        cursor.execute("""
            SELECT 
                s.grade,
                s.feedback,
                s.submitted_at,
                s.graded_at,
                a.id as assignment_id,
                a.title as assignment_title,
                a.points_possible,
                a.due_date,
                c.id as class_id,
                c.name as class_name,
                c.course_code
            FROM submissions s
            JOIN assignments a ON s.assignment_id = a.id
            JOIN classes c ON a.class_id = c.id
            WHERE s.student_id = %s 
            AND s.status = 'graded'
            ORDER BY s.graded_at DESC
        """, (user_id,))
        
        grades = cursor.fetchall()
        cursor.close()
        
        # Calculate GPA/overall average
        total_points = 0
        earned_points = 0
        
        for grade in grades:
            if grade['grade']:
                earned_points += grade['grade']
                total_points += grade['points_possible']
        
        overall_grade = (earned_points / total_points * 100) if total_points > 0 else 0
        
        return jsonify({
            'overall_grade': round(overall_grade, 2),
            'total_assignments': len(grades),
            'earned_points': earned_points,
            'total_points': total_points,
            'grades': grades
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@student_bp.route('/calendar', methods=['GET'])
@jwt_required()
@role_required(['student'])
def get_calendar():
    """Get calendar with all deadlines"""
    try:
        user_id = get_jwt_identity()
        
        cursor = mysql.connection.cursor()
        
        # Get student profile
        cursor.execute("SELECT id FROM student_profiles WHERE user_id = %s", (user_id,))
        student = cursor.fetchone()
        
        # Get all assignments from enrolled classes
        cursor.execute("""
            SELECT 
                a.id,
                a.title,
                a.due_date,
                'assignment' as event_type,
                c.name as class_name,
                c.course_code
            FROM assignments a
            JOIN classes c ON a.class_id = c.id
            JOIN class_enrollments ce ON c.id = ce.class_id
            WHERE ce.student_id = %s 
            AND ce.status = 'approved'
            AND a.is_published = TRUE
            AND a.due_date >= DATE_SUB(NOW(), INTERVAL 30 DAY)
            
            UNION
            
            SELECT 
                an.id,
                an.title,
                an.created_at as due_date,
                'announcement' as event_type,
                c.name as class_name,
                c.course_code
            FROM announcements an
            JOIN classes c ON an.class_id = c.id
            JOIN class_enrollments ce ON c.id = ce.class_id
            WHERE ce.student_id = %s 
            AND ce.status = 'approved'
            AND an.created_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)
            
            ORDER BY due_date ASC
        """, (student['id'], student['id']))
        
        events = cursor.fetchall()
        cursor.close()
        
        return jsonify({'events': events}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500