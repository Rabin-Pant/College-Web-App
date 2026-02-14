from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from utils.database import mysql
from utils.decorators import teacher_required
from datetime import date, datetime

teacher_attendance_bp = Blueprint('teacher_attendance', __name__)

# ============ GET ATTENDANCE FOR A SECTION ============

@teacher_attendance_bp.route('/section/<int:section_id>', methods=['GET'], strict_slashes=False)
@jwt_required()
@teacher_required
def get_attendance(section_id):
    """Get attendance for a section on a specific date"""
    try:
        teacher_id = get_jwt_identity()
        attendance_date = request.args.get('date')
        
        if not attendance_date:
            attendance_date = date.today().isoformat()
        
        # Verify teacher is assigned to this section
        cursor = mysql.connection.cursor()
        cursor.execute("""
            SELECT ta.id FROM teacher_assignments ta
            WHERE ta.teacher_id = %s AND ta.section_id = %s
        """, (teacher_id, section_id))
        
        if not cursor.fetchone():
            cursor.close()
            return jsonify({'error': 'You are not assigned to this section'}), 403
        
        # Get all enrolled students with their attendance for this date
        cursor.execute("""
            SELECT 
                u.id,
                u.name,
                u.email,
                u.profile_pic,
                sp.student_id,
                sp.major,
                COALESCE(a.status, 'absent') as attendance_status
            FROM enrollments e
            JOIN users u ON e.student_id = u.id
            JOIN student_profiles sp ON u.id = sp.user_id
            LEFT JOIN attendance a ON a.student_id = u.id 
                AND a.section_id = %s 
                AND a.date = %s
            WHERE e.section_id = %s AND e.status = 'approved'
            ORDER BY u.name
        """, (section_id, attendance_date, section_id))
        
        students = cursor.fetchall()
        
        # Get attendance summary for this section
        cursor.execute("""
            SELECT 
                COUNT(*) as total_classes,
                SUM(CASE WHEN status = 'present' THEN 1 ELSE 0 END) as present,
                SUM(CASE WHEN status = 'absent' THEN 1 ELSE 0 END) as absent,
                SUM(CASE WHEN status = 'late' THEN 1 ELSE 0 END) as late,
                SUM(CASE WHEN status = 'excused' THEN 1 ELSE 0 END) as excused
            FROM attendance
            WHERE section_id = %s
        """, (section_id,))
        
        summary = cursor.fetchone()
        cursor.close()
        
        return jsonify({
            'section_id': section_id,
            'date': attendance_date,
            'students': students,
            'total_students': len(students),
            'summary': summary
        }), 200
        
    except Exception as e:
        print(f"Error getting attendance: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


# ============ MARK ATTENDANCE FOR A SINGLE STUDENT ============

@teacher_attendance_bp.route('/', methods=['POST'], strict_slashes=False)
@jwt_required()
@teacher_required
def mark_attendance():
    """Mark attendance for a student"""
    try:
        teacher_id = get_jwt_identity()
        data = request.get_json()
        
        required_fields = ['section_id', 'student_id', 'status']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        attendance_date = data.get('date', date.today().isoformat())
        
        # Verify teacher is assigned to this section
        cursor = mysql.connection.cursor()
        cursor.execute("""
            SELECT ta.id FROM teacher_assignments ta
            WHERE ta.teacher_id = %s AND ta.section_id = %s
        """, (teacher_id, data['section_id']))
        
        if not cursor.fetchone():
            cursor.close()
            return jsonify({'error': 'You are not assigned to this section'}), 403
        
        # Check if student is enrolled
        cursor.execute("""
            SELECT id FROM enrollments 
            WHERE section_id = %s AND student_id = %s AND status = 'approved'
        """, (data['section_id'], data['student_id']))
        
        if not cursor.fetchone():
            cursor.close()
            return jsonify({'error': 'Student is not enrolled in this section'}), 400
        
        # Insert or update attendance
        cursor.execute("""
            INSERT INTO attendance (section_id, student_id, date, status, marked_by)
            VALUES (%s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE 
                status = VALUES(status),
                marked_by = VALUES(marked_by)
        """, (
            data['section_id'], data['student_id'], attendance_date, data['status'], teacher_id
        ))
        
        mysql.connection.commit()
        affected = cursor.rowcount
        cursor.close()
        
        return jsonify({
            'message': 'Attendance marked successfully',
            'affected': affected
        }), 200
        
    except Exception as e:
        print(f"Error marking attendance: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


# ============ MARK BULK ATTENDANCE ============

@teacher_attendance_bp.route('/bulk', methods=['POST'], strict_slashes=False)
@jwt_required()
@teacher_required
def mark_bulk_attendance():
    """Mark attendance for multiple students"""
    try:
        teacher_id = get_jwt_identity()
        data = request.get_json()
        
        required_fields = ['section_id', 'attendance']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        attendance_date = data.get('date')
        if not attendance_date:
            attendance_date = date.today().isoformat()
            
        section_id = data['section_id']
        attendance_list = data['attendance']
        
        # Verify teacher is assigned to this section
        cursor = mysql.connection.cursor()
        cursor.execute("""
            SELECT ta.id FROM teacher_assignments ta
            WHERE ta.teacher_id = %s AND ta.section_id = %s
        """, (teacher_id, section_id))
        
        if not cursor.fetchone():
            cursor.close()
            return jsonify({'error': 'You are not assigned to this section'}), 403
        
        success_count = 0
        errors = []
        
        for item in attendance_list:
            try:
                student_id = item.get('student_id')
                status = item.get('status')
                
                if not student_id or not status:
                    errors.append(f"Missing student_id or status")
                    continue
                
                # Check if student is enrolled
                cursor.execute("""
                    SELECT id FROM enrollments 
                    WHERE section_id = %s AND student_id = %s AND status = 'approved'
                """, (section_id, student_id))
                
                if not cursor.fetchone():
                    errors.append(f"Student {student_id} not enrolled")
                    continue
                
                # Insert or update attendance
                cursor.execute("""
                    INSERT INTO attendance (section_id, student_id, date, status, marked_by)
                    VALUES (%s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE 
                        status = VALUES(status),
                        marked_by = VALUES(marked_by)
                """, (
                    section_id, student_id, attendance_date, status, teacher_id
                ))
                
                success_count += 1
                
            except Exception as e:
                errors.append(str(e))
        
        mysql.connection.commit()
        cursor.close()
        
        return jsonify({
            'message': f'Marked attendance for {success_count} students',
            'success_count': success_count,
            'errors': errors
        }), 200
        
    except Exception as e:
        print(f"Error marking bulk attendance: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


# ============ GET ATTENDANCE SUMMARY ============

@teacher_attendance_bp.route('/summary/<int:section_id>', methods=['GET'], strict_slashes=False)
@jwt_required()
@teacher_required
def get_attendance_summary(section_id):
    """Get attendance summary for a section"""
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
        
        # Get daily attendance summary
        cursor.execute("""
            SELECT 
                date,
                COUNT(*) as total,
                SUM(CASE WHEN status = 'present' THEN 1 ELSE 0 END) as present,
                SUM(CASE WHEN status = 'absent' THEN 1 ELSE 0 END) as absent,
                SUM(CASE WHEN status = 'late' THEN 1 ELSE 0 END) as late,
                SUM(CASE WHEN status = 'excused' THEN 1 ELSE 0 END) as excused
            FROM attendance
            WHERE section_id = %s
            GROUP BY date
            ORDER BY date DESC
            LIMIT 30
        """, (section_id,))
        
        daily = cursor.fetchall()
        
        # Get student-wise summary
        cursor.execute("""
            SELECT 
                u.id,
                u.name,
                u.email,
                sp.student_id,
                COUNT(a.id) as total_classes,
                SUM(CASE WHEN a.status = 'present' THEN 1 ELSE 0 END) as present,
                SUM(CASE WHEN a.status = 'absent' THEN 1 ELSE 0 END) as absent,
                SUM(CASE WHEN a.status = 'late' THEN 1 ELSE 0 END) as late,
                SUM(CASE WHEN a.status = 'excused' THEN 1 ELSE 0 END) as excused,
                ROUND((SUM(CASE WHEN a.status = 'present' OR a.status = 'late' THEN 1 ELSE 0 END) / COUNT(a.id)) * 100, 2) as attendance_percentage
            FROM enrollments e
            JOIN users u ON e.student_id = u.id
            JOIN student_profiles sp ON u.id = sp.user_id
            LEFT JOIN attendance a ON a.student_id = u.id AND a.section_id = %s
            WHERE e.section_id = %s AND e.status = 'approved'
            GROUP BY u.id
            ORDER BY u.name
        """, (section_id, section_id))
        
        students = cursor.fetchall()
        cursor.close()
        
        return jsonify({
            'section_id': section_id,
            'daily_summary': daily,
            'student_summary': students
        }), 200
        
    except Exception as e:
        print(f"Error getting attendance summary: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500