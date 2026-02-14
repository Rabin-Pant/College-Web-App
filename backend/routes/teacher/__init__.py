from routes.teacher.sections import teacher_sections_bp
from routes.teacher.materials import teacher_materials_bp
from routes.teacher.assignments import teacher_assignments_bp
from routes.teacher.grading import teacher_grading_bp
from routes.teacher.attendance import teacher_attendance_bp
from routes.teacher.zoom import teacher_zoom_bp
from routes.teacher.enrollments import teacher_enrollments_bp
from routes.teacher.schedule import teacher_schedule_bp  # ADD THIS

__all__ = [
    'teacher_sections_bp',
    'teacher_materials_bp',
    'teacher_assignments_bp',
    'teacher_grading_bp',
    'teacher_attendance_bp',
    'teacher_zoom_bp',
    'teacher_enrollments_bp',
    'teacher_schedule_bp'  # ADD THIS
]