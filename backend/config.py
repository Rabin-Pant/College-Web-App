import os
from datetime import timedelta
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    # ============ BASE CONFIGURATION ============
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-fallback')
    FLASK_APP = os.getenv('FLASK_APP', 'app.py')
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    FLASK_DEBUG = os.getenv('FLASK_DEBUG', '1').lower() in ('true', '1', 't')
    
    # ============ JWT CONFIGURATION ============
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'jwt-secret-key-fallback')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    JWT_TOKEN_LOCATION = ['headers']
    JWT_HEADER_NAME = 'Authorization'
    JWT_HEADER_TYPE = 'Bearer'
    
    # ============ MYSQL DATABASE CONFIGURATION ============
    MYSQL_HOST = os.getenv('MYSQL_HOST', 'localhost')
    MYSQL_USER = os.getenv('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', '')
    MYSQL_DB = os.getenv('MYSQL_DB', 'college_app')
    MYSQL_PORT = int(os.getenv('MYSQL_PORT', 3306))
    MYSQL_CURSORCLASS = 'DictCursor'
    MYSQL_CHARSET = 'utf8mb4'
    
    # ============ FILE UPLOAD CONFIGURATION ============
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100MB
    
    UPLOAD_PATHS = {
        'assignments': os.path.join(UPLOAD_FOLDER, 'assignments'),
        'submissions': os.path.join(UPLOAD_FOLDER, 'submissions'),
        'materials': os.path.join(UPLOAD_FOLDER, 'materials'),
        'profile_pics': os.path.join(UPLOAD_FOLDER, 'profile_pics'),
        'feedback': os.path.join(UPLOAD_FOLDER, 'feedback'),
        'temp': os.path.join(UPLOAD_FOLDER, 'temp')
    }
    
    ALLOWED_EXTENSIONS = {
        'pdf', 'doc', 'docx', 'ppt', 'pptx', 'xls', 'xlsx', 'txt', 'md',
        'jpg', 'jpeg', 'png', 'gif', 'svg', 'webp',
        'zip', 'rar', '7z', 'tar', 'gz',
        'mp4', 'mov', 'avi', 'webm', 'mkv',
        'py', 'js', 'html', 'css', 'cpp', 'c', 'java', 'ipynb', 'json', 'xml',
        'csv', 'log', 'ini', 'conf'
    }
    
    MAX_FILE_SIZES = {
        'assignments': 50,
        'submissions': 50,
        'materials': 100,
        'profile_pics': 5,
        'feedback': 20,
        'temp': 10
    }
    
    # ============ CORS CONFIGURATION ============
    CORS_ORIGINS = [
        'http://localhost:3000',
        'http://localhost:3001',
        'http://127.0.0.1:3000',
        'http://127.0.0.1:3001'
    ]
    CORS_METHODS = ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS']
    CORS_ALLOW_HEADERS = ['Content-Type', 'Authorization']
    
    # ============ EMAIL CONFIGURATION ============
    MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.getenv('MAIL_PORT', 587))
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'True').lower() in ('true', '1', 't')
    MAIL_USE_SSL = os.getenv('MAIL_USE_SSL', 'False').lower() in ('true', '1', 't')
    MAIL_USERNAME = os.getenv('MAIL_USERNAME', '')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD', '')
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER', 'noreply@collegeapp.com')
    
    # ============ APPLICATION SETTINGS ============
    COLLEGE_EMAIL_DOMAIN = os.getenv('COLLEGE_EMAIL_DOMAIN', '@yourcollege.edu')
    CLASS_CODE_LENGTH = 6
    CLASS_CODE_CHARS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
    ITEMS_PER_PAGE = int(os.getenv('ITEMS_PER_PAGE', 20))
    MAX_PAGE_SIZE = 100
    TIMEZONE = os.getenv('TIMEZONE', 'UTC')
    DATE_FORMAT = '%Y-%m-%d'
    DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'
    
    # ============ SECURITY SETTINGS ============
    PASSWORD_MIN_LENGTH = 8
    PASSWORD_REQUIRE_UPPERCASE = True
    PASSWORD_REQUIRE_LOWERCASE = True
    PASSWORD_REQUIRE_NUMBER = True
    PASSWORD_REQUIRE_SPECIAL = True
    
    SESSION_COOKIE_SECURE = os.getenv('SESSION_COOKIE_SECURE', 'False').lower() in ('true', '1', 't')
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # ============ FEATURE FLAGS ============
    ENABLE_EMAIL_VERIFICATION = os.getenv('ENABLE_EMAIL_VERIFICATION', 'False').lower() in ('true', '1', 't')
    ENABLE_PASSWORD_RESET = os.getenv('ENABLE_PASSWORD_RESET', 'True').lower() in ('true', '1', 't')
    ENABLE_FILE_UPLOADS = os.getenv('ENABLE_FILE_UPLOADS', 'True').lower() in ('true', '1', 't')
    ENABLE_NOTIFICATIONS = os.getenv('ENABLE_NOTIFICATIONS', 'True').lower() in ('true', '1', 't')
    
    # ============ LOGGING ============
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'app.log')
    LOG_MAX_BYTES = 10 * 1024 * 1024  # 10MB
    LOG_BACKUP_COUNT = 5

    @staticmethod
    def init_app(app):
        """Initialize application with configuration - THIS IS THE ONLY PLACE 'app' IS USED"""
        import os
        for folder_name, folder_path in Config.UPLOAD_PATHS.items():
            os.makedirs(folder_path, exist_ok=True)
            print(f"✅ Created upload folder: {folder_name}")
        
        if app.config['FLASK_ENV'] == 'development':
            print("⚠️ Running in development mode")
            if app.config['SECRET_KEY'] == 'dev-secret-key-fallback':
                print("⚠️ Using default SECRET_KEY - change this in production!")
            if app.config['JWT_SECRET_KEY'] == 'jwt-secret-key-fallback':
                print("⚠️ Using default JWT_SECRET_KEY - change this in production!")


class DevelopmentConfig(Config):
    DEBUG = True
    FLASK_ENV = 'development'
    FLASK_DEBUG = 1


class ProductionConfig(Config):
    DEBUG = False
    FLASK_ENV = 'production'
    FLASK_DEBUG = 0
    SESSION_COOKIE_SECURE = True
    
    SECRET_KEY = os.getenv('SECRET_KEY')
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY')
    
    @staticmethod
    def init_app(app):
        Config.init_app(app)
        import logging
        from logging.handlers import RotatingFileHandler
        
        file_handler = RotatingFileHandler(
            Config.LOG_FILE,
            maxBytes=Config.LOG_MAX_BYTES,
            backupCount=Config.LOG_BACKUP_COUNT
        )
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        print("✅ Production logging initialized")


class TestingConfig(Config):
    TESTING = True
    DEBUG = True
    FLASK_ENV = 'testing'
    MYSQL_DB = 'college_app_test'
    WTF_CSRF_ENABLED = False
    PRESERVE_CONTEXT_ON_EXCEPTION = False


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}