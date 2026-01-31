"""
도전 과제 시스템
- 55개 이상의 다양한 도전 과제
- 카테고리별 분류
- 진행률 추적 및 보상
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime, timedelta
import json
import os


class AchievementCategory(str, Enum):
    FOCUS = "focus"           # 집중력
    STREAK = "streak"         # 연속 달성
    TIME = "time"             # 시간대
    MILESTONE = "milestone"   # 마일스톤
    SPECIAL = "special"       # 특별
    HIDDEN = "hidden"         # 숨겨진


class AchievementRarity(str, Enum):
    COMMON = "common"         # 흔함 (동)
    UNCOMMON = "uncommon"     # 드묾 (은)
    RARE = "rare"             # 레어 (금)
    EPIC = "epic"             # 에픽 (보라)
    LEGENDARY = "legendary"   # 전설 (주황)


@dataclass
class Achievement:
    """도전 과제 정의"""
    id: str
    name: str
    description: str
    category: AchievementCategory
    rarity: AchievementRarity
    icon: str  # Bootstrap icon class
    coin_reward: int
    requirement: Dict  # 달성 조건
    hidden: bool = False  # 숨겨진 업적 여부


@dataclass
class UserAchievement:
    """사용자 도전 과제 상태"""
    achievement_id: str
    progress: float  # 0.0 ~ 1.0
    current_value: int
    target_value: int
    unlocked: bool
    unlocked_at: Optional[str]


# ============================================================
# 전체 도전 과제 정의 (55개)
# ============================================================

ACHIEVEMENTS: Dict[str, Achievement] = {}


def _add(achievement: Achievement):
    ACHIEVEMENTS[achievement.id] = achievement


# ------------------------------------------------------------
# 카테고리 1: 집중력 (Focus) - 15개
# ------------------------------------------------------------

_add(Achievement(
    id="focus_first_session",
    name="첫 발걸음",
    description="첫 번째 집중 세션을 완료하세요",
    category=AchievementCategory.FOCUS,
    rarity=AchievementRarity.COMMON,
    icon="bi-star",
    coin_reward=10,
    requirement={"type": "total_sessions", "value": 1},
))

_add(Achievement(
    id="focus_10_sessions",
    name="집중 입문자",
    description="10개의 세션을 완료하세요",
    category=AchievementCategory.FOCUS,
    rarity=AchievementRarity.COMMON,
    icon="bi-bullseye",
    coin_reward=30,
    requirement={"type": "total_sessions", "value": 10},
))

_add(Achievement(
    id="focus_50_sessions",
    name="집중 수련생",
    description="50개의 세션을 완료하세요",
    category=AchievementCategory.FOCUS,
    rarity=AchievementRarity.UNCOMMON,
    icon="bi-fire",
    coin_reward=100,
    requirement={"type": "total_sessions", "value": 50},
))

_add(Achievement(
    id="focus_100_sessions",
    name="집중 마스터",
    description="100개의 세션을 완료하세요",
    category=AchievementCategory.FOCUS,
    rarity=AchievementRarity.RARE,
    icon="bi-award",
    coin_reward=300,
    requirement={"type": "total_sessions", "value": 100},
))

_add(Achievement(
    id="focus_500_sessions",
    name="집중의 달인",
    description="500개의 세션을 완료하세요",
    category=AchievementCategory.FOCUS,
    rarity=AchievementRarity.EPIC,
    icon="bi-trophy",
    coin_reward=1000,
    requirement={"type": "total_sessions", "value": 500},
))

_add(Achievement(
    id="focus_30min",
    name="롱런 챌린저",
    description="30분 이상 집중 세션을 완료하세요",
    category=AchievementCategory.FOCUS,
    rarity=AchievementRarity.UNCOMMON,
    icon="bi-hourglass-split",
    coin_reward=50,
    requirement={"type": "single_focus_minutes", "value": 30},
))

_add(Achievement(
    id="focus_45min",
    name="마라톤 러너",
    description="45분 이상 집중 세션을 완료하세요",
    category=AchievementCategory.FOCUS,
    rarity=AchievementRarity.RARE,
    icon="bi-stopwatch",
    coin_reward=150,
    requirement={"type": "single_focus_minutes", "value": 45},
))

_add(Achievement(
    id="focus_60min",
    name="울트라 포커스",
    description="60분 이상 집중 세션을 완료하세요",
    category=AchievementCategory.FOCUS,
    rarity=AchievementRarity.EPIC,
    icon="bi-lightning-charge",
    coin_reward=300,
    requirement={"type": "single_focus_minutes", "value": 60},
))

_add(Achievement(
    id="focus_total_1h",
    name="1시간 누적",
    description="총 1시간 집중하세요",
    category=AchievementCategory.FOCUS,
    rarity=AchievementRarity.COMMON,
    icon="bi-clock",
    coin_reward=20,
    requirement={"type": "total_focus_minutes", "value": 60},
))

_add(Achievement(
    id="focus_total_10h",
    name="10시간 누적",
    description="총 10시간 집중하세요",
    category=AchievementCategory.FOCUS,
    rarity=AchievementRarity.UNCOMMON,
    icon="bi-clock-history",
    coin_reward=100,
    requirement={"type": "total_focus_minutes", "value": 600},
))

_add(Achievement(
    id="focus_total_50h",
    name="50시간 누적",
    description="총 50시간 집중하세요",
    category=AchievementCategory.FOCUS,
    rarity=AchievementRarity.RARE,
    icon="bi-gem",
    coin_reward=500,
    requirement={"type": "total_focus_minutes", "value": 3000},
))

_add(Achievement(
    id="focus_total_100h",
    name="100시간 마스터",
    description="총 100시간 집중하세요",
    category=AchievementCategory.FOCUS,
    rarity=AchievementRarity.EPIC,
    icon="bi-diamond",
    coin_reward=1500,
    requirement={"type": "total_focus_minutes", "value": 6000},
))

_add(Achievement(
    id="focus_no_abort",
    name="완벽주의자",
    description="중단 없이 5개 세션 연속 완료",
    category=AchievementCategory.FOCUS,
    rarity=AchievementRarity.UNCOMMON,
    icon="bi-check-circle",
    coin_reward=80,
    requirement={"type": "consecutive_complete", "value": 5},
))

_add(Achievement(
    id="focus_no_abort_10",
    name="철벽 집중",
    description="중단 없이 10개 세션 연속 완료",
    category=AchievementCategory.FOCUS,
    rarity=AchievementRarity.RARE,
    icon="bi-shield-check",
    coin_reward=200,
    requirement={"type": "consecutive_complete", "value": 10},
))

_add(Achievement(
    id="focus_high_difficulty",
    name="어려운 길을 택하다",
    description="난이도 5 세션을 완료하세요",
    category=AchievementCategory.FOCUS,
    rarity=AchievementRarity.UNCOMMON,
    icon="bi-exclamation-diamond",
    coin_reward=100,
    requirement={"type": "difficulty_complete", "value": 5},
))

# ------------------------------------------------------------
# 카테고리 2: 연속 달성 (Streak) - 10개
# ------------------------------------------------------------

_add(Achievement(
    id="streak_3days",
    name="3일 연속",
    description="3일 연속으로 세션을 완료하세요",
    category=AchievementCategory.STREAK,
    rarity=AchievementRarity.COMMON,
    icon="bi-calendar-check",
    coin_reward=30,
    requirement={"type": "streak_days", "value": 3},
))

_add(Achievement(
    id="streak_7days",
    name="일주일 전사",
    description="7일 연속으로 세션을 완료하세요",
    category=AchievementCategory.STREAK,
    rarity=AchievementRarity.UNCOMMON,
    icon="bi-calendar-week",
    coin_reward=100,
    requirement={"type": "streak_days", "value": 7},
))

_add(Achievement(
    id="streak_14days",
    name="2주 챌린저",
    description="14일 연속으로 세션을 완료하세요",
    category=AchievementCategory.STREAK,
    rarity=AchievementRarity.RARE,
    icon="bi-calendar2-week",
    coin_reward=250,
    requirement={"type": "streak_days", "value": 14},
))

_add(Achievement(
    id="streak_30days",
    name="한 달의 기적",
    description="30일 연속으로 세션을 완료하세요",
    category=AchievementCategory.STREAK,
    rarity=AchievementRarity.EPIC,
    icon="bi-calendar-month",
    coin_reward=500,
    requirement={"type": "streak_days", "value": 30},
))

_add(Achievement(
    id="streak_60days",
    name="60일 레전드",
    description="60일 연속으로 세션을 완료하세요",
    category=AchievementCategory.STREAK,
    rarity=AchievementRarity.LEGENDARY,
    icon="bi-calendar-heart",
    coin_reward=1500,
    requirement={"type": "streak_days", "value": 60},
))

_add(Achievement(
    id="streak_100days",
    name="100일 신화",
    description="100일 연속으로 세션을 완료하세요",
    category=AchievementCategory.STREAK,
    rarity=AchievementRarity.LEGENDARY,
    icon="bi-stars",
    coin_reward=3000,
    requirement={"type": "streak_days", "value": 100},
))

_add(Achievement(
    id="streak_weekend",
    name="주말도 열공",
    description="주말에 세션을 완료하세요",
    category=AchievementCategory.STREAK,
    rarity=AchievementRarity.COMMON,
    icon="bi-calendar-event",
    coin_reward=25,
    requirement={"type": "weekend_session", "value": 1},
))

_add(Achievement(
    id="streak_10_weekends",
    name="주말 마스터",
    description="10번의 주말에 세션을 완료하세요",
    category=AchievementCategory.STREAK,
    rarity=AchievementRarity.UNCOMMON,
    icon="bi-calendar-fill",
    coin_reward=150,
    requirement={"type": "weekend_sessions", "value": 10},
))

_add(Achievement(
    id="streak_daily_3",
    name="하루 3세션",
    description="하루에 3개 이상 세션 완료",
    category=AchievementCategory.STREAK,
    rarity=AchievementRarity.UNCOMMON,
    icon="bi-lightning",
    coin_reward=60,
    requirement={"type": "daily_sessions", "value": 3},
))

_add(Achievement(
    id="streak_daily_5",
    name="하루 5세션",
    description="하루에 5개 이상 세션 완료",
    category=AchievementCategory.STREAK,
    rarity=AchievementRarity.RARE,
    icon="bi-lightning-charge-fill",
    coin_reward=150,
    requirement={"type": "daily_sessions", "value": 5},
))

# ------------------------------------------------------------
# 카테고리 3: 시간대 (Time) - 8개
# ------------------------------------------------------------

_add(Achievement(
    id="time_early_bird",
    name="얼리버드",
    description="오전 6시 이전에 세션을 완료하세요",
    category=AchievementCategory.TIME,
    rarity=AchievementRarity.UNCOMMON,
    icon="bi-sunrise",
    coin_reward=50,
    requirement={"type": "hour_before", "value": 6},
))

_add(Achievement(
    id="time_morning_glory",
    name="모닝 글로리",
    description="오전에 10개 세션 완료",
    category=AchievementCategory.TIME,
    rarity=AchievementRarity.UNCOMMON,
    icon="bi-sun",
    coin_reward=80,
    requirement={"type": "morning_sessions", "value": 10},
))

_add(Achievement(
    id="time_night_owl",
    name="밤올빼미",
    description="밤 11시 이후에 세션을 완료하세요",
    category=AchievementCategory.TIME,
    rarity=AchievementRarity.UNCOMMON,
    icon="bi-moon-stars",
    coin_reward=50,
    requirement={"type": "hour_after", "value": 23},
))

_add(Achievement(
    id="time_midnight",
    name="미드나잇 워리어",
    description="자정~새벽 3시 사이에 세션 완료",
    category=AchievementCategory.TIME,
    rarity=AchievementRarity.RARE,
    icon="bi-moon-fill",
    coin_reward=100,
    requirement={"type": "midnight_session", "value": 1},
))

_add(Achievement(
    id="time_all_hours",
    name="24시간 집중러",
    description="모든 시간대에서 세션을 완료하세요 (6구간)",
    category=AchievementCategory.TIME,
    rarity=AchievementRarity.EPIC,
    icon="bi-clock-fill",
    coin_reward=500,
    requirement={"type": "all_time_slots", "value": 6},
))

_add(Achievement(
    id="time_lunch_break",
    name="점심 시간 활용",
    description="점심 시간(12-13시)에 세션 완료",
    category=AchievementCategory.TIME,
    rarity=AchievementRarity.COMMON,
    icon="bi-cup-hot",
    coin_reward=30,
    requirement={"type": "lunch_session", "value": 1},
))

_add(Achievement(
    id="time_golden_hour",
    name="골든 아워",
    description="AI가 추천한 골든타임에 10회 세션 완료",
    category=AchievementCategory.TIME,
    rarity=AchievementRarity.RARE,
    icon="bi-brightness-high",
    coin_reward=200,
    requirement={"type": "golden_hour_sessions", "value": 10},
))

_add(Achievement(
    id="time_consistent",
    name="일정한 시간에",
    description="같은 시간대에 20회 세션 완료",
    category=AchievementCategory.TIME,
    rarity=AchievementRarity.RARE,
    icon="bi-alarm",
    coin_reward=180,
    requirement={"type": "consistent_time", "value": 20},
))

# ------------------------------------------------------------
# 카테고리 4: 마일스톤 (Milestone) - 12개
# ------------------------------------------------------------

_add(Achievement(
    id="milestone_coins_100",
    name="100 코인 달성",
    description="100 코인을 획득하세요",
    category=AchievementCategory.MILESTONE,
    rarity=AchievementRarity.COMMON,
    icon="bi-coin",
    coin_reward=10,
    requirement={"type": "total_coins", "value": 100},
))

_add(Achievement(
    id="milestone_coins_500",
    name="500 코인 달성",
    description="500 코인을 획득하세요",
    category=AchievementCategory.MILESTONE,
    rarity=AchievementRarity.UNCOMMON,
    icon="bi-cash-coin",
    coin_reward=50,
    requirement={"type": "total_coins", "value": 500},
))

_add(Achievement(
    id="milestone_coins_1000",
    name="1000 코인 클럽",
    description="1000 코인을 획득하세요",
    category=AchievementCategory.MILESTONE,
    rarity=AchievementRarity.RARE,
    icon="bi-currency-exchange",
    coin_reward=100,
    requirement={"type": "total_coins", "value": 1000},
))

_add(Achievement(
    id="milestone_coins_5000",
    name="5000 코인 마스터",
    description="5000 코인을 획득하세요",
    category=AchievementCategory.MILESTONE,
    rarity=AchievementRarity.EPIC,
    icon="bi-piggy-bank",
    coin_reward=500,
    requirement={"type": "total_coins", "value": 5000},
))

_add(Achievement(
    id="milestone_reading",
    name="독서광",
    description="학습/독서 세션 20개 완료",
    category=AchievementCategory.MILESTONE,
    rarity=AchievementRarity.UNCOMMON,
    icon="bi-book",
    coin_reward=80,
    requirement={"type": "task_type_count", "task_type": "reading", "value": 20},
))

_add(Achievement(
    id="milestone_practice",
    name="실습 마니아",
    description="실습/연습 세션 20개 완료",
    category=AchievementCategory.MILESTONE,
    rarity=AchievementRarity.UNCOMMON,
    icon="bi-code-slash",
    coin_reward=80,
    requirement={"type": "task_type_count", "task_type": "practice", "value": 20},
))

_add(Achievement(
    id="milestone_creation",
    name="창작 아티스트",
    description="창작/작업 세션 20개 완료",
    category=AchievementCategory.MILESTONE,
    rarity=AchievementRarity.UNCOMMON,
    icon="bi-palette",
    coin_reward=80,
    requirement={"type": "task_type_count", "task_type": "creation", "value": 20},
))

_add(Achievement(
    id="milestone_routine",
    name="루틴의 힘",
    description="일상/반복 세션 20개 완료",
    category=AchievementCategory.MILESTONE,
    rarity=AchievementRarity.UNCOMMON,
    icon="bi-list-check",
    coin_reward=80,
    requirement={"type": "task_type_count", "task_type": "routine", "value": 20},
))

_add(Achievement(
    id="milestone_all_types",
    name="만능 집중러",
    description="모든 과제 유형 각각 10개 이상 완료",
    category=AchievementCategory.MILESTONE,
    rarity=AchievementRarity.RARE,
    icon="bi-grid-3x3-gap",
    coin_reward=300,
    requirement={"type": "all_task_types", "value": 10},
))

_add(Achievement(
    id="milestone_achievements_10",
    name="도전 수집가",
    description="10개의 도전 과제 달성",
    category=AchievementCategory.MILESTONE,
    rarity=AchievementRarity.UNCOMMON,
    icon="bi-collection",
    coin_reward=100,
    requirement={"type": "achievement_count", "value": 10},
))

_add(Achievement(
    id="milestone_achievements_25",
    name="도전 마니아",
    description="25개의 도전 과제 달성",
    category=AchievementCategory.MILESTONE,
    rarity=AchievementRarity.RARE,
    icon="bi-collection-fill",
    coin_reward=300,
    requirement={"type": "achievement_count", "value": 25},
))

_add(Achievement(
    id="milestone_achievements_50",
    name="도전 정복자",
    description="50개의 도전 과제 달성",
    category=AchievementCategory.MILESTONE,
    rarity=AchievementRarity.LEGENDARY,
    icon="bi-stars",
    coin_reward=1000,
    requirement={"type": "achievement_count", "value": 50},
))

# ------------------------------------------------------------
# 카테고리 5: 특별 (Special) - 7개
# ------------------------------------------------------------

_add(Achievement(
    id="special_comeback",
    name="컴백 챔피언",
    description="7일 이상 쉬고 다시 시작",
    category=AchievementCategory.SPECIAL,
    rarity=AchievementRarity.UNCOMMON,
    icon="bi-arrow-repeat",
    coin_reward=100,
    requirement={"type": "comeback_days", "value": 7},
))

_add(Achievement(
    id="special_improvement",
    name="성장 중",
    description="완주율이 20% 이상 향상",
    category=AchievementCategory.SPECIAL,
    rarity=AchievementRarity.RARE,
    icon="bi-graph-up-arrow",
    coin_reward=200,
    requirement={"type": "improvement_rate", "value": 20},
))

_add(Achievement(
    id="special_ai_follower",
    name="AI 조언자",
    description="AI 추천을 10회 적용",
    category=AchievementCategory.SPECIAL,
    rarity=AchievementRarity.UNCOMMON,
    icon="bi-robot",
    coin_reward=80,
    requirement={"type": "ai_recommendation_used", "value": 10},
))

_add(Achievement(
    id="special_micro_routine",
    name="마이크로 루틴 마스터",
    description="마이크로 루틴으로 5회 완료",
    category=AchievementCategory.SPECIAL,
    rarity=AchievementRarity.UNCOMMON,
    icon="bi-list-task",
    coin_reward=100,
    requirement={"type": "micro_routine_success", "value": 5},
))

_add(Achievement(
    id="special_no_phone",
    name="스마트폰 정복",
    description="스마트폰 유혹 없이 10회 연속 완료",
    category=AchievementCategory.SPECIAL,
    rarity=AchievementRarity.RARE,
    icon="bi-phone-x",
    coin_reward=200,
    requirement={"type": "no_phone_abort", "value": 10},
))

_add(Achievement(
    id="special_variety",
    name="다양성의 왕",
    description="다양한 집중 시간(10/15/20/25/30분)으로 각각 완료",
    category=AchievementCategory.SPECIAL,
    rarity=AchievementRarity.RARE,
    icon="bi-shuffle",
    coin_reward=180,
    requirement={"type": "focus_variety", "value": 5},
))

_add(Achievement(
    id="special_new_year",
    name="새해 결심",
    description="1월 1일에 세션 완료",
    category=AchievementCategory.SPECIAL,
    rarity=AchievementRarity.EPIC,
    icon="bi-balloon",
    coin_reward=300,
    requirement={"type": "special_date", "date": "01-01"},
))

# ------------------------------------------------------------
# 카테고리 6: 숨겨진 (Hidden) - 5개
# ------------------------------------------------------------

_add(Achievement(
    id="hidden_first_abort",
    name="실패도 경험",
    description="첫 중단을 경험하세요",
    category=AchievementCategory.HIDDEN,
    rarity=AchievementRarity.COMMON,
    icon="bi-emoji-frown",
    coin_reward=10,
    requirement={"type": "first_abort", "value": 1},
    hidden=True,
))

_add(Achievement(
    id="hidden_3am_club",
    name="새벽 3시 클럽",
    description="새벽 3시에 세션 완료",
    category=AchievementCategory.HIDDEN,
    rarity=AchievementRarity.EPIC,
    icon="bi-moon",
    coin_reward=300,
    requirement={"type": "exact_hour", "value": 3},
    hidden=True,
))

_add(Achievement(
    id="hidden_420",
    name="420",
    description="4시 20분에 세션 시작",
    category=AchievementCategory.HIDDEN,
    rarity=AchievementRarity.EPIC,
    icon="bi-flower1",
    coin_reward=420,
    requirement={"type": "exact_time", "hour": 4, "minute": 20},
    hidden=True,
))

_add(Achievement(
    id="hidden_palindrome",
    name="회문의 날",
    description="날짜가 회문인 날에 세션 완료 (예: 2024-04-20-24)",
    category=AchievementCategory.HIDDEN,
    rarity=AchievementRarity.LEGENDARY,
    icon="bi-symmetry-horizontal",
    coin_reward=500,
    requirement={"type": "palindrome_date", "value": 1},
    hidden=True,
))

_add(Achievement(
    id="hidden_lucky_7",
    name="럭키 세븐",
    description="7일, 7시, 7분에 7번째 세션 완료",
    category=AchievementCategory.HIDDEN,
    rarity=AchievementRarity.LEGENDARY,
    icon="bi-7-circle",
    coin_reward=777,
    requirement={"type": "lucky_7", "value": 1},
    hidden=True,
))


# ============================================================
# 도전 과제 관리 시스템
# ============================================================

class AchievementManager:
    """도전 과제 관리자"""

    def __init__(self, storage_path: str = "data/achievements"):
        self.storage_path = storage_path
        os.makedirs(storage_path, exist_ok=True)

    def get_user_file(self, user_id: str) -> str:
        return f"{self.storage_path}/user_{user_id}.json"

    def load_user_achievements(self, user_id: str) -> Dict[str, UserAchievement]:
        """사용자 도전 과제 상태 로드"""
        file_path = self.get_user_file(user_id)

        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return {
                    k: UserAchievement(**v) for k, v in data.items()
                }

        # 초기화
        return {
            ach_id: UserAchievement(
                achievement_id=ach_id,
                progress=0.0,
                current_value=0,
                target_value=ach.requirement.get("value", 1),
                unlocked=False,
                unlocked_at=None,
            )
            for ach_id, ach in ACHIEVEMENTS.items()
        }

    def save_user_achievements(self, user_id: str, achievements: Dict[str, UserAchievement]):
        """사용자 도전 과제 상태 저장"""
        file_path = self.get_user_file(user_id)

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(
                {k: asdict(v) for k, v in achievements.items()},
                f,
                ensure_ascii=False,
                indent=2,
            )

    def check_and_update(
        self,
        user_id: str,
        session_data: Dict,
        user_stats: Dict,
    ) -> List[Achievement]:
        """
        세션 완료 후 도전 과제 체크 및 업데이트

        Returns:
            새로 달성한 도전 과제 목록
        """
        user_achievements = self.load_user_achievements(user_id)
        newly_unlocked = []

        for ach_id, ach in ACHIEVEMENTS.items():
            user_ach = user_achievements[ach_id]

            if user_ach.unlocked:
                continue

            # 조건 체크
            requirement = ach.requirement
            req_type = requirement.get("type")
            target = requirement.get("value", 1)

            current = self._evaluate_requirement(
                req_type, target, requirement, session_data, user_stats
            )

            user_ach.current_value = current
            user_ach.target_value = target
            user_ach.progress = min(1.0, current / target if target > 0 else 0)

            if current >= target:
                user_ach.unlocked = True
                user_ach.unlocked_at = datetime.now().isoformat()
                newly_unlocked.append(ach)

        self.save_user_achievements(user_id, user_achievements)
        return newly_unlocked

    def _evaluate_requirement(
        self,
        req_type: str,
        target: int,
        requirement: Dict,
        session: Dict,
        stats: Dict,
    ) -> int:
        """조건 평가"""
        if req_type == "total_sessions":
            return stats.get("total_sessions", 0)

        elif req_type == "single_focus_minutes":
            return session.get("total_focus_sec", 0) // 60

        elif req_type == "total_focus_minutes":
            return stats.get("total_focus_minutes", 0)

        elif req_type == "consecutive_complete":
            return stats.get("consecutive_complete", 0)

        elif req_type == "streak_days":
            return stats.get("streak_days", 0)

        elif req_type == "difficulty_complete":
            if session.get("status") == "completed" and session.get("difficulty") >= target:
                return target
            return 0

        elif req_type == "hour_before":
            hour = session.get("start_hour", 12)
            return target if hour < target and session.get("status") == "completed" else 0

        elif req_type == "hour_after":
            hour = session.get("start_hour", 12)
            return target if hour >= target and session.get("status") == "completed" else 0

        elif req_type == "total_coins":
            return stats.get("total_coins", 0)

        elif req_type == "weekend_session":
            day = session.get("day_of_week", 0)
            return 1 if day >= 5 and session.get("status") == "completed" else 0

        elif req_type == "daily_sessions":
            return stats.get("sessions_today", 0)

        elif req_type == "task_type_count":
            task_type = requirement.get("task_type")
            return stats.get(f"task_count_{task_type}", 0)

        elif req_type == "achievement_count":
            return stats.get("unlocked_achievements", 0)

        # 기타 조건들...
        return 0

    def get_all_achievements(self, include_hidden: bool = False) -> List[Dict]:
        """모든 도전 과제 목록"""
        result = []
        for ach in ACHIEVEMENTS.values():
            if ach.hidden and not include_hidden:
                continue
            result.append({
                "id": ach.id,
                "name": ach.name,
                "description": ach.description,
                "category": ach.category.value,
                "rarity": ach.rarity.value,
                "icon": ach.icon,
                "coin_reward": ach.coin_reward,
                "hidden": ach.hidden,
            })
        return result

    def get_user_progress(self, user_id: str) -> Dict:
        """사용자 도전 과제 진행 상황"""
        user_achievements = self.load_user_achievements(user_id)

        total = len([a for a in ACHIEVEMENTS.values() if not a.hidden])
        unlocked = sum(1 for ua in user_achievements.values() if ua.unlocked and not ACHIEVEMENTS[ua.achievement_id].hidden)

        by_category = {}
        for cat in AchievementCategory:
            cat_achs = [a for a in ACHIEVEMENTS.values() if a.category == cat and not a.hidden]
            cat_unlocked = sum(
                1 for a in cat_achs
                if user_achievements[a.id].unlocked
            )
            by_category[cat.value] = {
                "total": len(cat_achs),
                "unlocked": cat_unlocked,
                "progress": round(cat_unlocked / len(cat_achs) * 100, 1) if cat_achs else 0,
            }

        return {
            "total": total,
            "unlocked": unlocked,
            "progress_percent": round(unlocked / total * 100, 1) if total > 0 else 0,
            "by_category": by_category,
            "achievements": [
                {
                    **asdict(user_achievements[ach_id]),
                    "name": ach.name,
                    "description": ach.description if not ach.hidden or user_achievements[ach_id].unlocked else "???",
                    "icon": ach.icon,
                    "rarity": ach.rarity.value,
                    "coin_reward": ach.coin_reward,
                    "hidden": ach.hidden,
                }
                for ach_id, ach in ACHIEVEMENTS.items()
            ],
        }


# 싱글톤 인스턴스
_achievement_manager: Optional[AchievementManager] = None


def get_achievement_manager() -> AchievementManager:
    global _achievement_manager
    if _achievement_manager is None:
        _achievement_manager = AchievementManager()
    return _achievement_manager


# 통계
print(f"Total achievements: {len(ACHIEVEMENTS)}")
for cat in AchievementCategory:
    count = sum(1 for a in ACHIEVEMENTS.values() if a.category == cat)
    print(f"  {cat.value}: {count}")
