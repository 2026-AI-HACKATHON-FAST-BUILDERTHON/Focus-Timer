"""
세션 관련 API 라우터
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from datetime import datetime, timedelta
import uuid

from models.schemas import (
    SessionStartRequest,
    SessionCompleteRequest,
    SessionAbortRequest,
    SessionResponse,
    SessionStatus,
)
from routers.auth import get_current_user

router = APIRouter(prefix="/sessions", tags=["Sessions"])

# 임시 인메모리 저장소 (데모용)
sessions_db: dict = {}
user_coins: dict = {}


def calculate_coin_reward(total_focus_sec: int, completed: bool) -> int:
    """
    코인 보상 계산
    - 집중 시간 1분당 10코인
    - 완료 보너스 +20%
    """
    base_reward = (total_focus_sec // 60) * 10
    if completed:
        base_reward = int(base_reward * 1.2)
    return base_reward


@router.post("/start", response_model=SessionResponse)
async def start_session(
    request: SessionStartRequest,
    user: dict = Depends(get_current_user),
):
    """
    새 세션 시작
    """
    session_id = str(uuid.uuid4())
    now = datetime.utcnow()

    session = {
        "id": session_id,
        "user_id": user["user_id"],
        "task_type": request.task_type,
        "difficulty": request.difficulty,
        "goal": request.goal,
        "mode_plan": request.mode_plan,
        "status": None,  # 진행 중
        "abort_reason": None,
        "total_focus_sec": 0,
        "total_break_sec": 0,
        "rounds_completed": 0,
        "coin_reward": 0,
        "created_at": now,
        "start_hour": now.hour,
    }

    sessions_db[session_id] = session

    return SessionResponse(
        id=session_id,
        user_id=user["user_id"],
        task_type=request.task_type,
        difficulty=request.difficulty,
        goal=request.goal,
        mode_plan=request.mode_plan,
        status=SessionStatus.COMPLETED,  # 임시
        abort_reason=None,
        total_focus_sec=0,
        total_break_sec=0,
        rounds_completed=0,
        coin_reward=0,
        created_at=now,
    )


@router.post("/complete", response_model=SessionResponse)
async def complete_session(
    request: SessionCompleteRequest,
    user: dict = Depends(get_current_user),
):
    """
    세션 완료
    - 코인 보상 지급
    """
    if request.session_id not in sessions_db:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    session = sessions_db[request.session_id]

    if session["user_id"] != user["user_id"]:
        raise HTTPException(status_code=403, detail="권한이 없습니다")

    # 코인 보상 계산
    coin_reward = calculate_coin_reward(request.total_focus_sec, completed=True)

    # 세션 업데이트
    session.update({
        "status": SessionStatus.COMPLETED,
        "total_focus_sec": request.total_focus_sec,
        "total_break_sec": request.total_break_sec,
        "rounds_completed": request.rounds_completed,
        "coin_reward": coin_reward,
    })

    # 사용자 코인 업데이트
    user_id = user["user_id"]
    if user_id not in user_coins:
        user_coins[user_id] = 0
    user_coins[user_id] += coin_reward

    return SessionResponse(
        id=session["id"],
        user_id=session["user_id"],
        task_type=session["task_type"],
        difficulty=session["difficulty"],
        goal=session["goal"],
        mode_plan=session["mode_plan"],
        status=SessionStatus.COMPLETED,
        abort_reason=None,
        total_focus_sec=request.total_focus_sec,
        total_break_sec=request.total_break_sec,
        rounds_completed=request.rounds_completed,
        coin_reward=coin_reward,
        created_at=session["created_at"],
    )


@router.post("/abort", response_model=SessionResponse)
async def abort_session(
    request: SessionAbortRequest,
    user: dict = Depends(get_current_user),
):
    """
    세션 중단
    - 중단 사유 기록
    - 부분 보상 지급
    """
    if request.session_id not in sessions_db:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    session = sessions_db[request.session_id]

    if session["user_id"] != user["user_id"]:
        raise HTTPException(status_code=403, detail="권한이 없습니다")

    # 부분 코인 보상 (완료 보너스 없음)
    coin_reward = calculate_coin_reward(request.total_focus_sec, completed=False)

    # 세션 업데이트
    session.update({
        "status": SessionStatus.ABORTED,
        "abort_reason": request.abort_reason,
        "total_focus_sec": request.total_focus_sec,
        "rounds_completed": request.rounds_completed,
        "coin_reward": coin_reward,
    })

    # 사용자 코인 업데이트
    user_id = user["user_id"]
    if user_id not in user_coins:
        user_coins[user_id] = 0
    user_coins[user_id] += coin_reward

    return SessionResponse(
        id=session["id"],
        user_id=session["user_id"],
        task_type=session["task_type"],
        difficulty=session["difficulty"],
        goal=session["goal"],
        mode_plan=session["mode_plan"],
        status=SessionStatus.ABORTED,
        abort_reason=request.abort_reason,
        total_focus_sec=request.total_focus_sec,
        total_break_sec=0,
        rounds_completed=request.rounds_completed,
        coin_reward=coin_reward,
        created_at=session["created_at"],
    )


@router.get("", response_model=List[SessionResponse])
async def get_sessions(
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    limit: int = 20,
    user: dict = Depends(get_current_user),
):
    """
    세션 목록 조회
    """
    user_sessions = [
        s for s in sessions_db.values()
        if s["user_id"] == user["user_id"] and s["status"] is not None
    ]

    # 날짜 필터링
    if from_date:
        from_dt = datetime.fromisoformat(from_date)
        user_sessions = [s for s in user_sessions if s["created_at"] >= from_dt]

    if to_date:
        to_dt = datetime.fromisoformat(to_date)
        user_sessions = [s for s in user_sessions if s["created_at"] <= to_dt]

    # 최신순 정렬
    user_sessions.sort(key=lambda x: x["created_at"], reverse=True)

    return [
        SessionResponse(
            id=s["id"],
            user_id=s["user_id"],
            task_type=s["task_type"],
            difficulty=s["difficulty"],
            goal=s["goal"],
            mode_plan=s["mode_plan"],
            status=s["status"],
            abort_reason=s.get("abort_reason"),
            total_focus_sec=s["total_focus_sec"],
            total_break_sec=s["total_break_sec"],
            rounds_completed=s["rounds_completed"],
            coin_reward=s["coin_reward"],
            created_at=s["created_at"],
        )
        for s in user_sessions[:limit]
    ]
