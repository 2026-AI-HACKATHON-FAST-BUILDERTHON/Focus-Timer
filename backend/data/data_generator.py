"""
더미 데이터 생성기
- 각 페르소나별로 현실적인 세션 데이터 생성
- AI 모델 학습을 위한 학습 데이터셋 구축
"""

import random
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
from data.personas import PersonaType, PERSONA_PROFILES
import json
import os


def generate_session_for_persona(
    persona_type: PersonaType,
    session_date: datetime,
    session_id: int,
) -> Dict:
    """
    특정 페르소나의 세션 데이터 생성
    """
    profile = PERSONA_PROFILES[persona_type]

    # 활동 시간대에서 시작 시간 선택
    start_hour = random.choice(profile["active_hours"])

    # 과제 유형 선택
    task_type = random.choice(profile["task_preference"])

    # 난이도 (1-5)
    difficulty = min(5, max(1, random.randint(1, profile["difficulty_tolerance"] + 1)))

    # 집중 시간 설정
    focus_minutes = random.randint(
        profile["preferred_focus_min"],
        profile["preferred_focus_max"]
    )
    break_minutes = random.randint(3, 7)
    rounds = random.randint(2, 5)

    # 완료 여부 결정 (완주율 기반)
    base_completion_prob = profile["completion_rate"]

    # 요인별 조정
    if difficulty >= 4:
        base_completion_prob -= 0.1
    if start_hour >= 22 or start_hour <= 2:
        base_completion_prob -= 0.1
    if focus_minutes > 30:
        base_completion_prob -= 0.05

    completed = random.random() < base_completion_prob

    # 중단된 경우 중단 사유 결정
    abort_reason = None
    abort_at_round = None
    actual_focus_seconds = 0

    if not completed:
        # 중단 사유 확률에 따라 선택
        abort_reasons_probs = profile["abort_reasons"]
        if abort_reasons_probs:
            reasons = list(abort_reasons_probs.keys())
            probs = list(abort_reasons_probs.values())
            # 확률 정규화
            total_prob = sum(probs)
            if total_prob > 0:
                probs = [p / total_prob for p in probs]
                abort_reason = random.choices(reasons, weights=probs, k=1)[0]
            else:
                abort_reason = random.choice(["phone", "tired", "bored"])
        else:
            abort_reason = random.choice(["phone", "tired", "bored"])

        # 중단 시점 (몇 라운드에서 중단?)
        abort_at_round = random.randint(1, rounds)
        actual_focus_seconds = (abort_at_round - 1) * focus_minutes * 60 + random.randint(30, focus_minutes * 60)
    else:
        actual_focus_seconds = rounds * focus_minutes * 60

    return {
        "session_id": session_id,
        "persona_type": persona_type.value,
        "date": session_date.isoformat(),
        "start_hour": start_hour,
        "day_of_week": session_date.weekday(),
        "task_type": task_type,
        "difficulty": difficulty,
        "planned_focus_minutes": focus_minutes,
        "planned_break_minutes": break_minutes,
        "planned_rounds": rounds,
        "status": "completed" if completed else "aborted",
        "abort_reason": abort_reason,
        "abort_at_round": abort_at_round,
        "total_focus_sec": actual_focus_seconds,
        "completion_rate": 1.0 if completed else (abort_at_round - 1) / rounds if abort_at_round else 0,
    }


def generate_dataset(
    num_users_per_persona: int = 10,
    sessions_per_user: int = 30,
    days_span: int = 60,
) -> Tuple[List[Dict], List[Dict]]:
    """
    전체 학습 데이터셋 생성

    Returns:
        (users, sessions): 유저 리스트, 세션 리스트
    """
    users = []
    sessions = []
    session_id = 1
    user_id = 1

    for persona_type in PersonaType:
        for _ in range(num_users_per_persona):
            user = {
                "user_id": user_id,
                "persona_type": persona_type.value,
                "created_at": (datetime.now() - timedelta(days=days_span)).isoformat(),
            }
            users.append(user)

            # 각 유저별 세션 생성
            for session_idx in range(sessions_per_user):
                # 랜덤 날짜 (지난 N일 중)
                days_ago = random.randint(0, days_span)
                session_date = datetime.now() - timedelta(days=days_ago)

                session = generate_session_for_persona(
                    persona_type=persona_type,
                    session_date=session_date,
                    session_id=session_id,
                )
                session["user_id"] = user_id
                sessions.append(session)
                session_id += 1

            user_id += 1

    return users, sessions


def generate_training_features(sessions: List[Dict]) -> List[Dict]:
    """
    세션 데이터에서 ML 학습용 피처 추출
    """
    features = []

    for session in sessions:
        feature = {
            # 입력 피처
            "start_hour": session["start_hour"],
            "day_of_week": session["day_of_week"],
            "task_type_reading": 1 if session["task_type"] == "reading" else 0,
            "task_type_practice": 1 if session["task_type"] == "practice" else 0,
            "task_type_creation": 1 if session["task_type"] == "creation" else 0,
            "task_type_routine": 1 if session["task_type"] == "routine" else 0,
            "difficulty": session["difficulty"],
            "planned_focus_minutes": session["planned_focus_minutes"],
            "planned_break_minutes": session["planned_break_minutes"],
            "planned_rounds": session["planned_rounds"],
            # 타겟
            "completed": 1 if session["status"] == "completed" else 0,
            "completion_rate": session["completion_rate"],
            # 메타
            "user_id": session["user_id"],
            "persona_type": session["persona_type"],
        }
        features.append(feature)

    return features


def save_dataset(output_dir: str = "data/generated"):
    """데이터셋을 파일로 저장"""
    os.makedirs(output_dir, exist_ok=True)

    users, sessions = generate_dataset()
    features = generate_training_features(sessions)

    with open(f"{output_dir}/users.json", "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

    with open(f"{output_dir}/sessions.json", "w", encoding="utf-8") as f:
        json.dump(sessions, f, ensure_ascii=False, indent=2)

    with open(f"{output_dir}/training_features.json", "w", encoding="utf-8") as f:
        json.dump(features, f, ensure_ascii=False, indent=2)

    print(f"Generated {len(users)} users, {len(sessions)} sessions")
    print(f"Training features: {len(features)} samples")

    return users, sessions, features


if __name__ == "__main__":
    save_dataset()
