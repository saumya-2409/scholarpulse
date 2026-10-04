from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from jose import JWTError, jwt

from config import (
    JWT_SECRET_KEY,
    JWT_ALGORITHM,
    JWT_EXPIRE_MINUTES,
)

from database import create_user, login_user
from utils.auth import get_current_user


router = APIRouter(
    prefix="/api/auth",
    tags=["Authentication"],
)


class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str

def create_access_token(user_id: int, email: str):
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=JWT_EXPIRE_MINUTES
    )

    payload = {
        "sub": str(user_id),
        "email": email,
        "exp": expire,
    }

    return jwt.encode(
        payload,
        JWT_SECRET_KEY,
        algorithm=JWT_ALGORITHM,
    )


@router.post("/register")
def register(request: RegisterRequest):
    name = request.name.strip()
    email = request.email.strip().lower()
    password = request.password

    if not name:
        raise HTTPException(
            status_code=400,
            detail="Name is required.",
        )

    if len(password) < 6:
        raise HTTPException(
            status_code=400,
            detail="Password must be at least 6 characters.",
        )

    result = create_user(
        email=email,
        name=name,
        password=password,
    )

    if not result["success"]:
        raise HTTPException(
            status_code=400,
            detail=result["error"],
        )

    return {
        "message": "Account created successfully.",
        "user": {
            "id": result["user_id"],
            "name": result["name"],
            "email": result["email"],
        },
    }


@router.post("/login")
def login(request: LoginRequest):
    email = request.email.strip().lower()

    result = login_user(
        email=email,
        password=request.password,
    )

    if not result["success"]:
        raise HTTPException(
            status_code=401,
            detail=result["error"],
        )

    user = result["user"]

    access_token = create_access_token(
        user_id=user["id"],
        email=user["email"],
    )

    return {
        "message": "Login successful.",
        "access_token": access_token,
        "token_type": "bearer",
        "user": user,
    }


@router.get("/me")
def get_me(current_user=Depends(get_current_user)):
    return {
        "user": current_user,
    }