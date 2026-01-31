"""
AI 추천 API 라우터 (고도화 버전)
- XGBoost 기반 예측
- Multi-Armed Bandit 최적화
- 골든타임 분석
- 적응형 난이도
"""

from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime
from typing import Optional

from models.schemas import RecommendationRequest, RecommendationResponse, TaskType
from services.advanced_recommender import (
    get_advanced_recommender,
    train_advanced_models,
    AdvancedAIRecommender,
)
from routers.auth import get_current_user
from routers.sessions import sessions_db

router = APIRouter(prefix="/recommendation", tags=["Recommendation"])


@router.post("", response_model=RecommendationResponse)
async def get_recommendation(
    request: RecommendationRequest,
    user: dict = Depends(get_current_user),
):
    """
    AI 기반 세션 추천 (고도화 버전)

    - XGBoost 완주 확률 예측
    - Thompson Sampling으로 최적 전략 선택
    - 페르소나 기반 개인화
    """
    # 최근 세션 가져오기 (최대 20개)
    user_sessions = [
        s for s in sessions_db.values()
        if s["user_id"] == user["user_id"] and s["status"] is not None
    ]
    user_sessions.sort(key=lambda x: x["created_at"], reverse=True)
    recent_sessions = user_sessions[:20]

    # 고도화된 AI 추천 엔진 사용
    recommender = get_advanced_recommender()
    recommendation = recommender.get_recommendation(
        recent_sessions=recent_sessions,
        task_type=request.task_type,
        difficulty=request.difficulty,
        hour=request.hour,
        day_of_week=request.day_of_week,
    )

    return recommendation


@router.get("/quick", response_model=RecommendationResponse)
async def get_quick_recommendation(
    user: dict = Depends(get_current_user),
):
    """
    빠른 추천 (현재 시간 기준)
    """
    now = datetime.now()

    # 최근 세션 가져오기
    user_sessions = [
        s for s in sessions_db.values()
        if s["user_id"] == user["user_id"] and s["status"] is not None
    ]
    user_sessions.sort(key=lambda x: x["created_at"], reverse=True)
    recent_sessions = user_sessions[:20]

    # 고도화된 AI 추천 엔진 사용
    recommender = get_advanced_recommender()
    recommendation = recommender.get_recommendation(
        recent_sessions=recent_sessions,
        task_type=TaskType.READING,
        difficulty=3,
        hour=now.hour,
        day_of_week=now.weekday(),
    )

    return recommendation


@router.post("/train")
async def train_ai_model(force: bool = False):
    """
    AI 모델 학습 (관리자용)

    - 100,000개 세션 데이터 생성
    - XGBoost 모델 학습
    - Multi-Armed Bandit 초기화
    """
    try:
        recommender = get_advanced_recommender()
        result = recommender.train(force_retrain=force)
        return {
            "status": result.get("status", "success"),
            "message": "Advanced AI models trained successfully",
            "details": result,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Training failed: {str(e)}")


@router.get("/model-info")
async def get_model_info():
    """
    현재 모델 정보 조회
    """
    recommender = get_advanced_recommender()

    return {
        "is_trained": recommender.is_trained,
        "feature_count": len(recommender.feature_names),
        "features": recommender.feature_names,
        "mab_stats": recommender.mab.get_stats(),
        "feature_importance": recommender.get_feature_importance(),
    }


@router.post("/feedback")
async def submit_feedback(
    session_id: str,
    focus_minutes: int,
    break_minutes: int,
    rounds: int,
    completed: bool,
    user: dict = Depends(get_current_user),
):
    """
    세션 결과 피드백 (MAB 업데이트)

    세션 완료 후 호출하여 추천 시스템 개선
    """
    recommender = get_advanced_recommender()
    recommender.update_mab(focus_minutes, break_minutes, rounds, completed)

    # 골든타임 업데이트
    now = datetime.now()
    recommender.golden_time.update(now.hour, now.weekday(), completed)

    # 적응형 난이도 업데이트
    session = sessions_db.get(session_id)
    if session:
        difficulty = session.get("difficulty", 3)
        recommender.adaptive_difficulty.update(difficulty, completed)

    return {
        "status": "success",
        "message": "Feedback recorded",
        "updated_arm": f"{focus_minutes}_{break_minutes}_{rounds}",
    }


@router.get("/golden-time")
async def get_golden_time(
    user: dict = Depends(get_current_user),
):
    """
    사용자의 골든타임 분석
    """
    # 사용자 세션에서 골든타임 분석
    user_sessions = [
        s for s in sessions_db.values()
        if s["user_id"] == user["user_id"] and s["status"] is not None
    ]

    if not user_sessions:
        return {
            "golden_hours": [],
            "best_day": None,
            "message": "아직 세션 데이터가 부족해요. 더 많은 세션을 완료하면 분석이 가능해요!",
        }

    from services.advanced_recommender import GoldenTimeAnalyzer

    analyzer = GoldenTimeAnalyzer()
    for s in user_sessions:
        analyzer.update(
            s.get("start_hour", 12),
            s.get("day_of_week", 0),
            s.get("status") == "completed"
        )

    return analyzer.get_analysis()


@router.get("/persona/{user_id}")
async def get_user_persona(
    user_id: str,
    user: dict = Depends(get_current_user),
):
    """
    사용자 페르소나 분석

    - 최근 세션 데이터 기반
    - 8가지 페르소나 중 분류
    """
    user_sessions = [
        s for s in sessions_db.values()
        if s["user_id"] == user_id and s["status"] is not None
    ]

    if not user_sessions:
        return {
            "persona_type": "casual_learner",
            "persona_name": "가벼운 학습자",
            "description": "아직 데이터가 부족해요. 몇 번 더 세션을 진행하면 더 정확한 분석이 가능해요!",
            "confidence": 0.0,
        }

    user_sessions.sort(key=lambda x: x["created_at"], reverse=True)
    recent_sessions = user_sessions[:20]

    # 분석
    completion_rate = sum(1 for s in recent_sessions if s.get("status") == "completed") / len(recent_sessions)
    focus_times = [s.get("total_focus_sec", 0) / 60 for s in recent_sessions]
    avg_focus = sum(focus_times) / len(focus_times) if focus_times else 25

    abort_counts = {}
    for s in recent_sessions:
        reason = s.get("abort_reason")
        if reason:
            abort_counts[reason] = abort_counts.get(reason, 0) + 1
    top_abort = max(abort_counts, key=abort_counts.get) if abort_counts else "phone"

    active_hours = [s.get("start_hour", 12) for s in recent_sessions]

    from data.personas import classify_user_persona, get_persona_profile

    persona_type = classify_user_persona(
        completion_rate, avg_focus, top_abort, active_hours
    )
    profile = get_persona_profile(persona_type)

    return {
        "persona_type": persona_type.value,
        "persona_name": profile["name"],
        "description": profile["description"],
        "completion_rate": round(completion_rate, 2),
        "avg_focus_minutes": round(avg_focus, 1),
        "top_abort_reason": top_abort,
        "confidence": min(1.0, len(recent_sessions) / 20),
        "tips": profile.get("tips", []),
    }


@router.get("/adaptive-difficulty")
async def get_adaptive_difficulty(
    task_type: str = "reading",
    focus_minutes: int = 25,
    user: dict = Depends(get_current_user),
):
    """
    적응형 난이도 추천
    """
    now = datetime.now()

    # 사용자 완주율
    user_sessions = [
        s for s in sessions_db.values()
        if s["user_id"] == user["user_id"] and s["status"] is not None
    ]

    completion_rate = 0.7
    if user_sessions:
        recent = user_sessions[-20:]
        completion_rate = sum(1 for s in recent if s.get("status") == "completed") / len(recent)

    from services.advanced_recommender import AdaptiveDifficultySystem

    system = AdaptiveDifficultySystem()

    # 이전 결과로 시스템 워밍업
    for s in user_sessions[-10:]:
        system.update(
            s.get("difficulty", 3),
            s.get("status") == "completed"
        )

    recommended = system.get_recommended_difficulty()
    objective = system.get_objective_difficulty(
        task_type, focus_minutes, now.hour, completion_rate
    )

    return {
        "recommended_difficulty": recommended,
        "objective_difficulty_score": round(objective, 2),
        "user_completion_rate": round(completion_rate, 2),
        "explanation": get_difficulty_explanation(recommended, objective),
    }


def get_difficulty_explanation(recommended: int, objective: float) -> str:
    """난이도 추천 설명 생성"""
    if objective < 4:
        return f"현재 상황은 집중하기 좋은 환경이에요. 난이도 {recommended}을 추천해요!"
    elif objective < 6:
        return f"적당한 도전 수준이에요. 난이도 {recommended}으로 시작해보세요."
    elif objective < 8:
        return f"조금 어려운 상황이에요. 난이도 {recommended}으로 천천히 시작해보세요."
    else:
        return f"힘든 상황이에요. 짧은 집중과 낮은 난이도 {recommended}으로 시작해요!"
