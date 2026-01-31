import React, { useState, useEffect } from 'react';
import { GlobalStyles } from './styles/GlobalStyles';
import LoginPage from './pages/LoginPage';
import TimerPage from './pages/TimerPage';
import SurveyPage from './pages/SurveyPage';

type AppState = 'login' | 'survey' | 'timer';

function App() {
  const [appState, setAppState] = useState<AppState>('login');
  const [userMBTI, setUserMBTI] = useState<string | null>(null);

  // 앱 시작 시 저장된 상태 확인
  useEffect(() => {
    const authToken = localStorage.getItem('authToken');
    const surveyCompleted = localStorage.getItem('mbtiSurveyCompleted') === 'true';
    const savedMBTI = localStorage.getItem('userMBTI');

    if (authToken) {
      if (surveyCompleted && savedMBTI) {
        setUserMBTI(savedMBTI);
        setAppState('timer');
      } else {
        setAppState('survey');
      }
    }
  }, []);

  const handleLoginSuccess = () => {
    localStorage.setItem('isLoggedIn', 'true');

    // 이미 설문을 완료했는지 확인
    const surveyCompleted = localStorage.getItem('mbtiSurveyCompleted') === 'true';
    const savedMBTI = localStorage.getItem('userMBTI');

    if (surveyCompleted && savedMBTI) {
      setUserMBTI(savedMBTI);
      setAppState('timer');
    } else {
      setAppState('survey');
    }
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
