from __future__ import annotations

import streamlit as st

from core import auth
from core.utils import (
    ensure_session_defaults,
    init_page,
    login_user,
    logout_user,
)

from pages.pages_admin import render_admin_page
from pages.pages_student import render_student_page
from pages.pages_teacher import render_teacher_page


# =========================================
# 页面初始化（必须最前）
# =========================================
st.set_page_config(
    page_title="Student Management System",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# =========================================
# 彻底隐藏 Sidebar
# =========================================
st.markdown(
    """
    <style>

    section[data-testid="stSidebar"]{
        display:none !important;
    }

    [data-testid="stSidebarNav"]{
        display:none !important;
    }

    [data-testid="collapsedControl"]{
        display:none !important;
    }

    button[kind="header"]{
        display:none !important;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# def _render_login_page() -> None:

#     # 使用 empty 容器
#     login_container = st.empty()

#     with login_container.container():

#         st.title("Student Management System")
#         st.caption("openGauss + Python + Streamlit")

#         with st.form("login_form", clear_on_submit=True):

#             username = st.text_input("Username")
#             password = st.text_input(
#                 "Password",
#                 type="password"
#             )

#             submitted = st.form_submit_button("Login")

#             if submitted:

#                 try:

#                     user = auth.login(
#                         username=username.strip(),
#                         password=password
#                     )

#                     if not user:
#                         st.error(
#                             "Login failed. "
#                             "Check username/password or account status."
#                         )
#                         return

#                     # =========================
#                     # 登录状态写入
#                     # =========================
#                     login_user(user)

#                     # =========================
#                     # 立即清空登录页面
#                     # 防止残影
#                     # =========================
#                     login_container.empty()

#                     # =========================
#                     # 强制刷新
#                     # =========================
#                     st.rerun()

#                 except Exception as exc:
#                     st.error(f"Login failed: {exc}")

from core.face_auth import capture_face, match_face
    
def _render_login_page() -> None:
    if st.session_state.get(
        "face_login_success",
        False
    ):

        user = st.session_state.get(
            "face_login_user"
        )

        if user:

            login_user(user)

        st.session_state.pop(
            "face_login_success",
            None
        )

        st.session_state.pop(
            "face_login_user",
            None
        )

        st.rerun()

    login_container = st.empty()

    with login_container.container():

        st.title("Student Management System")

        username = st.text_input(
            "Username",
            key="login_username"
        )

        password = st.text_input(
            "Password",
            type="password"
        )

        with st.form(
            "login_form",
            clear_on_submit=True
        ):
            submitted = st.form_submit_button(
                "Login"
            )

        # =========================
        # 人脸登录
        # =========================
        if st.button(
            "📷 Face Login",
            type="primary"
        ):

            username_val = (
                st.session_state
                .get("login_username", "")
                .strip()
            )

            if not username_val:

                st.error(
                    "Please enter username first!"
                )

                return

            with st.spinner(
                "Capturing face..."
            ):

                face = capture_face()

            if face is None:

                st.error(
                    "No face detected!"
                )

                return

            if match_face(
                username_val,
                face
            ):

                # =====================
                # 直接获取用户
                # 不再要求密码
                # =====================
                user = auth.get_user_by_username(
                    username_val
                )

                if not user:

                    st.error(
                        "User not found!"
                    )

                    return

                st.session_state[
                    "face_login_user"
                ] = user

                st.session_state[
                    "face_login_success"
                ] = True

                st.rerun()

            else:

                st.error(
                    "Face not match!"
                )

        # =========================
        # 普通账号密码登录
        # =========================
        if submitted:

            try:

                user = auth.login(
                    username=username.strip(),
                    password=password
                )

                if not user:

                    st.error(
                        "Login failed."
                    )

                    return

                login_user(user)

                login_container.empty()

                st.rerun()

            except Exception as exc:

                st.error(
                    f"Error: {exc}"
                )
                
def _render_topbar(user: dict) -> None:

    col1, col2, col3 = st.columns([6, 2, 1])

    with col1:
        st.markdown(
            f"# Student Management System"
        )

    with col2:
        st.write(
            f"👤 {user['username']} "
            f"({user['role_name']})"
        )

    with col3:

        if st.button(
            "Logout",
            key="logout_btn"
        ):

            logout_user()

            st.cache_data.clear()

            st.cache_resource.clear()

            st.rerun()


def _render_role_page(user: dict) -> None:

    role = str(user.get("role_name"))

    try:

        _render_topbar(user)

        st.divider()

        if role == "admin":

            render_admin_page(user)

        elif role == "teacher":

            render_teacher_page(user)

        elif role == "student":

            render_student_page(user)

        else:
            st.error(f"Unsupported role: {role}")

    except Exception as exc:

        st.error(f"Page render failed: {exc}")


def main() -> None:

    init_page()

    ensure_session_defaults()

    authenticated = bool(
        st.session_state.get(
            "authenticated",
            False
        )
    )

    user = st.session_state.get("user")

    # =========================
    # 已登录
    # =========================
    if authenticated and user:

        _render_role_page(user)

        return

    # =========================
    # 未登录
    # =========================
    _render_login_page()


if __name__ == "__main__":
    main()
