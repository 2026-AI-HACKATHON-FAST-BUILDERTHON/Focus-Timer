"""
인증 관련 API 라우터 - Supabase DB 연동
"""

from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime, timedelta
import uuid
import bcrypt
from jose import jwt, JWTError

from database.connection import get_cursor

router = APIRouter(prefix="/auth", tags=["Auth"])

# JWT 설정
SECRET_KEY = "focus-timer-secret-key-2024-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24 * 7  # 7일


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
    nickname: Optional[str] = None


class UserResponse(BaseModel):
    user_id: str
    email: str
    nickname: Optional[str]
    coin_balance: int
    mbti_type: Optional[str] = None
    current_streak_days: int = 0


def hash_password(password: str) -> str:
    """비밀번호 해싱"""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    """비밀번호 검증"""
    return bcrypt.checkpw(password.encode(), hashed.encode())


def create_access_token(user_id: str, email: str) -> str:
    """JWT 토큰 생성"""
    expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    payload = {
        "sub": user_id,
        "email": email,
        "exp": expire,
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    """JWT 토큰 디코딩"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="유효하지 않은 토큰입니다")


async def get_current_user(authorization: Optional[str] = Header(None)) -> dict:
    """
    JWT 토큰 검증 및 사용자 정보 반환
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="인증이 필요합니다")

    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="잘못된 인증 형식입니다")

    token = authorization[7:]
    payload = decode_token(token)

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="유효하지 않은 토큰입니다")

    # DB에서 사용자 조회
    with get_cursor() as cur:
        cur.execute(
            """
            SELECT id, email, nickname, coin_balance, mbti_type,
                   current_streak_days, persona_type, is_active
            FROM users
            WHERE id = %s AND is_active = TRUE
            """,
            (user_id,)
        )
        user = cur.fetchone()

    if not user:
        raise HTTPException(status_code=401, detail="사용자를 찾을 수 없습니다")

    return dict(user)


@router.post("/signup", response_model=TokenResponse)
async def signup(request: SignupRequest):
    """
    회원가입 - 이메일/비밀번호
    """
    with get_cursor() as cur:
        # 이메일 중복 확인
        cur.execute("SELECT id FROM users WHERE email = %s", (request.email,))
        if cur.fetchone():
            raise HTTPException(status_code=400, detail="이미 가입된 이메일입니다")

        # 새 사용자 생성
        user_id = str(uuid.uuid4())
        password_hash = hash_password(request.password)
        nickname = request.nickname or request.email.split("@")[0]

        cur.execute(
            """
            INSERT INTO users (id, email, password_hash, nickname, coin_balance)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id, email, nickname
            """,
            (user_id, request.email, password_hash, nickname, 0)
        )
        new_user = cur.fetchone()

    access_token = create_access_token(user_id, request.email)

    return TokenResponse(
        access_token=access_token,
        user_id=str(new_user["id"]),
        email=new_user["email"],
        nickname=new_user["nickname"],
    )


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    """
    로그인 - 이메일/비밀번호
    """
    with get_cursor() as cur:
        cur.execute(
            """
            SELECT id, email, password_hash, nickname, is_active
            FROM users
            WHERE email = %s
            """,
            (request.email,)
        )
        user = cur.fetchone()

    if not user:
        raise HTTPException(status_code=401, detail="이메일 또는 비밀번호가 올바르지 않습니다")

    if not user["is_active"]:
        raise HTTPException(status_code=401, detail="비활성화된 계정입니다")

    if not verify_password(request.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="이메일 또는 비밀번호가 올바르지 않습니다")

    # 마지막 로그인 시간 업데이트
    with get_cursor() as cur:
        cur.execute(
            "UPDATE users SET last_session_at = NOW() WHERE id = %s",
            (str(user["id"]),)
        )

    access_token = create_access_token(str(user["id"]), user["email"])

    return TokenResponse(
        access_token=access_token,
        user_id=str(user["id"]),
        email=user["email"],
        nickname=user["nickname"],
    )


@router.get("/me", response_model=UserResponse)
async def get_me(user: dict = Depends(get_current_user)):
    """
    현재 로그인한 사용자 정보 조회
    """
    return UserResponse(
        user_id=str(user["id"]),
        email=user["email"],
        nickname=user.get("nickname"),
        coin_balance=user.get("coin_balance", 0),
        mbti_type=user.get("mbti_type"),
        current_streak_days=user.get("current_streak_days", 0),
    )


@router.post("/logout")
async def logout(user: dict = Depends(get_current_user)):
    """
    로그아웃 (클라이언트에서 토큰 삭제)
    """
    return {"message": "로그아웃 성공"}
