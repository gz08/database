-- Final demo seed data for Student Management System (openGauss)
-- Accounts:
-- admin_demo   / admin123
-- teacher_demo / teacher123
-- student_demo / student123
-- g2_student02 / student123
-- g2_student03 / student123
-- g2_student04 / student123
-- g2_student05 / student123
-- g2_student06 / student123
-- g2_student07 / student123
-- g2_student08 / student123
-- g2_student09 / student123
-- g2_student10 / student123
-- grade1_demo  / student123
-- CSE204 is a Grade 2 course without enrollments or grades for enroll/drop demo.

BEGIN;

INSERT INTO roles (role_name)
VALUES
    ('admin'),
    ('teacher'),
    ('student');

INSERT INTO users (username, password_hash, role_id, is_active)
VALUES
    (
        'admin_demo',
        '240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9',
        (SELECT id FROM roles WHERE role_name = 'admin'),
        TRUE
    ),
    (
        'teacher_demo',
        'cde383eee8ee7a4400adf7a15f716f179a2eb97646b37e089eb8d6d04e663416',
        (SELECT id FROM roles WHERE role_name = 'teacher'),
        TRUE
    ),
    (
        'student_demo',
        '703b0a3d6ad75b649a28adde7d83c6251da457549263bc7ff45ec709b0a8448b',
        (SELECT id FROM roles WHERE role_name = 'student'),
        TRUE
    ),
    (
        'g2_student02',
        '703b0a3d6ad75b649a28adde7d83c6251da457549263bc7ff45ec709b0a8448b',
        (SELECT id FROM roles WHERE role_name = 'student'),
        TRUE
    ),
    (
        'g2_student03',
        '703b0a3d6ad75b649a28adde7d83c6251da457549263bc7ff45ec709b0a8448b',
        (SELECT id FROM roles WHERE role_name = 'student'),
        TRUE
    ),
    (
        'g2_student04',
        '703b0a3d6ad75b649a28adde7d83c6251da457549263bc7ff45ec709b0a8448b',
        (SELECT id FROM roles WHERE role_name = 'student'),
        TRUE
    ),
    (
        'g2_student05',
        '703b0a3d6ad75b649a28adde7d83c6251da457549263bc7ff45ec709b0a8448b',
        (SELECT id FROM roles WHERE role_name = 'student'),
        TRUE
    ),
    (
        'g2_student06',
        '703b0a3d6ad75b649a28adde7d83c6251da457549263bc7ff45ec709b0a8448b',
        (SELECT id FROM roles WHERE role_name = 'student'),
        TRUE
    ),
    (
        'g2_student07',
        '703b0a3d6ad75b649a28adde7d83c6251da457549263bc7ff45ec709b0a8448b',
        (SELECT id FROM roles WHERE role_name = 'student'),
        TRUE
    ),
    (
        'g2_student08',
        '703b0a3d6ad75b649a28adde7d83c6251da457549263bc7ff45ec709b0a8448b',
        (SELECT id FROM roles WHERE role_name = 'student'),
        TRUE
    ),
    (
        'g2_student09',
        '703b0a3d6ad75b649a28adde7d83c6251da457549263bc7ff45ec709b0a8448b',
        (SELECT id FROM roles WHERE role_name = 'student'),
        TRUE
    ),
    (
        'g2_student10',
        '703b0a3d6ad75b649a28adde7d83c6251da457549263bc7ff45ec709b0a8448b',
        (SELECT id FROM roles WHERE role_name = 'student'),
        TRUE
    ),
    (
        'grade1_demo',
        '703b0a3d6ad75b649a28adde7d83c6251da457549263bc7ff45ec709b0a8448b',
        (SELECT id FROM roles WHERE role_name = 'student'),
        TRUE
    );

INSERT INTO teachers (user_id, teacher_no, full_name, department, phone, email)
VALUES (
    (SELECT id FROM users WHERE username = 'teacher_demo'),
    'TCH2024001',
    'Tom Teacher',
    'Computer Science',
    '13800000011',
    'teacher_demo@example.com'
);

INSERT INTO students (
    user_id,
    student_no,
    full_name,
    gender,
    grade_year,
    major,
    phone,
    email
)
VALUES
    (
        (SELECT id FROM users WHERE username = 'student_demo'),
        'STU2024001',
        'Alice Demo',
        'F',
        2,
        'Computer Science',
        '13800000021',
        'STU2024001@edu'
    ),
    (
        (SELECT id FROM users WHERE username = 'g2_student02'),
        'STU2024002',
        'Brian Excellent',
        'M',
        2,
        'Computer Science',
        '13800000022',
        'STU2024002@edu'
    ),
    (
        (SELECT id FROM users WHERE username = 'g2_student03'),
        'STU2024003',
        'Cathy Excellent',
        'F',
        2,
        'Computer Science',
        '13800000023',
        'STU2024003@edu'
    ),
    (
        (SELECT id FROM users WHERE username = 'g2_student04'),
        'STU2024004',
        'David Stable',
        'M',
        2,
        'Computer Science',
        '13800000024',
        'STU2024004@edu'
    ),
    (
        (SELECT id FROM users WHERE username = 'g2_student05'),
        'STU2024005',
        'Ella Stable',
        'F',
        2,
        'Computer Science',
        '13800000025',
        'STU2024005@edu'
    ),
    (
        (SELECT id FROM users WHERE username = 'g2_student06'),
        'STU2024006',
        'Frank Stable',
        'M',
        2,
        'Computer Science',
        '13800000026',
        'STU2024006@edu'
    ),
    (
        (SELECT id FROM users WHERE username = 'g2_student07'),
        'STU2024007',
        'Gina LabWeak',
        'F',
        2,
        'Computer Science',
        '13800000027',
        'STU2024007@edu'
    ),
    (
        (SELECT id FROM users WHERE username = 'g2_student08'),
        'STU2024008',
        'Henry LabWeak',
        'M',
        2,
        'Computer Science',
        '13800000028',
        'STU2024008@edu'
    ),
    (
        (SELECT id FROM users WHERE username = 'g2_student09'),
        'STU2024009',
        'Ivy LowAttendance',
        'F',
        2,
        'Computer Science',
        '13800000029',
        'STU2024009@edu'
    ),
    (
        (SELECT id FROM users WHERE username = 'g2_student10'),
        'STU2024010',
        'Jack Risk',
        'M',
        2,
        'Computer Science',
        '13800000030',
        'STU2024010@edu'
    ),
    (
        (SELECT id FROM users WHERE username = 'grade1_demo'),
        'STU2025001',
        'Grace Freshman',
        'F',
        1,
        'Computer Science',
        '13800000031',
        'STU2025001@edu'
    );

INSERT INTO courses (
    course_code,
    course_name,
    course_outline,
    credits,
    teacher_id,
    capacity,
    semester,
    target_grade_year,
    attendance_weight,
    experiment_weight,
    exam_weight
)
VALUES
    (
        'CSE201',
        'Database Systems',
        'Relational design, SQL, transactions, and openGauss practice.',
        3.0,
        (SELECT id FROM teachers WHERE teacher_no = 'TCH2024001'),
        60,
        '2026-Spring',
        2,
        10,
        30,
        60
    ),
    (
        'CSE202',
        'Python Programming',
        'Python syntax, files, functions, data handling, and small projects.',
        2.5,
        (SELECT id FROM teachers WHERE teacher_no = 'TCH2024001'),
        60,
        '2026-Spring',
        2,
        10,
        30,
        60
    ),
    (
        'CSE203',
        'Data Structures',
        'Lists, stacks, queues, trees, graphs, and algorithm basics.',
        3.0,
        (SELECT id FROM teachers WHERE teacher_no = 'TCH2024001'),
        60,
        '2026-Spring',
        2,
        10,
        30,
        60
    ),
    (
        'CSE204',
        'Software Testing Practice',
        'Test cases, boundary values, defect reports, and simple QA workflow.',
        2.0,
        (SELECT id FROM teachers WHERE teacher_no = 'TCH2024001'),
        60,
        '2026-Spring',
        2,
        10,
        30,
        60
    ),
    (
        'CSE101',
        'Introduction to Computing',
        'Computing concepts, basic tools, and introductory problem solving.',
        2.0,
        (SELECT id FROM teachers WHERE teacher_no = 'TCH2024001'),
        50,
        '2026-Spring',
        1,
        10,
        30,
        60
    );

INSERT INTO enrollments (student_id, course_id, status)
SELECT
    s.id,
    c.id,
    'enrolled'
FROM students s
JOIN courses c ON c.target_grade_year = s.grade_year
WHERE c.course_code <> 'CSE204';

WITH grade_seed (
    student_no,
    course_code,
    attendance_score,
    experiment_score,
    exam_score,
    final_score,
    remarks
) AS (
    VALUES
        ('STU2024001', 'CSE201', 95.0, 92.0, 88.0, 90.5, 'Main demo student: strong database foundation.'),
        ('STU2024001', 'CSE202', 88.0, 80.0, 76.0, 78.4, 'Main demo student: programming is steady but needs practice.'),
        ('STU2024001', 'CSE203', 86.0, 70.0, 62.0, 67.6, 'Main demo student: data structures need focused support.'),
        ('STU2024002', 'CSE201', 96.0, 95.0, 94.0, 94.5, 'Excellent student with balanced performance.'),
        ('STU2024002', 'CSE202', 94.0, 96.0, 93.0, 94.2, 'Excellent student with strong programming labs.'),
        ('STU2024002', 'CSE203', 98.0, 94.0, 95.0, 95.0, 'Excellent student with high exam accuracy.'),
        ('STU2024003', 'CSE201', 92.0, 94.0, 90.0, 91.4, 'Excellent student with practical strength.'),
        ('STU2024003', 'CSE202', 95.0, 92.0, 91.0, 92.3, 'Excellent student and stable coder.'),
        ('STU2024003', 'CSE203', 93.0, 95.0, 89.0, 91.2, 'Excellent student with strong lab work.'),
        ('STU2024004', 'CSE201', 88.0, 84.0, 82.0, 83.0, 'Stable student with consistent progress.'),
        ('STU2024004', 'CSE202', 86.0, 83.0, 80.0, 81.5, 'Stable student with room for exam improvement.'),
        ('STU2024004', 'CSE203', 85.0, 82.0, 78.0, 79.7, 'Stable student near the class average.'),
        ('STU2024005', 'CSE201', 84.0, 82.0, 79.0, 80.1, 'Stable student with normal learning pace.'),
        ('STU2024005', 'CSE202', 86.0, 80.0, 78.0, 79.4, 'Stable student with balanced skills.'),
        ('STU2024005', 'CSE203', 82.0, 81.0, 76.0, 78.1, 'Stable student needs more algorithm drills.'),
        ('STU2024006', 'CSE201', 90.0, 80.0, 75.0, 78.0, 'Stable student; exam score limits the final grade.'),
        ('STU2024006', 'CSE202', 88.0, 78.0, 74.0, 77.0, 'Stable student needs review before exams.'),
        ('STU2024006', 'CSE203', 86.0, 79.0, 73.0, 76.3, 'Stable student should strengthen core concepts.'),
        ('STU2024007', 'CSE201', 90.0, 62.0, 82.0, 76.8, 'Experiment weak student with acceptable exams.'),
        ('STU2024007', 'CSE202', 88.0, 60.0, 80.0, 74.8, 'Experiment weak student needs lab support.'),
        ('STU2024007', 'CSE203', 86.0, 58.0, 78.0, 72.8, 'Experiment weak student shows repeated lab difficulty.'),
        ('STU2024008', 'CSE201', 84.0, 55.0, 78.0, 71.7, 'Experiment weak student; lab tasks are the key issue.'),
        ('STU2024008', 'CSE202', 82.0, 57.0, 76.0, 70.9, 'Experiment weak student needs coding practice.'),
        ('STU2024008', 'CSE203', 85.0, 54.0, 75.0, 69.7, 'Experiment weak student is close to risk level.'),
        ('STU2024009', 'CSE201', 55.0, 88.0, 84.0, 82.3, 'Low attendance but strong assignments and exams.'),
        ('STU2024009', 'CSE202', 58.0, 85.0, 82.0, 80.5, 'Low attendance pattern should be monitored.'),
        ('STU2024009', 'CSE203', 60.0, 82.0, 80.0, 78.6, 'Low attendance affects participation.'),
        ('STU2024010', 'CSE201', 72.0, 60.0, 58.0, 60.0, 'Risk student with weak labs and exams.'),
        ('STU2024010', 'CSE202', 70.0, 58.0, 55.0, 57.4, 'Risk student needs targeted programming support.'),
        ('STU2024010', 'CSE203', 68.0, 55.0, 52.0, 54.5, 'Risk student needs immediate intervention.'),
        ('STU2025001', 'CSE101', 90.0, 86.0, 82.0, 84.0, 'Grade 1 demo student for course-level filtering.')
)
INSERT INTO grades (
    enrollment_id,
    teacher_id,
    attendance_score,
    experiment_score,
    exam_score,
    score,
    remarks
)
SELECT
    e.id,
    t.id,
    g.attendance_score,
    g.experiment_score,
    g.exam_score,
    g.final_score,
    g.remarks
FROM grade_seed g
JOIN students s ON s.student_no = g.student_no
JOIN courses c ON c.course_code = g.course_code
JOIN enrollments e ON e.student_id = s.id AND e.course_id = c.id
JOIN teachers t ON t.teacher_no = 'TCH2024001';

COMMIT;
