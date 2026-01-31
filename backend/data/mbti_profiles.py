"""
MBTI 기반 학습 성향 프로필

이론적 배경:
- Carl Jung의 심리 유형론 (Psychological Types, 1921) - 공개 도메인
- MBTI 4가지 차원: E/I, S/N, T/F, J/P
- 각 차원이 학습 스타일에 미치는 영향 연구 기반

참고 문헌:
1. Jung, C. G. (1921). Psychological Types. Princeton University Press.
2. Lawrence, G. (1993). People Types and Tiger Stripes. CAPT.
3. DiTiberio, J. K., & Hammer, A. L. (1993). Introduction to Type in College. CPP.
4. Felder, R. M. (1996). Matters of Style. ASEE Prism.

Note: MBTI는 The Myers-Briggs Company의 상표이나,
기본 심리 유형 이론은 Carl Jung의 저작으로 공개 도메인입니다.
본 프로필은 학술 연구에 기반한 일반적인 학습 성향을 정의합니다.
"""

from enum import Enum
from dataclasses import dataclass
from typing import Dict, List, Optional


class MBTIDimension(Enum):
    """MBTI 4가지 차원"""
    EI = "에너지 방향"  # Extraversion/Introversion
    SN = "인식 기능"    # Sensing/iNtuition
    TF = "판단 기능"    # Thinking/Feeling
    JP = "생활 양식"    # Judging/Perceiving


@dataclass
class DimensionProfile:
    """각 차원별 학습 성향"""
    code: str
    name: str
    description: str
    study_preferences: List[str]
    optimal_focus_minutes: tuple  # (min, max)
    optimal_break_style: str
    distraction_triggers: List[str]
    motivation_factors: List[str]
    recommended_task_types: List[str]


# 각 차원별 학습 성향 정의
DIMENSION_PROFILES: Dict[str, DimensionProfile] = {
    # 에너지 방향
    "E": DimensionProfile(
        code="E",
        name="외향형",
        description="외부 세계와 상호작용에서 에너지를 얻음",
        study_preferences=[
            "스터디 그룹 학습",
            "토론 기반 학습",
            "짧은 집중 + 잦은 휴식",
            "다양한 환경 변화",
        ],
        optimal_focus_minutes=(15, 25),
        optimal_break_style="active",  # 활동적 휴식 (스트레칭, 대화)
        distraction_triggers=["고립감", "조용함이 지속될 때", "혼자 오래 있을 때"],
        motivation_factors=["사회적 인정", "즉각적 피드백", "팀 목표"],
        recommended_task_types=["practice", "creation"],
    ),
    "I": DimensionProfile(
        code="I",
        name="내향형",
        description="내면의 세계와 깊은 사고에서 에너지를 얻음",
        study_preferences=[
            "혼자 조용히 학습",
            "깊은 집중 학습",
            "긴 집중 시간",
            "방해 없는 환경",
        ],
        optimal_focus_minutes=(30, 45),
        optimal_break_style="quiet",  # 조용한 휴식 (명상, 산책)
        distraction_triggers=["소음", "잦은 방해", "갑작스러운 상호작용"],
        motivation_factors=["개인적 성취", "깊은 이해", "자기 발전"],
        recommended_task_types=["reading", "creation"],
    ),

    # 인식 기능
    "S": DimensionProfile(
        code="S",
        name="감각형",
        description="구체적이고 실용적인 정보를 선호",
        study_preferences=[
            "단계별 학습",
            "실습 중심",
            "명확한 지침",
            "현실적 예시",
        ],
        optimal_focus_minutes=(20, 30),
        optimal_break_style="structured",  # 구조화된 휴식
        distraction_triggers=["추상적 내용", "불명확한 목표", "이론만 있는 학습"],
        motivation_factors=["실용적 결과", "즉각적 적용", "체크리스트 완료"],
        recommended_task_types=["practice", "routine"],
    ),
    "N": DimensionProfile(
        code="N",
        name="직관형",
        description="패턴과 가능성, 큰 그림을 선호",
        study_preferences=[
            "개념 중심 학습",
            "창의적 접근",
            "자유로운 탐구",
            "연결고리 찾기",
        ],
        optimal_focus_minutes=(25, 40),
        optimal_break_style="creative",  # 창의적 휴식 (아이디어 메모)
        distraction_triggers=["반복적 작업", "세부사항 과다", "융통성 없는 규칙"],
        motivation_factors=["새로운 아이디어", "가능성 탐구", "혁신적 해결"],
        recommended_task_types=["creation", "reading"],
    ),

    # 판단 기능
    "T": DimensionProfile(
        code="T",
        name="사고형",
        description="논리와 객관적 분석을 선호",
        study_preferences=[
            "논리적 구조화",
            "데이터 기반 학습",
            "비판적 분석",
            "효율성 추구",
        ],
        optimal_focus_minutes=(25, 35),
        optimal_break_style="productive",  # 생산적 휴식 (정리, 계획)
        distraction_triggers=["비논리적 상황", "감정적 요소", "비효율적 방법"],
        motivation_factors=["논리적 해결", "효율성 향상", "객관적 성과"],
        recommended_task_types=["practice", "reading"],
    ),
    "F": DimensionProfile(
        code="F",
        name="감정형",
        description="가치와 조화, 인간관계를 중시",
        study_preferences=[
            "의미 있는 학습",
            "협력적 학습",
            "개인적 연결",
            "격려와 지지",
        ],
        optimal_focus_minutes=(20, 30),
        optimal_break_style="social",  # 사회적 휴식 (대화, 공유)
        distraction_triggers=["갈등 상황", "비판적 피드백", "경쟁적 환경"],
        motivation_factors=["의미 발견", "타인 도움", "긍정적 피드백"],
        recommended_task_types=["creation", "routine"],
    ),

    # 생활 양식
    "J": DimensionProfile(
        code="J",
        name="판단형",
        description="계획적이고 체계적인 접근 선호",
        study_preferences=[
            "명확한 계획",
            "데드라인 준수",
            "체계적 진행",
            "완료 지향",
        ],
        optimal_focus_minutes=(25, 35),
        optimal_break_style="scheduled",  # 계획된 휴식
        distraction_triggers=["불확실성", "계획 변경", "마감 없음"],
        motivation_factors=["목표 달성", "계획 완수", "진행 체크"],
        recommended_task_types=["routine", "practice"],
    ),
    "P": DimensionProfile(
        code="P",
        name="인식형",
        description="유연하고 자발적인 접근 선호",
        study_preferences=[
            "유연한 스케줄",
            "흥미 기반 학습",
            "다양한 옵션",
            "마지막 순간 집중",
        ],
        optimal_focus_minutes=(15, 25),
        optimal_break_style="flexible",  # 유연한 휴식
        distraction_triggers=["엄격한 규칙", "단조로움", "강제된 구조"],
        motivation_factors=["흥미", "자유로움", "새로운 발견"],
        recommended_task_types=["creation", "reading"],
    ),
}


@dataclass
class MBTIProfile:
    """16가지 MBTI 유형별 종합 프로필"""
    type_code: str
    name: str
    nickname: str
    description: str
    study_style: str
    optimal_focus_range: tuple  # (min, max) 분
    optimal_break_range: tuple
    optimal_rounds: tuple
    best_study_hours: List[int]
    completion_tendency: float  # 0-1, 완주 성향
    distraction_vulnerability: float  # 0-1, 방해 취약도
    tips: List[str]


# 16가지 MBTI 유형별 학습 프로필
MBTI_PROFILES: Dict[str, MBTIProfile] = {
    "INTJ": MBTIProfile(
        type_code="INTJ",
        name="전략가",
        nickname="용의주도한 전략가",
        description="독립적이고 전략적인 사고를 가진 유형",
        study_style="장기 목표를 세우고 체계적으로 깊이 파고드는 학습",
        optimal_focus_range=(35, 50),
        optimal_break_range=(5, 7),
        optimal_rounds=(3, 4),
        best_study_hours=[6, 7, 8, 21, 22],
        completion_tendency=0.85,
        distraction_vulnerability=0.25,
        tips=[
            "복잡한 문제를 분석하는 시간을 충분히 확보하세요",
            "혼자만의 조용한 공간에서 최고의 집중력을 발휘해요",
            "장기 목표를 시각화하면 동기부여가 됩니다",
        ],
    ),
    "INTP": MBTIProfile(
        type_code="INTP",
        name="논리술사",
        nickname="호기심 많은 사색가",
        description="논리적 분석과 아이디어 탐구를 즐기는 유형",
        study_style="개념을 깊이 탐구하고 이론적 연결고리를 찾는 학습",
        optimal_focus_range=(30, 45),
        optimal_break_range=(5, 10),
        optimal_rounds=(2, 4),
        best_study_hours=[10, 11, 22, 23, 0],
        completion_tendency=0.65,
        distraction_vulnerability=0.45,
        tips=[
            "호기심을 따라가되, 시간 제한을 두세요",
            "아이디어를 메모하는 습관이 집중력을 높여요",
            "완벽주의를 내려놓고 '충분히 좋은' 것에 만족하세요",
        ],
    ),
    "ENTJ": MBTIProfile(
        type_code="ENTJ",
        name="통솔자",
        nickname="대담한 통솔자",
        description="목표 지향적이고 효율성을 추구하는 리더 유형",
        study_style="명확한 목표와 효율적인 계획으로 빠르게 성과 내기",
        optimal_focus_range=(25, 35),
        optimal_break_range=(3, 5),
        optimal_rounds=(4, 5),
        best_study_hours=[6, 7, 8, 9, 18, 19],
        completion_tendency=0.90,
        distraction_vulnerability=0.20,
        tips=[
            "도전적인 목표가 당신을 움직이게 해요",
            "리더십을 발휘할 수 있는 그룹 스터디도 좋아요",
            "성과를 측정하고 기록하면 동기부여가 됩니다",
        ],
    ),
    "ENTP": MBTIProfile(
        type_code="ENTP",
        name="변론가",
        nickname="뜨거운 논쟁을 즐기는 변론가",
        description="창의적이고 토론을 즐기며 새로운 가능성을 탐구하는 유형",
        study_style="다양한 관점을 탐구하고 아이디어를 발전시키는 학습",
        optimal_focus_range=(15, 25),
        optimal_break_range=(5, 7),
        optimal_rounds=(3, 5),
        best_study_hours=[10, 11, 14, 15, 21, 22],
        completion_tendency=0.60,
        distraction_vulnerability=0.55,
        tips=[
            "짧은 집중 시간으로 시작해서 늘려가세요",
            "다양한 주제를 번갈아 학습하면 지루함을 줄일 수 있어요",
            "아이디어를 기록해두고 나중에 탐구하세요",
        ],
    ),
    "INFJ": MBTIProfile(
        type_code="INFJ",
        name="옹호자",
        nickname="선의의 옹호자",
        description="통찰력 있고 이상주의적이며 의미를 추구하는 유형",
        study_style="의미와 목적을 연결하며 깊이 있게 학습",
        optimal_focus_range=(30, 45),
        optimal_break_range=(7, 10),
        optimal_rounds=(2, 3),
        best_study_hours=[6, 7, 20, 21, 22],
        completion_tendency=0.80,
        distraction_vulnerability=0.30,
        tips=[
            "학습의 의미와 목적을 되새기면 집중력이 높아져요",
            "조용하고 영감을 주는 환경을 만드세요",
            "완벽주의 성향을 조절하고 자신에게 여유를 주세요",
        ],
    ),
    "INFP": MBTIProfile(
        type_code="INFP",
        name="중재자",
        nickname="열정적인 중재자",
        description="이상주의적이고 창의적이며 깊은 감정을 가진 유형",
        study_style="개인적 의미를 찾으며 창의적으로 학습",
        optimal_focus_range=(20, 35),
        optimal_break_range=(7, 10),
        optimal_rounds=(2, 3),
        best_study_hours=[9, 10, 11, 21, 22, 23],
        completion_tendency=0.65,
        distraction_vulnerability=0.50,
        tips=[
            "학습 내용과 개인적 가치를 연결해보세요",
            "창의적인 방식으로 정리하면 기억에 오래 남아요",
            "자기 비판보다는 작은 성취를 축하하세요",
        ],
    ),
    "ENFJ": MBTIProfile(
        type_code="ENFJ",
        name="선도자",
        nickname="정의로운 사회운동가",
        description="카리스마 있고 영감을 주며 타인을 이끄는 유형",
        study_style="타인과 함께 성장하며 영감을 주고받는 학습",
        optimal_focus_range=(25, 35),
        optimal_break_range=(5, 7),
        optimal_rounds=(3, 4),
        best_study_hours=[7, 8, 9, 14, 15, 19, 20],
        completion_tendency=0.85,
        distraction_vulnerability=0.30,
        tips=[
            "스터디 그룹을 이끌면 학습 효과가 배가돼요",
            "다른 사람을 가르치는 것이 최고의 학습법이에요",
            "자신의 필요도 돌보는 것을 잊지 마세요",
        ],
    ),
    "ENFP": MBTIProfile(
        type_code="ENFP",
        name="활동가",
        nickname="재기발랄한 활동가",
        description="열정적이고 창의적이며 가능성을 추구하는 유형",
        study_style="흥미와 열정을 따라 다양하게 탐구하는 학습",
        optimal_focus_range=(15, 25),
        optimal_break_range=(5, 7),
        optimal_rounds=(3, 5),
        best_study_hours=[10, 11, 14, 15, 16, 21],
        completion_tendency=0.55,
        distraction_vulnerability=0.65,
        tips=[
            "짧은 세션으로 시작해서 성공 경험을 쌓으세요",
            "다양한 주제를 번갈아 학습하면 집중이 잘 돼요",
            "루틴을 만들되, 약간의 유연성을 허용하세요",
        ],
    ),
    "ISTJ": MBTIProfile(
        type_code="ISTJ",
        name="현실주의자",
        nickname="청렴결백한 논리주의자",
        description="책임감 있고 체계적이며 사실에 기반한 유형",
        study_style="체계적이고 단계적인 방식으로 철저하게 학습",
        optimal_focus_range=(30, 45),
        optimal_break_range=(5, 7),
        optimal_rounds=(3, 4),
        best_study_hours=[6, 7, 8, 9, 19, 20],
        completion_tendency=0.90,
        distraction_vulnerability=0.20,
        tips=[
            "명확한 체크리스트를 만들면 만족감이 높아져요",
            "익숙한 환경에서 최고의 성과를 내요",
            "계획을 세우되, 가끔 유연성도 필요해요",
        ],
    ),
    "ISFJ": MBTIProfile(
        type_code="ISFJ",
        name="수호자",
        nickname="용감한 수호자",
        description="헌신적이고 따뜻하며 책임감 있는 유형",
        study_style="꾸준하고 성실하게 세부사항까지 챙기는 학습",
        optimal_focus_range=(25, 40),
        optimal_break_range=(5, 7),
        optimal_rounds=(3, 4),
        best_study_hours=[7, 8, 9, 10, 19, 20],
        completion_tendency=0.85,
        distraction_vulnerability=0.25,
        tips=[
            "다른 사람을 위한 학습이라고 생각하면 동기부여가 돼요",
            "편안하고 익숙한 환경을 만드세요",
            "자신의 노력도 인정하고 쉬어가세요",
        ],
    ),
    "ESTJ": MBTIProfile(
        type_code="ESTJ",
        name="경영자",
        nickname="엄격한 관리자",
        description="효율적이고 조직적이며 결과 지향적인 유형",
        study_style="명확한 목표와 체계적 계획으로 효율적으로 학습",
        optimal_focus_range=(25, 35),
        optimal_break_range=(3, 5),
        optimal_rounds=(4, 5),
        best_study_hours=[6, 7, 8, 18, 19, 20],
        completion_tendency=0.90,
        distraction_vulnerability=0.20,
        tips=[
            "목표를 세분화하고 하나씩 달성하세요",
            "진행 상황을 측정하면 동기부여가 됩니다",
            "때로는 유연성을 허용하는 것도 효율적이에요",
        ],
    ),
    "ESFJ": MBTIProfile(
        type_code="ESFJ",
        name="집정관",
        nickname="사교적인 외교관",
        description="사교적이고 배려심 있으며 조화를 추구하는 유형",
        study_style="다른 사람과 함께하며 서로 격려하는 학습",
        optimal_focus_range=(20, 30),
        optimal_break_range=(5, 7),
        optimal_rounds=(3, 4),
        best_study_hours=[8, 9, 10, 14, 15, 19],
        completion_tendency=0.80,
        distraction_vulnerability=0.35,
        tips=[
            "스터디 그룹이 학습 효과를 높여줘요",
            "주변 사람에게 목표를 공유하면 책임감이 생겨요",
            "자신을 위한 학습도 중요하다는 걸 기억하세요",
        ],
    ),
    "ISTP": MBTIProfile(
        type_code="ISTP",
        name="장인",
        nickname="만능 재주꾼",
        description="실용적이고 분석적이며 도구를 다루는 데 능숙한 유형",
        study_style="직접 해보며 문제를 해결하는 실습 중심 학습",
        optimal_focus_range=(20, 30),
        optimal_break_range=(5, 7),
        optimal_rounds=(2, 4),
        best_study_hours=[10, 11, 14, 15, 22, 23],
        completion_tendency=0.70,
        distraction_vulnerability=0.40,
        tips=[
            "실습과 이론을 번갈아 학습하세요",
            "문제 해결에 초점을 맞추면 집중이 잘 돼요",
            "자유롭게 탐구할 시간을 확보하세요",
        ],
    ),
    "ISFP": MBTIProfile(
        type_code="ISFP",
        name="모험가",
        nickname="호기심 많은 예술가",
        description="온화하고 감각적이며 현재에 충실한 유형",
        study_style="개인적 관심사를 따라 자유롭게 탐구하는 학습",
        optimal_focus_range=(15, 25),
        optimal_break_range=(5, 10),
        optimal_rounds=(2, 4),
        best_study_hours=[10, 11, 14, 15, 16, 21],
        completion_tendency=0.60,
        distraction_vulnerability=0.50,
        tips=[
            "시각적, 감각적 자료를 활용하세요",
            "자신만의 창의적 방식으로 정리해보세요",
            "작은 성취도 소중히 여기세요",
        ],
    ),
    "ESTP": MBTIProfile(
        type_code="ESTP",
        name="사업가",
        nickname="모험을 즐기는 사업가",
        description="활동적이고 현실적이며 즉흥적인 유형",
        study_style="실용적이고 즉각적인 결과를 추구하는 학습",
        optimal_focus_range=(15, 25),
        optimal_break_range=(5, 7),
        optimal_rounds=(3, 5),
        best_study_hours=[10, 11, 14, 15, 16, 17],
        completion_tendency=0.55,
        distraction_vulnerability=0.60,
        tips=[
            "짧고 강렬한 집중 세션이 효과적이에요",
            "게임화된 학습이 동기부여에 좋아요",
            "움직이면서 학습하는 것도 시도해보세요",
        ],
    ),
    "ESFP": MBTIProfile(
        type_code="ESFP",
        name="연예인",
        nickname="자유로운 영혼의 연예인",
        description="사교적이고 즐거움을 추구하며 현재에 충실한 유형",
        study_style="재미있고 사교적인 방식으로 즐기며 학습",
        optimal_focus_range=(10, 20),
        optimal_break_range=(5, 7),
        optimal_rounds=(3, 5),
        best_study_hours=[11, 12, 14, 15, 16, 17],
        completion_tendency=0.50,
        distraction_vulnerability=0.70,
        tips=[
            "가장 짧은 집중 시간으로 시작하세요",
            "친구와 함께 학습하면 더 재미있어요",
            "보상 시스템을 활용하세요 - 당신은 그럴 자격이 있어요!",
        ],
    ),
}


def get_combined_profile(mbti_type: str) -> Dict:
    """MBTI 유형의 종합 프로필 반환"""
    if mbti_type not in MBTI_PROFILES:
        return None

    profile = MBTI_PROFILES[mbti_type]

    # 각 차원별 성향 결합
    dimensions = {
        "EI": DIMENSION_PROFILES.get(mbti_type[0]),
        "SN": DIMENSION_PROFILES.get(mbti_type[1]),
        "TF": DIMENSION_PROFILES.get(mbti_type[2]),
        "JP": DIMENSION_PROFILES.get(mbti_type[3]),
    }

    return {
        "type_code": profile.type_code,
        "name": profile.name,
        "nickname": profile.nickname,
        "description": profile.description,
        "study_style": profile.study_style,
        "optimal_focus_range": profile.optimal_focus_range,
        "optimal_break_range": profile.optimal_break_range,
        "optimal_rounds": profile.optimal_rounds,
        "best_study_hours": profile.best_study_hours,
        "completion_tendency": profile.completion_tendency,
        "distraction_vulnerability": profile.distraction_vulnerability,
        "tips": profile.tips,
        "dimensions": {
            k: {
                "name": v.name,
                "study_preferences": v.study_preferences,
                "distraction_triggers": v.distraction_triggers,
                "motivation_factors": v.motivation_factors,
            }
            for k, v in dimensions.items() if v
        },
    }


def calculate_optimal_settings(mbti_type: str, user_context: Dict = None) -> Dict:
    """MBTI 기반 최적 설정 계산"""
    if mbti_type not in MBTI_PROFILES:
        return {
            "focus_minutes": 25,
            "break_minutes": 5,
            "rounds": 4,
            "confidence": 0.0,
        }

    profile = MBTI_PROFILES[mbti_type]
    context = user_context or {}

    # 기본 설정
    focus_min, focus_max = profile.optimal_focus_range
    break_min, break_max = profile.optimal_break_range
    rounds_min, rounds_max = profile.optimal_rounds

    # 중간값 사용
    focus = (focus_min + focus_max) // 2
    break_time = (break_min + break_max) // 2
    rounds = (rounds_min + rounds_max) // 2

    # 시간대 조정
    hour = context.get("hour", 12)
    if hour in profile.best_study_hours:
        # 골든타임에는 조금 더 긴 집중 가능
        focus = min(focus + 5, focus_max)

    # 피로도 조정
    fatigue = context.get("fatigue", 0.3)
    if fatigue > 0.6:
        focus = max(focus - 5, focus_min)
        rounds = max(rounds - 1, rounds_min)

    return {
        "focus_minutes": focus,
        "break_minutes": break_time,
        "rounds": rounds,
        "completion_tendency": profile.completion_tendency,
        "confidence": 0.85,  # MBTI 기반 추천 신뢰도
    }


# 설문 질문 정의
SURVEY_QUESTIONS = [
    {
        "id": "q1_energy",
        "question": "에너지를 얻는 방식은?",
        "dimension": "EI",
        "options": [
            {"value": "E", "text": "사람들과 어울릴 때 활력이 생겨요", "icon": "bi-people-fill"},
            {"value": "I", "text": "혼자만의 시간이 충전해줘요", "icon": "bi-person-fill"},
        ],
    },
    {
        "id": "q2_study_env",
        "question": "선호하는 학습 환경은?",
        "dimension": "EI",
        "options": [
            {"value": "E", "text": "카페나 스터디 그룹에서 함께", "icon": "bi-cup-hot-fill"},
            {"value": "I", "text": "조용한 개인 공간에서 혼자", "icon": "bi-house-fill"},
        ],
    },
    {
        "id": "q3_info_style",
        "question": "정보를 받아들이는 방식은?",
        "dimension": "SN",
        "options": [
            {"value": "S", "text": "구체적인 사실과 단계별 설명", "icon": "bi-list-check"},
            {"value": "N", "text": "전체 그림과 개념적 이해", "icon": "bi-lightbulb-fill"},
        ],
    },
    {
        "id": "q4_learning_pref",
        "question": "학습할 때 더 끌리는 것은?",
        "dimension": "SN",
        "options": [
            {"value": "S", "text": "실용적이고 바로 써먹을 수 있는 것", "icon": "bi-tools"},
            {"value": "N", "text": "이론적이고 새로운 가능성 탐구", "icon": "bi-stars"},
        ],
    },
    {
        "id": "q5_decision",
        "question": "결정을 내릴 때 중요한 것은?",
        "dimension": "TF",
        "options": [
            {"value": "T", "text": "논리적 분석과 객관적 기준", "icon": "bi-calculator"},
            {"value": "F", "text": "가치관과 주변 사람들의 감정", "icon": "bi-heart-fill"},
        ],
    },
    {
        "id": "q6_feedback",
        "question": "피드백을 받을 때 선호하는 방식은?",
        "dimension": "TF",
        "options": [
            {"value": "T", "text": "직접적이고 논리적인 비판", "icon": "bi-chat-square-text"},
            {"value": "F", "text": "격려와 함께 부드러운 제안", "icon": "bi-emoji-smile"},
        ],
    },
    {
        "id": "q7_schedule",
        "question": "일정을 관리하는 스타일은?",
        "dimension": "JP",
        "options": [
            {"value": "J", "text": "미리 계획하고 체계적으로", "icon": "bi-calendar-check"},
            {"value": "P", "text": "유연하게 상황에 따라", "icon": "bi-shuffle"},
        ],
    },
    {
        "id": "q8_deadline",
        "question": "마감을 대하는 태도는?",
        "dimension": "JP",
        "options": [
            {"value": "J", "text": "일찍 끝내고 여유 갖기", "icon": "bi-check2-circle"},
            {"value": "P", "text": "마감 직전에 집중력 폭발", "icon": "bi-lightning-charge-fill"},
        ],
    },
]


def calculate_mbti_from_survey(answers: Dict[str, str]) -> str:
    """설문 답변에서 MBTI 유형 계산"""
    dimensions = {"E": 0, "I": 0, "S": 0, "N": 0, "T": 0, "F": 0, "J": 0, "P": 0}

    for q in SURVEY_QUESTIONS:
        answer = answers.get(q["id"])
        if answer:
            dimensions[answer] += 1

    mbti = ""
    mbti += "E" if dimensions["E"] >= dimensions["I"] else "I"
    mbti += "S" if dimensions["S"] >= dimensions["N"] else "N"
    mbti += "T" if dimensions["T"] >= dimensions["F"] else "F"
    mbti += "J" if dimensions["J"] >= dimensions["P"] else "P"

    return mbti
