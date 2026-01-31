"""
AI 분석 대시보드 API 라우터 - Supabase DB 연동
- 골든타임 히트맵 데이터
- 페르소나 분석
- 트렌드 분석
- AI 인사이트 생성
- 레벨 시스템
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timedelta
from collections import defaultdict

from routers.auth import get_current_user
from database.connection import get_cursor
from data.personas import PersonaType, classify_user_persona, get_persona_profile

router = APIRouter(prefix="/analytics", tags=["Analytics"])


# ===============================
# Response Models
# ===============================

class HourlyHeatmapData(BaseModel):
    hour: int
    day: int  # 0=월, 6=일
    total_sessions: int
    completed_sessions: int
    completion_rate: float


class GoldenTimeHeatmapResponse(BaseModel):
    heatmap_data: List[HourlyHeatmapData]
    golden_hours: List[int]
    worst_hours: List[int]
    best_day: Optional[int]
    best_day_name: Optional[str]
    total_sessions_analyzed: int


class PersonaAnalysisResponse(BaseModel):
    persona_type: str
    persona_name: str
    persona_icon: str
    description: str
    strengths: List[str]
    weaknesses: List[str]
    tips: List[str]
    completion_rate: float
    avg_focus_minutes: float
    top_abort_reason: Optional[str]
    confidence: float


class TrendDataPoint(BaseModel):
    date: str
    day_name: str
    focus_minutes: int
    sessions: int
    completed: int
    completion_rate: float


class TrendAnalysisResponse(BaseModel):
    daily_data: List[TrendDataPoint]
    weekly_trend: str  # "improving", "stable", "declining"
    completion_rate_change: float
    focus_time_change: float
    streak_days: int
    best_streak: int


class AIInsight(BaseModel):
    type: str  # "success", "warning", "tip", "achievement"
    icon: str  # Bootstrap icon class
    title: str
    message: str
    priority: int  # 1=high, 2=medium, 3=low


class AIInsightsResponse(BaseModel):
    insights: List[AIInsight]
    summary: str
    generated_at: str


class LevelInfo(BaseModel):
    level: int
    level_name: str
    level_icon: str
    current_achievements: int
    next_level_threshold: int
    progress_percent: float
    total_achievements: int


# ===============================
# Level System
# ===============================

LEVEL_THRESHOLDS = [
    (0, "새싹", "bi-flower1"),
    (5, "초보자", "bi-flower2"),
    (15, "수련생", "bi-flower3"),
    (30, "집중러", "bi-star"),
    (50, "마스터", "bi-star-fill"),
]


def calculate_level(achievement_count: int) -> LevelInfo:
    """업적 개수로 레벨 계산"""
    current_level = 1
    current_name = "새싹"
    current_icon = "bi-flower1"
    next_threshold = 5

    for i, (threshold, name, icon) in enumerate(LEVEL_THRESHOLDS):
        if achievement_count >= threshold:
            current_level = i + 1
            current_name = name
            current_icon = icon
            if i + 1 < len(LEVEL_THRESHOLDS):
                next_threshold = LEVEL_THRESHOLDS[i + 1][0]
            else:
                next_threshold = threshold

    if current_level < len(LEVEL_THRESHOLDS):
        prev_threshold = LEVEL_THRESHOLDS[current_level - 1][0] if current_level > 1 else 0
        progress = (achievement_count - prev_threshold) / (next_threshold - prev_threshold) * 100
    else:
        progress = 100

    return LevelInfo(
        level=current_level,
        level_name=current_name,
        level_icon=current_icon,
        current_achievements=achievement_count,
        next_level_threshold=next_threshold,
        progress_percent=min(100, round(progress, 1)),
        total_achievements=57,
    )


# ===============================
# Endpoints
# ===============================

@router.get("/golden-time-heatmap", response_model=GoldenTimeHeatmapResponse)
async def get_golden_time_heatmap(user: dict = Depends(get_current_user)):
    """골든타임 히트맵 데이터"""
    user_id = str(user["id"])

    with get_cursor() as cur:
        # 골든타임 통계 조회
        cur.execute("""
            SELECT hour, day_of_week, success_count, total_count
            FROM golden_time_stats
            WHERE user_id = %s
        """, (user_id,))
        stats = cur.fetchall()

        # 전체 세션 수
        cur.execute("""
            SELECT COUNT(*) as total FROM sessions
            WHERE user_id = %s AND status IN ('completed', 'aborted')
        """, (user_id,))
        total_result = cur.fetchone()
        total_sessions = total_result["total"] if total_result else 0

    # 히트맵 데이터 구성
    heatmap = {}
    for s in stats:
        key = (s["hour"], s["day_of_week"])
        heatmap[key] = {
            "total": s["total_count"],
            "completed": s["success_count"]
        }

    heatmap_data = []
    for hour in range(24):
        for day in range(7):
            data = heatmap.get((hour, day), {"total": 0, "completed": 0})
            rate = data["completed"] / data["total"] if data["total"] > 0 else 0
            heatmap_data.append(HourlyHeatmapData(
                hour=hour,
                day=day,
                total_sessions=data["total"],
                completed_sessions=data["completed"],
                completion_rate=round(rate, 2),
            ))

    # 시간대별 통계 집계
    hourly_rates = defaultdict(lambda: {"total": 0, "completed": 0})
    for s in stats:
        hourly_rates[s["hour"]]["total"] += s["total_count"]
        hourly_rates[s["hour"]]["completed"] += s["success_count"]

    # 골든 아워
    hour_completion = [
        (h, data["completed"] / data["total"] if data["total"] >= 3 else 0, data["total"])
        for h, data in hourly_rates.items()
    ]
    hour_completion.sort(key=lambda x: (x[1], x[2]), reverse=True)
    golden_hours = [h for h, rate, total in hour_completion[:3] if rate > 0]
    worst_hours = [h for h, rate, total in hour_completion if total >= 3][-3:]

    # 요일별 통계
    daily_rates = defaultdict(lambda: {"total": 0, "completed": 0})
    for s in stats:
        daily_rates[s["day_of_week"]]["total"] += s["total_count"]
        daily_rates[s["day_of_week"]]["completed"] += s["success_count"]

    best_day = None
    best_day_rate = 0
    day_names = ["월", "화", "수", "목", "금", "토", "일"]
    for day, data in daily_rates.items():
        if data["total"] >= 3:
            rate = data["completed"] / data["total"]
            if rate > best_day_rate:
                best_day_rate = rate
                best_day = day

    return GoldenTimeHeatmapResponse(
        heatmap_data=heatmap_data,
        golden_hours=golden_hours,
        worst_hours=worst_hours,
        best_day=best_day,
        best_day_name=day_names[best_day] if best_day is not None else None,
        total_sessions_analyzed=total_sessions,
    )


@router.get("/persona", response_model=PersonaAnalysisResponse)
async def get_persona_analysis(user: dict = Depends(get_current_user)):
    """페르소나 분석"""
    user_id = str(user["id"])

    with get_cursor() as cur:
        # 최근 세션 조회
        cur.execute("""
            SELECT status, total_focus_sec, abort_reason, start_hour
            FROM sessions
            WHERE user_id = %s AND status IN ('completed', 'aborted')
            ORDER BY created_at DESC
            LIMIT 20
        """, (user_id,))
        sessions = cur.fetchall()

    if len(sessions) < 5:
        return PersonaAnalysisResponse(
            persona_type="casual_learner",
            persona_name="캐주얼 러너",
            persona_icon="bi-person",
            description="아직 데이터가 부족해요. 더 많은 세션을 진행하면 정확한 분석이 가능합니다.",
            strengths=["시작이 반이에요!"],
            weaknesses=[],
            tips=["꾸준히 세션을 진행해보세요."],
            completion_rate=0.0,
            avg_focus_minutes=0.0,
            top_abort_reason=None,
            confidence=0.0,
        )

    # 통계 계산
    completion_rate = sum(1 for s in sessions if s["status"] == "completed") / len(sessions)
    focus_times = [s["total_focus_sec"] / 60 for s in sessions]
    avg_focus = sum(focus_times) / len(focus_times)

    # 중단 사유
    abort_counts = {}
    for s in sessions:
        if s["abort_reason"]:
            abort_counts[s["abort_reason"]] = abort_counts.get(s["abort_reason"], 0) + 1
    top_abort = max(abort_counts, key=abort_counts.get) if abort_counts else None

    # 활동 시간대
    active_hours = [s["start_hour"] for s in sessions]

    # 페르소나 분류
    persona_type = classify_user_persona(completion_rate, avg_focus, top_abort or "phone", active_hours)
    profile = get_persona_profile(persona_type)

    persona_icons = {
        PersonaType.MORNING_PERSON: "bi-sunrise",
        PersonaType.NIGHT_OWL: "bi-moon-stars",
        PersonaType.SPRINTER: "bi-lightning",
        PersonaType.MARATHONER: "bi-hourglass-split",
        PersonaType.DIGITAL_DETOXER: "bi-phone-vibrate",
        PersonaType.ENERGY_MANAGER: "bi-battery-charging",
        PersonaType.PERFECTIONIST: "bi-bullseye",
        PersonaType.EXPERIMENTER: "bi-compass",
        PersonaType.CASUAL_LEARNER: "bi-person",
    }

    confidence = min(1.0, len(sessions) / 20)

    return PersonaAnalysisResponse(
        persona_type=persona_type.value,
        persona_name=profile["name"],
        persona_icon=persona_icons.get(persona_type, "bi-person"),
        description=profile["description"],
        strengths=profile.get("strengths", []),
        weaknesses=profile.get("weaknesses", []),
        tips=profile.get("tips", []),
        completion_rate=round(completion_rate, 2),
        avg_focus_minutes=round(avg_focus, 1),
        top_abort_reason=top_abort,
        confidence=round(confidence, 2),
    )


@router.get("/trends", response_model=TrendAnalysisResponse)
async def get_trend_analysis(days: int = 14, user: dict = Depends(get_current_user)):
    """트렌드 분석"""
    user_id = str(user["id"])

    with get_cursor() as cur:
        # 일별 통계
        cur.execute("""
            SELECT
                DATE(created_at) as date,
                EXTRACT(DOW FROM created_at) as day_of_week,
                COUNT(*) as total,
                SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
                SUM(total_focus_sec) as focus_sec
            FROM sessions
            WHERE user_id = %s
              AND status IN ('completed', 'aborted')
              AND created_at >= NOW() - INTERVAL '%s days'
            GROUP BY DATE(created_at), EXTRACT(DOW FROM created_at)
            ORDER BY DATE(created_at)
        """, (user_id, days))
        daily_stats = cur.fetchall()

        # 이번 주 통계
        cur.execute("""
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
                SUM(total_focus_sec) as focus_sec
            FROM sessions
            WHERE user_id = %s
              AND status IN ('completed', 'aborted')
              AND created_at >= NOW() - INTERVAL '7 days'
        """, (user_id,))
        this_week = cur.fetchone()

        # 지난 주 통계
        cur.execute("""
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
                SUM(total_focus_sec) as focus_sec
            FROM sessions
            WHERE user_id = %s
              AND status IN ('completed', 'aborted')
              AND created_at >= NOW() - INTERVAL '14 days'
              AND created_at < NOW() - INTERVAL '7 days'
        """, (user_id,))
        last_week = cur.fetchone()

        # 연속 성공
        cur.execute("""
            SELECT status FROM sessions
            WHERE user_id = %s AND status IN ('completed', 'aborted')
            ORDER BY created_at DESC
            LIMIT 30
        """, (user_id,))
        recent_statuses = cur.fetchall()

    day_names = ["일", "월", "화", "수", "목", "금", "토"]
    daily_data = []
    for stat in daily_stats:
        total = stat["total"] or 0
        completed = stat["completed"] or 0
        rate = completed / total if total > 0 else 0
        daily_data.append(TrendDataPoint(
            date=stat["date"].strftime("%Y-%m-%d"),
            day_name=day_names[int(stat["day_of_week"])],
            focus_minutes=(stat["focus_sec"] or 0) // 60,
            sessions=total,
            completed=completed,
            completion_rate=round(rate, 2),
        ))

    # 완주율 변화
    this_total = this_week["total"] or 0
    this_completed = this_week["completed"] or 0
    this_week_rate = this_completed / this_total if this_total > 0 else 0

    last_total = last_week["total"] or 0
    last_completed = last_week["completed"] or 0
    last_week_rate = last_completed / last_total if last_total > 0 else 0

    rate_change = this_week_rate - last_week_rate

    # 집중 시간 변화
    this_focus = (this_week["focus_sec"] or 0) // 60
    last_focus = (last_week["focus_sec"] or 0) // 60
    focus_change = this_focus - last_focus

    # 트렌드
    if rate_change > 0.1:
        trend = "improving"
    elif rate_change < -0.1:
        trend = "declining"
    else:
        trend = "stable"

    # 연속 성공
    streak = 0
    for s in recent_statuses:
        if s["status"] == "completed":
            streak += 1
        else:
            break

    return TrendAnalysisResponse(
        daily_data=daily_data,
        weekly_trend=trend,
        completion_rate_change=round(rate_change, 2),
        focus_time_change=focus_change,
        streak_days=streak,
        best_streak=max(streak, user.get("best_streak_days", streak)),
    )


@router.get("/insights", response_model=AIInsightsResponse)
async def get_ai_insights(user: dict = Depends(get_current_user)):
    """AI 인사이트 생성"""
    user_id = str(user["id"])
    now = datetime.utcnow()

    with get_cursor() as cur:
        # 최근 7일 세션
        cur.execute("""
            SELECT status, abort_reason, start_hour, created_at
            FROM sessions
            WHERE user_id = %s
              AND status IN ('completed', 'aborted')
              AND created_at >= NOW() - INTERVAL '7 days'
            ORDER BY created_at DESC
        """, (user_id,))
        recent_sessions = cur.fetchall()

        # 골든타임 통계
        cur.execute("""
            SELECT hour, success_count, total_count
            FROM golden_time_stats
            WHERE user_id = %s AND total_count >= 3
            ORDER BY success_count::float / total_count DESC
            LIMIT 3
        """, (user_id,))
        golden_times = cur.fetchall()

    insights = []

    if len(recent_sessions) < 3:
        insights.append(AIInsight(
            type="tip",
            icon="bi-lightbulb",
            title="시작이 반이에요!",
            message="더 많은 세션을 진행하면 AI가 당신만을 위한 인사이트를 제공해드려요.",
            priority=1,
        ))
        return AIInsightsResponse(
            insights=insights,
            summary="세션을 더 진행해보세요!",
            generated_at=now.isoformat(),
        )

    # 완주율 분석
    completion_rate = sum(1 for s in recent_sessions if s["status"] == "completed") / len(recent_sessions)

    if completion_rate >= 0.8:
        insights.append(AIInsight(
            type="success",
            icon="bi-trophy",
            title="완벽한 한 주!",
            message=f"완주율 {int(completion_rate * 100)}%! 놀라운 집중력이에요.",
            priority=1,
        ))
    elif completion_rate >= 0.6:
        insights.append(AIInsight(
            type="tip",
            icon="bi-graph-up-arrow",
            title="좋은 흐름이에요",
            message=f"완주율 {int(completion_rate * 100)}%. 조금만 더 힘내면 80%를 넘길 수 있어요!",
            priority=2,
        ))
    else:
        insights.append(AIInsight(
            type="warning",
            icon="bi-exclamation-triangle",
            title="집중이 어려웠나요?",
            message="짧은 세션(15분)으로 시작해서 성공 경험을 쌓아보세요.",
            priority=1,
        ))

    # 골든타임
    if golden_times:
        best = golden_times[0]
        rate = best["success_count"] / best["total_count"] * 100
        insights.append(AIInsight(
            type="tip",
            icon="bi-clock",
            title=f"{best['hour']}시가 골든타임!",
            message=f"이 시간대 완주율 {rate:.0f}%! 중요한 작업은 이 시간에 시작해보세요.",
            priority=2,
        ))

    # 중단 사유
    abort_counts = defaultdict(int)
    for s in recent_sessions:
        if s["abort_reason"]:
            abort_counts[s["abort_reason"]] += 1

    if abort_counts:
        top_reason = max(abort_counts, key=abort_counts.get)
        reason_tips = {
            "phone": ("bi-phone-vibrate", "스마트폰 유혹", "집중 시작 전 스마트폰을 다른 방에 두어보세요."),
            "tired": ("bi-battery-half", "피로감", "짧은 세션 후 충분히 휴식하세요."),
            "anxious": ("bi-heart-pulse", "불안/스트레스", "시작 전 심호흡 3번!"),
            "bored": ("bi-emoji-neutral", "지루함", "작은 목표를 세우고 달성할 때마다 칭찬해주세요."),
            "environment": ("bi-volume-mute", "환경 방해", "조용한 장소나 노이즈캔슬링 이어폰을 사용해보세요."),
        }
        if top_reason in reason_tips:
            icon, title, message = reason_tips[top_reason]
            insights.append(AIInsight(
                type="warning",
                icon=icon,
                title=f"'{title}' 주의보",
                message=message,
                priority=2,
            ))

    # 연속 성공
    streak = 0
    for s in recent_sessions:
        if s["status"] == "completed":
            streak += 1
        else:
            break

    if streak >= 5:
        insights.append(AIInsight(
            type="achievement",
            icon="bi-fire",
            title=f"{streak}회 연속 성공!",
            message="대단해요! 불꽃 같은 집중력을 유지하고 있어요!",
            priority=1,
        ))

    insights.sort(key=lambda x: x.priority)

    return AIInsightsResponse(
        insights=insights[:5],
        summary=insights[0].message if insights else "꾸준히 세션을 진행해보세요!",
        generated_at=now.isoformat(),
    )


@router.get("/level", response_model=LevelInfo)
async def get_user_level(user: dict = Depends(get_current_user)):
    """사용자 레벨 정보"""
    user_id = str(user["id"])

    with get_cursor() as cur:
        cur.execute("""
            SELECT COUNT(*) as count FROM user_achievements
            WHERE user_id = %s AND is_unlocked = TRUE
        """, (user_id,))
        result = cur.fetchone()

    unlocked_count = result["count"] if result else 0
    return calculate_level(unlocked_count)


# ===============================
# 통합 대시보드 API (성능 최적화)
# ===============================

class DashboardResponse(BaseModel):
    level: LevelInfo
    heatmap: GoldenTimeHeatmapResponse
    persona: PersonaAnalysisResponse
    trends: TrendAnalysisResponse
    insights: AIInsightsResponse


@router.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard(user: dict = Depends(get_current_user)):
    """
    통합 대시보드 데이터 (5개 API를 1번 호출로 통합)
    - 레벨, 히트맵, 페르소나, 트렌드, 인사이트를 한 번에 반환
    """
    user_id = str(user["id"])
    now = datetime.utcnow()
    day_names = ["일", "월", "화", "수", "목", "금", "토"]
    day_names_kr = ["월", "화", "수", "목", "금", "토", "일"]

    with get_cursor() as cur:
        # 1. 레벨 (업적 개수)
        cur.execute("""
            SELECT COUNT(*) as count FROM user_achievements
            WHERE user_id = %s AND is_unlocked = TRUE
        """, (user_id,))
        unlocked_count = (cur.fetchone() or {}).get("count", 0)

        # 2. 골든타임 통계
        cur.execute("""
            SELECT hour, day_of_week, success_count, total_count
            FROM golden_time_stats
            WHERE user_id = %s
        """, (user_id,))
        golden_stats = cur.fetchall()

        cur.execute("""
            SELECT COUNT(*) as total FROM sessions
            WHERE user_id = %s AND status IN ('completed', 'aborted')
        """, (user_id,))
        total_sessions = (cur.fetchone() or {}).get("total", 0)

        # 3. 최근 세션 (페르소나 + 인사이트용)
        cur.execute("""
            SELECT status, total_focus_sec, abort_reason, start_hour, created_at
            FROM sessions
            WHERE user_id = %s AND status IN ('completed', 'aborted')
            ORDER BY created_at DESC
            LIMIT 20
        """, (user_id,))
        recent_sessions = cur.fetchall()

        # 4. 트렌드 - 일별 통계
        cur.execute("""
            SELECT
                DATE(created_at) as date,
                EXTRACT(DOW FROM created_at) as day_of_week,
                COUNT(*) as total,
                SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
                SUM(total_focus_sec) as focus_sec
            FROM sessions
            WHERE user_id = %s
              AND status IN ('completed', 'aborted')
              AND created_at >= NOW() - INTERVAL '14 days'
            GROUP BY DATE(created_at), EXTRACT(DOW FROM created_at)
            ORDER BY DATE(created_at)
        """, (user_id,))
        daily_stats = cur.fetchall()

        # 5. 이번 주 / 지난 주 비교
        cur.execute("""
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
                SUM(total_focus_sec) as focus_sec
            FROM sessions
            WHERE user_id = %s
              AND status IN ('completed', 'aborted')
              AND created_at >= NOW() - INTERVAL '7 days'
        """, (user_id,))
        this_week = cur.fetchone() or {}

        cur.execute("""
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
                SUM(total_focus_sec) as focus_sec
            FROM sessions
            WHERE user_id = %s
              AND status IN ('completed', 'aborted')
              AND created_at >= NOW() - INTERVAL '14 days'
              AND created_at < NOW() - INTERVAL '7 days'
        """, (user_id,))
        last_week = cur.fetchone() or {}

        # 6. 인사이트용 골든타임
        cur.execute("""
            SELECT hour, success_count, total_count
            FROM golden_time_stats
            WHERE user_id = %s AND total_count >= 3
            ORDER BY success_count::float / total_count DESC
            LIMIT 3
        """, (user_id,))
        golden_times = cur.fetchall()

    # === 레벨 계산 ===
    level_info = calculate_level(unlocked_count)

    # === 히트맵 계산 ===
    heatmap = {}
    for s in golden_stats:
        key = (s["hour"], s["day_of_week"])
        heatmap[key] = {"total": s["total_count"], "completed": s["success_count"]}

    heatmap_data = []
    for hour in range(24):
        for day in range(7):
            data = heatmap.get((hour, day), {"total": 0, "completed": 0})
            rate = data["completed"] / data["total"] if data["total"] > 0 else 0
            heatmap_data.append(HourlyHeatmapData(
                hour=hour, day=day,
                total_sessions=data["total"],
                completed_sessions=data["completed"],
                completion_rate=round(rate, 2),
            ))

    hourly_rates = defaultdict(lambda: {"total": 0, "completed": 0})
    for s in golden_stats:
        hourly_rates[s["hour"]]["total"] += s["total_count"]
        hourly_rates[s["hour"]]["completed"] += s["success_count"]

    hour_completion = [
        (h, data["completed"] / data["total"] if data["total"] >= 3 else 0, data["total"])
        for h, data in hourly_rates.items()
    ]
    hour_completion.sort(key=lambda x: (x[1], x[2]), reverse=True)
    golden_hours = [h for h, rate, total in hour_completion[:3] if rate > 0]
    worst_hours = [h for h, rate, total in hour_completion if total >= 3][-3:]

    daily_rates = defaultdict(lambda: {"total": 0, "completed": 0})
    for s in golden_stats:
        daily_rates[s["day_of_week"]]["total"] += s["total_count"]
        daily_rates[s["day_of_week"]]["completed"] += s["success_count"]

    best_day = None
    best_day_rate = 0
    for day, data in daily_rates.items():
        if data["total"] >= 3:
            rate = data["completed"] / data["total"]
            if rate > best_day_rate:
                best_day_rate = rate
                best_day = day

    heatmap_response = GoldenTimeHeatmapResponse(
        heatmap_data=heatmap_data,
        golden_hours=golden_hours,
        worst_hours=worst_hours,
        best_day=best_day,
        best_day_name=day_names_kr[best_day] if best_day is not None else None,
        total_sessions_analyzed=total_sessions,
    )

    # === 페르소나 계산 ===
    if len(recent_sessions) < 5:
        persona_response = PersonaAnalysisResponse(
            persona_type="casual_learner",
            persona_name="캐주얼 러너",
            persona_icon="bi-person",
            description="아직 데이터가 부족해요. 더 많은 세션을 진행하면 정확한 분석이 가능합니다.",
            strengths=["시작이 반이에요!"],
            weaknesses=[],
            tips=["꾸준히 세션을 진행해보세요."],
            completion_rate=0.0,
            avg_focus_minutes=0.0,
            top_abort_reason=None,
            confidence=0.0,
        )
    else:
        completion_rate = sum(1 for s in recent_sessions if s["status"] == "completed") / len(recent_sessions)
        focus_times = [s["total_focus_sec"] / 60 for s in recent_sessions]
        avg_focus = sum(focus_times) / len(focus_times)

        abort_counts = {}
        for s in recent_sessions:
            if s["abort_reason"]:
                abort_counts[s["abort_reason"]] = abort_counts.get(s["abort_reason"], 0) + 1
        top_abort = max(abort_counts, key=abort_counts.get) if abort_counts else None

        active_hours = [s["start_hour"] for s in recent_sessions]
        persona_type = classify_user_persona(completion_rate, avg_focus, top_abort or "phone", active_hours)
        profile = get_persona_profile(persona_type)

        persona_icons = {
            PersonaType.MORNING_PERSON: "bi-sunrise",
            PersonaType.NIGHT_OWL: "bi-moon-stars",
            PersonaType.SPRINTER: "bi-lightning",
            PersonaType.MARATHONER: "bi-hourglass-split",
            PersonaType.DIGITAL_DETOXER: "bi-phone-vibrate",
            PersonaType.ENERGY_MANAGER: "bi-battery-charging",
            PersonaType.PERFECTIONIST: "bi-bullseye",
            PersonaType.EXPERIMENTER: "bi-compass",
            PersonaType.CASUAL_LEARNER: "bi-person",
        }

        persona_response = PersonaAnalysisResponse(
            persona_type=persona_type.value,
            persona_name=profile["name"],
            persona_icon=persona_icons.get(persona_type, "bi-person"),
            description=profile["description"],
            strengths=profile.get("strengths", []),
            weaknesses=profile.get("weaknesses", []),
            tips=profile.get("tips", []),
            completion_rate=round(completion_rate, 2),
            avg_focus_minutes=round(avg_focus, 1),
            top_abort_reason=top_abort,
            confidence=round(min(1.0, len(recent_sessions) / 20), 2),
        )

    # === 트렌드 계산 ===
    trend_daily_data = []
    for stat in daily_stats:
        total = stat["total"] or 0
        completed = stat["completed"] or 0
        rate = completed / total if total > 0 else 0
        trend_daily_data.append(TrendDataPoint(
            date=stat["date"].strftime("%Y-%m-%d"),
            day_name=day_names[int(stat["day_of_week"])],
            focus_minutes=(stat["focus_sec"] or 0) // 60,
            sessions=total,
            completed=completed,
            completion_rate=round(rate, 2),
        ))

    this_total = this_week.get("total") or 0
    this_completed = this_week.get("completed") or 0
    this_week_rate = this_completed / this_total if this_total > 0 else 0

    last_total = last_week.get("total") or 0
    last_completed = last_week.get("completed") or 0
    last_week_rate = last_completed / last_total if last_total > 0 else 0

    rate_change = this_week_rate - last_week_rate
    this_focus = (this_week.get("focus_sec") or 0) // 60
    last_focus = (last_week.get("focus_sec") or 0) // 60

    if rate_change > 0.1:
        trend = "improving"
    elif rate_change < -0.1:
        trend = "declining"
    else:
        trend = "stable"

    streak = 0
    for s in recent_sessions:
        if s["status"] == "completed":
            streak += 1
        else:
            break

    trends_response = TrendAnalysisResponse(
        daily_data=trend_daily_data,
        weekly_trend=trend,
        completion_rate_change=round(rate_change, 2),
        focus_time_change=this_focus - last_focus,
        streak_days=streak,
        best_streak=max(streak, user.get("best_streak_days", streak)),
    )

    # === 인사이트 계산 ===
    insights = []
    if len(recent_sessions) < 3:
        insights.append(AIInsight(
            type="tip", icon="bi-lightbulb", title="시작이 반이에요!",
            message="더 많은 세션을 진행하면 AI가 당신만을 위한 인사이트를 제공해드려요.",
            priority=1,
        ))
    else:
        comp_rate = sum(1 for s in recent_sessions if s["status"] == "completed") / len(recent_sessions)

        if comp_rate >= 0.8:
            insights.append(AIInsight(
                type="success", icon="bi-trophy", title="완벽한 한 주!",
                message=f"완주율 {int(comp_rate * 100)}%! 놀라운 집중력이에요.",
                priority=1,
            ))
        elif comp_rate >= 0.6:
            insights.append(AIInsight(
                type="tip", icon="bi-graph-up-arrow", title="좋은 흐름이에요",
                message=f"완주율 {int(comp_rate * 100)}%. 조금만 더 힘내면 80%를 넘길 수 있어요!",
                priority=2,
            ))
        else:
            insights.append(AIInsight(
                type="warning", icon="bi-exclamation-triangle", title="집중이 어려웠나요?",
                message="짧은 세션(15분)으로 시작해서 성공 경험을 쌓아보세요.",
                priority=1,
            ))

        if golden_times:
            best = golden_times[0]
            rate = best["success_count"] / best["total_count"] * 100
            insights.append(AIInsight(
                type="tip", icon="bi-clock", title=f"{best['hour']}시가 골든타임!",
                message=f"이 시간대 완주율 {rate:.0f}%! 중요한 작업은 이 시간에 시작해보세요.",
                priority=2,
            ))

        abort_counts = defaultdict(int)
        for s in recent_sessions:
            if s["abort_reason"]:
                abort_counts[s["abort_reason"]] += 1

        if abort_counts:
            top_reason = max(abort_counts, key=abort_counts.get)
            reason_tips = {
                "phone": ("bi-phone-vibrate", "스마트폰 유혹", "집중 시작 전 스마트폰을 다른 방에 두어보세요."),
                "tired": ("bi-battery-half", "피로감", "짧은 세션 후 충분히 휴식하세요."),
                "anxious": ("bi-heart-pulse", "불안/스트레스", "시작 전 심호흡 3번!"),
                "bored": ("bi-emoji-neutral", "지루함", "작은 목표를 세우고 달성할 때마다 칭찬해주세요."),
                "environment": ("bi-volume-mute", "환경 방해", "조용한 장소나 노이즈캔슬링 이어폰을 사용해보세요."),
            }
            if top_reason in reason_tips:
                icon, title, message = reason_tips[top_reason]
                insights.append(AIInsight(
                    type="warning", icon=icon, title=f"'{title}' 주의보",
                    message=message, priority=2,
                ))

        if streak >= 5:
            insights.append(AIInsight(
                type="achievement", icon="bi-fire", title=f"{streak}회 연속 성공!",
                message="대단해요! 불꽃 같은 집중력을 유지하고 있어요!",
                priority=1,
            ))

    insights.sort(key=lambda x: x.priority)

    insights_response = AIInsightsResponse(
        insights=insights[:5],
        summary=insights[0].message if insights else "꾸준히 세션을 진행해보세요!",
        generated_at=now.isoformat(),
    )

    return DashboardResponse(
        level=level_info,
        heatmap=heatmap_response,
        persona=persona_response,
        trends=trends_response,
        insights=insights_response,
    )
