from __future__ import annotations

import streamlit as st

from core import auth
from core import models
from core import services
from core.utils import (
    logout_user,
    render_records,
    require_text,
    safe_run,
    selectbox_from_records,
    validate_password,
)


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
    previous_auto_email = str(
        st.session_state.get("admin_create_student_auto_email", "")
    )
    current_email = str(st.session_state.get("admin_create_student_email", ""))

    if not current_email.strip() or current_email.strip() == previous_auto_email:
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


def render_admin_page(current_user: dict) -> None:
    page = st.container()

    with page:
        st.title("Admin Dashboard")

        tab_overview, tab_accounts, tab_students = st.tabs(
            ["Global Overview", "Account Management", "Student Management"]
        )

        with tab_overview:
            _render_global_overview()
        with tab_accounts:
            _render_account_management(current_user)
        with tab_students:
            _render_student_management()


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
    if active_filter == "all":
        is_active = None
    else:
        is_active = active_filter == "active"

    users = models.list_users(keyword=keyword or None, role_name=role_name, is_active=is_active)
    render_records(_user_table_rows(users), "No account matched.")

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
                    return models.create_student_account(
                        username=username,
                        password_hash=auth.hash_password(password),
                        student_no=require_text(student_no, "Student No"),
                        is_active=new_active,
                    )
                return models.create_user(
                    username=username,
                    password_hash=auth.hash_password(password),
                    role_name=new_role,
                    is_active=new_active,
                )

            safe_run(action, "Account created successfully.", rerun=True)

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
    with c1:
        with st.form("admin_reset_password"):
            reset_password = st.text_input("New password", type="password")
            pwd_submit = st.form_submit_button("Reset Password")
            if pwd_submit:
                def action():
                    pwd = validate_password(reset_password)
                    return auth.change_password(int(selected_user["id"]), pwd)

                safe_run(action, "Password reset completed.", rerun=True)

        with st.form("admin_delete_account"):
            confirm_delete = st.checkbox("Confirm delete this account")
            delete_submit = st.form_submit_button("Delete Account")
            if delete_submit:
                def action():
                    if not confirm_delete:
                        raise ValueError("Please confirm before deleting.")
                    deleted = models.delete_user_account(int(selected_user["id"]))
                    if deleted <= 0:
                        raise ValueError("Account delete failed.")
                    if int(selected_user["id"]) == int(current_user["id"]):
                        logout_user()
                    return deleted

                safe_run(action, "Account deleted.", rerun=True)

    with c2:
        with st.form("admin_toggle_active"):
            next_active = st.radio(
                "Account status",
                options=[True, False],
                format_func=lambda x: "Active" if x else "Disabled",
                index=0 if selected_user["is_active"] else 1,
            )
            active_submit = st.form_submit_button("Apply Status")
            if active_submit:
                safe_run(
                    lambda: models.update_user_active_status(int(selected_user["id"]), bool(next_active)),
                    "Account status updated.",
                    rerun=True,
                )


def _render_student_management() -> None:
    _clear_create_student_inputs_if_needed()

    st.subheader("Search Students")
    keyword = st.text_input("Student keyword (name / number / major)")
    students = models.list_students(keyword=keyword or None)
    render_records(students, "No student matched.")

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
        help="The email is filled as StudentNo@edu after Student No is entered. You can edit it manually.",
    )
    submit = st.button("Create Student", key="admin_create_student_submit")

    if submit:
        def action():
            student_no_val = require_text(student_no, "Student No")
            full_name_val = require_text(full_name, "Full Name")
            major_val = require_text(major, "Major")
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
            st.session_state["admin_clear_create_student_inputs"] = True
            return created

        safe_run(action, "Student created.", rerun=True)

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
                    return models.update_student(
                        student_id=int(selected_student["id"]),
                        full_name=require_text(full_name, "Full Name"),
                        gender=gender,
                        grade_year=int(grade_year),
                        major=require_text(major, "Major"),
                        phone=phone.strip() or None,
                        email=email.strip() or None,
                    )

                safe_run(action, "Student updated.", rerun=True)

    with c2:
        with st.form("admin_delete_student"):
            confirm = st.checkbox("Confirm delete student profile")
            delete_submit = st.form_submit_button("Delete Student")
            if delete_submit:
                def action():
                    if not confirm:
                        raise ValueError("Please confirm before deleting.")
                    user_id = selected_student.get("user_id")
                    deleted = models.delete_student(int(selected_student["id"]))
                    if deleted <= 0:
                        raise ValueError("Student delete failed.")
                    if user_id is not None:
                        models.update_user_active_status(int(user_id), False)
                    return deleted

                safe_run(action, "Student deleted.", rerun=True)
