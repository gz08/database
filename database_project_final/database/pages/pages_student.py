from __future__ import annotations
from html import escape
import streamlit as st
import streamlit.components.v1 as components
import base64
from pathlib import Path
import os
from core import models
from core import services
from core import auth
from core.utils import render_records, safe_run, selectbox_from_records, write_operation_log
from pages.ai_tutor import render_ai_tutor_page
from core.face_auth import render_face_register, capture_face, match_face

# ===================== 通用分页工具函数（与admin页面保持一致） =====================
def paginate_data(data_list: list, page_num: int, page_size: int = 15) -> tuple[list, int]:
    """通用分页"""
    total = len(data_list)
    total_pages = (total + page_size - 1) // page_size
    start = (page_num - 1) * page_size
    end = start + page_size
    return data_list[start:end], total_pages

# ===================== 会话状态初始化（分页隔离） =====================
# 课程列表分页
if "course_list_page" not in st.session_state or st.session_state.course_list_page < 1:
    st.session_state.course_list_page = 1

# 统一分页样式（与admin页面保持一致）
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

# 通用数据分页组件（与admin页面保持一致）
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

# ===================== 原有业务工具函数（无修改） =====================
def _course_label(course: dict) -> str:
    return f"{course['course_code']} | {course['course_name']}"

def _score_text(value: object) -> str:
    if value is None:
        return "N/A"
    return f"{float(value):.1f}"

def _weight_text(course: dict) -> str:
    return (
        f"Attendance {float(course.get('attendance_weight', 0)):.1f}% / "
        f"Experiment {float(course.get('experiment_weight', 0)):.1f}% / "
        f"Exam {float(course.get('exam_weight', 0)):.1f}%"
    )

def _score_class(value: object) -> str:
    if value is None:
        return "empty"
    score = float(value)
    if score < 60:
        return "risk"
    if score < 75:
        return "warn"
    return "good"

def _score_width(value: object) -> float:
    if value is None:
        return 0.0
    return max(0.0, min(float(value), 100.0))

def _grade_stat(label: str, value: object) -> str:
    score_class = _score_class(value)
    width = _score_width(value)
    return f"""
    <div class="grade-stat">
        <div class="grade-stat-label">{escape(label)}</div>
        <div class="grade-stat-value {score_class}">{escape(_score_text(value))}</div>
        <div class="grade-track"><span class="{score_class}" style="width: {width:.1f}%"></span></div>
    </div>
    """

def _render_grade_details(course: dict, grade: dict | None) -> None:
    attendance_score = grade.get("attendance_score") if grade else None
    experiment_score = grade.get("experiment_score") if grade else None
    exam_score = grade.get("exam_score") if grade else None
    final_score = grade.get("score") if grade else None
    graded_status = "Recorded" if grade else "Pending"
    status_class = "recorded" if grade else "pending"
    stats_html = "".join(
        [
            _grade_stat("Attendance", attendance_score),
            _grade_stat("Experiment", experiment_score),
            _grade_stat("Exam", exam_score),
            _grade_stat("Final", final_score),
        ]
    )
    components.html(
        f"""
        <style>
        * {{
            box-sizing: border-box;
        }}
        body {{
            margin: 0;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
            background: transparent;
        }}
        .grade-detail-shell {{
            margin-top: 10px;
        }}
        .grade-detail-head {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            gap: 16px;
            padding: 2px 0 14px;
            border-bottom: 1px solid #d9e2ec;
        }}
        .grade-title {{
            margin: 0;
            font-size: 20px;
            font-weight: 700;
            line-height: 1.25;
        }}
        .grade-subtitle {{
            margin-top: 4px;
            color: #627d98;
            font-size: 13px;
            font-weight: 600;
        }}
        .grade-status {{
            border-radius: 999px;
            padding: 6px 12px;
            font-size: 12px;
            font-weight: 700;
            white-space: nowrap;
        }}
        .grade-status.recorded {{
            color: #0f5132;
            background: #d1fae5;
            border: 1px solid #86efac;
        }}
        .grade-status.pending {{
            color: #7c2d12;
            background: #ffedd5;
            border: 1px solid #fdba7;
        }}
        .grade-meta-grid {{
            display: grid;
            grid-template-columns: minmax(0, 1.4fr) minmax(240px, 0.6fr);
            gap: 14px;
            margin-top: 14px;
        }}
        .grade-meta-panel {{
            border: 1px solid #d9e2ec;
            background: #ffffff;
            border-radius: 8px;
            padding: 14px 16px;
            box-shadow: 0 1px 2px rgba(15, 23, 42, 0.05);
        }}
        .grade-meta-label {{
            color: #627d98;
            font-size: 12px;
            font-weight: 700;
            text-transform: uppercase;
        }}
        .grade-meta-text {{
            margin-top: 6px;
            color: #243b53;
            font-size: 14px;
            line-height: 1.55;
            overflow-wrap: anywhere;
        }}
        .grade-stat-grid {{
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 12px;
            margin-top: 14px;
        }}
        .grade-stat {{
            border: 1px solid #d9e2ec;
            background: #ffffff;
            border-radius: 8px;
            padding: 14px 14px 12px;
            box-shadow: 0 1px 2px rgba(15, 23, 42, 0.05);
        }}
        .grade-stat-label {{
            color: #627d98;
            font-size: 12px;
            font-weight: 700;
        }}
        .grade-stat-value {{
            margin-top: 7px;
            font-size: 24px;
            font-weight: 750;
            line-height: 1;
        }}
        .grade-stat-value.good {{ color: #0f766e; }}
        .grade-stat-value.warn {{ color: #b45309; }}
        .grade-stat-value.risk {{ color: #b91c1c; }}
        .grade-stat-value.empty {{ color: #94a3b8; }}
        .grade-track {{
            height: 6px;
            margin-top: 12px;
            border-radius: 999px;
            background: #e5e7eb;
            overflow: hidden;
        }}
        .grade-track span {{
            display: block;
            height: 100%;
            border-radius: 999px;
        }}
        .grade-track span.good {{ background: #14b8a6; }}
        .grade-track span.warn {{ background: #f59e0b; }}
        .grade-track span.risk {{ background: #ef4444; }}
        .grade-track span.empty {{ background: transparent; }}
        @media (max-width: 900px) {{
            .grade-detail-head {{
                flex-direction: column;
            }}
            .grade-meta-grid {{
                grid-template-columns: 1fr;
            }}
            .grade-stat-grid {{
                grid-template-columns: repeat(2, minmax(0, 1fr));
            }}
        }}
        @media (max-width: 520px) {{
            .grade-stat-grid {{
                grid-template-columns: 1fr;
            }}
        }}
        </style>
        <div class="grade-detail-shell">
            <div class="grade-detail-head">
                <div>
                    <h4 class="grade-title">{escape(str(course.get("course_name") or ""))}</h4>
                </div>
                <span class="grade-status {status_class}">{graded_status}</span>
            </div>
            <div class="grade-meta-grid">
                <div class="grade-meta-panel">
                    <div class="grade-meta-label">Course Outline</div>
                    <div class="grade-meta-text">{escape(str(course.get("course_outline") or "N/A"))}</div>
                </div>
                <div class="grade-meta-panel">
                    <div class="grade-meta-label">Weights</div>
                    <div class="grade-meta-text">{escape(_weight_text(course))}</div>
                </div>
            </div>
            <div class="grade-stat-grid">
                {stats_html}
            </div>
        </div>
        """,
        height=360,
        scrolling=False,
    )

def _profile_value(value: object) -> str:
    if value is None:
        return "Not provided"
    text = str(value).strip()
    return text if text else "Not provided"

def _profile_row(label: str, value: object) -> str:
    return (
        '<div class="profile-row">'
        f'<span class="profile-label">{escape(label)}</span>'
        f'<span class="profile-value">{escape(_profile_value(value))}</span>'
        '</div>'
    )

def _profile_card(title: str, rows: list[tuple[str, object]]) -> str:
    row_html = "".join(_profile_row(label, value) for label, value in rows)
    return (
        '<section class="profile-card">'
        f'<h4>{escape(title)}</h4>'
        f'{row_html}'
        '</section>'
    )

def _render_change_password(username: str, current_user: dict) -> None:
    """人脸识别验证 + 自助改密码功能"""
    if "pwd_face_verified" not in st.session_state:
        st.session_state.pwd_face_verified = False

    st.subheader("🔐 Self-Service Password Change")
    st.info("Please complete face verification first, then set your new password")

    if not st.session_state.pwd_face_verified:
        if st.button("📷 Start Face Verification", type="primary"):
            with st.spinner("Capturing face for verification..."):
                face_img = capture_face()
            if face_img is None:
                st.error("Face not detected, please try again!")
                return
            if match_face(username, face_img):
                st.success("✅ Face verification passed! Please set new password below")
                st.session_state.pwd_face_verified = True
                st.rerun()
            else:
                st.error("❌ Face mismatch, verification failed")
                return
    else:
        with st.form("change_pwd_form", clear_on_submit=True):
            new_pwd = st.text_input("New Password", type="password")
            confirm_pwd = st.text_input("Confirm New Password", type="password")
            submit_btn = st.form_submit_button("Submit Password Change")

            if submit_btn:
                if not new_pwd or not confirm_pwd:
                    st.error("Password cannot be empty")
                    return
                if new_pwd != confirm_pwd:
                    st.error("Two passwords are inconsistent")
                    return
                if len(new_pwd) < 6:
                    st.error("Password must be at least 6 characters")
                    return
                user_info = models.get_user_by_username(username)
                if not user_info:
                    st.error("User does not exist")
                    st.session_state.pwd_face_verified = False
                    st.rerun()
                    return
                try:
                    auth.change_password(int(user_info["id"]), new_pwd)
                    write_operation_log(
                        current_user,
                        operate_type="修改密码",
                        operate_content=f"学生用户 {username} 修改密码",
                        target_type="user",
                        target_id=int(user_info["id"]),
                    )
                    st.success("🎉 Password changed successfully!")
                    st.session_state.pwd_face_verified = False
                    st.rerun()
                except Exception as e:
                    st.error(f"Password change failed: {str(e)}")
                    st.session_state.pwd_face_verified = False

# ===================== 成绩单工具函数（修复路径+印章显示问题） =====================
def get_seal_base64(seal_path: str) -> str:
    """读取公章图片并转为 base64，修复路径与中文文件名问题"""
    try:
        img_path = Path(seal_path).resolve()
        if not img_path.exists():
            st.warning(f"公章文件未找到：{img_path}")
            return ""
        with open(img_path, "rb") as f:
            img_bytes = f.read()
        return base64.b64encode(img_bytes).decode("utf-8")
    except Exception as e:
        st.error(f"读取公章失败：{str(e)}")
        return ""


def generate_transcript_html(student: dict, grade_list: list[dict], seal_b64: str) -> str:
    """生成只读成绩单（带全屏斜向重复水印）"""

    student_no = _profile_value(student.get("student_no"))
    full_name = _profile_value(student.get("full_name"))
    major = _profile_value(student.get("major"))
    grade_year = _profile_value(student.get("grade_year"))

    table_rows = ""
    total_score = 0.0
    count_valid = 0

    for g in grade_list:
        course_code = escape(_profile_value(g.get("course_code")))
        course_name = escape(_profile_value(g.get("course_name")))
        score = g.get("score")

        att_score = _score_text(g.get("attendance_score"))
        exp_score = _score_text(g.get("experiment_score"))
        exam_score = _score_text(g.get("exam_score"))
        final_score = _score_text(score)

        if score is not None:
            total_score += float(score)
            count_valid += 1

        table_rows += f"""
        <tr>
            <td>{course_code}</td>
            <td>{course_name}</td>
            <td>{att_score}</td>
            <td>{exp_score}</td>
            <td>{exam_score}</td>
            <td><strong>{final_score}</strong></td>
        </tr>
        """

    avg_score = total_score / count_valid if count_valid > 0 else 0.0

    seal_html = ""
    if seal_b64:
        seal_html = (
            f'<img src="data:image/png;base64,{seal_b64}" '
            f'class="seal-img" alt="Official Seal">'
        )

    # 生成大量水印
    watermark_text = f"学号:{student_no}    姓名:{full_name}"
    watermark_html = "".join(
        f'<div class="watermark-item">{watermark_text}</div>'
        for _ in range(250)
    )

    transcript = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>Student Academic Transcript</title>

<style>

body {{
    font-family: "Microsoft Yahei", SimSun, sans-serif;
    padding: 30px;
    background: #ffffff;
    position: relative;
    overflow-x: hidden;

    user-select: none;
    -webkit-user-select: none;
    -moz-user-select: none;
    -ms-user-select: none;
}}

/* ===========================
   全屏重复斜向水印
   =========================== */

.watermark-layer {{
    position: fixed;

    top: -300px;
    left: -300px;

    width: 220%;
    height: 220%;

    display: flex;
    flex-wrap: wrap;
    align-content: flex-start;

    transform: rotate(-28deg);

    pointer-events: none;

    z-index: 50000;

    overflow: hidden;
}}

.watermark-item {{
    width: 320px;
    height: 90px;

    display: flex;
    align-items: center;
    justify-content: center;

    white-space: nowrap;

    font-size: 20px;
    font-weight: bold;

    color: rgba(150,150,150,0.18);
}}

/* ===========================
   成绩单主体
   =========================== */

.transcript-wrap {{
    max-width: 900px;

    margin: 0 auto;

    border: 1px solid #cccccc;

    padding: 30px;

    position: relative;

    z-index: 1000;

    background: transparent;

    min-height: 85vh;
}}

h2 {{
    text-align: center;
    margin-bottom: 25px;
    font-size: 22px;
}}

.student-info {{
    display: flex;
    flex-wrap: wrap;
    gap: 20px;
    margin-bottom: 20px;
}}

table {{
    width: 100%;
    border-collapse: collapse;
}}

th,
td {{
    border: 1px solid #999999;
    padding: 8px 10px;
    text-align: center;

    /* 半透明背景让水印透出来 */
    background: rgba(255,255,255,0.75);
}}

th {{
    background: rgba(245,247,250,0.75);
}}

.avg-line {{
    margin-top: 20px;
    font-size: 15px;
    font-weight: bold;
}}

.tip {{
    margin-top: 30px;
    text-align: right;
    color: #666666;
    font-size: 12px;
}}

/* ===========================
   印章最高层
   =========================== */

.seal-container {{
    position: absolute;

    right: 50px;
    bottom: 60px;

    width: 140px;

    z-index: 99999;

    pointer-events: none;
}}

.seal-img {{
    width: 140px;
    height: auto;

    opacity: 1;

    transform: rotate(-12deg);
}}

@media print {{

    .watermark-layer {{
        position: fixed;
    }}

    .seal-container {{
        position: fixed;
    }}
}}

</style>
</head>

<body>

<div class="watermark-layer">
    {watermark_html}
</div>

<div class="transcript-wrap">

    <h2>Student Academic Transcript</h2>

    <div class="student-info">
        <div>Student ID: {student_no}</div>
        <div>Name: {full_name}</div>
        <div>Major: {escape(major)}</div>
        <div>Grade: {escape(grade_year)}</div>
    </div>

    <table>
        <thead>
            <tr>
                <th>Course Code</th>
                <th>Course Name</th>
                <th>Attendance</th>
                <th>Experiment</th>
                <th>Exam</th>
                <th>Final Score</th>
            </tr>
        </thead>
        <tbody>
            {table_rows}
        </tbody>
    </table>

    <div class="avg-line">
        Average Score: {avg_score:.1f}
    </div>

    <div class="seal-container">
        {seal_html}
    </div>

</div>

</body>
</html>
"""
    return transcript



def _render_transcript(student_id: int, student: dict) -> None:
    """渲染成绩单预览、仅保留下载功能，移除打印按钮"""
    st.subheader("📄 Official Academic Transcript (Read-Only)")
    st.info("This transcript is an official document with official seal, content cannot be modified.")

    # 获取当前脚本所在目录 pages
    current_file_dir = Path(__file__).parent.resolve()
    # 相对路径逻辑：pages_student.py 在 pages 文件夹，向上一层到 database，再进入 static
    # 路径结构：database/pages/pages_student.py -> database/static/公章.png
    SEAL_PATH = str(current_file_dir.parent / "static" / "公章.png")
    seal_b64 = get_seal_base64(SEAL_PATH)

    # 查询成绩数据
    grades = models.list_grades(student_id=student_id)
    if not grades:
        st.warning("No grade records available for transcript.")
        return

    # 拼接课程信息
    all_courses = models.list_courses()
    course_dict = {int(c["id"]): c for c in all_courses}
    full_grade_data = []
    for g in grades:
        cid = int(g["course_id"])
        course = course_dict.get(cid, {})
        merge_item = {**g, **course}
        full_grade_data.append(merge_item)

    # 生成成绩单HTML
    transcript_html = generate_transcript_html(student, full_grade_data, seal_b64)

    # 预览成绩单
    components.html(transcript_html, height=600, scrolling=True)

    # 仅保留下载按钮，删除打印按钮
    b64_html = base64.b64encode(transcript_html.encode("utf-8")).decode()
    download_href = f"""
    <a href="data:text/html;base64,{b64_html}" download="Student_Transcript.html">
        <button style="padding: 6px 16px; cursor: pointer;">⬇️ Download Transcript</button>
    </a>
    """
    st.markdown(download_href, unsafe_allow_html=True)

# ===================== 主页面渲染函数（新增成绩单Tab） =====================
def render_student_page(current_user: dict) -> None:
    page = st.container()
    with page:
        st.title("Student Dashboard")
        student = models.get_student_by_user_id(int(current_user["id"]))
        if not student:
            st.error("Student profile is missing. Please contact admin.")
            return
        student_id = int(student["id"])
        username = current_user["username"]
        # 新增 Transcript 标签页
        tab_profile, tab_courses, tab_ai_plan, tab_transcript, tab_pwd = st.tabs(
            ["My Profile", "Course Selection", "AI Plan", "Transcript", "Change Password"]
        )
        with tab_profile:
            _render_profile(student, username, current_user)
        with tab_courses:
            _render_course_selection(student_id, int(student["grade_year"]), current_user)
        with tab_ai_plan:
            render_ai_tutor_page(current_user)
        with tab_transcript:
            _render_transcript(student_id, student)
        with tab_pwd:
            _render_change_password(username, current_user)

def _render_profile(student: dict, username: str, current_user: dict) -> None:
    st.subheader("Personal Information")
    is_active = bool(student.get("user_is_active"))
    status_text = "Active" if is_active else "Disabled"
    status_class = "active" if is_active else "disabled"
    basic_rows = [
        ("Student No", student.get("student_no")),
        ("Full Name", student.get("full_name")),
        ("Grade Year", student.get("grade_year")),
        ("Major", student.get("major")),
    ]
    contact_rows = [
        ("Phone", student.get("phone")),
        ("Email", student.get("email")),
    ]
    account_rows = [
        ("Login Username", username),
        ("Account Status", status_text),
    ]
    st.markdown(
        """
        <style>
        .profile-hero {
            border: 1px solid #d9e2ec;
            background: #ffffff;
            border-radius: 8px;
            padding: 22px 24px;
            margin: 8px 0 18px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 16px;
            box-shadow: 0 1px 2px rgba(15, 23, 42, 0.06);
        }
        .profile-name {
            margin: 0;
            color: #102a43;
            font-size: 28px;
            font-weight: 700;
            line-height: 1.2;
        }
        .profile-summary {
            margin-top: 6px;
            color: #52606d;
            font-size: 16px;
            font-weight: 600;
        }
        .profile-status {
            border-radius: 999px;
            padding: 7px 13px;
            font-size: 13px;
            font-weight: 700;
            white-space: nowrap;
        }
        .profile-status.active {
            color: #0f5132;
            background: #d1fae5;
            border: 1px solid #86efac;
        }
        .profile-status.disabled {
            color: #842029;
            background: #fee2e2;
            border: 1px solid #fecaca;
        }
        .profile-grid {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 16px;
        }
        .profile-card {
            border: 1px solid #d9e2ec;
            background: #ffffff;
            border-radius: 8px;
            padding: 18px 18px 14px;
            box-shadow: 0 1px 2px rgba(15, 23, 42, 0.06);
        }
        .profile-card h4 {
            margin: 0 0 12px;
            color: #243b53;
            font-size: 16px;
            font-weight: 700;
        }
        .profile-row {
            display: flex;
            justify-content: space-between;
            gap: 14px;
            padding: 9px 0;
            border-top: 1px solid #eef2f6;
        }
        .profile-row:first-of-type {
            border-top: none;
        }
        .profile-label {
            color: #627d98;
            font-size: 13px;
        }
        .profile-value {
            color: #102a43;
            font-size: 14px;
            font-weight: 600;
            text-align: right;
            overflow-wrap: anywhere;
        }
        @media (max-width: 900px) {
            .profile-hero {
                align-items: flex-start;
                flex-direction: column;
            }
            .profile-grid {
                grid-template-columns: 1fr;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    hero_html = f"""
    <div class="profile-hero">
        <div>
            <h3 class="profile-name">{escape(_profile_value(student.get("full_name")))}</h3>
            <div class="profile-summary">
                {escape(_profile_value(student.get("student_no")))}
                &nbsp;&middot;&nbsp;
                {escape(_profile_value(student.get("major")))}
                &nbsp;&middot;&nbsp;
                Grade {escape(_profile_value(student.get("grade_year")))}
            </div>
        </div>
        <span class="profile-status {status_class}">{status_text}</span>
    </div>
    """
    cards_html = (
        '<div class="profile-grid">'
        f'{_profile_card("Basic Information", basic_rows)}'
        f'{_profile_card("Contact Information", contact_rows)}'
        f'{_profile_card("Account Information", account_rows)}'
        '</div>'
    )
    st.markdown(hero_html + cards_html, unsafe_allow_html=True)

    st.divider()
    st.subheader("Update Contact Information")
    with st.form("student_profile_update_form", clear_on_submit=False):
        phone = st.text_input("Phone", value=str(student.get("phone") or ""))
        email = st.text_input("Email", value=str(student.get("email") or ""))
        submitted = st.form_submit_button("Save Changes")

        if submitted:
            def update_profile_action():
                updated = models.update_student(
                    student_id=int(student["id"]),
                    phone=phone.strip() or None,
                    email=email.strip() or None,
                )
                write_operation_log(
                    current_user,
                    operate_type="修改个人信息",
                    operate_content=f"学生 {username} 更新联系方式：电话={phone.strip() or '未填写'}，邮箱={email.strip() or '未填写'}",
                    target_type="student",
                    target_id=int(student["id"]),
                )
                return updated

            result = safe_run(update_profile_action, "Profile updated successfully.", rerun=True)
            if result is not None:
                st.success("Profile updated successfully.")

    # 恢复人脸录入模块（第一段代码原有完整逻辑）
    st.divider()
    st.subheader("Face Registration")
    render_face_register(student["username"])

def _render_course_selection(student_id: int, grade_year: int, current_user: dict) -> None:
    st.subheader("Course List")
    keyword = st.text_input("Search courses by code / name")
    courses = (
        services.search_courses(keyword, target_grade_year=grade_year)
        if keyword.strip()
        else models.list_courses(target_grade_year=grade_year)
    )
    enrollments = models.list_enrollments(student_id=student_id)
    enrollment_map = {int(e["course_id"]): e for e in enrollments}
    grades = models.list_grades(student_id=student_id)
    grade_map = {int(g["course_id"]): g for g in grades}

    # 组装表格数据
    display_rows = []
    for course in courses:
        course_id = int(course["id"])
        status = "not_enrolled"
        if course_id in enrollment_map:
            status = str(enrollment_map[course_id])
        score = None
        if course_id in grade_map:
            score = grade_map[course_id].get("score")
        display_rows.append(
            {
                "course_code": course["course_code"],
                "course_name": course["course_name"],
                "credits": course["credits"],
                "semester": course["semester"],
                "teacher_name": course.get("teacher_name"),
                "status": status,
                "final_score": score,
            }
        )

    # ========== 课程列表分页（与Admin页面规则完全一致） ==========
    PAGE_SIZE = 15
    page_key = "course_list_page"
    current_page = max(1, st.session_state[page_key])
    page_data, total_pages = paginate_data(display_rows, current_page, PAGE_SIZE)

    if current_page > total_pages and total_pages > 0:
        st.session_state[page_key] = total_pages
        current_page = total_pages

    st.write(f"共 {len(display_rows)} 条数据，每页 {PAGE_SIZE} 条，总页数：{total_pages}")
    render_records(page_data, "No courses found.")
    render_pagination_style()
    render_pagination(current_page, total_pages, page_key)
    # ==========================================================

    st.divider()
    st.subheader("My Grade Details")
    enrolled_courses = [
        course
        for course
        in courses
        if enrollment_map.get(int(course["id"]), {}).get("status") == "enrolled"
    ]
    selected_detail_course, selected_detail_course_id = selectbox_from_records(
        "Select an enrolled course",
        enrolled_courses,
        id_key="id",
        label_builder=_course_label,
        key="student_grade_detail_select",
    )
    if selected_detail_course:
        selected_grade = grade_map.get(int(selected_detail_course_id))
        _render_grade_details(selected_detail_course, selected_grade)

    st.divider()
    st.subheader("Enroll Course")
    enrollable_courses = [c for c in courses if enrollment_map.get(int(c["id"]), {}).get("status") != "enrolled"]
    selected_course, selected_course_id = selectbox_from_records(
        "Select a course to enroll",
        enrollable_courses,
        id_key="id",
        label_builder=_course_label,
        key="student_enroll_select",
    )
    if selected_course:
        if st.button("Enroll", key="student_enroll_btn"):
            def enroll_action():
                result = services.enroll_course(student_id=student_id, course_id=int(selected_course_id))
                write_operation_log(
                    current_user,
                    operate_type="选课",
                    operate_content=f"学生ID {student_id} 选课 {selected_course['course_code']} - {selected_course['course_name']}",
                    target_type="course",
                    target_id=int(selected_course_id),
                )
                return result

            safe_run(enroll_action, "Enroll success.", rerun=True)

    st.divider()
    st.subheader("Drop Course")
    droppable = [c for c in courses if enrollment_map.get(int(c["id"]), {}).get("status") == "enrolled"]
    selected_drop_course, selected_drop_course_id = selectbox_from_records(
        "Select an enrolled course to drop",
        droppable,
        id_key="id",
        label_builder=_course_label,
        key="student_drop_select",
    )
    if selected_drop_course:
        if st.button("Drop Course", key="student_drop_btn"):
            def drop_action():
                result = services.drop_course(student_id=student_id, course_id=int(selected_drop_course_id))
                write_operation_log(
                    current_user,
                    operate_type="退课",
                    operate_content=f"学生ID {student_id} 退课 {selected_drop_course['course_code']} - {selected_drop_course['course_name']}",
                    target_type="course",
                    target_id=int(selected_drop_course_id),
                )
                return result

            safe_run(drop_action, "Drop success.", rerun=True)