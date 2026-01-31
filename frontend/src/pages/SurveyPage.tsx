import React, { useState } from 'react';
import styled from 'styled-components';

interface SurveyOption {
  value: string;
  text: string;
  icon: string;
}

interface SurveyQuestion {
  id: string;
  question: string;
  dimension: string;
  options: SurveyOption[];
}

// 설문 질문 데이터
const SURVEY_QUESTIONS: SurveyQuestion[] = [
  {
    id: 'q1_energy',
    question: '에너지를 얻는 방식은?',
    dimension: 'EI',
    options: [
      { value: 'E', text: '사람들과 어울릴 때 활력이 생겨요', icon: 'bi-people-fill' },
      { value: 'I', text: '혼자만의 시간이 충전해줘요', icon: 'bi-person-fill' },
    ],
  },
  {
    id: 'q2_study_env',
    question: '선호하는 학습 환경은?',
    dimension: 'EI',
    options: [
      { value: 'E', text: '카페나 스터디 그룹에서 함께', icon: 'bi-cup-hot-fill' },
      { value: 'I', text: '조용한 개인 공간에서 혼자', icon: 'bi-house-fill' },
    ],
  },
  {
    id: 'q3_info_style',
    question: '정보를 받아들이는 방식은?',
    dimension: 'SN',
    options: [
      { value: 'S', text: '구체적인 사실과 단계별 설명', icon: 'bi-list-check' },
      { value: 'N', text: '전체 그림과 개념적 이해', icon: 'bi-lightbulb-fill' },
    ],
  },
  {
    id: 'q4_learning_pref',
    question: '학습할 때 더 끌리는 것은?',
    dimension: 'SN',
    options: [
      { value: 'S', text: '실용적이고 바로 써먹을 수 있는 것', icon: 'bi-tools' },
      { value: 'N', text: '이론적이고 새로운 가능성 탐구', icon: 'bi-stars' },
    ],
  },
  {
    id: 'q5_decision',
    question: '결정을 내릴 때 중요한 것은?',
    dimension: 'TF',
    options: [
      { value: 'T', text: '논리적 분석과 객관적 기준', icon: 'bi-calculator' },
      { value: 'F', text: '가치관과 주변 사람들의 감정', icon: 'bi-heart-fill' },
    ],
  },
  {
    id: 'q6_feedback',
    question: '피드백을 받을 때 선호하는 방식은?',
    dimension: 'TF',
    options: [
      { value: 'T', text: '직접적이고 논리적인 비판', icon: 'bi-chat-square-text' },
      { value: 'F', text: '격려와 함께 부드러운 제안', icon: 'bi-emoji-smile' },
    ],
  },
  {
    id: 'q7_schedule',
    question: '일정을 관리하는 스타일은?',
    dimension: 'JP',
    options: [
      { value: 'J', text: '미리 계획하고 체계적으로', icon: 'bi-calendar-check' },
      { value: 'P', text: '유연하게 상황에 따라', icon: 'bi-shuffle' },
    ],
  },
  {
    id: 'q8_deadline',
    question: '마감을 대하는 태도는?',
    dimension: 'JP',
    options: [
      { value: 'J', text: '일찍 끝내고 여유 갖기', icon: 'bi-check2-circle' },
      { value: 'P', text: '마감 직전에 집중력 폭발', icon: 'bi-lightning-charge-fill' },
    ],
  },
];

// MBTI 프로필 데이터
const MBTI_PROFILES: Record<string, {
  name: string;
  nickname: string;
  studyStyle: string;
  focusRange: [number, number];
  breakRange: [number, number];
  completionTendency: number;
  tips: string[];
}> = {
  INTJ: { name: '전략가', nickname: '용의주도한 전략가', studyStyle: '장기 목표를 세우고 체계적으로 깊이 파고드는 학습', focusRange: [35, 50], breakRange: [5, 7], completionTendency: 0.85, tips: ['복잡한 문제를 분석하는 시간을 충분히 확보하세요', '혼자만의 조용한 공간에서 최고의 집중력을 발휘해요'] },
  INTP: { name: '논리술사', nickname: '호기심 많은 사색가', studyStyle: '개념을 깊이 탐구하고 이론적 연결고리를 찾는 학습', focusRange: [30, 45], breakRange: [5, 10], completionTendency: 0.65, tips: ['호기심을 따라가되, 시간 제한을 두세요', '아이디어를 메모하는 습관이 집중력을 높여요'] },
  ENTJ: { name: '통솔자', nickname: '대담한 통솔자', studyStyle: '명확한 목표와 효율적인 계획으로 빠르게 성과 내기', focusRange: [25, 35], breakRange: [3, 5], completionTendency: 0.90, tips: ['도전적인 목표가 당신을 움직이게 해요', '성과를 측정하고 기록하면 동기부여가 됩니다'] },
  ENTP: { name: '변론가', nickname: '뜨거운 논쟁을 즐기는 변론가', studyStyle: '다양한 관점을 탐구하고 아이디어를 발전시키는 학습', focusRange: [15, 25], breakRange: [5, 7], completionTendency: 0.60, tips: ['짧은 집중 시간으로 시작해서 늘려가세요', '다양한 주제를 번갈아 학습하면 지루함을 줄일 수 있어요'] },
  INFJ: { name: '옹호자', nickname: '선의의 옹호자', studyStyle: '의미와 목적을 연결하며 깊이 있게 학습', focusRange: [30, 45], breakRange: [7, 10], completionTendency: 0.80, tips: ['학습의 의미와 목적을 되새기면 집중력이 높아져요', '조용하고 영감을 주는 환경을 만드세요'] },
  INFP: { name: '중재자', nickname: '열정적인 중재자', studyStyle: '개인적 의미를 찾으며 창의적으로 학습', focusRange: [20, 35], breakRange: [7, 10], completionTendency: 0.65, tips: ['학습 내용과 개인적 가치를 연결해보세요', '창의적인 방식으로 정리하면 기억에 오래 남아요'] },
  ENFJ: { name: '선도자', nickname: '정의로운 사회운동가', studyStyle: '타인과 함께 성장하며 영감을 주고받는 학습', focusRange: [25, 35], breakRange: [5, 7], completionTendency: 0.85, tips: ['스터디 그룹을 이끌면 학습 효과가 배가돼요', '다른 사람을 가르치는 것이 최고의 학습법이에요'] },
  ENFP: { name: '활동가', nickname: '재기발랄한 활동가', studyStyle: '흥미와 열정을 따라 다양하게 탐구하는 학습', focusRange: [15, 25], breakRange: [5, 7], completionTendency: 0.55, tips: ['짧은 세션으로 시작해서 성공 경험을 쌓으세요', '다양한 주제를 번갈아 학습하면 집중이 잘 돼요'] },
  ISTJ: { name: '현실주의자', nickname: '청렴결백한 논리주의자', studyStyle: '체계적이고 단계적인 방식으로 철저하게 학습', focusRange: [30, 45], breakRange: [5, 7], completionTendency: 0.90, tips: ['명확한 체크리스트를 만들면 만족감이 높아져요', '익숙한 환경에서 최고의 성과를 내요'] },
  ISFJ: { name: '수호자', nickname: '용감한 수호자', studyStyle: '꾸준하고 성실하게 세부사항까지 챙기는 학습', focusRange: [25, 40], breakRange: [5, 7], completionTendency: 0.85, tips: ['다른 사람을 위한 학습이라고 생각하면 동기부여가 돼요', '편안하고 익숙한 환경을 만드세요'] },
  ESTJ: { name: '경영자', nickname: '엄격한 관리자', studyStyle: '명확한 목표와 체계적 계획으로 효율적으로 학습', focusRange: [25, 35], breakRange: [3, 5], completionTendency: 0.90, tips: ['목표를 세분화하고 하나씩 달성하세요', '진행 상황을 측정하면 동기부여가 됩니다'] },
  ESFJ: { name: '집정관', nickname: '사교적인 외교관', studyStyle: '다른 사람과 함께하며 서로 격려하는 학습', focusRange: [20, 30], breakRange: [5, 7], completionTendency: 0.80, tips: ['스터디 그룹이 학습 효과를 높여줘요', '주변 사람에게 목표를 공유하면 책임감이 생겨요'] },
  ISTP: { name: '장인', nickname: '만능 재주꾼', studyStyle: '직접 해보며 문제를 해결하는 실습 중심 학습', focusRange: [20, 30], breakRange: [5, 7], completionTendency: 0.70, tips: ['실습과 이론을 번갈아 학습하세요', '문제 해결에 초점을 맞추면 집중이 잘 돼요'] },
  ISFP: { name: '모험가', nickname: '호기심 많은 예술가', studyStyle: '개인적 관심사를 따라 자유롭게 탐구하는 학습', focusRange: [15, 25], breakRange: [5, 10], completionTendency: 0.60, tips: ['시각적, 감각적 자료를 활용하세요', '자신만의 창의적 방식으로 정리해보세요'] },
  ESTP: { name: '사업가', nickname: '모험을 즐기는 사업가', studyStyle: '실용적이고 즉각적인 결과를 추구하는 학습', focusRange: [15, 25], breakRange: [5, 7], completionTendency: 0.55, tips: ['짧고 강렬한 집중 세션이 효과적이에요', '게임화된 학습이 동기부여에 좋아요'] },
  ESFP: { name: '연예인', nickname: '자유로운 영혼의 연예인', studyStyle: '재미있고 사교적인 방식으로 즐기며 학습', focusRange: [10, 20], breakRange: [5, 7], completionTendency: 0.50, tips: ['가장 짧은 집중 시간으로 시작하세요', '친구와 함께 학습하면 더 재미있어요'] },
};

// 16가지 MBTI 유형 목록
const MBTI_TYPES = [
  'INTJ', 'INTP', 'ENTJ', 'ENTP',
  'INFJ', 'INFP', 'ENFJ', 'ENFP',
  'ISTJ', 'ISFJ', 'ESTJ', 'ESFJ',
  'ISTP', 'ISFP', 'ESTP', 'ESFP',
];

type SurveyMode = 'choice' | 'survey' | 'select' | 'result';

interface SurveyPageProps {
  onComplete: (mbti: string, profile: typeof MBTI_PROFILES[string]) => void;
}

const SurveyPage: React.FC<SurveyPageProps> = ({ onComplete }) => {
  const [mode, setMode] = useState<SurveyMode>('choice');
  const [currentStep, setCurrentStep] = useState(0);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [showResult, setShowResult] = useState(false);
  const [mbtiResult, setMbtiResult] = useState<string>('');

  const handleAnswer = (questionId: string, value: string) => {
    const newAnswers = { ...answers, [questionId]: value };
    setAnswers(newAnswers);

    // 다음 질문으로
    if (currentStep < SURVEY_QUESTIONS.length - 1) {
      setTimeout(() => setCurrentStep(currentStep + 1), 300);
    } else {
      // 결과 계산
      calculateMBTI(newAnswers);
    }
  };

  const calculateMBTI = (finalAnswers: Record<string, string>) => {
    const dimensions: Record<string, number> = {
      E: 0, I: 0, S: 0, N: 0, T: 0, F: 0, J: 0, P: 0
    };

    SURVEY_QUESTIONS.forEach((q) => {
      const answer = finalAnswers[q.id];
      if (answer) {
        dimensions[answer]++;
      }
    });

    let mbti = '';
    mbti += dimensions.E >= dimensions.I ? 'E' : 'I';
    mbti += dimensions.S >= dimensions.N ? 'S' : 'N';
    mbti += dimensions.T >= dimensions.F ? 'T' : 'F';
    mbti += dimensions.J >= dimensions.P ? 'J' : 'P';

    setMbtiResult(mbti);
    setMode('result');

    // 로컬 스토리지에 저장
    localStorage.setItem('userMBTI', mbti);
    localStorage.setItem('mbtiSurveyCompleted', 'true');
  };

  const handleDirectSelect = (selectedMbti: string) => {
    setMbtiResult(selectedMbti);
    setMode('result');

    // 로컬 스토리지에 저장
    localStorage.setItem('userMBTI', selectedMbti);
    localStorage.setItem('mbtiSurveyCompleted', 'true');
  };

  const handleComplete = () => {
    if (mbtiResult && MBTI_PROFILES[mbtiResult]) {
      onComplete(mbtiResult, MBTI_PROFILES[mbtiResult]);
    }
  };

  const currentQuestion = SURVEY_QUESTIONS[currentStep];
  const progress = ((currentStep + 1) / SURVEY_QUESTIONS.length) * 100;

  // 초기 선택 화면: 설문 vs 직접 선택
  if (mode === 'choice') {
    return (
      <StyledWrapper>
        <div className="survey-page">
          <div className="survey-header">
            <h1><i className="bi bi-person-badge"></i> 학습 성향 설정</h1>
            <p>당신에게 맞는 집중 루틴을 찾기 위해 MBTI가 필요해요</p>
          </div>

          <div className="choice-container">
            <button
              className="choice-card"
              onClick={() => setMode('select')}
            >
              <div className="choice-icon">
                <i className="bi bi-grid-3x3-gap-fill"></i>
              </div>
              <h3>MBTI를 알고 있어요</h3>
              <p>16가지 유형 중 선택하기</p>
            </button>

            <button
              className="choice-card"
              onClick={() => setMode('survey')}
            >
              <div className="choice-icon">
                <i className="bi bi-clipboard-check"></i>
              </div>
              <h3>MBTI를 모르거나 확인하고 싶어요</h3>
              <p>8개 질문으로 분석하기</p>
            </button>
          </div>
        </div>
      </StyledWrapper>
    );
  }

  // 직접 선택 화면
  if (mode === 'select') {
    return (
      <StyledWrapper>
        <div className="survey-page">
          <div className="survey-header">
            <h1><i className="bi bi-grid-3x3-gap-fill"></i> MBTI 선택</h1>
            <p>당신의 MBTI 유형을 선택해주세요</p>
          </div>

          <div className="mbti-grid">
            {MBTI_TYPES.map((type) => (
              <button
                key={type}
                className="mbti-type-btn"
                onClick={() => handleDirectSelect(type)}
              >
                <span className="type-code">{type}</span>
                <span className="type-name">{MBTI_PROFILES[type]?.name}</span>
              </button>
            ))}
          </div>

          <button
            className="back-btn"
            onClick={() => setMode('choice')}
          >
            <i className="bi bi-arrow-left"></i>
            뒤로 가기
          </button>
        </div>
      </StyledWrapper>
    );
  }

  // 결과 화면
  if (mode === 'result' && mbtiResult) {
    const profile = MBTI_PROFILES[mbtiResult];

    return (
      <StyledWrapper>
        <div className="survey-page result-page">
          <div className="result-card">
            <div className="result-header">
              <div className="mbti-badge">{mbtiResult}</div>
              <h2 className="result-name">{profile.name}</h2>
              <p className="result-nickname">{profile.nickname}</p>
            </div>

            <div className="result-section">
              <h3><i className="bi bi-book-fill"></i> 학습 스타일</h3>
              <p>{profile.studyStyle}</p>
            </div>

            <div className="result-section">
              <h3><i className="bi bi-clock-fill"></i> 추천 집중 시간</h3>
              <div className="time-range">
                <span className="range-value">{profile.focusRange[0]}~{profile.focusRange[1]}분</span>
                <span className="range-label">집중</span>
                <span className="range-value">{profile.breakRange[0]}~{profile.breakRange[1]}분</span>
                <span className="range-label">휴식</span>
              </div>
            </div>

            <div className="result-section">
              <h3><i className="bi bi-graph-up"></i> 예상 완주 성향</h3>
              <div className="tendency-bar">
                <div
                  className="tendency-fill"
                  style={{ width: `${profile.completionTendency * 100}%` }}
                ></div>
                <span className="tendency-value">{Math.round(profile.completionTendency * 100)}%</span>
              </div>
            </div>

            <div className="result-section tips-section">
              <h3><i className="bi bi-lightbulb-fill"></i> 집중력 팁</h3>
              <ul>
                {profile.tips.map((tip, idx) => (
                  <li key={idx}>{tip}</li>
                ))}
              </ul>
            </div>

            <button className="start-btn" onClick={handleComplete}>
              <i className="bi bi-play-fill"></i>
              이제 집중 시작하기
            </button>
          </div>
        </div>
      </StyledWrapper>
    );
  }

  // 설문 화면 (mode === 'survey')
  return (
    <StyledWrapper>
      <div className="survey-page">
        <div className="survey-header">
          <h1><i className="bi bi-clipboard-check"></i> 학습 성향 분석</h1>
          <p>8개의 질문으로 당신에게 딱 맞는 집중 루틴을 찾아드려요</p>
        </div>

        <div className="progress-container">
          <div className="progress-bar">
            <div className="progress-fill" style={{ width: `${progress}%` }}></div>
          </div>
          <span className="progress-text">{currentStep + 1} / {SURVEY_QUESTIONS.length}</span>
        </div>

        <div className="question-card">
          <h2 className="question-text">{currentQuestion.question}</h2>

          <div className="options-container">
            {currentQuestion.options.map((option) => (
              <button
                key={option.value}
                className={`option-btn ${answers[currentQuestion.id] === option.value ? 'selected' : ''}`}
                onClick={() => handleAnswer(currentQuestion.id, option.value)}
              >
                <i className={`bi ${option.icon}`}></i>
                <span>{option.text}</span>
              </button>
            ))}
          </div>
        </div>


        <div className="navigation">
          {currentStep > 0 ? (
            <button
              className="nav-btn prev"
              onClick={() => setCurrentStep(currentStep - 1)}
            >
              <i className="bi bi-chevron-left"></i>
              이전
            </button>
          ) : (
            <button
              className="nav-btn prev"
              onClick={() => setMode('choice')}
            >
              <i className="bi bi-chevron-left"></i>
              뒤로
            </button>
          )}
        </div>
      </div>
    </StyledWrapper>
  );
};

const StyledWrapper = styled.div`
  .survey-page {
    min-height: 100vh;
    background: linear-gradient(180deg, #FAFBFF 0%, #F0F4FF 100%);
    padding: 40px 20px;
    display: flex;
    flex-direction: column;
    align-items: center;
  }

  .survey-header {
    text-align: center;
    margin-bottom: 32px;

    h1 {
      font-size: 28px;
      font-weight: 700;
      color: #2D3748;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 12px;

      i {
        color: #6C63FF;
      }
    }

    p {
      color: #718096;
      margin-top: 8px;
      font-size: 15px;
    }
  }

  .progress-container {
    width: 100%;
    max-width: 500px;
    margin-bottom: 32px;
    display: flex;
    align-items: center;
    gap: 16px;
  }

  .progress-bar {
    flex: 1;
    height: 8px;
    background: #E2E8F0;
    border-radius: 4px;
    overflow: hidden;
  }

  .progress-fill {
    height: 100%;
    background: linear-gradient(90deg, #6C63FF 0%, #5046E5 100%);
    border-radius: 4px;
    transition: width 0.3s ease;
  }

  .progress-text {
    color: #6C63FF;
    font-weight: 600;
    font-size: 14px;
    min-width: 50px;
  }

  .question-card {
    background: #FFFFFF;
    border-radius: 24px;
    padding: 40px;
    width: 100%;
    max-width: 500px;
    box-shadow: 0 10px 40px rgba(108, 99, 255, 0.1);
    text-align: center;
  }

  .question-text {
    font-size: 22px;
    font-weight: 700;
    color: #2D3748;
    margin-bottom: 32px;
    line-height: 1.4;
  }

  .options-container {
    display: flex;
    flex-direction: column;
    gap: 16px;
  }

  .option-btn {
    display: flex;
    align-items: center;
    gap: 16px;
    padding: 20px 24px;
    background: #FAFBFF;
    border: 2px solid #E2E8F0;
    border-radius: 16px;
    font-size: 16px;
    color: #4A5568;
    text-align: left;
    transition: all 0.2s;

    i {
      font-size: 24px;
      color: #6C63FF;
    }

    &:hover {
      border-color: #6C63FF;
      background: #F0F4FF;
    }

    &.selected {
      border-color: #6C63FF;
      background: linear-gradient(135deg, #F0F4FF 0%, #E8EDFF 100%);

      i {
        color: #5046E5;
      }
    }
  }

  .skip-btn {
    margin-top: 24px;
    background: transparent;
    border: none;
    color: #A0AEC0;
    font-size: 14px;

    &:hover {
      color: #718096;
    }
  }

  .navigation {
    margin-top: 24px;
    display: flex;
    justify-content: center;
  }

  .nav-btn {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 12px 20px;
    background: #F0F4FF;
    border: none;
    border-radius: 12px;
    color: #6C63FF;
    font-size: 14px;
    font-weight: 600;
    transition: all 0.2s;

    &:hover {
      background: #E8EDFF;
    }
  }

  /* 초기 선택 화면 */
  .choice-container {
    display: flex;
    flex-direction: column;
    gap: 20px;
    width: 100%;
    max-width: 500px;
  }

  .choice-card {
    background: #FFFFFF;
    border: 2px solid #E2E8F0;
    border-radius: 20px;
    padding: 32px;
    text-align: center;
    transition: all 0.2s;
    cursor: pointer;

    &:hover {
      border-color: #6C63FF;
      transform: translateY(-4px);
      box-shadow: 0 10px 40px rgba(108, 99, 255, 0.15);
    }

    .choice-icon {
      width: 64px;
      height: 64px;
      background: linear-gradient(135deg, #F0F4FF 0%, #E8EDFF 100%);
      border-radius: 20px;
      display: flex;
      align-items: center;
      justify-content: center;
      margin: 0 auto 16px;

      i {
        font-size: 28px;
        color: #6C63FF;
      }
    }

    h3 {
      font-size: 18px;
      font-weight: 700;
      color: #2D3748;
      margin-bottom: 8px;
    }

    p {
      font-size: 14px;
      color: #718096;
    }
  }

  /* MBTI 선택 그리드 */
  .mbti-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 12px;
    width: 100%;
    max-width: 500px;
    margin-bottom: 24px;
  }

  .mbti-type-btn {
    background: #FFFFFF;
    border: 2px solid #E2E8F0;
    border-radius: 16px;
    padding: 16px 8px;
    text-align: center;
    transition: all 0.2s;

    &:hover {
      border-color: #6C63FF;
      background: #F0F4FF;
      transform: scale(1.05);
    }

    .type-code {
      display: block;
      font-size: 18px;
      font-weight: 800;
      color: #6C63FF;
      letter-spacing: 1px;
      margin-bottom: 4px;
    }

    .type-name {
      display: block;
      font-size: 11px;
      color: #718096;
    }
  }

  .back-btn {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 12px 24px;
    background: #F0F4FF;
    border: none;
    border-radius: 12px;
    color: #6C63FF;
    font-size: 14px;
    font-weight: 600;
    transition: all 0.2s;

    &:hover {
      background: #E8EDFF;
    }
  }

  /* 결과 페이지 */
  .result-page {
    padding-top: 20px;
  }

  .result-card {
    background: #FFFFFF;
    border-radius: 24px;
    padding: 32px;
    width: 100%;
    max-width: 500px;
    box-shadow: 0 10px 40px rgba(108, 99, 255, 0.15);
  }

  .result-header {
    text-align: center;
    margin-bottom: 24px;
    padding-bottom: 24px;
    border-bottom: 1px solid #E2E8F0;
  }

  .mbti-badge {
    display: inline-block;
    background: linear-gradient(135deg, #6C63FF 0%, #5046E5 100%);
    color: #FFFFFF;
    padding: 12px 32px;
    border-radius: 16px;
    font-size: 32px;
    font-weight: 800;
    letter-spacing: 4px;
    margin-bottom: 16px;
  }

  .result-name {
    font-size: 24px;
    font-weight: 700;
    color: #2D3748;
    margin-bottom: 4px;
  }

  .result-nickname {
    color: #718096;
    font-size: 15px;
  }

  .result-section {
    margin-bottom: 24px;

    h3 {
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 16px;
      font-weight: 600;
      color: #4A5568;
      margin-bottom: 12px;

      i {
        color: #6C63FF;
      }
    }

    p {
      color: #718096;
      font-size: 14px;
      line-height: 1.6;
    }
  }

  .time-range {
    display: flex;
    align-items: center;
    gap: 12px;
    flex-wrap: wrap;
  }

  .range-value {
    background: #F0F4FF;
    padding: 8px 16px;
    border-radius: 10px;
    font-weight: 700;
    color: #6C63FF;
    font-size: 16px;
  }

  .range-label {
    color: #A0AEC0;
    font-size: 13px;
  }

  .tendency-bar {
    position: relative;
    height: 24px;
    background: #E2E8F0;
    border-radius: 12px;
    overflow: hidden;
  }

  .tendency-fill {
    height: 100%;
    background: linear-gradient(90deg, #48BB78 0%, #38A169 100%);
    border-radius: 12px;
    transition: width 1s ease;
  }

  .tendency-value {
    position: absolute;
    right: 12px;
    top: 50%;
    transform: translateY(-50%);
    font-weight: 700;
    font-size: 13px;
    color: #2D3748;
  }

  .tips-section {
    background: #FAFBFF;
    padding: 20px;
    border-radius: 16px;
    margin-bottom: 24px;

    ul {
      list-style: none;
      padding: 0;
      margin: 0;

      li {
        position: relative;
        padding-left: 20px;
        margin-bottom: 10px;
        color: #4A5568;
        font-size: 14px;
        line-height: 1.5;

        &::before {
          content: "✓";
          position: absolute;
          left: 0;
          color: #48BB78;
          font-weight: bold;
        }

        &:last-child {
          margin-bottom: 0;
        }
      }
    }
  }

  .start-btn {
    width: 100%;
    padding: 18px;
    background: linear-gradient(135deg, #6C63FF 0%, #5046E5 100%);
    color: #FFFFFF;
    border: none;
    border-radius: 16px;
    font-size: 18px;
    font-weight: 700;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 10px;
    transition: all 0.2s;
    box-shadow: 0 4px 16px rgba(108, 99, 255, 0.3);

    &:hover {
      transform: translateY(-2px);
      box-shadow: 0 6px 20px rgba(108, 99, 255, 0.4);
    }

    i {
      font-size: 20px;
    }
  }

  @media (max-width: 768px) {
    .survey-page {
      padding: 24px 16px;
    }

    .survey-header h1 {
      font-size: 22px;
    }

    .question-card {
      padding: 28px 20px;
    }

    .question-text {
      font-size: 18px;
    }

    .option-btn {
      padding: 16px 18px;
      font-size: 14px;
    }
  }
`;

export default SurveyPage;
