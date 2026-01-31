import React, { useState, useEffect } from 'react';
import { GlobalStyles } from './styles/GlobalStyles';
import LoginPage from './pages/LoginPage';
import TimerPage from './pages/TimerPage';
import SurveyPage from './pages/SurveyPage';
import { getSurveyResult } from './services/api';

type AppState = 'login' | 'survey' | 'timer' | 'loading';

function App() {
  const [appState, setAppState] = useState<AppState>('login');
  const [userMBTI, setUserMBTI] = useState<string | null>(null);

  // DB에서 MBTI 확인하는 함수
  const checkMBTIFromDB = async () => {
    try {
      const result = await getSurveyResult();
      if (result.has_result && result.mbti_type) {
        setUserMBTI(result.mbti_type);
        localStorage.setItem('userMBTI', result.mbti_type);
        localStorage.setItem('mbtiSurveyCompleted', 'true');
        setAppState('timer');
      } else {
        setAppState('survey');
      }
    } catch (error) {
      console.error('MBTI 확인 실패:', error);
      setAppState('survey');
    }
  };

  // 앱 시작 시 저장된 상태 확인
  useEffect(() => {
    const authToken = localStorage.getItem('authToken');

    if (authToken) {
      setAppState('loading');
      checkMBTIFromDB();
    }
  }, []);

  const handleLoginSuccess = async () => {
    localStorage.setItem('isLoggedIn', 'true');
    setAppState('loading');

    // DB에서 MBTI 확인
    await checkMBTIFromDB();
  };

  const handleSurveyComplete = (mbti: string) => {
    setUserMBTI(mbti);
    localStorage.setItem('userMBTI', mbti);
    localStorage.setItem('mbtiSurveyCompleted', 'true');
    setAppState('timer');
  };

  return (
    <>
      <GlobalStyles />
      {appState === 'login' && (
        <LoginPage onLoginSuccess={handleLoginSuccess} />
      )}
      {appState === 'loading' && (
        <div style={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          height: '100vh',
          background: 'linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%)',
          color: '#fff',
          fontSize: '18px'
        }}>
          <div style={{ textAlign: 'center' }}>
            <div style={{ marginBottom: '16px', fontSize: '48px' }}>🐱</div>
            <div>사용자 정보를 확인하는 중...</div>
          </div>
        </div>
      )}
      {appState === 'survey' && (
        <SurveyPage
          onComplete={handleSurveyComplete}
        />
      )}
      {appState === 'timer' && (
        <TimerPage
          userMBTI={userMBTI}
        />
      )}
    </>
  );
}

export default App;
