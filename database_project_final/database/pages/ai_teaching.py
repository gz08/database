from __future__ import annotations
import streamlit as st
from core import models
from core.ai_agent import get_teacher_teaching_data, generate_teaching_plan
from core.utils import selectbox_from_records

def _student_label(student: dict) -> str:
    return f"{student['student_no']} | {student['full_name']} | {student['major']}"

def _course_label(course: dict) -> str:
    return f"{course['course_code']} | {course['course_name']}"

def _student_filter_label(student_id: int | None, labels: dict[int, str]) -> str:
    if student_id is None:
        return "Whole Class"
    return labels.get(student_id, str(student_id))

def render_ai_teaching_page(current_user: dict):
    st.title("🤖 AI 专属教学方案")
    teacher = models.get_teacher_by_user_id(int(current_user["id"]))
    if not teacher:
        st.error("未找到教师信息")
        return
    teacher_id = int(teacher["id"])
    
    # 筛选条件：课程 + 学生
    st.subheader("选择教学对象")
    courses = models.list_courses(teacher_id=teacher_id)
    selected_course, course_id = selectbox_from_records(
        "选择课程（班级）", courses, "id", _course_label, key="teach_course"
    )
    
    students = []
    if selected_course:
        enrollments = models.list_enrollments(course_id=int(course_id), status="enrolled")
        seen_student_ids: set[int] = set()
        for enrollment in enrollments:
            sid = int(enrollment["student_id"])
            if sid in seen_student_ids:
                continue
            seen_student_ids.add(sid)
            student = models.get_student_by_id(sid)
            if student:
                students.append(student)

    student_labels = {int(student["id"]): _student_label(student) for student in students}
    selected_student_id = st.selectbox(
        "选择学生",
        options=[None] + list(student_labels.keys()),
        format_func=lambda sid: _student_filter_label(sid, student_labels),
        key="teach_student",
    )
    
    if st.button("📚 生成专属教学方法", type="primary"):
        with st.spinner("AI正在生成教学方案..."):
            data = get_teacher_teaching_data(
                teacher_id=teacher_id,
                student_id=int(selected_student_id) if selected_student_id is not None else None,
                course_id=int(course_id) if selected_course else None
            )
            if not data:
                st.error("未获取到教学数据")
                return
            plan = generate_teaching_plan(data)
        st.markdown("---")
        st.markdown(plan)
