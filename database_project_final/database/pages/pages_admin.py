from __future__ import annotations
import streamlit as st
import pandas as pd
from io import BytesIO
from core import auth
from core import models
from core import services
from core.db import execute_non_query
from core.utils import (
    logout_user,
    render_records,
    require_text,
    safe_run,
    selectbox_from_records,
    validate_password,
    write_operation_log
)

# ===================== 通用分页工具函数 =====================
def paginate_data(data_list: list, page_num: int, page_size: int = 15) -> tuple[list, int]:
    """通用分页"""
    total = len(data_list)
    total_pages = (total + page_size - 1) // page_size
    start = (page_num - 1) * page_size
    end = start + page_size
    return data_list[start:end], total_pages

# ===================== 会话状态初始化（隔离各模块，防止串扰） =====================
if "file_id_acc_create" not in st.session_state:
    st.session_state.file_id_acc_create = None
if "file_id_acc_update" not in st.session_state:
    st.session_state.file_id_acc_update = None
if "file_id_stu_create" not in st.session_state:
    st.session_state.file_id_stu_create = None
if "file_id_stu_update" not in st.session_state:
    st.session_state.file_id_stu_update = None
# 日志分页
if "log_page" not in st.session_state or st.session_state.log_page < 1:
    st.session_state.log_page = 1
# 失败行数据存储
if "error_df" not in st.session_state:
    st.session_state.error_df = None
if "error_rows" not in st.session_state:
    st.session_state.error_rows = set()
# 主列表分页状态
if "user_list_page" not in st.session_state or st.session_state.user_list_page < 1:
    st.session_state.user_list_page = 1
if "student_list_page" not in st.session_state or st.session_state.student_list_page < 1:
    st.session_state.student_list_page = 1
# 独立模块报错分页 & 报错存储
if "err_acc_create_list" not in st.session_state:
    st.session_state.err_acc_create_list = []
if "err_acc_create_page" not in st.session_state:
    st.session_state.err_acc_create_page = 1
if "err_acc_update_list" not in st.session_state:
    st.session_state.err_acc_update_list = []
if "err_acc_update_page" not in st.session_state:
    st.session_state.err_acc_update_page = 1
if "err_stu_create_list" not in st.session_state:
    st.session_state.err_stu_create_list = []
if "err_stu_create_page" not in st.session_state:
    st.session_state.err_stu_create_page = 1
if "err_stu_update_list" not in st.session_state:
    st.session_state.err_stu_update_list = []
if "err_stu_update_page" not in st.session_state:
    st.session_state.err_stu_update_page = 1

# 统一空值清洗
def clean_val(v):
    if pd.isna(v):
        return ""
    s = str(v).strip()
    if s.lower in ["nan", "null", "none"]:
        return ""
    return s

# 【通用工具函数】导出失败行文件
def export_error_rows(original_df: pd.DataFrame, error_line_nums: set, file_suffix: str = ".xlsx") -> BytesIO | None:
    if not error_line_nums or original_df.empty:
        return None
    error_indexes = [line - 2 for line in error_line_nums if (line - 2) in original_df.index]
    error_df = original_df.loc[error_indexes].copy()
    output = BytesIO()
    if file_suffix == ".csv":
        error_df.to_csv(output, index=False, encoding="utf-8-sig")
    else:
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            error_df.to_excel(writer, index=False)
    output.seek(0)
    return output

# ===================== 报错列表分页渲染组件 =====================
def render_error_paginate(error_list: list, page_key: str, page_size: int = 10):
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
        jump = st.number_input("跳转页码", min_value=1, max_value=total_pages,
                               value=current_page, label_visibility="collapsed", key=f"{page_key}_jump")
        if jump != current_page:
            st.session_state[page_key] = jump
            st.rerun()
    with col_next:
        if st.button("下一页", disabled=current_page >= total_pages, key=f"{page_key}_next"):
            st.session_state[page_key] += 1
            st.rerun()

# ===================== 批量创建账号 =====================
def batch_create_accounts(uploaded_file, current_operator):
    errors = []
    success = 0
    skipped = 0
    error_line_set = set()
    raw_df = pd.DataFrame()
    # 修复：函数内提前定义 imported
    imported = set()
    try:
        bio = BytesIO(uploaded_file.getvalue())
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(bio, dtype=str).fillna("")
        elif uploaded_file.name.endswith((".xlsx", ".xls")):
            df = pd.read_excel(bio, dtype=str).fillna("")
        else:
            errors.append("仅支持 CSV / XLSX / XLS")
            st.session_state.error_df = None
            st.session_state.error_rows = set()
            return success, skipped, len(errors), errors
        raw_df = df.copy()
    except Exception as e:
        errors.append(f"文件读取失败：{str(e)}")
        st.session_state.error_df = None
        st.session_state.error_rows = set()
        return success, skipped, len(errors), errors
    required_cols = ["Role", "Username", "Password", "Status"]
    if list(df.columns) != required_cols:
        errors.append(f"必须列：{required_cols}，当前列：{list(df.columns)}")
        st.session_state.error_df = None
        st.session_state.error_rows = set()
        return success, skipped, len(errors), errors
    user_map = {}
    conflict_users = set()
    for idx, row in df.iterrows():
        role = clean_val(row["Role"])
        username = clean_val(row["Username"])
        pwd = clean_val(row["Password"])
        sta = clean_val(row["Status"])
        if not username:
            continue
        val = (role, pwd, sta)
        if username in user_map:
            if user_map[username] != val:
                conflict_users.add(username)
        else:
            user_map[username] = val
    total = len(df)
    bar = st.progress(0)
    txt = st.empty()
    for idx, row in df.iterrows():
        bar.progress((idx + 1) / total)
        txt.markdown(f"**导入进度：{idx+1}/{total}**")
        line = idx + 2
        try:
            role = clean_val(row["Role"]).lower()
            username = clean_val(row["Username"])
            pwd = clean_val(row["Password"])
            sta = clean_val(row["Status"]).lower()
            if not username:
                errors.append(f"第{line}行：Username 不能为空")
                skipped += 1
                error_line_set.add(line)
                continue
            if not pwd:
                errors.append(f"第{line}行：Password 不能为空")
                skipped += 1
                error_line_set.add(line)
                continue
            if role not in ["admin", "teacher", "student"]:
                errors.append(f"第{line}行：Role 只能是 admin/teacher/student")
                skipped += 1
                error_line_set.add(line)
                continue
            if sta not in ["active", "disabled"]:
                errors.append(f"第{line}行：Status 只能是 Active / Disabled")
                skipped += 1
                error_line_set.add(line)
                continue
            if username in conflict_users:
                errors.append(f"第{line}行：{username} 信息不一致，无法导入")
                skipped += 1
                error_line_set.add(line)
                continue
            if username in imported:
                errors.append(f"第{line}行：{username} 信息重复，已跳过")
                skipped += 1
                error_line_set.add(line)
                continue
            validate_password(pwd)
            exist_user = models.get_user_by_username(username)
            if exist_user:
                errors.append(f"第{line}行：用户 {username} 已存在")
                skipped += 1
                error_line_set.add(line)
                continue
            is_active = sta == "active"
            if role == "student":
                exist_stu = models.get_student_by_student_no(username)
                if exist_stu:
                    errors.append(f"第{line}行：学号 {username} 已存在")
                    skipped += 1
                    error_line_set.add(line)
                    continue
                stu = models.create_student(
                    student_no=username,
                    full_name=username,
                    gender="Other",
                    grade_year=1,
                    major="Undeclared",
                    phone=None,
                    email=None
                )
                user = models.create_user(
                    username=username,
                    password_hash=auth.hash_password(pwd),
                    role_name="student",
                    is_active=is_active
                )
                models.bind_student_user(stu["id"], user["id"])
                write_operation_log(
                    current_operator,
                    operate_type="批量创建账号(学生)",
                    operate_content=f"批量导入创建学生账号：{username}",
                    target_type="student账号",
                    target_id=user["id"]
                )
            else:
                user = models.create_user(
                    username=username,
                    password_hash=auth.hash_password(pwd),
                    role_name=role,
                    is_active=is_active
                )
                write_operation_log(
                    current_operator,
                    operate_type="批量创建账号",
                    operate_content=f"批量导入创建{role}账号：{username}",
                    target_type=f"{role}账号",
                    target_id=user["id"]
                )
            imported.add(username)
            success += 1
        except Exception as e:
            errors.append(f"第{line}行：{str(e)}")
            skipped += 1
            error_line_set.add(line)
    bar.progress(1.0)
    txt.markdown("✅ 导入完成")
    st.session_state.error_df = raw_df
    st.session_state.error_rows = error_line_set
    return success, skipped, len(errors), errors

# ===================== 批量更新/删除账号 =====================
def batch_update_accounts(uploaded_file, current_operator):
    errors = []
    success = 0
    skipped = 0
    error_line_set = set()
    raw_df = pd.DataFrame()
    try:
        bio = BytesIO(uploaded_file.getvalue())
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(bio, dtype=str).fillna("")
        elif uploaded_file.name.endswith((".xlsx", ".xls")):
            df = pd.read_excel(bio, dtype=str).fillna("")
        else:
            errors.append("仅支持 CSV / XLSX / XLS")
            st.session_state.error_df = None
            st.session_state.error_rows = set()
            return success, skipped, len(errors), errors
        raw_df = df.copy()
    except Exception as e:
        errors.append(f"文件读取失败：{str(e)}")
        st.session_state.error_df = None
        st.session_state.error_rows = set()
        return success, skipped, len(errors), errors
    required_cols = ["Username", "NewPassword", "Status", "Action"]
    if list(df.columns) != required_cols:
        errors.append(f"必须列：{required_cols}")
        st.session_state.error_df = None
        st.session_state.error_rows = set()
        return success, skipped, len(errors), errors
    total = len(df)
    bar = st.progress(0)
    txt = st.empty()
    for idx, row in df.iterrows():
        bar.progress((idx + 1) / total)
        txt.markdown(f"**处理进度：{idx+1}/{total}**")
        line = idx + 2
        try:
            username = clean_val(row["Username"])
            new_pwd = clean_val(row["NewPassword"])
            sta = clean_val(row["Status"]).lower()
            action = clean_val(row["Action"]).lower()
            if not username:
                raise ValueError("Username 不能为空")
            if not action:
                raise ValueError("Action 不能为空")
            if action not in ["update", "delete"]:
                raise ValueError("Action 只能是 update/delete")
            if sta and sta not in ["active", "disabled"]:
                raise ValueError("Status 只能是 Active / Disabled")
            user = models.get_user_by_username(username)
            if not user:
                raise ValueError("用户不存在")
            user_id = int(user["id"])
            role_name = user.get("role_name", "")
            if action == "delete":
                models.delete_user_account(user_id)
                stu = models.get_student_by_student_no(username)
                if stu:
                    models.delete_student(int(stu["id"]))
                write_operation_log(
                    current_operator,
                    operate_type="批量删除账号",
                    operate_content=f"批量删除账号：{username}",
                    target_type=f"{role_name}账号",
                    target_id=user_id
                )
                success += 1
            else:
                content_list = [f"更新账号：{username}"]
                target_type = f"{role_name}账号"
                if new_pwd:
                    validate_password(new_pwd)
                    auth.change_password(user_id,new_pwd)
                    content_list.append("重置密码")
                if sta:
                    models.update_user_active_status(user_id, sta == "active")
                    content_list.append(f"状态改为{sta}")
                write_operation_log(
                    current_operator,
                    operate_type="批量更新账号",
                    operate_content="；".join(content_list),
                    target_type=target_type,
                    target_id=user_id
                )
                success += 1
        except Exception as e:
            errors.append(f"第{line}行：{str(e)}")
            skipped += 1
            error_line_set.add(line)
    bar.progress(1.0)
    txt.markdown("✅ 处理完成")
    st.session_state.error_df = raw_df
    st.session_state.error_rows = error_line_set
    return success, skipped, len(errors), errors

# ===================== 批量导入学生 =====================
def batch_import_students(uploaded_file, current_operator):
    errors = []
    success = 0
    skipped = 0
    error_line_set = set()
    raw_df = pd.DataFrame()
    # 修复：函数内提前定义 imported
    imported = set()
    try:
        bio = BytesIO(uploaded_file.getvalue())
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(bio, dtype=str).fillna("")
        elif uploaded_file.name.endswith((".xlsx", ".xls")):
            df = pd.read_excel(bio, dtype=str).fillna("")
        else:
            errors.append("仅支持 CSV / XLSX / XLS")
            st.session_state.error_df = None
            st.session_state.error_rows = set()
            return success, skipped, len(errors), errors
        raw_df = df.copy()
    except Exception as e:
        errors.append(f"文件读取失败：{str(e)}")
        st.session_state.error_df = None
        st.session_state.error_rows = set()
        return success, skipped, len(errors), errors
    required_cols = ["StudentNo", "FullName", "Gender", "GradeYear", "Major", "Phone", "Email"]
    if list(df.columns) != required_cols:
        errors.append(f"必须列：{required_cols}")
        st.session_state.error_df = None
        st.session_state.error_rows = set()
        return success, skipped, len(errors), errors
    student_map = {}
    conflict_students = set()
    for idx, row in df.iterrows():
        sno = clean_val(row["StudentNo"])
        name = clean_val(row["FullName"])
        gender = clean_val(row["Gender"])
        gy = clean_val(row["GradeYear"])
        major = clean_val(row["Major"])
        phone = clean_val(row["Phone"])
        email = clean_val(row["Email"])
        if not sno:
            continue
        val = (name, gender, gy, major, phone, email)
        if sno in student_map:
            if student_map[sno] != val:
                conflict_students.add(sno)
        else:
            student_map[sno] = val
    total = len(df)
    bar = st.progress(0)
    txt = st.empty()
    for idx, row in df.iterrows():
        bar.progress((idx + 1) / total)
        txt.markdown(f"**导入进度：{idx+1}/{total}**")
        line = idx + 2
        try:
            sno = clean_val(row["StudentNo"])
            name = clean_val(row["FullName"])
            gender = clean_val(row["Gender"])
            gy_str = clean_val(row["GradeYear"])
            major = clean_val(row["Major"])
            phone = clean_val(row["Phone"])
            email = clean_val(row["Email"])
            if not sno:
                errors.append(f"第{line}行：StudentNo 不能为空")
                skipped += 1
                error_line_set.add(line)
                continue
            if not name:
                errors.append(f"第{line}行：FullName 不能为空")
                skipped += 1
                error_line_set.add(line)
                continue
            if not gender:
                errors.append(f"第{line}行：Gender 不能为空")
                skipped += 1
                error_line_set.add(line)
                continue
            if not gy_str:
                errors.append(f"第{line}行：GradeYear 不能为空")
                skipped += 1
                error_line_set.add(line)
                continue
            if not major:
                errors.append(f"第{line}行：Major 不能为空")
                skipped += 1
                error_line_set.add(line)
                continue
            if sno in conflict_students:
                errors.append(f"第{line}行：学号 {sno} 信息不一致，无法导入")
                skipped += 1
                error_line_set.add(line)
                continue
            if sno in imported:
                errors.append(f"第{line}行：学号 {sno} 信息重复，已跳过")
                skipped += 1
                error_line_set.add(line)
                continue
            try:
                gy = int(gy_str)
            except:
                errors.append(f"第{line}行：GradeYear 必须是数字")
                skipped += 1
                error_line_set.add(line)
                continue
            services.validate_gender(gender)
            services.validate_grade_year(gy)
            exist_stu = models.get_student_by_student_no(sno)
            if exist_stu:
                errors.append(f"第{line}行：学号 {sno} 已存在")
                skipped += 1
                error_line_set.add(line)
                continue
            stu = models.create_student(
                student_no=sno,
                full_name=name,
                gender=gender,
                grade_year=gy,
                major=major,
                phone=phone if phone else None,
                email=email if email else f"{sno}@edu"
            )
            exist_user = models.get_user_by_username(sno)
            if not exist_user:
                user = models.create_user(
                    username=sno,
                    password_hash=auth.hash_password("Student@123"),
                    role_name="student",
                    is_active=True
                )
                models.bind_student_user(stu["id"], user["id"])
                write_operation_log(
                    current_operator,
                    operate_type="批量导入学生+账号",
                    operate_content=f"批量导入学号：{sno}，姓名：{name}",
                    target_type="student账号",
                    target_id=stu["id"]
                )
            else:
                write_operation_log(
                    current_operator,
                    operate_type="批量导入学生",
                    operate_content=f"批量导入学号：{sno}，姓名：{name}",
                    target_type="student账号",
                    target_id=stu["id"]
                )
            imported.add(sno)
            success += 1
        except Exception as e:
            errors.append(f"第{line}行：{str(e)}")
            skipped += 1
            error_line_set.add(line)
    bar.progress(1.0)
    txt.markdown("✅ 导入完成")
    st.session_state.error_df = raw_df
    st.session_state.error_rows = error_line_set
    return success, skipped, len(errors), errors

# ===================== 批量更新/删除学生 =====================
def batch_update_students(uploaded_file, current_operator):
    errors = []
    success = 0
    skipped = 0
    error_line_set = set()
    raw_df = pd.DataFrame()
    try:
        bio = BytesIO(uploaded_file.getvalue())
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(bio, dtype=str).fillna("")
        elif uploaded_file.name.endswith((".xlsx", ".xls")):
            df = pd.read_excel(bio, dtype=str).fillna("")
        else:
            errors.append("仅支持 CSV / XLSX / XLS")
            st.session_state.error_df = None
            st.session_state.error_rows = set()
            return success, skipped, len(errors), errors
        raw_df = df.copy()
    except Exception as e:
        errors.append(f"文件读取失败：{str(e)}")
        st.session_state.error_df = None
        st.session_state.error_rows = set()
        return success, skipped, len(errors), errors
    required_cols = ["StudentNo", "FullName", "Gender", "GradeYear", "Major", "Phone", "Email", "Action"]
    if list(df.columns) != required_cols:
        errors.append(f"必须列：{required_cols}")
        st.session_state.error_df = None
        st.session_state.error_rows = set()
        return success, skipped, len(errors), errors
    total = len(df)
    bar = st.progress(0)
    txt = st.empty()
    for idx, row in df.iterrows():
        bar.progress((idx + 1) / total)
        txt.markdown(f"**处理进度：{idx+1}/{total}**")
        line = idx + 2
        try:
            sno = clean_val(row["StudentNo"])
            name = clean_val(row["FullName"])
            gender = clean_val(row["Gender"])
            gy_str = clean_val(row["GradeYear"])
            major = clean_val(row["Major"])
            phone = clean_val(row["Phone"])
            email = clean_val(row["Email"])
            action = clean_val(row["Action"]).lower()
            if not sno:
                errors.append(f"第{line}行：StudentNo 不能为空")
                skipped += 1
                error_line_set.add(line)
                continue
            if action not in ["update", "delete"]:
                errors.append(f"第{line}行：Action 只能是 update/delete")
                skipped += 1
                error_line_set.add(line)
                continue
            stu = models.get_student_by_student_no(sno)
            if not stu:
                errors.append(f"第{line}行：学生不存在")
                skipped += 1
                error_line_set.add(line)
                continue
            stu_id = int(stu["id"])
            if action == "delete":
                models.delete_student(stu_id)
                user = models.get_user_by_username(sno)
                if user:
                    models.delete_user_account(int(user["id"]))
                write_operation_log(
                    current_operator,
                    operate_type="批量删除学生",
                    operate_content=f"批量删除学号：{sno}",
                    target_type="student账号",
                    target_id=stu_id
                )
                success += 1
            else:
                if not name:
                    errors.append(f"第{line}行：FullName 不能为空")
                    skipped += 1
                    error_line_set.add(line)
                    continue
                if not gender:
                    errors.append(f"第{line}行：Gender 不能为空")
                    skipped += 1
                    error_line_set.add(line)
                    continue
                if not gy_str:
                    errors.append(f"第{line}行：GradeYear 不能为空")
                    skipped += 1
                    error_line_set.add(line)
                try:
                    gy = int(gy_str)
                except:
                    errors.append(f"第{line}行：GradeYear 必须是数字")
                    skipped += 1
                    error_line_set.add(line)
                    continue
                services.validate_gender(gender)
                services.validate_grade_year(gy)
                models.update_student(
                    student_id=stu_id,
                    full_name=name,
                    gender=gender,
                    grade_year=gy,
                    major=major,
                    phone=phone if phone else None,
                    email=email if email else None
                )
                write_operation_log(
                    current_operator,
                    operate_type="批量更新学生",
                    operate_content=f"批量更新学号：{sno} 信息",
                    target_type="student账号",
                    target_id=stu_id
                )
                success += 1
        except Exception as e:
            errors.append(f"第{line}行：{str(e)}")
            skipped += 1
            error_line_set.add(line)
    bar.progress(1.0)
    txt.markdown("✅ 处理完成")
    st.session_state.error_df = raw_df
    st.session_state.error_rows = error_line_set
    return success, skipped, len(errors), errors

# ===================== 原有页面辅助函数 =====================
def _user_label(user: dict) -> str:
    role = str(user["role_name"]).capitalize()
    status = "Active" if user["is_active"] else "Disabled"
    return f"{user['username']} · {role} · {status}"

def _user_table_rows(users: list[dict]) -> list[dict]:
    return [
        {
            "Username": user["username"],
            "Role": str(user["role_name"]).capitalize(),
            "Status": "Active" if user["is_active"] else "Disabled",
            "Created At": user["created_at"],
            "Updated At": user["updated_at"],
        }
        for user in users
    ]

def _student_label(student: dict) -> str:
    return f"{student['student_no']} | {student['full_name']}"

def _default_student_email(student_no: str) -> str:
    cleaned = student_no.strip()
    return f"{cleaned}@edu" if cleaned else ""

def _sync_create_student_email() -> None:
    student_no = str(st.session_state.get("admin_create_student_no", ""))
    next_auto_email = _default_student_email(student_no)
    previous_auto = str(st.session_state.get("admin_create_student_auto_email", ""))
    current_email = str(st.session_state.get("admin_create_student_email", ""))
    if not current_email.strip() or current_email.strip() == previous_auto:
        st.session_state["admin_create_student_email"] = next_auto_email
    st.session_state["admin_create_student_auto_email"] = next_auto_email

def _clear_create_student_inputs_if_needed() -> None:
    if not st.session_state.pop("admin_clear_create_student_inputs", False):
        return
    for key in (
        "admin_create_student_no",
        "admin_create_student_full_name",
        "admin_create_student_major",
        "admin_create_student_phone",
        "admin_create_student_email",
        "admin_create_student_auto_email",
    ):
        st.session_state.pop(key, None)

# 统一分页样式
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

# 通用数据分页组件
def render_pagination(current_page: int, total_pages: int, page_key: str) -> None:
    input_key = f"{page_key}_input"
    if input_key not in st.session_state:
        st.session_state[input_key] = current_page
    col_wrapper = st.columns([2, 6, 2])[1]
    with col_wrapper:
        col_prev, col_page_input, col_jump, col_next = st.columns([1, 1, 1, 1])
        with col_prev:
            if st.button("上一页", disabled=current_page <= 1, key=f"{page_key}_prev"):
                st.session_state[page_key] = current_page - 1
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
                st.session_state[page_key] = max(1, min(int(jump_page), total_pages))
                if input_key in st.session_state:
                    del st.session_state[input_key]
                st.rerun()
        with col_next:
            if st.button("下一页", disabled=current_page >= total_pages, key=f"{page_key}_next"):
                st.session_state[page_key] = current_page + 1
                if input_key in st.session_state:
                    del st.session_state[input_key]
                st.rerun()

# ===================== 新增：操作日志页面渲染函数（弹窗确认+修复SQL调用） =====================
def _render_operation_log(current_user):
    st.title("📜 Operation Logs | 操作审计日志")
    st.info("所有账号、学生、批量操作行为均已记录，支持多条件筛选、单条/整体删除日志")

    # 加载全部有效账号作为下拉选项
    all_users = models.list_users()
    username_list = ["全部"]
    for u in all_users:
        uname = u.get("username", "")
        if uname and uname not in username_list:
            username_list.append(uname)

    # 筛选栏布局
    col1, col2, col3, col4 = st.columns(4)

    # 关键词下拉（用户名）
    keyword = col1.selectbox(
        "关键词(用户名)",
        options=username_list,
        index=0,
        key="log_keyword_sel"
    )

    # 操作类型下拉
    opt_type_list = [
        "全部", "批量创建账号", "批量更新账号", "批量删除账号",
        "批量导入学生", "批量更新学生", "批量删除学生",
        "单条创建账号", "重置密码", "状态变更", "删除账号",
        "创建学生", "更新学生", "删除学生"
    ]
    opt_type = col2.selectbox("操作类型", options=opt_type_list, index=0)

    # 操作对象：已移除学生档案
    target_type_list = [
        "全部",
        "admin账号",
        "teacher账号",
        "student账号"
    ]
    target_type = col3.selectbox("操作对象", options=target_type_list, index=0)

    # 操作人用户名
    operator = col4.selectbox(
        "操作人用户名",
        options=username_list,
        index=0
    )

    # 筛选参数转换
    filter_keyword = None if keyword == "全部" else keyword
    filter_opt = None if opt_type == "全部" else opt_type
    filter_target = None if target_type == "全部" else target_type
    filter_operator = None if operator == "全部" else operator

    page_size = 20
    current_page = st.session_state.log_page

    # 查询日志
    log_list, total_count = models.list_operation_log(
        keyword=filter_keyword,
        operate_type=filter_opt,
        target_type=filter_target,
        operator=filter_operator,
        page=current_page,
        page_size=page_size
    )

    st.write(f"总记录数：{total_count} | 每页 {page_size} 条 | 当前第 {current_page} 页")

    # -------------------- 一键清空日志（弹窗确认） --------------------
    st.divider()

    @st.dialog("⚠️ 确认清空全部日志")
    def clear_all_log_dialog():
        st.warning("此操作将删除所有操作日志，数据不可恢复，请谨慎操作！")
        col_d1, col_d2 = st.columns(2)
        with col_d1:
            if st.button("取消", use_container_width=True):
                st.rerun()
        with col_d2:
            if st.button("确认清空", type="primary", use_container_width=True):
                execute_non_query("TRUNCATE TABLE operation_log;")
                write_operation_log(
                    current_user,
                    operate_type="清空全部操作日志",
                    operate_content="管理员通过弹窗确认，清空系统所有审计日志",
                    target_type="admin账号"
                )
                st.success("✅ 全部日志已清空！")
                st.rerun()

    if st.button("🗑️ 一键清空全部日志", type="secondary"):
        clear_all_log_dialog()

    st.divider()
    # -------------------------------------------------------------------

    # 渲染日志列表 + 单条删除
    if not log_list:
        st.info("暂无操作日志记录")
    else:
        for idx, item in enumerate(log_list):
            log_id = item.get("id", 0)
            op_user = item.get("operator_username", "")
            op_role = item.get("operator_role", "")
            op_type = item.get("operate_type", "")
            op_content = item.get("operate_content", "")
            t_type = item.get("target_type", "")
            t_id = item.get("target_id", "")
            op_time = item.get("operate_time", "")
            client_ip = item.get("client_ip", "")

            c_left, c_right = st.columns([9, 1])
            with c_left:
                st.markdown(
                    f"""
                    **[{op_time}] 【{op_role}】{op_user}**
                    操作类型：{op_type} | 操作对象：{t_type}（ID：{t_id}）
                    详情：{op_content} | IP：{client_ip}
                    """
                )
            with c_right:
                if st.button("删除", key=f"del_log_{log_id}_{idx}"):
                    try:
                        execute_non_query("DELETE FROM operation_log WHERE id = %s", (log_id,))
                        write_operation_log(
                            current_user,
                            operate_type="删除单条日志",
                            operate_content=f"删除日志ID：{log_id}",
                            target_type="admin账号",
                            target_id=log_id
                        )
                        st.success("✅ 本条日志已删除")
                        st.rerun()
                    except Exception as e:
                        st.error(f"删除失败：{str(e)}")
            st.divider()

    # 日志分页
    total_pages = (total_count + page_size - 1) // page_size
    render_pagination_style()
    render_pagination(current_page, total_pages, "log_page")

# ===================== 主Admin页面入口 =====================
def render_admin_page(current_user: dict) -> None:
    page = st.container()
    with page:
        st.title("Admin Dashboard")
        tab_overview, tab_accounts, tab_students, tab_log = st.tabs(
            ["Global Overview", "Account Management", "Student Management", "Operation Logs"]
        )
        with tab_overview:
            _render_global_overview()
        with tab_accounts:
            _render_account_management(current_user)
        with tab_students:
            _render_student_management()
        with tab_log:
            _render_operation_log(current_user)

def _render_global_overview() -> None:
    users = models.list_users()
    admin_count = sum(1 for user in users if user["role_name"] == "admin")
    teacher_count = sum(1 for user in users if user["role_name"] == "teacher")
    student_count = sum(1 for user in users if user["role_name"] == "student")
    active_count = sum(1 for user in users if user["is_active"])
    disabled_count = len(users) - active_count
    st.subheader("Account Overview")
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Total Accounts", len(users))
    c2.metric("Admin Accounts", admin_count)
    c3.metric("Teacher Accounts", teacher_count)
    c4.metric("Student Accounts", student_count)
    c5.metric("Active Accounts", active_count)
    c6.metric("Disabled Accounts", disabled_count)
    st.subheader("Recent Accounts")
    recent_users = users[-10:] if len(users) > 10 else users
    render_records(_user_table_rows(recent_users), "No accounts found.")

def _render_account_management(current_user: dict) -> None:
    st.subheader("Search Accounts")
    col1, col2, col3 = st.columns(3)
    keyword = col1.text_input("Username keyword")
    role_filter = col2.selectbox("Role", options=["all", "admin", "teacher", "student"])
    active_filter = col3.selectbox("Status", options=["all", "active", "disabled"])
    role_name = None if role_filter == "all" else role_filter
    is_active = None if active_filter == "all" else (active_filter == "active")
    users = models.list_users(keyword=keyword or None, role_name=role_name, is_active=is_active)
    PAGE_SIZE = 15
    page_key = "user_list_page"
    current_page = max(1, st.session_state[page_key])
    page_data, total_pages = paginate_data(users, current_page, PAGE_SIZE)
    if current_page > total_pages and total_pages > 0:
        st.session_state[page_key] = total_pages
        current_page = total_pages
    st.write(f"共 {len(users)} 条数据，每页 {PAGE_SIZE} 条，总页数：{total_pages}")
    render_records(_user_table_rows(page_data), "No account matched.")
    render_pagination_style()
    render_pagination(current_page, total_pages, page_key)

    # ========== 批量创建账号 ==========
    st.divider()
    st.subheader("📥 批量创建账号")
    file1 = st.file_uploader("上传 XLSX/CSV", type=["csv", "xlsx", "xls"], key="batch_acc_create")
    if file1 and st.session_state.file_id_acc_create != file1.file_id:
        st.session_state.err_acc_create_list = []
        st.session_state.err_acc_create_page = 1
        st.session_state.error_df = None
        st.session_state.error_rows = set()
        st.session_state.file_id_acc_create = file1.file_id
    if file1 and st.button("▶ 开始导入", type="primary", key="btn_acc_create"):
        s, sk, f, errs = batch_create_accounts(file1, current_user)
        st.session_state.err_acc_create_list = errs
        st.divider()
        st.subheader("📊 导入结果")
        col1, col2, col3 = st.columns(3)
        col1.metric("✅ 成功", s)
        col2.metric("⏭️ 跳过", sk)
        col3.metric("❌ 失败", f)
    if st.session_state.err_acc_create_list:
        st.divider()
        st.warning("导入错误列表：")
        render_error_paginate(st.session_state.err_acc_create_list, "err_acc_create_page", page_size=10)
        if st.session_state.error_df is not None and st.session_state.error_rows:
            buf = export_error_rows(st.session_state.error_df, st.session_state.error_rows, ".xlsx")
            if buf:
                st.download_button(
                    label="📥 下载失败行文件(Excel)",
                    data=buf,
                    file_name="批量账号创建_失败行.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key="dl_err1"
                )
        if st.button("✅ Close Errors & Continue", type="primary", use_container_width=True, key="close1"):
            st.session_state.err_acc_create_list = []
            st.session_state.err_acc_create_page = 1
            st.session_state.error_df = None
            st.session_state.error_rows = set()
            st.rerun()

    # ========== 单个创建账号 ==========
    st.divider()
    st.subheader("Create Account")
    new_role = st.selectbox(
        "Role",
        options=["admin", "teacher", "student"],
        key="admin_create_account_role",
    )
    with st.form("admin_create_account"):
        new_username = st.text_input("Username")
        new_password = st.text_input("Password", type="password")
        student_no = ""
        if new_role == "student":
            student_no = st.text_input("Student No")
        new_active = st.checkbox("Active", value=True)
        submitted = st.form_submit_button("Create Account")
        if submitted:
            def action():
                username = require_text(new_username, "Username")
                password = validate_password(new_password)
                if new_role == "student":
                    res = models.create_student_account(
                        username=username,
                        password_hash=auth.hash_password(password),
                        student_no=require_text(student_no),
                        is_active=new_active,
                    )
                    write_operation_log(
                        current_user,
                        operate_type="单条创建账号(学生)",
                        operate_content=f"创建学生账号：{username}",
                        target_type="student账号",
                        target_id=res["id"]
                    )
                    return res
                res = models.create_user(
                    username=username,
                    password_hash=auth.hash_password(password),
                    role_name=new_role,
                    is_active=new_active,
                )
                write_operation_log(
                    current_user,
                    operate_type="单条创建账号",
                    operate_content=f"创建{new_role}账号：{username}",
                    target_type=f"{new_role}账号",
                    target_id=res["id"]
                )
                return res
            safe_run(action, "Account created successfully.", rerun=True)

    # ========== 批量更新/删除账号 ==========
    st.divider()
    st.subheader("📥 批量更新/删除账号")
    file2 = st.file_uploader("上传 XLSX/CSV", type=["csv", "xlsx", "xls"], key="batch_acc_update")
    if file2 and st.session_state.file_id_acc_update != file2.file_id:
        st.session_state.err_acc_update_list = []
        st.session_state.err_acc_update_page = 1
        st.session_state.error_df = None
        st.session_state.error_rows = set()
        st.session_state.file_id_acc_update = file2.file_id
    if file2 and st.button("▶ 开始处理", type="primary", key="btn_acc_update"):
        s, sk, f, errs = batch_update_accounts(file2, current_user)
        st.session_state.err_acc_update_list = errs
        st.divider()
        st.subheader("📊 处理结果")
        col1, col2, col3 = st.columns(3)
        col1.metric("✅ 成功", s)
        col2.metric("⏭️ 跳过", sk)
        col3.metric("❌ 失败", f)
    if st.session_state.err_acc_update_list:
        st.divider()
        st.warning("处理错误列表：")
        render_error_paginate(st.session_state.err_acc_update_list, "err_acc_update_page", page_size=10)
        if st.session_state.error_df is not None and st.session_state.error_rows:
            buf = export_error_rows(st.session_state.error_df, st.session_state.error_rows, ".xlsx")
            if buf:
                st.download_button(
                    label="📥 下载失败行文件(Excel)",
                    data=buf,
                    file_name="批量账号更新_失败行.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key="dl_err2"
                )
        if st.button("✅ Close Errors & Continue", type="primary", use_container_width=True, key="close2"):
            st.session_state.err_acc_update_list = []
            st.session_state.err_acc_update_page = 1
            st.session_state.error_df = None
            st.session_state.error_rows = set()
            st.rerun()

    # ========== 账号修改/删除/重置密码 ==========
    st.divider()
    st.subheader("Update / Delete Account")
    selected_user, _ = selectbox_from_records(
        "Select account",
        users,
        id_key="id",
        label_builder=_user_label,
        key="admin_account_select",
    )
    if not selected_user:
        return
    c1, c2 = st.columns(2)
    role_name = selected_user.get("role_name", "")
    with c1:
        # 重置密码
        with st.form("admin_reset_password"):
            reset_password = st.text_input("New password", type="password")
            pwd_submit = st.form_submit_button("Reset Password")
            if pwd_submit:
                def action():
                    pwd = validate_password(reset_password)
                    res = auth.change_password(int(selected_user["id"]),pwd)
                    write_operation_log(
                        current_user,
                        operate_type="重置密码",
                        operate_content=f"对账号 {selected_user['username']} 执行密码重置",
                        target_type=f"{role_name}账号",
                        target_id=int(selected_user["id"])
                    )
                    return res
                safe_run(action, "Password reset completed.", rerun=True)
        # 删除账号
        with st.form("admin_delete_account"):
            confirm_delete = st.checkbox("Confirm delete this account")
            delete_submit = st.form_submit_button("Delete Account")
            if delete_submit:
                def action():
                    if not confirm_delete:
                        raise ValueError("Please confirm before deleting.")
                    deleted = models.delete_user_account(int(selected_user["id"]))
                    write_operation_log(
                        current_user,
                        operate_type="删除账号",
                        operate_content=f"删除账号：{selected_user['username']}",
                        target_type=f"{role_name}账号",
                        target_id=int(selected_user["id"])
                    )
                    if int(selected_user["id"]) == int(current_user["id"]):
                        logout_user()
                    return deleted
                safe_run(action, "Account deleted.", rerun=True)
    with c2:
        # 状态切换
        with st.form("admin_toggle_active"):
            next_active = st.radio(
                "Account status",
                options=[True, False],
                format_func=lambda x: "Active" if x else "Disabled",
                index=0 if selected_user["is_active"] else 1,
            )
            active_submit = st.form_submit_button("Apply Status")
            if active_submit:
                def action():
                    status_text = "启用" if next_active else "禁用"
                    res = models.update_user_active_status(int(selected_user["id"]), bool(next_active))
                    write_operation_log(
                        current_user,
                        operate_type="状态变更",
                        operate_content=f"将账号 {selected_user['username']} 设置为{status_text}",
                        target_type=f"{role_name}账号",
                        target_id=int(selected_user["id"])
                    )
                    return res
                safe_run(action, "Account status updated.", rerun=True)

def _render_student_management() -> None:
    _clear_create_student_inputs_if_needed()
    current_user = st.session_state.get("user", {})
    st.subheader("Search Students")
    keyword = st.text_input("Student keyword (name / number / major)")
    students = models.list_students(keyword=keyword or None)
    PAGE_SIZE = 15
    page_key = "student_list_page"
    current_page = max(1, st.session_state[page_key])
    page_data, total_pages = paginate_data(students, current_page, PAGE_SIZE)
    if current_page > total_pages and total_pages > 0:
        st.session_state[page_key] = total_pages
        current_page = total_pages
    st.write(f"共 {len(students)} 条数据，每页 {PAGE_SIZE} 条，总页数：{total_pages}")
    render_records(page_data, "No student matched.")
    render_pagination_style()
    render_pagination(current_page, total_pages, page_key)

    # ========== 批量导入学生 ==========
    st.divider()
    st.subheader("📥 批量导入学生")
    file3 = st.file_uploader("Upload XLSX/CSV", type=["csv", "xlsx", "xls"], key="batch_stu_create")
    if file3 and st.session_state.file_id_stu_create != file3.file_id:
        st.session_state.err_stu_create_list = []
        st.session_state.err_stu_create_page = 1
        st.session_state.error_df = None
        st.session_state.error_rows = set()
        st.session_state.file_id_stu_create = file3.file_id
    if file3 and st.button("▶ 导入学生", type="primary", key="btn_stu_create"):
        s, sk, f, errs = batch_import_students(file3, current_user)
        st.session_state.err_stu_create_list = errs
        st.divider()
        st.subheader("📊 导入结果")
        col1, col2, col3 = st.columns(3)
        col1.metric("✅ 成功", s)
        col2.metric("⏭️ 跳过", sk)
        col3.metric("❌ 失败", f)
    if st.session_state.err_stu_create_list:
        st.divider()
        st.warning("导入错误列表：")
        render_error_paginate(st.session_state.err_stu_create_list, "err_stu_create_page", page_size=10)
        if st.session_state.error_df is not None and st.session_state.error_rows:
            buf = export_error_rows(st.session_state.error_df, st.session_state.error_rows, ".xlsx")
            if buf:
                st.download_button(
                    label="📥 下载失败行文件(Excel)",
                    data=buf,
                    file_name="批量学生导入_失败行.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key="dl_err3"
                )
        if st.button("✅ Close Errors & Continue", type="primary", use_container_width=True, key="close3"):
            st.session_state.err_stu_create_list = []
            st.session_state.err_stu_create_page = 1
            st.session_state.error_df = None
            st.session_state.error_rows = set()
            st.rerun()

    # ========== 单个创建学生 ==========
    st.divider()
    st.subheader("Create Student")
    c1, c2 = st.columns(2)
    student_no = c1.text_input(
        "Student No",
        key="admin_create_student_no",
        on_change=_sync_create_student_email,
    )
    full_name = c2.text_input("Full Name", key="admin_create_student_full_name")
    gender = c1.selectbox("Gender", options=["M", "F", "Other"])
    grade_year = c2.number_input("Grade Year", min_value=1, max_value=8, value=1, step=1)
    major = c1.text_input("Major", key="admin_create_student_major")
    phone = c2.text_input("Phone", key="admin_create_student_phone")
    email = c1.text_input(
        "Email",
        key="admin_create_student_email",
        help="The email is filled as StudentNo@edu after Student No is entered.",
    )
    submit = st.button("Create Student", key="admin_create_student_submit")
    if submit:
        def action():
            student_no_val = require_text(student_no, "Student No")
            full_name_val = require_text(full_name, "Full Name")
            major_val = require_text(major)
            services.validate_gender(gender)
            services.validate_grade_year(int(grade_year))
            created = models.create_student(
                student_no=student_no_val,
                full_name=full_name_val,
                gender=gender,
                grade_year=int(grade_year),
                major=major_val,
                phone=phone.strip() or None,
                email=email.strip() or _default_student_email(student_no_val),
            )
            write_operation_log(
                current_user,
                operate_type="创建学生",
                operate_content=f"创建学生：学号{student_no_val}，姓名{full_name_val}",
                target_type="student账号",
                target_id=int(created["id"])
            )
            st.session_state["admin_clear_create_student_inputs"] = True
            return created
        safe_run(action, "Student created.", rerun=True)

    # ========== 批量更新/删除学生 ==========
    st.divider()
    st.subheader("📥 批量更新/删除学生")
    file4 = st.file_uploader("上传 XLSX/CSV", type=["csv", "xlsx", "xls"], key="batch_stu_update")
    if file4 and st.session_state.file_id_stu_update != file4.file_id:
        st.session_state.err_stu_update_list = []
        st.session_state.err_stu_update_page = 1
        st.session_state.error_df = None
        st.session_state.error_rows = set()
        st.session_state.file_id_stu_update = file4.file_id
    if file4 and st.button("▶ 批量处理", type="primary", key="btn_stu_update"):
        s, sk, f, errs = batch_update_students(file4, current_user)
        st.session_state.err_stu_update_list = errs
        st.divider()
        st.subheader("📊 处理结果")
        col1, col2, col3 = st.columns(3)
        col1.metric("✅ 成功", s)
        col2.metric("⏭️ 跳过", sk)
        col3.metric("❌ 失败", f)
    if st.session_state.err_stu_update_list:
        st.divider()
        st.warning("导入错误列表：")
        render_error_paginate(st.session_state.err_stu_update_list, "err_stu_update_page",page_size=10)
        if st.session_state.error_df is not None and st.session_state.error_rows:
            buf = export_error_rows(st.session_state.error_df, st.session_state.error_rows,".xlsx")
            if buf:
                st.download_button(
                    label="📥 下载失败行文件(Excel)",
                    data=buf,
                    file_name="批量学生更新_失败行.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key="dl_err4"
                )
        if st.button("✅ Close Errors & Continue", type="primary", use_container_width=True, key="close4"):
            st.session_state.err_stu_update_list = []
            st.session_state.err_stu_update_page = 1
            st.session_state.error_df = None
            st.session_state.error_rows = set()
            st.rerun()

    # ========== 学生修改/删除 ==========
    st.divider()
    st.subheader("Update / Delete Student")
    selected_student, _ = selectbox_from_records(
        "Select student",
        students,
        id_key="id",
        label_builder=_student_label,
        key="admin_student_select",
    )
    if not selected_student:
        return
    stu_id = int(selected_student["id"])
    stu_no = selected_student["student_no"]
    c1, c2 = st.columns(2)
    with c1:
        with st.form("admin_update_student"):
            full_name = st.text_input("Full Name", value=str(selected_student["full_name"]))
            gender = st.selectbox(
                "Gender",
                options=["M", "F", "Other"],
                index=["M", "F", "Other"].index(str(selected_student["gender"])),
            )
            grade_year = st.number_input(
                "Grade Year",
                min_value=1,
                max_value=8,
                value=int(selected_student["grade_year"]),
                step=1,
            )
            major = st.text_input("Major", value=str(selected_student["major"]))
            phone = st.text_input("Phone", value=str(selected_student["phone"] or ""))
            email = st.text_input("Email", value=str(selected_student["email"] or ""))
            update_submit = st.form_submit_button("Update Student")
            if update_submit:
                def action():
                    services.validate_gender(gender)
                    services.validate_grade_year(int(grade_year))
                    res = models.update_student(
                        student_id=stu_id,
                        full_name=full_name,
                        gender=gender,
                        grade_year=grade_year,
                        major=major,
                        phone=phone.strip() or None,
                        email=email.strip() or None
                    )
                    write_operation_log(
                        current_user,
                        operate_type="更新学生",
                        operate_content=f"更新学号 {stu_no} 信息",
                        target_type="student账号",
                        target_id=stu_id
                    )
                    return res
                safe_run(action, "Student updated.", rerun=True)
    with c2:
        with st.form("admin_delete_student"):
            confirm = st.checkbox("Confirm delete student profile")
            delete_submit = st.form_submit_button("Delete Student")
            if delete_submit:
                def action():
                    if not confirm:
                        raise ValueError("Please confirm before deleting.")
                    deleted = models.delete_student(stu_id)
                    write_operation_log(
                        current_user,
                        operate_type="删除学生",
                        operate_content=f"删除学号 {stu_no}",
                        target_type="student账号",
                        target_id=stu_id
                    )
                    user_id = selected_student.get("user_id")
                    if user_id is not None:
                        models.update_user_active_status(int(user_id), False)
                    return deleted
                safe_run(action, "Student deleted.", rerun=True)