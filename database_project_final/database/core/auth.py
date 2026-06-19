import hashlib
import hmac
from typing import Any, Optional

from core import models


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def verify_password(password: str, password_hash: str) -> bool:
    calculated = hash_password(password)
    return hmac.compare_digest(calculated, password_hash)


def get_current_user(user_id: int) -> Optional[dict[str, Any]]:
    return models.get_user_by_id(user_id)


def get_role_name(user_id: int) -> Optional[str]:
    user = models.get_user_by_id(user_id)
    if not user:
        return None
    return str(user["role_name"])


def is_user_active(user: Optional[dict[str, Any]]) -> bool:
    if not user:
        return False
    return bool(user.get("is_active", False))


def login(username: str, password: str) -> Optional[dict[str, Any]]:
    user = models.get_user_by_username(username)
    if not user:
        return None
    if not is_user_active(user):
        return None
    if not verify_password(password, str(user["password_hash"])):
        return None

    return {
        "id": user["id"],
        "username": user["username"],
        "role_name": user["role_name"],
        "is_active": user["is_active"],
    }


def change_password(user_id: int, new_password: str) -> Optional[dict[str, Any]]:
    new_hash = hash_password(new_password)
    return models.update_user_password(user_id, new_hash)

def get_user_by_username(
    username: str
) -> Optional[dict[str, Any]]:

    user = models.get_user_by_username(
        username
    )

    if not user:
        return None

    if not is_user_active(user):
        return None

    return {
        "id": user["id"],
        "username": user["username"],
        "role_name": user["role_name"],
        "is_active": user["is_active"],
    }