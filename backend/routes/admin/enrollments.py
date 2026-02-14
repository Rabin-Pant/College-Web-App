from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from utils.database import mysql
from utils.decorators import admin_required
from models.enrollment import Enrollment
from models.section import Section
from datetime import datetime

admin_enrollments_bp = Blueprint('admin_enrollments', __name__)

# ============ GET ALL ENROLLMENTS ============

@admin_enrollments_bp.route('/', methods=['GET'], strict_slashes=False)
@jwt_required()
@admin_required
def get_all_enrollments():
    """Get all enrollments with filters"""
    try:
        status = request.args.get('status')
        section_id = request.args.get('section_id', type=int)
        student_id = request.args.get('student_id', type=int)
        
        cursor = mysql.connection.cursor()
        
        # Debug print
        print(f"📡 Fetching enrollments with filters - status: {status}, section_id: {section_id}, student_id: {student_id}")
        
        query = """
            SELECT 
                e.id as enrollment_id,
                e.student_id,
                e.section_id,
                e.status,
                e.enrollment_date,
                e.approved_by,
                e.approved_date,
                e.grade_final,
                e.created_at,
                e.updated_at,
                u.name as student_name,
                u.email as student_email,
                u.profile_pic,
                sp.student_id as student_number,
                sp.major,
                sp.enrollment_year,
                s.name as section_name,
                s.academic_year,
                s.semester,
                sub.id as subject_id,
                sub.code as subject_code,
                sub.name as subject_name,
                sub.credits,
                c.id as course_id,
                c.name as course_name,
                c.code as course_code,
                t.id as teacher_id,
                t.name as teacher_name,
                t.email as teacher_email
            FROM enrollments e
            JOIN users u ON e.student_id = u.id
            JOIN student_profiles sp ON u.id = sp.user_id
            JOIN sections s ON e.section_id = s.id
            JOIN subjects sub ON s.subject_id = sub.id
            JOIN courses c ON sub.course_id = c.id
            LEFT JOIN teacher_assignments ta ON s.id = ta.section_id
            LEFT JOIN users t ON ta.teacher_id = t.id
            WHERE 1=1
        """
        params = []
        
        if status:
            query += " AND e.status = %s"
            params.append(status)
        if section_id:
            query += " AND e.section_id = %s"
            params.append(section_id)
        if student_id:
            query += " AND e.student_id = %s"
            params.append(student_id)
            
        query += " ORDER BY e.enrollment_date DESC"
        
        cursor.execute(query, params)
        enrollments = cursor.fetchall()
        cursor.close()
        
        return jsonify({
            'total': len(enrollments),
            'enrollments': enrollments
        }), 200
        
    except Exception as e:
        print(f"❌ Error getting enrollments: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


# ============ GET PENDING ENROLLMENTS ============

@admin_enrollments_bp.route('/pending', methods=['GET'], strict_slashes=False)
@jwt_required()
@admin_required
def get_pending_enrollments():
    """Get all pending enrollments"""
    try:
        cursor = mysql.connection.cursor()
        
        cursor.execute("""
            SELECT 
                e.id as enrollment_id,
                e.enrollment_date,
                u.id as student_id,
                u.name as student_name,
                u.email as student_email,
                sp.student_id as student_number,
                sp.major,
                s.id as section_id,
                s.name as section_name,
                sub.id as subject_id,
                sub.code as subject_code,
                sub.name as subject_name,
                c.name as course_name,
                t.id as teacher_id,
                t.name as teacher_name
            FROM enrollments e
            JOIN users u ON e.student_id = u.id
            JOIN student_profiles sp ON u.id = sp.user_id
            JOIN sections s ON e.section_id = s.id
            JOIN subjects sub ON s.subject_id = sub.id
            JOIN courses c ON sub.course_id = c.id
            LEFT JOIN teacher_assignments ta ON s.id = ta.section_id
            LEFT JOIN users t ON ta.teacher_id = t.id
            WHERE e.status = 'pending'
            ORDER BY e.enrollment_date
        """)
        
        pending = cursor.fetchall()
        cursor.close()
        
        return jsonify({
            'total': len(pending),
            'enrollments': pending
        }), 200
        
    except Exception as e:
        print(f"Error getting pending enrollments: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


# ============ APPROVE ENROLLMENT ============

@admin_enrollments_bp.route('/<int:enrollment_id>/approve', methods=['POST'], strict_slashes=False)
@jwt_required()
@admin_required
def approve_enrollment(enrollment_id):
    """Approve a pending enrollment"""
    try:
        admin_id = get_jwt_identity()
        
        cursor = mysql.connection.cursor()
        
        # Get enrollment details
        cursor.execute("""
            SELECT e.*, s.capacity, s.enrolled_count 
            FROM enrollments e
            JOIN sections s ON e.section_id = s.id
            WHERE e.id = %s
        """, (enrollment_id,))
        
        enrollment = cursor.fetchone()
        
        if not enrollment:
            cursor.close()
            return jsonify({'error': 'Enrollment not found'}), 404
        
        if enrollment['status'] != 'pending':
            cursor.close()
            return jsonify({'error': 'Enrollment is not pending'}), 400
        
        if enrollment['enrolled_count'] >= enrollment['capacity']:
            cursor.close()
            return jsonify({'error': 'Section is full'}), 400
        
        # Update enrollment status
        cursor.execute("""
            UPDATE enrollments 
            SET status = 'approved', approved_by = %s, approved_date = CURDATE()
            WHERE id = %s
        """, (admin_id, enrollment_id))
        
        # Increment section enrolled count
        cursor.execute("""
            UPDATE sections 
            SET enrolled_count = enrolled_count + 1 
            WHERE id = %s
        """, (enrollment['section_id'],))
        
        mysql.connection.commit()
        cursor.close()
        
        return jsonify({'message': 'Enrollment approved successfully'}), 200
        
    except Exception as e:
        print(f"Error approving enrollment: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


# ============ REJECT ENROLLMENT ============

@admin_enrollments_bp.route('/<int:enrollment_id>/reject', methods=['POST'], strict_slashes=False)
@jwt_required()
@admin_required
def reject_enrollment(enrollment_id):
    """Reject a pending enrollment"""
    try:
        admin_id = get_jwt_identity()
        
        cursor = mysql.connection.cursor()
        
        # Check if enrollment exists and is pending
        cursor.execute("""
            SELECT * FROM enrollments 
            WHERE id = %s AND status = 'pending'
        """, (enrollment_id,))
        
        if not cursor.fetchone():
            cursor.close()
            return jsonify({'error': 'Enrollment not found or not pending'}), 404
        
        # Update enrollment status
        cursor.execute("""
            UPDATE enrollments 
            SET status = 'rejected', approved_by = %s, approved_date = CURDATE()
            WHERE id = %s
        """, (admin_id, enrollment_id))
        
        mysql.connection.commit()
        cursor.close()
        
        return jsonify({'message': 'Enrollment rejected'}), 200
        
    except Exception as e:
        print(f"Error rejecting enrollment: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


# ============ BULK APPROVE ============

@admin_enrollments_bp.route('/bulk-approve', methods=['POST'], strict_slashes=False)
@jwt_required()
@admin_required
def bulk_approve():
    """Approve multiple enrollments at once"""
    try:
        admin_id = get_jwt_identity()
        data = request.get_json()
        enrollment_ids = data.get('enrollment_ids', [])
        
        if not enrollment_ids:
            return jsonify({'error': 'No enrollment IDs provided'}), 400
        
        cursor = mysql.connection.cursor()
        success_count = 0
        failed_ids = []
        
        for enrollment_id in enrollment_ids:
            try:
                # Get enrollment details
                cursor.execute("""
                    SELECT e.*, s.capacity, s.enrolled_count 
                    FROM enrollments e
                    JOIN sections s ON e.section_id = s.id
                    WHERE e.id = %s
                """, (enrollment_id,))
                
                enrollment = cursor.fetchone()
                
                if not enrollment or enrollment['status'] != 'pending' or enrollment['enrolled_count'] >= enrollment['capacity']:
                    failed_ids.append(enrollment_id)
                    continue
                
                cursor.execute("""
                    UPDATE enrollments 
                    SET status = 'approved', approved_by = %s, approved_date = CURDATE()
                    WHERE id = %s
                """, (admin_id, enrollment_id))
                
                cursor.execute("""
                    UPDATE sections 
                    SET enrolled_count = enrolled_count + 1 
                    WHERE id = %s
                """, (enrollment['section_id'],))
                
                success_count += 1
                
            except Exception:
                failed_ids.append(enrollment_id)
        
        mysql.connection.commit()
        cursor.close()
        
        return jsonify({
            'message': f'Approved {success_count} enrollments',
            'success_count': success_count,
            'failed_ids': failed_ids
        }), 200
        
    except Exception as e:
        print(f"Error bulk approving: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


# ============ DELETE ENROLLMENT ============

@admin_enrollments_bp.route('/<int:enrollment_id>', methods=['DELETE'], strict_slashes=False)
@jwt_required()
@admin_required
def delete_enrollment(enrollment_id):
    """Delete an enrollment"""
    try:
        cursor = mysql.connection.cursor()
        
        # Get section_id before deleting
        cursor.execute("SELECT section_id, status FROM enrollments WHERE id = %s", (enrollment_id,))
        enrollment = cursor.fetchone()
        
        if not enrollment:
            cursor.close()
            return jsonify({'error': 'Enrollment not found'}), 404
        
        # If it was approved, decrement section count
        if enrollment['status'] == 'approved':
            cursor.execute("""
                UPDATE sections 
                SET enrolled_count = enrolled_count - 1 
                WHERE id = %s AND enrolled_count > 0
            """, (enrollment['section_id'],))
        
        # Delete enrollment
        cursor.execute("DELETE FROM enrollments WHERE id = %s", (enrollment_id,))
        
        mysql.connection.commit()
        cursor.close()
        
        return jsonify({'message': 'Enrollment deleted successfully'}), 200
        
    except Exception as e:
        print(f"Error deleting enrollment: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


# ============ GET ENROLLMENT BY ID ============

@admin_enrollments_bp.route('/<int:enrollment_id>', methods=['GET'], strict_slashes=False)
@jwt_required()
@admin_required
def get_enrollment(enrollment_id):
    """Get a specific enrollment by ID"""
    try:
        cursor = mysql.connection.cursor()
        
        cursor.execute("""
            SELECT 
                e.*,
                u.name as student_name,
                u.email as student_email,
                sp.student_id as student_number,
                sp.major,
                s.name as section_name,
                sub.code as subject_code,
                sub.name as subject_name,
                c.name as course_name,
                c.code as course_code,
                t.name as teacher_name
            FROM enrollments e
            JOIN users u ON e.student_id = u.id
            JOIN student_profiles sp ON u.id = sp.user_id
            JOIN sections s ON e.section_id = s.id
            JOIN subjects sub ON s.subject_id = sub.id
            JOIN courses c ON sub.course_id = c.id
            LEFT JOIN teacher_assignments ta ON s.id = ta.section_id
            LEFT JOIN users t ON ta.teacher_id = t.id
            WHERE e.id = %s
        """, (enrollment_id,))
        
        enrollment = cursor.fetchone()
        cursor.close()
        
        if not enrollment:
            return jsonify({'error': 'Enrollment not found'}), 404
        
        return jsonify(enrollment), 200
        
    except Exception as e:
        print(f"Error getting enrollment: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500