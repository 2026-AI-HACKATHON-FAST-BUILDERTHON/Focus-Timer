import React, { useState } from 'react';
import styled from 'styled-components';

export type AbortReason =
  | 'phone'
  | 'tired'
  | 'bored'
  | 'anxious'
  | 'environment'
  | 'urgent'
  | 'other';

interface AbortModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: (reason: AbortReason, detail?: string) => void;
}

const abortReasons: { key: AbortReason; icon: string; label: string }[] = [
  { key: 'phone', icon: 'bi-phone', label: '스마트폰 유혹' },
  { key: 'tired', icon: 'bi-moon-stars', label: '피로/졸림' },
  { key: 'bored', icon: 'bi-emoji-neutral', label: '지루함' },
  { key: 'anxious', icon: 'bi-emoji-frown', label: '불안/스트레스' },
  { key: 'environment', icon: 'bi-volume-up', label: '환경 방해' },
  { key: 'urgent', icon: 'bi-alarm', label: '긴급 상황' },
  { key: 'other', icon: 'bi-question-circle', label: '기타' },
];

const AbortModal: React.FC<AbortModalProps> = ({ isOpen, onClose, onConfirm }) => {
  const [selectedReason, setSelectedReason] = useState<AbortReason | null>(null);
  const [otherDetail, setOtherDetail] = useState('');

  if (!isOpen) return null;

  const handleConfirm = () => {
    if (selectedReason) {
      onConfirm(selectedReason, selectedReason === 'other' ? otherDetail : undefined);
      setSelectedReason(null);
      setOtherDetail('');
    }
  };

  return (
    <StyledWrapper>
      <div className="modal-overlay" onClick={onClose}>
        <div className="modal-content" onClick={(e) => e.stopPropagation()}>
          <h3 className="modal-title">세션을 중단하시겠어요?</h3>
          <p className="modal-subtitle">중단 사유를 알려주시면 더 나은 추천을 해드릴게요</p>

          <div className="reasons-grid">
            {abortReasons.map((reason) => (
              <button
                key={reason.key}
                className={`reason-btn ${selectedReason === reason.key ? 'active' : ''}`}
                onClick={() => setSelectedReason(reason.key)}
              >
                <i className={`bi ${reason.icon} reason-icon`}></i>
                <span className="reason-label">{reason.label}</span>
              </button>
            ))}
          </div>

          {selectedReason === 'other' && (
            <input
              type="text"
              className="other-input"
              placeholder="중단 사유를 적어주세요"
              value={otherDetail}
              onChange={(e) => setOtherDetail(e.target.value)}
            />
          )}

          <div className="modal-actions">
            <button className="action-btn cancel" onClick={onClose}>
              계속하기
            </button>
            <button
              className="action-btn confirm"
              onClick={handleConfirm}
              disabled={!selectedReason}
            >
              중단하기
            </button>
          </div>
        </div>
      </div>
    </StyledWrapper>
  );
};

const StyledWrapper = styled.div`
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
    padding: 32px;
    max-width: 420px;
    width: 100%;
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
  }

  .modal-title {
    color: #2D3748;
    font-size: 20px;
    font-weight: 700;
    text-align: center;
    margin-bottom: 8px;
  }

  .modal-subtitle {
    color: #718096;
    font-size: 14px;
    text-align: center;
    margin-bottom: 24px;
  }

  .reasons-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 10px;
    margin-bottom: 20px;
  }

  .reason-btn {
    background: #FAFBFF;
    border: 2px solid #E2E8F0;
    border-radius: 14px;
    padding: 16px;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 8px;
    transition: all 0.2s;

    &:hover {
      border-color: #FC8181;
    }

    &.active {
      background: #FFF5F5;
      border-color: #FC8181;
    }
  }

  .reason-icon {
    font-size: 24px;
    color: #6C63FF;
  }

  .reason-label {
    color: #4A5568;
    font-size: 13px;
    font-weight: 500;
  }

  .other-input {
    width: 100%;
    background: #FAFBFF;
    border: 2px solid #E2E8F0;
    border-radius: 12px;
    padding: 14px 16px;
    color: #2D3748;
    font-size: 14px;
    margin-bottom: 20px;

    &::placeholder {
      color: #A0AEC0;
    }

    &:focus {
      border-color: #6C63FF;
    }
  }

  .modal-actions {
    display: flex;
    gap: 12px;
  }

  .action-btn {
    flex: 1;
    padding: 16px;
    border-radius: 12px;
    font-size: 15px;
    font-weight: 600;
    transition: all 0.2s;
  }

  .cancel {
    background: #FFFFFF;
    border: 2px solid #48BB78;
    color: #48BB78;

    &:hover {
      background: #F0FFF4;
    }
  }

  .confirm {
    background: linear-gradient(135deg, #FC8181 0%, #F56565 100%);
    border: none;
    color: #FFFFFF;

    &:hover:not(:disabled) {
      transform: translateY(-1px);
      box-shadow: 0 4px 12px rgba(245, 101, 101, 0.3);
    }

    &:disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }
  }

  @media (max-width: 768px) {
    .modal-content {
      padding: 24px;
    }

    .reasons-grid {
      grid-template-columns: 1fr;
    }

    .reason-btn {
      flex-direction: row;
      justify-content: flex-start;
      padding: 14px 16px;
    }
  }
`;

export default AbortModal;
