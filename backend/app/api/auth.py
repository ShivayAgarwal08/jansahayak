from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserLogin, UserResponse, TokenResponse, UserUpdate
from app.core.security import hash_password, verify_password, create_access_token
from app.api.deps import get_current_user

from app.core.config import settings

router = APIRouter(prefix="/auth", tags=["Authentication"])

def _get_cookie_params():
    is_prod = settings.ENVIRONMENT == "production"
    return {
        "httponly": True,
        "max_age": 60 * 60 * 24,
        "samesite": "none" if is_prod else "lax",
        "secure": is_prod
    }

@router.post("/register", response_model=TokenResponse)
def register_citizen(user_in: UserCreate, response: Response, db: Session = Depends(get_db)):
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user_in.email.lower()).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists. Please log in."
        )

    user = User(
        full_name=user_in.full_name.strip(),
        email=user_in.email.lower().strip(),
        phone=user_in.phone,
        hashed_password=hash_password(user_in.password),
        role="citizen",
        preferred_language=user_in.preferred_language or "en",
        state=user_in.state,
        district=user_in.district,
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(subject=user.id, role=user.role)
    response.set_cookie(
        key="access_token",
        value=f"Bearer {token}",
        **_get_cookie_params()
    )

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": user
    }

@router.post("/login", response_model=TokenResponse)
def login_citizen(user_in: UserLogin, response: Response, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == user_in.email.lower()).first()
    if not user or not verify_password(user_in.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password. Please verify your credentials."
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This account has been deactivated. Please contact support."
        )

    token = create_access_token(subject=user.id, role=user.role)
    response.set_cookie(
        key="access_token",
        value=f"Bearer {token}",
        **_get_cookie_params()
    )

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": user
    }

@router.post("/logout")
def logout_citizen(response: Response):
    is_prod = settings.ENVIRONMENT == "production"
    response.delete_cookie(
        key="access_token",
        samesite="none" if is_prod else "lax",
        secure=is_prod
    )
    return {"message": "Successfully logged out."}

@router.get("/me", response_model=UserResponse)
def get_profile(current_user: User = Depends(get_current_user)):
    return current_user

@router.put("/me", response_model=UserResponse)
def update_profile(user_update: UserUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if user_update.full_name is not None:
        current_user.full_name = user_update.full_name.strip()
    if user_update.phone is not None:
        current_user.phone = user_update.phone.strip()
    if user_update.preferred_language is not None:
        current_user.preferred_language = user_update.preferred_language
    if user_update.state is not None:
        current_user.state = user_update.state
    if user_update.district is not None:
        current_user.district = user_update.district

    db.commit()
    db.refresh(current_user)
    return current_user

@router.delete("/me")
def delete_account(response: Response, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Citizen data privacy right: Permanently delete account and all associated drafts and bookmarks.
    """
    db.delete(current_user)
    db.commit()
    is_prod = settings.ENVIRONMENT == "production"
    response.delete_cookie(
        key="access_token",
        samesite="none" if is_prod else "lax",
        secure=is_prod
    )
    return {"message": "Your account and all associated personal records have been permanently deleted."}
