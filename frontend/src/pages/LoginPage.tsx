import React, { useState } from 'react';
import styled from 'styled-components';
import AuthCard from '../components/auth/AuthCard';
import * as api from '../services/api';

interface LoginPageProps {
  onLoginSuccess: () => void;
}

const LoginPage: React.FC<LoginPageProps> = ({ onLoginSuccess }) => {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleLogin = async (email: string, password: string) => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await api.demoLogin(email, password);

      // 토큰을 localStorage에 저장
      localStorage.setItem('authToken', response.access_token);
      localStorage.setItem('userId', response.user_id);
      localStorage.setItem('userEmail', response.email);
      if (response.nickname) {
        localStorage.setItem('userNickname', response.nickname);
      }

      onLoginSuccess();
    } catch (err: any) {
      console.error('Login error:', err);
      setError('이메일 또는 비밀번호가 올바르지 않습니다.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSignup = async (name: string, email: string, password: string) => {
    setIsLoading(true);
    setError(null);

    try {
      // 회원가입 API도 토큰을 반환함
      const response = await api.demoSignup(email, password, name);

      // 토큰을 localStorage에 저장
      localStorage.setItem('authToken', response.access_token);
      localStorage.setItem('userId', response.user_id);
      localStorage.setItem('userEmail', response.email);
      if (response.nickname) {
        localStorage.setItem('userNickname', response.nickname);
      }

      onLoginSuccess();
    } catch (err: any) {
      console.error('Signup error:', err);
      if (err.message?.includes('400')) {
        setError('이미 가입된 이메일입니다.');
      } else {
        setError('회원가입에 실패했습니다. 다시 시도해주세요.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <StyledWrapper>
      <div className="login-page">
        {/* 헤더 */}
        <header className="header">
          <div className="logo">
            <i className="bi bi-clock-fill"></i>
            <span>Focus Timer</span>
          </div>
        </header>

        {/* 메인 콘텐츠 */}
        <main className="main-content">
          <div className="hero-section">
            <h1 className="hero-title">
              <span className="highlight">집중</span>하지 못하는
              <br />
              당신을 위한 타이머
            </h1>
            <p className="hero-description">
              AI가 당신의 패턴을 분석해<br />
              최적의 집중 전략을 추천해드려요
            </p>
          </div>

          {error && <div className="error-message">{error}</div>}

          <AuthCard
            onLogin={handleLogin}
            onSignup={handleSignup}
            isLoading={isLoading}
          />

          <div className="demo-hint">
            <i className="bi bi-info-circle"></i>
            테스트 계정: test@focustimer.com / test1234
          </div>
        </main>

      </div>
    </StyledWrapper>
  );
};

const StyledWrapper = styled.div`
  .login-page {
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    background: linear-gradient(180deg, #FAFBFF 0%, #F0F4FF 100%);
  }

  /* 헤더 */
  .header {
    padding: 24px 32px;
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

  /* 메인 콘텐츠 */
  .main-content {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 20px;
    gap: 32px;
  }

  .hero-section {
    text-align: center;
  }

  .hero-title {
    font-size: 32px;
    font-weight: 700;
    color: #2D3748;
    line-height: 1.4;
    margin-bottom: 16px;

    .highlight {
      color: #6C63FF;
    }
  }

  .hero-description {
    color: #718096;
    font-size: 16px;
    line-height: 1.7;
  }

  .error-message {
    background: #FFF5F5;
    border: 1px solid #FC8181;
    color: #C53030;
    padding: 12px 24px;
    border-radius: 10px;
    font-size: 14px;
  }

  .demo-hint {
    display: flex;
    align-items: center;
    gap: 8px;
    color: #718096;
    font-size: 13px;
    background: #F0F4FF;
    padding: 10px 16px;
    border-radius: 8px;

    i {
      color: #6C63FF;
    }
  }

  /* 반응형 */
  @media (max-width: 768px) {
    .header {
      padding: 16px 20px;
    }

    .logo {
      font-size: 18px;
    }

    .hero-title {
      font-size: 26px;
    }

    .hero-description {
      font-size: 14px;
    }
  }
`;

export default LoginPage;
