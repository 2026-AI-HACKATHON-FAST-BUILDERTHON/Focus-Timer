"""
유저 페르소나 정의
- 다양한 집중 패턴을 가진 가상 유저 프로필
- AI 모델 학습을 위한 더미 데이터 생성 기반
"""

from typing import List, Dict
from enum import Enum
import random


class PersonaType(str, Enum):
    FOCUSED_STUDENT = "focused_student"      # 집중력 좋은 학생
    DISTRACTED_WORKER = "distracted_worker"  # 산만한 직장인
    NIGHT_OWL = "night_owl"                  # 야행성 유저
    MORNING_PERSON = "morning_person"        # 아침형 인간
    PHONE_ADDICT = "phone_addict"            # 스마트폰 중독자
    ANXIOUS_PERFECTIONIST = "anxious_perfectionist"  # 불안한 완벽주의자
    CASUAL_LEARNER = "casual_learner"        # 가벼운 학습자
    INTENSIVE_CREATOR = "intensive_creator"  # 집중 창작자
    # 추가 타입
    SPRINTER = "sprinter"                    # 짧은 집중 선호
    MARATHONER = "marathoner"                # 긴 집중 선호
    DIGITAL_DETOXER = "digital_detoxer"      # 디지털 디톡서
    ENERGY_MANAGER = "energy_manager"        # 에너지 관리자
    PERFECTIONIST = "perfectionist"          # 완벽주의자
    EXPERIMENTER = "experimenter"            # 실험가


PERSONA_PROFILES: Dict[PersonaType, Dict] = {
    PersonaType.FOCUSED_STUDENT: {
        "name": "집중력 좋은 학생",
        "description": "25분 집중도 거뜬히 해내는 모범생. 꾸준한 루틴으로 높은 완주율을 유지합니다.",
        "preferred_focus_min": 25,
        "preferred_focus_max": 45,
        "completion_rate": 0.85,
        "abort_reasons": {"bored": 0.05, "tired": 0.05, "urgent": 0.05},
        "active_hours": list(range(9, 22)),
        "task_preference": ["reading", "practice"],
        "difficulty_tolerance": 4,
        "strengths": ["높은 완주율", "긴 집중 시간", "꾸준한 루틴"],
        "weaknesses": ["가끔 번아웃 위험"],
        "tips": ["주 1회 완전 휴식일을 가져보세요", "새로운 과제 유형에 도전해보세요"],
    },
    PersonaType.DISTRACTED_WORKER: {
        "name": "산만한 직장인",
        "description": "업무 중 자주 딴짓하게 되는 직장인. 짧은 집중 루프가 효과적입니다.",
        "preferred_focus_min": 10,
        "preferred_focus_max": 20,
        "completion_rate": 0.55,
        "abort_reasons": {"phone": 0.3, "bored": 0.15, "environment": 0.1},
        "active_hours": list(range(9, 18)),
        "task_preference": ["routine", "practice"],
        "difficulty_tolerance": 2,
        "strengths": ["멀티태스킹 능력", "빠른 작업 전환"],
        "weaknesses": ["긴 집중 어려움", "외부 자극에 민감"],
        "tips": ["10분 집중 + 2분 휴식으로 시작하세요", "스마트폰을 다른 방에 두세요"],
    },
    PersonaType.NIGHT_OWL: {
        "name": "올빼미형 집중러",
        "description": "밤에 집중력이 높아지는 올빼미족. 저녁 시간을 최대한 활용하세요.",
        "preferred_focus_min": 20,
        "preferred_focus_max": 35,
        "completion_rate": 0.70,
        "abort_reasons": {"tired": 0.2, "phone": 0.1},
        "active_hours": list(range(20, 24)) + list(range(0, 3)),
        "task_preference": ["creation", "reading"],
        "difficulty_tolerance": 3,
        "strengths": ["밤 시간 높은 집중력", "조용한 환경 활용"],
        "weaknesses": ["아침 시간 생산성 낮음", "피로 누적 위험"],
        "tips": ["저녁 9-11시에 중요한 작업을 배치하세요", "적정 수면 시간을 확보하세요"],
    },
    PersonaType.MORNING_PERSON: {
        "name": "아침형 인간",
        "description": "새벽/아침에 생산성이 폭발하는 사람. 이른 시간을 활용하세요.",
        "preferred_focus_min": 25,
        "preferred_focus_max": 40,
        "completion_rate": 0.80,
        "abort_reasons": {"tired": 0.1, "urgent": 0.1},
        "active_hours": list(range(5, 12)),
        "task_preference": ["reading", "routine"],
        "difficulty_tolerance": 4,
        "strengths": ["아침 고집중력", "하루 일찍 성취감 확보"],
        "weaknesses": ["저녁 시간 피로감"],
        "tips": ["가장 어려운 과제는 아침에 배치하세요", "오후 3시 이후는 가벼운 작업만"],
    },
    PersonaType.PHONE_ADDICT: {
        "name": "디지털 디톡스 필요형",
        "description": "스마트폰 유혹에 취약한 타입. 물리적 분리가 효과적입니다.",
        "preferred_focus_min": 5,
        "preferred_focus_max": 15,
        "completion_rate": 0.40,
        "abort_reasons": {"phone": 0.5, "bored": 0.1},
        "active_hours": list(range(10, 23)),
        "task_preference": ["routine"],
        "difficulty_tolerance": 1,
        "strengths": ["빠른 정보 습득력", "디지털 친화적"],
        "weaknesses": ["집중 유지 어려움", "알림에 민감"],
        "tips": ["집중 시작 전 스마트폰을 다른 방에 두세요", "5분 집중부터 시작해 점진적으로 늘려가세요"],
    },
    PersonaType.ANXIOUS_PERFECTIONIST: {
        "name": "불안한 완벽주의자",
        "description": "시작 전 걱정이 많고 중간에 불안해지는 사람. 작은 성공 경험이 중요합니다.",
        "preferred_focus_min": 15,
        "preferred_focus_max": 25,
        "completion_rate": 0.50,
        "abort_reasons": {"anxious": 0.35, "tired": 0.15},
        "active_hours": list(range(8, 20)),
        "task_preference": ["practice", "creation"],
        "difficulty_tolerance": 2,
        "strengths": ["높은 품질 추구", "꼼꼼한 작업"],
        "weaknesses": ["시작이 어려움", "완벽 강박"],
        "tips": ["심호흡 3회 후 시작하세요", "완벽하지 않아도 괜찮아요. 시작이 중요합니다"],
    },
    PersonaType.CASUAL_LEARNER: {
        "name": "캐주얼 러너",
        "description": "부담없이 조금씩 학습하는 사람. 꾸준함이 무기입니다.",
        "preferred_focus_min": 15,
        "preferred_focus_max": 20,
        "completion_rate": 0.75,
        "abort_reasons": {"bored": 0.15, "tired": 0.1},
        "active_hours": list(range(12, 22)),
        "task_preference": ["reading", "routine"],
        "difficulty_tolerance": 2,
        "strengths": ["꾸준한 학습 습관", "부담 없는 접근"],
        "weaknesses": ["깊은 몰입 부족"],
        "tips": ["하루 20분 꾸준히 유지하세요", "가끔 30분 집중에 도전해보세요"],
    },
    PersonaType.INTENSIVE_CREATOR: {
        "name": "집중 창작자",
        "description": "몰입하면 시간 가는 줄 모르는 창작자. 긴 세션이 효과적입니다.",
        "preferred_focus_min": 30,
        "preferred_focus_max": 60,
        "completion_rate": 0.65,
        "abort_reasons": {"tired": 0.2, "environment": 0.1, "bored": 0.05},
        "active_hours": list(range(10, 24)),
        "task_preference": ["creation"],
        "difficulty_tolerance": 5,
        "strengths": ["깊은 몰입력", "창의적 문제 해결"],
        "weaknesses": ["중간 휴식 잊음", "피로 누적"],
        "tips": ["45분 집중 후 반드시 10분 휴식하세요", "물과 간식을 가까이 두세요"],
    },
    # 추가 페르소나
    PersonaType.SPRINTER: {
        "name": "스프린터",
        "description": "짧고 강렬한 집중을 선호하는 타입. 10-15분 세션이 최적입니다.",
        "preferred_focus_min": 10,
        "preferred_focus_max": 15,
        "completion_rate": 0.80,
        "abort_reasons": {"bored": 0.1, "tired": 0.05},
        "active_hours": list(range(9, 21)),
        "task_preference": ["routine", "practice"],
        "difficulty_tolerance": 3,
        "strengths": ["높은 완주율", "빠른 성취감"],
        "weaknesses": ["긴 작업에 부적합"],
        "tips": ["어려운 과제는 여러 개의 짧은 세션으로 나누세요"],
    },
    PersonaType.MARATHONER: {
        "name": "마라토너",
        "description": "긴 집중 시간을 선호하는 타입. 40분 이상 세션에서 진가를 발휘합니다.",
        "preferred_focus_min": 40,
        "preferred_focus_max": 60,
        "completion_rate": 0.70,
        "abort_reasons": {"tired": 0.15, "environment": 0.1},
        "active_hours": list(range(8, 22)),
        "task_preference": ["reading", "creation"],
        "difficulty_tolerance": 5,
        "strengths": ["깊은 몰입", "복잡한 작업 처리"],
        "weaknesses": ["시작 전 워밍업 필요"],
        "tips": ["긴 세션 전 5분 워밍업을 해보세요", "휴식 시간을 꼭 지키세요"],
    },
    PersonaType.DIGITAL_DETOXER: {
        "name": "디지털 디톡서",
        "description": "스마트폰 중단이 가장 많은 타입. 물리적 분리 전략이 효과적입니다.",
        "preferred_focus_min": 10,
        "preferred_focus_max": 20,
        "completion_rate": 0.50,
        "abort_reasons": {"phone": 0.4, "bored": 0.15},
        "active_hours": list(range(10, 22)),
        "task_preference": ["routine"],
        "difficulty_tolerance": 2,
        "strengths": ["디지털 도구 활용 능력"],
        "weaknesses": ["알림에 쉽게 분산"],
        "tips": ["집중 모드/방해금지 모드를 활용하세요", "스마트워치 알림도 끄세요"],
    },
    PersonaType.ENERGY_MANAGER: {
        "name": "에너지 관리자",
        "description": "피로 중단이 많은 타입. 컨디션 관리가 핵심입니다.",
        "preferred_focus_min": 15,
        "preferred_focus_max": 25,
        "completion_rate": 0.55,
        "abort_reasons": {"tired": 0.35, "bored": 0.1},
        "active_hours": list(range(9, 18)),
        "task_preference": ["routine", "reading"],
        "difficulty_tolerance": 2,
        "strengths": ["자기 컨디션 인식력"],
        "weaknesses": ["에너지 변동 큼"],
        "tips": ["충분한 수면을 확보하세요", "오후 졸릴 때는 5분 스트레칭 후 재시작"],
    },
    PersonaType.PERFECTIONIST: {
        "name": "완벽주의자",
        "description": "높은 완주율을 자랑하는 타입. 목표 달성에 강합니다.",
        "preferred_focus_min": 25,
        "preferred_focus_max": 40,
        "completion_rate": 0.85,
        "abort_reasons": {"tired": 0.08, "urgent": 0.07},
        "active_hours": list(range(8, 21)),
        "task_preference": ["practice", "reading"],
        "difficulty_tolerance": 4,
        "strengths": ["높은 완주율", "꾸준한 실행력"],
        "weaknesses": ["번아웃 주의"],
        "tips": ["완벽하지 않아도 괜찮아요", "주 1회 완전 휴식을 가지세요"],
    },
    PersonaType.EXPERIMENTER: {
        "name": "실험가",
        "description": "다양한 시간대와 과제 유형을 시도하는 타입. 최적의 패턴을 찾아가고 있습니다.",
        "preferred_focus_min": 15,
        "preferred_focus_max": 35,
        "completion_rate": 0.60,
        "abort_reasons": {"bored": 0.2, "tired": 0.15},
        "active_hours": list(range(7, 24)),
        "task_preference": ["reading", "practice", "creation", "routine"],
        "difficulty_tolerance": 3,
        "strengths": ["유연성", "다양한 시도"],
        "weaknesses": ["패턴 정립 필요"],
        "tips": ["효과 좋았던 조합을 기록해두세요", "골든타임을 찾으면 고정 루틴을 만드세요"],
    },
}


def get_persona_profile(persona_type: PersonaType) -> Dict:
    """페르소나 프로필 반환"""
    return PERSONA_PROFILES.get(persona_type, PERSONA_PROFILES[PersonaType.CASUAL_LEARNER])


def classify_user_persona(
    completion_rate: float,
    avg_focus_minutes: float,
    top_abort_reason: str,
    active_hours: List[int],
) -> PersonaType:
    """
    사용자 데이터를 기반으로 가장 유사한 페르소나 분류
    """
    scores = {}

    for persona_type, profile in PERSONA_PROFILES.items():
        score = 0

        # 완주율 비교
        rate_diff = abs(completion_rate - profile["completion_rate"])
        score += (1 - rate_diff) * 30

        # 집중 시간 비교
        focus_range = (profile["preferred_focus_min"], profile["preferred_focus_max"])
        if focus_range[0] <= avg_focus_minutes <= focus_range[1]:
            score += 25
        elif avg_focus_minutes < focus_range[0]:
            score += 15 * (avg_focus_minutes / focus_range[0])
        else:
            score += 15 * (focus_range[1] / avg_focus_minutes)

        # 중단 사유 비교
        abort_probs = profile["abort_reasons"]
        if top_abort_reason in abort_probs:
            score += abort_probs[top_abort_reason] * 30

        # 활동 시간대 비교
        if active_hours:
            overlap = len(set(active_hours) & set(profile["active_hours"]))
            score += (overlap / len(profile["active_hours"])) * 15

        scores[persona_type] = score

    return max(scores, key=scores.get)
