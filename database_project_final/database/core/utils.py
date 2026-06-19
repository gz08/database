from __future__ import annotations
from datetime import date, datetime, time
from decimal import Decimal
from typing import Any, Callable, Optional
import streamlit as st
import base64
import core.models as models
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
            --app-accent: #0f766e;
            --app-accent-hover: #0d9488;
            --app-accent-soft: rgba(15, 118, 110, 0.10);
            --app-accent-focus: rgba(15, 118, 110, 0.18);
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
            border-radius: 8px !important;
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

        .stTextInput input,
        .stNumberInput input,
        .stTextArea textarea,
        [data-baseweb="select"] > div {{
            min-height: 38px !important;
            border: 1px solid #cbd5e1 !important;
            border-radius: 8px !important;
            background-color: #ffffff !important;
            box-shadow: none !important;
            transition: border-color 0.15s ease, box-shadow 0.15s ease !important;
        }}

        .stTextArea textarea {{
            min-height: 88px !important;
        }}

        .stTextInput input:focus,
        .stNumberInput input:focus,
        .stTextArea textarea:focus,
        [data-baseweb="select"] > div:focus-within {{
            border-color: var(--app-accent) !important;
            box-shadow: 0 0 0 3px var(--app-accent-focus) !important;
            outline: none !important;
        }}

        .stFileUploader section {{
            border: 1px dashed #94a3b8 !important;
            border-radius: 8px !important;
            background-color: rgba(255, 255, 255, 0.78) !important;
        }}

        button, .stButton button, .stFormSubmitButton button {{
            font-size: 14px !important;
            line-height: 1.35 !important;
            font-weight: 600 !important;
        }}

        .stButton button,
        .stFormSubmitButton button,
        button[kind="primary"],
        button[kind="secondary"] {{
            min-height: 38px !important;
            border-radius: 8px !important;
            border: 1px solid var(--app-accent) !important;
            background: var(--app-accent) !important;
            color: #ffffff !important;
            box-shadow: 0 1px 2px rgba(15, 23, 42, 0.08) !important;
            transition: background-color 0.15s ease, border-color 0.15s ease,
                box-shadow 0.15s ease !important;
        }}

        .stButton button:hover,
        .stFormSubmitButton button:hover,
        button[kind="primary"]:hover,
        button[kind="secondary"]:hover {{
            border-color: var(--app-accent-hover) !important;
            background: var(--app-accent-hover) !important;
            color: #ffffff !important;
            box-shadow: 0 4px 10px var(--app-accent-focus) !important;
        }}

        .stButton button:focus,
        .stFormSubmitButton button:focus,
        button[kind="primary"]:focus,
        button[kind="secondary"]:focus {{
            box-shadow: 0 0 0 3px var(--app-accent-focus) !important;
            outline: none !important;
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

        [data-testid="stDataFrame"] {{
            border: 1px solid #e2e8f0 !important;
            border-radius: 8px !important;
            overflow: hidden !important;
            background: #ffffff !important;
        }}

        [data-testid="stDataFrame"] div {{
            scrollbar-color: #94a3b8 #f8fafc !important;
        }}

        [data-baseweb="tab-list"] {{
            gap: 4px !important;
            border-bottom: 1px solid #dbe4ee !important;
        }}

        [data-baseweb="tab"] {{
            font-size: 14px !important;
            line-height: 1.35 !important;
            font-weight: 600 !important;
            min-height: 38px !important;
            padding: 8px 14px !important;
            color: #475569 !important;
            border-radius: 8px 8px 0 0 !important;
        }}

        [data-baseweb="tab"]:hover {{
            color: var(--app-accent) !important;
            background: var(--app-accent-soft) !important;
        }}

        [data-baseweb="tab"][aria-selected="true"] {{
            color: var(--app-accent) !important;
            background: var(--app-accent-soft) !important;
        }}

        [data-baseweb="tab-highlight"] {{
            background-color: var(--app-accent) !important;
            height: 3px !important;
            border-radius: 999px !important;
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

# def logout_user() -> None:
#     st.session_state["authenticated"] = False
#     st.session_state["user"] = None

def logout_user() -> None:

    st.session_state["authenticated"] = False

    st.session_state["user"] = None

    keys_to_remove = [

        "login_username",

        "face_login_running",

        "face_login_success",

        "face_login_user",

        "face_capture_state",
    ]

    for key in keys_to_remove:

        st.session_state.pop(
            key,
            None
        )
        
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
# ===================== 新增：全局操作日志工具 =====================
def write_operation_log(
    operator: dict,
    operate_type: str,
    operate_content: str,
    target_type: Optional[str] = None,
    target_id: Optional[int] = None
) -> None:
    """
    通用日志写入函数
    :param operator: 当前登录用户session信息 {username, role_name}
    :param operate_type: 操作类型（新增/删除/修改/批量导入/密码重置等）
    :param operate_content: 操作详情
    :param target_type: 操作对象类型（user/student/course/grade等）
    :param target_id: 操作对象ID
    """
    try:
        username = operator.get("username", "unknown")
        role = operator.get("role_name", "unknown")
        models.create_operation_log(
            operator_username=username,
            operator_role=role,
            operate_type=operate_type,
            operate_content=operate_content,
            target_type=target_type,
            target_id=target_id
        )
    except Exception:
        # 日志写入失败不影响主业务流程
        pass