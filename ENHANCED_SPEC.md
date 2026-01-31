# 🚀 Focus Timer - 고도화 명세서

## 1. 제품 비전

### 핵심 가치 제안
> "집중하지 못하는 당신을 이해하고, 맞춤형 집중 전략을 제안하는 AI 타이머"

### 차별화 포인트
1. **개인화된 세션 추천**: 단순 25분 고정이 아닌, 사용자 패턴 기반 최적 루프
2. **중단 예방 시스템**: 실패하기 전에 개입하는 프로액티브 AI
3. **성장 가시화**: 주간 리포트로 개선 과정을 눈으로 확인

---

## 2. 기능 명세 (MVP)

### 2.1 인증 시스템
- **로그인 방식**: Supabase Magic Link (이메일)
- **UI**: 플립 카드 애니메이션 (로그인 ↔ 회원가입)
- **보안**: JWT 토큰 기반

### 2.2 타이머 기능

#### 기본 타이머
- 집중 시간 / 휴식 시간 설정
- 시작 / 일시정지 / 중단
- 라운드 표시

#### AI 추천 루프
```json
{
  "recommended_loop": [
    {"type": "focus", "minutes": 12},
    {"type": "break", "minutes": 2},
    {"type": "focus", "minutes": 8}
  ],
  "predicted_completion_prob": 0.72,
  "reason": "최근 20분 이상 세션에서 중단이 많아 12분으로 시작합니다"
}
```

### 2.3 세션 관리

#### 세션 시작 시 입력
- 과제 유형 (학습/실습/창작/일상)
- 난이도 (1~5)
- 목표 (선택)

#### 세션 중단 시 입력
- 중단 사유 선택
  - 📱 스마트폰 유혹
  - 😴 피로/졸림
  - 😐 지루함
  - 😰 불안/스트레스
  - 🔊 환경 방해
  - ⏰ 긴급 상황

### 2.4 캐릭터 시스템

#### 햄스터 캐릭터
- 쳇바퀴 돌리는 애니메이션
- 상태 텍스트 (한국어)
  - "열심히 집중하는 중..."
  - "열심히 멍때리는 중..."
  - "열심히 로또 1등 상상하는 중..."
  - "열심히 점심 메뉴 고민하는 중..."
  - "열심히 퇴근 카운트다운 중..."

### 2.5 리워드 시스템

#### 코인 획득
- 세션 완료 시 코인 지급
- 코인량 = focus_time_minutes * 10

#### 상점 (Phase 2)
- 캐릭터 꾸미기 아이템
- 테마 변경

### 2.6 주간 리포트

#### 표시 데이터
- 총 집중 시간
- 완주율
- 주요 중단 사유
- 가장 집중 잘되는 시간대

#### AI 추천
- "다음 주 실험 1개"
- 예: "오후 11시 이후 중단률↑ → 10분 루프 + 휴식 2분 추천"

---

## 3. 기술 아키텍처

### 3.1 Frontend (React)
```
src/
├── components/
│   ├── auth/
│   │   └── AuthCard.tsx       # 로그인/회원가입 플립 카드
│   ├── timer/
│   │   ├── Timer.tsx          # 메인 타이머
│   │   ├── TimerDisplay.tsx   # 시간 표시
│   │   └── Controls.tsx       # 제어 버튼
│   ├── character/
│   │   ├── Hamster.tsx        # 햄스터 캐릭터
│   │   └── StatusText.tsx     # 상태 텍스트
│   ├── session/
│   │   ├── SessionSetup.tsx   # 세션 시작 설정
│   │   └── AbortModal.tsx     # 중단 사유 선택
│   └── report/
│       └── WeeklyReport.tsx   # 주간 리포트
├── pages/
│   ├── LoginPage.tsx
│   ├── TimerPage.tsx
│   └── ReportPage.tsx
├── hooks/
│   ├── useTimer.ts
│   ├── useSession.ts
│   └── useAuth.ts
├── services/
│   ├── api.ts
│   └── supabase.ts
└── styles/
    └── theme.ts
```

### 3.2 Backend (FastAPI)
```
backend/
├── main.py
├── routers/
│   ├── auth.py
│   ├── sessions.py
│   ├── recommendation.py
│   └── report.py
├── services/
│   ├── recommender_rules.py   # 룰 기반 추천
│   └── report_generator.py
├── models/
│   └── schemas.py
└── utils/
    └── supabase.py
```

### 3.3 Database (Supabase)

#### 테이블
1. **user_profile**: 사용자 설정
2. **sessions**: 세션 기록
3. **economy_ledger**: 코인 거래 내역

---

## 4. UI/UX 가이드

### 4.1 컬러 팔레트
- Primary: #956afa (퍼플)
- Background: #111 (다크)
- Text: #fff (화이트)
- Accent: #2d8cf0 (블루)

### 4.2 폰트
- 기본: 'Poppins', sans-serif
- 숫자: monospace

### 4.3 반응형 브레이크포인트
- Mobile: < 768px
- Tablet: 768px ~ 1024px
- Desktop: > 1024px

---

## 5. API 명세 (MVP)

### 인증
- `POST /auth/login` - 매직 링크 발송
- `GET /auth/me` - 현재 사용자 정보

### 세션
- `POST /sessions/start` - 세션 시작
- `POST /sessions/complete` - 세션 완료
- `POST /sessions/abort` - 세션 중단
- `GET /sessions` - 세션 목록

### 추천
- `POST /recommendation` - AI 추천 루프

### 리포트
- `GET /report/weekly` - 주간 리포트

---

## 6. 개발 우선순위

### Must Have (MVP)
1. ✅ 로그인/회원가입
2. ✅ 기본 타이머
3. ✅ 세션 기록
4. ✅ 햄스터 캐릭터
5. ✅ 룰 기반 추천

### Should Have
1. 주간 리포트
2. 코인 시스템
3. 중단 사유 분석

### Could Have
1. 상점
2. 캐릭터 꾸미기
3. ML 모델 추천

---

## 7. 심사 대응 전략

### AI Necessity 강조 포인트
- "25분 고정 뽀모도로"가 아닌 **개인화된 최적 루프**
- 사용자 데이터 기반 **의사결정 엔진**
- 중단 패턴 분석으로 **예방적 개입**

### Real Impact 측정
- 완주율 변화 추적
- 총 집중 시간 증가
- 중단 빈도 감소

---

## 8. 변경 이력

| 날짜 | 버전 | 변경 내용 |
|------|------|----------|
| 2025-01-31 | v1.0 | 초기 명세서 작성 |
