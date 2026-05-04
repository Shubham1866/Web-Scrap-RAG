from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from datetime import datetime
from app.db.session import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    mobileno = Column(String(15))
    email = Column(String(255), unique=True, index=True, nullable=False)
    password = Column(String(255), nullable=False)
