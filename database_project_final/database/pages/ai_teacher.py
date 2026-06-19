# from __future__ import annotations

# import streamlit as st

# from core import models
# from core.ai_agent import get_teacher_teaching_data, generate_teacher_report_online
# from core.utils import render_records


# def _build_teaching_rows(data: dict) -> list[dict]:
#     grades_by_enrollment = {
#         int(g["enrollment_id"]): g
#         for g in data.get("grades", [])
#         if g.get("enrollment_id") is not None
#     }

#     rows = []
#     for enrollment in data.get("enrollments", []):
#         enrollment_id = int(enrollment["id"])
#         grade = grades_by_enrollment.get(enrollment_id)
#         rows.append(
#             {
#                 "course_code": enrollment.get("course_code"),
#                 "course_name": enrollment.get("course_name"),
#                 "student_no": enrollment.get("student_no"),
#                 "student_name": enrollment.get("student_name"),
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


# def render_teacher_agent_page(current_user: dict) -> None:
#     st.title("🤖 AI 教学助手")

#     teacher = models.get_teacher_by_user_id(int(current_user["id"]))
#     if not teacher:
#         st.error("未找到你的教师信息")
#         return

#     data = get_teacher_teaching_data(int(teacher["id"]))
#     if not data:
#         st.error("暂时无法读取你的教学数据")
#         return

#     courses = data.get("courses", [])
#     enrollments = data.get("enrollments", [])
#     grades = data.get("grades", [])
#     active_student_ids = {
#         int(item["student_id"])
#         for item in enrollments
#         if item.get("status") == "enrolled" and item.get("student_id") is not None
#     }

#     c1, c2, c3, c4 = st.columns(4)
#     c1.metric("负责课程", len(courses))
#     c2.metric("授课学生", len(active_student_ids))
#     c3.metric("已有成绩", len(grades))
#     c4.metric("平均分", _average_score(data))

#     with st.expander("查看用于分析的课程、选课与成绩数据", expanded=False):
#         render_records(_build_teaching_rows(data), "暂无课程、选课或成绩数据。")

#     if st.button("🚀 生成教学分析报告", type="primary"):
#         with st.spinner("AI 正在分析你的教学数据..."):
#             report = generate_teacher_report_online(data)
#         st.markdown("---")
#         st.markdown(report)
from __future__ import annotations
import streamlit as st

def render_teacher_agent_page(current_user: dict) -> None:
    st.title("🤖 AI 教学助手（已升级）")
    st.warning("此功能已升级为「AI Teaching」，请从顶部标签页进入使用")