from routes.admin.courses import admin_courses_bp
from routes.admin.subjects import admin_subjects_bp
from routes.admin.sections import admin_sections_bp
from routes.admin.teacher_assignments import admin_teacher_assignments_bp
from routes.admin.enrollments import admin_enrollments_bp
from routes.admin.schedules import admin_schedules_bp
from routes.admin.users import admin_users_bp
from routes.admin.stats import admin_stats_bp
from routes.admin.reports import admin_reports_bp
from routes.admin.settings import admin_settings_bp

__all__ = [
    'admin_courses_bp',
    'admin_subjects_bp',
    'admin_sections_bp',
    'admin_teacher_assignments_bp',
    'admin_enrollments_bp',
    'admin_schedules_bp',
    'admin_users_bp',
    'admin_stats_bp',
    'admin_reports_bp',
    'admin_settings_bp'
]