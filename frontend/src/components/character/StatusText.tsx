import React, { useState, useEffect } from 'react';
import styled from 'styled-components';

interface StatusTextProps {
  isRunning?: boolean;
  isPaused?: boolean;
}

const statusMessages = [
  '집중하는 중...',
  '천재가 되는 중...',
  '로또 1등 상상하는 중...',
  '점심 메뉴 고민하는 중...',
  '퇴근 카운트다운 중...',
  '세계 평화 기원하는 중...',
  '오늘 저녁 뭐먹지 고민 중...',
  '주말 계획 세우는 중...',
  '커피 한 잔 생각하는 중...',
  '월급날 기다리는 중...',
  '유튜브 참는 중...',
  '인스타 안보는 중...',
  '핸드폰 멀리하는 중...',
  '딴생각 막는 중...',
  '졸음과 싸우는 중...',
  '집중력 레벨업 중...',
  '뇌 풀가동 중...',
  '생산성 폭발하는 중...',
  '갓생 사는 중...',
  '자기계발 하는 중...',
  '미래의 나를 위해 투자 중...',
  '성공을 향해 달리는 중...',
  '오늘의 할 일 끝내는 중...',
  '내일의 나에게 선물하는 중...',
];

const idleMessages = [
  '쉬는 중...',
  '충전하는 중...',
  '에너지 모으는 중...',
  '다음 집중 준비하는 중...',
  '스트레칭 하는 중...',
  '눈 쉬게 하는 중...',
  '물 마시는 중...',
  '심호흡 하는 중...',
  '창밖 구경하는 중...',
  '햄스터 응원받는 중...',
];

const pausedMessage = '일시정지 중...';

const StatusText: React.FC<StatusTextProps> = ({ isRunning = true, isPaused = false }) => {
  const messages = isRunning ? statusMessages : idleMessages;
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isAnimating, setIsAnimating] = useState(false);

  useEffect(() => {
    // 일시정지 상태면 메시지 순환 중지
    if (isPaused) return;

    const interval = setInterval(() => {
      setIsAnimating(true);
      setTimeout(() => {
        setCurrentIndex((prev) => (prev + 1) % messages.length);
        setIsAnimating(false);
      }, 300);
    }, 2500);

    return () => clearInterval(interval);
  }, [messages.length, isPaused]);

  return (
    <StyledWrapper $isPaused={isPaused}>
      <div className={`status-card ${isPaused ? 'paused' : ''}`}>
        <div className="status-loader">
          <span className="status-prefix">{isPaused ? '' : '열심히'}</span>
          <div className="status-words">
            <span className={`status-word ${isAnimating && !isPaused ? 'slide-out' : 'slide-in'}`}>
              {isPaused ? pausedMessage : messages[currentIndex]}
            </span>
          </div>
          {isPaused && (
            <i className="bi bi-pause-circle-fill pause-icon"></i>
          )}
        </div>
      </div>
    </StyledWrapper>
  );
};

const StyledWrapper = styled.div<{ $isPaused: boolean }>`
  .status-card {
    background: #FFFFFF;
    padding: 12px 24px;
    border-radius: 16px;
    box-shadow: 0 4px 16px rgba(108, 99, 255, 0.1);
    transition: all 0.3s ease;

    &.paused {
      background: #F7FAFC;
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
    }
  }

  .status-loader {
    font-family: "Poppins", "Noto Sans KR", sans-serif;
    font-weight: 500;
    font-size: 18px;
    height: 32px;
    display: flex;
    align-items: center;
  }

  .status-prefix {
    color: #718096;
    margin-right: 6px;
  }

  .status-words {
    overflow: hidden;
    position: relative;
    height: 32px;
  }

  .status-word {
    display: block;
    height: 32px;
    line-height: 32px;
    color: #6C63FF;
    font-weight: 600;
    transition: all 0.3s ease;
  }

  .pause-icon {
    margin-left: 8px;
    color: #A0AEC0;
    font-size: 18px;
  }

  .status-card.paused .status-word {
    color: #A0AEC0;
  }

  .slide-in {
    transform: translateY(0);
    opacity: 1;
  }

  .slide-out {
    transform: translateY(-100%);
    opacity: 0;
  }

  @media (max-width: 768px) {
    .status-loader {
      font-size: 15px;
    }

    .status-card {
      padding: 10px 18px;
    }

    .status-words, .status-word {
      height: 28px;
      line-height: 28px;
    }
  }
`;

export default StatusText;
