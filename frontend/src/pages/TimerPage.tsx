import React, { useState, useCallback, useEffect } from 'react';
import styled from 'styled-components';
import LevelCat from '../components/character/LevelCat';
import StatusText from '../components/character/StatusText';
import Loader from '../components/common/Loader';
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

// 도전과제 타입 (API 응답과 맞춤)
interface Achievement {
  id: string;
  name: string;
  description: string;
  category: string;
  rarity: string;
  icon: string;
  coin_reward: number;
  unlocked: boolean;
  unlocked_at?: string;
  progress?: number;
}

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
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [sessionStartTime, setSessionStartTime] = useState<Date | null>(null);
  const [showAbortModal, setShowAbortModal] = useState(false);
  const [showStatsModal, setShowStatsModal] = useState(false);
  const [showSettingsModal, setShowSettingsModal] = useState(false);
  const [showAchievementsModal, setShowAchievementsModal] = useState(false);
  const [showMBTIModal, setShowMBTIModal] = useState(false);
  const [showAnalysisModal, setShowAnalysisModal] = useState(false);
  const [showAboutModal, setShowAboutModal] = useState(false);
  const [aboutTimerSeconds, setAboutTimerSeconds] = useState(30 * 60); // 30분 = 1800초
  const userNickname = localStorage.getItem('userNickname');
  const [achievements, setAchievements] = useState<Achievement[]>([]);
  const [achievementsLoading, setAchievementsLoading] = useState(false);
  const [earnedCoins, setEarnedCoins] = useState(0);
  const [userLevel, setUserLevel] = useState(1);
  const [showMobileMenu, setShowMobileMenu] = useState(false);

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

  // 사용자 레벨 가져오기
  useEffect(() => {
    const fetchUserLevel = async () => {
      try {
        const levelInfo = await api.getUserLevel();
        setUserLevel(levelInfo.level);
      } catch (error) {
        console.error('Failed to fetch user level:', error);
        setUserLevel(1); // 기본 레벨
      }
    };
    fetchUserLevel();
  }, []);

  // 도전과제 가져오기
  const fetchAchievements = useCallback(async () => {
    setAchievementsLoading(true);
    try {
      const response = await api.getAchievements();
      setAchievements(response.achievements);
    } catch (error) {
      console.error('Failed to fetch achievements:', error);
    } finally {
      setAchievementsLoading(false);
    }
  }, []);

  // 도전과제 모달 열릴 때 데이터 로드
  useEffect(() => {
    if (showAchievementsModal) {
      fetchAchievements();
    }
  }, [showAchievementsModal, fetchAchievements]);

  // 서비스 소개 모달 30분 타이머
  useEffect(() => {
    if (showAboutModal) {
      // 모달 열릴 때 30분으로 리셋
      setAboutTimerSeconds(30 * 60);

      const interval = setInterval(() => {
        setAboutTimerSeconds(prev => {
          if (prev <= 0) return 0;
          return prev - 1;
        });
      }, 1000);

      return () => clearInterval(interval);
    }
  }, [showAboutModal]);

  // 타이머 포맷팅 함수
  const formatAboutTimer = (totalSeconds: number) => {
    const minutes = Math.floor(totalSeconds / 60);
    const seconds = totalSeconds % 60;
    return `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
  };

  const handlePhaseComplete = useCallback((phase: TimerPhase) => {
    if (phase.type === 'focus') {
      console.log('Focus phase complete!');
    }
  }, []);

  const handleSessionComplete = useCallback(async () => {
    if (sessionConfig) {
      const totalFocusMinutes = sessionConfig.focusMinutes * sessionConfig.rounds;
      const totalFocusSec = totalFocusMinutes * 60;
      const totalBreakSec = sessionConfig.breakMinutes * (sessionConfig.rounds - 1) * 60;

      // 백엔드 API 호출
      if (currentSessionId) {
        try {
          const response = await api.completeSession({
            session_id: currentSessionId,
            total_focus_sec: totalFocusSec,
            total_break_sec: totalBreakSec,
            rounds_completed: sessionConfig.rounds,
          });
          setEarnedCoins(response.coin_reward);

          // 도전과제 확인
          api.checkAchievements().catch(console.error);
        } catch (error) {
          console.error('Failed to complete session:', error);
          // API 실패시 로컬 계산값 사용
          setEarnedCoins(totalFocusMinutes * 10);
        }
      } else {
        setEarnedCoins(totalFocusMinutes * 10);
      }

      // 로컬 통계 업데이트
      const today = new Date().getDay();
      const dayIndex = today === 0 ? 6 : today - 1;
      const newWeeklyMinutes = [...stats.weeklyMinutes];
      newWeeklyMinutes[dayIndex] += totalFocusMinutes;

      updateStats({
        totalCoins: stats.totalCoins + (totalFocusMinutes * 10),
        completedSessions: stats.completedSessions + 1,
        weeklyMinutes: newWeeklyMinutes,
      });
    }
    setPageState('completed');
    setCurrentSessionId(null);
  }, [sessionConfig, currentSessionId, stats, updateStats]);

  const timer = useTimer({
    onPhaseComplete: handlePhaseComplete,
    onSessionComplete: handleSessionComplete,
  });

  const handleStartSession = async (config: SessionConfig) => {
    setSessionConfig(config);
    setSessionStartTime(new Date());

    // mode_plan 생성
    const modePlan: Array<{ type: 'focus' | 'break'; minutes: number }> = [];
    for (let i = 0; i < config.rounds; i++) {
      modePlan.push({ type: 'focus', minutes: config.focusMinutes });
      if (i < config.rounds - 1) {
        modePlan.push({ type: 'break', minutes: config.breakMinutes });
      }
    }

    // 백엔드 API 호출
    try {
      const response = await api.startSession({
        task_type: (config.taskType || 'reading') as 'reading' | 'practice' | 'creation' | 'routine',
        difficulty: config.difficulty || 3,
        goal: config.goal,
        mode_plan: modePlan,
      });
      setCurrentSessionId(response.id);
    } catch (error) {
      console.error('Failed to start session:', error);
      // API 실패해도 타이머는 시작
    }

    const phases: TimerPhase[] = modePlan.map(p => ({
      type: p.type,
      minutes: p.minutes,
    }));

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

  const handleAbortConfirm = async (reason: AbortReason, detail?: string) => {
    timer.stop();

    // 경과 시간 계산
    const elapsedSec = sessionStartTime
      ? Math.floor((new Date().getTime() - sessionStartTime.getTime()) / 1000)
      : 0;

    // 백엔드 API 호출
    if (currentSessionId) {
      try {
        await api.abortSession({
          session_id: currentSessionId,
          abort_reason: reason as 'phone' | 'tired' | 'bored' | 'anxious' | 'environment' | 'urgent' | 'other',
          abort_detail: detail,
          total_focus_sec: elapsedSec,
          rounds_completed: Math.max(0, timer.currentRound - 1),
        });
      } catch (error) {
        console.error('Failed to abort session:', error);
      }
    }

    setShowAbortModal(false);
    setPageState('setup');
    setCurrentSessionId(null);
    setSessionStartTime(null);
  };

  const handleNewSession = () => {
    setPageState('setup');
    setSessionConfig(null);
    setEarnedCoins(0);
  };

  // 레벨에 따른 칭호
  const getLevelTitle = (level: number): string => {
    if (level >= 50) return '전설의 집중왕';
    if (level >= 40) return '마스터';
    if (level >= 30) return '전문가';
    if (level >= 20) return '숙련자';
    if (level >= 15) return '중급자';
    if (level >= 10) return '도전자';
    if (level >= 5) return '초보자';
    if (level >= 2) return '새싹';
    return '입문자';
  };

  // 달성 시간에 따른 축하 메시지
  const getCompletionMessage = (): { text: string; icon: string } => {
    if (!sessionConfig) return { text: '훌륭해요! 오늘도 집중력을 발휘했어요.', icon: 'bi-hand-thumbs-up-fill' };

    const totalMinutes = sessionConfig.focusMinutes * sessionConfig.rounds;

    if (totalMinutes >= 120) {
      return { text: '대단해요! 2시간 이상 집중하다니, 당신은 집중력 마스터!', icon: 'bi-trophy-fill' };
    } else if (totalMinutes >= 90) {
      return { text: '와우! 90분 넘게 집중했어요. 프로 집중러 인정!', icon: 'bi-lightning-charge-fill' };
    } else if (totalMinutes >= 60) {
      return { text: '1시간 집중 완료! 오늘 정말 열심히 했어요!', icon: 'bi-star-fill' };
    } else if (totalMinutes >= 45) {
      return { text: '45분 집중 성공! 꾸준히 하면 습관이 돼요!', icon: 'bi-stars' };
    } else if (totalMinutes >= 30) {
      return { text: '30분 완주! 작은 성공이 큰 변화를 만들어요!', icon: 'bi-bullseye' };
    } else if (totalMinutes >= 15) {
      return { text: '15분 집중 성공! 시작이 반이에요!', icon: 'bi-rocket-takeoff-fill' };
    } else {
      return { text: '짧지만 해냈어요! 내일은 조금 더 도전해볼까요?', icon: 'bi-brightness-high-fill' };
    }
  };

  return (
    <StyledWrapper>
      <div className="timer-page">
        <header className="header">
          <div className="header-left">
            <h1 className="logo">
              <i className="bi bi-clock-fill"></i>
              Focus Timer
            </h1>
            {userNickname && (
              <span className="user-greeting">
                <i className="bi bi-person-fill"></i>
                {userNickname}님
              </span>
            )}
          </div>
          <div className="header-actions">
            {userMBTI && MBTI_PROFILES[userMBTI] && (
              <button className="mbti-badge-btn" onClick={() => setShowMBTIModal(true)}>
                <span className="mbti-type">{userMBTI}</span>
              </button>
            )}
            {/* 데스크탑 메뉴 */}
            <div className="desktop-menu">
              <button className="header-btn analysis-btn" onClick={() => setShowAnalysisModal(true)} title="AI 분석">
                <i className="bi bi-graph-up-arrow"></i>
              </button>
              <button className="header-btn" onClick={() => setShowAchievementsModal(true)} title="도전과제">
                <i className="bi bi-trophy-fill"></i>
              </button>
              <button className="header-btn" onClick={() => setShowStatsModal(true)} title="통계">
                <i className="bi bi-bar-chart-fill"></i>
              </button>
              <button className="header-btn" onClick={() => setShowAboutModal(true)} title="서비스 소개">
                <i className="bi bi-info-circle-fill"></i>
              </button>
              <button className="header-btn" onClick={() => setShowSettingsModal(true)} title="설정">
                <i className="bi bi-gear-fill"></i>
              </button>
            </div>
            {/* 모바일 메뉴 토글 */}
            <button className="mobile-menu-toggle" onClick={() => setShowMobileMenu(!showMobileMenu)}>
              <i className={`bi ${showMobileMenu ? 'bi-x-lg' : 'bi-list'}`}></i>
            </button>
          </div>
          {/* 모바일 드롭다운 메뉴 */}
          {showMobileMenu && (
            <div className="mobile-menu-dropdown">
              <button onClick={() => { setShowAnalysisModal(true); setShowMobileMenu(false); }}>
                <i className="bi bi-graph-up-arrow"></i> AI 분석
              </button>
              <button onClick={() => { setShowAchievementsModal(true); setShowMobileMenu(false); }}>
                <i className="bi bi-trophy-fill"></i> 도전과제
              </button>
              <button onClick={() => { setShowStatsModal(true); setShowMobileMenu(false); }}>
                <i className="bi bi-bar-chart-fill"></i> 통계
              </button>
              <button onClick={() => { setShowAboutModal(true); setShowMobileMenu(false); }}>
                <i className="bi bi-info-circle-fill"></i> 서비스 소개
              </button>
              <button onClick={() => { setShowSettingsModal(true); setShowMobileMenu(false); }}>
                <i className="bi bi-gear-fill"></i> 설정
              </button>
            </div>
          )}
        </header>

        <main className="main-content">
          {pageState === 'setup' && (
            <div className="setup-page">
              <div className="idle-cat">
                <LevelCat level={userLevel} isRunning={true} size="medium" />
                <div className="level-badge">
                  <i className="bi bi-star-fill"></i>
                  Lv.{userLevel} {getLevelTitle(userLevel)}
                </div>
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
                <LevelCat
                  level={userLevel}
                  isRunning={timer.isRunning && !timer.isPaused}
                  size="large"
                />
                <StatusText
                  isRunning={timer.currentPhase?.type === 'focus'}
                  isPaused={timer.isPaused}
                />
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
                <i className={`bi ${getCompletionMessage().icon}`}></i>
              </div>
              <h2 className="completed-title">세션 완료!</h2>
              <p className="completed-message">
                {getCompletionMessage().text}
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
                <div className="stat-card coin-card">
                  <i className="bi bi-coin"></i>
                  <div className="stat-value">{stats.totalCoins}</div>
                  <div className="stat-label">보유 코인</div>
                  <div className="stat-hint">사용처 : 개발중!!</div>
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
                <div className="setting-item disabled">
                  <div className="setting-info">
                    <i className="bi bi-bell"></i>
                    <span>알림 소리</span>
                    <span className="coming-soon">준비 중</span>
                  </div>
                  <label className="toggle">
                    <input
                      type="checkbox"
                      checked={false}
                      disabled
                    />
                    <span className="slider"></span>
                  </label>
                </div>
                <div className="setting-item disabled">
                  <div className="setting-info">
                    <i className="bi bi-moon-stars"></i>
                    <span>자동 휴식 알림</span>
                    <span className="coming-soon">준비 중</span>
                  </div>
                  <label className="toggle">
                    <input
                      type="checkbox"
                      checked={false}
                      disabled
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
              {achievementsLoading ? (
                <div className="loading-container">
                  <Loader />
                </div>
              ) : (
                <>
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
                      <span className="count">{achievements.filter(a => a.unlocked).reduce((sum, a) => sum + a.coin_reward, 0)}</span>
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
                          <span>{ach.coin_reward}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </>
              )}
            </div>
          </div>
        )}

        {/* AI 분석 모달 */}
        {showAnalysisModal && (
          <div className="modal-overlay" onClick={() => setShowAnalysisModal(false)}>
            <div className="modal-content analysis-modal" onClick={(e) => e.stopPropagation()}>
              <div className="modal-header">
                <h3><i className="bi bi-graph-up-arrow"></i> AI 분석 대시보드</h3>
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

        {/* 서비스 소개 모달 */}
        {showAboutModal && (
          <div className="modal-overlay" onClick={() => setShowAboutModal(false)}>
            <div className="modal-content about-modal" onClick={(e) => e.stopPropagation()}>
              <div className="modal-header">
                <h3><i className="bi bi-info-circle-fill"></i> Focus Timer 소개</h3>
                <button className="close-btn" onClick={() => setShowAboutModal(false)}>
                  <i className="bi bi-x-lg"></i>
                </button>
              </div>
              <div className="about-modal-body">
                {/* 서비스 소개 */}
                <section className="about-section">
                  <div className="about-hero">
                    <div className="hero-timer">
                      <div className="hero-timer-display">{formatAboutTimer(aboutTimerSeconds)}</div>
                      <div className="hero-timer-label">집중 타이머</div>
                    </div>
                    <h2>집중하지 못하는 당신을 위한<br/>AI 타이머</h2>
                    <p>Focus Timer는 AI가 당신의 집중 패턴을<br/>학습하여 개인화된 집중 전략을 제안합니다.</p>
                  </div>
                </section>

                {/* 왜 만들었나요? */}
                <section className="about-section">
                  <h3><i className="bi bi-question-circle-fill"></i> 왜 만들었나요?</h3>
                  <div className="about-card">
                    <p>기존 뽀모도로 타이머는 모든 사람에게 25분을 강요합니다.</p>
                    <ul className="problem-list">
                      <li><i className="bi bi-x-circle"></i> ADHD 경향이 있는 사람은 25분도 길게 느낌</li>
                      <li><i className="bi bi-x-circle"></i> 몰입형 학습자는 25분이 짧아 흐름이 끊김</li>
                      <li><i className="bi bi-x-circle"></i> 시간대별 최적 집중 시간이 다름</li>
                    </ul>
                    <p className="highlight">
                      <i className="bi bi-lightbulb-fill"></i>
                      Focus Timer는 <strong>당신에게 맞는 시간</strong>을 AI가 찾아줍니다!
                    </p>
                  </div>
                </section>

                {/* 어떻게 사용하나요? */}
                <section className="about-section">
                  <h3><i className="bi bi-play-circle-fill"></i> 어떻게 사용하나요?</h3>
                  <div className="how-to-use">
                    <div className="step-card">
                      <div className="step-number">1</div>
                      <div className="step-content">
                        <h4>MBTI 학습 성향 분석</h4>
                        <p>8개 질문으로 당신의 집중 유형을 파악합니다</p>
                      </div>
                    </div>
                    <div className="step-card">
                      <div className="step-number">2</div>
                      <div className="step-content">
                        <h4>AI 추천 받기</h4>
                        <p>과제 유형과 시간대에 맞는 최적 설정을 추천받습니다</p>
                      </div>
                    </div>
                    <div className="step-card">
                      <div className="step-number">3</div>
                      <div className="step-content">
                        <h4>집중 & 성장</h4>
                        <p>세션을 완료하고 코인과 도전과제를 획득하세요</p>
                      </div>
                    </div>
                  </div>
                </section>

                {/* AI 기술 */}
                <section className="about-section">
                  <h3><i className="bi bi-cpu-fill"></i> AI 기술</h3>
                  <div className="tech-cards">
                    <div className="tech-card">
                      <div className="tech-icon">
                        <i className="bi bi-graph-up-arrow"></i>
                      </div>
                      <h4>XGBoost 예측</h4>
                      <p>82.34% 정확도로 완주 확률 예측</p>
                    </div>
                    <div className="tech-card">
                      <div className="tech-icon">
                        <i className="bi bi-shuffle"></i>
                      </div>
                      <h4>Thompson Sampling</h4>
                      <p>192개 전략 중 최적 조합 탐색</p>
                    </div>
                    <div className="tech-card">
                      <div className="tech-icon">
                        <i className="bi bi-clock-fill"></i>
                      </div>
                      <h4>골든타임 분석</h4>
                      <p>시간대별 완주율 패턴 학습</p>
                    </div>
                    <div className="tech-card">
                      <div className="tech-icon">
                        <i className="bi bi-person-badge-fill"></i>
                      </div>
                      <h4>페르소나 분류</h4>
                      <p>9가지 집중 유형 자동 분류</p>
                    </div>
                  </div>
                </section>

                {/* 팀 소개 */}
                <section className="about-section">
                  <h3><i className="bi bi-people-fill"></i> 팀 소개</h3>
                  <div className="team-card">
                    <div className="team-name">코드간장조림</div>
                    <div className="team-event">FAST BUILDERTHON 2026</div>
                    <div className="team-members">
                      <span>신주용</span>
                      <span>강지나</span>
                      <span>송민지</span>
                      <span>김현웅</span>
                    </div>
                  </div>
                </section>
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

  .header-left {
    display: flex;
    align-items: center;
    gap: 16px;
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

  .user-greeting {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 6px 14px;
    background: linear-gradient(135deg, #F0F4FF 0%, #E8EDFF 100%);
    border-radius: 20px;
    color: #4A5568;
    font-size: 14px;
    font-weight: 500;

    i {
      color: #6C63FF;
      font-size: 14px;
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

  .desktop-menu {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .mobile-menu-toggle {
    display: none;
    background: #F0F4FF;
    border: none;
    color: #6C63FF;
    width: 44px;
    height: 44px;
    border-radius: 12px;
    font-size: 20px;
    transition: all 0.2s;

    &:hover {
      background: #6C63FF;
      color: #FFFFFF;
    }
  }

  .mobile-menu-dropdown {
    display: none;
    position: absolute;
    top: 100%;
    right: 20px;
    background: #FFFFFF;
    border-radius: 16px;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15);
    padding: 12px;
    z-index: 100;
    min-width: 180px;

    button {
      display: flex;
      align-items: center;
      gap: 12px;
      width: 100%;
      padding: 12px 16px;
      background: none;
      border: none;
      border-radius: 10px;
      color: #4A5568;
      font-size: 14px;
      font-weight: 500;
      transition: all 0.2s;
      text-align: left;

      i {
        color: #6C63FF;
        font-size: 18px;
        width: 20px;
      }

      &:hover {
        background: #F0F4FF;
        color: #6C63FF;
      }
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

  .idle-cat {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 12px;
  }

  .level-badge {
    display: flex;
    align-items: center;
    gap: 6px;
    background: linear-gradient(135deg, #F6AD55 0%, #ED8936 100%);
    color: #FFFFFF;
    padding: 8px 16px;
    border-radius: 20px;
    font-size: 14px;
    font-weight: 700;
    box-shadow: 0 4px 12px rgba(246, 173, 85, 0.3);

    i {
      font-size: 14px;
    }
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

    .stat-hint {
      font-size: 10px;
      color: #A0AEC0;
      margin-top: 6px;
    }

    &.coin-card {
      background: linear-gradient(135deg, #FFFAF0 0%, #FFF5EB 100%);
      border: 1px solid #F6AD55;

      i {
        color: #F6AD55;
      }
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
    transition: all 0.2s;

    &.disabled {
      opacity: 0.6;
      background: #F7FAFC;
    }
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

  .coming-soon {
    font-size: 10px;
    background: #E2E8F0;
    color: #718096;
    padding: 2px 8px;
    border-radius: 8px;
    font-weight: 600;
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
      position: relative;
    }

    .logo {
      font-size: 18px;

      i {
        font-size: 20px;
      }
    }

    .header-left {
      gap: 8px;
    }

    .user-greeting {
      display: none;
    }

    .desktop-menu {
      display: none;
    }

    .mobile-menu-toggle {
      display: flex;
      align-items: center;
      justify-content: center;
    }

    .mobile-menu-dropdown {
      display: flex;
      flex-direction: column;
      gap: 4px;
    }

    .main-content {
      padding: 20px;
    }

    .setup-page {
      gap: 24px;
    }

    .idle-cat {
      transform: scale(0.85);
    }

    .session-summary {
      flex-direction: column;
      gap: 16px;
    }
  }

  /* Loading Container */
  .loading-container {
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 40px 20px;
    min-height: 120px;
  }

  /* Analysis Modal */
  .analysis-modal {
    max-width: 500px;
    max-height: 85vh;
    display: flex;
    flex-direction: column;
    overflow: hidden;
    padding-bottom: 0;
  }

  .analysis-modal-body {
    flex: 1;
    overflow-y: auto;
    overflow-x: hidden;
    margin: 0 -28px 0 -28px;
    padding: 0 28px 28px 28px;
    border-radius: 0 0 24px 24px;

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

  /* 서비스 소개 모달 */
  .about-modal {
    max-width: 500px;
    max-height: 85vh;
    display: flex;
    flex-direction: column;
    overflow: hidden;
    padding-bottom: 0;
  }

  .about-modal-body {
    flex: 1;
    overflow-y: auto;
    overflow-x: hidden;
    margin: 0 -28px 0 -28px;
    padding: 0 28px 28px 28px;

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

  .about-section {
    margin-bottom: 24px;

    h3 {
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 16px;
      font-weight: 700;
      color: #2D3748;
      margin-bottom: 12px;

      i {
        color: #6C63FF;
      }
    }
  }

  .about-hero {
    text-align: center;
    padding: 24px 16px;
    background: linear-gradient(135deg, #F0F4FF 0%, #E8EDFF 100%);
    border-radius: 16px;

    .hero-timer {
      margin-bottom: 16px;
    }

    .hero-timer-display {
      font-size: 48px;
      font-weight: 800;
      color: #6C63FF;
      font-family: 'SF Mono', 'Monaco', 'Inconsolata', 'Fira Mono', 'Droid Sans Mono', monospace;
      letter-spacing: 2px;
      text-shadow: 0 2px 8px rgba(108, 99, 255, 0.2);
    }

    .hero-timer-label {
      font-size: 12px;
      color: #718096;
      margin-top: 4px;
    }

    h2 {
      font-size: 20px;
      font-weight: 700;
      color: #2D3748;
      line-height: 1.4;
      margin-bottom: 8px;
    }

    p {
      color: #718096;
      font-size: 14px;
      line-height: 1.5;
    }
  }

  .about-card {
    background: #FAFBFF;
    border-radius: 14px;
    padding: 16px;

    p {
      color: #4A5568;
      font-size: 14px;
      margin-bottom: 12px;
    }

    .problem-list {
      list-style: none;
      padding: 0;
      margin: 0 0 16px 0;

      li {
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 8px 0;
        color: #718096;
        font-size: 13px;

        i {
          color: #FC8181;
          font-size: 14px;
        }
      }
    }

    .highlight {
      display: flex;
      align-items: center;
      gap: 8px;
      background: linear-gradient(135deg, #6C63FF10 0%, #5046E510 100%);
      border: 1px solid #6C63FF30;
      border-radius: 10px;
      padding: 12px;
      color: #4A5568;
      font-size: 13px;
      margin: 0;

      i {
        color: #F6AD55;
        font-size: 16px;
      }

      strong {
        color: #6C63FF;
      }
    }
  }

  .how-to-use {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  .step-card {
    display: flex;
    align-items: center;
    gap: 14px;
    background: #FAFBFF;
    border-radius: 12px;
    padding: 14px;

    .step-number {
      width: 32px;
      height: 32px;
      background: linear-gradient(135deg, #6C63FF 0%, #5046E5 100%);
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      color: #FFFFFF;
      font-size: 14px;
      font-weight: 700;
      flex-shrink: 0;
    }

    .step-content {
      h4 {
        font-size: 14px;
        font-weight: 600;
        color: #2D3748;
        margin-bottom: 2px;
      }

      p {
        font-size: 12px;
        color: #718096;
        margin: 0;
      }
    }
  }

  .tech-cards {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 10px;
  }

  .tech-card {
    background: #FAFBFF;
    border-radius: 12px;
    padding: 14px;
    text-align: center;

    .tech-icon {
      width: 36px;
      height: 36px;
      background: linear-gradient(135deg, #6C63FF20 0%, #5046E520 100%);
      border-radius: 10px;
      display: flex;
      align-items: center;
      justify-content: center;
      margin: 0 auto 8px;

      i {
        color: #6C63FF;
        font-size: 18px;
      }
    }

    h4 {
      font-size: 13px;
      font-weight: 600;
      color: #2D3748;
      margin-bottom: 4px;
    }

    p {
      font-size: 11px;
      color: #718096;
      margin: 0;
    }
  }

  .team-card {
    background: linear-gradient(135deg, #F0F4FF 0%, #E8EDFF 100%);
    border-radius: 14px;
    padding: 20px;
    text-align: center;

    .team-name {
      font-size: 18px;
      font-weight: 700;
      color: #6C63FF;
      margin-bottom: 4px;
    }

    .team-event {
      font-size: 12px;
      color: #718096;
      margin-bottom: 16px;
    }

    .team-members {
      display: flex;
      justify-content: center;
      gap: 12px;
      flex-wrap: wrap;

      span {
        background: #FFFFFF;
        padding: 6px 14px;
        border-radius: 20px;
        font-size: 13px;
        color: #4A5568;
        font-weight: 500;
      }
    }
  }

  @media (max-width: 768px) {
    .user-greeting {
      display: none;
    }

    .tech-cards {
      grid-template-columns: 1fr;
    }
  }
`;

export default TimerPage;
