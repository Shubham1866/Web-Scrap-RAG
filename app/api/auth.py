from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.schemas.auth import RegisterRequest, LoginRequest
from app.services.auth_service import register_user, login_user
from app.db.session import get_db

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/register")
def register(user: RegisterRequest, db: Session = Depends(get_db)):
    result = register_user(db, user.name, user.email, user.password, user.mobileno)

    if not result:
        raise HTTPException(status_code=400, detail="Email already exists")

    return {"message": "User registered successfully"}


@router.post("/login")
def login(user: LoginRequest, db: Session = Depends(get_db)):
    token = login_user(db, user.email, user.password)

    if not token:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    return {
        "access_token": token,
        "token_type": "bearer"
    }