from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from utils.database import mysql
from utils.decorators import student_required
from datetime import date

student_enrollments_bp = Blueprint('student_enrollments', __name__)

@student_enrollments_bp.route('/pending', methods=['GET'], strict_slashes=False)
@jwt_required()
@student_required
def get_pending_enrollments():
    """Get pending enrollment requests for the student"""
    try:
        student_id = get_jwt_identity()
        
        cursor = mysql.connection.cursor()
        cursor.execute("""
            SELECT 
                e.id as enrollment_id,
                e.enrollment_date,
                e.status,
                s.id as section_id,
                s.name as section_name,
                sub.id as subject_id,
                sub.code as subject_code,
                sub.name as subject_name,
                c.id as course_id,
                c.name as course_name,
                c.code as course_code
            FROM enrollments e
            JOIN sections s ON e.section_id = s.id
            JOIN subjects sub ON s.subject_id = sub.id
            JOIN courses c ON sub.course_id = c.id
            WHERE e.student_id = %s AND e.status = 'pending'
            ORDER BY e.enrollment_date DESC
        """, (student_id,))
        
        enrollments = cursor.fetchall()
        cursor.close()
        
        return jsonify({'enrollments': enrollments}), 200
        
    except Exception as e:
        print(f"Error getting pending enrollments: {e}")
        return jsonify({'error': str(e)}), 500


@student_enrollments_bp.route('/', methods=['POST'], strict_slashes=False)
@jwt_required()
@student_required
def request_enrollment():
    """Request enrollment in a section"""
    try:
        student_id = get_jwt_identity()
        data = request.get_json()
        
        if not data.get('section_id'):
            return jsonify({'error': 'Section ID is required'}), 400
        
        cursor = mysql.connection.cursor()
        
        # Check if section exists and has space
        cursor.execute("""
            SELECT s.* FROM sections s
            WHERE s.id = %s AND s.is_active = TRUE AND s.enrolled_count < s.capacity
        """, (data['section_id'],))
        
        section = cursor.fetchone()
        if not section:
            cursor.close()
            return jsonify({'error': 'Section not available'}), 400
        
        # Check if already enrolled or pending
        cursor.execute("""
            SELECT id, status FROM enrollments 
            WHERE student_id = %s AND section_id = %s
        """, (student_id, data['section_id']))
        
        existing = cursor.fetchone()
        if existing:
            cursor.close()
            return jsonify({'error': f'Already {existing["status"]}'}), 400
        
        # Create enrollment request
        cursor.execute("""
            INSERT INTO enrollments (student_id, section_id, status, enrollment_date)
            VALUES (%s, %s, 'pending', %s)
        """, (student_id, data['section_id'], date.today()))
        
        mysql.connection.commit()
        enrollment_id = cursor.lastrowid
        cursor.close()
        
        return jsonify({
            'message': 'Enrollment request submitted',
            'enrollment_id': enrollment_id
        }), 201
        
    except Exception as e:
        print(f"Error requesting enrollment: {e}")
        return jsonify({'error': str(e)}), 500