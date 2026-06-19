# import os
# from contextlib import contextmanager
# from typing import Any, Generator, Optional

# import psycopg2
# from psycopg2.extras import RealDictCursor


# def get_db_config() -> dict[str, Any]:
#     return {
#         "host": os.getenv("DB_HOST", "127.0.0.1"),
#         "port": int(os.getenv("DB_PORT", "5432")),
#         "dbname": os.getenv("DB_NAME", "postgres"),
#         "user": os.getenv("DB_USER", "db_user"),
#         "password": os.getenv("DB_PASSWORD", "DbUser@123"),
#         "sslmode": os.getenv("DB_SSLMODE", "prefer"),
#     }


# def get_connection():
#     config = get_db_config()
#     return psycopg2.connect(**config)


# @contextmanager
# def get_cursor(dict_cursor: bool = False) -> Generator[Any, None, None]:
#     conn = get_connection()
#     cursor = None
#     try:
#         if dict_cursor:
#             cursor = conn.cursor(cursor_factory=RealDictCursor)
#         else:
#             cursor = conn.cursor()
#         yield conn, cursor
#         conn.commit()
#     except Exception:
#         conn.rollback()
#         raise
#     finally:
#         if cursor is not None:
#             cursor.close()
#         conn.close()


# def execute_query(
#     query: str,
#     params: Optional[tuple[Any, ...] | dict[str, Any]] = None,
#     fetchone: bool = False,
#     dict_cursor: bool = True,
# ):
#     with get_cursor(dict_cursor=dict_cursor) as (_, cursor):
#         cursor.execute(query, params)
#         if fetchone:
#             return cursor.fetchone()
#         return cursor.fetchall()


# def execute_non_query(
#     query: str,
#     params: Optional[tuple[Any, ...] | dict[str, Any]] = None,
# ) -> int:
#     with get_cursor(dict_cursor=False) as (_, cursor):
#         cursor.execute(query, params)
#         return cursor.rowcount


# def execute_script(script: str) -> None:
#     with get_cursor(dict_cursor=False) as (_, cursor):
#         cursor.execute(script)


# def test_connection() -> bool:
#     try:
#         with get_cursor(dict_cursor=False) as (_, cursor):
#             cursor.execute("SELECT 1")
#             cursor.fetchone()
#         return True
#     except Exception:
#         return False

import os
from contextlib import contextmanager
from typing import Any, Generator, Optional
import psycopg2
from psycopg2.extras import RealDictCursor

def get_db_config() -> dict[str, Any]:
    return {
        "host": os.getenv("DB_HOST", "127.0.0.1"),
        "port": int(os.getenv("DB_PORT", "5432")),
        "dbname": os.getenv("DB_NAME", "postgres"),
        "user": os.getenv("DB_USER", "db_user"),
        "password": os.getenv("DB_PASSWORD", "DbUser@123"),
        "sslmode": os.getenv("DB_SSLMODE", "prefer"),
    }

def get_connection():
    env_port = os.getenv("DB_PORT")
    candidate_ports = []
    if env_port:
        candidate_ports.append(int(env_port))
    candidate_ports.extend([5432, 15432])

    seen = set()
    last_error = None
    for port in candidate_ports:
        if port in seen:
            continue
        seen.add(port)
        try:
            config = {
                "host": os.getenv("DB_HOST", "127.0.0.1"),
                "port": port,
                "dbname": os.getenv("DB_NAME", "postgres"),
                "user": os.getenv("DB_USER", "db_user"),
                "password": os.getenv("DB_PASSWORD", "DbUser@123"),
                "sslmode": os.getenv("DB_SSLMODE", "prefer"),
            }
            return psycopg2.connect(**config)
        except Exception as exc:
            last_error = exc

    if last_error is not None:
        raise last_error
    raise RuntimeError("无法建立数据库连接")

# ========== 修复点：Generator 补充第三个参数 None ==========
@contextmanager
def get_cursor(dict_cursor: bool = False) -> Generator[Any, None, None]:
    conn = get_connection()
    cursor = None
    try:
        if dict_cursor:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
        else:
            cursor = conn.cursor()
        yield conn, cursor
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        if cursor is not None:
            cursor.close()
        conn.close()

def execute_query(
    query: str,
    params: Optional[tuple[Any, ...] | dict[str, Any]] = None,
    fetchone: bool = False,
    dict_cursor: bool = True,
):
    with get_cursor(dict_cursor=dict_cursor) as (_, cursor):
        cursor.execute(query, params)
        if fetchone:
            return cursor.fetchone()
        return cursor.fetchall()

def execute_non_query(
    query: str,
    params: Optional[tuple[Any, ...] | dict[str, Any]] = None,
) -> int:
    with get_cursor(dict_cursor=False) as (_, cursor):
        cursor.execute(query, params)
        return cursor.rowcount

def execute_script(script: str) -> None:
    with get_cursor(dict_cursor=False) as (_, cursor):
        cursor.execute(script)

def test_connection() -> bool:
    try:
        with get_cursor(dict_cursor=False) as (_, cursor):
            cursor.execute("SELECT 1")
            cursor.fetchone()
        return True
    except Exception:
        return None

# ===================== 操作日志表初始化（项目启动自动建表） =====================
def init_operation_log_table() -> None:
    """初始化操作日志表，不存在则自动创建"""
    create_sql = """
    CREATE TABLE IF NOT EXISTS operation_log (
        id SERIAL PRIMARY KEY,
        operator_username VARCHAR(50) NOT NULL,
        operator_role VARCHAR(20) NOT NULL,
        operate_type VARCHAR(50) NOT NULL,
        operate_content TEXT NOT NULL,
        target_type VARCHAR(30),
        target_id INT,
        operate_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        client_ip VARCHAR(50)
    );
    """
    execute_script(create_sql)

# 项目启动自动初始化日志表
init_operation_log_table()