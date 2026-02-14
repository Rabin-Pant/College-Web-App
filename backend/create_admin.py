from app import app
from utils.database import mysql
from werkzeug.security import generate_password_hash

with app.app_context():
    cursor = mysql.connection.cursor()
    cursor.execute("DELETE FROM users WHERE email = 'admin@yourcollege.edu'")
    hashed_pw = generate_password_hash('Admin@123')
    cursor.execute("""
        INSERT INTO users (email, password, name, role, email_verified, college_email)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, ('admin@yourcollege.edu', hashed_pw, 'System Administrator', 'admin', True, 'admin@yourcollege.edu'))
    mysql.connection.commit()
    print("✅ Admin user created successfully!")
    print("📧 Email: admin@yourcollege.edu")
    print("🔑 Password: Admin@123")
    cursor.close()
