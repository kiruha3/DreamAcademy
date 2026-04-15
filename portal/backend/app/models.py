from sqlalchemy import Column, Integer, String, DateTime, Float, Text, func
from .database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    firstname = Column(String, nullable=False)
    lastname = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="student", nullable=False)
    moodle_user_id = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Submission(Base):
    __tablename__ = "submissions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    cmid = Column(Integer, nullable=False, index=True)
    course_id = Column(Integer, nullable=False, index=True)
    file_path = Column(String, nullable=True)
    submitted_at = Column(DateTime(timezone=True), server_default=func.now())
    grade = Column(Float, nullable=True)
    feedback = Column(Text, nullable=True)
    graded_at = Column(DateTime(timezone=True), nullable=True)
