from __future__ import annotations
from typing import Any
import streamlit as st
import pandas as pd
import re
from io import BytesIO
from core import models
from core import services
from core.utils import render_records, require_text, safe_run, selectbox_from_records, write_operation_log

# 权重列固定定义
REQUIRED_COLUMNS = [
    'student_no', 'student_name', 'course_code', 'course_name',
    'attendance_score', 'experiment_score', 'exam_score', 'final_score',
    'weight', 'remarks'
]

# ===================== 通用分页工具函数 =====================
def paginate_data(data_list: list, page_num: int, page_size: int = 15) -> tuple[list, int]:
    """通用分页"""
    total = len(data_list)
    total_pages = (total + page_size - 1) // page_size
    start = (page_num - 1) * page_size
    end = start + page_size
    return data_list[start:end], total_pages

# ===================== 会话状态初始化（分页+报错隔离） =====================
# 表格分页状态
if "student_view_page" not in st.session_state or st.session_state.student_view_page < 1:
    st.session_state.student_view_page = 1
if "course_view_page" not in st.session_state or st.session_state.course_view_page < 1:
    st.session_state.course_view_page = 1
if "enrollment_view_page" not in st.session_state or st.session_state.enrollment_view_page < 1:
    st.session_state.enrollment_view_page = 1
if "grade_view_page" not in st.session_state or st.session_state.grade_view_page < 1:
    st.session_state.grade_view_page = 1
# 新增：成绩排名分页
if "rank_view_page" not in st.session_state or st.session_state.rank_view_page < 1:
    st.session_state.rank_view_page = 1

# 成绩导入 报错分页&数据存储
if "grade_import_error_list" not in st.session_state:
    st.session_state.grade_import_error_list = []
if "grade_import_error_page" not in st.session_state:
    st.session_state.grade_import_error_page = 1
if "grade_import_error_df" not in st.session_state:
    st.session_state.grade_import_error_df = None
if "grade_import_error_rows" not in st.session_state:
    st.session_state.grade_import_error_rows = set()
if "last_grade_file_id" not in st.session_state:
    st.session_state.last_grade_file_id = None

# ===================== 统一分页样式美化 =====================
def render_pagination_style():
    st.markdown(
        """
        <style>
        div[data-testid="stNumberInput"] input::-webkit-outer-spin-button,
        div[data-testid="stNumberInput"] input::-webkit-inner-spin-button {
            -webkit-appearance: none;
            margin: 0;
        }
        div[data-testid="stNumberInput"] input[type="number"] {
            -moz-appearance: textfield;
        }
        div[data-testid="stNumberInput"] .stNumberInput__controls {
            display: none !important;
        }
        div[data-testid="stNumberInput"] > div {
            display: flex;
            justify-content: center;
        }
        div[data-testid="stNumberInput"] > div > input {
            width: 60px !important;
            text-align: center !important;
            padding: 0 !important;
            line-height: 38px !important;
            height: 38px !important;
            margin: 0 auto;
        }
        .stButton > button {
            height: 38px !important;
            line-height: 1.2 !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

# ===================== 通用数据分页组件 =====================
def render_pagination(current_page: int, total_pages: int, page_key: str) -> None:
    input_key = f"{page_key}_input"
    if input_key not in st.session_state:
        st.session_state[input_key] = current_page

    col_wrapper = st.columns([2, 6, 2])[1]
    with col_wrapper:
        col_prev, col_page_input, col_jump, col_next = st.columns([1, 1, 1, 1])
        with col_prev:
            if st.button("上一页", disabled=current_page <= 1, key=f"{page_key}_prev"):
                new_page = current_page - 1
                st.session_state[page_key] = new_page
                if input_key in st.session_state:
                    del st.session_state[input_key]
                st.rerun()
        with col_page_input:
            jump_page = st.number_input(
                "页码", min_value=1, max_value=max(1, total_pages),
                value=current_page, step=1, key=input_key,
                label_visibility="collapsed", format="%d"
            )
        with col_jump:
            if st.button("跳转", key=f"{page_key}_jump"):
                target_page = max(1, min(int(jump_page), total_pages))
                st.session_state[page_key] = target_page
                if input_key in st.session_state:
                    del st.session_state[input_key]
                st.rerun()
        with col_next:
            if st.button("下一页", disabled=current_page >= total_pages, key=f"{page_key}_next"):
                new_page = current_page + 1
                st.session_state[page_key] = new_page
                if input_key in st.session_state:
                    del st.session_state[input_key]
                st.rerun()

# ===================== 报错列表分页渲染组件（通用） =====================
def render_error_paginate(error_list: list, page_key: str, page_size: int = 10):
    """独立报错分页组件"""
    if not error_list:
        return

    if page_key not in st.session_state or st.session_state[page_key] < 1:
        st.session_state[page_key] = 1

    current_page = st.session_state[page_key]
    page_data, total_pages = paginate_data(error_list, current_page, page_size)

    if current_page > total_pages and total_pages > 0:
        st.session_state[page_key] = total_pages
        current_page = total_pages

    st.info(f"共 {len(error_list)} 条错误，每页 {page_size} 条，第 {current_page}/{total_pages} 页")
    for err in page_data:
        st.warning(f"- {err}")

    col_prev, col_page, col_next = st.columns([1, 2, 1])
    with col_prev:
        if st.button("上一页", disabled=current_page <= 1, key=f"{page_key}_prev"):
            st.session_state[page_key] -= 1
            st.rerun()
    with col_page:
        jump = st.number_input(
            "跳转页码", min_value=1, max_value=total_pages,
            value=current_page, label_visibility="collapsed", key=f"{page_key}_jump"
        )
        if jump != current_page:
            st.session_state[page_key] = jump
            st.rerun()
    with col_next:
        if st.button("下一页", disabled=current_page >= total_pages, key=f"{page_key}_next"):
            st.session_state[page_key] += 1
            st.rerun()

# ===================== 通用导出失败行工具函数（修复变量名错误） =====================
def export_failed_rows(original_df: pd.DataFrame, error_line_set: set, file_suffix: str = ".xlsx") -> BytesIO | None:
    """提取失败行并生成文件，行号为Excel实际行(从2开始)"""
    if not error_line_set or original_df is None or original_df.empty:
        return None
    error_indexes = [line - 2 for line in original_df.index if (line - 2) in error_line_set]
    if not error_indexes:
        return None
    failed_df = original_df.loc[error_indexes].copy()

    output = BytesIO()
    if file_suffix == ".csv":
        # 修复此处变量名 failed → failed_df
        failed_df.to_csv(output, index=False, encoding="utf-8-sig")
    else:
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            failed_df.to_excel(writer, index=False)
    output.seek(0)
    return output

def parse_weight_string(weight_str):
    numbers = re.findall(r"\d+\.?\d*", weight_str)
    if len(numbers) != 3:
        raise ValueError(f"Invalid weight format: {weight_str}")
    return float(numbers[0]), float(numbers[1]), float(numbers[2])

def _import_grades_from_file(uploaded_file, teacher_id, current_operator):
    result = {
        "success": 0, "updated": 0, "skipped": 0, "failed": 0, "errors": []
    }
    raw_df = pd.DataFrame()
    error_line_set = set()

    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        elif uploaded_file.name.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(uploaded_file)
        else:
            result["errors"].append(f"Unsupported file: {uploaded_file.name}")
            st.session_state.grade_import_error_df = None
            st.session_state.grade_import_error_rows = set()
            return result
        raw_df = df.copy()
    except Exception as e:
        result["errors"].append(f"Read failed: {str(e)}")
        st.session_state.grade_import_error_df = None
        st.session_state.grade_import_error_rows = set()
        return result

    # 列名校验
    if list(df.columns) != REQUIRED_COLUMNS:
        result["errors"].append(f"Columns must be: {REQUIRED_COLUMNS}")
        st.session_state.grade_import_error_df = None
        st.session_state.grade_import_error_rows = set()
        return result

    # 学号/姓名 全局校验
    student_mapping = {}
    for idx, row in df.iterrows():
        sno = str(row['student_no']).strip()
        sname = str(row['student_name']).strip()
        if pd.isna(sno) or pd.isna(sname):
            continue
        if sno in student_mapping and student_mapping[sno] != sname:
            line_num = idx + 2
            result["errors"].append(f"第{line_num}行：学号{sno}对应多个姓名")
            error_line_set.add(line_num)
    if result["errors"]:
        st.session_state.grade_import_error_df = raw_df
        st.session_state.grade_import_error_rows = error_line_set
        return result

    # 课程编号/名称/权重 全局校验
    course_name_map = {}
    course_weight_map = {}
    conflict_courses = {}
    weight_parse_failed = False
    for idx, row in df.iterrows():
        code = str(row['course_code']).strip()
        name = str(row['course_name']).strip()
        w_str = str(row['weight']).strip()
        try:
            aw, ew, xw = parse_weight_string(w_str)
        except:
            line_num = idx + 2
            result["errors"].append(f"第{line_num}行: Invalid weight format '{w_str}'")
            error_line_set.add(line_num)
            weight_parse_failed = True
            continue

        if code not in course_name_map:
            course_name_map[code] = name
        elif course_name_map[code] != name:
            key = f"Course {code} | Name conflict: {course_name_map[code]} vs {name}"
            conflict_courses[key] = "Same course code cannot have different names"
            error_line_set.add(idx + 2)

        if code not in course_weight_map:
            course_weight_map[code] = w_str
        elif course_weight_map[code] != w_str:
            key = f"Course {code} | Weight conflict"
            conflict_courses[key] = f"Weights: {course_weight_map[code]} , {w_str}"
            error_line_set.add(idx + 2)

    if conflict_courses:
        for k, v in conflict_courses.items():
            result["errors"].append(f"{k}: {v}")
    if weight_parse_failed or conflict_courses:
        st.session_state.grade_import_error_df = raw_df
        st.session_state.grade_import_error_rows = error_line_set
        return result

    # 逐行业务处理
    total = len(df)
    st.markdown("---")
    st.markdown("### 📊 Import Progress", unsafe_allow_html=True)
    progress_bar = st.progress(0.0)
    status_text = st.empty()

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
            attendance_score = float(row['attendance_score'])
            experiment_score = float(row['experiment_score'])
            exam_score = float(row['exam_score'])
            final = float(row['final_score'])
            weight_str = str(row['weight']).strip()
            rem = str(row['remarks']).strip() if pd.notna(row['remarks']) else None

            for score, name in [(attendance_score, 'att'), (experiment_score, 'exp'), (exam_score, 'exam')]:
                if not (0 <= score <= 100):
                    raise ValueError(f"{name} must be 0-100")

            stu = models.get_student_by_student_no(sno)
            if not stu:
                raise ValueError(f"未找到学号 {sno}")
            if str(stu["full_name"]).strip() != sname:
                raise ValueError(f"学号{sno}系统姓名与表格不匹配")
            stu_id = int(stu["id"])

            course = models.get_course_by_code(code)
            if not course:
                raise ValueError(f"未找到课程 {code}")
            if str(course["course_name"]).strip() != cname:
                raise ValueError(f"课程{code}系统名称与表格不匹配")
            cid = int(course["id"])

            aw, ew, xw = parse_weight_string(weight_str)
            enroll = models.get_enrollment_by_student_course(stu_id, cid)
            if not enroll or enroll["status"] != "enrolled":
                raise ValueError("学生未选修该课程")
            eid = int(enroll["id"])

            exist = models.get_grade_by_enrollment_id(eid)
            if exist:
                same = (
                    abs(float(exist["attendance_score"]) - attendance_score) < 0.001 and
                    abs(float(exist["experiment_score"]) - experiment_score) < 0.001 and
                    abs(float(exist["exam_score"]) - exam_score) < 0.001 and
                    (exist.get("remarks") or "") == (rem or "")
                )
                if same:
                    result["skipped"] += 1
                    continue
                models.update_grade(
                    int(exist["id"]), attendance_score, experiment_score, exam_score, final, rem, teacher_id
                )
                # 批量导入更新成绩 - 写入操作日志
                write_operation_log(
                    current_operator,
                    operate_type="批量导入更新成绩",
                    operate_content=f"课程{code}，学号{sno}，更新各项分数",
                    target_type="grade",
                    target_id=int(exist["id"])
                )
                result["updated"] += 1
            else:
                new_grade = models.create_grade(
                    eid, teacher_id, attendance_score, experiment_score, exam_score, final, rem
                )
                # 批量导入新增成绩 - 写入操作日志
                write_operation_log(
                    current_operator,
                    operate_type="批量导入新增成绩",
                    operate_content=f"课程{code}，学号{sno}，录入成绩",
                    target_type="grade",
                    target_id=new_grade["id"]
                )
                result["success"] += 1
        except Exception as e:
            result["failed"] += 1
            result["errors"].append(f"第{row_num}行：{str(e)}")
            error_line_set.add(row_num)

    progress_bar.progress(1.0)
    status_text.markdown("<h4 style='color:#059669;'>✅ Import Completed</h4>", unsafe_allow_html=True)

    st.session_state.grade_import_error_df = raw_df
    st.session_state.grade_import_error_rows = error_line_set
    return result

def _course_label(course: dict) -> str:
    return f"{course['course_code']} | {course['course_name']}"

def _student_label(student: dict) -> str:
    return f"{student['student_no']} | {student['full_name']}"

def _enrollment_label(enrollment: dict) -> str:
    return (
        f"{enrollment['student_no']} {enrollment['student_name']} -> "
        f"{enrollment['course_code']} {enrollment['course_name']} "
        f"({enrollment['status']})"
    )

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
            "course_code": grade.get("course_name"),
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

def _list_teacher_enrollments(teacher_course_ids: set[int]) -> list[dict[str, Any]]:
    if not teacher_course_ids:
        return []
    all_enrollments = models.list_enrollments()
    return [e for e in all_enrollments if int(e["course_id"]) in teacher_course_ids]

def _render_import_grades(teacher_id, current_operator):
    st.subheader("📥 Import Grades (XLSX/CSV)")
    uploaded_file = st.file_uploader(
        "Upload", type=["csv", "xlsx", "xls"], help=f"Columns: {REQUIRED_COLUMNS}",
        key="grade_import_file"
    )
    # 切换文件清空旧状态
    if uploaded_file and st.session_state.get("last_grade_file_id") != uploaded_file.file_id:
        st.session_state.grade_import_error_list = []
        st.session_state.grade_import_error_page = 1
        st.session_state.grade_import_error_df = None
        st.session_state.grade_import_error_rows = set()
        st.session_state.last_grade_file_id = uploaded_file.file_id

    if uploaded_file and st.button("Start Import", type="primary"):
        with st.spinner("Preparing import..."):
            res = _import_grades_from_file(uploaded_file, teacher_id, current_operator)
        st.session_state.grade_import_error_list = res["errors"]
        st.divider()
        st.subheader("Import Result")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Created", res["success"])
        c2.metric("Updated", res["updated"])
        c3.metric("Skipped", res["skipped"])
        c4.metric("Failed", res["failed"])

    # 报错分页展示
    if st.session_state.grade_import_error_list:
        st.divider()
        st.warning("导入错误列表：")
        render_error_paginate(st.session_state.grade_import_error_list, "grade_import_error_page", page_size=10)

        # 下载失败行文件
        err_df = st.session_state.grade_import_error_df
        err_rows = st.session_state.grade_import_error_rows
        if err_df is not None and err_rows and len(err_rows) > 0:
            buf = export_failed_rows(err_df, err_rows, ".xlsx")
            if buf:
                st.download_button(
                    label="📥 下载失败行文件(Excel)",
                    data=buf,
                    file_name="成绩导入_失败行.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key="dl_grade_error_rows"
                )

        # 清空错误
        if st.button("✅ Close Errors & Continue", type="primary", use_container_width=True, key="close_grade_err"):
            st.session_state.grade_import_error_list = []
            st.session_state.grade_import_error_page = 1
            st.session_state.grade_import_error_df = None
            st.session_state.grade_import_error_rows = set()
            st.rerun()

# ===================== 成绩统计模块（新增排名分页） =====================
def _render_grade_statistics(all_grades):
    st.subheader("📈 Grade Statistics & Ranking")
    if not all_grades:
        st.info("No grade data available for statistics")
        return

    df = pd.DataFrame(all_grades)
    df.rename(columns={"score": "final_score"}, inplace=True)
    df = df[df["final_score"].notna()]
    df["final_score"] = df["final_score"].astype(float)

    all_codes = sorted(df["course_code"].unique().tolist())
    select_course = st.selectbox(
        "Select Course (All = Default)",
        options=["All Courses"] + all_codes,
        key="stat_course_sel"
    )

    filter_df = df.copy()
    if select_course != "All Courses":
        filter_df = filter_df[filter_df["course_code"] == select_course]

    if filter_df.empty:
        st.warning("No data after filtering")
        return

    scores = filter_df["final_score"].tolist()
    avg_score = sum(scores) / len(scores)
    median_score = pd.Series(scores).median()
    max_score = max(scores)
    min_score = min(scores)

    st.subheader("Basic Statistics")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Average Score", f"{avg_score:.2f}")
    c2.metric("Median Score", f"{median_score:.2f}")
    c3.metric("Highest Score", f"{max_score:.2f}")
    c4.metric("Lowest Score", f"{min_score:.2f}")

    st.divider()
    st.subheader("Student Ranking (Descending)")

    # 排名数据处理 + 分页
    rank_df = filter_df[["student_no", "student_name", "course_code", "course_name", "final_score"]].copy()
    rank_df = rank_df.sort_values("final_score", ascending=False).reset_index(drop=True)
    rank_df.insert(0, "Rank", range(1, len(rank_df)+1))

    RANK_PAGE_SIZE = 15
    current_rank_page = max(1, st.session_state.rank_view_page)
    rank_data, total_rank_pages = paginate_data(rank_df.to_dict("records"), current_rank_page, RANK_PAGE_SIZE)

    if current_rank_page > total_rank_pages and total_rank_pages > 0:
        st.session_state.rank_view_page = total_rank_pages
        current_rank_page = total_rank_pages

    st.write(f"共 {len(rank_df)} 条排名数据，每页 {RANK_PAGE_SIZE} 条，第 {current_rank_page}/{total_rank_pages} 页")
    render_records(rank_data, "暂无排名数据")
    render_pagination_style()
    render_pagination(current_rank_page, total_rank_pages, "rank_view_page")

def _render_grade_management(teacher_id, c_ids, current_operator):
    st.subheader("Current Grades")
    grades = models.list_grades(teacher_id=teacher_id)
    PAGE_SIZE = 15
    page_key = "grade_view_page"
    current_page = max(1, st.session_state[page_key])
    page_data, total_pages = paginate_data(grades, current_page, PAGE_SIZE)

    if current_page > total_pages and total_pages > 0:
        st.session_state.grade_view_page = total_pages
        current_page = total_pages

    st.write(f"共 {len(grades)} 条数据，每页 {PAGE_SIZE} 条，总页数：{total_pages}")
    render_records(_grade_table_rows(page_data), "No grades")
    render_pagination_style()
    render_pagination(current_page, total_pages, page_key)

    st.divider()
    _render_grade_statistics(grades)

    st.divider()
    _render_import_grades(teacher_id, current_operator)

    st.divider()
    st.subheader("Record / Update Grade")
    enrollments = _list_teacher_enrollments(c_ids)
    enrollments = [e for e in enrollments if e["status"] == "enrolled"]
    selected_enrollment, selected_enrollment_id = selectbox_from_records(
        "Select enrollment",
        enrollments,
        id_key="id",
        label_builder=_enrollment_label,
        key="teacher_grade_enrollment_select",
    )
    if selected_enrollment:
        existing = models.get_grade_by_enrollment_id(int(selected_enrollment_id))
        course = models.get_course_by_id(int(selected_enrollment["course_id"]))
        if not course:
            st.error("Course missing")
            return
        d_att = float(existing["attendance_score"]) if existing else 0.0
        d_exp = float(existing["experiment_score"]) if existing else 0.0
        d_exam = float(existing["exam_score"]) if existing else 0.0
        d_rem = existing["remarks"] or "" if existing else ""
        st.info(f"Weights: Attendance {course['attendance_weight']}% · Experiment {course['experiment_weight']}% · Exam {course['exam_weight']}%")
        with st.form("save_grade"):
            attendance_score = st.number_input("Attendance", min_value=0.0, max_value=100.0, value=d_att, step=0.5)
            experiment_score = st.number_input("Experiment", min_value=0.0, max_value=100.0, value=d_exp, step=0.5)
            exam_score = st.number_input("Exam", min_value=0.0, max_value=100.0, value=d_exam, step=0.5)
            remarks = st.text_area("Remarks", value=d_rem)
            if st.form_submit_button("Save Grade"):
                def action():
                    res = services.save_grade(
                        teacher_id, int(selected_enrollment_id), attendance_score, experiment_score, exam_score, remarks.strip() or None
                    )
                    # 单条成绩新增/更新 写入操作日志
                    if existing:
                        log_type = "更新成绩"
                        log_content = f"课程{course['course_code']}，学号{selected_enrollment['student_no']}，更新分数"
                    else:
                        log_type = "录入成绩"
                        log_content = f"课程{course['course_code']}，学号{selected_enrollment['student_no']}，录入成绩"
                    write_operation_log(
                        current_operator,
                        operate_type=log_type,
                        operate_content=log_content,
                        target_type="grade",
                        target_id=res["id"]
                    )
                    return res
                safe_run(action, "Saved", rerun=True)

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
        with tabs[0]:
            _render_student_view()
        with tabs[1]:
            _render_course_management(teacher_id, courses, current_user)
        with tabs[2]:
            _render_enrollment_info(courses, c_ids)
        with tabs[3]:
            _render_grade_management(teacher_id, c_ids, current_user)
        with tabs[4]:
            from pages.ai_teaching import render_ai_teaching_page
            render_ai_teaching_page(current_user)

def _render_student_view() -> None:
    st.subheader("Students")
    kw = st.text_input("Search")
    students = models.list_students(keyword=kw) if kw.strip() else models.list_students()

    PAGE_SIZE = 15
    page_key = "student_view_page"
    current_page = max(1, st.session_state[page_key])
    page_data, total_pages = paginate_data(students, current_page, PAGE_SIZE)

    if current_page > total_pages and total_pages > 0:
        st.session_state.student_view_page = total_pages
        current_page = total_pages

    st.write(f"共 {len(students)} 条数据，每页 {PAGE_SIZE} 条，总页数：{total_pages}")
    render_records(_student_table_rows(page_data), "No students")
    render_pagination_style()
    render_pagination(current_page, total_pages, page_key)

def _render_course_management(teacher_id: int, courses: list[dict[str, Any]], current_user):
    st.subheader("My Courses")
    kw = st.text_input("Search courses")
    if kw.strip():
        # 1. 全局按关键词筛选所有课程
        matched_all_courses = models.list_courses(keyword=kw.strip())
        # 2. 求交集：只保留属于当前老师 + 匹配关键词的课程
        teacher_course_id_set = {int(c["id"]) for c in courses}
        filtered = [
            c for c in matched_all_courses
            if int(c.get("teacher_id", 0)) == teacher_id
        ]
    else:
        # 无搜索词，展示教师全部课程
        filtered = courses

    PAGE_SIZE = 15
    page_key = "course_view_page"
    current_page = max(1, st.session_state[page_key])
    page_data, total_pages = paginate_data(filtered, current_page, PAGE_SIZE)

    if current_page > total_pages and total_pages > 0:
        st.session_state.course_view_page = total_pages
        current_page = total_pages

    st.write(f"共 {len(filtered)} 条数据，每页 {PAGE_SIZE} 条，总页数：{total_pages}")
    render_records(_course_table_rows(page_data), "No courses")
    render_pagination_style()
    render_pagination(current_page, total_pages, page_key)

    st.divider()
    st.subheader("Create Course")
    with st.form("create_course"):
        # 分两行三列，语义分离，杜绝列覆盖错乱
        row1_col1, row1_col2, row1_col3 = st.columns(3)
        with row1_col1:
            code = st.text_input("Course Code")
            cred = st.number_input("Credits", 0.5, 10.0, 3.0, 0.5)
        with row1_col2:
            name = st.text_input("Course Name")
            cap = st.number_input("Capacity", 1, 1000, 50, 1)
        with row1_col3:
            sem = st.text_input("Semester", "2026-Spring")
            target = st.number_input("Grade Year", 1, 8, 2, 1)

        row2_col1, row2_col2, row2_col3 = st.columns(3)
        with row2_col1:
            aw = st.number_input("Attendance %", 0.0, 100.0, 10.0, 5.0)
        with row2_col2:
            ew = st.number_input("Experiment %", 0.0, 100.0, 30.0, 5.0)
        with row2_col3:
            xw = st.number_input("Exam %", 0.0, 100.0, 60.0, 5.0)

        outline = st.text_area("Course Outline", max_chars=500)

        if st.form_submit_button("Create"):
            def act():
                services.validate_grade_weights(aw, ew, xw)
                # 严格对齐 create_course 参数顺序，不再错位
                course = models.create_course(
                    course_code=require_text(code, "Code"),
                    course_name=require_text(name, "Name"),
                    credits=cred,
                    semester=sem,
                    course_outline=outline.strip(),
                    teacher_id=teacher_id,
                    capacity=cap,
                    target_grade_year=target,
                    attendance_weight=aw,
                    experiment_weight=ew,
                    exam_weight=xw,
                )
                # 新增课程 - 写入操作日志
                write_operation_log(
                    current_user,
                    operate_type="新增课程",
                    operate_content=f"课程编号：{code}，课程名称：{name}",
                    target_type="course",
                    target_id=course["id"]
                )
                return course
            safe_run(act, "Created", rerun=True)

    st.divider()
    st.subheader("Update / Delete")
    selected, _ = selectbox_from_records(
        "Select course", courses, "id", _course_label, "c_sel"
    )
    if not selected:
        return
    cid = int(selected["id"])
    if services.course_has_grades(cid):
        st.warning("Has grades, cannot update/delete")
    c1, c2 = st.columns(2)
    with c1:
        with st.form("update_course"):
            name = st.text_input("Name", selected["course_name"])
            sem = st.text_input("Semester", selected["semester"])
            outline = st.text_area("Outline", selected.get("course_outline", ""))
            cred = st.number_input("Credits", 0.5, 10.0, float(selected["credits"]), 0.5)
            cap = st.number_input("Capacity", 1, 1000, int(selected["capacity"]), 1)
            target = st.number_input("Grade Year", 1, 8, int(selected.get("target_grade_year", 2)), 1)
            aw = st.number_input("Attendance %", 0.0, 100.0, float(selected.get("attendance_weight", 10)), 5.0)
            ew = st.number_input("Experiment %", 0.0, 100.0, float(selected.get("experiment_weight", 30)), 5.0)
            xw = st.number_input("Exam %", 0.0, 100.0, float(selected.get("exam_weight", 60)), 5.0)
            if st.form_submit_button("Update"):
                def act():
                    services.ensure_course_has_no_grades(cid)
                    services.validate_grade_weights(aw, ew, xw)
                    course = models.update_course(
                        course_id=cid,
                        course_name=require_text(name, "Name"),
                        course_outline=outline.strip(),
                        credits=cred,
                        teacher_id=teacher_id,
                        capacity=cap,
                        semester=sem,
                        target_grade_year=target,
                        attendance_weight=aw,
                        experiment_weight=ew,
                        exam_weight=xw,
                    )
                    write_operation_log(
                        current_user,
                        operate_type="更新课程",
                        operate_content=f"课程ID{cid}，修改课程信息",
                        target_type="course",
                        target_id=cid
                    )
                    return course
                safe_run(act, "Updated", rerun=True)
    
    with c2:
        with st.form("del_course"):
            confirm = st.checkbox("Confirm delete")
            if st.form_submit_button("Delete"):
                def act():
                    services.ensure_course_has_no_grades(cid)
                    row = models.delete_course(cid)
                    # 删除课程 - 写入操作日志
                    write_operation_log(
                        current_user,
                        operate_type="删除课程",
                        operate_content=f"课程ID{cid}，删除课程",
                        target_type="course",
                        target_id=cid
                    )
                    return row
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
        enrs = [e for e in enrs if e["status"] == "enrolled"]

    PAGE_SIZE = 15
    page_key = "enrollment_view_page"
    current_page = max(1, st.session_state[page_key])
    page_data, total_pages = paginate_data(enrs, current_page, PAGE_SIZE)

    if current_page > total_pages and total_pages > 0:
        st.session_state.enrollment_view_page = total_pages
        current_page = total_pages

    st.write(f"共 {len(enrs)} 条数据，每页 {PAGE_SIZE} 条，总页数：{total_pages}")
    render_records(_enrollment_table_rows(page_data), "No records")
    render_pagination_style()
    render_pagination(current_page, total_pages, page_key)