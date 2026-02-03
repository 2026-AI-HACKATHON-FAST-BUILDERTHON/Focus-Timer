/**
 * Focus Timer API Service
 */

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// 인증 토큰 가져오기
const getAuthToken = (): string | null => {
  return localStorage.getItem('authToken');
};

// API 요청 헬퍼
async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const token = getAuthToken();

  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...(token && { Authorization: `Bearer ${token}` }),
    ...options.headers,
  };

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    throw new Error(`API Error: ${response.status}`);
  }

  return response.json();
}

// 추천 API
export interface RecommendationRequest {
  task_type: 'reading' | 'practice' | 'creation' | 'routine';
  difficulty: number;
  hour: number;
  day_of_week: number;
}

export interface LoopPhase {
  type: 'focus' | 'break';
  minutes: number;
}

export interface RecommendationResponse {
  recommended_loop: LoopPhase[];
  predicted_completion_prob: number;
  reason: string;
  risk_level: 'low' | 'medium' | 'high';
  micro_routine: string | null;
  persona_type: string | null;
}

export async function getRecommendation(
  request: RecommendationRequest
): Promise<RecommendationResponse> {
  return apiRequest<RecommendationResponse>('/recommendation', {
    method: 'POST',
    body: JSON.stringify(request),
  });
}

export async function getQuickRecommendation(): Promise<RecommendationResponse> {
  return apiRequest<RecommendationResponse>('/recommendation/quick');
}

// 골든타임 API
export interface GoldenTimeResponse {
  golden_hours: number[];
  golden_hours_text: string[];
  best_day: number | null;
  best_day_text: string | null;
  hourly_rates: Record<number, number>;
}

export async function getGoldenTime(): Promise<GoldenTimeResponse> {
  return apiRequest<GoldenTimeResponse>('/recommendation/golden-time');
}

// 적응형 난이도 API
export interface AdaptiveDifficultyResponse {
  recommended_difficulty: number;
  objective_difficulty_score: number;
  user_completion_rate: number;
  explanation: string;
}

export async function getAdaptiveDifficulty(
  taskType: string,
  focusMinutes: number
): Promise<AdaptiveDifficultyResponse> {
  return apiRequest<AdaptiveDifficultyResponse>(
    `/recommendation/adaptive-difficulty?task_type=${taskType}&focus_minutes=${focusMinutes}`
  );
}

// 페르소나 API
export interface PersonaResponse {
  persona_type: string;
  persona_name: string;
  description: string;
  completion_rate: number;
  avg_focus_minutes: number;
  top_abort_reason: string;
  confidence: number;
  tips?: string[];
}

export async function getUserPersona(userId: string): Promise<PersonaResponse> {
  return apiRequest<PersonaResponse>(`/recommendation/persona/${userId}`);
}

// 세션 피드백 API
export async function submitSessionFeedback(
  sessionId: string,
  focusMinutes: number,
  breakMinutes: number,
  rounds: number,
  completed: boolean
): Promise<{ status: string; message: string }> {
  return apiRequest('/recommendation/feedback', {
    method: 'POST',
    body: JSON.stringify({
      session_id: sessionId,
      focus_minutes: focusMinutes,
      break_minutes: breakMinutes,
      rounds,
      completed,
    }),
  });
}

// ===============================
// Session API (세션 관리)
// ===============================

export interface SessionStartRequest {
  task_type: 'reading' | 'practice' | 'creation' | 'routine';
  difficulty: number;
  goal?: string;
  mode_plan: Array<{ type: 'focus' | 'break'; minutes: number }>;
}

export interface SessionResponse {
  id: string;
  user_id: string;
  task_type: string;
  difficulty: number;
  goal?: string;
  mode_plan?: Array<{ type: string; minutes: number }>;
  status: 'completed' | 'aborted';
  abort_reason?: string;
  total_focus_sec: number;
  total_break_sec: number;
  rounds_completed: number;
  coin_reward: number;
  created_at: string;
}

export async function startSession(request: SessionStartRequest): Promise<SessionResponse> {
  return apiRequest('/sessions/start', {
    method: 'POST',
    body: JSON.stringify(request),
  });
}

export interface SessionCompleteRequest {
  session_id: string;
  total_focus_sec: number;
  total_break_sec: number;
  rounds_completed: number;
}

export async function completeSession(request: SessionCompleteRequest): Promise<SessionResponse> {
  return apiRequest('/sessions/complete', {
    method: 'POST',
    body: JSON.stringify(request),
  });
}

export interface SessionAbortRequest {
  session_id: string;
  abort_reason: 'phone' | 'tired' | 'bored' | 'anxious' | 'environment' | 'urgent' | 'other';
  abort_detail?: string;
  total_focus_sec: number;
  rounds_completed: number;
}

export async function abortSession(request: SessionAbortRequest): Promise<SessionResponse> {
  return apiRequest('/sessions/abort', {
    method: 'POST',
    body: JSON.stringify(request),
  });
}

export async function getSessionStats(): Promise<{
  total_sessions: number;
  completed_sessions: number;
  completion_rate: number;
  total_focus_minutes: number;
  total_coins: number;
  sessions_7d: number;
  completed_7d: number;
}> {
  return apiRequest('/sessions/stats');
}

// 도전과제 API
export interface Achievement {
  id: string;
  name: string;
  description: string;
  category: string;
  rarity: string;
  icon: string;
  coin_reward: number;
  unlocked: boolean;
  unlocked_at?: string;
  progress?: number;
}

export interface AchievementListResponse {
  total: number;
  unlocked: number;
  achievements: Achievement[];
  total_coins_earned: number;
}

export async function getAchievements(): Promise<AchievementListResponse> {
  return apiRequest<AchievementListResponse>('/achievements');
}

export async function checkAchievements(): Promise<{
  new_achievements: Achievement[];
  total_new: number;
  coins_earned: number;
}> {
  return apiRequest('/achievements/check', { method: 'POST' });
}

// MBTI 설문 API
export interface SurveyQuestion {
  id: string;
  question: string;
  dimension: string;
  options: { value: string; text: string; icon: string }[];
}

export async function getSurveyQuestions(): Promise<{
  total_questions: number;
  questions: SurveyQuestion[];
}> {
  return apiRequest('/survey/questions');
}

export interface SurveyResult {
  mbti_type: string;
  profile: {
    type_code: string;
    name: string;
    nickname: string;
    study_style: string;
    optimal_focus_range: [number, number];
    optimal_break_range: [number, number];
    completion_tendency: number;
    tips: string[];
  };
  optimal_settings: {
    focus_minutes: number;
    break_minutes: number;
    rounds: number;
  };
}

export async function submitSurvey(
  answers: Record<string, string>
): Promise<SurveyResult> {
  return apiRequest('/survey/submit', {
    method: 'POST',
    body: JSON.stringify({ answers }),
  });
}

export async function getSurveyResult(): Promise<SurveyResult & { has_result: boolean }> {
  return apiRequest('/survey/result');
}

// 인증 API
export interface LoginResponse {
  access_token: string;
  token_type: string;
  user_id: string;
  email: string;
  nickname?: string;
}

export async function demoLogin(
  email: string,
  password: string
): Promise<LoginResponse> {
  return apiRequest('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  });
}

export async function demoSignup(
  email: string,
  password: string,
  nickname: string
): Promise<LoginResponse> {
  return apiRequest('/auth/signup', {
    method: 'POST',
    body: JSON.stringify({ email, password, nickname }),
  });
}

// 이메일 중복 확인
export interface CheckAvailabilityResponse {
  available: boolean;
  message: string;
}

export async function checkEmailAvailability(email: string): Promise<CheckAvailabilityResponse> {
  return apiRequest<CheckAvailabilityResponse>(`/auth/check-email?email=${encodeURIComponent(email)}`);
}

// 닉네임 중복 확인
export async function checkNicknameAvailability(nickname: string): Promise<CheckAvailabilityResponse> {
  return apiRequest<CheckAvailabilityResponse>(`/auth/check-nickname?nickname=${encodeURIComponent(nickname)}`);
}

// 현재 사용자 정보 조회
export interface UserInfo {
  user_id: string;
  email: string;
  nickname: string | null;
  coin_balance: number;
  mbti_type: string | null;
  current_streak_days: number;
}

export async function getUserInfo(): Promise<UserInfo> {
  return apiRequest<UserInfo>('/auth/me');
}

// ===============================
// Analytics API (AI 분석 대시보드)
// ===============================

// 골든타임 히트맵
export interface HourlyHeatmapData {
  hour: number;
  day: number;
  total_sessions: number;
  completed_sessions: number;
  completion_rate: number;
}

export interface GoldenTimeHeatmapResponse {
  heatmap_data: HourlyHeatmapData[];
  golden_hours: number[];
  worst_hours: number[];
  best_day: number | null;
  best_day_name: string | null;
  total_sessions_analyzed: number;
}

export async function getGoldenTimeHeatmap(): Promise<GoldenTimeHeatmapResponse> {
  return apiRequest<GoldenTimeHeatmapResponse>('/analytics/golden-time-heatmap');
}

// 페르소나 분석
export interface PersonaAnalysisResponse {
  persona_type: string;
  persona_name: string;
  persona_icon: string;
  description: string;
  strengths: string[];
  weaknesses: string[];
  tips: string[];
  completion_rate: number;
  avg_focus_minutes: number;
  top_abort_reason: string | null;
  confidence: number;
}

export async function getPersonaAnalysis(): Promise<PersonaAnalysisResponse> {
  return apiRequest<PersonaAnalysisResponse>('/analytics/persona');
}

// 트렌드 분석
export interface TrendDataPoint {
  date: string;
  day_name: string;
  focus_minutes: number;
  sessions: number;
  completed: number;
  completion_rate: number;
}

export interface TrendAnalysisResponse {
  daily_data: TrendDataPoint[];
  weekly_trend: 'improving' | 'stable' | 'declining';
  completion_rate_change: number;
  focus_time_change: number;
  streak_days: number;
  best_streak: number;
}

export async function getTrendAnalysis(days: number = 14): Promise<TrendAnalysisResponse> {
  return apiRequest<TrendAnalysisResponse>(`/analytics/trends?days=${days}`);
}

// AI 인사이트
export interface AIInsight {
  type: 'success' | 'warning' | 'tip' | 'achievement';
  icon: string;
  title: string;
  message: string;
  priority: number;
}

export interface AIInsightsResponse {
  insights: AIInsight[];
  summary: string;
  generated_at: string;
}

export async function getAIInsights(): Promise<AIInsightsResponse> {
  return apiRequest<AIInsightsResponse>('/analytics/insights');
}

// 레벨 정보
export interface LevelInfo {
  level: number;
  level_name: string;
  level_icon: string;
  current_achievements: number;
  next_level_threshold: number;
  progress_percent: number;
  total_achievements: number;
}

export async function getUserLevel(): Promise<LevelInfo> {
  return apiRequest<LevelInfo>('/analytics/level');
}

// 통합 대시보드 API (5개 API를 1번 호출로 최적화)
export interface DashboardResponse {
  level: LevelInfo;
  heatmap: GoldenTimeHeatmapResponse;
  persona: PersonaAnalysisResponse;
  trends: TrendAnalysisResponse;
  insights: AIInsightsResponse;
}

export async function getDashboard(): Promise<DashboardResponse> {
  return apiRequest<DashboardResponse>('/analytics/dashboard');
}

// 주간 리포트
export interface DailyStat {
  date: string;
  day_name: string;
  focus_minutes: number;
  sessions: number;
  completed: number;
}

export interface WeeklyReportResponse {
  total_focus_minutes: number;
  total_sessions: number;
  completed_sessions: number;
  completion_rate: number;
  most_common_abort_reason: string | null;
  best_focus_hour: number | null;
  experiment_suggestion: string;
  daily_stats: DailyStat[];
}

export async function getWeeklyReport(): Promise<WeeklyReportResponse> {
  return apiRequest<WeeklyReportResponse>('/report/weekly');
}
