"""
AUTHENTICATION & AUTHORIZATION STUB
Owner: Ahmed (FastAPI foundation & authentication lead - 70%)
Maintained temporarily by: Tigiste (Integration & Security Lead)

TODO (Ahmed): Replace this mock/stub with the official JWT verification
once backend/auth/ or backend/api/auth.py lands.
"""
from typing import Annotated, Callable, Optional
from fastapi import Depends, HTTPException, Header, status
from pydantic import BaseModel


class CurrentUser(BaseModel):
    id: int
    phone: str
    name: str
    role: str  # "ANALYST", "ADMIN", "USER"


# Standard mock tokens for integration/testing until Ahmed's JWT lands
MOCK_USERS: dict[str, CurrentUser] = {
    "mock-analyst-token": CurrentUser(
        id=1, phone="0911000001", name="Analyst Tigiste", role="ANALYST"
    ),
    "mock-admin-token": CurrentUser(
        id=2, phone="0911000002", name="Admin Ahmed", role="ADMIN"
    ),
    "mock-user-token": CurrentUser(
        id=3, phone="0911000003", name="Standard User", role="USER"
    ),
}


def get_current_user(
    authorization: Annotated[Optional[str], Header()] = None,
) -> CurrentUser:
    """
    Validates Bearer token from the Authorization header.
    Raises 401 if missing, malformed, or invalid.
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format. Expected 'Bearer <token>'",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = authorization.removeprefix("Bearer ").strip()

    if token == "expired-token":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = MOCK_USERS.get(token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or unrecognized authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


def require_role(allowed_roles: list[str]) -> Callable[[CurrentUser], CurrentUser]:
    """
    Dependency factory to enforce role-based access control (RBAC).
    Rejects unauthorized roles with 403 Forbidden.
    """
    def role_checker(
        current_user: Annotated[CurrentUser, Depends(get_current_user)]
    ) -> CurrentUser:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access forbidden: role '{current_user.role}' lacks required permissions",
            )
        return current_user

    return role_checker
