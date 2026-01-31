"""
도전 과제 API 라우터
- 55개 도전 과제 시스템
- 진행률 추적
- 획득 기록
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Optional
from datetime import datetime
from pydantic import BaseModel

from services.achievements import (
    AchievementManager,
    AchievementCategory,
    AchievementRarity,
    ACHIEVEMENTS,
)
from routers.auth import get_current_user
from routers.sessions import sessions_db

router = APIRouter(prefix="/achievements", tags=["Achievements"])

# In-memory 저장소 (실제로는 DB 사용)
user_achievements_db: Dict[str, Dict] = {}  # user_id -> {achievement_id: unlocked_at}
user_stats_db: Dict[str, Dict] = {}  # user_id -> stats


class AchievementResponse(BaseModel):
    id: str
    name: str
    description: str
    category: str
    rarity: str
    icon: str
    coin_reward: int
    unlocked: bool
    unlocked_at: Optional[str] = None
    progress: Optional[float] = None


class AchievementListResponse(BaseModel):
    total: int
    unlocked: int
    achievements: List[AchievementResponse]
    total_coins_earned: int


class CategoryStatsResponse(BaseModel):
    category: str
    total: int
    unlocked: int
    percentage: float


class AchievementSummaryResponse(BaseModel):
    total_achievements: int
    unlocked_count: int
    unlock_percentage: float
    total_coins_earned: int
    categories: List[CategoryStatsResponse]
    recent_unlocks: List[AchievementResponse]
    rarity_distribution: Dict[str, Dict[str, int]]


def get_user_stats(user_id: str) -> Dict:
    """사용자 통계 계산"""
    user_sessions = [
        s for s in sessions_db.values()
        if s.get("user_id") == user_id
    ]

    if not user_sessions:
        return {
            "total_sessions": 0,
            "completed_sessions": 0,
            "total_focus_minutes": 0,
            "current_streak": 0,
            "max_streak": 0,
            "total_coins": 0,
            "sessions_by_task": {},
            "sessions_by_hour": {},
            "longest_focus_session": 0,
            "perfect_days": 0,
            "weekend_sessions": 0,
            "early_morning_sessions": 0,
            "night_sessions": 0,
            "midnight_sessions": 0,
            "consecutive_completions": 0,
            "micro_routines_completed": 0,
            "ai_recommendations_followed": 0,
        }

    completed = [s for s in user_sessions if s.get("status") == "completed"]
    total_focus = sum(s.get("total_focus_sec", 0) for s in completed) / 60

    # 시간대별 세션
    sessions_by_hour = {}
    for s in completed:
        hour = s.get("start_hour", 12)
        sessions_by_hour[hour] = sessions_by_hour.get(hour, 0) + 1

    # 과제 유형별 세션
    sessions_by_task = {}
    for s in user_sessions:
        task = s.get("task_type", "reading")
        sessions_by_task[task] = sessions_by_task.get(task, 0) + 1

    # 특수 시간대 세션
    early_morning = sum(1 for s in completed if 5 <= s.get("start_hour", 12) < 7)
    night = sum(1 for s in completed if 22 <= s.get("start_hour", 12) <= 23)
    midnight = sum(1 for s in completed if 0 <= s.get("start_hour", 12) < 3)

    # 주말 세션
    weekend = sum(1 for s in completed if s.get("is_weekend", False))

    # 가장 긴 집중 세션
    longest = max((s.get("total_focus_sec", 0) for s in completed), default=0) / 60

    # 연속 완료 (streak 계산은 날짜 기반으로 해야 함)
    streak = 0
    if completed:
        sorted_sessions = sorted(completed, key=lambda x: x.get("created_at", ""), reverse=True)
        # 간단한 streak 계산 (실제로는 날짜 비교 필요)
        streak = min(len(sorted_sessions), 30)

    return {
        "total_sessions": len(user_sessions),
        "completed_sessions": len(completed),
        "total_focus_minutes": total_focus,
        "current_streak": streak,
        "max_streak": streak,
        "total_coins": user_stats_db.get(user_id, {}).get("total_coins", 0),
        "sessions_by_task": sessions_by_task,
        "sessions_by_hour": sessions_by_hour,
        "longest_focus_session": longest,
        "perfect_days": 0,  # 계산 필요
        "weekend_sessions": weekend,
        "early_morning_sessions": early_morning,
        "night_sessions": night,
        "midnight_sessions": midnight,
        "consecutive_completions": 0,  # 계산 필요
        "micro_routines_completed": 0,
        "ai_recommendations_followed": 0,
        "unlocked_achievements": len(user_achievements_db.get(user_id, {})),
    }


@router.get("", response_model=AchievementListResponse)
async def get_achievements(
    category: Optional[str] = None,
    show_hidden: bool = False,
    user: dict = Depends(get_current_user),
):
    """
    전체 도전 과제 목록 조회

    - category: 카테고리 필터 (focus, streak, time, milestone, special, hidden)
    - show_hidden: 숨겨진 도전 과제 표시 여부
    """
    user_id = user["user_id"]
    user_unlocked = user_achievements_db.get(user_id, {})
    user_stats = get_user_stats(user_id)

    achievements = []
    total_coins = 0

    for ach in ACHIEVEMENTS:
        # 카테고리 필터
        if category and ach.category.value != category:
            continue

        # 숨겨진 도전 과제 처리
        if ach.hidden and not show_hidden:
            if ach.id not in user_unlocked:
                continue

        unlocked = ach.id in user_unlocked
        unlocked_at = user_unlocked.get(ach.id)

        if unlocked:
            total_coins += ach.coin_reward

        # 진행률 계산
        progress = calculate_progress(ach, user_stats)

        achievements.append(AchievementResponse(
            id=ach.id,
            name=ach.name,
            description=ach.description if unlocked or not ach.hidden else "???",
            category=ach.category.value,
            rarity=ach.rarity.value,
            icon=ach.icon,
            coin_reward=ach.coin_reward,
            unlocked=unlocked,
            unlocked_at=unlocked_at,
            progress=progress if not unlocked else 1.0,
        ))

    return AchievementListResponse(
        total=len(achievements),
        unlocked=len(user_unlocked),
        achievements=achievements,
        total_coins_earned=total_coins,
    )


@router.get("/summary", response_model=AchievementSummaryResponse)
async def get_achievement_summary(
    user: dict = Depends(get_current_user),
):
    """
    도전 과제 요약 통계
    """
    user_id = user["user_id"]
    user_unlocked = user_achievements_db.get(user_id, {})

    # 카테고리별 통계
    categories = []
    for cat in AchievementCategory:
        cat_achievements = [a for a in ACHIEVEMENTS if a.category == cat]
        cat_unlocked = [a for a in cat_achievements if a.id in user_unlocked]

        categories.append(CategoryStatsResponse(
            category=cat.value,
            total=len(cat_achievements),
            unlocked=len(cat_unlocked),
            percentage=len(cat_unlocked) / len(cat_achievements) * 100 if cat_achievements else 0,
        ))

    # 희귀도별 분포
    rarity_dist = {}
    for rarity in AchievementRarity:
        rarity_achievements = [a for a in ACHIEVEMENTS if a.rarity == rarity]
        rarity_unlocked = [a for a in rarity_achievements if a.id in user_unlocked]
        rarity_dist[rarity.value] = {
            "total": len(rarity_achievements),
            "unlocked": len(rarity_unlocked),
        }

    # 최근 획득
    recent = sorted(
        [(ach_id, time) for ach_id, time in user_unlocked.items()],
        key=lambda x: x[1],
        reverse=True
    )[:5]

    recent_unlocks = []
    for ach_id, unlocked_at in recent:
        ach = next((a for a in ACHIEVEMENTS if a.id == ach_id), None)
        if ach:
            recent_unlocks.append(AchievementResponse(
                id=ach.id,
                name=ach.name,
                description=ach.description,
                category=ach.category.value,
                rarity=ach.rarity.value,
                icon=ach.icon,
                coin_reward=ach.coin_reward,
                unlocked=True,
                unlocked_at=unlocked_at,
            ))

    # 총 코인
    total_coins = sum(
        next((a.coin_reward for a in ACHIEVEMENTS if a.id == ach_id), 0)
        for ach_id in user_unlocked
    )

    return AchievementSummaryResponse(
        total_achievements=len(ACHIEVEMENTS),
        unlocked_count=len(user_unlocked),
        unlock_percentage=len(user_unlocked) / len(ACHIEVEMENTS) * 100,
        total_coins_earned=total_coins,
        categories=categories,
        recent_unlocks=recent_unlocks,
        rarity_distribution=rarity_dist,
    )


@router.get("/{achievement_id}", response_model=AchievementResponse)
async def get_achievement(
    achievement_id: str,
    user: dict = Depends(get_current_user),
):
    """
    특정 도전 과제 상세 조회
    """
    ach = next((a for a in ACHIEVEMENTS if a.id == achievement_id), None)
    if not ach:
        raise HTTPException(status_code=404, detail="Achievement not found")

    user_id = user["user_id"]
    user_unlocked = user_achievements_db.get(user_id, {})
    user_stats = get_user_stats(user_id)

    unlocked = ach.id in user_unlocked

    return AchievementResponse(
        id=ach.id,
        name=ach.name,
        description=ach.description if unlocked or not ach.hidden else "???",
        category=ach.category.value,
        rarity=ach.rarity.value,
        icon=ach.icon,
        coin_reward=ach.coin_reward,
        unlocked=unlocked,
        unlocked_at=user_unlocked.get(ach.id),
        progress=calculate_progress(ach, user_stats) if not unlocked else 1.0,
    )


@router.post("/check")
async def check_achievements(
    user: dict = Depends(get_current_user),
):
    """
    새로운 도전 과제 달성 확인

    세션 완료 후 호출하여 새로 달성한 과제를 확인
    """
    user_id = user["user_id"]
    user_stats = get_user_stats(user_id)

    # 최근 세션
    user_sessions = [
        s for s in sessions_db.values()
        if s.get("user_id") == user_id
    ]
    latest_session = max(user_sessions, key=lambda x: x.get("created_at", "")) if user_sessions else None

    # 도전 과제 매니저
    manager = AchievementManager()

    # 이미 획득한 도전 과제
    existing = set(user_achievements_db.get(user_id, {}).keys())
    manager.user_achievements = existing.copy()

    # 새 도전 과제 확인
    new_achievements = manager.check_and_update(
        user_id=user_id,
        session_data=latest_session or {},
        user_stats=user_stats,
    )

    # 새로 획득한 도전 과제 저장
    if new_achievements:
        if user_id not in user_achievements_db:
            user_achievements_db[user_id] = {}

        now = datetime.now().isoformat()
        for ach in new_achievements:
            user_achievements_db[user_id][ach.id] = now

        # 코인 추가
        coins_earned = sum(a.coin_reward for a in new_achievements)
        if user_id not in user_stats_db:
            user_stats_db[user_id] = {"total_coins": 0}
        user_stats_db[user_id]["total_coins"] += coins_earned

    return {
        "new_achievements": [
            {
                "id": a.id,
                "name": a.name,
                "description": a.description,
                "rarity": a.rarity.value,
                "icon": a.icon,
                "coin_reward": a.coin_reward,
            }
            for a in new_achievements
        ],
        "total_new": len(new_achievements),
        "coins_earned": sum(a.coin_reward for a in new_achievements),
    }


def calculate_progress(ach, user_stats: Dict) -> float:
    """도전 과제 진행률 계산"""
    req = ach.requirement

    if "count" in req:
        target = req["count"]

        if ach.category == AchievementCategory.FOCUS:
            current = user_stats.get("completed_sessions", 0)
        elif ach.category == AchievementCategory.STREAK:
            if "weekend" in ach.id:
                current = user_stats.get("weekend_sessions", 0)
            else:
                current = user_stats.get("current_streak", 0)
        elif ach.category == AchievementCategory.MILESTONE:
            if "coin" in ach.id:
                current = user_stats.get("total_coins", 0)
            elif "achievement" in ach.id:
                current = user_stats.get("unlocked_achievements", 0)
            else:
                current = user_stats.get("completed_sessions", 0)
        else:
            current = user_stats.get("completed_sessions", 0)

        return min(1.0, current / target) if target > 0 else 0.0

    if "minutes" in req:
        target = req["minutes"]
        current = user_stats.get("total_focus_minutes", 0)
        return min(1.0, current / target) if target > 0 else 0.0

    if "days" in req:
        target = req["days"]
        current = user_stats.get("current_streak", 0)
        return min(1.0, current / target) if target > 0 else 0.0

    return 0.0
