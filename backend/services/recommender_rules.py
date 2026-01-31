"""
룰 기반 추천 엔진
- 사용자의 최근 세션 데이터를 기반으로 최적의 집중 루프를 추천
- AI Necessity: 개인 로그 기반 의사결정 엔진
"""

from typing import List, Dict, Optional
from models.schemas import TaskType, AbortReason, LoopPhase, RecommendationResponse


def calculate_recommendation(
    recent_sessions: List[Dict],
    task_type: TaskType,
    difficulty: int,
    hour: int,
    day_of_week: int,
) -> RecommendationResponse:
    """
    룰 기반 추천 생성

    입력:
    - recent_sessions: 최근 세션 데이터 (최대 10개)
    - task_type: 과제 유형
    - difficulty: 난이도 (1-5)
    - hour: 시작 시각 (0-23)
    - day_of_week: 요일 (0=월 ~ 6=일)

    출력:
    - 추천 루프, 예상 완주 확률, 근거
    """

    # 기본값 설정
    base_focus = 25
    base_break = 5
    rounds = 4

    # 분석 변수
    abort_rate = 0.0
    avg_focus_time = 0
    common_abort_reasons: Dict[str, int] = {}
    night_abort_count = 0
    total_sessions = len(recent_sessions)

    # 최근 세션 분석
    if recent_sessions:
        aborted_count = sum(1 for s in recent_sessions if s.get("status") == "aborted")
        abort_rate = aborted_count / total_sessions if total_sessions > 0 else 0

        # 평균 집중 시간 계산
        focus_times = [s.get("total_focus_sec", 0) for s in recent_sessions]
        avg_focus_time = sum(focus_times) / len(focus_times) if focus_times else 0

        # 중단 사유 분포
        for s in recent_sessions:
            reason = s.get("abort_reason")
            if reason:
                common_abort_reasons[reason] = common_abort_reasons.get(reason, 0) + 1

        # 밤 시간대 중단 분석
        for s in recent_sessions:
            start_hour = s.get("start_hour", 12)
            if start_hour >= 22 or start_hour <= 2:
                if s.get("status") == "aborted":
                    night_abort_count += 1

    reasons = []
    risk_level = "low"

    # 룰 1: 중단율이 높으면 집중 시간 단축
    if abort_rate > 0.5:
        base_focus = 12
        base_break = 3
        reasons.append(f"최근 중단율이 {abort_rate*100:.0f}%로 높아 12분 루프로 시작합니다")
        risk_level = "high"
    elif abort_rate > 0.3:
        base_focus = 15
        base_break = 3
        reasons.append(f"최근 중단율이 {abort_rate*100:.0f}%로 15분 루프를 추천합니다")
        risk_level = "medium"

    # 룰 2: 밤 시간대 (22시~02시) 조정
    if 22 <= hour or hour <= 2:
        base_focus = min(base_focus, 15)
        base_break = max(base_break, 5)
        if night_abort_count > 2:
            base_focus = 10
            reasons.append("밤 시간대 중단이 많았어요. 짧은 루프로 시작해볼까요?")
            risk_level = "high"
        else:
            reasons.append("늦은 시간이네요. 부담 없이 짧게 시작해봐요")

    # 룰 3: 과제 유형별 조정
    if task_type == TaskType.PRACTICE:
        # 실습은 몰입이 필요 - 집중 시간 유지, 휴식 짧게
        base_break = max(2, base_break - 1)
        reasons.append("실습 과제는 흐름이 중요해서 휴식을 짧게 설정했어요")
    elif task_type == TaskType.ROUTINE:
        # 일상 반복 작업 - 휴식 길게
        base_break = min(10, base_break + 2)
        reasons.append("반복 작업엔 충분한 휴식이 도움돼요")
    elif task_type == TaskType.CREATION:
        # 창작 - 긴 집중 시간 선호할 수 있음
        if avg_focus_time > 20 * 60 and abort_rate < 0.3:
            base_focus = min(30, base_focus + 5)
            reasons.append("창작 작업에 집중을 잘하시네요! 조금 더 긴 루프로 설정했어요")

    # 룰 4: 난이도별 조정
    if difficulty >= 4:
        # 어려운 과제 - 집중 시간 단축
        base_focus = min(base_focus, 20)
        reasons.append("어려운 과제니까 짧게 자주 쉬어가며 해봐요")
    elif difficulty <= 2:
        # 쉬운 과제 - 조금 더 길게
        base_focus = min(30, base_focus + 5)

    # 룰 5: 주말 조정
    if day_of_week >= 5:  # 토요일, 일요일
        base_break = min(10, base_break + 2)
        if not any("주말" in r for r in reasons):
            reasons.append("주말엔 여유롭게 진행해봐요")

    # 룰 6: 스마트폰 유혹이 많으면 마이크로 루틴 추천
    micro_routine = None
    if common_abort_reasons.get("phone", 0) >= 2:
        micro_routine = "시작 전 스마트폰을 다른 방에 두고, 첫 2분은 화면만 봐주세요"
        risk_level = "high" if risk_level != "high" else risk_level
    elif common_abort_reasons.get("bored", 0) >= 2:
        micro_routine = "시작하기 전에 오늘 할 일 중 가장 쉬운 것 하나만 먼저 시작해보세요"
    elif common_abort_reasons.get("tired", 0) >= 2:
        micro_routine = "시작 전 스트레칭 1분! 피로할 땐 몸을 먼저 깨워주세요"

    # 완주 확률 계산 (단순 룰 기반)
    base_prob = 0.7
    if abort_rate > 0.5:
        base_prob -= 0.2
    elif abort_rate > 0.3:
        base_prob -= 0.1

    if base_focus <= 15:
        base_prob += 0.1

    if difficulty >= 4:
        base_prob -= 0.1

    if 22 <= hour or hour <= 2:
        base_prob -= 0.05

    completion_prob = max(0.4, min(0.9, base_prob))

    # 루프 생성
    loop: List[LoopPhase] = []
    for i in range(rounds):
        loop.append(LoopPhase(type="focus", minutes=base_focus))
        if i < rounds - 1:  # 마지막 라운드 후에는 휴식 없음
            loop.append(LoopPhase(type="break", minutes=base_break))

    # 근거 문장 생성
    if not reasons:
        reasons.append(f"{base_focus}분 집중 + {base_break}분 휴식으로 시작해볼게요")

    reason_text = " ".join(reasons[:2])  # 최대 2개 근거만

    return RecommendationResponse(
        recommended_loop=loop,
        predicted_completion_prob=round(completion_prob, 2),
        reason=reason_text,
        risk_level=risk_level,
        micro_routine=micro_routine,
    )


def generate_weekly_experiment(
    weekly_stats: Dict,
    abort_reasons: Dict[str, int],
    hourly_completion_rate: Dict[int, float],
) -> str:
    """
    주간 리포트용 '실험 1개' 추천
    """
    suggestions = []

    # 시간대 분석
    if hourly_completion_rate:
        worst_hour = min(hourly_completion_rate, key=hourly_completion_rate.get)
        best_hour = max(hourly_completion_rate, key=hourly_completion_rate.get)

        if hourly_completion_rate[worst_hour] < 0.5:
            hour_str = f"{worst_hour}시"
            suggestions.append(f"{hour_str} 세션에서 중단이 많았어요. 이 시간대엔 10분 루프로 시작해보는 건 어떨까요?")

    # 중단 사유 분석
    if abort_reasons:
        top_reason = max(abort_reasons, key=abort_reasons.get)
        reason_map = {
            "phone": "스마트폰을 다른 공간에 두고 세션을 시작해보세요",
            "tired": "세션 시작 전 1분 스트레칭을 추가해보세요",
            "bored": "집중 시간을 15분으로 줄이고 작은 목표를 설정해보세요",
            "anxious": "시작 전 심호흡 3번으로 마음을 정리해보세요",
            "environment": "조용한 장소를 찾거나 노이즈캔슬링을 사용해보세요",
        }
        if top_reason in reason_map:
            suggestions.append(f"{reason_map[top_reason]}")

    # 기본 제안
    if not suggestions:
        suggestions.append("이번 주는 집중 시간을 5분 줄이고 라운드를 1개 늘려보는 실험을 해보세요!")

    return suggestions[0]
