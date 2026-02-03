import React, { useState, useEffect } from 'react';
import styled from 'styled-components';
import * as api from '../../services/api';

interface AuthCardProps {
  onLogin: (email: string, password: string) => void;
  onSignup: (name: string, email: string, password: string) => void;
  isLoading?: boolean;
}

interface ValidationState {
  isChecking: boolean;
  isValid: boolean | null;
  message: string;
}

const AuthCard: React.FC<AuthCardProps> = ({ onLogin, onSignup, isLoading }) => {
  const [isFlipped, setIsFlipped] = useState(false);
  const [loginEmail, setLoginEmail] = useState('');
  const [loginPassword, setLoginPassword] = useState('');
  const [signupName, setSignupName] = useState('');
  const [signupEmail, setSignupEmail] = useState('');
  const [signupPassword, setSignupPassword] = useState('');

  // 유효성 검사 상태
  const [emailValidation, setEmailValidation] = useState<ValidationState>({
    isChecking: false,
    isValid: null,
    message: '',
  });
  const [nicknameValidation, setNicknameValidation] = useState<ValidationState>({
    isChecking: false,
    isValid: null,
    message: '',
  });

  // 이메일 형식 검사
  const isValidEmailFormat = (email: string): boolean => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  };

  // 디바운스된 이메일 중복 검사
  useEffect(() => {
    if (!signupEmail) {
      setEmailValidation({ isChecking: false, isValid: null, message: '' });
      return;
    }

    if (!isValidEmailFormat(signupEmail)) {
      setEmailValidation({
        isChecking: false,
        isValid: false,
        message: '올바른 이메일 형식이 아닙니다',
      });
      return;
    }

    setEmailValidation((prev) => ({ ...prev, isChecking: true }));

    const timer = setTimeout(async () => {
      try {
        const result = await api.checkEmailAvailability(signupEmail);
        setEmailValidation({
          isChecking: false,
          isValid: result.available,
          message: result.message,
        });
      } catch {
        setEmailValidation({
          isChecking: false,
          isValid: null,
          message: '확인 중 오류가 발생했습니다',
        });
      }
    }, 500);

    return () => clearTimeout(timer);
  }, [signupEmail]);

  // 디바운스된 닉네임 중복 검사
  useEffect(() => {
    if (!signupName) {
      setNicknameValidation({ isChecking: false, isValid: null, message: '' });
      return;
    }

    if (signupName.length < 2) {
      setNicknameValidation({
        isChecking: false,
        isValid: false,
        message: '닉네임은 2자 이상이어야 합니다',
      });
      return;
    }

    setNicknameValidation((prev) => ({ ...prev, isChecking: true }));

    const timer = setTimeout(async () => {
      try {
        const result = await api.checkNicknameAvailability(signupName);
        setNicknameValidation({
          isChecking: false,
          isValid: result.available,
          message: result.message,
        });
      } catch {
        setNicknameValidation({
          isChecking: false,
          isValid: null,
          message: '확인 중 오류가 발생했습니다',
        });
      }
    }, 500);

    return () => clearTimeout(timer);
  }, [signupName]);

  const handleLoginSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onLogin(loginEmail, loginPassword);
  };

  const handleSignupSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    // 유효성 검사 통과 확인
    if (emailValidation.isValid === false || nicknameValidation.isValid === false) {
      return;
    }

    onSignup(signupName, signupEmail, signupPassword);
  };

  const isSignupDisabled =
    isLoading ||
    emailValidation.isChecking ||
    nicknameValidation.isChecking ||
    emailValidation.isValid === false ||
    nicknameValidation.isValid === false;

  return (
    <StyledWrapper>
      <div className={`flip-card ${isFlipped ? 'flipped' : ''}`}>
        <div className="flip-card-inner">
          {/* 로그인 (앞면) */}
          <div className="flip-card-front">
            <div className="card-header">
              <h2>로그인</h2>
              <p>다시 만나서 반가워요!</p>
            </div>
            <form onSubmit={handleLoginSubmit}>
              <div className="input-group">
                <i className="bi bi-envelope"></i>
                <input
                  type="email"
                  placeholder="이메일"
                  value={loginEmail}
                  onChange={(e) => setLoginEmail(e.target.value)}
                  required
                />
              </div>
              <div className="input-group">
                <i className="bi bi-lock"></i>
                <input
                  type="password"
                  placeholder="비밀번호"
                  value={loginPassword}
                  onChange={(e) => setLoginPassword(e.target.value)}
                  required
                />
              </div>
              <button type="submit" className="submit-btn" disabled={isLoading}>
                {isLoading ? '로그인 중...' : '시작하기'}
              </button>
            </form>
            <div className="switch-text">
              계정이 없으신가요?{' '}
              <button
                type="button"
                className="switch-btn"
                onClick={() => setIsFlipped(true)}
              >
                회원가입
              </button>
            </div>
          </div>

          {/* 회원가입 (뒷면) */}
          <div className="flip-card-back">
            <div className="card-header">
              <h2>회원가입</h2>
              <p>함께 집중력을 키워봐요!</p>
            </div>
            <form onSubmit={handleSignupSubmit}>
              <div className="input-group">
                <i className="bi bi-person"></i>
                <input
                  type="text"
                  placeholder="닉네임"
                  value={signupName}
                  onChange={(e) => setSignupName(e.target.value)}
                  className={
                    nicknameValidation.isValid === true
                      ? 'valid'
                      : nicknameValidation.isValid === false
                      ? 'invalid'
                      : ''
                  }
                  required
                />
                {nicknameValidation.isChecking && (
                  <span className="validation-icon checking">
                    <i className="bi bi-arrow-repeat"></i>
                  </span>
                )}
                {!nicknameValidation.isChecking && nicknameValidation.isValid === true && (
                  <span className="validation-icon valid">
                    <i className="bi bi-check-circle-fill"></i>
                  </span>
                )}
                {!nicknameValidation.isChecking && nicknameValidation.isValid === false && (
                  <span className="validation-icon invalid">
                    <i className="bi bi-x-circle-fill"></i>
                  </span>
                )}
              </div>
              {nicknameValidation.message && nicknameValidation.isValid === false && (
                <div className="validation-message invalid">{nicknameValidation.message}</div>
              )}

              <div className="input-group">
                <i className="bi bi-envelope"></i>
                <input
                  type="email"
                  placeholder="이메일"
                  value={signupEmail}
                  onChange={(e) => setSignupEmail(e.target.value)}
                  className={
                    emailValidation.isValid === true
                      ? 'valid'
                      : emailValidation.isValid === false
                      ? 'invalid'
                      : ''
                  }
                  required
                />
                {emailValidation.isChecking && (
                  <span className="validation-icon checking">
                    <i className="bi bi-arrow-repeat"></i>
                  </span>
                )}
                {!emailValidation.isChecking && emailValidation.isValid === true && (
                  <span className="validation-icon valid">
                    <i className="bi bi-check-circle-fill"></i>
                  </span>
                )}
                {!emailValidation.isChecking && emailValidation.isValid === false && (
                  <span className="validation-icon invalid">
                    <i className="bi bi-x-circle-fill"></i>
                  </span>
                )}
              </div>
              {emailValidation.message && emailValidation.isValid === false && (
                <div className="validation-message invalid">{emailValidation.message}</div>
              )}

              <div className="input-group">
                <i className="bi bi-lock"></i>
                <input
                  type="password"
                  placeholder="비밀번호"
                  value={signupPassword}
                  onChange={(e) => setSignupPassword(e.target.value)}
                  required
                />
              </div>
              <button type="submit" className="submit-btn" disabled={isSignupDisabled}>
                {isLoading ? '가입 중...' : '가입하기'}
              </button>
            </form>
            <div className="switch-text">
              이미 계정이 있으신가요?{' '}
              <button
                type="button"
                className="switch-btn"
                onClick={() => setIsFlipped(false)}
              >
                로그인
              </button>
            </div>
          </div>
        </div>
      </div>
    </StyledWrapper>
  );
};

const StyledWrapper = styled.div`
  perspective: 1000px;
  width: 100%;
  max-width: 380px;

  .flip-card {
    width: 100%;
    height: 480px;
    position: relative;
  }

  .flip-card-inner {
    position: relative;
    width: 100%;
    height: 100%;
    transition: transform 0.6s cubic-bezier(0.4, 0, 0.2, 1);
    transform-style: preserve-3d;
  }

  .flip-card.flipped .flip-card-inner {
    transform: rotateY(180deg);
  }

  .flip-card-front,
  .flip-card-back {
    position: absolute;
    width: 100%;
    height: 100%;
    backface-visibility: hidden;
    -webkit-backface-visibility: hidden;
    background: #FFFFFF;
    border-radius: 20px;
    padding: 32px;
    box-shadow: 0 8px 32px rgba(108, 99, 255, 0.12);
    display: flex;
    flex-direction: column;
  }

  .flip-card-back {
    transform: rotateY(180deg);
  }

  .card-header {
    text-align: center;
    margin-bottom: 24px;

    h2 {
      font-size: 24px;
      font-weight: 700;
      color: #2D3748;
      margin-bottom: 8px;
    }

    p {
      color: #718096;
      font-size: 14px;
    }
  }

  form {
    flex: 1;
    display: flex;
    flex-direction: column;
  }

  .input-group {
    position: relative;
    margin-bottom: 12px;

    i:first-child {
      position: absolute;
      left: 16px;
      top: 50%;
      transform: translateY(-50%);
      color: #A0AEC0;
      font-size: 18px;
      transition: color 0.2s;
    }

    input {
      width: 100%;
      padding: 14px 44px 14px 48px;
      font-size: 15px;
      border: 2px solid #E2E8F0;
      border-radius: 12px;
      background: #FAFBFF;
      color: #2D3748;
      transition: all 0.2s;

      &::placeholder {
        color: #A0AEC0;
      }

      &:focus {
        border-color: #6C63FF;
        background: #FFFFFF;
        box-shadow: 0 0 0 4px rgba(108, 99, 255, 0.1);
      }

      &.valid {
        border-color: #48BB78;
        background: #F0FFF4;
      }

      &.invalid {
        border-color: #FC8181;
        background: #FFF5F5;
      }
    }

    &:focus-within i:first-child {
      color: #6C63FF;
    }

    .validation-icon {
      position: absolute;
      right: 16px;
      top: 50%;
      transform: translateY(-50%);
      font-size: 18px;

      &.checking {
        color: #A0AEC0;
        animation: spin 1s linear infinite;
      }

      &.valid {
        color: #48BB78;
      }

      &.invalid {
        color: #FC8181;
      }
    }
  }

  @keyframes spin {
    from {
      transform: translateY(-50%) rotate(0deg);
    }
    to {
      transform: translateY(-50%) rotate(360deg);
    }
  }

  .validation-message {
    font-size: 12px;
    margin-top: -8px;
    margin-bottom: 12px;
    padding-left: 16px;

    &.invalid {
      color: #E53E3E;
    }

    &.valid {
      color: #38A169;
    }
  }

  .submit-btn {
    width: 100%;
    padding: 16px;
    font-size: 16px;
    font-weight: 600;
    color: #FFFFFF;
    background: linear-gradient(135deg, #6C63FF 0%, #5046E5 100%);
    border: none;
    border-radius: 12px;
    margin-top: auto;
    transition: all 0.2s;
    box-shadow: 0 4px 16px rgba(108, 99, 255, 0.3);

    &:hover:not(:disabled) {
      transform: translateY(-2px);
      box-shadow: 0 6px 24px rgba(108, 99, 255, 0.4);
    }

    &:active:not(:disabled) {
      transform: translateY(0);
    }

    &:disabled {
      opacity: 0.7;
      cursor: not-allowed;
    }
  }

  .switch-text {
    text-align: center;
    margin-top: 24px;
    padding-top: 20px;
    border-top: 1px solid #E2E8F0;
    color: #718096;
    font-size: 14px;
  }

  .switch-btn {
    background: none;
    border: none;
    color: #6C63FF;
    font-weight: 600;
    font-size: 14px;
    padding: 0;
    cursor: pointer;
    transition: color 0.2s;

    &:hover {
      color: #5046E5;
      text-decoration: underline;
    }
  }

  @media (max-width: 768px) {
    max-width: 100%;

    .flip-card {
      height: 460px;
    }

    .flip-card-front,
    .flip-card-back {
      padding: 24px;
    }

    .card-header {
      margin-bottom: 16px;

      h2 {
        font-size: 22px;
      }
    }

    .input-group {
      margin-bottom: 10px;

      input {
        padding: 12px 40px 12px 44px;
      }
    }

    .submit-btn {
      padding: 14px;
    }
  }
`;

export default AuthCard;
