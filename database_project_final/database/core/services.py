from typing import Any, Optional

from core import models


ROLE_ADMIN = "admin"
ROLE_TEACHER = "teacher"
ROLE_STUDENT = "student"


def validate_score(score: float) -> None:
    if score < 0 or score > 100:
        raise ValueError("Score must be between 0 and 100.")


def validate_weight(weight: float, field_name: str) -> None:
    if weight < 0 or weight > 100:
        raise ValueError(f"{field_name} must be between 0 and 100.")


def validate_grade_weights(
    attendance_weight: float,
    experiment_weight: float,
    exam_weight: float,
) -> None:
    validate_weight(attendance_weight, "Attendance weight")
    validate_weight(experiment_weight, "Experiment weight")
    validate_weight(exam_weight, "Exam weight")

    total = attendance_weight + experiment_weight + exam_weight
    if abs(total - 100) > 0.001:
        raise ValueError("Attendance, experiment, and exam weights must add up to 100.")


def calculate_final_score(
    attendance_score: float,
    experiment_score: float,
    exam_score: float,
    attendance_weight: float,
    experiment_weight: float,
    exam_weight: float,
) -> float:
    validate_score(attendance_score)
    validate_score(experiment_score)
    validate_score(exam_score)
    validate_grade_weights(attendance_weight, experiment_weight, exam_weight)

    final_score = (
        attendance_score * attendance_weight
        + experiment_score * experiment_weight
        + exam_score * exam_weight
    ) / 100
    return round(final_score, 2)


def validate_grade_year(grade_year: int) -> None:
    if grade_year < 1 or grade_year > 8:
        raise ValueError("Grade year must be between 1 and 8.")


def validate_gender(gender: str) -> None:
    allowed = {"M", "F", "Other"}
    if gender not in allowed:
        raise ValueError("Gender must be one of: M, F, Other.")


def validate_course_capacity(capacity: int) -> None:
    if capacity <= 0:
        raise ValueError("Course capacity must be positive.")


def validate_credits(credits: float) -> None:
    if credits <= 0 or credits > 10:
        raise ValueError("Credits must be in range (0, 10].")


def validate_course_outline(course_outline: Optional[str]) -> None:
    if course_outline is not None and len(course_outline.strip()) > 100:
        raise ValueError("Course outline must be no more than 100 characters.")


def validate_target_grade_year(target_grade_year: int) -> None:
    validate_grade_year(target_grade_year)


# ----------------------------
# Permission Helpers
# ----------------------------
def can_manage_accounts(role_name: str) -> bool:
    return role_name == ROLE_ADMIN


def can_manage_student_crud(role_name: str) -> bool:
    return role_name == ROLE_ADMIN


def can_view_students(role_name: str) -> bool:
    return role_name in {ROLE_ADMIN, ROLE_TEACHER}


def can_manage_courses(role_name: str) -> bool:
    return role_name == ROLE_TEACHER


def can_manage_grades(role_name: str) -> bool:
    return role_name == ROLE_TEACHER


def can_view_enrollments(role_name: str) -> bool:
    return role_name in {ROLE_ADMIN, ROLE_TEACHER}


def can_select_courses(role_name: str) -> bool:
    return role_name == ROLE_STUDENT


def can_view_global_data(role_name: str) -> bool:
    return role_name == ROLE_ADMIN


def can_manage_system_roles(role_name: str) -> bool:
    return role_name == ROLE_ADMIN


# ----------------------------
# Business Rule Helpers
# ----------------------------
def ensure_student_exists(student_id: int) -> dict[str, Any]:
    student = models.get_student_by_id(student_id)
    if not student:
        raise ValueError("Student not found.")
    return student


def ensure_teacher_exists(teacher_id: int) -> dict[str, Any]:
    teacher = models.get_teacher_by_id(teacher_id)
    if not teacher:
        raise ValueError("Teacher not found.")
    return teacher


def ensure_course_exists(course_id: int) -> dict[str, Any]:
    course = models.get_course_by_id(course_id)
    if not course:
        raise ValueError("Course not found.")
    return course


def ensure_enrollment_exists(enrollment_id: int) -> dict[str, Any]:
    enrollment = models.get_enrollment_by_id(enrollment_id)
    if not enrollment:
        raise ValueError("Enrollment not found.")
    return enrollment


def has_duplicate_enrollment(student_id: int, course_id: int) -> bool:
    enrollment = models.get_enrollment_by_student_course(student_id, course_id)
    return enrollment is not None and enrollment["status"] == "enrolled"


def is_course_full(course_id: int) -> bool:
    course = ensure_course_exists(course_id)
    current = models.count_active_enrollments(course_id)
    return current >= int(course["capacity"])


def course_has_grades(course_id: int) -> bool:
    ensure_course_exists(course_id)
    return models.count_course_grades(course_id) > 0


def ensure_course_has_no_grades(course_id: int) -> None:
    if course_has_grades(course_id):
        raise ValueError("This course already has recorded grades and cannot be updated or deleted.")


def ensure_can_enroll(student_id: int, course_id: int) -> None:
    student = ensure_student_exists(student_id)
    course = ensure_course_exists(course_id)

    if int(student["grade_year"]) != int(course["target_grade_year"]):
        raise ValueError("This course is not open to the student's grade year.")

    if has_duplicate_enrollment(student_id, course_id):
        raise ValueError("Student has already enrolled in this course.")

    if is_course_full(course_id):
        raise ValueError("Course capacity is full.")


def enroll_course(student_id: int, course_id: int) -> dict[str, Any]:
    ensure_can_enroll(student_id, course_id)
    existing = models.get_enrollment_by_student_course(student_id, course_id)

    if existing and existing["status"] == "dropped":
        enrollment = models.update_enrollment_status(int(existing["id"]), "enrolled")
        if not enrollment:
            raise ValueError("Failed to re-enroll course.")
        return enrollment

    return models.create_enrollment(student_id, course_id, "enrolled")


def drop_course(student_id: int, course_id: int) -> dict[str, Any]:
    enrollment = models.get_enrollment_by_student_course(student_id, course_id)
    if not enrollment:
        raise ValueError("Enrollment record does not exist.")
    if enrollment["status"] == "dropped":
        raise ValueError("Course is already dropped.")
    if models.get_grade_by_enrollment_id(int(enrollment["id"])):
        raise ValueError("This course already has a recorded grade and cannot be dropped.")

    updated = models.update_enrollment_status(int(enrollment["id"]), "dropped")
    if not updated:
        raise ValueError("Failed to drop course.")
    return updated


def ensure_teacher_can_grade_course(teacher_id: int, enrollment_id: int) -> None:
    ensure_teacher_exists(teacher_id)
    enrollment = ensure_enrollment_exists(enrollment_id)
    course = ensure_course_exists(int(enrollment["course_id"]))

    course_teacher_id = course.get("teacher_id")
    if course_teacher_id is not None and int(course_teacher_id) != teacher_id:
        raise ValueError("Teacher is not assigned to this course.")


def save_grade(
    teacher_id: int,
    enrollment_id: int,
    attendance_score: float,
    experiment_score: float,
    exam_score: float,
    remarks: Optional[str] = None,
) -> dict[str, Any]:
    ensure_teacher_can_grade_course(teacher_id, enrollment_id)
    enrollment = ensure_enrollment_exists(enrollment_id)
    course = ensure_course_exists(int(enrollment["course_id"]))
    final_score = calculate_final_score(
        attendance_score=attendance_score,
        experiment_score=experiment_score,
        exam_score=exam_score,
        attendance_weight=float(course["attendance_weight"]),
        experiment_weight=float(course["experiment_weight"]),
        exam_weight=float(course["exam_weight"]),
    )
    return models.upsert_grade(
        enrollment_id=enrollment_id,
        teacher_id=teacher_id,
        attendance_score=attendance_score,
        experiment_score=experiment_score,
        exam_score=exam_score,
        score=final_score,
        remarks=remarks,
    )


def search_students(keyword: str) -> list[dict[str, Any]]:
    return models.list_students(keyword=keyword)


def search_courses(
    keyword: str,
    target_grade_year: Optional[int] = None,
) -> list[dict[str, Any]]:
    return models.list_courses(keyword=keyword, target_grade_year=target_grade_year)
