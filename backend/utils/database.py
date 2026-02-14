from flask_mysqldb import MySQL

# MySQL extension instance
mysql = MySQL()

def get_db():
    """Get database connection"""
    return mysql.connection

def test_connection(app):
    """Test database connection"""
    try:
        with app.app_context():
            cursor = mysql.connection.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            cursor.close()
            return True, "✅ Database connection successful!"
    except Exception as e:
        return False, f"❌ Database connection failed: {str(e)}"

def init_db(app):
    """Initialize database with app"""
    mysql.init_app(app)
    print("✅ MySQL initialized")