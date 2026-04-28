from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer
from jose import jwt
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.core.security import SECRET_KEY, ALGORITHM

security = HTTPBearer()


def get_current_user(token=Depends(security), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")
    except:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = db.query(User).get(user_id)
    return user