from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from backend.database.session import get_db
from backend.rate_limiter import limiter
from backend.models.user import User
from backend.schemas.auth import TokenResponse, UserLogin, UserPublic, UserRegister
from backend.auth.security import (
    create_access_token,
    get_current_user,
    get_password_hash,
    require_roles,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserPublic, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
def register_user(request: Request, user_data: UserRegister, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.phone == user_data.phone).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already exists",
        )

    new_user = User(
        phone=user_data.phone,
        name=user_data.name,
        password_hash=get_password_hash(user_data.password),
        role="USER",
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/minute")
def login_user(request: Request, user_data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.phone == user_data.phone).first()

    if not user or not verify_password(user_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid phone or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token(user.id, user.role)
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": user,
    }


@router.get("/me", response_model=UserPublic)
def get_current_user_data(current_user: User = Depends(get_current_user)):
    return current_user


@router.get("/user-only")
def user_only(current_user: User = Depends(require_roles("USER"))):
    return {"message": "Access granted", "user": current_user.phone}


@router.get("/analyst-only")
def analyst_only(current_user: User = Depends(require_roles("ANALYST"))):
    return {"message": "Access granted", "user": current_user.phone}


@router.get("/admin-only")
def admin_only(current_user: User = Depends(require_roles("ADMIN"))):
    return {"message": "Access granted", "user": current_user.phone}
