# from __future__ import annotations

# from datetime import date, datetime, time
# from decimal import Decimal
# from typing import Any, Callable, Optional

# import streamlit as st


# def init_page() -> None:
#     st.set_page_config(
#         page_title="Student Management System",
#         page_icon="SMS",
#         layout="wide",
#     )


# def ensure_session_defaults() -> None:
#     st.session_state.setdefault("authenticated", False)
#     st.session_state.setdefault("user", None)


# def login_user(user: dict[str, Any]) -> None:
#     st.session_state["authenticated"] = True
#     st.session_state["user"] = user


# def logout_user() -> None:
#     st.session_state["authenticated"] = False
#     st.session_state["user"] = None


# def require_text(value: str, field_name: str) -> str:
#     cleaned = value.strip()
#     if not cleaned:
#         raise ValueError(f"{field_name} is required.")
#     return cleaned


# def validate_password(password: str, min_length: int = 6) -> str:
#     if len(password) < min_length:
#         raise ValueError(f"Password length must be at least {min_length}.")
#     return password


# def safe_run(
#     action: Callable[[], Any],
#     success_message: Optional[str] = None,
#     rerun: bool = False,
# ):
#     try:
#         result = action()
#         if success_message:
#             st.success(success_message)
#         if rerun:
#             st.rerun()
#         return result
#     except Exception as exc:
#         st.error(str(exc))
#         return None


# def render_records(records: list[dict[str, Any]], empty_message: str = "No records.") -> None:
#     if not records:
#         st.info(empty_message)
#         return

#     def normalize_value(value: Any) -> Any:
#         if isinstance(value, Decimal):
#             return float(value)
#         if isinstance(value, (datetime, date, time)):
#             return value.isoformat()
#         return value

#     normalized = [{k: normalize_value(v) for k, v in row.items()} for row in records]
#     st.dataframe(normalized, use_container_width=True, hide_index=True)


# def selectbox_from_records(
#     label: str,
#     records: list[dict[str, Any]],
#     id_key: str,
#     label_builder: Callable[[dict[str, Any]], str],
#     key: Optional[str] = None,
# ) -> tuple[Optional[dict[str, Any]], Optional[Any]]:
#     if not records:
#         st.info("No selectable records.")
#         return None, None

#     ids = [item[id_key] for item in records]
#     labels = {item[id_key]: label_builder(item) for item in records}

#     selected_id = st.selectbox(
#         label,
#         options=ids,
#         format_func=lambda x: labels.get(x, str(x)),
#         key=key,
#     )
#     selected = next((item for item in records if item[id_key] == selected_id), None)
#     return selected, selected_id

# from __future__ import annotations
# from datetime import date, datetime, time
# from decimal import Decimal
# from typing import Any, Callable, Optional
# import streamlit as st

# def init_page() -> None:
#     st.set_page_config(
#         page_title="Student Management System",
#         page_icon="SMS",
#         layout="wide",
#     )

# def ensure_session_defaults() -> None:
#     st.session_state.setdefault("authenticated", False)
#     st.session_state.setdefault("user", None)

# def login_user(user: dict[str, Any]) -> None:
#     st.session_state["authenticated"] = True
#     st.session_state["user"] = user

# def logout_user() -> None:
#     st.session_state["authenticated"] = False
#     st.session_state["user"] = None

# def require_text(value: str, field_name: str) -> str:
#     cleaned = value.strip()
#     if not cleaned:
#         raise ValueError(f"{field_name} is required.")
#     return cleaned

# def validate_password(password: str, min_length: int = 6) -> str:
#     if len(password) < min_length:
#         raise ValueError(f"Password length must be at least {min_length}.")
#     return password

# def safe_run(
#     action: Callable[[], Any],
#     success_message: Optional[str] = None,
#     rerun: bool = False,
# ):
#     try:
#         result = action()
#         if success_message:
#             st.success(success_message)
#         if rerun:
#             st.rerun()
#         return result
#     except Exception as exc:
#         st.error(str(exc))
#         return None

# def render_records(records: list[dict[str, Any]], empty_message: str = "No records.") -> None:
#     if not records:
#         st.info(empty_message)
#         return

#     def normalize_value(value: Any) -> Any:
#         if isinstance(value, Decimal):
#             return float(value)
#         if isinstance(value, (datetime, date, time)):
#             return value.isoformat()
#         return value

#     normalized = [{k: normalize_value(v) for k, v in row.items()} for row in records]
#     # 已修复：use_container_width → width
#     st.dataframe(normalized, width="stretch", hide_index=True)

# def selectbox_from_records(
#     label: str,
#     records: list[dict[str, Any]],
#     id_key: str,
#     label_builder: Callable[[dict[str, Any]], str],
#     key: Optional[str] = None,
# ) -> tuple[Optional[dict[str, Any]], Optional[Any]]:
#     if not records:
#         st.info("No selectable records.")
#         return None, None
#     ids = [item[id_key] for item in records]
#     labels = {item[id_key]: label_builder(item) for item in records}
#     selected_id = st.selectbox(
#         label,
#         options=ids,
#         format_func=lambda x: labels.get(x, str(x)),
#         key=key,
#     )
#     selected = next((item for item in records if item[id_key] == selected_id), None)
#     return selected, selected_id

from __future__ import annotations
from datetime import date, datetime, time
from decimal import Decimal
from typing import Any, Callable, Optional
import streamlit as st
import base64

# 辅助函数：读取本地图片并编码为 base64（Streamlit 唯一稳定方法）
def get_base64_of_image(image_path):
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()

def init_page() -> None:
    # st.set_page_config(
    #     page_title="Student Management System",
    #     page_icon="SMS",
    #     layout="wide",
    # )

    # 🔥 100% 能显示的背景代码（虚化 + 清晰输入框）
    try:
        img_base64 = get_base64_of_image("static/数据库大作业背景图（去水印）.png")
        page_bg_img = f'''
        <style>
        :root {{
            --app-font: "Segoe UI", "Microsoft YaHei", "PingFang SC",
                "Hiragino Sans GB", "Noto Sans CJK SC", Arial, sans-serif;
        }}

        html, body, .stApp, [data-testid="stAppViewContainer"] {{
            font-family: var(--app-font) !important;
            font-size: 15px !important;
            line-height: 1.55 !important;
            letter-spacing: 0 !important;
        }}

        .stApp {{
            background:
                linear-gradient(
                    rgba(248, 250, 252, 0.94),
                    rgba(248, 250, 252, 0.94)
                ),
                url("data:image/png;base64,{img_base64}") center / cover fixed no-repeat !important;
            color: #111827 !important;
        }}

        [data-testid="collapsedControl"],
        button[kind="header"],
        [aria-label="Open sidebar"],
        [aria-label="Close sidebar"] {{
            display: none !important;
            visibility: hidden !important;
        }}

        h1, h2, h3, h4, h5, h6,
        p, li, label, input, textarea, button,
        [data-testid="stMarkdownContainer"],
        [data-testid="stMetric"],
        [data-testid="stMetricLabel"],
        [data-testid="stMetricValue"],
        [data-testid="stDataFrame"],
        [data-baseweb="select"],
        [data-baseweb="tab"] {{
            font-family: var(--app-font) !important;
            letter-spacing: 0 !important;
        }}

        h1 {{
            font-size: 28px !important;
            line-height: 1.25 !important;
            font-weight: 700 !important;
        }}

        h2, h3 {{
            font-size: 20px !important;
            line-height: 1.35 !important;
            font-weight: 650 !important;
        }}

        h4, h5, h6 {{
            font-size: 16px !important;
            line-height: 1.4 !important;
            font-weight: 650 !important;
        }}

        p, li, [data-testid="stMarkdownContainer"] {{
            font-size: 15px !important;
            line-height: 1.55 !important;
        }}

        .stTextInput > div > div {{
            background-color: white !important;
            border-radius: 6px;
        }}

        .stTextInput > label,
        .stSelectbox > label,
        .stNumberInput > label,
        .stTextArea > label,
        .stFileUploader > label,
        .stCheckbox > label,
        .stRadio > label {{
            color: #111827 !important;
            font-size: 14px !important;
            line-height: 1.4 !important;
            font-weight: 600 !important;
        }}

        input, textarea, [data-baseweb="select"] * {{
            font-size: 14px !important;
            line-height: 1.45 !important;
        }}

        button, .stButton button, .stFormSubmitButton button {{
            font-size: 14px !important;
            line-height: 1.35 !important;
            font-weight: 600 !important;
        }}

        [data-testid="stMetric"] label {{
            font-size: 13px !important;
            line-height: 1.35 !important;
            font-weight: 600 !important;
        }}

        [data-testid="stMetricValue"] {{
            font-size: 22px !important;
            line-height: 1.2 !important;
            font-weight: 700 !important;
        }}

        [data-testid="stDataFrame"] * {{
            font-size: 13px !important;
            line-height: 1.4 !important;
        }}

        [data-baseweb="tab"] {{
            font-size: 14px !important;
            line-height: 1.35 !important;
            font-weight: 600 !important;
        }}

        .stHeader {{
            background-color: transparent !important;
        }}
        </style>
        '''
        st.markdown(page_bg_img, unsafe_allow_html=True)
    except:
        pass  # 图片找不到也不会崩界面

def ensure_session_defaults() -> None:
    st.session_state.setdefault("authenticated", False)
    st.session_state.setdefault("user", None)

def login_user(user: dict[str, Any]) -> None:
    st.session_state["authenticated"] = True
    st.session_state["user"] = user

def logout_user() -> None:
    st.session_state["authenticated"] = False
    st.session_state["user"] = None

def require_text(value: str, field_name: str) -> str:
    cleaned = value.strip()
    if not cleaned:
        raise ValueError(f"{field_name} 不能为空")
    return cleaned

def validate_password(password: str, min_length: int = 6) -> str:
    if len(password) < min_length:
        raise ValueError(f"密码至少 {min_length} 位")
    return password

def safe_run(
    action: Callable[[], Any],
    success_message: Optional[str] = None,
    rerun: bool = False,
):
    try:
        result = action()
        if success_message:
            st.success(success_message)
        if rerun:
            st.rerun()
        return result
    except Exception as exc:
        st.error(str(exc))
        return None

def render_records(records: list[dict[str, Any]], empty_message: str = "暂无数据") -> None:
    if not records:
        st.info(empty_message)
        return
    def normalize_value(value: Any) -> Any:
        if isinstance(value, Decimal):
            return float(value)
        if isinstance(value, (datetime, date, time)):
            return value.isoformat()
        return value
    normalized = [{k: normalize_value(v) for k, v in row.items()} for row in records]
    st.dataframe(normalized, use_container_width=True, hide_index=True)

def selectbox_from_records(
    label: str,
    records: list[dict[str, Any]],
    id_key: str,
    label_builder: Callable[[dict[str, Any]], str],
    key: Optional[str] = None,
) -> tuple[Optional[dict[str, Any]], Optional[Any]]:
    if not records:
        st.info("暂无可选数据")
        return None, None
    ids = [item[id_key] for item in records]
    labels = {item[id_key]: label_builder(item) for item in records}
    selected_id = st.selectbox(
        label,
        options=ids,
        format_func=lambda x: labels.get(x, str(x)),
        key=key,
    )
    selected = next((item for item in records if item[id_key] == selected_id), None)
    return selected, selected_id
