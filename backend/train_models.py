#!/usr/bin/env python3
"""
AI 모델 학습 스크립트

사용법:
    python train_models.py

100,000개 세션 데이터 생성 후 XGBoost 모델 학습
"""

import sys
import os

# 현재 디렉토리를 path에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.advanced_recommender import train_advanced_models

if __name__ == "__main__":
    print("=" * 60)
    print("🧠 Focus Timer AI 모델 학습")
    print("=" * 60)
    print()

    result = train_advanced_models()

    print()
    print("=" * 60)
    print("📊 학습 결과:")
    print(f"  - 상태: {result.get('status', 'unknown')}")
    print(f"  - 샘플 수: {result.get('samples', 0):,}")
    print(f"  - 피처 수: {result.get('features', 0)}")
    print(f"  - 완주 예측 정확도: {result.get('completion_accuracy', 0) * 100:.2f}%")
    print(f"  - 집중 시간 예측 RMSE: {result.get('focus_rmse', 0):.2f}분")
    print("=" * 60)
