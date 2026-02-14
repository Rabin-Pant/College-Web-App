from flask import Blueprint, request, jsonify, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from utils.database import mysql
from utils.decorators import role_required
from utils.file_handler import save_file, delete_file
import os

material_bp = Blueprint('materials', __name__)

@material_bp.route('/', methods=['POST'])
@jwt_required()
@role_required(['teacher'])
def upload_material():
    """Upload study material"""
    try:
        user_id = get_jwt_identity()
        
        class_id = request.form.get('class_id')
        title = request.form.get('title')
        description = request.form.get('description', '')
        material_type = request.form.get('type', 'document')
        week = request.form.get('week')
        topic = request.form.get('topic')
        
        if not all([class_id, title]):
            return jsonify({'error': 'Class ID and title are required'}), 400
        
        # Verify teacher owns the class
        cursor = mysql.connection.cursor()
        cursor.execute("""
            SELECT c.* FROM classes c
            JOIN teacher_profiles tp ON c.teacher_id = tp.id
            WHERE c.id = %s AND tp.user_id = %s
        """, (class_id, user_id))
        
        if not cursor.fetchone():
            cursor.close()
            return jsonify({'error': 'Class not found or unauthorized'}), 403
        
        # Handle file upload
        file = request.files.get('file')
        url = request.form.get('url')
        
        if not file and not url:
            cursor.close()
            return jsonify({'error': 'Either file or URL is required'}), 400
        
        file_path = None
        if file and file.filename:
            file_path = save_file(file, f"materials/{class_id}")
        
        # Get teacher profile id
        cursor.execute("SELECT id FROM teacher_profiles WHERE user_id = %s", (user_id,))
        teacher = cursor.fetchone()
        
        # Insert material
        cursor.execute("""
            INSERT INTO materials (
                title, description, type, url, file_path,
                class_id, uploaded_by, week, topic
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            title, description, material_type, url, file_path,
            class_id, teacher['id'], week, topic
        ))
        
        mysql.connection.commit()
        material_id = cursor.lastrowid
        cursor.close()
        
        return jsonify({
            'message': 'Material uploaded successfully',
            'material_id': material_id
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@material_bp.route('/class/<int:class_id>', methods=['GET'])
@jwt_required()
def get_class_materials(class_id):
    """Get all materials for a class"""
    try:
        user_id = get_jwt_identity()
        
        cursor = mysql.connection.cursor()
        
        # Check access
        cursor.execute("SELECT role FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        
        has_access = False
        
        if user['role'] == 'teacher':
            cursor.execute("""
                SELECT c.* FROM classes c
                JOIN teacher_profiles tp ON c.teacher_id = tp.id
                WHERE c.id = %s AND tp.user_id = %s
            """, (class_id, user_id))
            has_access = cursor.fetchone() is not None
            
        elif user['role'] == 'student':
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
                has_access = enrollment and enrollment['status'] == 'approved'
        
        if not has_access:
            cursor.close()
            return jsonify({'error': 'Access denied'}), 403
        
        # Get materials
        cursor.execute("""
            SELECT 
                m.*,
                u.name as uploaded_by_name,
                (SELECT COUNT(*) FROM bookmarks b 
                 WHERE b.material_id = m.id AND b.user_id = %s) as is_bookmarked
            FROM materials m
            JOIN teacher_profiles tp ON m.uploaded_by = tp.id
            JOIN users u ON tp.user_id = u.id
            WHERE m.class_id = %s
            ORDER BY m.created_at DESC
        """, (user_id if user['role'] == 'student' else 0, class_id))
        
        materials = cursor.fetchall()
        cursor.close()
        
        return jsonify({'materials': materials}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@material_bp.route('/<int:material_id>/download', methods=['GET'])
@jwt_required()
def download_material(material_id):
    """Download material file"""
    try:
        user_id = get_jwt_identity()
        
        cursor = mysql.connection.cursor()
        
        # Get material info
        cursor.execute("""
            SELECT m.*, c.id as class_id FROM materials m
            JOIN classes c ON m.class_id = c.id
            WHERE m.id = %s
        """, (material_id,))
        
        material = cursor.fetchone()
        
        if not material:
            cursor.close()
            return jsonify({'error': 'Material not found'}), 404
        
        # Check access
        cursor.execute("SELECT role FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        
        has_access = False
        
        if user['role'] == 'teacher':
            cursor.execute("""
                SELECT c.* FROM classes c
                JOIN teacher_profiles tp ON c.teacher_id = tp.id
                WHERE c.id = %s AND tp.user_id = %s
            """, (material['class_id'], user_id))
            has_access = cursor.fetchone() is not None
            
        elif user['role'] == 'student':
            cursor.execute("""
                SELECT sp.id FROM student_profiles sp
                WHERE sp.user_id = %s
            """, (user_id,))
            student = cursor.fetchone()
            
            if student:
                cursor.execute("""
                    SELECT status FROM class_enrollments
                    WHERE class_id = %s AND student_id = %s
                """, (material['class_id'], student['id']))
                enrollment = cursor.fetchone()
                has_access = enrollment and enrollment['status'] == 'approved'
        
        cursor.close()
        
        if not has_access:
            return jsonify({'error': 'Access denied'}), 403
        
        if not material['file_path']:
            return jsonify({'error': 'No file available'}), 404
        
        file_path = os.path.join('uploads', material['file_path'])
        
        if not os.path.exists(file_path):
            return jsonify({'error': 'File not found'}), 404
        
        return send_file(
            file_path,
            as_attachment=True,
            download_name=os.path.basename(material['file_path'])
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@material_bp.route('/<int:material_id>/bookmark', methods=['POST'])
@jwt_required()
@role_required(['student'])
def bookmark_material(material_id):
    """Bookmark a material"""
    try:
        user_id = get_jwt_identity()
        
        cursor = mysql.connection.cursor()
        
        # Check if material exists
        cursor.execute("SELECT * FROM materials WHERE id = %s", (material_id,))
        material = cursor.fetchone()
        
        if not material:
            cursor.close()
            return jsonify({'error': 'Material not found'}), 404
        
        # Add bookmark
        try:
            cursor.execute("""
                INSERT INTO bookmarks (user_id, material_id)
                VALUES (%s, %s)
            """, (user_id, material_id))
            mysql.connection.commit()
            message = 'Material bookmarked'
        except:
            # Already bookmarked
            message = 'Already bookmarked'
        
        cursor.close()
        
        return jsonify({'message': message}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@material_bp.route('/<int:material_id>/bookmark', methods=['DELETE'])
@jwt_required()
@role_required(['student'])
def remove_bookmark(material_id):
    """Remove bookmark"""
    try:
        user_id = get_jwt_identity()
        
        cursor = mysql.connection.cursor()
        cursor.execute("""
            DELETE FROM bookmarks 
            WHERE user_id = %s AND material_id = %s
        """, (user_id, material_id))
        
        mysql.connection.commit()
        cursor.close()
        
        return jsonify({'message': 'Bookmark removed'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@material_bp.route('/bookmarks', methods=['GET'])
@jwt_required()
@role_required(['student'])
def get_bookmarks():
    """Get all bookmarked materials"""
    try:
        user_id = get_jwt_identity()
        
        cursor = mysql.connection.cursor()
        cursor.execute("""
            SELECT 
                m.*,
                c.name as class_name,
                c.course_code,
                u.name as uploaded_by_name
            FROM bookmarks b
            JOIN materials m ON b.material_id = m.id
            JOIN classes c ON m.class_id = c.id
            JOIN teacher_profiles tp ON m.uploaded_by = tp.id
            JOIN users u ON tp.user_id = u.id
            WHERE b.user_id = %s
            ORDER BY b.created_at DESC
        """, (user_id,))
        
        bookmarks = cursor.fetchall()
        cursor.close()
        
        return jsonify({'bookmarks': bookmarks}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@material_bp.route('/<int:material_id>', methods=['DELETE'])
@jwt_required()
@role_required(['teacher'])
def delete_material(material_id):
    """Delete a material"""
    try:
        user_id = get_jwt_identity()
        
        cursor = mysql.connection.cursor()
        
        # Verify teacher owns the material
        cursor.execute("""
            SELECT m.* FROM materials m
            JOIN teacher_profiles tp ON m.uploaded_by = tp.id
            WHERE m.id = %s AND tp.user_id = %s
        """, (material_id, user_id))
        
        material = cursor.fetchone()
        
        if not material:
            cursor.close()
            return jsonify({'error': 'Material not found or unauthorized'}), 404
        
        # Delete file if exists
        if material['file_path']:
            delete_file(material['file_path'])
        
        # Delete from database
        cursor.execute("DELETE FROM materials WHERE id = %s", (material_id,))
        mysql.connection.commit()
        cursor.close()
        
        return jsonify({'message': 'Material deleted successfully'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500