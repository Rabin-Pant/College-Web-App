# 🎓 College Management System

<div align="center">

![Version](https://img.shields.io/badge/version-2.0.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.13-green.svg)
![Flask](https://img.shields.io/badge/flask-2.3.3-red.svg)
![React](https://img.shields.io/badge/react-18.2.0-61dafb.svg)
![MySQL](https://img.shields.io/badge/mysql-8.0-orange.svg)
![License](https://img.shields.io/badge/license-MIT-yellow.svg)

A comprehensive college management system with role-based access control for **Admins**, **Teachers**, and **Students**. Built with Flask backend and React frontend.

[Features](#-features) • [Tech Stack](#-tech-stack) • [Installation](#-installation) • [API Documentation](#-api-documentation) • [Production Build](#-building-for-production)

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
- Python 3.13
- Flask 2.3.3
- Flask-JWT-Extended
- Flask-CORS
- Flask-MySQLdb
- PyMySQL
- Werkzeug
- python-dotenv
- bcrypt

### Frontend
- React 18
- React Router 6
- Tailwind CSS
- Axios
- React Hot Toast
- React Icons
- React Dropzone
- React DatePicker
- Headless UI
- Heroicons

### Database
- MySQL 8.0 / MariaDB 11.8


### 📁 Project Structure
```bash
college-app/
├── backend/                           # Flask Backend
│   ├── app.py                         # Main application
│   ├── config.py                      # Configuration
│   ├── requirements.txt               # Python dependencies
│   ├── .env.example                   # Environment variables template
    ├── create_admin                   #Sets email_verified = True
    ├── create_sample_data_final_v2    #Creates all necessary sample data
│   ├── models/                        # Database models
│   │   ├── user.py
│   │   ├── course.py
│   │   ├── subject.py
│   │   ├── section.py
│   │   ├── enrollment.py
│   │   ├── assignment.py
│   │   └── ...
│   ├── routes/                         # API routes
│   │   ├── admin/                      # Admin routes
│   │   ├── teacher/                    # Teacher routes
│   │   └── student/                    # Student routes
│   └── utils/                          # Helper functions
│       ├── auth_helpers.py
│       ├── file_handler.py
│       └── validators.py
│
└── frontend/                           # React Frontend
    ├── public/                         # Static files
    └── src/
        ├── components/                  # React components
        │   ├── admin/                    # Admin components
        │   ├── teacher/                  # Teacher components
        │   ├── student/                  # Student components
        │   └── common/                   # Shared components
        ├── pages/                        # Page components
        ├── context/                      # React context
        ├── services/                     # API services
        ├── utils/                        # Helper functions
        ├── App.js                         # Main app component
        ├── index.js                       # Entry point
        ├── package.json                  # Node dependencies
        └── tailwind.config.js             # Tailwind configuration
```
---

## 📋 Prerequisites

- Python 3.8 or higher
- Node.js 16 or higher
- MySQL 8.0 or MariaDB 10.5 or higher
- Git
- npm or yarn

---

## 🚀 Installation

### 1️⃣ Clone the Repository

```bash
git clone https://github.com/yourusername/college-app.git
cd college-app
```
### 2️⃣ Backend Setup
```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
mysql -u root -p < models/new_schema.sql

# Optional sample data
python create_sample_data_final_v2.py
python app.py

Backend runs at:
http://localhost:5000
```
### 3️⃣ Frontend Setup
```bash
cd frontend
npm install
echo "REACT_APP_API_URL=http://localhost:5000/api" > .env
npm start

Frontend runs at:
http://localhost:3000
```

👤 Default Users
```bash
Role	Email	                 Password	Description
Admin	admin@yourcollege.edu    Admin@123  Full system access
	
Teacher	teacher@yourcollege.edu  Test@123	Dr. John Smith
	
Student	student@yourcollege.edu  Test@123	Jane Doe

```

📚 API Documentation
```bash
Authentication
POST   /api/auth/register
POST   /api/auth/login
POST   /api/auth/refresh
GET    /api/auth/profile
PUT    /api/auth/profile
PUT    /api/auth/change-password

Admin, Teacher, Student, and Notification endpoints are available under /api/.
```

📦 Building for Production
```bash
Backend (Linux/Mac)
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app

Backend (Windows)
pip install waitress
waitress-serve --port=5000 app:app

Frontend
npm run build
npx serve -s build -l 3000
```

🐛 Known Issues
```bash
Email verification requires SMTP configuration

File upload size limited to 50MB

Zoom integration requires manual link entry

Missing database tables may cause 500 errors
```

🗺️ Roadmap
```bash
Add email notifications

Implement Zoom API integration

Add real-time chat

Create React Native mobile app

Add analytics dashboard

Add PDF/Excel export functionality
```

👨‍💻 Author
```bash
Rabin Pant
GitHub: https://github.com/Rabin-Pant
```
<div align="center">

Made with ❤️ by Rabin Pant
⭐ Star this repository if you found it helpful!

</div> 
