-- ==========================================
-- NEW COLLEGE MANAGEMENT SYSTEM SCHEMA
-- Run this to replace old structure
-- ==========================================

USE college_app;

-- ==========================================
-- 1. COURSES (Programs like AI, Computing)
-- ==========================================
CREATE TABLE IF NOT EXISTS courses (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL UNIQUE,
    code VARCHAR(20) NOT NULL UNIQUE,
    description TEXT,
    department VARCHAR(100),
    duration_years INT DEFAULT 4,
    total_credits INT DEFAULT 120,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- ==========================================
-- 2. SUBJECTS (Classes like Java, Python)
-- ==========================================
CREATE TABLE IF NOT EXISTS subjects (
    id INT PRIMARY KEY AUTO_INCREMENT,
    course_id INT NOT NULL,
    code VARCHAR(20) NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    credits INT DEFAULT 3,
    semester INT, -- Which semester this subject belongs to (1-8)
    is_core BOOLEAN DEFAULT TRUE, -- Core or elective
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE,
    UNIQUE KEY unique_subject (course_id, code)
);

-- ==========================================
-- 3. SECTIONS (A, B, C with capacity)
-- ==========================================
CREATE TABLE IF NOT EXISTS sections (
    id INT PRIMARY KEY AUTO_INCREMENT,
    subject_id INT NOT NULL,
    name VARCHAR(10) NOT NULL, -- A, B, C, etc.
    academic_year VARCHAR(20) NOT NULL, -- 2024-2025
    semester VARCHAR(20) NOT NULL, -- Fall 2024, Spring 2025
    capacity INT DEFAULT 30,
    enrolled_count INT DEFAULT 0,
    room VARCHAR(50),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE CASCADE,
    UNIQUE KEY unique_section (subject_id, name, academic_year, semester)
);

-- ==========================================
-- 4. TEACHER ASSIGNMENTS (Which teacher teaches which section)
-- ==========================================
CREATE TABLE IF NOT EXISTS teacher_assignments (
    id INT PRIMARY KEY AUTO_INCREMENT,
    teacher_id INT NOT NULL,
    section_id INT NOT NULL,
    is_primary BOOLEAN DEFAULT TRUE, -- Primary instructor or assistant
    assigned_date DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (teacher_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (section_id) REFERENCES sections(id) ON DELETE CASCADE,
    UNIQUE KEY unique_assignment (teacher_id, section_id)
);

-- ==========================================
-- 5. STUDENT ENROLLMENTS (Students in sections)
-- ==========================================
CREATE TABLE IF NOT EXISTS enrollments (
    id INT PRIMARY KEY AUTO_INCREMENT,
    student_id INT NOT NULL,
    section_id INT NOT NULL,
    status ENUM('pending', 'approved', 'rejected', 'dropped') DEFAULT 'pending',
    enrollment_date DATE DEFAULT CURRENT_DATE,
    approved_by INT,
    approved_date DATE,
    grade_final DECIMAL(5,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (section_id) REFERENCES sections(id) ON DELETE CASCADE,
    FOREIGN KEY (approved_by) REFERENCES users(id) ON DELETE SET NULL,
    UNIQUE KEY unique_enrollment (student_id, section_id)
);

-- ==========================================
-- 6. SCHEDULE (Timetable)
-- ==========================================
CREATE TABLE IF NOT EXISTS schedules (
    id INT PRIMARY KEY AUTO_INCREMENT,
    section_id INT NOT NULL,
    day ENUM('Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday') NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    room VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (section_id) REFERENCES sections(id) ON DELETE CASCADE
);

-- ==========================================
-- 7. ZOOM MEETINGS (Online classes)
-- ==========================================
CREATE TABLE IF NOT EXISTS zoom_meetings (
    id INT PRIMARY KEY AUTO_INCREMENT,
    teacher_id INT NOT NULL,
    section_id INT NOT NULL,
    topic VARCHAR(200) NOT NULL,
    description TEXT,
    meeting_date DATE NOT NULL,
    start_time TIME NOT NULL,
    duration_minutes INT DEFAULT 60,
    meeting_link VARCHAR(500),
    meeting_id VARCHAR(100),
    password VARCHAR(100),
    recording_link VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (teacher_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (section_id) REFERENCES sections(id) ON DELETE CASCADE
);

-- ==========================================
-- 8. ATTENDANCE
-- ==========================================
CREATE TABLE IF NOT EXISTS attendance (
    id INT PRIMARY KEY AUTO_INCREMENT,
    section_id INT NOT NULL,
    student_id INT NOT NULL,
    date DATE NOT NULL,
    status ENUM('present', 'absent', 'late', 'excused') DEFAULT 'absent',
    marked_by INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (section_id) REFERENCES sections(id) ON DELETE CASCADE,
    FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (marked_by) REFERENCES users(id) ON DELETE SET NULL,
    UNIQUE KEY unique_attendance (section_id, student_id, date)
);

-- ==========================================
-- 9. UPDATE EXISTING TABLES
-- ==========================================

-- Add academic_year to assignments
ALTER TABLE assignments 
ADD COLUMN section_id INT AFTER class_id,
ADD COLUMN academic_year VARCHAR(20) AFTER section_id,
ADD FOREIGN KEY (section_id) REFERENCES sections(id) ON DELETE CASCADE;

-- Add section_id to materials
ALTER TABLE materials 
ADD COLUMN section_id INT AFTER class_id,
ADD FOREIGN KEY (section_id) REFERENCES sections(id) ON DELETE CASCADE;

-- ==========================================
-- 10. DEFAULT DATA
-- ==========================================

-- Insert default courses
INSERT IGNORE INTO courses (name, code, description, department, duration_years) VALUES
('Artificial Intelligence', 'AI', 'AI and Machine Learning program', 'Computing', 4),
('Computing', 'COMP', 'Computer Science program', 'Computing', 4),
('Networking', 'NET', 'Network Engineering program', 'Networking', 4),
('Multimedia', 'MM', 'Digital Media program', 'Multimedia', 4);

-- Insert subjects for AI course (course_id = 1)
INSERT IGNORE INTO subjects (course_id, code, name, credits, semester) VALUES
(1, 'AI101', 'Introduction to Python', 3, 1),
(1, 'AI102', 'Mathematics for AI', 3, 1),
(1, 'AI201', 'Data Structures', 3, 2),
(1, 'AI202', 'Machine Learning Basics', 3, 2),
(1, 'AI301', 'Deep Learning', 3, 3),
(1, 'AI302', 'Natural Language Processing', 3, 3),
(1, 'AI401', 'Computer Vision', 3, 4),
(1, 'AI402', 'AI Project', 3, 4);

-- Insert subjects for Computing course (course_id = 2)
INSERT IGNORE INTO subjects (course_id, code, name, credits, semester) VALUES
(2, 'CS101', 'Java Programming', 3, 1),
(2, 'CS102', 'Discrete Mathematics', 3, 1),
(2, 'CS201', 'Operating Systems', 3, 2),
(2, 'CS202', 'Database Systems', 3, 2),
(2, 'CS301', 'Software Engineering', 3, 3),
(2, 'CS302', 'Computer Networks', 3, 3),
(2, 'CS401', 'Information Security', 3, 4),
(2, 'CS402', 'Cloud Computing', 3, 4);

-- ==========================================
-- 11. VIEWS FOR EASY QUERYING
-- ==========================================

-- View available sections for students
CREATE OR REPLACE VIEW vw_available_sections AS
SELECT 
    s.id as section_id,
    s.name as section_name,
    sub.id as subject_id,
    sub.code as subject_code,
    sub.name as subject_name,
    sub.credits,
    sub.semester,
    c.id as course_id,
    c.name as course_name,
    c.code as course_code,
    s.academic_year,
    s.semester as academic_semester,
    s.capacity,
    s.enrolled_count,
    (s.capacity - s.enrolled_count) as available_seats,
    u.id as teacher_id,
    u.name as teacher_name
FROM sections s
JOIN subjects sub ON s.subject_id = sub.id
JOIN courses c ON sub.course_id = c.id
JOIN teacher_assignments ta ON s.id = ta.section_id
JOIN users u ON ta.teacher_id = u.id
WHERE s.is_active = TRUE 
  AND s.enrolled_count < s.capacity;

-- View student enrolled classes
CREATE OR REPLACE VIEW vw_student_classes AS
SELECT 
    e.id as enrollment_id,
    e.student_id,
    e.status as enrollment_status,
    e.enrollment_date,
    s.id as section_id,
    s.name as section_name,
    sub.id as subject_id,
    sub.code as subject_code,
    sub.name as subject_name,
    sub.credits,
    c.id as course_id,
    c.name as course_name,
    s.academic_year,
    s.semester as academic_semester,
    sch.day,
    sch.start_time,
    sch.end_time,
    sch.room,
    u.id as teacher_id,
    u.name as teacher_name
FROM enrollments e
JOIN sections s ON e.section_id = s.id
JOIN subjects sub ON s.subject_id = sub.id
JOIN courses c ON sub.course_id = c.id
LEFT JOIN schedules sch ON s.id = sch.section_id
LEFT JOIN teacher_assignments ta ON s.id = ta.section_id
LEFT JOIN users u ON ta.teacher_id = u.id
WHERE e.status = 'approved';

-- View teacher assigned classes
CREATE OR REPLACE VIEW vw_teacher_classes AS
SELECT 
    ta.id as assignment_id,
    ta.teacher_id,
    s.id as section_id,
    s.name as section_name,
    sub.id as subject_id,
    sub.code as subject_code,
    sub.name as subject_name,
    sub.credits,
    c.id as course_id,
    c.name as course_name,
    c.code as course_code,
    s.academic_year,
    s.semester as academic_semester,
    s.capacity,
    s.enrolled_count,
    sch.day,
    sch.start_time,
    sch.end_time,
    sch.room,
    COUNT(e.id) as enrolled_students
FROM teacher_assignments ta
JOIN sections s ON ta.section_id = s.id
JOIN subjects sub ON s.subject_id = sub.id
JOIN courses c ON sub.course_id = c.id
LEFT JOIN schedules sch ON s.id = sch.section_id
LEFT JOIN enrollments e ON s.id = e.section_id AND e.status = 'approved'
GROUP BY ta.id;

-- ==========================================
-- 12. INDEXES FOR PERFORMANCE
-- ==========================================

CREATE INDEX idx_enrollments_student ON enrollments(student_id, status);
CREATE INDEX idx_enrollments_section ON enrollments(section_id, status);
CREATE INDEX idx_teacher_assignments_teacher ON teacher_assignments(teacher_id);
CREATE INDEX idx_schedules_section ON schedules(section_id);
CREATE INDEX idx_zoom_section ON zoom_meetings(section_id);
CREATE INDEX idx_attendance_section_date ON attendance(section_id, date);