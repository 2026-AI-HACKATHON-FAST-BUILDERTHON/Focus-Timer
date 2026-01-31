"""
AI 분석 대시보드 API 라우터
- 골든타임 히트맵 데이터
- 페르소나 분석
- 트렌드 분석
- AI 인사이트 생성
- 레벨 시스템
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from collections import defaultdict

from routers.auth import get_current_user
from routers.sessions import sessions_db
from routers.achievements import user_achievements_db
from data.personas import PersonaType, classify_user_persona, get_persona_profile, PERSONA_PROFILES

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
    completion_rate_change: float  # 이번주 vs 저번주
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
    (0, "새싹", "bi-flower1"),      # Lv1: 0개
    (5, "초보자", "bi-flower2"),    # Lv2: 5개
    (15, "수련생", "bi-flower3"),   # Lv3: 15개
    (30, "집중러", "bi-star"),      # Lv4: 30개
    (50, "마스터", "bi-star-fill"), # Lv5: 50개
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

    # 진행률 계산
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
        total_achievements=57,  # 전체 업적 수
    )


# ===============================
# Endpoints
# ===============================

@router.get("/golden-time-heatmap", response_model=GoldenTimeHeatmapResponse)
async def get_golden_time_heatmap(
    user: dict = Depends(get_current_user),
):
    """
    골든타임 히트맵 데이터
    - 시간대 x 요일 매트릭스
    - 완주율 기반 색상 강도
    """
    user_id = user["user_id"]

    # 전체 세션 수집
    user_sessions = [
        s for s in sessions_db.values()
        if s["user_id"] == user_id and s["status"] is not None
    ]

    # 시간대 x 요일 통계
    heatmap = defaultdict(lambda: {"total": 0, "completed": 0})

    for s in user_sessions:
        hour = s.get("start_hour", 12)
        day = s.get("day_of_week", 0)
        key = (hour, day)
        heatmap[key]["total"] += 1
        if s["status"] == "completed":
            heatmap[key]["completed"] += 1

    # 히트맵 데이터 구성
    heatmap_data = []
    for hour in range(24):
        for day in range(7):
            stats = heatmap.get((hour, day), {"total": 0, "completed": 0})
            rate = stats["completed"] / stats["total"] if stats["total"] > 0 else 0
            heatmap_data.append(HourlyHeatmapData(
                hour=hour,
                day=day,
                total_sessions=stats["total"],
                completed_sessions=stats["completed"],
                completion_rate=round(rate, 2),
            ))

    # 시간대별 전체 완주율
    hourly_rates = defaultdict(lambda: {"total": 0, "completed": 0})
    for s in user_sessions:
        hour = s.get("start_hour", 12)
        hourly_rates[hour]["total"] += 1
        if s["status"] == "completed":
            hourly_rates[hour]["completed"] += 1

    # 골든 아워 (상위 3개)
    hour_completion = [
        (h, stats["completed"] / stats["total"] if stats["total"] >= 3 else 0, stats["total"])
        for h, stats in hourly_rates.items()
    ]
    hour_completion.sort(key=lambda x: (x[1], x[2]), reverse=True)
    golden_hours = [h for h, rate, total in hour_completion[:3] if rate > 0]

    # 최악 시간대 (하위 3개)
    worst_hours = [h for h, rate, total in hour_completion if total >= 3][-3:]

    # 요일별 완주율
    daily_rates = defaultdict(lambda: {"total": 0, "completed": 0})
    for s in user_sessions:
        day = s.get("day_of_week", 0)
        daily_rates[day]["total"] += 1
        if s["status"] == "completed":
            daily_rates[day]["completed"] += 1

    best_day = None
    best_day_rate = 0
    day_names = ["월", "화", "수", "목", "금", "토", "일"]
    for day, stats in daily_rates.items():
        if stats["total"] >= 3:
            rate = stats["completed"] / stats["total"]
            if rate > best_day_rate:
                best_day_rate = rate
                best_day = day

    return GoldenTimeHeatmapResponse(
        heatmap_data=heatmap_data,
        golden_hours=golden_hours,
        worst_hours=worst_hours,
        best_day=best_day,
        best_day_name=day_names[best_day] if best_day is not None else None,
        total_sessions_analyzed=len(user_sessions),
    )


@router.get("/persona", response_model=PersonaAnalysisResponse)
async def get_persona_analysis(
    user: dict = Depends(get_current_user),
):
    """
    페르소나 분석
    - 사용자 행동 패턴 기반 분류
    - 강점/약점/팁 제공
    """
    user_id = user["user_id"]

    # 세션 데이터 수집
    user_sessions = [
        s for s in sessions_db.values()
        if s["user_id"] == user_id and s["status"] is not None
    ]

    if len(user_sessions) < 5:
        # 기본 페르소나
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

    recent = user_sessions[:20]

    # 통계 계산
    completion_rate = sum(1 for s in recent if s["status"] == "completed") / len(recent)
    focus_times = [s.get("total_focus_sec", 0) / 60 for s in recent]
    avg_focus = sum(focus_times) / len(focus_times)

    # 중단 사유 분석
    abort_counts = {}
    for s in recent:
        reason = s.get("abort_reason")
        if reason:
            abort_counts[reason] = abort_counts.get(reason, 0) + 1
    top_abort = max(abort_counts, key=abort_counts.get) if abort_counts else None

    # 활동 시간대
    active_hours = [s.get("start_hour", 12) for s in recent]

    # 페르소나 분류
    persona_type = classify_user_persona(completion_rate, avg_focus, top_abort or "phone", active_hours)
    profile = get_persona_profile(persona_type)

    # 페르소나별 아이콘
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

    # 신뢰도 계산 (세션 수 기반)
    confidence = min(1.0, len(user_sessions) / 20)

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
async def get_trend_analysis(
    days: int = 14,
    user: dict = Depends(get_current_user),
):
    """
    트렌드 분석
    - 일별 집중 시간, 완주율 변화
    - 주간 비교
    """
    user_id = user["user_id"]
    now = datetime.utcnow()

    # 지정 기간 세션
    user_sessions = [
        s for s in sessions_db.values()
        if s["user_id"] == user_id
        and s["status"] is not None
        and s["created_at"] >= now - timedelta(days=days)
    ]

    # 일별 통계
    day_names = ["월", "화", "수", "목", "금", "토", "일"]
    daily_data = []

    for i in range(days):
        day = now - timedelta(days=days - 1 - i)
        day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)

        day_sessions = [
            s for s in user_sessions
            if day_start <= s["created_at"] < day_end
        ]

        focus_minutes = sum(s["total_focus_sec"] for s in day_sessions) // 60
        completed = sum(1 for s in day_sessions if s["status"] == "completed")
        total = len(day_sessions)
        rate = completed / total if total > 0 else 0

        daily_data.append(TrendDataPoint(
            date=day_start.strftime("%Y-%m-%d"),
            day_name=day_names[day_start.weekday()],
            focus_minutes=focus_minutes,
            sessions=total,
            completed=completed,
            completion_rate=round(rate, 2),
        ))

    # 이번 주 vs 지난 주 비교
    this_week_start = now - timedelta(days=7)
    last_week_start = now - timedelta(days=14)

    this_week_sessions = [s for s in user_sessions if s["created_at"] >= this_week_start]
    last_week_sessions = [
        s for s in sessions_db.values()
        if s["user_id"] == user_id
        and s["status"] is not None
        and last_week_start <= s["created_at"] < this_week_start
    ]

    # 완주율 변화
    this_week_rate = (
        sum(1 for s in this_week_sessions if s["status"] == "completed") / len(this_week_sessions)
        if this_week_sessions else 0
    )
    last_week_rate = (
        sum(1 for s in last_week_sessions if s["status"] == "completed") / len(last_week_sessions)
        if last_week_sessions else 0
    )
    rate_change = this_week_rate - last_week_rate

    # 집중 시간 변화
    this_week_focus = sum(s["total_focus_sec"] for s in this_week_sessions) // 60
    last_week_focus = sum(s["total_focus_sec"] for s in last_week_sessions) // 60
    focus_change = this_week_focus - last_week_focus

    # 트렌드 판단
    if rate_change > 0.1:
        trend = "improving"
    elif rate_change < -0.1:
        trend = "declining"
    else:
        trend = "stable"

    # 연속 성공 계산
    all_sessions = sorted(user_sessions, key=lambda s: s["created_at"], reverse=True)
    streak = 0
    for s in all_sessions:
        if s["status"] == "completed":
            streak += 1
        else:
            break

    # 최고 연속 기록 (간단히 현재 스트릭 * 1.5로 추정)
    best_streak = max(streak, int(streak * 1.5))

    return TrendAnalysisResponse(
        daily_data=daily_data,
        weekly_trend=trend,
        completion_rate_change=round(rate_change, 2),
        focus_time_change=focus_change,
        streak_days=streak,
        best_streak=best_streak,
    )


@router.get("/insights", response_model=AIInsightsResponse)
async def get_ai_insights(
    user: dict = Depends(get_current_user),
):
    """
    AI 인사이트 생성
    - 개인화된 분석 메시지
    - 실행 가능한 팁 제공
    """
    user_id = user["user_id"]
    now = datetime.utcnow()

    # 세션 데이터
    user_sessions = [
        s for s in sessions_db.values()
        if s["user_id"] == user_id and s["status"] is not None
    ]

    recent_sessions = [
        s for s in user_sessions
        if s["created_at"] >= now - timedelta(days=7)
    ]

    insights = []

    # 데이터 부족 시
    if len(user_sessions) < 3:
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
    if recent_sessions:
        completion_rate = sum(1 for s in recent_sessions if s["status"] == "completed") / len(recent_sessions)

        if completion_rate >= 0.8:
            insights.append(AIInsight(
                type="success",
                icon="bi-trophy",
                title="완벽한 한 주!",
                message=f"완주율 {int(completion_rate * 100)}%! 놀라운 집중력이에요. 이 페이스를 유지해보세요.",
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

    # 골든타임 분석
    hour_stats = defaultdict(lambda: {"total": 0, "completed": 0})
    for s in user_sessions:
        hour = s.get("start_hour", 12)
        hour_stats[hour]["total"] += 1
        if s["status"] == "completed":
            hour_stats[hour]["completed"] += 1

    golden_hours = []
    for hour, stats in hour_stats.items():
        if stats["total"] >= 3:
            rate = stats["completed"] / stats["total"]
            if rate >= 0.7:
                golden_hours.append((hour, rate))

    if golden_hours:
        golden_hours.sort(key=lambda x: x[1], reverse=True)
        best_hour = golden_hours[0][0]
        insights.append(AIInsight(
            type="tip",
            icon="bi-clock",
            title=f"{best_hour}시가 골든타임!",
            message=f"이 시간대 완주율이 가장 높아요. 중요한 작업은 이 시간에 시작해보세요.",
            priority=2,
        ))

    # 중단 사유 분석
    abort_counts = defaultdict(int)
    for s in recent_sessions:
        if s.get("abort_reason"):
            abort_counts[s["abort_reason"]] += 1

    if abort_counts:
        top_reason = max(abort_counts, key=abort_counts.get)
        reason_tips = {
            "phone": ("bi-phone-vibrate", "스마트폰 유혹", "집중 시작 전 스마트폰을 다른 방에 두어보세요."),
            "tired": ("bi-battery-half", "피로감", "짧은 세션 후 충분히 휴식하세요. 2분 스트레칭도 좋아요."),
            "anxious": ("bi-heart-pulse", "불안/스트레스", "시작 전 심호흡 3번! 마음을 차분히 해보세요."),
            "bored": ("bi-emoji-neutral", "지루함", "작은 목표를 세우고 달성할 때마다 스스로 칭찬해주세요."),
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

    # 연속 성공 격려
    sorted_sessions = sorted(recent_sessions, key=lambda s: s["created_at"], reverse=True)
    streak = 0
    for s in sorted_sessions:
        if s["status"] == "completed":
            streak += 1
        else:
            break

    if streak >= 5:
        insights.append(AIInsight(
            type="achievement",
            icon="bi-fire",
            title=f"{streak}일 연속 성공!",
            message="대단해요! 불꽃 같은 집중력을 유지하고 있어요!",
            priority=1,
        ))
    elif streak >= 3:
        insights.append(AIInsight(
            type="success",
            icon="bi-star",
            title=f"{streak}일 연속 성공 중",
            message="좋은 흐름이에요! 5일 연속을 목표로 해봐요.",
            priority=2,
        ))

    # 정렬 (우선순위 순)
    insights.sort(key=lambda x: x.priority)

    # 요약 생성
    if insights:
        top_insight = insights[0]
        summary = top_insight.message
    else:
        summary = "꾸준히 세션을 진행해보세요!"

    return AIInsightsResponse(
        insights=insights[:5],  # 최대 5개
        summary=summary,
        generated_at=now.isoformat(),
    )


@router.get("/level", response_model=LevelInfo)
async def get_user_level(
    user: dict = Depends(get_current_user),
):
    """
    사용자 레벨 정보
    - 업적 달성 개수 기반
    """
    user_id = user["user_id"]

    # 업적 수 가져오기 (user_achievements_db에서 직접 조회)
    unlocked_count = len(user_achievements_db.get(user_id, {}))

    return calculate_level(unlocked_count)
