from flask import Flask, jsonify
from flask_cors import CORS  # Make sure this import is present
from flask_jwt_extended import JWTManager
from config import Config
import os

# ============ IMPORT UTILS ============
from utils.database import mysql, test_connection, init_db

# ============ IMPORT BLUEPRINTS ============

# Auth Blueprints
from routes.auth import auth_bp

# Feature Blueprints
from routes.classes import class_bp
from routes.assignments import assignment_bp
from routes.materials import material_bp
from routes.announcements import announcement_bp
from routes.notifications import notification_bp
from routes.courses import courses_bp
from routes.subjects import subjects_bp

# ============ ADMIN BLUEPRINTS ============
from routes.admin.courses import admin_courses_bp
from routes.admin.subjects import admin_subjects_bp
from routes.admin.sections import admin_sections_bp
from routes.admin.teacher_assignments import admin_teacher_assignments_bp
from routes.admin.enrollments import admin_enrollments_bp
from routes.admin.schedules import admin_schedules_bp
from routes.admin.users import admin_users_bp
from routes.admin.stats import admin_stats_bp
from routes.admin.reports import admin_reports_bp

# ============ TEACHER SUB-ROUTES ============
from routes.teacher.sections import teacher_sections_bp
from routes.teacher.materials import teacher_materials_bp
from routes.teacher.assignments import teacher_assignments_bp
from routes.teacher.grading import teacher_grading_bp
from routes.teacher.attendance import teacher_attendance_bp
from routes.teacher.zoom import teacher_zoom_bp
from routes.teacher.enrollments import teacher_enrollments_bp
from routes.teacher.schedule import teacher_schedule_bp

# ============ STUDENT SUB-ROUTES ============
from routes.student.sections import student_sections_bp
from routes.student.enrollments import student_enrollments_bp
from routes.student.assignments import student_assignments_bp
from routes.student.grades import student_grades_bp
from routes.student.materials import student_materials_bp
from routes.student.zoom import student_zoom_bp

# Initialize JWT
jwt = JWTManager()

def create_app(config_class=Config):
    # ============ CREATE FLASK APP ============
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # ============ CORS CONFIGURATION ============
    # Allow all origins for API routes (development only)
    # This is the key fix for your CORS errors
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    
    # ============ INITIALIZE EXTENSIONS ============
    # Initialize JWT
    jwt.init_app(app)
    
    # Initialize MySQL
    init_db(app)
    
    # Initialize app (creates folders, etc.)
    config_class.init_app(app)
    
    # ============ REGISTER BLUEPRINTS ============
    
    # Auth Blueprints (No auth required)
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    
    # Feature Blueprints (Mixed access - handled in routes)
    app.register_blueprint(class_bp, url_prefix='/api/classes')
    app.register_blueprint(assignment_bp, url_prefix='/api/assignments')
    app.register_blueprint(material_bp, url_prefix='/api/materials')
    app.register_blueprint(announcement_bp, url_prefix='/api/announcements')
    app.register_blueprint(notification_bp, url_prefix='/api/notifications')
    app.register_blueprint(courses_bp, url_prefix='/api/courses')
    app.register_blueprint(subjects_bp, url_prefix='/api/subjects')
    
    # ============ ADMIN MANAGEMENT BLUEPRINTS ============
    app.register_blueprint(admin_courses_bp, url_prefix='/api/admin/courses')
    app.register_blueprint(admin_subjects_bp, url_prefix='/api/admin/subjects')
    app.register_blueprint(admin_sections_bp, url_prefix='/api/admin/sections')
    app.register_blueprint(admin_teacher_assignments_bp, url_prefix='/api/admin/teacher-assignments')
    app.register_blueprint(admin_enrollments_bp, url_prefix='/api/admin/enrollments')
    app.register_blueprint(admin_schedules_bp, url_prefix='/api/admin/schedules')
    app.register_blueprint(admin_users_bp, url_prefix='/api/admin/users')
    app.register_blueprint(admin_stats_bp, url_prefix='/api/admin/stats')
    app.register_blueprint(admin_reports_bp, url_prefix='/api/admin/reports')
    
    # ============ TEACHER SUB-ROUTES ============
    app.register_blueprint(teacher_sections_bp, url_prefix='/api/teacher/sections')
    app.register_blueprint(teacher_materials_bp, url_prefix='/api/teacher/materials')
    app.register_blueprint(teacher_assignments_bp, url_prefix='/api/teacher/assignments')
    app.register_blueprint(teacher_grading_bp, url_prefix='/api/teacher/grading')
    app.register_blueprint(teacher_attendance_bp, url_prefix='/api/teacher/attendance')
    app.register_blueprint(teacher_zoom_bp, url_prefix='/api/teacher/zoom')
    app.register_blueprint(teacher_enrollments_bp, url_prefix='/api/teacher/enrollments')
    app.register_blueprint(teacher_schedule_bp, url_prefix='/api/teacher/schedule')
    
    # ============ STUDENT SUB-ROUTES ============
    app.register_blueprint(student_sections_bp, url_prefix='/api/student/sections')
    app.register_blueprint(student_enrollments_bp, url_prefix='/api/student/enrollments')
    app.register_blueprint(student_assignments_bp, url_prefix='/api/student/assignments')
    app.register_blueprint(student_grades_bp, url_prefix='/api/student/grades')
    app.register_blueprint(student_materials_bp, url_prefix='/api/student/materials')  
    app.register_blueprint(student_zoom_bp, url_prefix='/api/student/zoom')          
    
    
    # ============ BLUEPRINT REGISTRATION SUMMARY ============
    print("\n" + "="*60)
    print("🚀 COLLEGE APP API - BLUEPRINTS REGISTERED")
    print("="*60)
    print(f"✅ /api/auth                 - Authentication")
    print(f"✅ /api/classes              - Classes")
    print(f"✅ /api/assignments          - Assignments")
    print(f"✅ /api/materials            - Materials")
    print(f"✅ /api/announcements        - Announcements")
    print(f"✅ /api/notifications        - Notifications")
    print(f"✅ /api/courses              - Courses")
    print(f"✅ /api/subjects             - Subjects")
    print("-" * 60)
    print("📋 ADMIN MANAGEMENT ROUTES:")
    print(f"✅ /api/admin/courses         - Manage Courses")
    print(f"✅ /api/admin/subjects        - Manage Subjects")
    print(f"✅ /api/admin/sections        - Manage Sections")
    print(f"✅ /api/admin/teacher-assignments - Assign Teachers")
    print(f"✅ /api/admin/enrollments     - Manage Enrollments")
    print(f"✅ /api/admin/schedules       - Manage Timetable")
    print(f"✅ /api/admin/users           - Manage Users")
    print(f"✅ /api/admin/stats           - System Statistics")
    print(f"✅ /api/admin/reports         - Generate Reports")
    print("-" * 60)
    print("📋 TEACHER ROUTES:")
    print(f"✅ /api/teacher/sections      - My Sections")
    print(f"✅ /api/teacher/materials     - Upload Materials")
    print(f"✅ /api/teacher/assignments   - Create Assignments")
    print(f"✅ /api/teacher/grading       - Grade Submissions")
    print(f"✅ /api/teacher/attendance    - Take Attendance")
    print(f"✅ /api/teacher/zoom          - Zoom Meetings")
    print(f"✅ /api/teacher/enrollments   - Manage Enrollments")
    print(f"✅ /api/teacher/schedule      - Schedule")
    print("-" * 60)
    print("📋 STUDENT ROUTES:")
    print(f"✅ /api/student/sections      - My Sections")
    print(f"✅ /api/student/enrollments   - Enrollment Requests")
    print(f"✅ /api/student/assignments   - View Assignments")
    print(f"✅ /api/student/grades        - View Grades")
    print("="*60 + "\n")
    
    # ============ TEST ROUTES ============
    
    @app.route('/')
    def home():
        return jsonify({
            'message': 'College App API is running! 🚀',
            'status': 'success',
            'version': '2.0.0',
            'endpoints': {
                'auth': '/api/auth',
                'classes': '/api/classes',
                'assignments': '/api/assignments',
                'materials': '/api/materials',
                'announcements': '/api/announcements',
                'notifications': '/api/notifications',
                'courses': '/api/courses',
                'subjects': '/api/subjects',
                'admin_courses': '/api/admin/courses',
                'admin_subjects': '/api/admin/subjects',
                'admin_sections': '/api/admin/sections',
                'admin_teacher_assignments': '/api/admin/teacher-assignments',
                'admin_enrollments': '/api/admin/enrollments',
                'admin_schedules': '/api/admin/schedules',
                'admin_users': '/api/admin/users',
                'admin_stats': '/api/admin/stats',
                'admin_reports': '/api/admin/reports'
            }
        })
    
    @app.route('/api/health')
    def health_check():
        db_status, db_message = test_connection(app)
        
        cursor = None
        db_stats = {}
        try:
            cursor = mysql.connection.cursor()
            cursor.execute("SELECT COUNT(*) as count FROM users")
            db_stats['users'] = cursor.fetchone()['count']
            cursor.execute("SELECT COUNT(*) as count FROM courses")
            db_stats['courses'] = cursor.fetchone()['count']
            cursor.execute("SELECT COUNT(*) as count FROM subjects")
            db_stats['subjects'] = cursor.fetchone()['count']
            cursor.execute("SELECT COUNT(*) as count FROM sections")
            db_stats['sections'] = cursor.fetchone()['count']
            cursor.close()
        except Exception:
            db_stats = {'error': 'Could not fetch stats'}
            if cursor:
                cursor.close()
        
        return jsonify({
            'status': 'healthy',
            'timestamp': __import__('datetime').datetime.now().isoformat(),
            'environment': app.config['FLASK_ENV'],
            'debug': app.config['DEBUG'],
            'database': {
                'connected': db_status,
                'message': db_message,
                'stats': db_stats
            },
            'blueprints': {
                'count': len(app.blueprints),
                'registered': list(app.blueprints.keys())
            },
            'uploads': {
                'folder': app.config['UPLOAD_FOLDER'],
                'max_size_mb': app.config['MAX_CONTENT_LENGTH'] / (1024 * 1024)
            }
        })
    
    @app.route('/api/status')
    def api_status():
        return jsonify({
            'online': True,
            'version': '2.0.0',
            'time': __import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
    
    # ============ ERROR HANDLERS ============
    
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'error': 'Endpoint not found',
            'message': 'The requested URL was not found on the server',
            'status_code': 404
        }), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({
            'error': 'Internal server error',
            'message': 'Something went wrong on our end',
            'status_code': 500
        }), 500
    
    @app.errorhandler(405)
    def method_not_allowed(error):
        return jsonify({
            'error': 'Method not allowed',
            'message': 'The method is not allowed for this endpoint',
            'status_code': 405
        }), 405
    
    @app.errorhandler(413)
    def file_too_large(error):
        max_size = app.config['MAX_CONTENT_LENGTH'] / (1024 * 1024)
        return jsonify({
            'error': 'File too large',
            'message': f'Maximum file size is {max_size}MB',
            'status_code': 413
        }), 413
    
    # ============ JWT ERROR HANDLERS ============
    
    @jwt.unauthorized_loader
    def unauthorized_response(callback):
        return jsonify({
            'error': 'Missing authorization token',
            'message': 'Please provide a valid JWT token',
            'status_code': 401
        }), 401
    
    @jwt.invalid_token_loader
    def invalid_token_response(callback):
        return jsonify({
            'error': 'Invalid token',
            'message': 'The provided token is invalid or malformed',
            'status_code': 401
        }), 401
    
    @jwt.expired_token_loader
    def expired_token_response(jwt_header, jwt_payload):
        return jsonify({
            'error': 'Token has expired',
            'message': 'Please refresh your token or login again',
            'status_code': 401
        }), 401
    
    @jwt.needs_fresh_token_loader
    def needs_fresh_token_response(jwt_header, jwt_payload):
        return jsonify({
            'error': 'Fresh token required',
            'message': 'Please provide a fresh token for this action',
            'status_code': 401
        }), 401
    
    @jwt.revoked_token_loader
    def revoked_token_response(jwt_header, jwt_payload):
        return jsonify({
            'error': 'Token has been revoked',
            'message': 'This token is no longer valid',
            'status_code': 401
        }), 401
    
    # ============ REQUEST HANDLERS ============
    
    @app.before_request
    def before_request():
        if app.debug:
            from flask import request
            print(f"📥 {request.method} {request.path}")
    
    return app

# ============ CREATE APP INSTANCE ============
app = create_app()

# ============ RUN APPLICATION ============
if __name__ == '__main__':
    with app.app_context():
        success, message = test_connection(app)
        if success:
            print("\n" + "="*50)
            print("✅ DATABASE CONNECTION: SUCCESS")
            print("="*50)
            
            try:
                cursor = mysql.connection.cursor()
                cursor.execute("SHOW TABLES")
                tables = cursor.fetchall()
                print(f"\n📊 DATABASE TABLES: {len(tables)} total")
                
                new_tables = ['courses', 'subjects', 'sections', 'teacher_assignments', 
                             'enrollments', 'schedules', 'zoom_meetings', 'attendance']
                existing_new = [t for t in new_tables if any(t == list(table.values())[0] for table in tables)]
                
                if len(existing_new) == len(new_tables):
                    print("✅ All new tables created successfully!")
                else:
                    print(f"⚠️  New tables found: {len(existing_new)}/{len(new_tables)}")
                
                cursor.close()
            except Exception as e:
                print(f"⚠️  Could not verify tables: {e}")
            
        else:
            print("\n" + "="*50)
            print(f"⚠️ DATABASE CONNECTION: {message}")
            print("="*50)
    
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=app.config['DEBUG']
    )