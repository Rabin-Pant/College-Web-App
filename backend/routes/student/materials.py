from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from utils.database import mysql
from utils.decorators import student_required

student_materials_bp = Blueprint('student_materials', __name__)

@student_materials_bp.route('/section/<int:section_id>', methods=['GET'], strict_slashes=False)
@jwt_required()
@student_required
def get_section_materials(section_id):
    """Get all materials for a section"""
    try:
        student_id = get_jwt_identity()
        
        # Verify student is enrolled in this section
        cursor = mysql.connection.cursor()
        cursor.execute("""
            SELECT id FROM enrollments 
            WHERE student_id = %s AND section_id = %s AND status = 'approved'
        """, (student_id, section_id))
        
        if not cursor.fetchone():
            cursor.close()
            return jsonify({'error': 'You are not enrolled in this section'}), 403
        
        # Get materials
        cursor.execute("""
            SELECT 
                m.*,
                u.name as uploaded_by_name
            FROM materials m
            JOIN users u ON m.uploaded_by = u.id
            WHERE m.section_id = %s
            ORDER BY m.created_at DESC
        """, (section_id,))
        
        materials = cursor.fetchall()
        cursor.close()
        
        return jsonify({'materials': materials}), 200
        
    except Exception as e:
        print(f"Error getting materials: {e}")
        return jsonify({'error': str(e)}), 500