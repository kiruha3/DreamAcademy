from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, validator
from sqlalchemy.orm import Session
from typing import Optional
import secrets

from .security import get_db, get_password_hash, verify_password, create_access_token, get_current_user
from .models import User
from .config import get_settings
from .moodle_client import MoodleClient

router = APIRouter(prefix="/auth", tags=["auth"])


async def get_moodle_client() -> MoodleClient:
    settings = get_settings()
    client = MoodleClient(base_url=settings.MOODLE_URL, token=settings.MOODLE_TOKEN)
    try:
        yield client
    finally:
        await client.close()


class RegisterRequest(BaseModel):
    email: EmailStr
    username: str
    firstname: str
    lastname: str
    password: str
    role: str = "student"

    @validator("role")
    def validate_role(cls, v):
        allowed = {"student", "teacher", "course_creator", "admin"}
        if v not in allowed:
            raise ValueError(f"role must be one of {allowed}")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


class UserOut(BaseModel):
    id: int
    email: str
    username: str
    firstname: str
    lastname: str
    role: str
    moodle_user_id: Optional[int] = None

    model_config = {"from_attributes": True}


@router.post("/register")
async def register(
    req: RegisterRequest,
    db: Session = Depends(get_db),
    client: MoodleClient = Depends(get_moodle_client),
):
    if db.query(User).filter(User.email == req.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    if db.query(User).filter(User.username == req.username).first():
        raise HTTPException(status_code=400, detail="Username already taken")

    # Create user in Moodle first (or sync if already exists)
    moodle_password = req.password
    try:
        existing_moodle = await client.get_users(key="email", value=req.email)
        user_list = existing_moodle.get("users", [])
        if user_list:
            moodle_user_id = user_list[0]["id"]
        else:
            moodle_resp = await client.create_user(
                username=req.username,
                password=moodle_password,
                firstname=req.firstname,
                lastname=req.lastname,
                email=req.email,
            )
            moodle_user_id = moodle_resp[0]["id"] if isinstance(moodle_resp, list) and len(moodle_resp) > 0 else None
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Moodle user creation failed: {str(e)}")

    db_user = User(
        email=req.email,
        username=req.username,
        firstname=req.firstname,
        lastname=req.lastname,
        hashed_password=get_password_hash(req.password),
        role=req.role,
        moodle_user_id=moodle_user_id,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    access_token = create_access_token(data={"sub": str(db_user.id)})
    return {"access_token": access_token, "token_type": "bearer", "user": UserOut.model_validate(db_user)}


@router.post("/login")
async def login(req: LoginRequest, db: Session = Depends(get_db), client: MoodleClient = Depends(get_moodle_client)):
    user = db.query(User).filter(User.email == req.email).first()
    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    # Sync password to Moodle so portal pass == Moodle pass
    if user.moodle_user_id:
        try:
            await client.update_user_password(user.moodle_user_id, req.password)
        except Exception:
            pass  # Don't block login if Moodle update fails
    access_token = create_access_token(data={"sub": str(user.id)})
    return {"access_token": access_token, "token_type": "bearer", "user": UserOut.model_validate(user)}


@router.get("/me", response_model=UserOut)
async def read_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.get("/moodle-credentials")
async def moodle_credentials(current_user: User = Depends(get_current_user)):
    """Return Moodle login info for the authenticated user."""
    return {
        "moodle_url": get_settings().MOODLE_PUBLIC_URL,
        "username": current_user.username,
        "note": "Use the same password you use for the portal. It is automatically synced.",
    }


@router.post("/change-password")
async def change_password(
    req: ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    client: MoodleClient = Depends(get_moodle_client),
):
    if not verify_password(req.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    # Update local password
    current_user.hashed_password = get_password_hash(req.new_password)
    db.commit()
    # Sync to Moodle
    if current_user.moodle_user_id:
        try:
            await client.update_user_password(current_user.moodle_user_id, req.new_password)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Local password changed, but Moodle sync failed: {str(e)}")
    return {"status": "password_changed"}
