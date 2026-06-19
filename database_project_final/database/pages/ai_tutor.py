# from __future__ import annotations
# import streamlit as st
# from core import models
# from core.ai_agent import get_student_learning_data, generate_plan_online
# from core.utils import render_records


# def _build_learning_rows(data: dict) -> list[dict]:
#     grades_by_course = {
#         int(g["course_id"]): g
#         for g in data.get("grades", [])
#         if g.get("course_id") is not None
#     }

#     rows = []
#     for enrollment in data.get("enrollments", []):
#         course_id = int(enrollment["course_id"])
#         grade = grades_by_course.get(course_id)
#         rows.append(
#             {
#                 "course_code": enrollment.get("course_code"),
#                 "course_name": enrollment.get("course_name"),
#                 "status": enrollment.get("status"),
#                 "score": grade.get("score") if grade else None,
#                 "remarks": grade.get("remarks") if grade else None,
#             }
#         )
#     return rows


# def _average_score(data: dict) -> str:
#     scores = [float(g["score"]) for g in data.get("grades", []) if g.get("score") is not None]
#     if not scores:
#         return "N/A"
#     return f"{sum(scores) / len(scores):.1f}"


# def render_ai_tutor_page(current_user: dict):
#     st.title("🤖 AI 学习助手")

#     # 仅学生可用
#     student = models.get_student_by_user_id(int(current_user["id"]))
#     if not student:
#         st.error("未找到你的学生信息")
#         return

#     student_id = int(student["id"])
#     data = get_student_learning_data(student_id)
#     if not data:
#         st.error("暂时无法读取你的学习数据")
#         return

#     enrollments = data.get("enrollments", [])
#     grades = data.get("grades", [])
#     active_count = sum(1 for item in enrollments if item.get("status") == "enrolled")

#     c1, c2, c3 = st.columns(3)
#     c1.metric("已选课程", active_count)
#     c2.metric("已有成绩", len(grades))
#     c3.metric("平均分", _average_score(data))

#     with st.expander("查看用于分析的课程与成绩数据（仅你可见）", expanded=False):
#         render_records(_build_learning_rows(data), "暂无课程或成绩数据。")

#     if st.button("🚀 生成学习分析报告", type="primary"):
#         with st.spinner("AI 正在为你定制计划..."):
#             plan = generate_plan_online(data)
#         st.markdown("---")
#         st.markdown(plan)

from __future__ import annotations
import streamlit as st
from core import models
from core.ai_agent import get_student_learning_data, generate_student_plan

def render_ai_tutor_page(current_user: dict):
    st.title("🤖 AI 学习计划")
    student = models.get_student_by_user_id(int(current_user["id"]))
    if not student:
        st.error("未找到你的学生信息")
        return

    student_id = int(student["id"])
    data = get_student_learning_data(student_id)
    if not data:
        st.error("无法获取学习数据")
        return

    # ✅ 没有数据展示、没有离线、直接生成
    if st.button("🚀 生成我的学习计划", type="primary"):
        with st.spinner("AI 生成中..."):
            plan = generate_student_plan(data)
        st.markdown("---")
        st.markdown(plan)