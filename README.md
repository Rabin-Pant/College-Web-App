🎓 College Management System
<div align="center">






A full-stack College Management System with role-based access control for Admins, Teachers, and Students.
Built using Flask (Backend) and React (Frontend) with a MySQL database.

🚀 Features
 • 🛠 Tech Stack
 • ⚙️ Installation
 • 📚 API Documentation
 • 📦 Production Build

</div>
✨ Features
👑 Admin

Full system management & monitoring

Course & subject management

Section creation with capacity control

Assign teachers to sections

Approve/reject student enrollments

User management (create, verify, delete)

System-wide announcements

Analytics dashboard & reports

👨‍🏫 Teacher

View assigned sections

Upload study materials (PDF, PPT, video, links)

Create & publish assignments

Grade submissions with feedback

Take attendance (bulk support)

Schedule Zoom meetings

Approve enrollment requests

Send class notifications

Track student progress

👨‍🎓 Student

Browse & request enrollment

View enrolled sections

Access materials

Submit assignments (text + file upload)

View grades & feedback

Join Zoom meetings

Track attendance

Receive notifications

📱 Additional System Features

JWT Authentication

Optional Email Verification

Real-time notifications

File upload with progress tracking

Fully responsive design

Dark mode support

Calendar view for deadlines

Search & filtering system

🛠 Tech Stack
🔹 Backend

Python 3.13

Flask 2.3.3

Flask-JWT-Extended

Flask-CORS

Flask-MySQLdb

PyMySQL

bcrypt

python-dotenv

Werkzeug

🔹 Frontend

React 18

React Router 6

Tailwind CSS

Axios

React Hot Toast

React Dropzone

React DatePicker

Headless UI

Heroicons

🔹 Database

MySQL 8.0 / MariaDB 11.8

📋 Prerequisites

Python 3.8+

Node.js 16+

MySQL 8.0+ or MariaDB 10.5+

Git

npm or yarn

⚙️ Installation
1️⃣ Clone Repository
git clone https://github.com/yourusername/college-app.git
cd college-app

2️⃣ Backend Setup
cd backend

# Create virtual environment
python -m venv venv

# Activate
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env
cp .env.example .env


Update .env with your database credentials.

# Create database
mysql -u root -p < models/new_schema.sql

# (Optional) Add sample data
python create_sample_data_final_v2.py

# Run backend
python app.py


Backend runs on:

http://localhost:5000

3️⃣ Frontend Setup
cd frontend
npm install

# Create .env
echo "REACT_APP_API_URL=http://localhost:5000/api" > .env

npm start


Frontend runs on:

http://localhost:3000

👤 Default Test Accounts
Role	Email	Password
Admin	admin@yourcollege.edu
	Admin@123
Teacher	teacher@yourcollege.edu
	Test@123
Student	student@yourcollege.edu
	Test@123
📁 Project Structure
college-app/
│
├── backend/
│   ├── app.py
│   ├── config.py
│   ├── models/
│   ├── routes/
│   ├── utils/
│   └── requirements.txt
│
└── frontend/
    ├── public/
    ├── src/
    ├── package.json
    └── tailwind.config.js

📚 API Documentation
Authentication
POST   /api/auth/register
POST   /api/auth/login
POST   /api/auth/refresh
GET    /api/auth/profile
PUT    /api/auth/change-password

Admin
GET    /api/admin/users
POST   /api/admin/users
PUT    /api/admin/users/:id
DELETE /api/admin/users/:id
...

Teacher
GET    /api/teacher/sections
POST   /api/teacher/assignments
PUT    /api/teacher/grading/:id
...

Student
GET    /api/student/sections
POST   /api/student/enrollments
POST   /api/student/assignments/:id/submit
...


Full endpoint list available in project files.

🚦 Running Tests
Backend
cd backend
python -m pytest

Frontend
cd frontend
npm test

📦 Building for Production
Backend (Linux/Mac)
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app

Backend (Windows)
pip install waitress
waitress-serve --port=5000 app:app

Frontend
npm run build
npx serve -s build -l 3000

🗺️ Roadmap

Email notifications

Zoom API integration

Built-in video conferencing

React Native mobile app

Discussion forums

Real-time chat

Grade analytics dashboard

PDF/Excel export support

🐛 Known Issues

SMTP configuration required for email verification

File upload limit: 50MB

Zoom integration requires manual link

Missing DB tables may cause 500 errors

👨‍💻 Author

Rabin Pant
GitHub: https://github.com/Rabin-Pant

Email: rabinpant@194gmail.com

<div align="center">

Made with ❤️ by Rabin Pant
⭐ Star this repository if you found it helpful!

</div>
