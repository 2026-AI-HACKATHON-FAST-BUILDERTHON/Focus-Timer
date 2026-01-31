"""
인증 관련 API 라우터
"""

from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel, EmailStr
from typing import Optional
import os

router = APIRouter(prefix="/auth", tags=["Auth"])


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class SignupRequest(BaseModel):
    email: EmailStr
    password: str
    nickname: Optional[str] = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    email: str


class UserResponse(BaseModel):
    user_id: str
    email: str
    nickname: Optional[str]
    coin_balance: int


# 임시 인메모리 저장소 (데모용)
demo_users = {
    "demo@example.com": {
        "user_id": "demo-user-123",
        "email": "demo@example.com",
        "password": "demo123",
        "nickname": "데모 유저",
        "coin_balance": 100,
    }
}


async def get_current_user(authorization: Optional[str] = Header(None)) -> dict:
    """
    JWT 토큰 검증 및 사용자 정보 반환
    실제 구현에서는 Supabase JWT 검증
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="인증이 필요합니다")

    # 데모용: 간단한 토큰 검증
    if authorization.startswith("Bearer "):
        token = authorization[7:]
        # 실제로는 Supabase JWT 검증
        if token.startswith("demo-token-"):
            email = token.replace("demo-token-", "")
            if email in demo_users:
                return demo_users[email]

    raise HTTPException(status_code=401, detail="유효하지 않은 토큰입니다")


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    """
    로그인 - 이메일/비밀번호
    실제 구현에서는 Supabase Auth 사용
    """
    # 데모용 로그인
    if request.email in demo_users:
        user = demo_users[request.email]
        if user["password"] == request.password:
            return TokenResponse(
                access_token=f"demo-token-{request.email}",
                user_id=user["user_id"],
                email=user["email"],
            )

    # 새 사용자 자동 생성 (데모용)
    user_id = f"user-{len(demo_users) + 1}"
    demo_users[request.email] = {
        "user_id": user_id,
        "email": request.email,
        "password": request.password,
        "nickname": request.email.split("@")[0],
        "coin_balance": 0,
    }

    return TokenResponse(
        access_token=f"demo-token-{request.email}",
        user_id=user_id,
        email=request.email,
    )


@router.post("/signup", response_model=TokenResponse)
async def signup(request: SignupRequest):
    """
    회원가입
    실제 구현에서는 Supabase Auth 사용
    """
    if request.email in demo_users:
        raise HTTPException(status_code=400, detail="이미 가입된 이메일입니다")

    user_id = f"user-{len(demo_users) + 1}"
    demo_users[request.email] = {
        "user_id": user_id,
        "email": request.email,
        "password": request.password,
        "nickname": request.nickname or request.email.split("@")[0],
        "coin_balance": 0,
    }

    return TokenResponse(
        access_token=f"demo-token-{request.email}",
        user_id=user_id,
        email=request.email,
    )


@router.get("/me", response_model=UserResponse)
async def get_me(user: dict = Depends(get_current_user)):
    """
    현재 로그인한 사용자 정보 조회
    """
    return UserResponse(
        user_id=user["user_id"],
        email=user["email"],
        nickname=user.get("nickname"),
        coin_balance=user.get("coin_balance", 0),
    )
