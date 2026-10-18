from typing import Optional
from fastapi import Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.security import decode_access_token, oauth2_scheme
from app.models.user import User

def get_token_from_request(request: Request, token_header: Optional[str] = Depends(oauth2_scheme)) -> Optional[str]:
    """
    Extract token from Authorization header or HTTP-only cookie.
    """
    if token_header:
        return token_header
    cookie_token = request.cookies.get("access_token")
    if cookie_token:
        if cookie_token.startswith("Bearer "):
            return cookie_token[7:]
        return cookie_token
    return None

def get_current_user(
    request: Request,
    token: Optional[str] = Depends(get_token_from_request),
    db: Session = Depends(get_db)
) -> User:
    """
    Ensure the request is authenticated and return the current user.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate authentication credentials. Please log in.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not token:
        raise credentials_exception

    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        raise credentials_exception

    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user or not user.is_active:
        raise credentials_exception

    return user

def get_current_user_optional(
    request: Request,
    token: Optional[str] = Depends(get_token_from_request),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Optional authentication for endpoints accessible to both guests and citizens.
    """
    if not token:
        return None
    try:
        payload = decode_access_token(token)
        if not payload or "sub" not in payload:
            return None
        user = db.query(User).filter(User.id == int(payload["sub"])).first()
        return user if (user and user.is_active) else None
    except Exception:
        return None

def get_current_admin(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Ensure the current user has the administrator role.
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrative privileges required to access this resource."
        )
    return current_user
