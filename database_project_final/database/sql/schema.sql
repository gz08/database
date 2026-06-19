-- Schema for Student Management System (openGauss)
-- Keep core table names fixed:
-- roles, users, students, teachers, courses, enrollments, grades

BEGIN;

DROP TABLE IF EXISTS grades CASCADE;
DROP TABLE IF EXISTS enrollments CASCADE;
DROP TABLE IF EXISTS courses CASCADE;
DROP TABLE IF EXISTS teachers CASCADE;
DROP TABLE IF EXISTS students CASCADE;
DROP TABLE IF EXISTS users CASCADE;
DROP TABLE IF EXISTS roles CASCADE;

CREATE TABLE IF NOT EXISTS roles (
    id SERIAL PRIMARY KEY,
    role_name VARCHAR(20) NOT NULL UNIQUE,
    CONSTRAINT chk_roles_role_name
        CHECK (role_name IN ('admin', 'teacher', 'student'))
);

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role_id INTEGER NOT NULL REFERENCES roles(id),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS students (
    id SERIAL PRIMARY KEY,
    user_id INTEGER UNIQUE REFERENCES users(id),
    student_no VARCHAR(30) NOT NULL UNIQUE,
    full_name VARCHAR(100) NOT NULL,
    gender VARCHAR(10) NOT NULL,
    grade_year INTEGER NOT NULL,
    major VARCHAR(100) NOT NULL,
    phone VARCHAR(30),
    email VARCHAR(120),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_students_gender
        CHECK (gender IN ('M', 'F', 'Other')),
    CONSTRAINT chk_students_grade_year
        CHECK (grade_year BETWEEN 1 AND 8)
);

CREATE TABLE IF NOT EXISTS teachers (
    id SERIAL PRIMARY KEY,
    user_id INTEGER UNIQUE REFERENCES users(id),
    teacher_no VARCHAR(30) NOT NULL UNIQUE,
    full_name VARCHAR(100) NOT NULL,
    department VARCHAR(100) NOT NULL,
    phone VARCHAR(30),
    email VARCHAR(120),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS courses (
    id SERIAL PRIMARY KEY,
    course_code VARCHAR(30) NOT NULL UNIQUE,
    course_name VARCHAR(120) NOT NULL,
    course_outline VARCHAR(100),
    credits NUMERIC(3, 1) NOT NULL,
    teacher_id INTEGER REFERENCES teachers(id),
    capacity INTEGER NOT NULL DEFAULT 50,
    semester VARCHAR(30) NOT NULL,
    target_grade_year INTEGER NOT NULL DEFAULT 2,
    attendance_weight NUMERIC(5, 2) NOT NULL DEFAULT 10,
    experiment_weight NUMERIC(5, 2) NOT NULL DEFAULT 30,
    exam_weight NUMERIC(5, 2) NOT NULL DEFAULT 60,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_courses_credits
        CHECK (credits > 0 AND credits <= 10),
    CONSTRAINT chk_courses_capacity
        CHECK (capacity > 0),
    CONSTRAINT chk_courses_target_grade_year
        CHECK (target_grade_year BETWEEN 1 AND 8),
    CONSTRAINT chk_courses_attendance_weight
        CHECK (attendance_weight >= 0 AND attendance_weight <= 100),
    CONSTRAINT chk_courses_experiment_weight
        CHECK (experiment_weight >= 0 AND experiment_weight <= 100),
    CONSTRAINT chk_courses_exam_weight
        CHECK (exam_weight >= 0 AND exam_weight <= 100),
    CONSTRAINT chk_courses_weight_total
        CHECK (attendance_weight + experiment_weight + exam_weight = 100)
);

CREATE TABLE IF NOT EXISTS enrollments (
    id SERIAL PRIMARY KEY,
    student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    course_id INTEGER NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    status VARCHAR(20) NOT NULL DEFAULT 'enrolled',
    enrolled_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_enrollments_student_course UNIQUE (student_id, course_id),
    CONSTRAINT chk_enrollments_status
        CHECK (status IN ('enrolled', 'dropped'))
);

CREATE TABLE IF NOT EXISTS grades (
    id SERIAL PRIMARY KEY,
    enrollment_id INTEGER NOT NULL UNIQUE REFERENCES enrollments(id) ON DELETE CASCADE,
    teacher_id INTEGER REFERENCES teachers(id),
    attendance_score NUMERIC(5, 2) NOT NULL,
    experiment_score NUMERIC(5, 2) NOT NULL,
    exam_score NUMERIC(5, 2) NOT NULL,
    score NUMERIC(5, 2) NOT NULL,
    remarks VARCHAR(255),
    graded_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_grades_attendance_score
        CHECK (attendance_score >= 0 AND attendance_score <= 100),
    CONSTRAINT chk_grades_experiment_score
        CHECK (experiment_score >= 0 AND experiment_score <= 100),
    CONSTRAINT chk_grades_exam_score
        CHECK (exam_score >= 0 AND exam_score <= 100),
    CONSTRAINT chk_grades_score
        CHECK (score >= 0 AND score <= 100)
);

-- Indexes for common query paths (including fuzzy search fields)
CREATE INDEX IF NOT EXISTS idx_students_full_name ON students(full_name);
CREATE INDEX IF NOT EXISTS idx_students_student_no ON students(student_no);
CREATE INDEX IF NOT EXISTS idx_courses_course_name ON courses(course_name);
CREATE INDEX IF NOT EXISTS idx_courses_course_code ON courses(course_code);
CREATE INDEX IF NOT EXISTS idx_courses_target_grade_year ON courses(target_grade_year);
CREATE INDEX IF NOT EXISTS idx_enrollments_student_id ON enrollments(student_id);
CREATE INDEX IF NOT EXISTS idx_enrollments_course_id ON enrollments(course_id);
CREATE INDEX IF NOT EXISTS idx_grades_teacher_id ON grades(teacher_id);

COMMIT;
