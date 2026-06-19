from typing import Any, Optional

from core.db import execute_query, get_cursor


def _row_to_dict(row: Any) -> Optional[dict[str, Any]]:
    if row is None:
        return None
    return dict(row)


def _rows_to_dicts(rows: list[Any]) -> list[dict[str, Any]]:
    return [dict(row) for row in rows]


# ----------------------------
# User Queries
# ----------------------------
def get_user_by_id(user_id: int) -> Optional[dict[str, Any]]:
    sql = """
    SELECT
        u.id,
        u.username,
        u.password_hash,
        u.role_id,
        r.role_name,
        u.is_active,
        u.created_at,
        u.updated_at
    FROM users u
    JOIN roles r ON r.id = u.role_id
    WHERE u.id = %s
    """
    row = execute_query(sql, (user_id,), fetchone=True)
    return _row_to_dict(row)


def get_user_by_username(username: str) -> Optional[dict[str, Any]]:
    sql = """
    SELECT
        u.id,
        u.username,
        u.password_hash,
        u.role_id,
        r.role_name,
        u.is_active,
        u.created_at,
        u.updated_at
    FROM users u
    JOIN roles r ON r.id = u.role_id
    WHERE u.username = %s
    """
    row = execute_query(sql, (username,), fetchone=True)
    return _row_to_dict(row)


def list_users(
    keyword: Optional[str] = None,
    role_name: Optional[str] = None,
    is_active: Optional[bool] = None,
) -> list[dict[str, Any]]:
    sql = """
    SELECT
        u.id,
        u.username,
        u.role_id,
        r.role_name,
        u.is_active,
        u.created_at,
        u.updated_at
    FROM users u
    JOIN roles r ON r.id = u.role_id
    """
    conditions: list[str] = []
    params: list[Any] = []

    if keyword:
        pattern = f"%{keyword.strip()}%"
        conditions.append("LOWER(u.username) LIKE LOWER(%s)")
        params.append(pattern)

    if role_name:
        conditions.append("r.role_name = %s")
        params.append(role_name)

    if is_active is not None:
        conditions.append("u.is_active = %s")
        params.append(is_active)

    if conditions:
        sql += " WHERE " + " AND ".join(conditions)

    sql += " ORDER BY u.id"
    rows = execute_query(sql, tuple(params))
    return _rows_to_dicts(rows)


def create_user(
    username: str,
    password_hash: str,
    role_name: str,
    is_active: bool = True,
) -> dict[str, Any]:
    sql = """
    INSERT INTO users (username, password_hash, role_id, is_active)
    VALUES (
        %s,
        %s,
        (SELECT id FROM roles WHERE role_name = %s),
        %s
    )
    RETURNING id
    """
    with get_cursor(dict_cursor=True) as (_, cursor):
        cursor.execute(sql, (username, password_hash, role_name, is_active))
        new_id = cursor.fetchone()["id"]
    return get_user_by_id(new_id)  # type: ignore[arg-type]


def update_user_password(user_id: int, password_hash: str) -> Optional[dict[str, Any]]:
    sql = """
    UPDATE users
    SET
        password_hash = %s,
        updated_at = CURRENT_TIMESTAMP
    WHERE id = %s
    """
    with get_cursor(dict_cursor=False) as (_, cursor):
        cursor.execute(sql, (password_hash, user_id))
    return get_user_by_id(user_id)


def update_user_active_status(user_id: int, is_active: bool) -> Optional[dict[str, Any]]:
    sql = """
    UPDATE users
    SET
        is_active = %s,
        updated_at = CURRENT_TIMESTAMP
    WHERE id = %s
    """
    with get_cursor(dict_cursor=False) as (_, cursor):
        cursor.execute(sql, (is_active, user_id))
    return get_user_by_id(user_id)


def delete_user_account(user_id: int) -> int:
    with get_cursor(dict_cursor=False) as (_, cursor):
        cursor.execute("UPDATE students SET user_id = NULL WHERE user_id = %s", (user_id,))
        cursor.execute("UPDATE teachers SET user_id = NULL WHERE user_id = %s", (user_id,))
        cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
        return cursor.rowcount


# ----------------------------
# Student CRUD
# ----------------------------
def get_student_by_id(student_id: int) -> Optional[dict[str, Any]]:
    sql = """
    SELECT
        s.*,
        u.username,
        u.is_active AS user_is_active
    FROM students s
    LEFT JOIN users u ON u.id = s.user_id
    WHERE s.id = %s
    """
    row = execute_query(sql, (student_id,), fetchone=True)
    return _row_to_dict(row)


def get_student_by_student_no(student_no: str) -> Optional[dict[str, Any]]:
    sql = """
    SELECT
        s.*,
        u.username,
        u.is_active AS user_is_active
    FROM students s
    LEFT JOIN users u ON u.id = s.user_id
    WHERE s.student_no = %s
    """
    row = execute_query(sql, (student_no,), fetchone=True)
    return _row_to_dict(row)


def get_student_by_user_id(user_id: int) -> Optional[dict[str, Any]]:
    sql = """
    SELECT
        s.*,
        u.username,
        u.is_active AS user_is_active
    FROM students s
    JOIN users u ON u.id = s.user_id
    WHERE s.user_id = %s
    """
    row = execute_query(sql, (user_id,), fetchone=True)
    return _row_to_dict(row)


def list_students(keyword: Optional[str] = None) -> list[dict[str, Any]]:
    sql = """
    SELECT
        s.*,
        u.username,
        u.is_active AS user_is_active
    FROM students s
    LEFT JOIN users u ON u.id = s.user_id
    """
    params: list[Any] = []
    if keyword:
        pattern = f"%{keyword.strip()}%"
        sql += """
        WHERE
            LOWER(s.full_name) LIKE LOWER(%s)
            OR LOWER(s.student_no) LIKE LOWER(%s)
            OR LOWER(s.major) LIKE LOWER(%s)
        """
        params.extend([pattern, pattern, pattern])
    sql += " ORDER BY s.id"
    rows = execute_query(sql, tuple(params))
    return _rows_to_dicts(rows)


def create_student(
    student_no: str,
    full_name: str,
    gender: str,
    grade_year: int,
    major: str,
    phone: Optional[str] = None,
    email: Optional[str] = None,
    user_id: Optional[int] = None,
) -> dict[str, Any]:
    sql = """
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
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    RETURNING id
    """
    with get_cursor(dict_cursor=True) as (_, cursor):
        cursor.execute(
            sql,
            (user_id, student_no, full_name, gender, grade_year, major, phone, email),
        )
        new_id = cursor.fetchone()["id"]
    return get_student_by_id(new_id)  # type: ignore[arg-type]


def bind_student_user(student_id: int, user_id: int) -> Optional[dict[str, Any]]:
    sql = """
    UPDATE students
    SET
        user_id = %s,
        updated_at = CURRENT_TIMESTAMP
    WHERE id = %s
    """
    with get_cursor(dict_cursor=False) as (_, cursor):
        cursor.execute(sql, (user_id, student_id))
    return get_student_by_id(student_id)


def create_student_account(
    username: str,
    password_hash: str,
    student_no: str,
    is_active: bool = True,
) -> dict[str, Any]:
    with get_cursor(dict_cursor=True) as (_, cursor):
        cursor.execute(
            """
            SELECT id, user_id
            FROM students
            WHERE student_no = %s
            FOR UPDATE
            """,
            (student_no,),
        )
        student = cursor.fetchone()
        if not student:
            raise ValueError("Student No does not exist.")
        if student["user_id"] is not None:
            raise ValueError("This student already has a login account.")

        cursor.execute(
            """
            INSERT INTO users (username, password_hash, role_id, is_active)
            VALUES (
                %s,
                %s,
                (SELECT id FROM roles WHERE role_name = 'student'),
                %s
            )
            RETURNING id
            """,
            (username, password_hash, is_active),
        )
        new_user_id = cursor.fetchone()["id"]

        cursor.execute(
            """
            UPDATE students
            SET
                user_id = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
            """,
            (new_user_id, student["id"]),
        )

    return get_user_by_id(new_user_id)  # type: ignore[arg-type]


def update_student(
    student_id: int,
    full_name: Optional[str] = None,
    gender: Optional[str] = None,
    grade_year: Optional[int] = None,
    major: Optional[str] = None,
    phone: Optional[str] = None,
    email: Optional[str] = None,
) -> Optional[dict[str, Any]]:
    fields: list[str] = []
    params: list[Any] = []

    if full_name is not None:
        fields.append("full_name = %s")
        params.append(full_name)
    if gender is not None:
        fields.append("gender = %s")
        params.append(gender)
    if grade_year is not None:
        fields.append("grade_year = %s")
        params.append(grade_year)
    if major is not None:
        fields.append("major = %s")
        params.append(major)
    if phone is not None:
        fields.append("phone = %s")
        params.append(phone)
    if email is not None:
        fields.append("email = %s")
        params.append(email)

    if not fields:
        return get_student_by_id(student_id)

    sql = f"""
    UPDATE students
    SET
        {", ".join(fields)},
        updated_at = CURRENT_TIMESTAMP
    WHERE id = %s
    """
    params.append(student_id)
    with get_cursor(dict_cursor=False) as (_, cursor):
        cursor.execute(sql, tuple(params))
    return get_student_by_id(student_id)


def delete_student(student_id: int) -> int:
    sql = "DELETE FROM students WHERE id = %s"
    with get_cursor(dict_cursor=False) as (_, cursor):
        cursor.execute(sql, (student_id,))
        return cursor.rowcount


# ----------------------------
# Teacher Queries
# ----------------------------
def get_teacher_by_id(teacher_id: int) -> Optional[dict[str, Any]]:
    sql = """
    SELECT
        t.*,
        u.username,
        u.is_active AS user_is_active
    FROM teachers t
    LEFT JOIN users u ON u.id = t.user_id
    WHERE t.id = %s
    """
    row = execute_query(sql, (teacher_id,), fetchone=True)
    return _row_to_dict(row)


def get_teacher_by_user_id(user_id: int) -> Optional[dict[str, Any]]:
    sql = """
    SELECT
        t.*,
        u.username,
        u.is_active AS user_is_active
    FROM teachers t
    LEFT JOIN users u ON u.id = t.user_id
    WHERE t.user_id = %s
    """
    row = execute_query(sql, (user_id,), fetchone=True)
    return _row_to_dict(row)


def list_teachers(keyword: Optional[str] = None) -> list[dict[str, Any]]:
    sql = """
    SELECT
        t.*,
        u.username,
        u.is_active AS user_is_active
    FROM teachers t
    LEFT JOIN users u ON u.id = t.user_id
    """
    params: list[Any] = []
    if keyword:
        pattern = f"%{keyword.strip()}%"
        sql += """
        WHERE
            LOWER(t.full_name) LIKE LOWER(%s)
            OR LOWER(t.teacher_no) LIKE LOWER(%s)
            OR LOWER(t.department) LIKE LOWER(%s)
        """
        params.extend([pattern, pattern, pattern])
    sql += " ORDER BY t.id"
    rows = execute_query(sql, tuple(params))
    return _rows_to_dicts(rows)


# ----------------------------
# Course CRUD
# ----------------------------
def get_course_by_id(course_id: int) -> Optional[dict[str, Any]]:
    sql = """
    SELECT
        c.*,
        t.full_name AS teacher_name
    FROM courses c
    LEFT JOIN teachers t ON t.id = c.teacher_id
    WHERE c.id = %s
    """
    row = execute_query(sql, (course_id,), fetchone=True)
    return _row_to_dict(row)


def get_course_by_code(course_code: str) -> Optional[dict[str, Any]]:
    sql = """
    SELECT
        c.*,
        t.full_name AS teacher_name
    FROM courses c
    LEFT JOIN teachers t ON t.id = c.teacher_id
    WHERE c.course_code = %s
    """
    row = execute_query(sql, (course_code,), fetchone=True)
    return _row_to_dict(row)


def list_courses(
    keyword: Optional[str] = None,
    semester: Optional[str] = None,
    teacher_id: Optional[int] = None,
    target_grade_year: Optional[int] = None,
) -> list[dict[str, Any]]:
    sql = """
    SELECT
        c.*,
        t.full_name AS teacher_name
    FROM courses c
    LEFT JOIN teachers t ON t.id = c.teacher_id
    """
    conditions: list[str] = []
    params: list[Any] = []

    if keyword:
        pattern = f"%{keyword.strip()}%"
        conditions.append(
            "(LOWER(c.course_name) LIKE LOWER(%s) OR LOWER(c.course_code) LIKE LOWER(%s))"
        )
        params.extend([pattern, pattern])

    if semester:
        conditions.append("c.semester = %s")
        params.append(semester)

    if teacher_id is not None:
        conditions.append("c.teacher_id = %s")
        params.append(teacher_id)

    if target_grade_year is not None:
        conditions.append("c.target_grade_year = %s")
        params.append(target_grade_year)

    if conditions:
        sql += " WHERE " + " AND ".join(conditions)

    sql += " ORDER BY c.id"
    rows = execute_query(sql, tuple(params))
    return _rows_to_dicts(rows)


def create_course(
    course_code: str,
    course_name: str,
    credits: float,
    semester: str,
    course_outline: Optional[str] = None,
    teacher_id: Optional[int] = None,
    capacity: int = 50,
    target_grade_year: int = 2,
    attendance_weight: float = 10,
    experiment_weight: float = 30,
    exam_weight: float = 60,
) -> dict[str, Any]:
    sql = """
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
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    RETURNING id
    """
    with get_cursor(dict_cursor=True) as (_, cursor):
        cursor.execute(
            sql,
            (
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
                exam_weight,
            ),
        )
        new_id = cursor.fetchone()["id"]
    return get_course_by_id(new_id)  # type: ignore[arg-type]


def update_course(
    course_id: int,
    course_name: Optional[str] = None,
    course_outline: Optional[str] = None,
    credits: Optional[float] = None,
    teacher_id: Optional[int] = None,
    capacity: Optional[int] = None,
    semester: Optional[str] = None,
    target_grade_year: Optional[int] = None,
    attendance_weight: Optional[float] = None,
    experiment_weight: Optional[float] = None,
    exam_weight: Optional[float] = None,
) -> Optional[dict[str, Any]]:
    fields: list[str] = []
    params: list[Any] = []

    if course_name is not None:
        fields.append("course_name = %s")
        params.append(course_name)
    if course_outline is not None:
        fields.append("course_outline = %s")
        params.append(course_outline)
    if credits is not None:
        fields.append("credits = %s")
        params.append(credits)
    if teacher_id is not None:
        fields.append("teacher_id = %s")
        params.append(teacher_id)
    if capacity is not None:
        fields.append("capacity = %s")
        params.append(capacity)
    if semester is not None:
        fields.append("semester = %s")
        params.append(semester)
    if target_grade_year is not None:
        fields.append("target_grade_year = %s")
        params.append(target_grade_year)
    if attendance_weight is not None:
        fields.append("attendance_weight = %s")
        params.append(attendance_weight)
    if experiment_weight is not None:
        fields.append("experiment_weight = %s")
        params.append(experiment_weight)
    if exam_weight is not None:
        fields.append("exam_weight = %s")
        params.append(exam_weight)

    if not fields:
        return get_course_by_id(course_id)

    sql = f"""
    UPDATE courses
    SET
        {", ".join(fields)},
        updated_at = CURRENT_TIMESTAMP
    WHERE id = %s
    """
    params.append(course_id)
    with get_cursor(dict_cursor=False) as (_, cursor):
        cursor.execute(sql, tuple(params))
    return get_course_by_id(course_id)


def assign_course_teacher(course_id: int, teacher_id: Optional[int]) -> Optional[dict[str, Any]]:
    sql = """
    UPDATE courses
    SET
        teacher_id = %s,
        updated_at = CURRENT_TIMESTAMP
    WHERE id = %s
    """
    with get_cursor(dict_cursor=False) as (_, cursor):
        cursor.execute(sql, (teacher_id, course_id))
    return get_course_by_id(course_id)


def delete_course(course_id: int) -> int:
    sql = "DELETE FROM courses WHERE id = %s"
    with get_cursor(dict_cursor=False) as (_, cursor):
        cursor.execute(sql, (course_id,))
        return cursor.rowcount


# ----------------------------
# Enrollment Management
# ----------------------------
def get_enrollment_by_id(enrollment_id: int) -> Optional[dict[str, Any]]:
    sql = """
    SELECT
        e.*,
        s.student_no,
        s.full_name AS student_name,
        c.course_code,
        c.course_name
    FROM enrollments e
    JOIN students s ON s.id = e.student_id
    JOIN courses c ON c.id = e.course_id
    WHERE e.id = %s
    """
    row = execute_query(sql, (enrollment_id,), fetchone=True)
    return _row_to_dict(row)


def get_enrollment_by_student_course(student_id: int, course_id: int) -> Optional[dict[str, Any]]:
    sql = """
    SELECT
        e.*,
        s.student_no,
        s.full_name AS student_name,
        c.course_code,
        c.course_name
    FROM enrollments e
    JOIN students s ON s.id = e.student_id
    JOIN courses c ON c.id = e.course_id
    WHERE e.student_id = %s AND e.course_id = %s
    """
    row = execute_query(sql, (student_id, course_id), fetchone=True)
    return _row_to_dict(row)


def list_enrollments(
    student_id: Optional[int] = None,
    course_id: Optional[int] = None,
    status: Optional[str] = None,
) -> list[dict[str, Any]]:
    sql = """
    SELECT
        e.*,
        s.student_no,
        s.full_name AS student_name,
        c.course_code,
        c.course_name
    FROM enrollments e
    JOIN students s ON s.id = e.student_id
    JOIN courses c ON c.id = e.course_id
    """
    conditions: list[str] = []
    params: list[Any] = []

    if student_id is not None:
        conditions.append("e.student_id = %s")
        params.append(student_id)
    if course_id is not None:
        conditions.append("e.course_id = %s")
        params.append(course_id)
    if status:
        conditions.append("e.status = %s")
        params.append(status)

    if conditions:
        sql += " WHERE " + " AND ".join(conditions)
    sql += " ORDER BY e.id"
    rows = execute_query(sql, tuple(params))
    return _rows_to_dicts(rows)


def create_enrollment(student_id: int, course_id: int, status: str = "enrolled") -> dict[str, Any]:
    sql = """
    INSERT INTO enrollments (student_id, course_id, status)
    VALUES (%s, %s, %s)
    RETURNING id
    """
    with get_cursor(dict_cursor=True) as (_, cursor):
        cursor.execute(sql, (student_id, course_id, status))
        new_id = cursor.fetchone()["id"]
    return get_enrollment_by_id(new_id)  # type: ignore[arg-type]


def update_enrollment_status(enrollment_id: int, status: str) -> Optional[dict[str, Any]]:
    sql = """
    UPDATE enrollments
    SET
        status = %s,
        updated_at = CURRENT_TIMESTAMP
    WHERE id = %s
    """
    with get_cursor(dict_cursor=False) as (_, cursor):
        cursor.execute(sql, (status, enrollment_id))
    return get_enrollment_by_id(enrollment_id)


def delete_enrollment(enrollment_id: int) -> int:
    sql = "DELETE FROM enrollments WHERE id = %s"
    with get_cursor(dict_cursor=False) as (_, cursor):
        cursor.execute(sql, (enrollment_id,))
        return cursor.rowcount


def count_active_enrollments(course_id: int) -> int:
    sql = """
    SELECT COUNT(*)
    FROM enrollments
    WHERE course_id = %s AND status = 'enrolled'
    """
    row = execute_query(sql, (course_id,), fetchone=True, dict_cursor=False)
    return int(row[0]) if row else 0


def count_course_grades(course_id: int) -> int:
    sql = """
    SELECT COUNT(*)
    FROM grades g
    JOIN enrollments e ON e.id = g.enrollment_id
    WHERE e.course_id = %s
    """
    row = execute_query(sql, (course_id,), fetchone=True, dict_cursor=False)
    return int(row[0]) if row else 0


# ----------------------------
# Grade Management
# ----------------------------
def get_grade_by_id(grade_id: int) -> Optional[dict[str, Any]]:
    sql = """
    SELECT
        g.*,
        e.student_id,
        e.course_id
    FROM grades g
    JOIN enrollments e ON e.id = g.enrollment_id
    WHERE g.id = %s
    """
    row = execute_query(sql, (grade_id,), fetchone=True)
    return _row_to_dict(row)


def get_grade_by_enrollment_id(enrollment_id: int) -> Optional[dict[str, Any]]:
    sql = """
    SELECT
        g.*,
        e.student_id,
        e.course_id
    FROM grades g
    JOIN enrollments e ON e.id = g.enrollment_id
    WHERE g.enrollment_id = %s
    """
    row = execute_query(sql, (enrollment_id,), fetchone=True)
    return _row_to_dict(row)


def list_grades(
    student_id: Optional[int] = None,
    course_id: Optional[int] = None,
    teacher_id: Optional[int] = None,
) -> list[dict[str, Any]]:
    sql = """
    SELECT
        g.id,
        g.enrollment_id,
        g.teacher_id,
        g.attendance_score,
        g.experiment_score,
        g.exam_score,
        g.score,
        g.remarks,
        g.graded_at,
        g.updated_at,
        e.student_id,
        e.course_id,
        s.student_no,
        s.full_name AS student_name,
        c.course_code,
        c.course_name,
        c.attendance_weight,
        c.experiment_weight,
        c.exam_weight
    FROM grades g
    JOIN enrollments e ON e.id = g.enrollment_id
    JOIN students s ON s.id = e.student_id
    JOIN courses c ON c.id = e.course_id
    """
    conditions: list[str] = []
    params: list[Any] = []

    if student_id is not None:
        conditions.append("e.student_id = %s")
        params.append(student_id)
    if course_id is not None:
        conditions.append("e.course_id = %s")
        params.append(course_id)
    if teacher_id is not None:
        conditions.append("g.teacher_id = %s")
        params.append(teacher_id)

    if conditions:
        sql += " WHERE " + " AND ".join(conditions)
    sql += " ORDER BY g.id"
    rows = execute_query(sql, tuple(params))
    return _rows_to_dicts(rows)


def create_grade(
    enrollment_id: int,
    teacher_id: Optional[int],
    attendance_score: float,
    experiment_score: float,
    exam_score: float,
    score: float,
    remarks: Optional[str] = None,
) -> dict[str, Any]:
    sql = """
    INSERT INTO grades (
        enrollment_id,
        teacher_id,
        attendance_score,
        experiment_score,
        exam_score,
        score,
        remarks
    )
    VALUES (%s, %s, %s, %s, %s, %s, %s)
    RETURNING id
    """
    with get_cursor(dict_cursor=True) as (_, cursor):
        cursor.execute(
            sql,
            (
                enrollment_id,
                teacher_id,
                attendance_score,
                experiment_score,
                exam_score,
                score,
                remarks,
            ),
        )
        new_id = cursor.fetchone()["id"]
    return get_grade_by_id(new_id)  # type: ignore[arg-type]


def update_grade(
    grade_id: int,
    attendance_score: float,
    experiment_score: float,
    exam_score: float,
    score: float,
    remarks: Optional[str] = None,
    teacher_id: Optional[int] = None,
) -> Optional[dict[str, Any]]:
    if teacher_id is None:
        sql = """
        UPDATE grades
        SET
            attendance_score = %s,
            experiment_score = %s,
            exam_score = %s,
            score = %s,
            remarks = %s,
            updated_at = CURRENT_TIMESTAMP,
            graded_at = CURRENT_TIMESTAMP
        WHERE id = %s
        """
        params = (
            attendance_score,
            experiment_score,
            exam_score,
            score,
            remarks,
            grade_id,
        )
    else:
        sql = """
        UPDATE grades
        SET
            teacher_id = %s,
            attendance_score = %s,
            experiment_score = %s,
            exam_score = %s,
            score = %s,
            remarks = %s,
            updated_at = CURRENT_TIMESTAMP,
            graded_at = CURRENT_TIMESTAMP
        WHERE id = %s
        """
        params = (
            teacher_id,
            attendance_score,
            experiment_score,
            exam_score,
            score,
            remarks,
            grade_id,
        )

    with get_cursor(dict_cursor=False) as (_, cursor):
        cursor.execute(sql, params)
    return get_grade_by_id(grade_id)


def upsert_grade(
    enrollment_id: int,
    teacher_id: Optional[int],
    attendance_score: float,
    experiment_score: float,
    exam_score: float,
    score: float,
    remarks: Optional[str] = None,
) -> dict[str, Any]:
    existing = get_grade_by_enrollment_id(enrollment_id)
    if existing:
        updated = update_grade(
            grade_id=int(existing["id"]),
            teacher_id=teacher_id,
            attendance_score=attendance_score,
            experiment_score=experiment_score,
            exam_score=exam_score,
            score=score,
            remarks=remarks,
        )
        return updated if updated else existing
    return create_grade(
        enrollment_id=enrollment_id,
        teacher_id=teacher_id,
        attendance_score=attendance_score,
        experiment_score=experiment_score,
        exam_score=exam_score,
        score=score,
        remarks=remarks,
    )
# ===================== 新增：操作日志 数据模型 =====================
def create_operation_log(
    operator_username: str,
    operator_role: str,
    operate_type: str,
    operate_content: str,
    target_type: Optional[str] = None,
    target_id: Optional[int] = None,
    client_ip: Optional[str] = None
) -> int:
    """新增一条操作日志"""
    sql = """
    INSERT INTO operation_log (
        operator_username, operator_role, operate_type, operate_content,
        target_type, target_id, client_ip
    ) VALUES (%s, %s, %s, %s, %s, %s, %s)
    RETURNING id;
    """
    row = execute_query(
        sql,
        (operator_username, operator_role, operate_type, operate_content, target_type, target_id, client_ip),
        fetchone=True
    )
    return row["id"] if row else 0

def list_operation_log(
    keyword: Optional[str] = None,
    operate_type: Optional[str] = None,
    target_type: Optional[str] = None,
    operator: Optional[str] = None,
    page: int = 1,
    page_size: int = 20
) -> tuple[list[dict], int]:
    """分页查询操作日志，返回(日志列表, 总条数)"""
    base_sql = """
    SELECT * FROM operation_log
    """
    count_sql = "SELECT COUNT(*) AS total FROM operation_log"
    conditions = []
    params = []

    if operator:
        conditions.append("operator_username ILIKE %s")
        params.append(f"%{operator}%")
    if operate_type:
        conditions.append("operate_type = %s")
        params.append(operate_type)
    if target_type:
        conditions.append("target_type = %s")
        params.append(target_type)
    if keyword:
        conditions.append("(operate_content ILIKE %s OR operator_username ILIKE %s)")
        params.extend([f"%{keyword}%", f"%{keyword}%"])

    if conditions:
        where_clause = " WHERE " + " AND ".join(conditions)
        base_sql += where_clause
        count_sql += where_clause

    base_sql += " ORDER BY operate_time DESC LIMIT %s OFFSET %s"
    offset = (page - 1) * page_size
    params.extend([page_size, offset])

    total_row = execute_query(count_sql, tuple(params[:-2]) if params else None, fetchone=True)
    total = total_row["total"] if total_row else 0

    log_list = execute_query(base_sql, tuple(params))
    return _rows_to_dicts(log_list), total