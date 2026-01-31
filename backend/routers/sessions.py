"""
세션 관련 API 라우터 - Supabase DB 연동
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from datetime import datetime
import uuid

from models.schemas import (
    SessionStartRequest,
    SessionCompleteRequest,
    SessionAbortRequest,
    SessionResponse,
    SessionStatus,
)
from routers.auth import get_current_user
from database.connection import get_cursor
from services.advanced_recommender import get_advanced_recommender

router = APIRouter(prefix="/sessions", tags=["Sessions"])


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
    user_id = str(user["id"])
    now = datetime.utcnow()

    # mode_plan JSON 변환
    mode_plan_json = None
    planned_focus = 25
    planned_break = 5
    planned_rounds = 4

    if request.mode_plan:
        import json
        mode_plan_json = json.dumps(request.mode_plan)
        # 첫 번째 focus와 break 추출
        for phase in request.mode_plan:
            if phase.get("type") == "focus":
                planned_focus = phase.get("minutes", 25)
                break
        for phase in request.mode_plan:
            if phase.get("type") == "break":
                planned_break = phase.get("minutes", 5)
                break
        planned_rounds = sum(1 for p in request.mode_plan if p.get("type") == "focus")

    with get_cursor() as cur:
        cur.execute(
            """
            INSERT INTO sessions (
                id, user_id, task_type, difficulty, goal, status,
                planned_focus_min, planned_break_min, planned_rounds, mode_plan,
                start_hour, day_of_week, created_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id, user_id, task_type, difficulty, goal, status,
                      total_focus_sec, total_break_sec, rounds_completed,
                      coin_reward, created_at
            """,
            (
                session_id, user_id, request.task_type, request.difficulty,
                request.goal, "in_progress",
                planned_focus, planned_break, planned_rounds, mode_plan_json,
                now.hour, now.weekday(), now
            )
        )
        session = cur.fetchone()

    return SessionResponse(
        id=str(session["id"]),
        user_id=str(session["user_id"]),
        task_type=session["task_type"],
        difficulty=session["difficulty"],
        goal=session["goal"],
        mode_plan=request.mode_plan,
        status=SessionStatus.COMPLETED,  # 임시 반환값
        abort_reason=None,
        total_focus_sec=0,
        total_break_sec=0,
        rounds_completed=0,
        coin_reward=0,
        created_at=session["created_at"],
    )


@router.post("/complete", response_model=SessionResponse)
async def complete_session(
    request: SessionCompleteRequest,
    user: dict = Depends(get_current_user),
):
    """
    세션 완료 - 코인 보상 지급
    """
    user_id = str(user["id"])

    with get_cursor() as cur:
        # 세션 조회
        cur.execute(
            "SELECT * FROM sessions WHERE id = %s",
            (request.session_id,)
        )
        session = cur.fetchone()

        if not session:
            raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

        if str(session["user_id"]) != user_id:
            raise HTTPException(status_code=403, detail="권한이 없습니다")

        # 코인 보상 계산
        coin_reward = calculate_coin_reward(request.total_focus_sec, completed=True)

        # 세션 업데이트
        cur.execute(
            """
            UPDATE sessions SET
                status = 'completed',
                total_focus_sec = %s,
                total_break_sec = %s,
                rounds_completed = %s,
                coin_reward = %s,
                completed_at = NOW(),
                updated_at = NOW()
            WHERE id = %s
            RETURNING *
            """,
            (
                request.total_focus_sec,
                request.total_break_sec,
                request.rounds_completed,
                coin_reward,
                request.session_id
            )
        )
        updated_session = cur.fetchone()

        # 사용자 코인 업데이트
        cur.execute(
            """
            UPDATE users SET
                coin_balance = coin_balance + %s,
                total_coins_earned = total_coins_earned + %s,
                last_session_at = NOW()
            WHERE id = %s
            """,
            (coin_reward, coin_reward, user_id)
        )

    # AI 실시간 학습 업데이트
    try:
        recommender = get_advanced_recommender()
        focus_minutes = updated_session.get("planned_focus_min", 25)
        break_minutes = updated_session.get("planned_break_min", 5)
        rounds = updated_session.get("planned_rounds", 4)
        recommender.update_mab(focus_minutes, break_minutes, rounds, success=True)
        recommender.golden_time.update(
            updated_session["start_hour"],
            updated_session["day_of_week"],
            success=True
        )
        recommender.adaptive_difficulty.update(updated_session["difficulty"], success=True)
    except Exception as e:
        print(f"AI update error (complete): {e}")

    # golden_time_stats 테이블 업데이트
    with get_cursor() as cur:
        cur.execute(
            """
            INSERT INTO golden_time_stats (user_id, hour, day_of_week, success_count, total_count)
            VALUES (%s, %s, %s, 1, 1)
            ON CONFLICT (user_id, hour, day_of_week)
            DO UPDATE SET
                success_count = golden_time_stats.success_count + 1,
                total_count = golden_time_stats.total_count + 1,
                updated_at = NOW()
            """,
            (user_id, updated_session["start_hour"], updated_session["day_of_week"])
        )

        # adaptive_difficulty_history 추가
        cur.execute(
            """
            INSERT INTO adaptive_difficulty_history (user_id, difficulty, success, session_id)
            VALUES (%s, %s, %s, %s)
            """,
            (user_id, updated_session["difficulty"], True, request.session_id)
        )

    return SessionResponse(
        id=str(updated_session["id"]),
        user_id=str(updated_session["user_id"]),
        task_type=updated_session["task_type"],
        difficulty=updated_session["difficulty"],
        goal=updated_session["goal"],
        mode_plan=None,
        status=SessionStatus.COMPLETED,
        abort_reason=None,
        total_focus_sec=request.total_focus_sec,
        total_break_sec=request.total_break_sec,
        rounds_completed=request.rounds_completed,
        coin_reward=coin_reward,
        created_at=updated_session["created_at"],
    )


@router.post("/abort", response_model=SessionResponse)
async def abort_session(
    request: SessionAbortRequest,
    user: dict = Depends(get_current_user),
):
    """
    세션 중단 - 중단 사유 기록, 부분 보상 지급
    """
    user_id = str(user["id"])

    with get_cursor() as cur:
        # 세션 조회
        cur.execute(
            "SELECT * FROM sessions WHERE id = %s",
            (request.session_id,)
        )
        session = cur.fetchone()

        if not session:
            raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

        if str(session["user_id"]) != user_id:
            raise HTTPException(status_code=403, detail="권한이 없습니다")

        # 부분 코인 보상 (완료 보너스 없음)
        coin_reward = calculate_coin_reward(request.total_focus_sec, completed=False)

        # 세션 업데이트
        cur.execute(
            """
            UPDATE sessions SET
                status = 'aborted',
                abort_reason = %s,
                total_focus_sec = %s,
                rounds_completed = %s,
                coin_reward = %s,
                completed_at = NOW(),
                updated_at = NOW()
            WHERE id = %s
            RETURNING *
            """,
            (
                request.abort_reason,
                request.total_focus_sec,
                request.rounds_completed,
                coin_reward,
                request.session_id
            )
        )
        updated_session = cur.fetchone()

        # 사용자 코인 업데이트
        cur.execute(
            """
            UPDATE users SET
                coin_balance = coin_balance + %s,
                total_coins_earned = total_coins_earned + %s,
                last_session_at = NOW()
            WHERE id = %s
            """,
            (coin_reward, coin_reward, user_id)
        )

    # AI 실시간 학습 업데이트 (실패)
    try:
        recommender = get_advanced_recommender()
        focus_minutes = updated_session.get("planned_focus_min", 25)
        break_minutes = updated_session.get("planned_break_min", 5)
        rounds = updated_session.get("planned_rounds", 4)
        recommender.update_mab(focus_minutes, break_minutes, rounds, success=False)
        recommender.golden_time.update(
            updated_session["start_hour"],
            updated_session["day_of_week"],
            success=False
        )
        recommender.adaptive_difficulty.update(updated_session["difficulty"], success=False)
    except Exception as e:
        print(f"AI update error (abort): {e}")

    # golden_time_stats 테이블 업데이트 (실패)
    with get_cursor() as cur:
        cur.execute(
            """
            INSERT INTO golden_time_stats (user_id, hour, day_of_week, success_count, total_count)
            VALUES (%s, %s, %s, 0, 1)
            ON CONFLICT (user_id, hour, day_of_week)
            DO UPDATE SET
                total_count = golden_time_stats.total_count + 1,
                updated_at = NOW()
            """,
            (user_id, updated_session["start_hour"], updated_session["day_of_week"])
        )

        # adaptive_difficulty_history 추가
        cur.execute(
            """
            INSERT INTO adaptive_difficulty_history (user_id, difficulty, success, session_id)
            VALUES (%s, %s, %s, %s)
            """,
            (user_id, updated_session["difficulty"], False, request.session_id)
        )

    return SessionResponse(
        id=str(updated_session["id"]),
        user_id=str(updated_session["user_id"]),
        task_type=updated_session["task_type"],
        difficulty=updated_session["difficulty"],
        goal=updated_session["goal"],
        mode_plan=None,
        status=SessionStatus.ABORTED,
        abort_reason=request.abort_reason,
        total_focus_sec=request.total_focus_sec,
        total_break_sec=0,
        rounds_completed=request.rounds_completed,
        coin_reward=coin_reward,
        created_at=updated_session["created_at"],
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
    user_id = str(user["id"])

    query = """
        SELECT * FROM sessions
        WHERE user_id = %s AND status IS NOT NULL AND status != 'in_progress'
    """
    params = [user_id]

    if from_date:
        query += " AND created_at >= %s"
        params.append(from_date)

    if to_date:
        query += " AND created_at <= %s"
        params.append(to_date)

    query += " ORDER BY created_at DESC LIMIT %s"
    params.append(limit)

    with get_cursor() as cur:
        cur.execute(query, params)
        sessions = cur.fetchall()

    return [
        SessionResponse(
            id=str(s["id"]),
            user_id=str(s["user_id"]),
            task_type=s["task_type"],
            difficulty=s["difficulty"],
            goal=s["goal"],
            mode_plan=None,
            status=SessionStatus.COMPLETED if s["status"] == "completed" else SessionStatus.ABORTED,
            abort_reason=s.get("abort_reason"),
            total_focus_sec=s["total_focus_sec"],
            total_break_sec=s["total_break_sec"],
            rounds_completed=s["rounds_completed"],
            coin_reward=s["coin_reward"],
            created_at=s["created_at"],
        )
        for s in sessions
    ]


@router.get("/stats")
async def get_session_stats(user: dict = Depends(get_current_user)):
    """
    세션 통계 조회
    """
    user_id = str(user["id"])

    with get_cursor() as cur:
        # 전체 통계
        cur.execute(
            """
            SELECT
                COUNT(*) as total_sessions,
                SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed_sessions,
                SUM(total_focus_sec) as total_focus_sec,
                SUM(coin_reward) as total_coins
            FROM sessions
            WHERE user_id = %s AND status IN ('completed', 'aborted')
            """,
            (user_id,)
        )
        stats = cur.fetchone()

        # 최근 7일 통계
        cur.execute(
            """
            SELECT
                COUNT(*) as sessions_7d,
                SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed_7d
            FROM sessions
            WHERE user_id = %s
              AND status IN ('completed', 'aborted')
              AND created_at >= NOW() - INTERVAL '7 days'
            """,
            (user_id,)
        )
        recent = cur.fetchone()

    total = stats["total_sessions"] or 0
    completed = stats["completed_sessions"] or 0

    return {
        "total_sessions": total,
        "completed_sessions": completed,
        "completion_rate": round(completed / total, 2) if total > 0 else 0,
        "total_focus_minutes": (stats["total_focus_sec"] or 0) // 60,
        "total_coins": stats["total_coins"] or 0,
        "sessions_7d": recent["sessions_7d"] or 0,
        "completed_7d": recent["completed_7d"] or 0,
    }
