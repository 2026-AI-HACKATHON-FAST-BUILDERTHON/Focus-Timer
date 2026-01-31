"""
리포트 API 라우터
"""

from fastapi import APIRouter, Depends
from datetime import datetime, timedelta
from collections import defaultdict

from models.schemas import WeeklyReportResponse
from services.recommender_rules import generate_weekly_experiment
from routers.auth import get_current_user
from routers.sessions import sessions_db

router = APIRouter(prefix="/report", tags=["Report"])


@router.get("/weekly", response_model=WeeklyReportResponse)
async def get_weekly_report(
    user: dict = Depends(get_current_user),
):
    """
    주간 리포트

    - 총 집중 시간
    - 완주율
    - 시간대별 분석
    - AI 기반 실험 추천
    """
    user_id = user["user_id"]
    now = datetime.utcnow()
    week_ago = now - timedelta(days=7)

    # 최근 7일 세션 필터링
    weekly_sessions = [
        s for s in sessions_db.values()
        if s["user_id"] == user_id
        and s["status"] is not None
        and s["created_at"] >= week_ago
    ]

    # 기본 통계
    total_sessions = len(weekly_sessions)
    completed_sessions = sum(1 for s in weekly_sessions if s["status"] == "completed")
    total_focus_minutes = sum(s["total_focus_sec"] for s in weekly_sessions) // 60

    completion_rate = (
        completed_sessions / total_sessions if total_sessions > 0 else 0
    )

    # 중단 사유 분석
    abort_reasons = defaultdict(int)
    for s in weekly_sessions:
        if s.get("abort_reason"):
            abort_reasons[s["abort_reason"]] += 1

    most_common_reason = None
    if abort_reasons:
        most_common_reason = max(abort_reasons, key=abort_reasons.get)

    # 시간대별 완주율 분석
    hourly_stats = defaultdict(lambda: {"total": 0, "completed": 0})
    for s in weekly_sessions:
        hour = s.get("start_hour", 12)
        hourly_stats[hour]["total"] += 1
        if s["status"] == "completed":
            hourly_stats[hour]["completed"] += 1

    hourly_completion_rate = {
        hour: stats["completed"] / stats["total"]
        for hour, stats in hourly_stats.items()
        if stats["total"] > 0
    }

    best_focus_hour = None
    if hourly_completion_rate:
        best_focus_hour = max(hourly_completion_rate, key=hourly_completion_rate.get)

    # 일별 통계
    daily_stats = []
    for i in range(7):
        day = now - timedelta(days=6 - i)
        day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)

        day_sessions = [
            s for s in weekly_sessions
            if day_start <= s["created_at"] < day_end
        ]

        daily_stats.append({
            "date": day_start.strftime("%Y-%m-%d"),
            "day_name": ["월", "화", "수", "목", "금", "토", "일"][day_start.weekday()],
            "focus_minutes": sum(s["total_focus_sec"] for s in day_sessions) // 60,
            "sessions": len(day_sessions),
            "completed": sum(1 for s in day_sessions if s["status"] == "completed"),
        })

    # AI 실험 추천
    experiment_suggestion = generate_weekly_experiment(
        weekly_stats={"total_sessions": total_sessions, "completion_rate": completion_rate},
        abort_reasons=dict(abort_reasons),
        hourly_completion_rate=hourly_completion_rate,
    )

    return WeeklyReportResponse(
        total_focus_minutes=total_focus_minutes,
        total_sessions=total_sessions,
        completed_sessions=completed_sessions,
        completion_rate=round(completion_rate, 2),
        most_common_abort_reason=most_common_reason,
        best_focus_hour=best_focus_hour,
        experiment_suggestion=experiment_suggestion,
        daily_stats=daily_stats,
    )
