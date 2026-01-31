"""
고도화된 AI 추천 엔진
- XGBoost 기반 예측 모델
- Multi-Armed Bandit (Thompson Sampling) 최적화
- 적응형 난이도 시스템
- 골든타임 분석
"""

import numpy as np
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import pickle
import os
import json
from datetime import datetime, timedelta
import random

try:
    from xgboost import XGBClassifier, XGBRegressor
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False
    print("Warning: XGBoost not available, using fallback")

from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, mean_squared_error

from data.personas import PersonaType, classify_user_persona, get_persona_profile
from data.enhanced_generator import generate_large_dataset, extract_training_features
from models.schemas import TaskType, LoopPhase, RecommendationResponse


@dataclass
class MABArm:
    """Multi-Armed Bandit의 각 Arm (추천 전략)"""
    focus_minutes: int
    break_minutes: int
    rounds: int
    # Beta 분포 파라미터 (Thompson Sampling)
    alpha: float = 1.0  # 성공 횟수 + 1
    beta: float = 1.0   # 실패 횟수 + 1

    def sample(self) -> float:
        """Thompson Sampling: Beta 분포에서 샘플링"""
        return np.random.beta(self.alpha, self.beta)

    def update(self, success: bool):
        """결과에 따라 파라미터 업데이트"""
        if success:
            self.alpha += 1
        else:
            self.beta += 1

    @property
    def expected_value(self) -> float:
        """기대값 (평균 성공률)"""
        return self.alpha / (self.alpha + self.beta)


class ThompsonSamplingMAB:
    """
    Thompson Sampling Multi-Armed Bandit
    - 각 추천 전략의 성공률을 학습
    - 탐색(exploration)과 활용(exploitation) 균형
    """

    def __init__(self):
        # 다양한 집중 시간 전략 (10분 ~ 45분)
        self.arms: Dict[str, MABArm] = {}
        for focus in [10, 15, 20, 25, 30, 35, 40, 45]:
            for break_time in [3, 5, 7]:
                for rounds in [2, 3, 4, 5]:
                    key = f"{focus}_{break_time}_{rounds}"
                    self.arms[key] = MABArm(
                        focus_minutes=focus,
                        break_minutes=break_time,
                        rounds=rounds,
                    )

    def select_arm(self, context: Dict = None) -> MABArm:
        """
        Thompson Sampling으로 최적 전략 선택

        context: 컨텍스트 정보 (난이도, 시간대 등)
        """
        # 컨텍스트에 따른 필터링
        valid_arms = list(self.arms.values())

        if context:
            difficulty = context.get("difficulty", 3)
            hour = context.get("hour", 12)

            # 난이도 높으면 짧은 집중 시간 선호
            if difficulty >= 4:
                valid_arms = [a for a in valid_arms if a.focus_minutes <= 25]
            elif difficulty <= 2:
                valid_arms = [a for a in valid_arms if a.focus_minutes >= 20]

            # 밤 시간대는 짧은 집중 시간
            if hour >= 22 or hour <= 2:
                valid_arms = [a for a in valid_arms if a.focus_minutes <= 20]

        if not valid_arms:
            valid_arms = list(self.arms.values())

        # Thompson Sampling
        samples = [(arm, arm.sample()) for arm in valid_arms]
        best_arm = max(samples, key=lambda x: x[1])[0]

        return best_arm

    def update(self, arm_key: str, success: bool):
        """결과 업데이트"""
        if arm_key in self.arms:
            self.arms[arm_key].update(success)

    def get_stats(self) -> Dict:
        """통계 정보"""
        return {
            key: {
                "focus": arm.focus_minutes,
                "break": arm.break_minutes,
                "rounds": arm.rounds,
                "expected_success_rate": round(arm.expected_value, 3),
                "total_trials": int(arm.alpha + arm.beta - 2),
            }
            for key, arm in sorted(
                self.arms.items(),
                key=lambda x: x[1].expected_value,
                reverse=True
            )[:10]  # Top 10
        }

    def save(self, path: str):
        """저장"""
        data = {
            key: {"alpha": arm.alpha, "beta": arm.beta}
            for key, arm in self.arms.items()
        }
        with open(path, "w") as f:
            json.dump(data, f)

    def load(self, path: str):
        """로드"""
        if os.path.exists(path):
            with open(path, "r") as f:
                data = json.load(f)
            for key, params in data.items():
                if key in self.arms:
                    self.arms[key].alpha = params["alpha"]
                    self.arms[key].beta = params["beta"]


class GoldenTimeAnalyzer:
    """
    골든타임 분석기
    - 사용자별 최적 집중 시간대 분석
    - 요일별 패턴 분석
    """

    def __init__(self):
        self.hourly_stats: Dict[int, Dict] = {
            h: {"success": 0, "total": 0} for h in range(24)
        }
        self.daily_stats: Dict[int, Dict] = {
            d: {"success": 0, "total": 0} for d in range(7)
        }

    def update(self, hour: int, day: int, success: bool):
        """통계 업데이트"""
        self.hourly_stats[hour]["total"] += 1
        self.daily_stats[day]["total"] += 1
        if success:
            self.hourly_stats[hour]["success"] += 1
            self.daily_stats[day]["success"] += 1

    def get_golden_hours(self, top_n: int = 3) -> List[int]:
        """최적 시간대 반환"""
        rates = []
        for hour, stats in self.hourly_stats.items():
            if stats["total"] >= 3:  # 최소 3회 이상
                rate = stats["success"] / stats["total"]
                rates.append((hour, rate, stats["total"]))

        rates.sort(key=lambda x: (x[1], x[2]), reverse=True)
        return [h for h, _, _ in rates[:top_n]]

    def get_best_day(self) -> Optional[int]:
        """가장 좋은 요일"""
        best_day = None
        best_rate = 0
        for day, stats in self.daily_stats.items():
            if stats["total"] >= 3:
                rate = stats["success"] / stats["total"]
                if rate > best_rate:
                    best_rate = rate
                    best_day = day
        return best_day

    def get_analysis(self) -> Dict:
        """분석 결과"""
        golden_hours = self.get_golden_hours()
        best_day = self.get_best_day()

        day_names = ["월", "화", "수", "목", "금", "토", "일"]

        return {
            "golden_hours": golden_hours,
            "golden_hours_text": [f"{h}시" for h in golden_hours],
            "best_day": best_day,
            "best_day_text": day_names[best_day] if best_day is not None else None,
            "hourly_rates": {
                h: round(s["success"] / s["total"], 2) if s["total"] > 0 else 0
                for h, s in self.hourly_stats.items()
            },
        }


class AdaptiveDifficultySystem:
    """
    적응형 난이도 시스템
    - 사용자 성과에 따른 자동 난이도 조정
    - 객관적 난이도 점수 산출
    """

    def __init__(self):
        self.difficulty_history: List[Tuple[int, bool]] = []
        self.optimal_difficulty = 3.0

    def update(self, difficulty: int, success: bool):
        """결과 업데이트"""
        self.difficulty_history.append((difficulty, success))

        # 최근 10개 결과로 최적 난이도 계산
        recent = self.difficulty_history[-10:]
        if len(recent) >= 5:
            # 성공한 세션들의 평균 난이도
            success_difficulties = [d for d, s in recent if s]
            if success_difficulties:
                avg_success = sum(success_difficulties) / len(success_difficulties)

                # 성공률
                success_rate = sum(1 for _, s in recent if s) / len(recent)

                # 최적 난이도 조정
                if success_rate > 0.8:
                    # 너무 쉬움 -> 난이도 상향
                    self.optimal_difficulty = min(5, avg_success + 0.5)
                elif success_rate < 0.5:
                    # 너무 어려움 -> 난이도 하향
                    self.optimal_difficulty = max(1, avg_success - 0.5)
                else:
                    self.optimal_difficulty = avg_success

    def get_recommended_difficulty(self) -> int:
        """추천 난이도"""
        return round(self.optimal_difficulty)

    def get_objective_difficulty(
        self,
        task_type: str,
        focus_minutes: int,
        hour: int,
        user_completion_rate: float,
    ) -> float:
        """
        객관적 난이도 점수 산출 (0-10)
        """
        score = 5.0  # 기본값

        # 집중 시간 영향
        score += (focus_minutes - 25) * 0.1

        # 시간대 영향
        if 22 <= hour or hour <= 2:
            score += 1.5
        elif 5 <= hour <= 8:
            score -= 0.5

        # 과제 유형 영향
        type_modifier = {
            "reading": 0,
            "practice": 0.5,
            "creation": 1.0,
            "routine": -0.5,
        }
        score += type_modifier.get(task_type, 0)

        # 사용자 완주율 반영
        if user_completion_rate < 0.5:
            score += 1.0
        elif user_completion_rate > 0.8:
            score -= 1.0

        return max(0, min(10, score))


class AdvancedAIRecommender:
    """
    고도화된 AI 추천 시스템

    구성요소:
    1. XGBoost 예측 모델 (완주 확률, 최적 집중 시간)
    2. Multi-Armed Bandit (추천 전략 최적화)
    3. 골든타임 분석기
    4. 적응형 난이도 시스템
    """

    def __init__(self, model_path: str = "models/advanced"):
        self.model_path = model_path
        self.completion_model = None
        self.focus_time_model = None
        self.scaler = None
        self.mab = ThompsonSamplingMAB()
        self.golden_time = GoldenTimeAnalyzer()
        self.adaptive_difficulty = AdaptiveDifficultySystem()
        self.is_trained = False
        self.feature_names = []

        self._load_models()

    def _load_models(self):
        """모델 로드"""
        try:
            if os.path.exists(f"{self.model_path}/completion_model.pkl"):
                with open(f"{self.model_path}/completion_model.pkl", "rb") as f:
                    self.completion_model = pickle.load(f)
                with open(f"{self.model_path}/focus_time_model.pkl", "rb") as f:
                    self.focus_time_model = pickle.load(f)
                with open(f"{self.model_path}/scaler.pkl", "rb") as f:
                    self.scaler = pickle.load(f)
                with open(f"{self.model_path}/feature_names.json", "r") as f:
                    self.feature_names = json.load(f)

                self.mab.load(f"{self.model_path}/mab_state.json")
                self.is_trained = True
                print("Advanced AI models loaded successfully")
        except Exception as e:
            print(f"Model loading failed: {e}")
            self.is_trained = False

    def train(self, force_retrain: bool = False):
        """
        모델 학습

        1. 대규모 데이터 생성 (100,000 세션)
        2. 피처 엔지니어링
        3. XGBoost 모델 학습
        4. 모델 저장
        """
        if self.is_trained and not force_retrain:
            print("Models already trained. Use force_retrain=True to retrain.")
            return {"status": "already_trained"}

        print("=" * 50)
        print("Starting Advanced AI Training")
        print("=" * 50)

        # 1. 데이터 생성
        print("\n[1/5] Generating training data (100,000 sessions)...")
        users, sessions = generate_large_dataset(
            users_per_persona=500,
            sessions_per_user=25,
        )

        # 2. 피처 추출
        print("\n[2/5] Extracting features...")
        features = extract_training_features(sessions)

        # 피처 이름 저장
        self.feature_names = [
            "start_hour", "day_of_week", "is_weekend",
            "task_type_reading", "task_type_practice",
            "task_type_creation", "task_type_routine",
            "difficulty", "planned_focus_minutes",
            "planned_break_minutes", "planned_rounds",
            "sessions_today", "sessions_this_week", "streak_days",
            "last_session_hours_ago", "same_hour_completion_rate",
            "same_task_completion_rate", "recent_7day_completion_rate",
            "recent_7day_avg_focus", "fatigue_score", "momentum_score",
            "is_morning", "is_afternoon", "is_evening", "is_night",
        ]

        # 피처 배열 준비
        X = []
        y_completion = []
        y_focus = []

        for f in features:
            x = [f.get(name, 0) for name in self.feature_names]
            X.append(x)
            y_completion.append(f["completed"])
            # 완료된 경우 실제 집중 시간, 아니면 계획의 70%
            y_focus.append(
                f["total_focus_minutes"] if f["completed"]
                else f["planned_focus_minutes"] * 0.7
            )

        X = np.array(X)
        y_completion = np.array(y_completion)
        y_focus = np.array(y_focus)

        # 학습/테스트 분할
        X_train, X_test, y_comp_train, y_comp_test = train_test_split(
            X, y_completion, test_size=0.2, random_state=42
        )
        _, _, y_focus_train, y_focus_test = train_test_split(
            X, y_focus, test_size=0.2, random_state=42
        )

        # 3. 스케일링
        print("\n[3/5] Scaling features...")
        self.scaler = StandardScaler()
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)

        # 4. XGBoost 모델 학습
        print("\n[4/5] Training XGBoost models...")

        if XGBOOST_AVAILABLE:
            # 완주 예측 모델
            self.completion_model = XGBClassifier(
                n_estimators=200,
                max_depth=8,
                learning_rate=0.1,
                subsample=0.8,
                colsample_bytree=0.8,
                random_state=42,
                use_label_encoder=False,
                eval_metric='logloss',
            )
            self.completion_model.fit(X_train_scaled, y_comp_train)

            # 집중 시간 예측 모델
            self.focus_time_model = XGBRegressor(
                n_estimators=200,
                max_depth=6,
                learning_rate=0.1,
                subsample=0.8,
                colsample_bytree=0.8,
                random_state=42,
            )
            self.focus_time_model.fit(X_train_scaled, y_focus_train)
        else:
            # Fallback to sklearn
            from sklearn.ensemble import GradientBoostingClassifier, GradientBoostingRegressor

            self.completion_model = GradientBoostingClassifier(
                n_estimators=200, max_depth=8, random_state=42
            )
            self.completion_model.fit(X_train_scaled, y_comp_train)

            self.focus_time_model = GradientBoostingRegressor(
                n_estimators=200, max_depth=6, random_state=42
            )
            self.focus_time_model.fit(X_train_scaled, y_focus_train)

        # 평가
        comp_pred = self.completion_model.predict(X_test_scaled)
        comp_accuracy = accuracy_score(y_comp_test, comp_pred)

        focus_pred = self.focus_time_model.predict(X_test_scaled)
        focus_rmse = np.sqrt(mean_squared_error(y_focus_test, focus_pred))

        print(f"\n  Completion Model Accuracy: {comp_accuracy:.4f}")
        print(f"  Focus Time Model RMSE: {focus_rmse:.2f} minutes")

        # 5. 모델 저장
        print("\n[5/5] Saving models...")
        os.makedirs(self.model_path, exist_ok=True)

        with open(f"{self.model_path}/completion_model.pkl", "wb") as f:
            pickle.dump(self.completion_model, f)
        with open(f"{self.model_path}/focus_time_model.pkl", "wb") as f:
            pickle.dump(self.focus_time_model, f)
        with open(f"{self.model_path}/scaler.pkl", "wb") as f:
            pickle.dump(self.scaler, f)
        with open(f"{self.model_path}/feature_names.json", "w") as f:
            json.dump(self.feature_names, f)

        self.mab.save(f"{self.model_path}/mab_state.json")

        self.is_trained = True
        print("\n" + "=" * 50)
        print("Training Complete!")
        print("=" * 50)

        return {
            "status": "success",
            "samples": len(features),
            "features": len(self.feature_names),
            "completion_accuracy": round(comp_accuracy, 4),
            "focus_rmse": round(focus_rmse, 2),
        }

    def _prepare_features(
        self,
        task_type: TaskType,
        difficulty: int,
        hour: int,
        day_of_week: int,
        focus_minutes: int = 25,
        break_minutes: int = 5,
        rounds: int = 4,
        context: Dict = None,
    ) -> np.ndarray:
        """피처 벡터 준비"""
        context = context or {}

        is_weekend = day_of_week >= 5

        x = [
            hour,  # start_hour
            day_of_week,
            1 if is_weekend else 0,
            1 if task_type == TaskType.READING else 0,
            1 if task_type == TaskType.PRACTICE else 0,
            1 if task_type == TaskType.CREATION else 0,
            1 if task_type == TaskType.ROUTINE else 0,
            difficulty,
            focus_minutes,
            break_minutes,
            rounds,
            context.get("sessions_today", 0),
            context.get("sessions_this_week", 0),
            context.get("streak_days", 0),
            context.get("last_session_hours_ago", 24),
            context.get("same_hour_completion_rate", 0.7),
            context.get("same_task_completion_rate", 0.7),
            context.get("recent_7day_completion_rate", 0.7),
            context.get("recent_7day_avg_focus", 25),
            context.get("fatigue_score", 0.3),
            context.get("momentum_score", 0.5),
            1 if 5 <= hour < 12 else 0,  # is_morning
            1 if 12 <= hour < 18 else 0,  # is_afternoon
            1 if 18 <= hour < 22 else 0,  # is_evening
            1 if hour >= 22 or hour < 5 else 0,  # is_night
        ]

        return np.array(x).reshape(1, -1)

    def predict_completion(
        self,
        task_type: TaskType,
        difficulty: int,
        hour: int,
        day_of_week: int,
        focus_minutes: int,
        break_minutes: int,
        context: Dict = None,
    ) -> float:
        """완주 확률 예측"""
        if not self.is_trained:
            return self._fallback_completion_prob(difficulty, hour, focus_minutes)

        X = self._prepare_features(
            task_type, difficulty, hour, day_of_week,
            focus_minutes, break_minutes, context=context
        )
        X_scaled = self.scaler.transform(X)

        prob = self.completion_model.predict_proba(X_scaled)[0][1]
        return round(float(prob), 3)

    def _fallback_completion_prob(self, difficulty, hour, focus_minutes) -> float:
        """Fallback 확률 계산"""
        prob = 0.7
        prob -= (difficulty - 3) * 0.08
        if focus_minutes > 30:
            prob -= 0.1
        if hour >= 22 or hour <= 2:
            prob -= 0.1
        return max(0.3, min(0.9, prob))

    def get_recommendation(
        self,
        recent_sessions: List[Dict],
        task_type: TaskType,
        difficulty: int,
        hour: int,
        day_of_week: int,
    ) -> RecommendationResponse:
        """
        종합 AI 추천 생성
        """
        # 컨텍스트 구축
        context = self._build_context(recent_sessions)

        # 페르소나 분류
        persona_type = self._classify_persona(recent_sessions)
        persona_profile = get_persona_profile(persona_type) if persona_type else None

        # MAB로 최적 전략 선택
        mab_context = {"difficulty": difficulty, "hour": hour}
        best_arm = self.mab.select_arm(mab_context)

        # AI 예측으로 완주 확률 계산
        completion_prob = self.predict_completion(
            task_type, difficulty, hour, day_of_week,
            best_arm.focus_minutes, best_arm.break_minutes, context
        )

        # 골든타임 분석 업데이트
        if recent_sessions:
            for s in recent_sessions[-10:]:
                self.golden_time.update(
                    s.get("start_hour", hour),
                    s.get("day_of_week", day_of_week),
                    s.get("status") == "completed"
                )

        golden_hours = self.golden_time.get_golden_hours()

        # 적응형 난이도
        recommended_difficulty = self.adaptive_difficulty.get_recommended_difficulty()

        # 리스크 레벨
        if completion_prob < 0.5:
            risk_level = "high"
        elif completion_prob < 0.7:
            risk_level = "medium"
        else:
            risk_level = "low"

        # 마이크로 루틴
        micro_routine = self._get_micro_routine(recent_sessions)

        # 추천 근거 생성
        reasons = []
        if persona_profile:
            reasons.append(f"AI 분석 결과, '{persona_profile['name']}' 패턴입니다.")

        reasons.append(f"예측 완주 확률: {int(completion_prob * 100)}%")

        if golden_hours and hour in golden_hours:
            reasons.append("지금이 당신의 골든타임이에요!")
        elif golden_hours:
            reasons.append(f"골든타임은 {golden_hours[0]}시예요.")

        if recommended_difficulty != difficulty:
            reasons.append(f"추천 난이도: {recommended_difficulty} (현재: {difficulty})")

        # 루프 생성
        loop = []
        for i in range(best_arm.rounds):
            loop.append(LoopPhase(type="focus", minutes=best_arm.focus_minutes))
            if i < best_arm.rounds - 1:
                loop.append(LoopPhase(type="break", minutes=best_arm.break_minutes))

        return RecommendationResponse(
            recommended_loop=loop,
            predicted_completion_prob=completion_prob,
            reason=" ".join(reasons[:3]),
            risk_level=risk_level,
            micro_routine=micro_routine,
            persona_type=persona_type.value if persona_type else None,
        )

    def _build_context(self, sessions: List[Dict]) -> Dict:
        """세션 데이터에서 컨텍스트 구축"""
        if not sessions:
            return {}

        recent = sessions[:20]

        # 완주율
        completion_rate = sum(1 for s in recent if s.get("status") == "completed") / len(recent)

        # 평균 집중 시간
        focus_times = [s.get("total_focus_sec", 0) / 60 for s in recent]
        avg_focus = sum(focus_times) / len(focus_times)

        # 연속 성공
        streak = 0
        for s in recent:
            if s.get("status") == "completed":
                streak += 1
            else:
                break

        return {
            "recent_7day_completion_rate": completion_rate,
            "recent_7day_avg_focus": avg_focus,
            "momentum_score": min(1.0, streak * 0.15 + 0.3),
            "streak_days": streak,
        }

    def _classify_persona(self, sessions: List[Dict]) -> Optional[PersonaType]:
        """페르소나 분류"""
        if not sessions or len(sessions) < 5:
            return PersonaType.CASUAL_LEARNER

        recent = sessions[:20]
        completion_rate = sum(1 for s in recent if s.get("status") == "completed") / len(recent)
        focus_times = [s.get("total_focus_sec", 0) / 60 for s in recent]
        avg_focus = sum(focus_times) / len(focus_times) if focus_times else 25

        abort_counts = {}
        for s in recent:
            reason = s.get("abort_reason")
            if reason:
                abort_counts[reason] = abort_counts.get(reason, 0) + 1
        top_abort = max(abort_counts, key=abort_counts.get) if abort_counts else "phone"

        active_hours = [s.get("start_hour", 12) for s in recent]

        return classify_user_persona(completion_rate, avg_focus, top_abort, active_hours)

    def _get_micro_routine(self, sessions: List[Dict]) -> Optional[str]:
        """마이크로 루틴 제안"""
        if not sessions:
            return None

        # 주요 중단 사유 분석
        abort_counts = {}
        for s in sessions[:10]:
            reason = s.get("abort_reason")
            if reason:
                abort_counts[reason] = abort_counts.get(reason, 0) + 1

        if not abort_counts:
            return None

        top_reason = max(abort_counts, key=abort_counts.get)

        routines = {
            "phone": "📱 시작 전 스마트폰을 다른 방에 두세요. 첫 2분은 화면만 바라보기!",
            "tired": "😴 시작 전 1분 스트레칭으로 몸을 깨워주세요!",
            "anxious": "😰 시작 전 심호흡 3번! 긴장을 풀고 시작해요.",
            "bored": "😐 오늘의 작은 목표를 하나 정해보세요. 성취감이 집중력을 높여요!",
            "environment": "🔊 조용한 곳으로 이동하거나 노이즈캔슬링 이어폰을 사용해보세요.",
            "urgent": "⏰ 긴급 상황이 자주 발생하면, 짧은 10분 루프로 시작해보세요.",
        }

        return routines.get(top_reason)

    def update_mab(self, focus_minutes: int, break_minutes: int, rounds: int, success: bool):
        """MAB 업데이트"""
        arm_key = f"{focus_minutes}_{break_minutes}_{rounds}"
        self.mab.update(arm_key, success)
        self.mab.save(f"{self.model_path}/mab_state.json")

    def get_feature_importance(self) -> Dict:
        """피처 중요도 반환"""
        if not self.is_trained or not hasattr(self.completion_model, 'feature_importances_'):
            return {}

        importance = self.completion_model.feature_importances_
        return {
            name: round(float(imp), 4)
            for name, imp in sorted(
                zip(self.feature_names, importance),
                key=lambda x: x[1],
                reverse=True
            )
        }


# 싱글톤 인스턴스
_advanced_recommender: Optional[AdvancedAIRecommender] = None


def get_advanced_recommender() -> AdvancedAIRecommender:
    """고도화된 AI 추천 엔진 인스턴스"""
    global _advanced_recommender
    if _advanced_recommender is None:
        _advanced_recommender = AdvancedAIRecommender()
    return _advanced_recommender


def train_advanced_models():
    """고도화된 모델 학습"""
    recommender = get_advanced_recommender()
    return recommender.train(force_retrain=True)


if __name__ == "__main__":
    result = train_advanced_models()
    print(json.dumps(result, indent=2))
