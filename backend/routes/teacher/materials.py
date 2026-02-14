from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from utils.database import mysql
from utils.decorators import teacher_required
from utils.file_handler import save_file, delete_file
import os

teacher_materials_bp = Blueprint('teacher_materials', __name__)

@teacher_materials_bp.route('/section/<int:section_id>', methods=['GET'])
@jwt_required()
@teacher_required
def get_section_materials(section_id):
    """Get all materials for a section"""
    try:
        teacher_id = get_jwt_identity()
        
        # Verify teacher is assigned
        cursor = mysql.connection.cursor()
        cursor.execute("""
            SELECT ta.id FROM teacher_assignments ta
            WHERE ta.teacher_id = %s AND ta.section_id = %s
        """, (teacher_id, section_id))
        
        if not cursor.fetchone():
            cursor.close()
            return jsonify({'error': 'You are not assigned to this section'}), 403
        
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
        
        return jsonify({
            'section_id': section_id,
            'total': len(materials),
            'materials': materials
        }), 200
        
    except Exception as e:
        print(f"Error getting materials: {e}")
        return jsonify({'error': str(e)}), 500


@teacher_materials_bp.route('/', methods=['POST'])
@jwt_required()
@teacher_required
def upload_material():
    """Upload material for a section"""
    try:
        teacher_id = get_jwt_identity()
        
        section_id = request.form.get('section_id')
        title = request.form.get('title')
        description = request.form.get('description', '')
        material_type = request.form.get('type', 'document')
        week = request.form.get('week')
        topic = request.form.get('topic')
        
        if not all([section_id, title]):
            return jsonify({'error': 'Section ID and title are required'}), 400
        
        # Verify teacher is assigned
        cursor = mysql.connection.cursor()
        cursor.execute("""
            SELECT ta.id FROM teacher_assignments ta
            WHERE ta.teacher_id = %s AND ta.section_id = %s
        """, (teacher_id, section_id))
        
        if not cursor.fetchone():
            cursor.close()
            return jsonify({'error': 'You are not assigned to this section'}), 403
        
        # Handle file upload
        file = request.files.get('file')
        url = request.form.get('url')
        
        if not file and not url:
            cursor.close()
            return jsonify({'error': 'Either file or URL is required'}), 400
        
        file_path = None
        if file and file.filename:
            file_info = save_file(file, subfolder=f"materials/{section_id}")
            if file_info:
                file_path = file_info['file_path']
        
        # Insert material
        cursor.execute("""
            INSERT INTO materials (
                title, description, type, url, file_path,
                section_id, uploaded_by, week, topic
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            title, description, material_type, url, file_path,
            section_id, teacher_id, week, topic
        ))
        
        mysql.connection.commit()
        material_id = cursor.lastrowid
        cursor.close()
        
        return jsonify({
            'message': 'Material uploaded successfully',
            'material_id': material_id
        }), 201
        
    except Exception as e:
        print(f"Error uploading material: {e}")
        return jsonify({'error': str(e)}), 500


@teacher_materials_bp.route('/<int:material_id>', methods=['DELETE'])
@jwt_required()
@teacher_required
def delete_material(material_id):
    """Delete a material"""
    try:
        teacher_id = get_jwt_identity()
        
        cursor = mysql.connection.cursor()
        
        # Verify teacher owns the material
        cursor.execute("""
            SELECT m.* FROM materials m
            WHERE m.id = %s AND m.uploaded_by = %s
        """, (material_id, teacher_id))
        
        material = cursor.fetchone()
        
        if not material:
            cursor.close()
            return jsonify({'error': 'Material not found or unauthorized'}), 404
        
        # Delete file if exists
        if material['file_path']:
            delete_file(material['file_path'])
        
        cursor.execute("DELETE FROM materials WHERE id = %s", (material_id,))
        mysql.connection.commit()
        cursor.close()
        
        return jsonify({'message': 'Material deleted successfully'}), 200
        
    except Exception as e:
        print(f"Error deleting material: {e}")
        return jsonify({'error': str(e)}), 500