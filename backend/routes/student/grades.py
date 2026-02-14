from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from utils.database import mysql
from utils.decorators import student_required

student_grades_bp = Blueprint('student_grades', __name__)

@student_grades_bp.route('/recent', methods=['GET'], strict_slashes=False)
@jwt_required()
@student_required
def get_recent_grades():
    """Get recent grades for the student"""
    try:
        student_id = get_jwt_identity()
        
        cursor = mysql.connection.cursor()
        cursor.execute("""
            SELECT 
                s.id as submission_id,
                s.grade,
                s.feedback,
                s.graded_at,
                a.id as assignment_id,
                a.title as assignment_title,
                a.points_possible,
                sub.id as subject_id,
                sub.code as subject_code,
                sub.name as subject_name
            FROM submissions s
            JOIN assignments a ON s.assignment_id = a.id
            JOIN sections sec ON a.section_id = sec.id
            JOIN subjects sub ON sec.subject_id = sub.id
            WHERE s.student_id = %s AND s.status = 'graded'
            ORDER BY s.graded_at DESC
            LIMIT 5
        """, (student_id,))
        
        grades = cursor.fetchall()
        cursor.close()
        
        return jsonify({'grades': grades}), 200
        
    except Exception as e:
        print(f"Error getting recent grades: {e}")
        return jsonify({'error': str(e)}), 500