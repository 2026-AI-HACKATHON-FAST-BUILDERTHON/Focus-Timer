"""
고도화된 더미 데이터 생성기
- 100,000개 세션 데이터 생성
- 확장된 피처 (25개)
- 현실적인 시간적 패턴 반영
"""

import random
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, asdict
import json
import os
import math

from data.personas import PersonaType, PERSONA_PROFILES


@dataclass
class UserProfile:
    """사용자 프로필"""
    user_id: int
    persona_type: str
    created_at: str
    # 개인 특성
    preferred_start_hour: int
    consistency_score: float  # 0-1, 일관성
    morning_person_score: float  # 0-1, 아침형 정도
    weekend_active: bool
    avg_sessions_per_day: float


@dataclass
class SessionData:
    """세션 데이터"""
    session_id: int
    user_id: int
    persona_type: str
    date: str
    start_hour: int
    day_of_week: int
    is_weekend: bool
    task_type: str
    difficulty: int
    planned_focus_minutes: int
    planned_break_minutes: int
    planned_rounds: int
    status: str
    abort_reason: Optional[str]
    abort_at_round: Optional[int]
    total_focus_sec: int
    completion_rate: float
    # 추가 컨텍스트
    sessions_today: int
    sessions_this_week: int
    streak_days: int
    last_session_hours_ago: float
    same_hour_completion_rate: float
    same_task_completion_rate: float
    recent_7day_completion_rate: float
    recent_7day_avg_focus: float
    fatigue_score: float  # 피로도 (0-1)
    momentum_score: float  # 연속 성공 모멘텀 (0-1)


def generate_user_profile(user_id: int, persona_type: PersonaType) -> UserProfile:
    """사용자 프로필 생성"""
    profile = PERSONA_PROFILES[persona_type]

    # 선호 시작 시간 (페르소나 활동 시간에서 선택)
    preferred_hour = random.choice(profile["active_hours"])

    # 아침형 점수
    morning_score = 0.8 if persona_type == PersonaType.MORNING_PERSON else \
                   0.2 if persona_type == PersonaType.NIGHT_OWL else \
                   random.uniform(0.3, 0.7)

    return UserProfile(
        user_id=user_id,
        persona_type=persona_type.value,
        created_at=(datetime.now() - timedelta(days=random.randint(30, 180))).isoformat(),
        preferred_start_hour=preferred_hour,
        consistency_score=random.uniform(0.4, 0.9),
        morning_person_score=morning_score,
        weekend_active=random.random() < 0.6,
        avg_sessions_per_day=random.uniform(1.0, 4.0),
    )


def calculate_completion_probability(
    profile: Dict,
    user: UserProfile,
    hour: int,
    day_of_week: int,
    difficulty: int,
    focus_minutes: int,
    context: Dict,
) -> float:
    """
    완주 확률 계산 (현실적인 요소 반영)
    """
    base_prob = profile["completion_rate"]

    # 1. 시간대 영향 (-0.15 ~ +0.1)
    hour_diff = abs(hour - user.preferred_start_hour)
    if hour_diff > 6:
        hour_diff = 12 - hour_diff
    base_prob -= hour_diff * 0.02

    # 2. 아침형/저녁형 영향
    if hour < 10:
        base_prob += (user.morning_person_score - 0.5) * 0.15
    elif hour > 20:
        base_prob += (0.5 - user.morning_person_score) * 0.15

    # 3. 주말 영향
    is_weekend = day_of_week >= 5
    if is_weekend and not user.weekend_active:
        base_prob -= 0.1
    elif is_weekend and user.weekend_active:
        base_prob += 0.05

    # 4. 난이도 영향 (-0.2 ~ +0.05)
    difficulty_factor = (difficulty - 3) * 0.07
    base_prob -= difficulty_factor

    # 5. 집중 시간 영향
    if focus_minutes > 30:
        base_prob -= (focus_minutes - 30) * 0.005
    elif focus_minutes < 15:
        base_prob += 0.1

    # 6. 피로도 영향 (오늘 세션 수)
    sessions_today = context.get("sessions_today", 0)
    base_prob -= sessions_today * 0.05

    # 7. 연속 성공 모멘텀
    momentum = context.get("momentum_score", 0.5)
    base_prob += (momentum - 0.5) * 0.15

    # 8. 최근 완주율 영향
    recent_rate = context.get("recent_completion_rate", 0.7)
    base_prob = base_prob * 0.7 + recent_rate * 0.3

    # 9. 밤 시간대 페널티
    if 23 <= hour or hour <= 2:
        base_prob -= 0.15

    # 10. 일관성 영향
    base_prob = base_prob * (0.8 + user.consistency_score * 0.2)

    return max(0.15, min(0.95, base_prob))


def generate_sessions_for_user(
    user: UserProfile,
    num_sessions: int,
    start_session_id: int,
    days_span: int = 90,
) -> List[SessionData]:
    """사용자별 세션 데이터 생성"""
    profile = PERSONA_PROFILES[PersonaType(user.persona_type)]
    sessions = []

    # 날짜별 세션 분배
    session_dates = []
    current_date = datetime.now() - timedelta(days=days_span)

    while len(session_dates) < num_sessions:
        # 하루에 1-3개 세션 (평균에 따라)
        sessions_this_day = max(1, int(random.gauss(user.avg_sessions_per_day, 0.5)))
        for _ in range(sessions_this_day):
            if len(session_dates) < num_sessions:
                session_dates.append(current_date)
        current_date += timedelta(days=1)
        if current_date > datetime.now():
            current_date = datetime.now() - timedelta(days=days_span)

    session_dates.sort()

    # 컨텍스트 추적
    recent_results = []  # 최근 결과 (True/False)
    streak_days = 0
    last_session_time = None
    hourly_results = {h: [] for h in range(24)}
    task_results = {t: [] for t in ["reading", "practice", "creation", "routine"]}

    for idx, session_date in enumerate(session_dates):
        session_id = start_session_id + idx

        # 시간 선택 (선호 시간대 근처)
        hour_offset = int(random.gauss(0, 2))
        start_hour = (user.preferred_start_hour + hour_offset) % 24
        if start_hour not in profile["active_hours"]:
            start_hour = random.choice(profile["active_hours"])

        day_of_week = session_date.weekday()
        is_weekend = day_of_week >= 5

        # 과제 유형
        task_type = random.choice(profile["task_preference"])

        # 난이도
        difficulty = min(5, max(1, int(random.gauss(
            profile["difficulty_tolerance"],
            1
        ))))

        # 집중/휴식 시간
        focus_minutes = random.randint(
            profile["preferred_focus_min"],
            profile["preferred_focus_max"]
        )
        break_minutes = random.randint(3, 7)
        rounds = random.randint(2, 5)

        # 컨텍스트 계산
        sessions_today = sum(1 for d in session_dates[:idx] if d.date() == session_date.date())
        sessions_this_week = sum(1 for d in session_dates[max(0, idx-7):idx])

        # 최근 7일 완주율
        recent_7 = recent_results[-20:] if recent_results else []
        recent_completion_rate = sum(recent_7) / len(recent_7) if recent_7 else 0.7

        # 동일 시간대 완주율
        same_hour_results = hourly_results[start_hour][-10:]
        same_hour_rate = sum(same_hour_results) / len(same_hour_results) if same_hour_results else 0.7

        # 동일 과제 유형 완주율
        same_task_results = task_results[task_type][-10:]
        same_task_rate = sum(same_task_results) / len(same_task_results) if same_task_results else 0.7

        # 모멘텀 (연속 성공)
        consecutive_success = 0
        for r in reversed(recent_results[-5:]):
            if r:
                consecutive_success += 1
            else:
                break
        momentum = min(1.0, consecutive_success * 0.2 + 0.3)

        # 마지막 세션 이후 시간
        hours_since_last = 24.0
        if last_session_time:
            delta = session_date - last_session_time
            hours_since_last = delta.total_seconds() / 3600

        # 피로도
        fatigue = min(1.0, sessions_today * 0.25 + max(0, 8 - hours_since_last) * 0.05)

        context = {
            "sessions_today": sessions_today,
            "momentum_score": momentum,
            "recent_completion_rate": recent_completion_rate,
        }

        # 완주 확률 계산
        completion_prob = calculate_completion_probability(
            profile, user, start_hour, day_of_week,
            difficulty, focus_minutes, context
        )

        # 완료 여부 결정
        completed = random.random() < completion_prob

        # 중단된 경우
        abort_reason = None
        abort_at_round = None

        if not completed:
            abort_probs = profile["abort_reasons"]
            if abort_probs:
                reasons = list(abort_probs.keys())
                probs = list(abort_probs.values())
                total = sum(probs)
                if total > 0:
                    probs = [p / total for p in probs]
                    abort_reason = random.choices(reasons, weights=probs, k=1)[0]
            abort_at_round = random.randint(1, rounds)

        # 실제 집중 시간
        if completed:
            total_focus_sec = rounds * focus_minutes * 60
            completion_rate = 1.0
        else:
            total_focus_sec = (abort_at_round - 1) * focus_minutes * 60 + \
                             random.randint(30, focus_minutes * 60)
            completion_rate = (abort_at_round - 1) / rounds if abort_at_round else 0

        # 세션 데이터 생성
        session = SessionData(
            session_id=session_id,
            user_id=user.user_id,
            persona_type=user.persona_type,
            date=session_date.isoformat(),
            start_hour=start_hour,
            day_of_week=day_of_week,
            is_weekend=is_weekend,
            task_type=task_type,
            difficulty=difficulty,
            planned_focus_minutes=focus_minutes,
            planned_break_minutes=break_minutes,
            planned_rounds=rounds,
            status="completed" if completed else "aborted",
            abort_reason=abort_reason,
            abort_at_round=abort_at_round,
            total_focus_sec=total_focus_sec,
            completion_rate=completion_rate,
            sessions_today=sessions_today,
            sessions_this_week=sessions_this_week,
            streak_days=streak_days,
            last_session_hours_ago=hours_since_last,
            same_hour_completion_rate=same_hour_rate,
            same_task_completion_rate=same_task_rate,
            recent_7day_completion_rate=recent_completion_rate,
            recent_7day_avg_focus=sum(s.total_focus_sec for s in sessions[-7:]) / 7 / 60 if sessions else 25,
            fatigue_score=fatigue,
            momentum_score=momentum,
        )

        sessions.append(session)

        # 컨텍스트 업데이트
        recent_results.append(completed)
        hourly_results[start_hour].append(completed)
        task_results[task_type].append(completed)
        last_session_time = session_date

        if completed:
            streak_days = min(30, streak_days + 1)
        else:
            streak_days = 0

    return sessions


def generate_large_dataset(
    users_per_persona: int = 500,
    sessions_per_user: int = 25,
    output_dir: str = "data/generated_large",
) -> Tuple[List[Dict], List[Dict]]:
    """
    대규모 학습 데이터셋 생성

    기본값: 8 페르소나 × 500명 × 25세션 = 100,000 세션
    """
    os.makedirs(output_dir, exist_ok=True)

    users = []
    sessions = []
    user_id = 1
    session_id = 1

    print(f"Generating {users_per_persona * len(PersonaType) * sessions_per_user:,} sessions...")

    for persona_type in PersonaType:
        print(f"  Processing {persona_type.value}...")

        for _ in range(users_per_persona):
            # 유저 생성
            user = generate_user_profile(user_id, persona_type)
            users.append(asdict(user))

            # 세션 생성
            user_sessions = generate_sessions_for_user(
                user, sessions_per_user, session_id
            )
            sessions.extend([asdict(s) for s in user_sessions])

            session_id += len(user_sessions)
            user_id += 1

    # 저장
    print(f"Saving {len(users):,} users, {len(sessions):,} sessions...")

    with open(f"{output_dir}/users.json", "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

    with open(f"{output_dir}/sessions.json", "w", encoding="utf-8") as f:
        json.dump(sessions, f, ensure_ascii=False, indent=2)

    print("Done!")
    return users, sessions


def extract_training_features(sessions: List[Dict]) -> List[Dict]:
    """
    ML 학습용 피처 추출 (25개 피처)
    """
    features = []

    for s in sessions:
        feature = {
            # 기본 피처 (9개)
            "start_hour": s["start_hour"],
            "day_of_week": s["day_of_week"],
            "is_weekend": 1 if s["is_weekend"] else 0,
            "task_type_reading": 1 if s["task_type"] == "reading" else 0,
            "task_type_practice": 1 if s["task_type"] == "practice" else 0,
            "task_type_creation": 1 if s["task_type"] == "creation" else 0,
            "task_type_routine": 1 if s["task_type"] == "routine" else 0,
            "difficulty": s["difficulty"],
            "planned_focus_minutes": s["planned_focus_minutes"],
            "planned_break_minutes": s["planned_break_minutes"],
            "planned_rounds": s["planned_rounds"],

            # 컨텍스트 피처 (14개)
            "sessions_today": s["sessions_today"],
            "sessions_this_week": s["sessions_this_week"],
            "streak_days": s["streak_days"],
            "last_session_hours_ago": min(48, s["last_session_hours_ago"]),
            "same_hour_completion_rate": s["same_hour_completion_rate"],
            "same_task_completion_rate": s["same_task_completion_rate"],
            "recent_7day_completion_rate": s["recent_7day_completion_rate"],
            "recent_7day_avg_focus": s["recent_7day_avg_focus"],
            "fatigue_score": s["fatigue_score"],
            "momentum_score": s["momentum_score"],

            # 시간대 피처
            "is_morning": 1 if 5 <= s["start_hour"] < 12 else 0,
            "is_afternoon": 1 if 12 <= s["start_hour"] < 18 else 0,
            "is_evening": 1 if 18 <= s["start_hour"] < 22 else 0,
            "is_night": 1 if s["start_hour"] >= 22 or s["start_hour"] < 5 else 0,

            # 타겟
            "completed": 1 if s["status"] == "completed" else 0,
            "completion_rate": s["completion_rate"],
            "total_focus_minutes": s["total_focus_sec"] / 60,

            # 메타
            "user_id": s["user_id"],
            "persona_type": s["persona_type"],
        }
        features.append(feature)

    return features


if __name__ == "__main__":
    users, sessions = generate_large_dataset()
    features = extract_training_features(sessions)

    with open("data/generated_large/training_features.json", "w", encoding="utf-8") as f:
        json.dump(features, f, ensure_ascii=False, indent=2)

    print(f"Training features: {len(features):,} samples with {len(features[0])} features each")
