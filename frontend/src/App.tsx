import React, { useState, useEffect } from 'react';
import { GlobalStyles } from './styles/GlobalStyles';
import LoginPage from './pages/LoginPage';
import TimerPage from './pages/TimerPage';
import SurveyPage from './pages/SurveyPage';
import { Agentation } from 'agentation';

type AppState = 'login' | 'survey' | 'timer';

function App() {
  const [appState, setAppState] = useState<AppState>('login');
  const [userMBTI, setUserMBTI] = useState<string | null>(null);

  // 앱 시작 시 저장된 상태 확인
  useEffect(() => {
    const isLoggedIn = localStorage.getItem('isLoggedIn') === 'true';
    const surveyCompleted = localStorage.getItem('mbtiSurveyCompleted') === 'true';
    const savedMBTI = localStorage.getItem('userMBTI');

    if (isLoggedIn) {
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

  
  const handleAnnotationCopy = (markdown: string) => {
    console.log('UI 피드백 복사됨:', markdown);
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
      {/* 개발 모드에서 UI 피드백 수집 도구 */}
      {process.env.NODE_ENV === 'development' && (
        <Agentation onCopy={handleAnnotationCopy} />
      )}
    </>
  );
}

export default App;
