# #权重不变
# from __future__ import annotations
# from typing import Any
# import streamlit as st
# import pandas as pd
# from datetime import datetime
# from core import models
# from core import services
# from core.utils import render_records, require_text, safe_run, selectbox_from_records
# from pages.ai_teaching import render_ai_teaching_page

# def _course_label(course: dict[str, Any]) -> str:
#     return f"{course['course_code']} | {course['course_name']}"

# def _course_table_rows(courses: list[dict[str, Any]]) -> list[dict[str, Any]]:
#     return [
#         {
#             "course_code": course.get("course_code"),
#             "course_name": course.get("course_name"),
#             "course_outline": course.get("course_outline"),
#             "credits": course.get("credits"),
#             "capacity": course.get("capacity"),
#             "semester": course.get("semester"),
#             "target_grade_year": course.get("target_grade_year"),
#             "attendance_weight": course.get("attendance_weight", 10),
#             "experiment_weight": course.get("experiment_weight", 30),
#             "exam_weight": course.get("exam_weight", 60),
#             "created_at": course.get("created_at"),
#             "updated_at": course.get("updated_at"),
#         }
#         for course in courses
#     ]

# def _student_table_rows(students: list[dict[str, Any]]) -> list[dict[str, Any]]:
#     return [
#         {
#             "student_no": student.get("student_no"),
#             "full_name": student.get("full_name"),
#             "gender": student.get("gender"),
#             "grade_year": student.get("grade_year"),
#             "major": student.get("major"),
#             "phone": student.get("phone"),
#             "email": student.get("email"),
#             "username": student.get("username") or "No account",
#             "account_status": "Active" if student.get("user_is_active") else "No account / Disabled",
#             "created_at": student.get("created_at"),
#             "updated_at": student.get("updated_at"),
#         }
#         for student in students
#     ]

# def _enrollment_table_rows(enrollments: list[dict[str, Any]]) -> list[dict[str, Any]]:
#     return [
#         {
#             "student_no": enrollment.get("student_no"),
#             "student_name": enrollment.get("student_name"),
#             "course_code": enrollment.get("course_code"),
#             "course_name": enrollment.get("course_name"),
#             "status": enrollment.get("status"),
#             "enrolled_at": enrollment.get("enrolled_at"),
#             "updated_at": enrollment.get("updated_at"),
#         }
#         for enrollment in enrollments
#     ]

# def _grade_table_rows(grades: list[dict[str, Any]]) -> list[dict[str, Any]]:
#     return [
#         {
#             "student_no": grade.get("student_no"),
#             "student_name": grade.get("student_name"),
#             "course_code": grade.get("course_code"),
#             "course_name": grade.get("course_name"),
#             "attendance_score": grade.get("attendance_score"),
#             "experiment_score": grade.get("experiment_score"),
#             "exam_score": grade.get("exam_score"),
#             "final_score": grade.get("score"),
#             "weights": (
#                 f"{float(grade.get('attendance_weight', 0)):.1f}% / "
#                 f"{float(grade.get('experiment_weight', 0)):.1f}% / "
#                 f"{float(grade.get('exam_weight', 0)):.1f}%"
#             ),
#             "remarks": grade.get("remarks"),
#             "graded_at": grade.get("graded_at"),
#             "updated_at": grade.get("updated_at"),
#         }
#         for grade in grades
#     ]

# def _enrollment_label(enrollment: dict[str, Any]) -> str:
#     return (
#         f"{enrollment['student_no']} {enrollment['student_name']} -> "
#         f"{enrollment['course_code']} {enrollment['course_name']} "
#         f"({enrollment['status']})"
#     )

# def _list_teacher_enrollments(teacher_course_ids: set[int]) -> list[dict[str, Any]]:
#     if not teacher_course_ids:
#         return []
#     all_enrollments = models.list_enrollments()
#     return [e for e in all_enrollments if int(e["course_id"]) in teacher_course_ids]

# # 固定权重配置
# FIXED_ATTENDANCE_WEIGHT = 10.0
# FIXED_EXPERIMENT_WEIGHT = 30.0
# FIXED_EXAM_WEIGHT = 60.0
# # 要求的列头顺序
# REQUIRED_COLUMNS = [
#     'student_no', 'student_name', 'course_code', 'course_name',
#     'attendance_score', 'experiment_score', 'exam_score', 'final_score', 'remarks'
# ]

# def _calculate_final_score(attendance: float, experiment: float, exam: float) -> float:
#     """按固定权重计算最终成绩"""
#     return round(
#         attendance * FIXED_ATTENDANCE_WEIGHT / 100 +
#         experiment * FIXED_EXPERIMENT_WEIGHT / 100 +
#         exam * FIXED_EXAM_WEIGHT / 100,
#         2
#     )

# def _import_grades_from_file(uploaded_file, teacher_id: int) -> dict[str, Any]:
#     """从上传的文件导入成绩，返回导入结果统计"""
#     result = {
#         'success': 0,
#         'updated': 0,
#         'skipped': 0,
#         'failed': 0,
#         'errors': []
#     }
#     current_time = datetime.now()

#     # 读取文件
#     try:
#         if uploaded_file.name.endswith('.csv'):
#             df = pd.read_csv(uploaded_file)
#         elif uploaded_file.name.endswith(('.xlsx', '.xls')):
#             df = pd.read_excel(uploaded_file)
#         else:
#             result['errors'].append(f"不支持的文件格式：{uploaded_file.name}")
#             return result
#     except Exception as e:
#         result['errors'].append(f"文件读取失败：{str(e)}")
#         return result

#     # 校验列头
#     if list(df.columns) != REQUIRED_COLUMNS:
#         result['errors'].append(
#             f"列头不符合要求！\n要求顺序：{REQUIRED_COLUMNS}\n实际列头：{list(df.columns)}"
#         )
#         return result

#     # 遍历每一行数据
#     for idx, row in df.iterrows():
#         row_num = idx + 2  # 行号，Excel中第2行开始是数据
#         try:
#             # 读取并清洗数据
#             student_no = str(row['student_no']).strip()
#             student_name = str(row['student_name']).strip()
#             course_code = str(row['course_code']).strip()
#             course_name = str(row['course_name']).strip()
#             attendance_score = float(row['attendance_score'])
#             experiment_score = float(row['experiment_score'])
#             exam_score = float(row['exam_score'])
#             remarks = str(row['remarks']).strip() if pd.notna(row['remarks']) else None

#             # 校验必填字段
#             if not all([student_no, student_name, course_code, course_name]):
#                 raise ValueError("学号、姓名、课程编号、课程名称不能为空")

#             # 校验分数范围
#             for score, name in [
#                 (attendance_score, '出勤成绩'),
#                 (experiment_score, '实验成绩'),
#                 (exam_score, '考试成绩')
#             ]:
#                 if score < 0 or score > 100:
#                     raise ValueError(f"{name}必须在0-100之间，当前值：{score}")

#             # 计算最终成绩
#             final_score = _calculate_final_score(attendance_score, experiment_score, exam_score)

#             # 查找学生
#             student = models.get_student_by_student_no(student_no)
#             if not student:
#                 raise ValueError(f"未找到学号为 {student_no} 的学生")
#             student_id = int(student['id'])

#             # 查找课程
#             course = models.get_course_by_code(course_code)
#             if not course:
#                 raise ValueError(f"未找到课程编号为 {course_code} 的课程")
#             course_id = int(course['id'])

#             # 查找选课记录（仅已选状态）
#             enrollment = models.get_enrollment_by_student_course(student_id, course_id)
#             if not enrollment or enrollment['status'] != 'enrolled':
#                 raise ValueError(f"学生 {student_no} 未选修课程 {course_code}，或选课状态非已选")
#             enrollment_id = int(enrollment['id'])

#             # 查找现有成绩记录
#             existing_grade = models.get_grade_by_enrollment_id(enrollment_id)

#             # 判断是否需要更新/新增
#             if existing_grade:
#                 # 对比数据是否有变化
#                 is_same = (
#                     abs(float(existing_grade['attendance_score']) - attendance_score) < 0.001 and
#                     abs(float(existing_grade['experiment_score']) - experiment_score) < 0.001 and
#                     abs(float(existing_grade['exam_score']) - exam_score) < 0.001 and
#                     str(existing_grade['remarks'] or '') == str(remarks or '')
#                 )
#                 if is_same:
#                     result['skipped'] += 1
#                     continue
#                 # 执行更新
#                 updated_grade = models.update_grade(
#                     grade_id=int(existing_grade['id']),
#                     teacher_id=teacher_id,
#                     attendance_score=attendance_score,
#                     experiment_score=experiment_score,
#                     exam_score=exam_score,
#                     score=final_score,
#                     remarks=remarks
#                 )
#                 if updated_grade:
#                     result['updated'] += 1
#                 else:
#                     raise ValueError("成绩更新失败")
#             else:
#                 # 执行新增
#                 new_grade = models.create_grade(
#                     enrollment_id=enrollment_id,
#                     teacher_id=teacher_id,
#                     attendance_score=attendance_score,
#                     experiment_score=experiment_score,
#                     exam_score=exam_score,
#                     score=final_score,
#                     remarks=remarks
#                 )
#                 if new_grade:
#                     result['success'] += 1
#                 else:
#                     raise ValueError("成绩新增失败")

#         except Exception as e:
#             result['failed'] += 1
#             result['errors'].append(f"第{row_num}行：{str(e)}")
#             continue

#     return result

# def render_teacher_page(current_user: dict) -> None:
#     page = st.container()
#     with page:
#         st.title("Teacher Dashboard")
#         teacher = models.get_teacher_by_user_id(int(current_user["id"]))
#         if not teacher:
#             st.error("Teacher profile is missing. Please contact admin.")
#             return
#         teacher_id = int(teacher["id"])
#         teacher_courses = models.list_courses(teacher_id=teacher_id)
#         teacher_course_ids = {int(c["id"]) for c in teacher_courses}
#         # 添加AI Teaching标签页
#         tab_students, tab_courses, tab_enrollments, tab_grades, tab_ai_teaching = st.tabs(
#             ["View Students", "Course Management", "Enrollment Info", "Grade Management", "AI Teaching"]
#         )
#         with tab_students:
#             _render_student_view()
#         with tab_courses:
#             _render_course_management(teacher_id, teacher_courses)
#         with tab_enrollments:
#             _render_enrollment_info(teacher_courses, teacher_course_ids)
#         with tab_grades:
#             _render_grade_management(teacher_id, teacher_course_ids)
#         with tab_ai_teaching:
#             render_ai_teaching_page(current_user)

# def _render_student_view() -> None:
#     st.subheader("Students")
#     keyword = st.text_input("Search students by name / student no / major")
#     students = services.search_students(keyword) if keyword.strip() else models.list_students()
#     render_records(_student_table_rows(students), "No students found.")

# def _render_course_management(teacher_id: int, teacher_courses: list[dict[str, Any]]) -> None:
#     st.subheader("My Courses")
#     keyword = st.text_input("Search my courses by code / name")
#     if keyword.strip():
#         all_courses = models.list_courses(keyword=keyword.strip())
#         filtered = [c for c in all_courses if int(c["teacher_id"] or 0) == teacher_id]
#     else:
#         filtered = teacher_courses
#     render_records(_course_table_rows(filtered), "No courses found.")
#     st.divider()
#     st.subheader("Create Course")
#     with st.form("teacher_create_course"):
#         c1, c2, c3 = st.columns(3)
#         course_code = c1.text_input("Course Code")
#         course_name = c2.text_input("Course Name")
#         semester = c3.text_input("Semester", value="2026-Spring")
#         credits = c1.number_input("Credits", min_value=0.5, max_value=10.0, value=3.0, step=0.5)
#         capacity = c2.number_input("Capacity", min_value=1, max_value=1000, value=50, step=1)
#         target_grade_year = c3.number_input("Target Grade Year", min_value=1, max_value=8, value=2, step=1)
#         attendance_weight = c1.number_input("Attendance Weight (%)", min_value=0.0, max_value=100.0, value=10.0, step=5.0)
#         experiment_weight = c2.number_input("Experiment Weight (%)", min_value=0.0, max_value=100.0, value=30.0, step=5.0)
#         exam_weight = c3.number_input("Exam Weight (%)", min_value=0.0, max_value=100.0, value=60.0, step=5.0)
#         course_outline = st.text_area("Course Outline", max_chars=100, height=80)
#         submit = st.form_submit_button("Create Course")
#         if submit:
#             def action():
#                 outline_value = course_outline.strip()
#                 services.validate_credits(float(credits))
#                 services.validate_course_capacity(int(capacity))
#                 services.validate_target_grade_year(int(target_grade_year))
#                 services.validate_course_outline(outline_value)
#                 services.validate_grade_weights(
#                     float(attendance_weight),
#                     float(experiment_weight),
#                     float(exam_weight),
#                 )
#                 return models.create_course(
#                     course_code=require_text(course_code, "Course Code"),
#                     course_name=require_text(course_name, "Course Name"),
#                     credits=float(credits),
#                     semester=require_text(semester, "Semester"),
#                     course_outline=outline_value,
#                     teacher_id=teacher_id,
#                     capacity=int(capacity),
#                     target_grade_year=int(target_grade_year),
#                     attendance_weight=float(attendance_weight),
#                     experiment_weight=float(experiment_weight),
#                     exam_weight=float(exam_weight),
#                 )
#             safe_run(action, "Course created.", rerun=True)
#     st.divider()
#     st.subheader("Update / Delete Course")
#     selected_course, _ = selectbox_from_records(
#         "Select my course",
#         teacher_courses,
#         id_key="id",
#         label_builder=_course_label,
#         key="teacher_course_select",
#     )
#     if not selected_course:
#         return
#     selected_course_id = int(selected_course["id"])
#     if services.course_has_grades(selected_course_id):
#         st.warning("This course already has recorded grades and cannot be updated or deleted.")
#     c1, c2 = st.columns(2)
#     with c1:
#         with st.form("teacher_update_course"):
#             course_name = st.text_input("Course Name", value=str(selected_course["course_name"]))
#             semester = st.text_input("Semester", value=str(selected_course["semester"]))
#             course_outline = st.text_area(
#                 "Course Outline",
#                 value=str(selected_course.get("course_outline") or ""),
#                 max_chars=100,
#                 height=80,
#             )
#             credits = st.number_input(
#                 "Credits",
#                 min_value=0.5,
#                 max_value=10.0,
#                 value=float(selected_course["credits"]),
#                 step=0.5,
#             )
#             capacity = st.number_input(
#                 "Capacity",
#                 min_value=1,
#                 max_value=1000,
#                 value=int(selected_course["capacity"]),
#                 step=1,
#             )
#             target_grade_year = st.number_input(
#                 "Target Grade Year",
#                 min_value=1,
#                 max_value=8,
#                 value=int(selected_course.get("target_grade_year", 2)),
#                 step=1,
#             )
#             attendance_weight = st.number_input(
#                 "Attendance Weight (%)",
#                 min_value=0.0,
#                 max_value=100.0,
#                 value=float(selected_course.get("attendance_weight", 10)),
#                 step=5.0,
#             )
#             experiment_weight = st.number_input(
#                 "Experiment Weight (%)",
#                 min_value=0.0,
#                 max_value=100.0,
#                 value=float(selected_course.get("experiment_weight", 30)),
#                 step=5.0,
#             )
#             exam_weight = st.number_input(
#                 "Exam Weight (%)",
#                 min_value=0.0,
#                 max_value=100.0,
#                 value=float(selected_course.get("exam_weight", 60)),
#                 step=5.0,
#             )
#             update_submit = st.form_submit_button("Update Course")
#             if update_submit:
#                 def action():
#                     outline_value = course_outline.strip()
#                     services.ensure_course_has_no_grades(selected_course_id)
#                     services.validate_credits(float(credits))
#                     services.validate_course_capacity(int(capacity))
#                     services.validate_target_grade_year(int(target_grade_year))
#                     services.validate_course_outline(outline_value)
#                     services.validate_grade_weights(
#                         float(attendance_weight),
#                         float(experiment_weight),
#                         float(exam_weight),
#                     )
#                     return models.update_course(
#                         course_id=selected_course_id,
#                         course_name=require_text(course_name, "Course Name"),
#                         semester=require_text(semester, "Semester"),
#                         course_outline=outline_value,
#                         credits=float(credits),
#                         capacity=int(capacity),
#                         teacher_id=teacher_id,
#                         target_grade_year=int(target_grade_year),
#                         attendance_weight=float(attendance_weight),
#                         experiment_weight=float(experiment_weight),
#                         exam_weight=float(exam_weight),
#                     )
#                 safe_run(action, "Course updated.", rerun=True)
#     with c2:
#         with st.form("teacher_delete_course"):
#             confirm = st.checkbox("Confirm delete this course")
#             delete_submit = st.form_submit_button("Delete Course")
#             if delete_submit:
#                 def action():
#                     if not confirm:
#                         raise ValueError("Please confirm before deleting.")
#                     services.ensure_course_has_no_grades(selected_course_id)
#                     deleted = models.delete_course(selected_course_id)
#                     if deleted <= 0:
#                         raise ValueError("Course delete failed.")
#                     return deleted
#                 safe_run(action, "Course deleted.", rerun=True)

# def _render_enrollment_info(
#     teacher_courses: list[dict[str, Any]],
#     teacher_course_ids: set[int],
# ) -> None:
#     st.subheader("Enrollment Records")
#     if not teacher_courses:
#         st.info("No teacher course yet.")
#         return
#     selected_course, selected_id = selectbox_from_records(
#         "Course filter",
#         teacher_courses,
#         id_key="id",
#         label_builder=_course_label,
#         key="teacher_enrollment_course_filter",
#     )
#     include_dropped = st.checkbox("Include dropped records", value=False)
#     if selected_course:
#         enrollments = models.list_enrollments(course_id=int(selected_id))
#     else:
#         enrollments = _list_teacher_enrollments(teacher_course_ids)
#     if not include_dropped:
#         enrollments = [e for e in enrollments if e["status"] == "enrolled"]
#     render_records(_enrollment_table_rows(enrollments), "No enrollment records.")

# def _render_grade_management(teacher_id: int, teacher_course_ids: set[int]) -> None:
#     st.subheader("Current Grades")

#     # 新增：批量导入成绩功能
#     st.subheader("📥 批量导入成绩")
#     uploaded_file = st.file_uploader(
#         "上传CSV/XLSX文件",
#         type=['csv', 'xlsx', 'xls'],
#         help=f"文件列头必须严格按此顺序：{REQUIRED_COLUMNS}"
#     )
#     if uploaded_file:
#         if st.button("开始导入", type="primary"):
#             with st.spinner("正在导入成绩..."):
#                 import_result = _import_grades_from_file(uploaded_file, teacher_id)
#             # 显示导入结果
#             st.divider()
#             st.markdown("### 导入结果")
#             col1, col2, col3, col4 = st.columns(4)
#             col1.metric("新增成功", import_result['success'])
#             col2.metric("更新成功", import_result['updated'])
#             col3.metric("无变化跳过", import_result['skipped'])
#             col4.metric("导入失败", import_result['failed'])
#             # 显示错误信息
#             if import_result['errors']:
#                 st.error("导入错误详情：")
#                 for error in import_result['errors']:
#                     st.write(f"- {error}")
#             st.divider()
#             # 导入完成后刷新页面
#             st.rerun()

#     # 原有成绩表格
#     grades = models.list_grades(teacher_id=teacher_id)
#     render_records(_grade_table_rows(grades), "No grade records.")
#     st.divider()
#     st.subheader("Record / Update Grade")
#     enrollments = _list_teacher_enrollments(teacher_course_ids)
#     enrollments = [e for e in enrollments if e["status"] == "enrolled"]
#     selected_enrollment, selected_enrollment_id = selectbox_from_records(
#         "Select enrollment",
#         enrollments,
#         id_key="id",
#         label_builder=_enrollment_label,
#         key="teacher_grade_enrollment_select",
#     )
#     if not selected_enrollment:
#         return
#     existing = models.get_grade_by_enrollment_id(int(selected_enrollment_id))
#     course = models.get_course_by_id(int(selected_enrollment["course_id"]))
#     if not course:
#         st.error("Course information is missing.")
#         return
#     default_attendance_score = float(existing["attendance_score"]) if existing else 0.0
#     default_experiment_score = float(existing["experiment_score"]) if existing else 0.0
#     default_exam_score = float(existing["exam_score"]) if existing else 0.0
#     default_remarks = str(existing["remarks"] or "") if existing else ""
#     st.info(
#         "Weights: "
#         f"Attendance {float(course['attendance_weight']):.1f}% · "
#         f"Experiment {float(course['experiment_weight']):.1f}% · "
#         f"Exam {float(course['exam_weight']):.1f}%"
#     )
#     with st.form("teacher_save_grade"):
#         attendance_score = st.number_input(
#             "Attendance Score",
#             min_value=0.0,
#             max_value=100.0,
#             value=default_attendance_score,
#             step=0.5,
#         )
#         experiment_score = st.number_input(
#             "Experiment Score",
#             min_value=0.0,
#             max_value=100.0,
#             value=default_experiment_score,
#             step=0.5,
#         )
#         exam_score = st.number_input(
#             "Exam Score",
#             min_value=0.0,
#             max_value=100.0,
#             value=default_exam_score,
#             step=0.5,
#         )
#         remarks = st.text_area("Remarks", value=default_remarks)
#         submit = st.form_submit_button("Save Grade")
#         if submit:
#             safe_run(
#                 lambda: services.save_grade(
#                     teacher_id=teacher_id,
#                     enrollment_id=int(selected_enrollment_id),
#                     attendance_score=float(attendance_score),
#                     experiment_score=float(experiment_score),
#                     exam_score=float(exam_score),
#                     remarks=remarks.strip() or None,
#                 ),
#                 "Grade saved.",
#                 rerun=True,
#             )

# #权重会改变+进度条
# from __future__ import annotations
# from typing import Any
# import streamlit as st
# import pandas as pd
# import re
# from datetime import datetime
# from core import models
# from core import services
# from core.utils import render_records, require_text, safe_run, selectbox_from_records
# from pages.ai_teaching import render_ai_teaching_page

# def _course_label(course: dict[str, Any]) -> str:
#     return f"{course['course_code']} | {course['course_name']}"

# def _course_table_rows(courses: list[dict[str, Any]]) -> list[dict[str, Any]]:
#     return [
#         {
#             "course_code": course.get("course_code"),
#             "course_name": course.get("course_name"),
#             "course_outline": course.get("course_outline"),
#             "credits": course.get("credits"),
#             "capacity": course.get("capacity"),
#             "semester": course.get("semester"),
#             "target_grade_year": course.get("target_grade_year"),
#             "attendance_weight": course.get("attendance_weight", 10),
#             "experiment_weight": course.get("experiment_weight", 30),
#             "exam_weight": course.get("exam_weight", 60),
#             "created_at": course.get("created_at"),
#             "updated_at": course.get("updated_at"),
#         }
#         for course in courses
#     ]

# def _student_table_rows(students: list[dict[str, Any]]) -> list[dict[str, Any]]:
#     return [
#         {
#             "student_no": student.get("student_no"),
#             "full_name": student.get("full_name"),
#             "gender": student.get("gender"),
#             "grade_year": student.get("grade_year"),
#             "major": student.get("major"),
#             "phone": student.get("phone"),
#             "email": student.get("email"),
#             "username": student.get("username") or "No account",
#             "account_status": "Active" if student.get("user_is_active") else "No account / Disabled",
#             "created_at": student.get("created_at"),
#             "updated_at": student.get("updated_at"),
#         }
#         for student in students
#     ]

# def _enrollment_table_rows(enrollments: list[dict[str, Any]]) -> list[dict[str, Any]]:
#     return [
#         {
#             "student_no": enrollment.get("student_no"),
#             "student_name": enrollment.get("student_name"),
#             "course_code": enrollment.get("course_code"),
#             "course_name": enrollment.get("course_name"),
#             "status": enrollment.get("status"),
#             "enrolled_at": enrollment.get("enrolled_at"),
#             "updated_at": enrollment.get("updated_at"),
#         }
#         for enrollment in enrollments
#     ]

# def _grade_table_rows(grades: list[dict[str, Any]]) -> list[dict[str, Any]]:
#     return [
#         {
#             "student_no": grade.get("student_no"),
#             "student_name": grade.get("student_name"),
#             "course_code": grade.get("course_code"),
#             "course_name": grade.get("course_name"),
#             "attendance_score": grade.get("attendance_score"),
#             "experiment_score": grade.get("experiment_score"),
#             "exam_score": grade.get("exam_score"),
#             "final_score": grade.get("score"),
#             "weights": (
#                 f"{float(grade.get('attendance_weight', 0)):.1f}% / "
#                 f"{float(grade.get('experiment_weight', 0)):.1f}% / "
#                 f"{float(grade.get('exam_weight', 0)):.1f}%"
#             ),
#             "remarks": grade.get("remarks"),
#             "graded_at": grade.get("graded_at"),
#             "updated_at": grade.get("updated_at"),
#         }
#         for grade in grades
#     ]

# def _enrollment_label(enrollment: dict[str, Any]) -> str:
#     return (
#         f"{enrollment['student_no']} {enrollment['student_name']} -> "
#         f"{enrollment['course_code']} {enrollment['course_name']} "
#         f"({enrollment['status']})"
#     )

# def _list_teacher_enrollments(teacher_course_ids: set[int]) -> list[dict[str, Any]]:
#     if not teacher_course_ids:
#         return []
#     all_enrollments = models.list_enrollments()
#     return [e for e in all_enrollments if int(e["course_id"]) in teacher_course_ids]

# REQUIRED_COLUMNS = [
#     'student_no', 'student_name', 'course_code', 'course_name',
#     'attendance_score', 'experiment_score', 'exam_score', 'final_score',
#     'weight', 'remarks'
# ]

# def parse_weight_string(weight_str):
#     numbers = re.findall(r"\d+\.?\d*", weight_str)
#     if len(numbers) != 3:
#         raise ValueError(f"Invalid weight format: {weight_str}")
#     return float(numbers[0]), float(numbers[1]), float(numbers[2])

# def _import_grades_from_file(uploaded_file, teacher_id: int) -> dict[str, Any]:
#     result = {
#         'success': 0, 'updated': 0, 'skipped': 0, 'failed': 0, 'errors': []
#     }
#     try:
#         if uploaded_file.name.endswith('.csv'):
#             df = pd.read_csv(uploaded_file)
#         elif uploaded_file.name.endswith(('.xlsx', '.xls')):
#             df = pd.read_excel(uploaded_file)
#         else:
#             result['errors'].append(f"Unsupported file: {uploaded_file.name}")
#             return result
#     except Exception as e:
#         result['errors'].append(f"Read failed: {str(e)}")
#         return result

#     if list(df.columns) != REQUIRED_COLUMNS:
#         result['errors'].append(f"Columns must be: {REQUIRED_COLUMNS}")
#         return result

#     course_name_map = {}
#     course_weight_map = {}
#     conflict_courses = {}

#     for idx, row in df.iterrows():
#         code = str(row['course_code']).strip()
#         name = str(row['course_name']).strip()
#         w_str = str(row['weight']).strip()

#         try:
#             aw, ew, xw = parse_weight_string(w_str)
#         except:
#             result['errors'].append(f"Row {idx+2}: Invalid weight format '{w_str}'")
#             return result

#         if code not in course_name_map:
#             course_name_map[code] = name
#         else:
#             if course_name_map[code] != name:
#                 key = f"Course {code} | Name conflict: {course_name_map[code]} vs {name}"
#                 conflict_courses[key] = "Same course code cannot have different names"

#         if code not in course_weight_map:
#             course_weight_map[code] = w_str
#         else:
#             if course_weight_map[code] != w_str:
#                 key = f"Course {code} | Weight conflict"
#                 allw = f"{course_weight_map[code]} , {w_str}"
#                 conflict_courses[key] = f"Weights: {allw}"

#     total = len(df)
#     st.markdown("---")
#     st.markdown("### 📊 Import Progress", unsafe_allow_html=True)
#     progress_container = st.container()
#     with progress_container:
#         progress_bar = st.progress(0.0)
#         status_text = st.empty()
#         status_text.markdown(f"<h4>Ready to import: 0/{total}</h4>", unsafe_allow_html=True)

#     if conflict_courses:
#         st.markdown("---")
#         st.markdown("# ❌ ERROR: Data Conflicts Found", unsafe_allow_html=True)
#         for c, msg in conflict_courses.items():
#             st.markdown(f"""
#                 <div style='background-color:#fee2e2; border-left:5px solid #dc2626; padding:12px; margin:8px 0; border-radius:4px;'>
#                     <span style='color:#dc2626; font-size:18px; font-weight:bold;'>{c}: {msg}</span>
#                 </div>
#             """, unsafe_allow_html=True)
#         result['errors'].append("Import stopped due to conflicts")
#         # st.button("🔄 Close Error & Return", type="primary", use_container_width=True)
#         return result

#     for idx, row in df.iterrows():
#         current = idx + 1
#         progress = current / total
#         progress_bar.progress(progress)
#         status_text.markdown(f"<h4>Processing: {current}/{total} ({progress:.0%})</h4>", unsafe_allow_html=True)
        
#         row_num = idx + 2
#         try:
#             sno = str(row['student_no']).strip()
#             sname = str(row['student_name']).strip()
#             code = str(row['course_code']).strip()
#             cname = str(row['course_name']).strip()
#             att = float(row['attendance_score'])
#             exp = float(row['experiment_score'])
#             exam = float(row['exam_score'])
#             final = float(row['final_score'])
#             weight_str = str(row['weight']).strip()
#             rem = str(row['remarks']).strip() if pd.notna(row['remarks']) else None

#             for s, n in [(att,'att'), (exp,'exp'), (exam,'exam')]:
#                 if not (0 <= s <= 100):
#                     raise ValueError(f"{n} must be 0-100")

#             stu = models.get_student_by_student_no(sno)
#             if not stu: raise ValueError(f"Student {sno} not found")
#             stu_id = int(stu['id'])

#             course = models.get_course_by_code(code)
#             if not course: raise ValueError(f"Course {code} not found")
#             cid = int(course['id'])

#             aw, ew, xw = parse_weight_string(weight_str)

#             enroll = models.get_enrollment_by_student_course(stu_id, cid)
#             if not enroll or enroll['status'] != 'enrolled':
#                 raise ValueError(f"Not enrolled")
#             eid = int(enroll['id'])

#             exist = models.get_grade_by_enrollment_id(eid)
#             if exist:
#                 same = (
#                     abs(float(exist['attendance_score'])-att)<0.001 and
#                     abs(float(exist['experiment_score'])-exp)<0.001 and
#                     abs(float(exist['exam_score'])-exam)<0.001 and
#                     (exist.get('remarks') or '') == (rem or '')
#                 )
#                 if same:
#                     result['skipped'] +=1
#                     continue
#                 models.update_grade(
#                     int(exist['id']), att, exp, exam, final, rem, teacher_id
#                 )
#                 result['updated'] +=1
#             else:
#                 models.create_grade(
#                     eid, teacher_id, att, exp, exam, final, rem
#                 )
#                 result['success'] +=1

#         except Exception as e:
#             result['failed'] +=1
#             result['errors'].append(f"Row {row_num}: {str(e)}")

#     progress_bar.progress(1.0)
#     status_text.markdown("<h4 style='color:#059669;'>✅ Import Completed</h4>", unsafe_allow_html=True)
#     return result

# def render_teacher_page(current_user: dict) -> None:
#     page = st.container()
#     with page:
#         st.title("Teacher Dashboard")
#         teacher = models.get_teacher_by_user_id(int(current_user["id"]))
#         if not teacher:
#             st.error("Teacher profile missing")
#             return
#         teacher_id = int(teacher["id"])
#         courses = models.list_courses(teacher_id=teacher_id)
#         c_ids = {int(c["id"]) for c in courses}

#         tabs = st.tabs([
#             "View Students", "Course Management",
#             "Enrollment Info", "Grade Management", "AI Teaching"
#         ])
#         with tabs[0]: _render_student_view()
#         with tabs[1]: _render_course_management(teacher_id, courses)
#         with tabs[2]: _render_enrollment_info(courses, c_ids)
#         with tabs[3]: _render_grade_management(teacher_id, c_ids)
#         with tabs[4]: render_ai_teaching_page(current_user)

# def _render_student_view() -> None:
#     st.subheader("Students")
#     kw = st.text_input("Search")
#     students = services.search_students(kw) if kw.strip() else models.list_students()
#     render_records(_student_table_rows(students), "No students")

# def _render_course_management(teacher_id: int, courses: list[dict[str, Any]]):
#     st.subheader("My Courses")
#     kw = st.text_input("Search courses")
#     if kw.strip():
#         all_c = models.list_courses(keyword=kw.strip())
#         filtered = [c for c in all_c if int(c.get("teacher_id",0))==teacher_id]
#     else:
#         filtered = courses
#     render_records(_course_table_rows(filtered), "No courses")
#     st.divider()

#     st.subheader("Create Course")
#     with st.form("create_course"):
#         c1,c2,c3 = st.columns(3)
#         code = c1.text_input("Course Code")
#         name = c2.text_input("Course Name")
#         sem = c3.text_input("Semester", "2026-Spring")
#         cred = c1.number_input("Credits", 0.5,10.0,3.0,0.5)
#         cap = c2.number_input("Capacity",1,1000,50,1)
#         target = c3.number_input("Grade Year",1,8,2,1)
#         aw = c1.number_input("Attendance %",0.0,100.0,10.0,5.0)
#         ew = c2.number_input("Experiment %",0.0,100.0,30.0,5.0)
#         xw = c3.number_input("Exam %",0.0,100.0,60.0,5.0)
#         outline = st.text_area("Outline", max_chars=100)
#         if st.form_submit_button("Create"):
#             def act():
#                 services.validate_grade_weights(aw,ew,xw)
#                 return models.create_course(
#                     require_text(code,"Code"), require_text(name,"Name"),
#                     cred, sem, outline.strip(), teacher_id, cap, target, aw,ew,xw
#                 )
#             safe_run(act, "Created", rerun=True)
#     st.divider()

#     st.subheader("Update / Delete")
#     selected, _ = selectbox_from_records(
#         "Select course", courses, "id", _course_label, "c_sel"
#     )
#     if not selected: return
#     cid = int(selected["id"])
#     if services.course_has_grades(cid):
#         st.warning("Has grades, cannot update/delete")
#     c1,c2 = st.columns(2)
#     with c1:
#         with st.form("update_course"):
#             name = st.text_input("Name", selected["course_name"])
#             sem = st.text_input("Semester", selected["semester"])
#             outline = st.text_area("Outline", selected.get("course_outline",""))
#             cred = st.number_input("Credits",0.5,10.0,float(selected["credits"]),0.5)
#             cap = st.number_input("Capacity",1,1000,int(selected["capacity"]),1)
#             target = st.number_input("Grade Year",1,8,int(selected.get("target_grade_year",2)),1)
#             aw = st.number_input("Attendance %",0.0,100.0,float(selected.get("attendance_weight",10)),5.0)
#             ew = st.number_input("Experiment %",0.0,100.0,float(selected.get("experiment_weight",30)),5.0)
#             xw = st.number_input("Exam %",0.0,100.0,float(selected.get("exam_weight",60)),5.0)
#             if st.form_submit_button("Update"):
#                 def act():
#                     services.ensure_course_has_no_grades(cid)
#                     services.validate_grade_weights(aw,ew,xw)
#                     return models.update_course(
#                         cid, require_text(name,"Name"), sem, outline.strip(),
#                         cred, cap, teacher_id, target, aw,ew,xw
#                     )
#                 safe_run(act, "Updated", rerun=True)
#     with c2:
#         with st.form("del_course"):
#             confirm = st.checkbox("Confirm delete")
#             if st.form_submit_button("Delete"):
#                 def act():
#                     if not confirm: raise ValueError("Confirm first")
#                     services.ensure_course_has_no_grades(cid)
#                     return models.delete_course(cid)
#                 safe_run(act, "Deleted", rerun=True)

# def _render_enrollment_info(courses, c_ids):
#     st.subheader("Enrollment Records")
#     if not courses:
#         st.info("No courses")
#         return
#     selected, sel_id = selectbox_from_records(
#         "Filter", courses, "id", _course_label, "enroll_filter"
#     )
#     incl_drop = st.checkbox("Include dropped", False)
#     if selected:
#         enrs = models.list_enrollments(course_id=int(sel_id))
#     else:
#         enrs = _list_teacher_enrollments(c_ids)
#     if not incl_drop:
#         enrs = [e for e in enrs if e["status"]=="enrolled"]
#     render_records(_enrollment_table_rows(enrs), "No records")

# def _render_grade_management(teacher_id, c_ids):
#     st.subheader("Current Grades")
#     st.subheader("📥 Import Grades (XLSX/CSV)")
#     file = st.file_uploader("Upload", type=["csv","xlsx","xls"], help=f"Columns: {REQUIRED_COLUMNS}")
#     if file and st.button("Start Import", type="primary"):
#         with st.spinner("Preparing import..."):
#             res = _import_grades_from_file(file, teacher_id)
#         st.divider()
#         st.subheader("Import Result")
#         c1,c2,c3,c4 = st.columns(4)
#         c1.metric("Created", res['success'])
#         c2.metric("Updated", res['updated'])
#         c3.metric("Skipped", res['skipped'])
#         c4.metric("Failed", res['failed'])
#         if res['errors']:
#             st.markdown("# ❌ Import Errors", unsafe_allow_html=True)
#             for e in res['errors']:
#                 st.markdown(f"""
#                     <div style='background-color:#fef2f2; border-left:5px solid #ef4444; padding:10px; margin:6px 0; border-radius:4px;'>
#                         <span style='color:#dc2626; font-size:16px; font-weight:bold;'>{e}</span>
#                     </div>
#                 """, unsafe_allow_html=True)
#             st.button("✅ Close Errors & Continue", type="primary", use_container_width=True)
#             return
#         st.divider()
#         st.rerun()

#     grades = models.list_grades(teacher_id=teacher_id)
#     render_records(_grade_table_rows(grades), "No grades")
#     st.divider()

#     st.subheader("Record / Update Grade")
#     enrs = _list_teacher_enrollments(c_ids)
#     enrs = [e for e in enrs if e["status"]=="enrolled"]
#     selected, eid = selectbox_from_records(
#         "Select enrollment", enrs, "id", _enrollment_label, "g_sel"
#     )
#     if not selected: return
#     exist = models.get_grade_by_enrollment_id(int(eid))
#     course = models.get_course_by_id(int(selected["course_id"]))
#     if not course:
#         st.error("Course missing")
#         return
#     d_att = float(exist["attendance_score"]) if exist else 0.0
#     d_exp = float(exist["experiment_score"]) if exist else 0.0
#     d_exam = float(exist["exam_score"]) if exist else 0.0
#     d_rem = exist["remarks"] or "" if exist else ""
#     st.info(f"Weights: Attendance {course['attendance_weight']}% · Experiment {course['experiment_weight']}% · Exam {course['exam_weight']}%")
#     with st.form("save_grade"):
#         att = st.number_input("Attendance",0.0,100.0,d_att,0.5)
#         exp = st.number_input("Experiment",0.0,100.0,d_exp,0.5)
#         exam = st.number_input("Exam",0.0,100.0,d_exam,0.5)
#         rem = st.text_area("Remarks", d_rem)
#         if st.form_submit_button("Save Grade"):
#             safe_run(lambda: services.save_grade(
#                 teacher_id, int(eid), att, exp, exam, rem.strip() or None
#             ), "Saved", rerun=True)

from __future__ import annotations
from typing import Any
import streamlit as st
import pandas as pd
import re
from datetime import datetime
from core import models
from core import services
from core.utils import render_records, require_text, safe_run, selectbox_from_records
from pages.ai_teaching import render_ai_teaching_page

def _course_label(course: dict[str, Any]) -> str:
    return f"{course['course_code']} | {course['course_name']}"

def _course_table_rows(courses: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "course_code": course.get("course_code"),
            "course_name": course.get("course_name"),
            "course_outline": course.get("course_outline"),
            "credits": course.get("credits"),
            "capacity": course.get("capacity"),
            "semester": course.get("semester"),
            "target_grade_year": course.get("target_grade_year"),
            "attendance_weight": course.get("attendance_weight", 10),
            "experiment_weight": course.get("experiment_weight", 30),
            "exam_weight": course.get("exam_weight", 60),
            "created_at": course.get("created_at"),
            "updated_at": course.get("updated_at"),
        }
        for course in courses
    ]

def _student_table_rows(students: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "student_no": student.get("student_no"),
            "full_name": student.get("full_name"),
            "gender": student.get("gender"),
            "grade_year": student.get("grade_year"),
            "major": student.get("major"),
            "phone": student.get("phone"),
            "email": student.get("email"),
            "username": student.get("username") or "No account",
            "account_status": "Active" if student.get("user_is_active") else "No account / Disabled",
            "created_at": student.get("created_at"),
            "updated_at": student.get("updated_at"),
        }
        for student in students
    ]

def _enrollment_table_rows(enrollments: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "student_no": enrollment.get("student_no"),
            "student_name": enrollment.get("student_name"),
            "course_code": enrollment.get("course_code"),
            "course_name": enrollment.get("course_name"),
            "status": enrollment.get("status"),
            "enrolled_at": enrollment.get("enrolled_at"),
            "updated_at": enrollment.get("updated_at"),
        }
        for enrollment in enrollments
    ]

def _grade_table_rows(grades: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "student_no": grade.get("student_no"),
            "student_name": grade.get("student_name"),
            "course_code": grade.get("course_code"),
            "course_name": grade.get("course_name"),
            "attendance_score": grade.get("attendance_score"),
            "experiment_score": grade.get("experiment_score"),
            "exam_score": grade.get("exam_score"),
            "final_score": grade.get("score"),
            "weights": (
                f"{float(grade.get('attendance_weight', 0)):.1f}% / "
                f"{float(grade.get('experiment_weight', 0)):.1f}% / "
                f"{float(grade.get('exam_weight', 0)):.1f}%"
            ),
            "remarks": grade.get("remarks"),
            "graded_at": grade.get("graded_at"),
            "updated_at": grade.get("updated_at"),
        }
        for grade in grades
    ]

def _enrollment_label(enrollment: dict[str, Any]) -> str:
    return (
        f"{enrollment['student_no']} {enrollment['student_name']} -> "
        f"{enrollment['course_code']} {enrollment['course_name']} "
        f"({enrollment['status']})"
    )

def _list_teacher_enrollments(teacher_course_ids: set[int]) -> list[dict[str, Any]]:
    if not teacher_course_ids:
        return []
    all_enrollments = models.list_enrollments()
    return [e for e in all_enrollments if int(e["course_id"]) in teacher_course_ids]

REQUIRED_COLUMNS = [
    'student_no', 'student_name', 'course_code', 'course_name',
    'attendance_score', 'experiment_score', 'exam_score', 'final_score',
    'weight', 'remarks'
]

def parse_weight_string(weight_str):
    numbers = re.findall(r"\d+\.?\d*", weight_str)
    if len(numbers) != 3:
        raise ValueError(f"Invalid weight format: {weight_str}")
    return float(numbers[0]), float(numbers[1]), float(numbers[2])

def _import_grades_from_file(uploaded_file, teacher_id: int) -> dict[str, Any]:
    result = {
        'success': 0, 'updated': 0, 'skipped': 0, 'failed': 0, 'errors': []
    }
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        elif uploaded_file.name.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(uploaded_file)
        else:
            result['errors'].append(f"Unsupported file: {uploaded_file.name}")
            return result
    except Exception as e:
        result['errors'].append(f"Read failed: {str(e)}")
        return result

    if list(df.columns) != REQUIRED_COLUMNS:
        result['errors'].append(f"Columns must be: {REQUIRED_COLUMNS}")
        return result

    # 预校验1：表格内学号与姓名必须一一对应
    student_mapping = {}
    for idx, row in df.iterrows():
        student_no = str(row['student_no']).strip()
        student_name = str(row['student_name']).strip()
        
        if pd.isna(row['student_no']) or pd.isna(row['student_name']):
            continue
            
        if student_no in student_mapping:
            if student_mapping[student_no] != student_name:
                result['errors'].append(f"第{idx+2}行：学号 {student_no} 对应多个姓名，系统不允许！")
        else:
            student_mapping[student_no] = student_name

    # 预校验2：表格内课程编号与课程名称必须一一对应
    course_mapping = {}
    for idx, row in df.iterrows():
        course_code = str(row['course_code']).strip()
        course_name = str(row['course_name']).strip()

        if pd.isna(row['course_code']) or pd.isna(row['course_name']):
            continue
            
        if course_code in course_mapping:
            if course_mapping[course_code] != course_name:
                result['errors'].append(f"第{idx+2}行：课程编号 {course_code} 对应多个课程名称，系统不允许！")
        else:
            course_mapping[course_code] = course_name

    course_name_map = {}
    course_weight_map = {}
    conflict_courses = {}
    for idx, row in df.iterrows():
        code = str(row['course_code']).strip()
        name = str(row['course_name']).strip()
        w_str = str(row['weight']).strip()
        try:
            aw, ew, xw = parse_weight_string(w_str)
        except:
            result['errors'].append(f"Row {idx+2}: Invalid weight format '{w_str}'")
            return result

        if code not in course_name_map:
            course_name_map[code] = name
        else:
            if course_name_map[code] != name:
                key = f"Course {code} | Name conflict: {course_name_map[code]} vs {name}"
                conflict_courses[key] = "Same course code cannot have different names"

        if code not in course_weight_map:
            course_weight_map[code] = w_str
        else:
            if course_weight_map[code] != w_str:
                key = f"Course {code} | Weight conflict"
                allw = f"{course_weight_map[code]} , {w_str}"
                conflict_courses[key] = f"Weights: {allw}"

    total = len(df)
    st.markdown("---")
    st.markdown("### 📊 Import Progress", unsafe_allow_html=True)
    progress_container = st.container()
    with progress_container:
        progress_bar = st.progress(0.0)
        status_text = st.empty()
        status_text.markdown(f"<h4>Ready to import: 0/{total}</h4>", unsafe_allow_html=True)

    if conflict_courses:
        st.markdown("---")
        st.markdown("# ❌ ERROR: Data Conflicts Found", unsafe_allow_html=True)
        for c, msg in conflict_courses.items():
            st.markdown(f"""
                <div style='background-color:#fee2e2; border-left:5px solid #dc2626; padding:12px; margin:8px 0; border-radius:4px;'>
                    <span style='color:#dc2626; font-size:18px; font-weight:bold;'>{c}: {msg}</span>
                </div>
            """, unsafe_allow_html=True)
        result['errors'].append("Import stopped due to conflicts")
        return result

    for idx, row in df.iterrows():
        current = idx + 1
        progress = current / total
        progress_bar.progress(progress)
        status_text.markdown(f"<h4>Processing: {current}/{total} ({progress:.0%})</h4>", unsafe_allow_html=True)
        
        row_num = idx + 2
        try:
            sno = str(row['student_no']).strip()
            sname = str(row['student_name']).strip()
            code = str(row['course_code']).strip()
            cname = str(row['course_name']).strip()
            att = float(row['attendance_score'])
            exp = float(row['experiment_score'])
            exam = float(row['exam_score'])
            final = float(row['final_score'])
            weight_str = str(row['weight']).strip()
            rem = str(row['remarks']).strip() if pd.notna(row['remarks']) else None

            for s, n in [(att,'att'), (exp,'exp'), (exam,'exam')]:
                if not (0 <= s <= 100):
                    raise ValueError(f"{n} must be 0-100")

            # 校验1：数据库中学号与姓名必须匹配
            stu = models.get_student_by_student_no(sno)
            if not stu:
                raise ValueError(f"未找到学号 {sno}")
            
            real_name = str(stu["full_name"]).strip()
            if real_name != sname:
                raise ValueError(f"学号 {sno} 系统姓名为「{real_name}」，与表格姓名「{sname}」不匹配")

            stu_id = int(stu['id'])
            # 校验2：课程必须存在，且课程编号与名称必须匹配
            course = models.get_course_by_code(code)
            if not course:
                raise ValueError(f"未找到课程编号 {code}")
            
            real_course_name = str(course["course_name"]).strip()
            if real_course_name != cname:
                raise ValueError(f"课程编号 {code} 系统名称为「{real_course_name}」，与表格名称「{cname}」不匹配")
            
            cid = int(course['id'])

            aw, ew, xw = parse_weight_string(weight_str)
            enroll = models.get_enrollment_by_student_course(stu_id, cid)
            if not enroll or enroll['status'] != 'enrolled':
                raise ValueError(f"学生未选修该课程")
            eid = int(enroll['id'])

            exist = models.get_grade_by_enrollment_id(eid)
            if exist:
                same = (
                    abs(float(exist['attendance_score'])-att)<0.001 and
                    abs(float(exist['experiment_score'])-exp)<0.001 and
                    abs(float(exist['exam_score'])-exam)<0.001 and
                    (exist.get('remarks') or '') == (rem or '')
                )
                if same:
                    result['skipped'] +=1
                    continue
                models.update_grade(
                    int(exist['id']), att, exp, exam, final, rem, teacher_id
                )
                result['updated'] +=1
            else:
                models.create_grade(
                    eid, teacher_id, att, exp, exam, final, rem
                )
                result['success'] +=1

        except Exception as e:
            result['failed'] +=1
            result['errors'].append(f"第{row_num}行：{str(e)}")

    progress_bar.progress(1.0)
    status_text.markdown("<h4 style='color:#059669;'>✅ Import Completed</h4>", unsafe_allow_html=True)
    return result

def render_teacher_page(current_user: dict) -> None:
    page = st.container()
    with page:
        st.title("Teacher Dashboard")
        teacher = models.get_teacher_by_user_id(int(current_user["id"]))
        if not teacher:
            st.error("Teacher profile missing")
            return
        teacher_id = int(teacher["id"])
        courses = models.list_courses(teacher_id=teacher_id)
        c_ids = {int(c["id"]) for c in courses}
        tabs = st.tabs([
            "View Students", "Course Management",
            "Enrollment Info", "Grade Management", "AI Teaching"
        ])
        with tabs[0]: _render_student_view()
        with tabs[1]: _render_course_management(teacher_id, courses)
        with tabs[2]: _render_enrollment_info(courses, c_ids)
        with tabs[3]: _render_grade_management(teacher_id, c_ids)
        with tabs[4]: render_ai_teaching_page(current_user)

def _render_student_view() -> None:
    st.subheader("Students")
    kw = st.text_input("Search")
    students = services.search_students(kw) if kw.strip() else models.list_students()
    render_records(_student_table_rows(students), "No students")

def _render_course_management(teacher_id: int, courses: list[dict[str, Any]]):
    st.subheader("My Courses")
    kw = st.text_input("Search courses")
    if kw.strip():
        all_c = models.list_courses(keyword=kw.strip())
        filtered = [c for c in all_c if int(c.get("teacher_id",0))==teacher_id]
    else:
        filtered = courses
    render_records(_course_table_rows(filtered), "No courses")

    st.divider()
    st.subheader("Create Course")
    with st.form("create_course"):
        c1,c2,c3 = st.columns(3)
        code = c1.text_input("Course Code")
        name = c2.text_input("Course Name")
        sem = c3.text_input("Semester", "2026-Spring")
        cred = c1.number_input("Credits", 0.5,10.0,3.0,0.5)
        cap = c2.number_input("Capacity",1,1000,50,1)
        target = c3.number_input("Grade Year",1,8,2,1)
        aw = c1.number_input("Attendance %",0.0,100.0,10.0,5.0)
        ew = c2.number_input("Experiment %",0.0,100.0,30.0,5.0)
        xw = c3.number_input("Exam %",0.0,100.0,60.0,5.0)
        outline = st.text_area("Outline", max_chars=100)
        if st.form_submit_button("Create"):
            def act():
                services.validate_grade_weights(aw,ew,xw)
                return models.create_course(
                    require_text(code,"Code"), require_text(name,"Name"),
                    cred, sem, outline.strip(), teacher_id, cap, target, aw,ew,xw
                )
            safe_run(act, "Created", rerun=True)

    st.divider()
    st.subheader("Update / Delete")
    selected, _ = selectbox_from_records(
        "Select course", courses, "id", _course_label, "c_sel"
    )
    if not selected: return
    cid = int(selected["id"])
    if services.course_has_grades(cid):
        st.warning("Has grades, cannot update/delete")
    c1,c2 = st.columns(2)
    with c1:
        with st.form("update_course"):
            name = st.text_input("Name", selected["course_name"])
            sem = st.text_input("Semester", selected["semester"])
            outline = st.text_area("Outline", selected.get("course_outline",""))
            cred = st.number_input("Credits",0.5,10.0,float(selected["credits"]),0.5)
            cap = st.number_input("Capacity",1,1000,int(selected["capacity"]),1)
            target = st.number_input("Grade Year",1,8,int(selected.get("target_grade_year",2)),1)
            aw = st.number_input("Attendance %",0.0,100.0,float(selected.get("attendance_weight",10)),5.0)
            ew = st.number_input("Experiment %",0.0,100.0,float(selected.get("experiment_weight",30)),5.0)
            xw = st.number_input("Exam %",0.0,100.0,float(selected.get("exam_weight",60)),5.0)
            if st.form_submit_button("Update"):
                def act():
                    services.ensure_course_has_no_grades(cid)
                    services.validate_grade_weights(aw,ew,xw)
                    return models.update_course(
                        cid, require_text(name,"Name"), sem, outline.strip(),
                        cred, cap, teacher_id, target, aw,ew,xw
                    )
                safe_run(act, "Updated", rerun=True)
    with c2:
        with st.form("del_course"):
            confirm = st.checkbox("Confirm delete")
            if st.form_submit_button("Delete"):
                def act():
                    if not confirm: raise ValueError("Confirm first")
                    services.ensure_course_has_no_grades(cid)
                    return models.delete_course(cid)
                safe_run(act, "Deleted", rerun=True)

def _render_enrollment_info(courses, c_ids):
    st.subheader("Enrollment Records")
    if not courses:
        st.info("No courses")
        return
    selected, sel_id = selectbox_from_records(
        "Filter", courses, "id", _course_label, "enroll_filter"
    )
    incl_drop = st.checkbox("Include dropped", False)
    if selected:
        enrs = models.list_enrollments(course_id=int(sel_id))
    else:
        enrs = _list_teacher_enrollments(c_ids)
    if not incl_drop:
        enrs = [e for e in enrs if e["status"]=="enrolled"]
    render_records(_enrollment_table_rows(enrs), "No records")

def _render_import_grades(teacher_id):
    st.subheader("📥 Import Grades (XLSX/CSV)")
    file = st.file_uploader("Upload", type=["csv","xlsx","xls"], help=f"Columns: {REQUIRED_COLUMNS}")
    if file and st.button("Start Import", type="primary"):
        with st.spinner("Preparing import..."):
            res = _import_grades_from_file(file, teacher_id)
        st.divider()
        st.subheader("Import Result")
        c1,c2,c3,c4 = st.columns(4)
        c1.metric("Created", res['success'])
        c2.metric("Updated", res['updated'])
        c3.metric("Skipped", res['skipped'])
        c4.metric("Failed", res['failed'])
        if res['errors']:
            st.markdown("# ❌ Import Errors", unsafe_allow_html=True)
            for e in res['errors']:
                st.markdown(f"""
                    <div style='background-color:#fef2f2; border-left:5px solid #ef4444; padding:10px; margin:6px 0; border-radius:4px;'>
                        <span style='color:#dc2626; font-size:16px; font-weight:bold;'>{e}</span>
                    </div>
                """, unsafe_allow_html=True)
            st.button("✅ Close Errors & Continue", type="primary", use_container_width=True)
            return
        st.divider()
        st.rerun()


def _render_grade_management(teacher_id, c_ids):
    st.subheader("Current Grades")
    grades = models.list_grades(teacher_id=teacher_id)
    render_records(_grade_table_rows(grades), "No grades")
    st.divider()
    st.subheader("Record / Update Grade")
    enrs = _list_teacher_enrollments(c_ids)
    enrs = [e for e in enrs if e["status"]=="enrolled"]
    selected, eid = selectbox_from_records(
        "Select enrollment", enrs, "id", _enrollment_label, "g_sel"
    )
    if selected:
        exist = models.get_grade_by_enrollment_id(int(eid))
        course = models.get_course_by_id(int(selected["course_id"]))
        if not course:
            st.error("Course missing")
        else:
            d_att = float(exist["attendance_score"]) if exist else 0.0
            d_exp = float(exist["experiment_score"]) if exist else 0.0
            d_exam = float(exist["exam_score"]) if exist else 0.0
            d_rem = exist["remarks"] or "" if exist else ""
            st.info(f"Weights: Attendance {course['attendance_weight']}% · Experiment {course['experiment_weight']}% · Exam {course['exam_weight']}%")
            with st.form("save_grade"):
                att = st.number_input("Attendance",0.0,100.0,d_att,0.5)
                exp = st.number_input("Experiment",0.0,100.0,d_exp,0.5)
                exam = st.number_input("Exam",0.0,100.0,d_exam,0.5)
                rem = st.text_area("Remarks", d_rem)
                if st.form_submit_button("Save Grade"):
                    safe_run(lambda: services.save_grade(
                        teacher_id, int(eid), att, exp, exam, rem.strip() or None
                    ), "Saved", rerun=True)

    st.divider()
    _render_import_grades(teacher_id)
