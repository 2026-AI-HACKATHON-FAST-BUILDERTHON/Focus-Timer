import React from 'react';
import styled from 'styled-components';

interface LevelCatProps {
  level: number;
  isRunning?: boolean;
  size?: 'small' | 'medium' | 'large';
}

const LevelCat: React.FC<LevelCatProps> = ({ level, isRunning = true, size = 'medium' }) => {
  // 레벨에 따른 GIF 선택 (1-5 레벨, 범위 밖이면 가장 가까운 레벨로)
  const getLevelGifPath = () => {
    const clampedLevel = Math.max(1, Math.min(5, level));
    return `/images/level_${clampedLevel}.gif`;
  };

  // 일시정지 GIF 경로
  const pausedGifPath = '/images/paused_cat.gif';

  // 레벨별 이름
  const getLevelName = () => {
    const names: Record<number, string> = {
      1: '아기 냥이',
      2: '탐험 냥이',
      3: '집중 냥이',
      4: '프로 냥이',
      5: '마스터 냥이',
    };
    const clampedLevel = Math.max(1, Math.min(5, level));
    return names[clampedLevel];
  };

  return (
    <StyledWrapper $size={size} $isRunning={isRunning}>
      <div className="cat-container">
        {/* 레벨 GIF - 실행 중일 때 표시 */}
        <img
          src={getLevelGifPath()}
          alt={getLevelName()}
          className={`cat-gif level-gif ${isRunning ? 'active' : ''}`}
        />
        {/* 일시정지 GIF - 멈췄을 때 표시 */}
        <img
          src={pausedGifPath}
          alt="쉬는 냥이"
          className={`cat-gif paused-gif ${!isRunning ? 'active' : ''}`}
        />
      </div>
    </StyledWrapper>
  );
};

const StyledWrapper = styled.div<{ $size: string; $isRunning: boolean }>`
  .cat-container {
    position: relative;
    display: flex;
    align-items: center;
    justify-content: center;
    width: ${props => {
      switch (props.$size) {
        case 'small': return '120px';
        case 'large': return '240px';
        default: return '180px';
      }
    }};
    height: ${props => {
      switch (props.$size) {
        case 'small': return '120px';
        case 'large': return '240px';
        default: return '180px';
      }
    }};
    /* 홈페이지 배경색과 동일하게 설정 */
    background: linear-gradient(180deg, #FAFBFF 0%, #F0F4FF 100%);
    border-radius: 20px;
    overflow: hidden;
  }

  .cat-gif {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    object-fit: contain;
    /*
     * GIF 배경을 페이지 배경과 블렌딩
     * multiply: 흰색 배경 GIF에 적합 (흰색이 투명해짐)
     */
    mix-blend-mode: multiply;
    filter: brightness(1.05);

    /* 부드러운 전환 효과 */
    opacity: 0;
    transform: scale(0.95);
    transition: opacity 0.5s ease-in-out, transform 0.5s ease-in-out;

    &.active {
      opacity: 1;
      transform: scale(1);
    }
  }

  .level-gif {
    z-index: 1;
  }

  .paused-gif {
    z-index: 2;
  }
`;

export default LevelCat;
