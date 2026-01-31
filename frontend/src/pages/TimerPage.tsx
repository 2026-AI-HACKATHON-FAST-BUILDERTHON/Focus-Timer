import React, { useState, useCallback, useEffect } from 'react';
import styled from 'styled-components';
import Hamster from '../components/character/Hamster';
import StatusText from '../components/character/StatusText';
import TimerDisplay from '../components/timer/TimerDisplay';
import Controls from '../components/timer/Controls';
import SessionSetup, { SessionConfig } from '../components/session/SessionSetup';
import AbortModal, { AbortReason } from '../components/session/AbortModal';
import AnalysisPage from './AnalysisPage';
import { useTimer, TimerPhase } from '../hooks/useTimer';
import * as api from '../services/api';

type PageState = 'setup' | 'running' | 'completed';

// 설정 타입
interface Settings {
  soundEnabled: boolean;
  vibrationEnabled: boolean;
  autoBreakAlert: boolean;
  aiRecommendation: boolean;
}

// 통계 타입
interface Stats {
  totalCoins: number;
  completedSessions: number;
  streakDays: number;
  completionRate: number;
  weeklyMinutes: number[];
}

// 도전과제 타입
interface Achievement {
  id: string;
  name: string;
  description: string;
  category: string;
  rarity: string;
  icon: string;
  coinReward: number;
  unlocked: boolean;
  progress?: number;
}

// 도전과제 데이터 (실제로는 API에서 가져옴)
const ACHIEVEMENTS_DATA: Achievement[] = [
  { id: 'first_session', name: '첫 걸음', description: '첫 세션 완료', category: 'focus', rarity: 'common', icon: 'bi-play-circle-fill', coinReward: 10, unlocked: true },
  { id: 'focus_10', name: '입문자', description: '10회 세션 완료', category: 'focus', rarity: 'common', icon: 'bi-lightning-fill', coinReward: 50, unlocked: true },
  { id: 'focus_50', name: '집중러', description: '50회 세션 완료', category: 'focus', rarity: 'uncommon', icon: 'bi-fire', coinReward: 100, unlocked: false, progress: 0.24 },
  { id: 'streak_3', name: '3일 연속', description: '3일 연속 집중', category: 'streak', rarity: 'common', icon: 'bi-calendar-check', coinReward: 30, unlocked: true },
  { id: 'streak_7', name: '일주일 도전', description: '7일 연속 집중', category: 'streak', rarity: 'uncommon', icon: 'bi-trophy', coinReward: 100, unlocked: false, progress: 0.43 },
  { id: 'streak_30', name: '한 달 마스터', description: '30일 연속 집중', category: 'streak', rarity: 'rare', icon: 'bi-award-fill', coinReward: 500, unlocked: false, progress: 0.1 },
  { id: 'early_bird', name: '얼리버드', description: '오전 6시 이전 세션', category: 'time', rarity: 'uncommon', icon: 'bi-sunrise-fill', coinReward: 50, unlocked: false },
  { id: 'night_owl', name: '올빼미', description: '자정 이후 세션 완료', category: 'time', rarity: 'uncommon', icon: 'bi-moon-stars-fill', coinReward: 50, unlocked: true },
  { id: 'focus_60min', name: '1시간 도전', description: '60분 이상 집중', category: 'focus', rarity: 'rare', icon: 'bi-hourglass-split', coinReward: 100, unlocked: false, progress: 0.75 },
  { id: 'all_tasks', name: '만능 학습자', description: '모든 과제 유형 완료', category: 'milestone', rarity: 'rare', icon: 'bi-grid-fill', coinReward: 200, unlocked: false, progress: 0.5 },
  { id: 'comeback_kid', name: '돌아온 집중러', description: '7일 후 복귀 세션', category: 'special', rarity: 'uncommon', icon: 'bi-arrow-repeat', coinReward: 75, unlocked: false },
  { id: 'perfectionist', name: '완벽주의자', description: '5연속 완주', category: 'special', rarity: 'epic', icon: 'bi-star-fill', coinReward: 300, unlocked: false, progress: 0.4 },
];

// MBTI 프로필 데이터
const MBTI_PROFILES: Record<string, { name: string; nickname: string; focusRange: [number, number] }> = {
  INTJ: { name: '전략가', nickname: '용의주도한 전략가', focusRange: [35, 50] },
  INTP: { name: '논리술사', nickname: '호기심 많은 사색가', focusRange: [30, 45] },
  ENTJ: { name: '통솔자', nickname: '대담한 통솔자', focusRange: [25, 35] },
  ENTP: { name: '변론가', nickname: '논쟁을 즐기는 변론가', focusRange: [15, 25] },
  INFJ: { name: '옹호자', nickname: '선의의 옹호자', focusRange: [30, 45] },
  INFP: { name: '중재자', nickname: '열정적인 중재자', focusRange: [20, 35] },
  ENFJ: { name: '선도자', nickname: '정의로운 사회운동가', focusRange: [25, 35] },
  ENFP: { name: '활동가', nickname: '재기발랄한 활동가', focusRange: [15, 25] },
  ISTJ: { name: '현실주의자', nickname: '청렴결백한 논리주의자', focusRange: [30, 45] },
  ISFJ: { name: '수호자', nickname: '용감한 수호자', focusRange: [25, 40] },
  ESTJ: { name: '경영자', nickname: '엄격한 관리자', focusRange: [25, 35] },
  ESFJ: { name: '집정관', nickname: '사교적인 외교관', focusRange: [20, 30] },
  ISTP: { name: '장인', nickname: '만능 재주꾼', focusRange: [20, 30] },
  ISFP: { name: '모험가', nickname: '호기심 많은 예술가', focusRange: [15, 25] },
  ESTP: { name: '사업가', nickname: '모험을 즐기는 사업가', focusRange: [15, 25] },
  ESFP: { name: '연예인', nickname: '자유로운 영혼의 연예인', focusRange: [10, 20] },
};

interface TimerPageProps {
  userMBTI?: string | null;
}

const TimerPage: React.FC<TimerPageProps> = ({ userMBTI }) => {
  const [pageState, setPageState] = useState<PageState>('setup');
  const [sessionConfig, setSessionConfig] = useState<SessionConfig | null>(null);
  const [showAbortModal, setShowAbortModal] = useState(false);
  const [showStatsModal, setShowStatsModal] = useState(false);
  const [showSettingsModal, setShowSettingsModal] = useState(false);
  const [showAchievementsModal, setShowAchievementsModal] = useState(false);
  const [showMBTIModal, setShowMBTIModal] = useState(false);
  const [showAnalysisModal, setShowAnalysisModal] = useState(false);
  const [achievements] = useState<Achievement[]>(ACHIEVEMENTS_DATA);
  const [earnedCoins, setEarnedCoins] = useState(0);

  // AI 추천 상태
  const [recommendation, setRecommendation] = useState<{
    focusMinutes: number;
    breakMinutes: number;
    reason: string;
    completionProb?: number;
    riskLevel?: string;
    microRoutine?: string | null;
  } | null>(null);
  const [isLoadingRecommendation, setIsLoadingRecommendation] = useState(false);

  // 실제 설정 상태 관리
  const [settings, setSettings] = useState<Settings>(() => {
    const saved = localStorage.getItem('focusTimerSettings');
    return saved ? JSON.parse(saved) : {
      soundEnabled: true,
      vibrationEnabled: true,
      autoBreakAlert: true,
      aiRecommendation: true,
    };
  });

  // 실제 통계 상태 관리
  const [stats, setStats] = useState<Stats>(() => {
    const saved = localStorage.getItem('focusTimerStats');
    return saved ? JSON.parse(saved) : {
      totalCoins: 150,
      completedSessions: 12,
      streakDays: 3,
      completionRate: 85,
      weeklyMinutes: [45, 60, 30, 75, 50, 20, 0], // 월~일
    };
  });

  // 설정 저장
  const updateSetting = (key: keyof Settings, value: boolean) => {
    const newSettings = { ...settings, [key]: value };
    setSettings(newSettings);
    localStorage.setItem('focusTimerSettings', JSON.stringify(newSettings));
  };

  // 통계 저장
  const updateStats = useCallback((newStats: Partial<Stats>) => {
    setStats(prev => {
      const updated = { ...prev, ...newStats };
      localStorage.setItem('focusTimerStats', JSON.stringify(updated));
      return updated;
    });
  }, []);

  // AI 추천 가져오기
  const fetchRecommendation = useCallback(async () => {
    if (!settings.aiRecommendation) return;

    setIsLoadingRecommendation(true);
    try {
      const now = new Date();
      const response = await api.getRecommendation({
        task_type: 'reading',
        difficulty: 3,
        hour: now.getHours(),
        day_of_week: now.getDay() === 0 ? 6 : now.getDay() - 1,
      });

      // 첫 번째 집중 페이즈에서 시간 추출
      const focusPhase = response.recommended_loop.find(p => p.type === 'focus');
      const breakPhase = response.recommended_loop.find(p => p.type === 'break');

      setRecommendation({
        focusMinutes: focusPhase?.minutes || 25,
        breakMinutes: breakPhase?.minutes || 5,
        reason: response.reason,
        completionProb: response.predicted_completion_prob,
        riskLevel: response.risk_level,
        microRoutine: response.micro_routine,
      });
    } catch (error) {
      console.error('Failed to fetch recommendation:', error);
      // MBTI 기반 폴백 추천
      if (userMBTI && MBTI_PROFILES[userMBTI]) {
        const profile = MBTI_PROFILES[userMBTI];
        const avgFocus = Math.round((profile.focusRange[0] + profile.focusRange[1]) / 2);
        setRecommendation({
          focusMinutes: avgFocus,
          breakMinutes: 5,
          reason: `${profile.name} 유형에 맞는 ${avgFocus}분 집중을 추천해요!`,
        });
      } else {
        setRecommendation({
          focusMinutes: 25,
          breakMinutes: 5,
          reason: '25분 집중 + 5분 휴식으로 시작해보세요!',
        });
      }
    } finally {
      setIsLoadingRecommendation(false);
    }
  }, [settings.aiRecommendation, userMBTI]);

  // 컴포넌트 마운트 시 추천 가져오기
  useEffect(() => {
    if (pageState === 'setup') {
      fetchRecommendation();
    }
  }, [pageState, fetchRecommendation]);

  const handlePhaseComplete = useCallback((phase: TimerPhase) => {
    if (phase.type === 'focus') {
      console.log('Focus phase complete!');
    }
  }, []);

  const handleSessionComplete = useCallback(() => {
    if (sessionConfig) {
      const totalFocusMinutes = sessionConfig.focusMinutes * sessionConfig.rounds;
      const coins = totalFocusMinutes * 10;
      setEarnedCoins(coins);

      // 통계 업데이트
      const today = new Date().getDay();
      const dayIndex = today === 0 ? 6 : today - 1; // 월=0, 일=6
      const newWeeklyMinutes = [...stats.weeklyMinutes];
      newWeeklyMinutes[dayIndex] += totalFocusMinutes;

      updateStats({
        totalCoins: stats.totalCoins + coins,
        completedSessions: stats.completedSessions + 1,
        weeklyMinutes: newWeeklyMinutes,
      });
    }
    setPageState('completed');
  }, [sessionConfig, stats, updateStats]);

  const timer = useTimer({
    onPhaseComplete: handlePhaseComplete,
    onSessionComplete: handleSessionComplete,
  });

  const handleStartSession = (config: SessionConfig) => {
    setSessionConfig(config);

    const phases: TimerPhase[] = [];
    for (let i = 0; i < config.rounds; i++) {
      phases.push({ type: 'focus', minutes: config.focusMinutes });
      if (i < config.rounds - 1) {
        phases.push({ type: 'break', minutes: config.breakMinutes });
      }
    }

    timer.start(phases);
    setPageState('running');
  };

  const handlePauseResume = () => {
    if (timer.isPaused) {
      timer.resume();
    } else {
      timer.pause();
    }
  };

  const handleStop = () => {
    setShowAbortModal(true);
  };

  const handleAbortConfirm = (reason: AbortReason, detail?: string) => {
    console.log('Session aborted:', reason, detail);
    timer.stop();
    setShowAbortModal(false);
    setPageState('setup');
  };

  const handleNewSession = () => {
    setPageState('setup');
    setSessionConfig(null);
    setEarnedCoins(0);
  };

  // 달성 시간에 따른 축하 메시지
  const getCompletionMessage = () => {
    if (!sessionConfig) return '훌륭해요! 오늘도 집중력을 발휘했어요.';

    const totalMinutes = sessionConfig.focusMinutes * sessionConfig.rounds;

    if (totalMinutes >= 120) {
      return '대단해요! 2시간 이상 집중하다니, 당신은 집중력 마스터! 🏆';
    } else if (totalMinutes >= 90) {
      return '와우! 90분 넘게 집중했어요. 프로 집중러 인정! 💪';
    } else if (totalMinutes >= 60) {
      return '1시간 집중 완료! 오늘 정말 열심히 했어요! ⭐';
    } else if (totalMinutes >= 45) {
      return '45분 집중 성공! 꾸준히 하면 습관이 돼요! 🌟';
    } else if (totalMinutes >= 30) {
      return '30분 완주! 작은 성공이 큰 변화를 만들어요! 🎯';
    } else if (totalMinutes >= 15) {
      return '15분 집중 성공! 시작이 반이에요! 🚀';
    } else {
      return '짧지만 해냈어요! 내일은 조금 더 도전해볼까요? 💫';
    }
  };

  return (
    <StyledWrapper>
      <div className="timer-page">
        <header className="header">
          <h1 className="logo">
            <i className="bi bi-clock-fill"></i>
            Focus Timer
          </h1>
          <div className="header-actions">
            {userMBTI && MBTI_PROFILES[userMBTI] && (
              <button className="mbti-badge-btn" onClick={() => setShowMBTIModal(true)}>
                <span className="mbti-type">{userMBTI}</span>
              </button>
            )}
            <button className="header-btn analysis-btn" onClick={() => setShowAnalysisModal(true)} title="AI 분석">
              <i className="bi bi-cpu-fill"></i>
            </button>
            <button className="header-btn" onClick={() => setShowAchievementsModal(true)}>
              <i className="bi bi-trophy-fill"></i>
            </button>
            <button className="header-btn" onClick={() => setShowStatsModal(true)}>
              <i className="bi bi-bar-chart-fill"></i>
            </button>
            <button className="header-btn" onClick={() => setShowSettingsModal(true)}>
              <i className="bi bi-gear-fill"></i>
            </button>
          </div>
        </header>

        <main className="main-content">
          {pageState === 'setup' && (
            <div className="setup-page">
              <div className="idle-hamster">
                <Hamster isRunning={true} speed="slow" />
              </div>
              <SessionSetup
                onStart={handleStartSession}
                recommendation={recommendation || undefined}
                isLoading={isLoadingRecommendation}
              />
            </div>
          )}

          {pageState === 'running' && (
            <div className="running-container">
              <div className="character-section">
                <Hamster
                  isRunning={timer.isRunning && !timer.isPaused}
                  speed={timer.isPaused ? 'slow' : 'normal'}
                />
                <StatusText isRunning={timer.currentPhase?.type === 'focus'} />
              </div>

              <div className="timer-section">
                <div className="round-indicator">
                  라운드 {timer.currentRound} / {timer.totalRounds}
                </div>

                <TimerDisplay
                  minutes={timer.minutes}
                  seconds={timer.seconds}
                  isBreak={timer.currentPhase?.type === 'break'}
                />

                {sessionConfig?.goal && (
                  <div className="goal-display">
                    <i className="bi bi-flag-fill"></i>
                    {sessionConfig.goal}
                  </div>
                )}
              </div>

              <Controls
                isRunning={timer.isRunning && !timer.isPaused}
                onStart={handlePauseResume}
                onPause={handlePauseResume}
                onStop={handleStop}
                onSkip={timer.skip}
              />
            </div>
          )}

          {pageState === 'completed' && (
            <div className="completed-container">
              <div className="celebration">
                <i className="bi bi-trophy-fill"></i>
              </div>
              <h2 className="completed-title">세션 완료!</h2>
              <p className="completed-message">
                {getCompletionMessage()}
              </p>

              <div className="reward-card">
                <div className="reward-icon">
                  <i className="bi bi-coin"></i>
                </div>
                <div className="reward-amount">+{earnedCoins}</div>
                <div className="reward-label">코인 획득</div>
              </div>

              {sessionConfig && (
                <div className="session-summary">
                  <div className="summary-item">
                    <span className="summary-label">총 집중 시간</span>
                    <span className="summary-value">
                      {sessionConfig.focusMinutes * sessionConfig.rounds}분
                    </span>
                  </div>
                  <div className="summary-item">
                    <span className="summary-label">완료 라운드</span>
                    <span className="summary-value">{sessionConfig.rounds}회</span>
                  </div>
                </div>
              )}

              <button className="new-session-btn" onClick={handleNewSession}>
                <i className="bi bi-arrow-repeat"></i>
                새 세션 시작
              </button>
            </div>
          )}
        </main>

        <AbortModal
          isOpen={showAbortModal}
          onClose={() => setShowAbortModal(false)}
          onConfirm={handleAbortConfirm}
        />

        {/* 통계 모달 */}
        {showStatsModal && (
          <div className="modal-overlay" onClick={() => setShowStatsModal(false)}>
            <div className="modal-content stats-modal" onClick={(e) => e.stopPropagation()}>
              <div className="modal-header">
                <h3><i className="bi bi-bar-chart-fill"></i> 나의 통계</h3>
                <button className="close-btn" onClick={() => setShowStatsModal(false)}>
                  <i className="bi bi-x-lg"></i>
                </button>
              </div>
              <div className="stats-grid">
                <div className="stat-card">
                  <i className="bi bi-coin"></i>
                  <div className="stat-value">{stats.totalCoins}</div>
                  <div className="stat-label">보유 코인</div>
                </div>
                <div className="stat-card">
                  <i className="bi bi-clock-history"></i>
                  <div className="stat-value">{stats.completedSessions}</div>
                  <div className="stat-label">완료 세션</div>
                </div>
                <div className="stat-card">
                  <i className="bi bi-fire"></i>
                  <div className="stat-value">{stats.streakDays}일</div>
                  <div className="stat-label">연속 집중</div>
                </div>
                <div className="stat-card">
                  <i className="bi bi-trophy"></i>
                  <div className="stat-value">{stats.completionRate}%</div>
                  <div className="stat-label">완주율</div>
                </div>
              </div>
              <div className="weekly-chart">
                <h4>이번 주 집중 시간 (분)</h4>
                <div className="chart-bars">
                  {['월', '화', '수', '목', '금', '토', '일'].map((day, index) => {
                    const maxMinutes = Math.max(...stats.weeklyMinutes, 60);
                    const height = stats.weeklyMinutes[index] > 0
                      ? Math.max((stats.weeklyMinutes[index] / maxMinutes) * 100, 10)
                      : 5;
                    const today = new Date().getDay();
                    const isToday = index === (today === 0 ? 6 : today - 1);
                    return (
                      <div className="bar-item" key={day}>
                        <div className="bar-value">{stats.weeklyMinutes[index]}</div>
                        <div
                          className={`bar ${isToday ? 'active' : ''}`}
                          style={{ height: `${height}%` }}
                        ></div>
                        <span className={isToday ? 'today' : ''}>{day}</span>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* 설정 모달 */}
        {showSettingsModal && (
          <div className="modal-overlay" onClick={() => setShowSettingsModal(false)}>
            <div className="modal-content settings-modal" onClick={(e) => e.stopPropagation()}>
              <div className="modal-header">
                <h3><i className="bi bi-gear-fill"></i> 설정</h3>
                <button className="close-btn" onClick={() => setShowSettingsModal(false)}>
                  <i className="bi bi-x-lg"></i>
                </button>
              </div>
              <div className="settings-list">
                <div className="setting-item">
                  <div className="setting-info">
                    <i className="bi bi-bell"></i>
                    <span>알림 소리</span>
                  </div>
                  <label className="toggle">
                    <input
                      type="checkbox"
                      checked={settings.soundEnabled}
                      onChange={(e) => updateSetting('soundEnabled', e.target.checked)}
                    />
                    <span className="slider"></span>
                  </label>
                </div>
                <div className="setting-item">
                  <div className="setting-info">
                    <i className="bi bi-phone-vibrate"></i>
                    <span>진동</span>
                  </div>
                  <label className="toggle">
                    <input
                      type="checkbox"
                      checked={settings.vibrationEnabled}
                      onChange={(e) => updateSetting('vibrationEnabled', e.target.checked)}
                    />
                    <span className="slider"></span>
                  </label>
                </div>
                <div className="setting-item">
                  <div className="setting-info">
                    <i className="bi bi-moon-stars"></i>
                    <span>자동 휴식 알림</span>
                  </div>
                  <label className="toggle">
                    <input
                      type="checkbox"
                      checked={settings.autoBreakAlert}
                      onChange={(e) => updateSetting('autoBreakAlert', e.target.checked)}
                    />
                    <span className="slider"></span>
                  </label>
                </div>
                <div className="setting-item">
                  <div className="setting-info">
                    <i className="bi bi-lightbulb"></i>
                    <span>AI 추천 사용</span>
                  </div>
                  <label className="toggle">
                    <input
                      type="checkbox"
                      checked={settings.aiRecommendation}
                      onChange={(e) => updateSetting('aiRecommendation', e.target.checked)}
                    />
                    <span className="slider"></span>
                  </label>
                </div>
              </div>
              <div className="settings-note">
                <i className="bi bi-info-circle"></i>
                설정은 자동으로 저장됩니다
              </div>
              <button className="retake-survey-btn" onClick={() => {
                localStorage.removeItem('mbtiSurveyCompleted');
                localStorage.removeItem('userMBTI');
                window.location.reload();
              }}>
                <i className="bi bi-arrow-repeat"></i>
                학습 성향 다시 분석하기
              </button>
              <button className="logout-btn" onClick={() => {
                localStorage.clear();
                window.location.reload();
              }}>
                <i className="bi bi-box-arrow-right"></i>
                로그아웃
              </button>
            </div>
          </div>
        )}

        {/* MBTI 모달 */}
        {showMBTIModal && userMBTI && MBTI_PROFILES[userMBTI] && (
          <div className="modal-overlay" onClick={() => setShowMBTIModal(false)}>
            <div className="modal-content mbti-modal" onClick={(e) => e.stopPropagation()}>
              <div className="modal-header">
                <h3><i className="bi bi-person-badge-fill"></i> 나의 학습 성향</h3>
                <button className="close-btn" onClick={() => setShowMBTIModal(false)}>
                  <i className="bi bi-x-lg"></i>
                </button>
              </div>
              <div className="mbti-result">
                <div className="mbti-type-badge">{userMBTI}</div>
                <h4 className="mbti-profile-name">{MBTI_PROFILES[userMBTI].name}</h4>
                <p className="mbti-profile-nickname">{MBTI_PROFILES[userMBTI].nickname}</p>
              </div>
              <div className="mbti-recommendation">
                <h5><i className="bi bi-clock-fill"></i> 추천 집중 시간</h5>
                <div className="time-recommend">
                  <span className="time-value">
                    {MBTI_PROFILES[userMBTI].focusRange[0]}~{MBTI_PROFILES[userMBTI].focusRange[1]}분
                  </span>
                </div>
                <p className="recommend-note">
                  당신의 성향에 맞는 집중 시간이에요. AI가 이를 바탕으로 최적의 루틴을 추천해드릴게요!
                </p>
              </div>
              <button className="retake-btn" onClick={() => {
                localStorage.removeItem('mbtiSurveyCompleted');
                localStorage.removeItem('userMBTI');
                window.location.reload();
              }}>
                <i className="bi bi-arrow-repeat"></i>
                다시 분석하기
              </button>
            </div>
          </div>
        )}

        {/* 도전과제 모달 */}
        {showAchievementsModal && (
          <div className="modal-overlay" onClick={() => setShowAchievementsModal(false)}>
            <div className="modal-content achievements-modal" onClick={(e) => e.stopPropagation()}>
              <div className="modal-header">
                <h3><i className="bi bi-trophy-fill"></i> 도전 과제</h3>
                <button className="close-btn" onClick={() => setShowAchievementsModal(false)}>
                  <i className="bi bi-x-lg"></i>
                </button>
              </div>
              <div className="achievements-summary">
                <div className="summary-stat">
                  <span className="count">{achievements.filter(a => a.unlocked).length}</span>
                  <span className="label">획득</span>
                </div>
                <div className="summary-divider"></div>
                <div className="summary-stat">
                  <span className="count">{achievements.length}</span>
                  <span className="label">전체</span>
                </div>
                <div className="summary-divider"></div>
                <div className="summary-stat">
                  <span className="count">{achievements.filter(a => a.unlocked).reduce((sum, a) => sum + a.coinReward, 0)}</span>
                  <span className="label">코인</span>
                </div>
              </div>
              <div className="achievements-list">
                {achievements.map((ach) => (
                  <div key={ach.id} className={`achievement-item ${ach.unlocked ? 'unlocked' : 'locked'} ${ach.rarity}`}>
                    <div className={`achievement-icon ${ach.unlocked ? '' : 'locked'}`}>
                      <i className={`bi ${ach.icon}`}></i>
                    </div>
                    <div className="achievement-info">
                      <div className="achievement-header">
                        <span className="achievement-name">{ach.name}</span>
                        <span className={`rarity-badge ${ach.rarity}`}>
                          {ach.rarity === 'common' ? '일반' :
                           ach.rarity === 'uncommon' ? '희귀' :
                           ach.rarity === 'rare' ? '레어' :
                           ach.rarity === 'epic' ? '에픽' : '전설'}
                        </span>
                      </div>
                      <span className="achievement-desc">{ach.description}</span>
                      {!ach.unlocked && ach.progress !== undefined && (
                        <div className="progress-bar">
                          <div className="progress-fill" style={{ width: `${ach.progress * 100}%` }}></div>
                        </div>
                      )}
                    </div>
                    <div className="achievement-reward">
                      <i className="bi bi-coin"></i>
                      <span>{ach.coinReward}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* AI 분석 모달 */}
        {showAnalysisModal && (
          <div className="modal-overlay" onClick={() => setShowAnalysisModal(false)}>
            <div className="modal-content analysis-modal" onClick={(e) => e.stopPropagation()}>
              <div className="modal-header">
                <h3><i className="bi bi-cpu-fill"></i> AI 분석 대시보드</h3>
                <button className="close-btn" onClick={() => setShowAnalysisModal(false)}>
                  <i className="bi bi-x-lg"></i>
                </button>
              </div>
              <div className="analysis-modal-body">
                <AnalysisPage />
              </div>
            </div>
          </div>
        )}
      </div>
    </StyledWrapper>
  );
};

const StyledWrapper = styled.div`
  .timer-page {
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    background: linear-gradient(180deg, #FAFBFF 0%, #F0F4FF 100%);
  }

  .header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 20px 32px;
    background: #FFFFFF;
    border-bottom: 1px solid #E2E8F0;
  }

  .logo {
    display: flex;
    align-items: center;
    gap: 10px;
    font-size: 22px;
    font-weight: 700;
    color: #6C63FF;

    i {
      font-size: 26px;
    }
  }

  .header-actions {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .mbti-badge-btn {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 8px 14px;
    background: linear-gradient(135deg, #6C63FF 0%, #5046E5 100%);
    border: none;
    border-radius: 12px;
    color: #FFFFFF;
    transition: all 0.2s;
    margin-right: 4px;

    .mbti-type {
      font-weight: 700;
      font-size: 14px;
      letter-spacing: 1px;
    }

    .mbti-name {
      font-size: 12px;
      opacity: 0.9;
    }

    &:hover {
      transform: translateY(-1px);
      box-shadow: 0 4px 12px rgba(108, 99, 255, 0.3);
    }
  }

  .header-btn {
    background: #F0F4FF;
    border: none;
    color: #6C63FF;
    width: 44px;
    height: 44px;
    border-radius: 12px;
    font-size: 18px;
    transition: all 0.2s;

    &:hover {
      background: #6C63FF;
      color: #FFFFFF;
    }
  }

  .main-content {
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 32px;
  }

  /* Setup 페이지 */
  .setup-page {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 32px;
    width: 100%;
    max-width: 500px;
  }

  .idle-hamster {
    display: flex;
    justify-content: center;
  }

  /* Running 상태 */
  .running-container {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 28px;
  }

  .character-section {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 16px;
  }

  .timer-section {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 16px;
  }

  .round-indicator {
    background: #FFFFFF;
    padding: 10px 24px;
    border-radius: 20px;
    color: #6C63FF;
    font-size: 14px;
    font-weight: 600;
    box-shadow: 0 2px 8px rgba(108, 99, 255, 0.1);
  }

  .goal-display {
    display: flex;
    align-items: center;
    gap: 8px;
    color: #718096;
    font-size: 14px;
    margin-top: 8px;

    i {
      color: #6C63FF;
    }
  }

  /* Completed 상태 */
  .completed-container {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 20px;
    text-align: center;
  }

  .celebration {
    font-size: 72px;
    color: #F6AD55;
    animation: bounce 1s ease infinite;
  }

  @keyframes bounce {
    0%, 100% {
      transform: translateY(0);
    }
    50% {
      transform: translateY(-16px);
    }
  }

  .completed-title {
    font-size: 28px;
    font-weight: 700;
    color: #2D3748;
  }

  .completed-message {
    color: #718096;
    font-size: 16px;
  }

  .reward-card {
    background: linear-gradient(135deg, #FFFAF0 0%, #FFF5EB 100%);
    border: 2px solid #F6AD55;
    border-radius: 20px;
    padding: 24px 48px;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 4px;
  }

  .reward-icon {
    font-size: 36px;
    color: #F6AD55;

    i {
      font-size: 40px;
    }
  }

  .reward-amount {
    font-size: 32px;
    font-weight: 700;
    color: #DD6B20;
  }

  .reward-label {
    color: #A0AEC0;
    font-size: 14px;
  }

  .session-summary {
    display: flex;
    gap: 32px;
    margin-top: 8px;
  }

  .summary-item {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 4px;
  }

  .summary-label {
    color: #A0AEC0;
    font-size: 12px;
  }

  .summary-value {
    color: #2D3748;
    font-size: 18px;
    font-weight: 600;
  }

  .new-session-btn {
    background: linear-gradient(135deg, #6C63FF 0%, #5046E5 100%);
    color: #FFFFFF;
    border: none;
    padding: 16px 40px;
    border-radius: 12px;
    font-size: 16px;
    font-weight: 600;
    display: flex;
    align-items: center;
    gap: 10px;
    margin-top: 16px;
    transition: all 0.2s;
    box-shadow: 0 4px 16px rgba(108, 99, 255, 0.3);

    &:hover {
      transform: translateY(-2px);
      box-shadow: 0 6px 20px rgba(108, 99, 255, 0.4);
    }
  }

  /* 모달 공통 스타일 */
  .modal-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(45, 55, 72, 0.6);
    backdrop-filter: blur(4px);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
    padding: 20px;
  }

  .modal-content {
    background: #FFFFFF;
    border-radius: 24px;
    padding: 28px;
    max-width: 400px;
    width: 100%;
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
  }

  .modal-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 24px;

    h3 {
      display: flex;
      align-items: center;
      gap: 10px;
      color: #2D3748;
      font-size: 20px;
      font-weight: 700;

      i {
        color: #6C63FF;
      }
    }
  }

  .close-btn {
    background: #F0F4FF;
    border: none;
    width: 36px;
    height: 36px;
    border-radius: 10px;
    color: #6C63FF;
    font-size: 16px;
    transition: all 0.2s;

    &:hover {
      background: #6C63FF;
      color: #FFFFFF;
    }
  }

  /* 통계 모달 */
  .stats-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 12px;
    margin-bottom: 24px;
  }

  .stat-card {
    background: #F0F4FF;
    border-radius: 16px;
    padding: 16px;
    text-align: center;

    i {
      font-size: 24px;
      color: #6C63FF;
      margin-bottom: 8px;
    }

    .stat-value {
      font-size: 24px;
      font-weight: 700;
      color: #2D3748;
    }

    .stat-label {
      font-size: 12px;
      color: #718096;
      margin-top: 4px;
    }
  }

  .weekly-chart {
    background: #FAFBFF;
    border-radius: 16px;
    padding: 20px;

    h4 {
      color: #4A5568;
      font-size: 14px;
      font-weight: 600;
      margin-bottom: 16px;
    }
  }

  .chart-bars {
    display: flex;
    justify-content: space-between;
    align-items: flex-end;
    height: 100px;
  }

  .bar-item {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 4px;
    flex: 1;

    .bar-value {
      font-size: 10px;
      color: #6C63FF;
      font-weight: 600;
      min-height: 14px;
    }

    .bar {
      width: 24px;
      background: #E2E8F0;
      border-radius: 6px;
      transition: all 0.3s;
      min-height: 4px;

      &.active {
        background: linear-gradient(180deg, #6C63FF 0%, #5046E5 100%);
      }
    }

    span {
      font-size: 12px;
      color: #718096;

      &.today {
        color: #6C63FF;
        font-weight: 600;
      }
    }
  }

  .settings-note {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 6px;
    color: #48BB78;
    font-size: 12px;
    margin-bottom: 16px;

    i {
      font-size: 14px;
    }
  }

  /* 설정 모달 */
  .settings-list {
    display: flex;
    flex-direction: column;
    gap: 16px;
    margin-bottom: 24px;
  }

  .setting-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 16px;
    background: #FAFBFF;
    border-radius: 12px;
  }

  .setting-info {
    display: flex;
    align-items: center;
    gap: 12px;
    color: #4A5568;
    font-size: 15px;

    i {
      font-size: 18px;
      color: #6C63FF;
    }
  }

  .toggle {
    position: relative;
    width: 48px;
    height: 26px;

    input {
      opacity: 0;
      width: 0;
      height: 0;
    }

    .slider {
      position: absolute;
      cursor: pointer;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      background: #E2E8F0;
      border-radius: 26px;
      transition: 0.3s;

      &::before {
        position: absolute;
        content: "";
        height: 20px;
        width: 20px;
        left: 3px;
        bottom: 3px;
        background: white;
        border-radius: 50%;
        transition: 0.3s;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
      }
    }

    input:checked + .slider {
      background: #6C63FF;
    }

    input:checked + .slider::before {
      transform: translateX(22px);
    }
  }

  .retake-survey-btn {
    width: 100%;
    padding: 14px;
    background: #F0F4FF;
    border: 2px solid #6C63FF;
    border-radius: 12px;
    color: #6C63FF;
    font-size: 15px;
    font-weight: 600;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    transition: all 0.2s;
    margin-bottom: 12px;

    &:hover {
      background: #E8EDFF;
    }
  }

  .logout-btn {
    width: 100%;
    padding: 14px;
    background: #FFF5F5;
    border: 2px solid #FC8181;
    border-radius: 12px;
    color: #E53E3E;
    font-size: 15px;
    font-weight: 600;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    transition: all 0.2s;

    &:hover {
      background: #FED7D7;
    }
  }

  /* MBTI 모달 */
  .mbti-modal {
    max-width: 400px;
    text-align: center;
  }

  .mbti-result {
    padding: 24px;
    background: linear-gradient(135deg, #F0F4FF 0%, #E8EDFF 100%);
    border-radius: 16px;
    margin-bottom: 20px;
  }

  .mbti-type-badge {
    display: inline-block;
    background: linear-gradient(135deg, #6C63FF 0%, #5046E5 100%);
    color: #FFFFFF;
    padding: 12px 28px;
    border-radius: 14px;
    font-size: 28px;
    font-weight: 800;
    letter-spacing: 3px;
    margin-bottom: 12px;
  }

  .mbti-profile-name {
    font-size: 22px;
    font-weight: 700;
    color: #2D3748;
    margin-bottom: 4px;
  }

  .mbti-profile-nickname {
    color: #718096;
    font-size: 14px;
  }

  .mbti-recommendation {
    background: #FAFBFF;
    border-radius: 14px;
    padding: 20px;
    margin-bottom: 20px;

    h5 {
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
      color: #4A5568;
      font-size: 14px;
      font-weight: 600;
      margin-bottom: 12px;

      i {
        color: #6C63FF;
      }
    }
  }

  .time-recommend {
    margin-bottom: 12px;
  }

  .time-value {
    background: linear-gradient(135deg, #6C63FF 0%, #5046E5 100%);
    color: #FFFFFF;
    padding: 10px 20px;
    border-radius: 10px;
    font-weight: 700;
    font-size: 18px;
  }

  .recommend-note {
    color: #718096;
    font-size: 13px;
    line-height: 1.5;
  }

  .retake-btn {
    width: 100%;
    padding: 14px;
    background: #F0F4FF;
    border: 2px solid #6C63FF;
    border-radius: 12px;
    color: #6C63FF;
    font-size: 15px;
    font-weight: 600;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    transition: all 0.2s;

    &:hover {
      background: #E8EDFF;
    }
  }

  /* 도전과제 모달 */
  .achievements-modal {
    max-width: 450px;
    max-height: 80vh;
    display: flex;
    flex-direction: column;
  }

  .achievements-summary {
    display: flex;
    justify-content: center;
    align-items: center;
    gap: 20px;
    padding: 16px;
    background: linear-gradient(135deg, #F0F4FF 0%, #E8EDFF 100%);
    border-radius: 16px;
    margin-bottom: 20px;
  }

  .summary-stat {
    display: flex;
    flex-direction: column;
    align-items: center;

    .count {
      font-size: 24px;
      font-weight: 700;
      color: #6C63FF;
    }

    .label {
      font-size: 12px;
      color: #718096;
    }
  }

  .summary-divider {
    width: 1px;
    height: 32px;
    background: #CBD5E0;
  }

  .achievements-list {
    display: flex;
    flex-direction: column;
    gap: 12px;
    overflow-y: auto;
    max-height: 400px;
    padding-right: 8px;

    &::-webkit-scrollbar {
      width: 6px;
    }

    &::-webkit-scrollbar-track {
      background: #F0F4FF;
      border-radius: 3px;
    }

    &::-webkit-scrollbar-thumb {
      background: #CBD5E0;
      border-radius: 3px;
    }
  }

  .achievement-item {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 14px;
    background: #FAFBFF;
    border-radius: 14px;
    border: 2px solid transparent;
    transition: all 0.2s;

    &.unlocked {
      background: #FFFFFF;
      border-color: #6C63FF;
    }

    &.locked {
      opacity: 0.7;
    }

    &.rare.unlocked {
      border-color: #3182CE;
      background: linear-gradient(135deg, #EBF8FF 0%, #F0F4FF 100%);
    }

    &.epic.unlocked {
      border-color: #9F7AEA;
      background: linear-gradient(135deg, #FAF5FF 0%, #F0F4FF 100%);
    }

    &.legendary.unlocked {
      border-color: #F6AD55;
      background: linear-gradient(135deg, #FFFAF0 0%, #FFF5EB 100%);
    }
  }

  .achievement-icon {
    width: 44px;
    height: 44px;
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: linear-gradient(135deg, #6C63FF 0%, #5046E5 100%);
    color: #FFFFFF;
    font-size: 20px;

    &.locked {
      background: #E2E8F0;
      color: #A0AEC0;
    }
  }

  .achievement-info {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 2px;
  }

  .achievement-header {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .achievement-name {
    font-size: 15px;
    font-weight: 600;
    color: #2D3748;
  }

  .rarity-badge {
    font-size: 10px;
    padding: 2px 6px;
    border-radius: 4px;
    font-weight: 600;

    &.common {
      background: #E2E8F0;
      color: #718096;
    }

    &.uncommon {
      background: #C6F6D5;
      color: #276749;
    }

    &.rare {
      background: #BEE3F8;
      color: #2B6CB0;
    }

    &.epic {
      background: #E9D8FD;
      color: #6B46C1;
    }

    &.legendary {
      background: #FEEBC8;
      color: #C05621;
    }
  }

  .achievement-desc {
    font-size: 12px;
    color: #718096;
  }

  .progress-bar {
    width: 100%;
    height: 4px;
    background: #E2E8F0;
    border-radius: 2px;
    margin-top: 6px;
    overflow: hidden;
  }

  .progress-fill {
    height: 100%;
    background: linear-gradient(90deg, #6C63FF 0%, #5046E5 100%);
    border-radius: 2px;
    transition: width 0.3s;
  }

  .achievement-reward {
    display: flex;
    align-items: center;
    gap: 4px;
    color: #F6AD55;
    font-weight: 600;
    font-size: 14px;

    i {
      font-size: 16px;
    }
  }

  @media (max-width: 768px) {
    .header {
      padding: 16px 20px;
    }

    .logo {
      font-size: 18px;
    }

    .main-content {
      padding: 20px;
    }

    .setup-page {
      gap: 24px;
    }

    .idle-hamster {
      transform: scale(0.85);
    }

    .session-summary {
      flex-direction: column;
      gap: 16px;
    }
  }

  /* Analysis Modal */
  .analysis-modal {
    max-width: 500px;
    max-height: 85vh;
    display: flex;
    flex-direction: column;
  }

  .analysis-modal-body {
    flex: 1;
    overflow-y: auto;
    margin: 0 -28px -28px -28px;
    padding: 0;

    &::-webkit-scrollbar {
      width: 6px;
    }

    &::-webkit-scrollbar-track {
      background: #F0F4FF;
      border-radius: 3px;
    }

    &::-webkit-scrollbar-thumb {
      background: #CBD5E0;
      border-radius: 3px;
    }
  }
`;

export default TimerPage;
