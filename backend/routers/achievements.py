"""
도전 과제 API 라우터 - Supabase DB 연동
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
from database.connection import get_cursor

router = APIRouter(prefix="/achievements", tags=["Achievements"])


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


def get_user_sessions(user_id: str) -> List[Dict]:
    """DB에서 사용자 세션 조회"""
    with get_cursor() as cur:
        cur.execute(
            """
            SELECT id, user_id, task_type, difficulty, goal, status,
                   total_focus_sec, total_break_sec, rounds_completed,
                   coin_reward, start_hour, day_of_week, abort_reason,
                   created_at, completed_at
            FROM sessions
            WHERE user_id = %s AND status IN ('completed', 'aborted')
            ORDER BY created_at DESC
            """,
            (user_id,)
        )
        return [dict(s) for s in cur.fetchall()]


def get_user_unlocked_achievements(user_id: str) -> Dict[str, str]:
    """DB에서 사용자가 획득한 도전 과제 조회"""
    with get_cursor() as cur:
        cur.execute(
            """
            SELECT achievement_id, unlocked_at
            FROM user_achievements
            WHERE user_id = %s
            """,
            (user_id,)
        )
        results = cur.fetchall()

    return {r["achievement_id"]: r["unlocked_at"].isoformat() if r["unlocked_at"] else None for r in results}


def get_user_stats(user_id: str) -> Dict:
    """사용자 통계 계산"""
    user_sessions = get_user_sessions(user_id)

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
            "unlocked_achievements": 0,
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

    # 주말 세션 (day_of_week: 5=토, 6=일)
    weekend = sum(1 for s in completed if s.get("day_of_week", 0) in [5, 6])

    # 가장 긴 집중 세션
    longest = max((s.get("total_focus_sec", 0) for s in completed), default=0) / 60

    # 사용자 코인 조회
    with get_cursor() as cur:
        cur.execute("SELECT coin_balance, current_streak_days FROM users WHERE id = %s", (user_id,))
        user_info = cur.fetchone()

    total_coins = user_info["coin_balance"] if user_info else 0
    streak = user_info["current_streak_days"] if user_info else 0

    # 획득한 도전 과제 수
    unlocked_count = len(get_user_unlocked_achievements(user_id))

    return {
        "total_sessions": len(user_sessions),
        "completed_sessions": len(completed),
        "total_focus_minutes": total_focus,
        "current_streak": streak,
        "max_streak": streak,
        "total_coins": total_coins,
        "sessions_by_task": sessions_by_task,
        "sessions_by_hour": sessions_by_hour,
        "longest_focus_session": longest,
        "perfect_days": 0,
        "weekend_sessions": weekend,
        "early_morning_sessions": early_morning,
        "night_sessions": night,
        "midnight_sessions": midnight,
        "consecutive_completions": 0,
        "micro_routines_completed": 0,
        "ai_recommendations_followed": 0,
        "unlocked_achievements": unlocked_count,
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
    user_id = str(user["id"])
    user_unlocked = get_user_unlocked_achievements(user_id)
    user_stats = get_user_stats(user_id)

    achievements = []
    total_coins = 0

    for ach in ACHIEVEMENTS.values():
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
    user_id = str(user["id"])
    user_unlocked = get_user_unlocked_achievements(user_id)

    # 카테고리별 통계
    categories = []
    for cat in AchievementCategory:
        cat_achievements = [a for a in ACHIEVEMENTS.values() if a.category == cat]
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
        rarity_achievements = [a for a in ACHIEVEMENTS.values() if a.rarity == rarity]
        rarity_unlocked = [a for a in rarity_achievements if a.id in user_unlocked]
        rarity_dist[rarity.value] = {
            "total": len(rarity_achievements),
            "unlocked": len(rarity_unlocked),
        }

    # 최근 획득
    recent = sorted(
        [(ach_id, time) for ach_id, time in user_unlocked.items()],
        key=lambda x: x[1] if x[1] else "",
        reverse=True
    )[:5]

    recent_unlocks = []
    for ach_id, unlocked_at in recent:
        ach = next((a for a in ACHIEVEMENTS.values() if a.id == ach_id), None)
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
        next((a.coin_reward for a in ACHIEVEMENTS.values() if a.id == ach_id), 0)
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
    ach = next((a for a in ACHIEVEMENTS.values() if a.id == achievement_id), None)
    if not ach:
        raise HTTPException(status_code=404, detail="Achievement not found")

    user_id = str(user["id"])
    user_unlocked = get_user_unlocked_achievements(user_id)
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
    user_id = str(user["id"])
    user_stats = get_user_stats(user_id)
    user_sessions = get_user_sessions(user_id)

    # 최근 세션
    latest_session = user_sessions[0] if user_sessions else None

    # 도전 과제 매니저
    manager = AchievementManager()

    # 이미 획득한 도전 과제
    existing = set(get_user_unlocked_achievements(user_id).keys())
    manager.user_achievements = existing.copy()

    # 새 도전 과제 확인
    new_achievements = manager.check_and_update(
        user_id=user_id,
        session_data=latest_session or {},
        user_stats=user_stats,
    )

    # 새로 획득한 도전 과제 DB에 저장
    if new_achievements:
        now = datetime.now()
        with get_cursor() as cur:
            for ach in new_achievements:
                cur.execute(
                    """
                    INSERT INTO user_achievements (user_id, achievement_id, unlocked_at)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (user_id, achievement_id) DO NOTHING
                    """,
                    (user_id, ach.id, now)
                )

            # 코인 추가
            coins_earned = sum(a.coin_reward for a in new_achievements)
            cur.execute(
                """
                UPDATE users SET
                    coin_balance = coin_balance + %s,
                    total_coins_earned = total_coins_earned + %s
                WHERE id = %s
                """,
                (coins_earned, coins_earned, user_id)
            )

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
