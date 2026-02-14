from routes.student.sections import student_sections_bp
from routes.student.enrollments import student_enrollments_bp
from routes.student.assignments import student_assignments_bp
from routes.student.grades import student_grades_bp
from routes.student.materials import student_materials_bp
from routes.student.zoom import student_zoom_bp

__all__ = [
    'student_sections_bp',
    'student_enrollments_bp',
    'student_assignments_bp',
    'student_grades_bp',
    'student_materials_bp',
    'student_zoom_bp'
]