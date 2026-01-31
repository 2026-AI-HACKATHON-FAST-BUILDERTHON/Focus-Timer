// 밝고 편안한 테마 - 시각적 편안함
export const theme = {
  colors: {
    primary: '#6C63FF',       // 부드러운 보라
    primaryLight: '#8B85FF',
    primaryDark: '#5046E5',
    secondary: '#FF6B9D',     // 따뜻한 핑크

    background: '#FAFBFF',    // 아주 연한 블루 화이트
    backgroundAlt: '#F0F4FF', // 연한 라벤더
    card: '#FFFFFF',

    text: '#2D3748',          // 진한 그레이 (순수 검정 아님)
    textLight: '#718096',     // 중간 그레이
    textMuted: '#A0AEC0',     // 연한 그레이

    success: '#48BB78',       // 부드러운 그린
    warning: '#F6AD55',       // 따뜻한 오렌지
    error: '#FC8181',         // 부드러운 레드

    border: '#E2E8F0',        // 연한 보더
    shadow: 'rgba(108, 99, 255, 0.1)',
  },
  fonts: {
    main: "'Poppins', 'Noto Sans KR', sans-serif",
    mono: "'JetBrains Mono', monospace",
  },
  borderRadius: {
    small: '8px',
    medium: '12px',
    large: '20px',
    round: '50%',
  },
  shadows: {
    small: '0 2px 8px rgba(108, 99, 255, 0.08)',
    medium: '0 4px 16px rgba(108, 99, 255, 0.12)',
    large: '0 8px 32px rgba(108, 99, 255, 0.16)',
  },
  breakpoints: {
    mobile: '768px',
    tablet: '1024px',
  },
};

export type ThemeType = typeof theme;
