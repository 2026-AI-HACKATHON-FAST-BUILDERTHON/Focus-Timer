"""
MBTI 및 학습 성향 설문 API
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, List, Optional
from pydantic import BaseModel
from datetime import datetime

from data.mbti_profiles import (
    SURVEY_QUESTIONS,
    MBTI_PROFILES,
    calculate_mbti_from_survey,
    get_combined_profile,
    calculate_optimal_settings,
)
from routers.auth import get_current_user

router = APIRouter(prefix="/survey", tags=["Survey"])

# In-memory 저장소 (실제로는 DB 사용)
user_survey_db: Dict[str, Dict] = {}


class SurveyAnswers(BaseModel):
    answers: Dict[str, str]


class SurveyResult(BaseModel):
    mbti_type: str
    profile: Dict
    optimal_settings: Dict
    completed_at: str


@router.get("/questions")
async def get_survey_questions():
    """
    설문 질문 목록 조회
    """
    return {
        "total_questions": len(SURVEY_QUESTIONS),
        "questions": SURVEY_QUESTIONS,
    }


@router.post("/submit", response_model=SurveyResult)
async def submit_survey(
    survey: SurveyAnswers,
    user: dict = Depends(get_current_user),
):
    """
    설문 제출 및 MBTI 분석
    """
    user_id = user["user_id"]

    # MBTI 계산
    mbti_type = calculate_mbti_from_survey(survey.answers)

    if mbti_type not in MBTI_PROFILES:
        raise HTTPException(status_code=400, detail="Invalid survey answers")

    # 프로필 조회
    profile = get_combined_profile(mbti_type)

    # 최적 설정 계산
    optimal_settings = calculate_optimal_settings(mbti_type)

    # 저장
    now = datetime.now().isoformat()
    user_survey_db[user_id] = {
        "mbti_type": mbti_type,
        "answers": survey.answers,
        "completed_at": now,
    }

    return SurveyResult(
        mbti_type=mbti_type,
        profile=profile,
        optimal_settings=optimal_settings,
        completed_at=now,
    )


@router.get("/result")
async def get_survey_result(
    user: dict = Depends(get_current_user),
):
    """
    저장된 설문 결과 조회
    """
    user_id = user["user_id"]

    if user_id not in user_survey_db:
        return {
            "has_result": False,
            "message": "설문을 완료해주세요",
        }

    data = user_survey_db[user_id]
    mbti_type = data["mbti_type"]
    profile = get_combined_profile(mbti_type)
    optimal_settings = calculate_optimal_settings(mbti_type)

    return {
        "has_result": True,
        "mbti_type": mbti_type,
        "profile": profile,
        "optimal_settings": optimal_settings,
        "completed_at": data["completed_at"],
    }


@router.get("/mbti/{mbti_type}")
async def get_mbti_profile(mbti_type: str):
    """
    특정 MBTI 유형 프로필 조회
    """
    mbti_type = mbti_type.upper()

    if mbti_type not in MBTI_PROFILES:
        raise HTTPException(status_code=404, detail="Invalid MBTI type")

    profile = get_combined_profile(mbti_type)
    optimal_settings = calculate_optimal_settings(mbti_type)

    return {
        "mbti_type": mbti_type,
        "profile": profile,
        "optimal_settings": optimal_settings,
    }


@router.delete("/reset")
async def reset_survey(
    user: dict = Depends(get_current_user),
):
    """
    설문 결과 초기화 (재설문 위해)
    """
    user_id = user["user_id"]

    if user_id in user_survey_db:
        del user_survey_db[user_id]

    return {
        "status": "success",
        "message": "설문이 초기화되었습니다. 다시 설문을 진행해주세요.",
    }


@router.get("/all-types")
async def get_all_mbti_types():
    """
    모든 MBTI 유형 목록 (간략 정보)
    """
    return {
        "types": [
            {
                "code": code,
                "name": profile.name,
                "nickname": profile.nickname,
                "completion_tendency": profile.completion_tendency,
            }
            for code, profile in MBTI_PROFILES.items()
        ]
    }
