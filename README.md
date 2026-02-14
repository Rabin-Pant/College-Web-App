# 🎓 College Management System

<div align="center">

![Version](https://img.shields.io/badge/version-2.0.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.13-green.svg)
![Flask](https://img.shields.io/badge/flask-2.3.3-red.svg)
![React](https://img.shields.io/badge/react-18.2.0-61dafb.svg)
![MySQL](https://img.shields.io/badge/mysql-8.0-orange.svg)
![License](https://img.shields.io/badge/license-MIT-yellow.svg)

A comprehensive college management system with role-based access control for **Admins**, **Teachers**, and **Students**. Built with Flask backend and React frontend.

[Features](#-features) • [Tech Stack](#-tech-stack) • [Installation](#-installation) • [API Documentation](#-api-documentation) • [Contributing](#-contributing)

</div>

---

## ✨ Features

### 👑 Admin
- ✅ Full system control and monitoring
- ✅ Course & Subject management
- ✅ Section creation with capacity control
- ✅ Teacher assignment to sections
- ✅ Student enrollment approval/rejection
- ✅ User management (create, verify, delete)
- ✅ System-wide announcements
- ✅ Analytics and reports dashboard

### 👨‍🏫 Teacher
- ✅ View assigned sections
- ✅ Upload study materials (PDF, PPT, videos, links)
- ✅ Create assignments with due dates and rubrics
- ✅ Grade submissions with feedback
- ✅ Take attendance
- ✅ Schedule Zoom meetings
- ✅ Approve/reject enrollment requests
- ✅ Send notifications to students
- ✅ View class roster and student progress

### 👨‍🎓 Student
- ✅ Browse available sections
- ✅ Request enrollment in sections
- ✅ View enrolled sections and schedule
- ✅ Access study materials
- ✅ Submit assignments (text + file upload)
- ✅ View grades and feedback
- ✅ Join Zoom meetings
- ✅ Receive notifications
- ✅ Track attendance

### 📱 Additional Features
- ✅ JWT Authentication
- ✅ Email verification (optional)
- ✅ Real-time notifications
- ✅ File upload with progress
- ✅ Responsive design (mobile-friendly)
- ✅ Dark mode support
- ✅ Calendar view of deadlines
- ✅ Search and filter functionality

---

## 🛠️ Tech Stack

### Backend
├── Python 3.13
├── Flask 2.3.3
├── Flask-JWT-Extended (Authentication)
├── Flask-CORS (CORS handling)
├── Flask-MySQLdb (Database)
├── PyMySQL (MySQL connector)
├── Werkzeug (Password hashing)
├── python-dotenv (Environment variables)
└── bcrypt (Encryption)

### Frontend
├── React 18
├── React Router 6 (Navigation)
├── Tailwind CSS (Styling)
├── Axios (API calls)
├── React Hot Toast (Notifications)
├── React Icons (Icons)
├── React Dropzone (File uploads)
├── React DatePicker (Date selection)
├── Headless UI (Accessible components)
└── Heroicons (Icons)

### Database
└── MySQL 8.0 / MariaDB 11.8


---

## 📋 Prerequisites

- **Python** 3.8 or higher
- **Node.js** 16 or higher
- **MySQL** 8.0 or **MariaDB** 10.5 or higher
- **Git** (for cloning)
- **npm** or **yarn** (for frontend)

---

## 🚀 Installation

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/college-app.git
cd college-app
```

2. Backend Setup
```bash
# Navigate to backend folder
cd backend
# Create virtual environment
python -m venv venv
# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Linux/Mac:
source venv/bin/activate
# Install dependencies
pip install -r requirements.txt
# Create .env file from template
cp .env.example .env
# Edit .env with your database credentials
# Open .env in your editor and update:
# - MYSQL_PASSWORD=your_password
# - SECRET_KEY=your_secret_key
# - JWT_SECRET_KEY=your_jwt_secret
# Create database
mysql -u root -p < models/new_schema.sql
# (Optional) Add sample data
python create_sample_data_final_v2.py
# Run backend server
python app.py
```

3. Frontend Setup
```bash
# Open a new terminal
cd frontend
# Install dependencies
npm install
# Create .env file
echo "REACT_APP_API_URL=http://localhost:5000/api" > .env
# Start development server
npm start
```
4. Access the Application
```bash
Frontend: http://localhost:3000
Backend API: http://localhost:5000
API Documentation: http://localhost:5000/api/health
```


👤 Default Users
After installation, you can login with these default accounts:

Role	Email	Password	Description
Admin	admin@yourcollege.edu	Admin@123	Full system access
Teacher	teacher@yourcollege.edu	Test@123	Dr. John Smith
Student	student@yourcollege.edu	Test@123	Jane Doe

📁 Project Structure
college-app/
├── backend/                           # Flask Backend
│   ├── app.py                        # Main application
│   ├── config.py                      # Configuration
│   ├── requirements.txt               # Python dependencies
│   ├── .env.example                   # Environment variables template
│   ├── models/                        # Database models
│   │   ├── user.py
│   │   ├── course.py
│   │   ├── subject.py
│   │   ├── section.py
│   │   ├── enrollment.py
│   │   ├── assignment.py
│   │   └── ...
│   ├── routes/                        # API routes
│   │   ├── admin/                     # Admin routes
│   │   ├── teacher/                    # Teacher routes
│   │   └── student/                    # Student routes
│   └── utils/                          # Helper functions
│       ├── auth_helpers.py
│       ├── file_handler.py
│       └── validators.py
│
└── frontend/                           # React Frontend
    ├── public/                         # Static files
    ├── src/
    │   ├── components/                  # React components
    │   │   ├── admin/                   # Admin components
    │   │   ├── teacher/                  # Teacher components
    │   │   ├── student/                  # Student components
    │   │   └── common/                   # Shared components
    │   ├── pages/                        # Page components
    │   ├── context/                       # React context
    │   ├── services/                      # API services
    │   └── utils/                         # Helper functions
    ├── package.json                       # Node dependencies
    └── tailwind.config.js                  # Tailwind configuration

🔑 Environment Variables
Backend (.env)
```bash
# Flask Configuration    
SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-key-here

# Database Configuration
MYSQL_HOST=localhost
MYSQL_USER=root
MYSQL_PASSWORD=your-password-here
MYSQL_DB=college_app

# Email Configuration (Optional)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_DEFAULT_SENDER=noreply@collegeapp.com

# App Configuration
FLASK_APP=app.py
FLASK_ENV=development
FLASK_DEBUG=1
```

Frontend (.env)
```bash
REACT_APP_API_URL=http://localhost:5000/api
```

📚 API Documentation
Authentication Endpoints
POST   /api/auth/register        # Register new user
POST   /api/auth/login           # Login user
POST   /api/auth/refresh          # Refresh JWT token
GET    /api/auth/profile          # Get user profile
PUT    /api/auth/profile          # Update profile
PUT    /api/auth/change-password  # Change password

Admin Endpoints
GET    /api/admin/users           # Get all users
POST   /api/admin/users           # Create user
PUT    /api/admin/users/:id/verify # Verify teacher
DELETE /api/admin/users/:id       # Delete user
GET    /api/admin/courses         # Get all courses
POST   /api/admin/courses         # Create course
PUT    /api/admin/courses/:id     # Update course
DELETE /api/admin/courses/:id     # Delete course
GET    /api/admin/subjects        # Get all subjects
POST   /api/admin/subjects        # Create subject
PUT    /api/admin/subjects/:id    # Update subject
DELETE /api/admin/subjects/:id    # Delete subject
GET    /api/admin/sections        # Get all sections
POST   /api/admin/sections        # Create section
PUT    /api/admin/sections/:id    # Update section
DELETE /api/admin/sections/:id    # Delete section
GET    /api/admin/enrollments     # Get all enrollments
POST   /api/admin/enrollments/:id/approve # Approve enrollment
POST   /api/admin/enrollments/:id/reject  # Reject enrollment
POST   /api/admin/enrollments/bulk-approve # Bulk approve
GET    /api/admin/stats           # Get system statistics
GET    /api/admin/reports/classes # Get class reports

Teacher Endpoints
GET    /api/teacher/sections      # Get assigned sections
GET    /api/teacher/sections/:id  # Get section details
GET    /api/teacher/sections/stats # Get teaching stats
POST   /api/teacher/materials     # Upload material
GET    /api/teacher/materials/section/:id # Get section materials
DELETE /api/teacher/materials/:id # Delete material
POST   /api/teacher/assignments   # Create assignment
GET    /api/teacher/assignments/section/:id # Get section assignments
PUT    /api/teacher/assignments/:id # Update assignment
DELETE /api/teacher/assignments/:id # Delete assignment
POST   /api/teacher/assignments/:id/publish # Publish assignment
GET    /api/teacher/grading/pending # Get pending grading
GET    /api/teacher/grading/assignment/:id # Get submissions for assignment
PUT    /api/teacher/grading/:id   # Grade submission
POST   /api/teacher/attendance/bulk # Mark attendance
GET    /api/teacher/attendance/section/:id # Get attendance
POST   /api/teacher/zoom          # Schedule Zoom meeting
GET    /api/teacher/zoom/upcoming # Get upcoming meetings
GET    /api/teacher/zoom/section/:id # Get section meetings
PUT    /api/teacher/zoom/:id      # Update meeting
DELETE /api/teacher/zoom/:id      # Delete meeting

Student Endpoints
GET    /api/student/sections      # Get enrolled sections
GET    /api/student/sections/:id  # Get section details
GET    /api/student/available-sections # Browse available sections
GET    /api/student/sections/available # Alias for available sections
POST   /api/student/enrollments   # Request enrollment
GET    /api/student/enrollments/pending # Get pending requests
GET    /api/student/assignments/upcoming # Get upcoming assignments
GET    /api/student/assignments/section/:id # Get section assignments
GET    /api/student/assignments/:id # Get assignment details
POST   /api/student/assignments/:id/submit # Submit assignment
GET    /api/student/assignments/:id/submissions # Get submission
GET    /api/student/grades/recent # Get recent grades
GET    /api/student/materials/section/:id # Get section materials
GET    /api/student/zoom/section/:id # Get section Zoom meetings

Notification Endpoints
GET    /api/notifications/        # Get user notifications
GET    /api/notifications/unread-count # Get unread count
PUT    /api/notifications/:id/read # Mark as read
PUT    /api/notifications/read-all # Mark all as read
DELETE /api/notifications/:id     # Delete notification
DELETE /api/notifications/clear-all # Clear all notifications
POST   /api/notifications/send-to-class/:id # Send to class
POST   /api/notifications/send-to-all-classes # Send to all classes
POST   /api/notifications/send-to-all-students # Send to all students
POST   /api/notifications/send-to-all-teachers # Send to all teachers
POST   /api/notifications/send-to-all-users # Send to all users
POST   /api/notifications/send-to-user/:id # Send to specific user

🚦 Running Tests
# Backend tests
cd backend
python -m pytest

# Frontend tests
cd frontend
npm test

📦 Building for Production
Backend
cd backend
# Update .env for production
FLASK_ENV=production
FLASK_DEBUG=0

# Run with gunicorn (Linux/Mac)
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app

# Or with waitress (Windows)
pip install waitress
waitress-serve --port=5000 app:app

Frontend
cd frontend
npm run build
# Serve the build folder with any static server
# For example, with serve:
npx serve -s build -l 3000

👨‍💻 Author
Rabin Pant
GitHub: https://github.com/Rabin-Pant
Email: rabinpant@194gmail.com

🐛 Known Issues
Email verification requires SMTP configuration
File upload size limited to 50MB
Zoom integration requires manual link entry (no API integration yet)
Some endpoints may return 500 errors if database tables are missing

🗺️ Roadmap
Add email notifications
Implement Zoom API integration
Add video conferencing directly in app
Create mobile app with React Native
Add discussion forums
Implement real-time chat
Add grade analytics and visualizations
Create export functionality (PDF/Excel)

<div align="center"> Made with ❤️ by Rabin Pant
Happy Coding! 🚀

</div> ```
