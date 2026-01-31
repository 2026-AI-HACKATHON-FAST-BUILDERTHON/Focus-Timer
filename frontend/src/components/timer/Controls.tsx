import React from 'react';
import styled from 'styled-components';

interface ControlsProps {
  isRunning: boolean;
  onStart: () => void;
  onPause: () => void;
  onStop: () => void;
  onSkip?: () => void;
  disabled?: boolean;
}

const Controls: React.FC<ControlsProps> = ({
  isRunning,
  onStart,
  onPause,
  onStop,
  onSkip,
  disabled = false,
}) => {
  return (
    <StyledWrapper>
      <div className="controls">
        {!isRunning ? (
          <button
            className="control-btn primary"
            onClick={onStart}
            disabled={disabled}
          >
            <i className="bi bi-play-fill"></i>
            시작
          </button>
        ) : (
          <button
            className="control-btn warning"
            onClick={onPause}
            disabled={disabled}
          >
            <i className="bi bi-pause-fill"></i>
            일시정지
          </button>
        )}

        <button
          className="control-btn danger"
          onClick={onStop}
          disabled={disabled || !isRunning}
        >
          <i className="bi bi-stop-fill"></i>
          중단
        </button>

        {onSkip && (
          <button
            className="control-btn secondary"
            onClick={onSkip}
            disabled={disabled}
          >
            <i className="bi bi-skip-forward-fill"></i>
            건너뛰기
          </button>
        )}
      </div>
    </StyledWrapper>
  );
};

const StyledWrapper = styled.div`
  .controls {
    display: flex;
    gap: 12px;
    flex-wrap: wrap;
    justify-content: center;
  }

  .control-btn {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 14px 28px;
    font-size: 15px;
    font-weight: 600;
    border-radius: 12px;
    border: none;
    color: #FFFFFF;
    transition: all 0.2s;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);

    i {
      font-size: 18px;
    }

    &:hover:not(:disabled) {
      transform: translateY(-2px);
      box-shadow: 0 6px 16px rgba(0, 0, 0, 0.15);
    }

    &:active:not(:disabled) {
      transform: translateY(0);
    }

    &:disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }
  }

  .primary {
    background: linear-gradient(135deg, #6C63FF 0%, #5046E5 100%);

    &:hover:not(:disabled) {
      box-shadow: 0 6px 20px rgba(108, 99, 255, 0.4);
    }
  }

  .warning {
    background: linear-gradient(135deg, #F6AD55 0%, #ED8936 100%);

    &:hover:not(:disabled) {
      box-shadow: 0 6px 20px rgba(237, 137, 54, 0.4);
    }
  }

  .danger {
    background: linear-gradient(135deg, #FC8181 0%, #F56565 100%);

    &:hover:not(:disabled) {
      box-shadow: 0 6px 20px rgba(245, 101, 101, 0.4);
    }
  }

  .secondary {
    background: #E2E8F0;
    color: #4A5568;

    &:hover:not(:disabled) {
      background: #CBD5E0;
    }
  }

  @media (max-width: 768px) {
    .control-btn {
      padding: 12px 20px;
      font-size: 14px;

      i {
        font-size: 16px;
      }
    }
  }
`;

export default Controls;
