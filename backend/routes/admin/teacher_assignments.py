from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from utils.database import mysql
from utils.decorators import admin_required
from models.teacher_assignment import TeacherAssignment
from models.section import Section

admin_teacher_assignments_bp = Blueprint('admin_teacher_assignments', __name__)

# ============ GET ALL ASSIGNMENTS ============

@admin_teacher_assignments_bp.route('/', methods=['GET'], strict_slashes=False)
@jwt_required()
@admin_required
def get_all_assignments():
    """Get all teacher assignments"""
    try:
        academic_year = request.args.get('academic_year')
        semester = request.args.get('semester')
        teacher_id = request.args.get('teacher_id', type=int)
        
        cursor = mysql.connection.cursor()
        query = """
            SELECT 
                ta.id,
                ta.is_primary,
                ta.assigned_date,
                ta.created_at,
                u.id as teacher_id,
                u.name as teacher_name,
                u.email as teacher_email,
                tp.employee_id,
                s.id as section_id,
                s.name as section_name,
                s.academic_year,
                s.semester as academic_semester,
                s.capacity,
                s.enrolled_count,
                sub.id as subject_id,
                sub.code as subject_code,
                sub.name as subject_name,
                sub.credits,
                c.id as course_id,
                c.name as course_name,
                c.code as course_code
            FROM teacher_assignments ta
            JOIN users u ON ta.teacher_id = u.id
            JOIN teacher_profiles tp ON u.id = tp.user_id
            JOIN sections s ON ta.section_id = s.id
            JOIN subjects sub ON s.subject_id = sub.id
            JOIN courses c ON sub.course_id = c.id
            WHERE 1=1
        """
        params = []
        
        if academic_year:
            query += " AND s.academic_year = %s"
            params.append(academic_year)
        if semester:
            query += " AND s.semester = %s"
            params.append(semester)
        if teacher_id:
            query += " AND ta.teacher_id = %s"
            params.append(teacher_id)
            
        query += " ORDER BY c.name, sub.semester, s.name"
        
        cursor.execute(query, params)
        assignments = cursor.fetchall()
        cursor.close()
        
        return jsonify({
            'total': len(assignments),
            'assignments': assignments
        }), 200
        
    except Exception as e:
        print(f"Error getting assignments: {e}")
        return jsonify({'error': str(e)}), 500


# ============ GET TEACHERS LIST ============

@admin_teacher_assignments_bp.route('/teachers', methods=['GET'], strict_slashes=False)
@jwt_required()
@admin_required
def get_teachers():
    """Get all teachers for dropdown"""
    try:
        cursor = mysql.connection.cursor()
        cursor.execute("""
            SELECT 
                u.id,
                u.name,
                u.email,
                tp.employee_id,
                tp.department
            FROM users u
            JOIN teacher_profiles tp ON u.id = tp.user_id
            WHERE u.role = 'teacher' AND u.email_verified = TRUE
            ORDER BY u.name
        """)
        teachers = cursor.fetchall()
        cursor.close()
        
        return jsonify({'teachers': teachers}), 200
        
    except Exception as e:
        print(f"Error getting teachers: {e}")
        return jsonify({'error': str(e)}), 500


# ============ GET UNASSIGNED SECTIONS ============

@admin_teacher_assignments_bp.route('/unassigned-sections', methods=['GET'], strict_slashes=False)
@jwt_required()
@admin_required
def get_unassigned_sections():
    """Get sections without teachers assigned"""
    try:
        academic_year = request.args.get('academic_year')
        semester = request.args.get('semester')
        
        cursor = mysql.connection.cursor()
        query = """
            SELECT 
                s.id,
                s.name,
                s.academic_year,
                s.semester,
                s.capacity,
                s.enrolled_count,
                sub.id as subject_id,
                sub.code as subject_code,
                sub.name as subject_name,
                c.id as course_id,
                c.name as course_name,
                c.code as course_code
            FROM sections s
            JOIN subjects sub ON s.subject_id = sub.id
            JOIN courses c ON sub.course_id = c.id
            WHERE NOT EXISTS (
                SELECT 1 FROM teacher_assignments ta WHERE ta.section_id = s.id
            )
        """
        params = []
        
        if academic_year:
            query += " AND s.academic_year = %s"
            params.append(academic_year)
        if semester:
            query += " AND s.semester = %s"
            params.append(semester)
            
        query += " ORDER BY c.name, sub.semester, s.name"
        
        cursor.execute(query, params)
        sections = cursor.fetchall()
        cursor.close()
        
        return jsonify({
            'total': len(sections),
            'sections': sections
        }), 200
        
    except Exception as e:
        print(f"Error getting unassigned sections: {e}")
        return jsonify({'error': str(e)}), 500


# ============ ASSIGN TEACHER TO SECTION ============

@admin_teacher_assignments_bp.route('/', methods=['POST'], strict_slashes=False)
@jwt_required()
@admin_required
def assign_teacher():
    """Assign a teacher to a section"""
    try:
        data = request.get_json()
        
        required_fields = ['teacher_id', 'section_id']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Verify section exists
        section = Section.get_by_id(data['section_id'])
        if not section:
            return jsonify({'error': 'Section not found'}), 404
        
        # Check if teacher already assigned to this section
        cursor = mysql.connection.cursor()
        cursor.execute("""
            SELECT id FROM teacher_assignments 
            WHERE section_id = %s
        """, (data['section_id'],))
        
        if cursor.fetchone():
            cursor.close()
            return jsonify({'error': 'Section already has a teacher assigned'}), 400
        
        cursor.close()
        
        assignment_id = TeacherAssignment.create(
            teacher_id=data['teacher_id'],
            section_id=data['section_id'],
            is_primary=data.get('is_primary', True)
        )
        
        return jsonify({
            'message': 'Teacher assigned successfully',
            'assignment_id': assignment_id
        }), 201
        
    except Exception as e:
        print(f"Error assigning teacher: {e}")
        return jsonify({'error': str(e)}), 500


# ============ REMOVE ASSIGNMENT ============

@admin_teacher_assignments_bp.route('/<int:assignment_id>', methods=['DELETE'], strict_slashes=False)
@jwt_required()
@admin_required
def remove_assignment(assignment_id):
    """Remove a teacher assignment"""
    try:
        success = TeacherAssignment.remove(assignment_id)
        
        if success:
            return jsonify({'message': 'Teacher unassigned successfully'}), 200
        else:
            return jsonify({'error': 'Assignment not found'}), 404
            
    except Exception as e:
        print(f"Error removing assignment: {e}")
        return jsonify({'error': str(e)}), 500


# ============ BULK ASSIGN ============

@admin_teacher_assignments_bp.route('/bulk', methods=['POST'], strict_slashes=False)
@jwt_required()
@admin_required
def bulk_assign():
    """Assign multiple teachers at once"""
    try:
        data = request.get_json()
        assignments = data.get('assignments', [])
        
        if not assignments:
            return jsonify({'error': 'No assignments provided'}), 400
        
        created_ids = []
        errors = []
        
        for idx, item in enumerate(assignments):
            try:
                if 'teacher_id' not in item or 'section_id' not in item:
                    errors.append(f"Row {idx+1}: Missing teacher_id or section_id")
                    continue
                
                # Check if section already has teacher
                cursor = mysql.connection.cursor()
                cursor.execute("""
                    SELECT id FROM teacher_assignments 
                    WHERE section_id = %s
                """, (item['section_id'],))
                
                if cursor.fetchone():
                    errors.append(f"Row {idx+1}: Section already has a teacher")
                    cursor.close()
                    continue
                
                cursor.close()
                
                assignment_id = TeacherAssignment.create(
                    teacher_id=item['teacher_id'],
                    section_id=item['section_id'],
                    is_primary=item.get('is_primary', True)
                )
                created_ids.append(assignment_id)
                
            except Exception as e:
                errors.append(f"Row {idx+1}: {str(e)}")
        
        return jsonify({
            'message': f'Created {len(created_ids)} assignments',
            'created_ids': created_ids,
            'errors': errors
        }), 201
        
    except Exception as e:
        print(f"Error bulk assigning: {e}")
        return jsonify({'error': str(e)}), 500


# ============ GET ASSIGNMENTS BY TEACHER ============

@admin_teacher_assignments_bp.route('/teacher/<int:teacher_id>', methods=['GET'], strict_slashes=False)
@jwt_required()
@admin_required
def get_teacher_assignments(teacher_id):
    """Get all assignments for a specific teacher"""
    try:
        assignments = TeacherAssignment.get_by_teacher(teacher_id)
        
        return jsonify({
            'teacher_id': teacher_id,
            'total': len(assignments),
            'assignments': assignments
        }), 200
        
    except Exception as e:
        print(f"Error getting teacher assignments: {e}")
        return jsonify({'error': str(e)}), 500


# ============ GET ASSIGNMENTS BY SECTION ============

@admin_teacher_assignments_bp.route('/section/<int:section_id>', methods=['GET'], strict_slashes=False)
@jwt_required()
@admin_required
def get_section_teachers(section_id):
    """Get teachers assigned to a section"""
    try:
        teachers = TeacherAssignment.get_by_section(section_id)
        
        return jsonify({
            'section_id': section_id,
            'total': len(teachers),
            'teachers': teachers
        }), 200
        
    except Exception as e:
        print(f"Error getting section teachers: {e}")
        return jsonify({'error': str(e)}), 500


# ============ UPDATE ASSIGNMENT ============

@admin_teacher_assignments_bp.route('/<int:assignment_id>', methods=['PUT'], strict_slashes=False)
@jwt_required()
@admin_required
def update_assignment(assignment_id):
    """Update an assignment (e.g., change is_primary status)"""
    try:
        data = request.get_json()
        
        cursor = mysql.connection.cursor()
        
        update_fields = []
        values = []
        
        if 'is_primary' in data:
            update_fields.append("is_primary = %s")
            values.append(data['is_primary'])
        
        if update_fields:
            query = f"UPDATE teacher_assignments SET {', '.join(update_fields)} WHERE id = %s"
            values.append(assignment_id)
            cursor.execute(query, tuple(values))
            mysql.connection.commit()
            affected = cursor.rowcount
        else:
            affected = 0
        
        cursor.close()
        
        if affected:
            return jsonify({'message': 'Assignment updated successfully'}), 200
        else:
            return jsonify({'error': 'Assignment not found'}), 404
            
    except Exception as e:
        print(f"Error updating assignment: {e}")
        return jsonify({'error': str(e)}), 500