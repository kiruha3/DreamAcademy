import os
import sys
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Ensure app is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.database import Base
from app.models import User

# Use in-memory SQLite for tests
TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def sample_user(db):
    user = User(
        email="test@example.com",
        username="testuser",
        firstname="Test",
        lastname="User",
        role="student",
        hashed_password="hashed",
        moodle_user_id=1,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
