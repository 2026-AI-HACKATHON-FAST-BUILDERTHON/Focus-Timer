import React from 'react';
import styled from 'styled-components';

interface TimerDisplayProps {
  minutes: number;
  seconds: number;
  isBreak?: boolean;
}

const TimerDisplay: React.FC<TimerDisplayProps> = ({ minutes, seconds, isBreak = false }) => {
  const formatTime = (num: number) => num.toString().padStart(2, '0');

  return (
    <StyledWrapper $isBreak={isBreak}>
      <div className="timer-container">
        <div className="time-display">
          <span className="time-value">{formatTime(minutes)}</span>
          <span className="time-separator">:</span>
          <span className="time-value">{formatTime(seconds)}</span>
        </div>
        <div className="timer-label">
          {isBreak ? '휴식 시간' : '집중 시간'}
        </div>
      </div>
    </StyledWrapper>
  );
};

const StyledWrapper = styled.div<{ $isBreak: boolean }>`
  .timer-container {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 12px;
  }

  .time-display {
    display: inline-flex;
    align-items: center;
    background: #FFFFFF;
    border-radius: 20px;
    padding: 24px 48px;
    box-shadow: 0 8px 32px ${props => props.$isBreak
      ? 'rgba(72, 187, 120, 0.15)'
      : 'rgba(108, 99, 255, 0.15)'};
    border: 2px solid ${props => props.$isBreak ? '#48BB78' : '#6C63FF'};
  }

  .time-value {
    font-family: 'JetBrains Mono', monospace;
    font-size: 64px;
    font-weight: 700;
    color: ${props => props.$isBreak ? '#48BB78' : '#6C63FF'};
    line-height: 1;
  }

  .time-separator {
    font-family: 'JetBrains Mono', monospace;
    font-size: 64px;
    font-weight: 700;
    color: ${props => props.$isBreak ? '#48BB78' : '#6C63FF'};
    margin: 0 8px;
    animation: blink 1s ease-in-out infinite;
  }

  .timer-label {
    font-size: 16px;
    font-weight: 500;
    color: ${props => props.$isBreak ? '#48BB78' : '#6C63FF'};
  }

  @keyframes blink {
    0%, 50% {
      opacity: 1;
    }
    51%, 100% {
      opacity: 0.3;
    }
  }

  @media (max-width: 768px) {
    .time-display {
      padding: 20px 32px;
    }

    .time-value {
      font-size: 48px;
    }

    .time-separator {
      font-size: 48px;
      margin: 0 4px;
    }

    .timer-label {
      font-size: 14px;
    }
  }
`;

export default TimerDisplay;
