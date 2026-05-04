from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.user import User
from app.core.security import hash_password, verify_password, create_token


def register_user(db, name, email, password, mobileno):
    # check if user exists
    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        return {"error": "User already exists"}

    new_user = User(
        name=name,
        email=email,
        password=hash_password(password),
        mobileno=mobileno
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {"message": "User registered successfully"}


def login_user(db: Session, email: str, password: str):
    user = db.query(User).filter(User.email == email).first()

    if not user or not verify_password(password, user.password):
        raise HTTPException(401, "Invalid credentials")

    return create_token({"user_id": user.id})