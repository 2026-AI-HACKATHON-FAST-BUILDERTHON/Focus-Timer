"""
AI 기반 추천 엔진
- 사용자 데이터 기반 개인화 추천
- ML 모델을 활용한 최적 집중 시간 예측
- 중단 위험도 예측
"""

import numpy as np
from typing import List, Dict, Optional, Tuple
from sklearn.ensemble import RandomForestClassifier, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
import pickle
import os
import json

from data.personas import PersonaType, classify_user_persona, get_persona_profile
from data.data_generator import generate_dataset, generate_training_features
from models.schemas import TaskType, LoopPhase, RecommendationResponse


class AIRecommender:
    """
    AI 기반 개인화 추천 시스템

    1. 사용자 페르소나 분류
    2. 완주 확률 예측 (Classification)
    3. 최적 집중 시간 추천 (Regression)
    4. 중단 위험도 예측
    """

    def __init__(self, model_path: str = "models/trained"):
        self.model_path = model_path
        self.completion_model: Optional[RandomForestClassifier] = None
        self.focus_time_model: Optional[GradientBoostingRegressor] = None
        self.scaler: Optional[StandardScaler] = None
        self.is_trained = False

        # 모델 로드 시도
        self._load_models()

    def _load_models(self):
        """저장된 모델 로드"""
        try:
            if os.path.exists(f"{self.model_path}/completion_model.pkl"):
                with open(f"{self.model_path}/completion_model.pkl", "rb") as f:
                    self.completion_model = pickle.load(f)
                with open(f"{self.model_path}/focus_time_model.pkl", "rb") as f:
                    self.focus_time_model = pickle.load(f)
                with open(f"{self.model_path}/scaler.pkl", "rb") as f:
                    self.scaler = pickle.load(f)
                self.is_trained = True
                print("AI models loaded successfully")
        except Exception as e:
            print(f"Model loading failed: {e}")
            self.is_trained = False

    def train(self, force_retrain: bool = False):
        """
        모델 학습

        1. 더미 데이터 생성
        2. 피처 엔지니어링
        3. 모델 학습
        4. 모델 저장
        """
        if self.is_trained and not force_retrain:
            print("Models already trained. Use force_retrain=True to retrain.")
            return

        print("Generating training data...")
        users, sessions = generate_dataset(
            num_users_per_persona=15,
            sessions_per_user=50,
            days_span=90,
        )

        print("Extracting features...")
        features = generate_training_features(sessions)

        # 피처 준비
        X = []
        y_completion = []
        y_focus = []

        for f in features:
            x = [
                f["start_hour"],
                f["day_of_week"],
                f["task_type_reading"],
                f["task_type_practice"],
                f["task_type_creation"],
                f["task_type_routine"],
                f["difficulty"],
                f["planned_focus_minutes"],
                f["planned_break_minutes"],
            ]
            X.append(x)
            y_completion.append(f["completed"])
            y_focus.append(f["planned_focus_minutes"] if f["completed"] else f["planned_focus_minutes"] * 0.7)

        X = np.array(X)
        y_completion = np.array(y_completion)
        y_focus = np.array(y_focus)

        # 스케일링
        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(X)

        # 완주 예측 모델 학습
        print("Training completion prediction model...")
        self.completion_model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42,
        )
        self.completion_model.fit(X_scaled, y_completion)

        # 최적 집중 시간 예측 모델 학습
        print("Training focus time recommendation model...")
        self.focus_time_model = GradientBoostingRegressor(
            n_estimators=100,
            max_depth=5,
            random_state=42,
        )
        self.focus_time_model.fit(X_scaled, y_focus)

        # 모델 저장
        os.makedirs(self.model_path, exist_ok=True)
        with open(f"{self.model_path}/completion_model.pkl", "wb") as f:
            pickle.dump(self.completion_model, f)
        with open(f"{self.model_path}/focus_time_model.pkl", "wb") as f:
            pickle.dump(self.focus_time_model, f)
        with open(f"{self.model_path}/scaler.pkl", "wb") as f:
            pickle.dump(self.scaler, f)

        self.is_trained = True
        print("Training complete! Models saved.")

    def _prepare_features(
        self,
        task_type: TaskType,
        difficulty: int,
        hour: int,
        day_of_week: int,
        focus_minutes: int = 25,
        break_minutes: int = 5,
    ) -> np.ndarray:
        """입력 데이터를 피처 벡터로 변환"""
        x = [
            hour,
            day_of_week,
            1 if task_type == TaskType.READING else 0,
            1 if task_type == TaskType.PRACTICE else 0,
            1 if task_type == TaskType.CREATION else 0,
            1 if task_type == TaskType.ROUTINE else 0,
            difficulty,
            focus_minutes,
            break_minutes,
        ]
        return np.array(x).reshape(1, -1)

    def predict_completion_probability(
        self,
        task_type: TaskType,
        difficulty: int,
        hour: int,
        day_of_week: int,
        focus_minutes: int,
        break_minutes: int,
    ) -> float:
        """완주 확률 예측"""
        if not self.is_trained:
            # 훈련되지 않은 경우 휴리스틱 사용
            return self._heuristic_completion_prob(
                task_type, difficulty, hour, focus_minutes
            )

        X = self._prepare_features(
            task_type, difficulty, hour, day_of_week, focus_minutes, break_minutes
        )
        X_scaled = self.scaler.transform(X)
        prob = self.completion_model.predict_proba(X_scaled)[0][1]
        return round(float(prob), 2)

    def recommend_focus_time(
        self,
        task_type: TaskType,
        difficulty: int,
        hour: int,
        day_of_week: int,
        user_history: Optional[List[Dict]] = None,
    ) -> int:
        """최적 집중 시간 추천"""
        if not self.is_trained:
            # 훈련되지 않은 경우 휴리스틱 사용
            return self._heuristic_focus_time(task_type, difficulty, hour)

        # 다양한 집중 시간에 대해 예측하고 최적 시간 선택
        best_focus = 25
        best_prob = 0

        for focus_time in range(10, 45, 5):
            X = self._prepare_features(
                task_type, difficulty, hour, day_of_week, focus_time, 5
            )
            X_scaled = self.scaler.transform(X)
            prob = self.completion_model.predict_proba(X_scaled)[0][1]

            # 완주 확률이 높으면서 적당히 긴 시간 선호
            adjusted_score = prob * (1 + focus_time / 100)

            if adjusted_score > best_prob:
                best_prob = adjusted_score
                best_focus = focus_time

        return best_focus

    def get_recommendation(
        self,
        recent_sessions: List[Dict],
        task_type: TaskType,
        difficulty: int,
        hour: int,
        day_of_week: int,
    ) -> RecommendationResponse:
        """
        종합 추천 생성

        1. 사용자 페르소나 분류
        2. 최적 집중 시간 추천
        3. 완주 확률 예측
        4. 리스크 레벨 결정
        5. 마이크로 루틴 제안
        """

        # 사용자 패턴 분석
        user_persona = None
        if recent_sessions:
            completion_rate = sum(1 for s in recent_sessions if s.get("status") == "completed") / len(recent_sessions)
            focus_times = [s.get("total_focus_sec", 0) / 60 for s in recent_sessions]
            avg_focus = sum(focus_times) / len(focus_times) if focus_times else 25

            # 주요 중단 사유
            abort_counts = {}
            for s in recent_sessions:
                reason = s.get("abort_reason")
                if reason:
                    abort_counts[reason] = abort_counts.get(reason, 0) + 1
            top_abort = max(abort_counts, key=abort_counts.get) if abort_counts else "phone"

            # 활동 시간대
            active_hours = [s.get("start_hour", 12) for s in recent_sessions]

            user_persona = classify_user_persona(
                completion_rate, avg_focus, top_abort, active_hours
            )
        else:
            completion_rate = 0.7
            avg_focus = 25
            top_abort = None
            user_persona = PersonaType.CASUAL_LEARNER

        # 페르소나 기반 추천 조정
        persona_profile = get_persona_profile(user_persona)

        # AI 기반 추천
        recommended_focus = self.recommend_focus_time(
            task_type, difficulty, hour, day_of_week, recent_sessions
        )

        # 페르소나 선호도와 AI 추천 결합
        focus_min = (recommended_focus + persona_profile["preferred_focus_min"]) // 2
        focus_min = max(10, min(45, focus_min))

        # 휴식 시간 (집중 시간의 1/5, 최소 3분)
        break_min = max(3, focus_min // 5)

        # 완주 확률 예측
        completion_prob = self.predict_completion_probability(
            task_type, difficulty, hour, day_of_week, focus_min, break_min
        )

        # 리스크 레벨
        if completion_prob < 0.5:
            risk_level = "high"
        elif completion_prob < 0.7:
            risk_level = "medium"
        else:
            risk_level = "low"

        # 라운드 수 (낮은 완주 확률 = 적은 라운드)
        rounds = 4 if completion_prob > 0.7 else (3 if completion_prob > 0.5 else 2)

        # 마이크로 루틴 제안
        micro_routine = None
        if top_abort == "phone":
            micro_routine = "시작 전 스마트폰을 다른 방에 두세요. 첫 2분은 화면만 바라보기!"
        elif top_abort == "tired":
            micro_routine = "시작 전 1분 스트레칭으로 몸을 깨워주세요!"
        elif top_abort == "anxious":
            micro_routine = "시작 전 심호흡 3번! 긴장을 풀고 시작해요."
        elif top_abort == "bored":
            micro_routine = "오늘의 작은 목표를 하나 정해보세요. 성취감이 집중력을 높여요!"

        # 추천 근거 생성
        reasons = []
        reasons.append(f"당신의 패턴을 분석한 결과, {persona_profile['name']} 유형이에요.")
        reasons.append(f"AI가 예측한 완주 확률은 {int(completion_prob * 100)}%입니다.")

        if completion_prob < 0.6:
            reasons.append(f"짧은 {focus_min}분 집중으로 성공 경험을 쌓아보세요!")

        # 루프 생성
        loop = []
        for i in range(rounds):
            loop.append(LoopPhase(type="focus", minutes=focus_min))
            if i < rounds - 1:
                loop.append(LoopPhase(type="break", minutes=break_min))

        return RecommendationResponse(
            recommended_loop=loop,
            predicted_completion_prob=completion_prob,
            reason=" ".join(reasons[:2]),
            risk_level=risk_level,
            micro_routine=micro_routine,
            persona_type=user_persona.value if user_persona else None,
        )

    def _heuristic_completion_prob(
        self,
        task_type: TaskType,
        difficulty: int,
        hour: int,
        focus_minutes: int,
    ) -> float:
        """훈련되지 않은 경우 휴리스틱 기반 완주 확률"""
        prob = 0.7

        if focus_minutes <= 15:
            prob += 0.1
        elif focus_minutes >= 30:
            prob -= 0.1

        if difficulty >= 4:
            prob -= 0.15
        elif difficulty <= 2:
            prob += 0.05

        if 22 <= hour or hour <= 2:
            prob -= 0.1

        return max(0.3, min(0.95, prob))

    def _heuristic_focus_time(
        self,
        task_type: TaskType,
        difficulty: int,
        hour: int,
    ) -> int:
        """훈련되지 않은 경우 휴리스틱 기반 집중 시간 추천"""
        base = 25

        if difficulty >= 4:
            base = 15
        elif difficulty <= 2:
            base = 30

        if 22 <= hour or hour <= 2:
            base = min(base, 15)

        if task_type == TaskType.CREATION:
            base = min(base + 5, 35)
        elif task_type == TaskType.ROUTINE:
            base = max(base - 5, 15)

        return base


# 싱글톤 인스턴스
_ai_recommender: Optional[AIRecommender] = None


def get_ai_recommender() -> AIRecommender:
    """AI 추천 엔진 인스턴스 반환"""
    global _ai_recommender
    if _ai_recommender is None:
        _ai_recommender = AIRecommender()
    return _ai_recommender


def train_models():
    """모델 학습 실행"""
    recommender = get_ai_recommender()
    recommender.train(force_retrain=True)


if __name__ == "__main__":
    train_models()
