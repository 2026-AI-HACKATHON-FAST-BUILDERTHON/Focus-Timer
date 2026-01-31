import React, { useState } from 'react';
import styled from 'styled-components';

export interface SessionConfig {
  taskType: 'reading' | 'practice' | 'creation' | 'routine';
  difficulty: number;
  goal: string;
  focusMinutes: number;
  breakMinutes: number;
  rounds: number;
}

interface SessionSetupProps {
  onStart: (config: SessionConfig) => void;
  recommendation?: {
    focusMinutes: number;
    breakMinutes: number;
    reason: string;
    completionProb?: number;
    riskLevel?: string;
    microRoutine?: string | null;
  };
  isLoading?: boolean;
}

const taskTypeData: Record<SessionConfig['taskType'], { icon: string; label: string }> = {
  reading: { icon: 'bi-book', label: '학습/독서' },
  practice: { icon: 'bi-code-slash', label: '실습/연습' },
  creation: { icon: 'bi-palette', label: '창작/작업' },
  routine: { icon: 'bi-list-check', label: '일상/반복' },
};

// 난이도별 설명 데이터
const difficultyData: Record<number, { label: string; description: string; aiEffect: string; color: string }> = {
  1: {
    label: '매우 쉬움',
    description: '단순 반복 작업, 익숙한 내용',
    aiEffect: 'AI가 긴 집중 시간을 추천해요',
    color: '#48BB78',
  },
  2: {
    label: '쉬움',
    description: '기본적인 내용, 약간의 사고 필요',
    aiEffect: 'AI가 안정적인 루틴을 추천해요',
    color: '#68D391',
  },
  3: {
    label: '보통',
    description: '일반적인 집중력이 필요한 작업',
    aiEffect: 'AI가 균형 잡힌 설정을 추천해요',
    color: '#F6AD55',
  },
  4: {
    label: '어려움',
    description: '높은 집중력과 사고력 필요',
    aiEffect: 'AI가 짧은 집중 + 충분한 휴식을 추천해요',
    color: '#FC8181',
  },
  5: {
    label: '매우 어려움',
    description: '최대 집중력이 필요한 도전적 과제',
    aiEffect: 'AI가 짧고 강렬한 세션을 추천해요',
    color: '#E53E3E',
  },
};

// 추천 텍스트를 개행 처리하는 헬퍼 함수
const formatRecommendationText = (text: string): string[] => {
  // 마침표, 느낌표, 물음표 뒤에서 분리 (단, 숫자% 뒤의 마침표는 제외)
  const sentences = text
    .split(/(?<=[.!?])\s+/)
    .filter(s => s.trim().length > 0);
  return sentences;
};

// 값 범위 제한 헬퍼 함수
const clampValue = (value: number, min: number, max: number): number => {
  if (isNaN(value)) return min;
  return Math.max(min, Math.min(max, value));
};

// 시간 설정 제한 상수
const TIME_LIMITS = {
  focusMinutes: { min: 1, max: 60 },    // 집중: 1~60분
  breakMinutes: { min: 1, max: 30 },    // 휴식: 1~30분
  rounds: { min: 1, max: 10 },          // 라운드: 1~10회
};

const SessionSetup: React.FC<SessionSetupProps> = ({ onStart, recommendation, isLoading }) => {
  const [config, setConfig] = useState<SessionConfig>({
    taskType: 'reading',
    difficulty: 3,
    goal: '',
    focusMinutes: recommendation?.focusMinutes || 25,
    breakMinutes: recommendation?.breakMinutes || 5,
    rounds: 4,
  });
  const [recommendationApplied, setRecommendationApplied] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onStart(config);
  };

  const applyRecommendation = () => {
    if (recommendation && !recommendationApplied) {
      setConfig((prev) => ({
        ...prev,
        focusMinutes: recommendation.focusMinutes,
        breakMinutes: recommendation.breakMinutes,
      }));
      setRecommendationApplied(true);
    }
  };

  return (
    <StyledWrapper>
      <div className="setup-container">
        <h2 className="setup-title">세션 설정</h2>

        {isLoading ? (
          <div className="recommendation-card loading">
            <div className="recommendation-header">
              <i className="bi bi-robot"></i>
              AI 분석 중...
            </div>
            <div className="loading-bar">
              <div className="loading-progress"></div>
            </div>
          </div>
        ) : recommendation && (
          <div className="recommendation-card">
            <div className="recommendation-header">
              <i className="bi bi-robot"></i>
              AI 맞춤 추천
              {recommendation.completionProb && (
                <span className={`prob-badge ${recommendation.riskLevel || 'low'}`}>
                  완주 확률 {Math.round(recommendation.completionProb * 100)}%
                </span>
              )}
            </div>
            <div className="recommendation-text">
              {formatRecommendationText(recommendation.reason).map((sentence, idx) => (
                <p key={idx}>{sentence}</p>
              ))}
            </div>
            {recommendation.microRoutine && (
              <div className="micro-routine">
                <i className="bi bi-lightbulb-fill"></i>
                <div className="micro-routine-content">
                  <span className="micro-routine-label">시작 전 루틴</span>
                  <div className="micro-routine-text">
                    {formatRecommendationText(recommendation.microRoutine).map((sentence, idx) => (
                      <p key={idx}>{sentence}</p>
                    ))}
                  </div>
                </div>
              </div>
            )}
            <div className="recommendation-values">
              <span><i className="bi bi-clock-fill"></i> {recommendation.focusMinutes}분 집중</span>
              <span><i className="bi bi-cup-hot-fill"></i> {recommendation.breakMinutes}분 휴식</span>
            </div>
            <button
              type="button"
              className={`recommendation-btn ${recommendationApplied ? 'applied' : ''}`}
              onClick={applyRecommendation}
              disabled={recommendationApplied}
            >
              {recommendationApplied ? (
                <>
                  <i className="bi bi-check-circle-fill"></i> 적용 완료!
                </>
              ) : (
                <>
                  <i className="bi bi-magic"></i> 추천 적용하기
                </>
              )}
            </button>
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>과제 유형</label>
            <div className="task-type-grid">
              {(Object.keys(taskTypeData) as SessionConfig['taskType'][]).map(
                (type) => (
                  <button
                    key={type}
                    type="button"
                    className={`task-type-btn ${config.taskType === type ? 'active' : ''}`}
                    onClick={() => setConfig((prev) => ({ ...prev, taskType: type }))}
                  >
                    <i className={`bi ${taskTypeData[type].icon}`}></i>
                    {taskTypeData[type].label}
                  </button>
                )
              )}
            </div>
          </div>

          <div className="form-group">
            <label>
              <i className="bi bi-speedometer2"></i>
              과제 난이도
              <span className="label-hint">AI 추천에 반영돼요</span>
            </label>
            <div className="difficulty-slider">
              {[1, 2, 3, 4, 5].map((level) => (
                <button
                  key={level}
                  type="button"
                  className={`difficulty-btn ${config.difficulty === level ? 'active' : ''}`}
                  style={{
                    '--active-color': difficultyData[level].color,
                  } as React.CSSProperties}
                  onClick={() => setConfig((prev) => ({ ...prev, difficulty: level }))}
                >
                  {level}
                </button>
              ))}
            </div>
            <div className="difficulty-info">
              <div className="difficulty-header">
                <span
                  className="difficulty-label"
                  style={{ color: difficultyData[config.difficulty].color }}
                >
                  {difficultyData[config.difficulty].label}
                </span>
                <span className="difficulty-desc">
                  {difficultyData[config.difficulty].description}
                </span>
              </div>
              <div className="ai-effect">
                <i className="bi bi-robot"></i>
                {difficultyData[config.difficulty].aiEffect}
              </div>
            </div>
          </div>

          <div className="form-group">
            <label>목표 (선택)</label>
            <input
              type="text"
              className="goal-input"
              placeholder="이번 세션에서 달성할 목표를 적어주세요"
              value={config.goal}
              onChange={(e) => setConfig((prev) => ({ ...prev, goal: e.target.value }))}
            />
          </div>

          <div className="time-settings">
            <div className="time-setting">
              <label>집중 시간 <span className="limit-hint">(1~60분)</span></label>
              <div className="time-input-wrapper">
                <input
                  type="number"
                  min={TIME_LIMITS.focusMinutes.min}
                  max={TIME_LIMITS.focusMinutes.max}
                  value={config.focusMinutes}
                  onChange={(e) => {
                    const value = parseInt(e.target.value) || TIME_LIMITS.focusMinutes.min;
                    const clamped = clampValue(value, TIME_LIMITS.focusMinutes.min, TIME_LIMITS.focusMinutes.max);
                    setConfig((prev) => ({ ...prev, focusMinutes: clamped }));
                  }}
                />
                <span>분</span>
              </div>
            </div>

            <div className="time-setting">
              <label>휴식 시간 <span className="limit-hint">(1~30분)</span></label>
              <div className="time-input-wrapper">
                <input
                  type="number"
                  min={TIME_LIMITS.breakMinutes.min}
                  max={TIME_LIMITS.breakMinutes.max}
                  value={config.breakMinutes}
                  onChange={(e) => {
                    const value = parseInt(e.target.value) || TIME_LIMITS.breakMinutes.min;
                    const clamped = clampValue(value, TIME_LIMITS.breakMinutes.min, TIME_LIMITS.breakMinutes.max);
                    setConfig((prev) => ({ ...prev, breakMinutes: clamped }));
                  }}
                />
                <span>분</span>
              </div>
            </div>

            <div className="time-setting">
              <label>라운드 <span className="limit-hint">(1~10회)</span></label>
              <div className="time-input-wrapper">
                <input
                  type="number"
                  min={TIME_LIMITS.rounds.min}
                  max={TIME_LIMITS.rounds.max}
                  value={config.rounds}
                  onChange={(e) => {
                    const value = parseInt(e.target.value) || TIME_LIMITS.rounds.min;
                    const clamped = clampValue(value, TIME_LIMITS.rounds.min, TIME_LIMITS.rounds.max);
                    setConfig((prev) => ({ ...prev, rounds: clamped }));
                  }}
                />
                <span>회</span>
              </div>
            </div>
          </div>

          <button type="submit" className="start-btn">
            <i className="bi bi-play-fill"></i>
            세션 시작
          </button>
        </form>
      </div>
    </StyledWrapper>
  );
};

const StyledWrapper = styled.div`
  .setup-container {
    background: #FFFFFF;
    border-radius: 24px;
    padding: 32px;
    width: 100%;
    max-width: 480px;
    box-shadow: 0 8px 32px rgba(108, 99, 255, 0.1);
  }

  .setup-title {
    text-align: center;
    color: #2D3748;
    margin-bottom: 24px;
    font-size: 22px;
    font-weight: 700;
  }

  .recommendation-card {
    background: linear-gradient(135deg, #F0F4FF 0%, #E8ECFF 100%);
    border: 1px solid #C4B5FD;
    border-radius: 16px;
    padding: 16px;
    margin-bottom: 24px;
  }

  .recommendation-header {
    display: flex;
    align-items: center;
    gap: 8px;
    color: #6C63FF;
    font-weight: 600;
    margin-bottom: 10px;

    i {
      font-size: 20px;
    }
  }

  .prob-badge {
    margin-left: auto;
    font-size: 12px;
    padding: 4px 10px;
    border-radius: 12px;
    font-weight: 700;

    &.low {
      background: #C6F6D5;
      color: #276749;
    }

    &.medium {
      background: #FEEBC8;
      color: #C05621;
    }

    &.high {
      background: #FED7D7;
      color: #C53030;
    }
  }

  .recommendation-text {
    margin-bottom: 14px;

    p {
      color: #4A5568;
      font-size: 14px;
      line-height: 1.6;
      margin: 0 0 6px 0;

      &:last-child {
        margin-bottom: 0;
      }

      &:first-child {
        font-weight: 600;
        color: #2D3748;
      }
    }
  }

  .micro-routine {
    background: linear-gradient(135deg, #FFFAF0 0%, #FFF5EB 100%);
    border: 1px solid #F6AD55;
    border-radius: 12px;
    padding: 14px 16px;
    margin-bottom: 14px;
    display: flex;
    align-items: flex-start;
    gap: 12px;

    i {
      color: #F6AD55;
      font-size: 20px;
      flex-shrink: 0;
      margin-top: 2px;
    }
  }

  .micro-routine-content {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .micro-routine-label {
    font-size: 11px;
    font-weight: 700;
    color: #C05621;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }

  .micro-routine-text {
    p {
      font-size: 14px;
      color: #744210;
      line-height: 1.6;
      margin: 0 0 4px 0;

      &:last-child {
        margin-bottom: 0;
      }
    }
  }

  .recommendation-values {
    display: flex;
    gap: 16px;
    margin-bottom: 14px;

    span {
      display: flex;
      align-items: center;
      gap: 6px;
      font-size: 14px;
      font-weight: 600;
      color: #4A5568;

      i {
        color: #6C63FF;
      }
    }
  }

  .recommendation-btn {
    background: linear-gradient(135deg, #6C63FF 0%, #5046E5 100%);
    color: #FFFFFF;
    border: none;
    padding: 10px 18px;
    border-radius: 10px;
    font-size: 14px;
    font-weight: 600;
    transition: all 0.2s;
    display: inline-flex;
    align-items: center;
    gap: 6px;

    &:hover:not(:disabled) {
      transform: translateY(-1px);
      box-shadow: 0 4px 12px rgba(108, 99, 255, 0.3);
    }

    &.applied {
      background: linear-gradient(135deg, #48BB78 0%, #38A169 100%);
      cursor: default;
    }

    &:disabled {
      opacity: 1;
    }
  }

  .recommendation-card.loading {
    .recommendation-header {
      color: #A0AEC0;
    }
  }

  .loading-bar {
    height: 4px;
    background: #E2E8F0;
    border-radius: 2px;
    overflow: hidden;
  }

  .loading-progress {
    height: 100%;
    width: 30%;
    background: linear-gradient(90deg, #6C63FF 0%, #A78BFA 100%);
    border-radius: 2px;
    animation: loading 1.5s ease-in-out infinite;
  }

  @keyframes loading {
    0% { transform: translateX(-100%); }
    100% { transform: translateX(400%); }
  }

  .form-group {
    margin-bottom: 24px;
  }

  label {
    display: block;
    color: #4A5568;
    font-size: 14px;
    font-weight: 500;
    margin-bottom: 10px;
  }

  .task-type-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 10px;
  }

  .task-type-btn {
    background: #FAFBFF;
    border: 2px solid #E2E8F0;
    color: #4A5568;
    padding: 14px;
    border-radius: 12px;
    font-size: 14px;
    font-weight: 500;
    transition: all 0.2s;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;

    i {
      font-size: 18px;
      color: #6C63FF;
    }

    &:hover {
      border-color: #6C63FF;
    }

    &.active {
      background: #F0F4FF;
      border-color: #6C63FF;
      color: #6C63FF;
    }
  }

  .difficulty-slider {
    display: flex;
    gap: 8px;
    margin-bottom: 8px;
  }

  .difficulty-btn {
    width: 44px;
    height: 44px;
    border-radius: 12px;
    background: #FAFBFF;
    border: 2px solid #E2E8F0;
    color: #A0AEC0;
    font-weight: 600;
    font-size: 15px;
    transition: all 0.2s;

    &:hover {
      border-color: var(--active-color, #6C63FF);
    }

    &.active {
      background: var(--active-color, #6C63FF);
      border-color: var(--active-color, #6C63FF);
      color: #FFFFFF;
    }
  }

  .difficulty-info {
    background: #FAFBFF;
    border-radius: 12px;
    padding: 14px 16px;
    margin-top: 12px;
  }

  .difficulty-header {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 8px;
  }

  .difficulty-label {
    font-weight: 700;
    font-size: 15px;
  }

  .difficulty-desc {
    color: #718096;
    font-size: 13px;
  }

  .ai-effect {
    display: flex;
    align-items: center;
    gap: 8px;
    color: #6C63FF;
    font-size: 13px;
    font-weight: 500;
    background: #F0F4FF;
    padding: 8px 12px;
    border-radius: 8px;

    i {
      font-size: 16px;
    }
  }

  .label-hint {
    font-size: 11px;
    color: #A0AEC0;
    font-weight: 400;
    margin-left: 8px;
  }

  label i {
    margin-right: 6px;
    color: #6C63FF;
  }

  .goal-input {
    width: 100%;
    background: #FAFBFF;
    border: 2px solid #E2E8F0;
    border-radius: 12px;
    padding: 14px 16px;
    color: #2D3748;
    font-size: 14px;

    &::placeholder {
      color: #A0AEC0;
    }

    &:focus {
      border-color: #6C63FF;
      background: #FFFFFF;
    }
  }

  .time-settings {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 12px;
    margin-bottom: 28px;
  }

  .time-setting {
    text-align: center;

    label {
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 4px;
      flex-wrap: wrap;
    }
  }

  .limit-hint {
    font-size: 10px;
    color: #A0AEC0;
    font-weight: 400;
  }

  .time-input-wrapper {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 6px;
    background: #FAFBFF;
    border: 2px solid #E2E8F0;
    border-radius: 12px;
    padding: 12px;

    input {
      width: 48px;
      background: transparent;
      border: none;
      color: #6C63FF;
      font-size: 20px;
      font-weight: 700;
      text-align: center;
    }

    span {
      color: #718096;
      font-size: 14px;
    }
  }

  .start-btn {
    width: 100%;
    background: linear-gradient(135deg, #6C63FF 0%, #5046E5 100%);
    color: #FFFFFF;
    border: none;
    padding: 18px;
    border-radius: 14px;
    font-size: 17px;
    font-weight: 600;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 10px;
    transition: all 0.2s;
    box-shadow: 0 4px 16px rgba(108, 99, 255, 0.3);

    &:hover {
      transform: translateY(-2px);
      box-shadow: 0 6px 24px rgba(108, 99, 255, 0.4);
    }

    i {
      font-size: 20px;
    }
  }

  @media (max-width: 768px) {
    .setup-container {
      padding: 24px;
    }

    .task-type-grid {
      grid-template-columns: 1fr;
    }

    .time-settings {
      grid-template-columns: 1fr;
      gap: 16px;
    }
  }
`;

export default SessionSetup;
