from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from utils.database import mysql
from utils.decorators import teacher_required

teacher_enrollments_bp = Blueprint('teacher_enrollments', __name__)

# ============ GET PENDING ENROLLMENTS ============

@teacher_enrollments_bp.route('/pending', methods=['GET'], strict_slashes=False)
@jwt_required()
@teacher_required
def get_pending_enrollments():
    """Get all pending enrollment requests for the teacher's sections"""
    try:
        teacher_id = get_jwt_identity()
        
        cursor = mysql.connection.cursor()
        cursor.execute("""
            SELECT 
                e.id as enrollment_id,
                e.enrollment_date,
                u.id as student_id,
                u.name as student_name,
                u.email as student_email,
                u.profile_pic,
                sp.student_id as student_number,
                sp.major,
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
            JOIN teacher_assignments ta ON s.id = ta.section_id
            JOIN users u ON e.student_id = u.id
            JOIN student_profiles sp ON u.id = sp.user_id
            WHERE ta.teacher_id = %s AND e.status = 'pending'
            ORDER BY e.enrollment_date
        """, (teacher_id,))
        
        pending = cursor.fetchall()
        cursor.close()
        
        return jsonify({
            'total': len(pending),
            'enrollments': pending
        }), 200
        
    except Exception as e:
        print(f"Error getting pending enrollments: {e}")
        return jsonify({'error': str(e)}), 500


# ============ APPROVE ENROLLMENT ============

@teacher_enrollments_bp.route('/<int:enrollment_id>/approve', methods=['POST'], strict_slashes=False)
@jwt_required()
@teacher_required
def approve_enrollment(enrollment_id):
    """Approve a pending enrollment request"""
    try:
        teacher_id = get_jwt_identity()
        
        cursor = mysql.connection.cursor()
        
        # Verify teacher owns the section and get details
        cursor.execute("""
            SELECT 
                e.*,
                s.capacity,
                s.enrolled_count,
                s.id as section_id
            FROM enrollments e
            JOIN sections s ON e.section_id = s.id
            JOIN teacher_assignments ta ON s.id = ta.section_id
            WHERE e.id = %s AND ta.teacher_id = %s
        """, (enrollment_id, teacher_id))
        
        enrollment = cursor.fetchone()
        
        if not enrollment:
            cursor.close()
            return jsonify({'error': 'Enrollment not found or unauthorized'}), 404
        
        if enrollment['status'] != 'pending':
            cursor.close()
            return jsonify({'error': 'Enrollment is not pending'}), 400
        
        if enrollment['enrolled_count'] >= enrollment['capacity']:
            cursor.close()
            return jsonify({'error': 'Section is full'}), 400
        
        # Approve enrollment
        cursor.execute("""
            UPDATE enrollments 
            SET status = 'approved', approved_by = %s, approved_date = CURDATE()
            WHERE id = %s
        """, (teacher_id, enrollment_id))
        
        # Update section enrolled count
        cursor.execute("""
            UPDATE sections 
            SET enrolled_count = enrolled_count + 1 
            WHERE id = %s
        """, (enrollment['section_id'],))
        
        mysql.connection.commit()
        cursor.close()
        
        # TODO: Send notification to student
        
        return jsonify({'message': 'Enrollment approved successfully'}), 200
        
    except Exception as e:
        print(f"Error approving enrollment: {e}")
        return jsonify({'error': str(e)}), 500


# ============ REJECT ENROLLMENT ============

@teacher_enrollments_bp.route('/<int:enrollment_id>/reject', methods=['POST'], strict_slashes=False)
@jwt_required()
@teacher_required
def reject_enrollment(enrollment_id):
    """Reject a pending enrollment request"""
    try:
        teacher_id = get_jwt_identity()
        
        cursor = mysql.connection.cursor()
        
        # Verify teacher owns the section
        cursor.execute("""
            SELECT e.* FROM enrollments e
            JOIN sections s ON e.section_id = s.id
            JOIN teacher_assignments ta ON s.id = ta.section_id
            WHERE e.id = %s AND ta.teacher_id = %s
        """, (enrollment_id, teacher_id))
        
        enrollment = cursor.fetchone()
        
        if not enrollment:
            cursor.close()
            return jsonify({'error': 'Enrollment not found or unauthorized'}), 404
        
        if enrollment['status'] != 'pending':
            cursor.close()
            return jsonify({'error': 'Enrollment is not pending'}), 400
        
        # Reject enrollment
        cursor.execute("""
            UPDATE enrollments 
            SET status = 'rejected', approved_by = %s, approved_date = CURDATE()
            WHERE id = %s
        """, (teacher_id, enrollment_id))
        
        mysql.connection.commit()
        cursor.close()
        
        # TODO: Send notification to student
        
        return jsonify({'message': 'Enrollment rejected'}), 200
        
    except Exception as e:
        print(f"Error rejecting enrollment: {e}")
        return jsonify({'error': str(e)}), 500


# ============ GET ENROLLMENTS BY SECTION ============

@teacher_enrollments_bp.route('/section/<int:section_id>', methods=['GET'], strict_slashes=False)
@jwt_required()
@teacher_required
def get_section_enrollments(section_id):
    """Get all enrollments for a specific section"""
    try:
        teacher_id = get_jwt_identity()
        
        # Verify teacher owns the section
        cursor = mysql.connection.cursor()
        cursor.execute("""
            SELECT ta.id FROM teacher_assignments ta
            WHERE ta.teacher_id = %s AND ta.section_id = %s
        """, (teacher_id, section_id))
        
        if not cursor.fetchone():
            cursor.close()
            return jsonify({'error': 'You are not assigned to this section'}), 403
        
        # Get enrollments
        cursor.execute("""
            SELECT 
                e.id as enrollment_id,
                e.status,
                e.enrollment_date,
                e.approved_date,
                u.id as student_id,
                u.name as student_name,
                u.email as student_email,
                u.profile_pic,
                sp.student_id as student_number,
                sp.major
            FROM enrollments e
            JOIN users u ON e.student_id = u.id
            JOIN student_profiles sp ON u.id = sp.user_id
            WHERE e.section_id = %s
            ORDER BY e.enrollment_date DESC
        """, (section_id,))
        
        enrollments = cursor.fetchall()
        cursor.close()
        
        return jsonify({
            'section_id': section_id,
            'total': len(enrollments),
            'enrollments': enrollments
        }), 200
        
    except Exception as e:
        print(f"Error getting section enrollments: {e}")
        return jsonify({'error': str(e)}), 500


# ============ BULK APPROVE ENROLLMENTS ============

@teacher_enrollments_bp.route('/bulk-approve', methods=['POST'], strict_slashes=False)
@jwt_required()
@teacher_required
def bulk_approve_enrollments():
    """Approve multiple enrollment requests at once"""
    try:
        teacher_id = get_jwt_identity()
        data = request.get_json()
        enrollment_ids = data.get('enrollment_ids', [])
        
        if not enrollment_ids:
            return jsonify({'error': 'No enrollment IDs provided'}), 400
        
        cursor = mysql.connection.cursor()
        success_count = 0
        failed_ids = []
        
        for enrollment_id in enrollment_ids:
            try:
                # Verify teacher owns the section
                cursor.execute("""
                    SELECT 
                        e.*,
                        s.capacity,
                        s.enrolled_count,
                        s.id as section_id
                    FROM enrollments e
                    JOIN sections s ON e.section_id = s.id
                    JOIN teacher_assignments ta ON s.id = ta.section_id
                    WHERE e.id = %s AND ta.teacher_id = %s
                """, (enrollment_id, teacher_id))
                
                enrollment = cursor.fetchone()
                
                if not enrollment or enrollment['status'] != 'pending' or enrollment['enrolled_count'] >= enrollment['capacity']:
                    failed_ids.append(enrollment_id)
                    continue
                
                cursor.execute("""
                    UPDATE enrollments 
                    SET status = 'approved', approved_by = %s, approved_date = CURDATE()
                    WHERE id = %s
                """, (teacher_id, enrollment_id))
                
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
        print(f"Error bulk approving enrollments: {e}")
        return jsonify({'error': str(e)}), 500