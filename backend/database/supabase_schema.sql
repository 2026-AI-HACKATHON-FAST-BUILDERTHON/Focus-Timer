-- ============================================================
-- Focus Timer Database Schema for Supabase (PostgreSQL)
-- Supabase SQL Editor에 복사하여 실행하세요
-- ============================================================

-- ============================================================
-- ENUM Types 생성
-- ============================================================
CREATE TYPE task_type AS ENUM ('reading', 'practice', 'creation', 'routine');
CREATE TYPE session_status AS ENUM ('in_progress', 'completed', 'aborted');
CREATE TYPE abort_reason_type AS ENUM ('phone', 'tired', 'bored', 'anxious', 'environment', 'urgent', 'other');
CREATE TYPE achievement_category AS ENUM ('focus', 'streak', 'time', 'milestone', 'special', 'hidden');
CREATE TYPE achievement_rarity AS ENUM ('common', 'uncommon', 'rare', 'epic', 'legendary');
CREATE TYPE transaction_type AS ENUM ('session_reward', 'achievement_reward', 'purchase', 'refund', 'bonus', 'adjustment');
CREATE TYPE shop_item_type AS ENUM ('hat', 'accessory', 'prop', 'theme', 'sound');

-- ============================================================
-- 1. Users Table
-- ============================================================
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    nickname VARCHAR(100),
    mbti_type CHAR(4),
    coin_balance INTEGER DEFAULT 0 CHECK (coin_balance >= 0),
    total_coins_earned INTEGER DEFAULT 0 CHECK (total_coins_earned >= 0),
    current_streak_days INTEGER DEFAULT 0 CHECK (current_streak_days >= 0),
    best_streak_days INTEGER DEFAULT 0 CHECK (best_streak_days >= 0),
    persona_type VARCHAR(30),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    last_session_at TIMESTAMPTZ
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_coin_balance ON users(coin_balance DESC);
CREATE INDEX idx_users_mbti ON users(mbti_type);
CREATE INDEX idx_users_persona ON users(persona_type);

-- ============================================================
-- 2. Sessions Table
-- ============================================================
CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    task_type task_type NOT NULL,
    difficulty SMALLINT NOT NULL CHECK (difficulty BETWEEN 1 AND 5),
    goal VARCHAR(500),
    status session_status NOT NULL DEFAULT 'in_progress',
    abort_reason abort_reason_type,
    abort_detail VARCHAR(500),

    -- Time tracking
    total_focus_sec INTEGER DEFAULT 0 CHECK (total_focus_sec >= 0),
    total_break_sec INTEGER DEFAULT 0 CHECK (total_break_sec >= 0),
    rounds_completed SMALLINT DEFAULT 0 CHECK (rounds_completed >= 0),

    -- Plan details
    planned_focus_min SMALLINT NOT NULL DEFAULT 25,
    planned_break_min SMALLINT NOT NULL DEFAULT 5,
    planned_rounds SMALLINT NOT NULL DEFAULT 4,
    mode_plan JSONB,

    -- Reward
    coin_reward INTEGER DEFAULT 0 CHECK (coin_reward >= 0),

    -- Temporal context
    start_hour SMALLINT NOT NULL CHECK (start_hour BETWEEN 0 AND 23),
    day_of_week SMALLINT NOT NULL CHECK (day_of_week BETWEEN 0 AND 6),

    -- AI context
    used_ai_recommendation BOOLEAN DEFAULT FALSE,
    ai_predicted_completion_prob DECIMAL(4,3),

    -- Audit
    created_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_sessions_user_created ON sessions(user_id, created_at DESC);
CREATE INDEX idx_sessions_user_status ON sessions(user_id, status);
CREATE INDEX idx_sessions_golden_time ON sessions(user_id, start_hour, day_of_week, status);
CREATE INDEX idx_sessions_completed_at ON sessions(completed_at DESC);

-- ============================================================
-- 3. Achievement Definitions Table
-- ============================================================
CREATE TABLE achievement_definitions (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description VARCHAR(500) NOT NULL,
    category achievement_category NOT NULL,
    rarity achievement_rarity NOT NULL,
    icon VARCHAR(50) NOT NULL,
    coin_reward INTEGER NOT NULL CHECK (coin_reward >= 0),
    requirement JSONB NOT NULL,
    is_hidden BOOLEAN DEFAULT FALSE,
    display_order SMALLINT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_achievements_category ON achievement_definitions(category, display_order);
CREATE INDEX idx_achievements_rarity ON achievement_definitions(rarity);

-- ============================================================
-- 4. User Achievements Table
-- ============================================================
CREATE TABLE user_achievements (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    achievement_id VARCHAR(50) NOT NULL REFERENCES achievement_definitions(id) ON DELETE CASCADE,
    current_value INTEGER DEFAULT 0,
    target_value INTEGER NOT NULL,
    is_unlocked BOOLEAN DEFAULT FALSE,
    unlocked_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(user_id, achievement_id)
);

CREATE INDEX idx_user_achievements_unlocked ON user_achievements(user_id, is_unlocked);

-- ============================================================
-- 5. MAB Arms State Table (Thompson Sampling)
-- ============================================================
CREATE TABLE mab_arms (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    arm_key VARCHAR(20) NOT NULL,
    focus_minutes SMALLINT NOT NULL,
    break_minutes SMALLINT NOT NULL,
    rounds SMALLINT NOT NULL,
    alpha DECIMAL(10,2) DEFAULT 1.0,
    beta DECIMAL(10,2) DEFAULT 1.0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(user_id, arm_key)
);

CREATE INDEX idx_mab_user_arm ON mab_arms(user_id, arm_key);

-- ============================================================
-- 6. Golden Time Stats Table
-- ============================================================
CREATE TABLE golden_time_stats (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    hour SMALLINT NOT NULL CHECK (hour BETWEEN 0 AND 23),
    day_of_week SMALLINT NOT NULL CHECK (day_of_week BETWEEN 0 AND 6),
    success_count INTEGER DEFAULT 0,
    total_count INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(user_id, hour, day_of_week)
);

CREATE INDEX idx_golden_time_user ON golden_time_stats(user_id);

-- ============================================================
-- 7. Adaptive Difficulty History Table
-- ============================================================
CREATE TABLE adaptive_difficulty_history (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    difficulty SMALLINT NOT NULL,
    success BOOLEAN NOT NULL,
    session_id UUID REFERENCES sessions(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_difficulty_user_recent ON adaptive_difficulty_history(user_id, created_at DESC);

-- ============================================================
-- 8. User Optimal Difficulty Cache
-- ============================================================
CREATE TABLE user_optimal_difficulty (
    user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    optimal_difficulty DECIMAL(3,1) DEFAULT 3.0,
    recent_success_rate DECIMAL(5,4),
    sample_size INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- 9. MBTI Profiles Reference Table
-- ============================================================
CREATE TABLE mbti_profiles (
    type_code CHAR(4) PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    nickname VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    study_style TEXT,
    optimal_focus_range_min SMALLINT NOT NULL,
    optimal_focus_range_max SMALLINT NOT NULL,
    optimal_break_range_min SMALLINT NOT NULL,
    optimal_break_range_max SMALLINT NOT NULL,
    optimal_rounds_min SMALLINT NOT NULL,
    optimal_rounds_max SMALLINT NOT NULL,
    best_study_hours JSONB,
    completion_tendency DECIMAL(3,2),
    distraction_vulnerability DECIMAL(3,2),
    tips JSONB
);

-- ============================================================
-- 10. User Survey Answers Table
-- ============================================================
CREATE TABLE user_survey_answers (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    question_id VARCHAR(20) NOT NULL,
    dimension CHAR(2) NOT NULL,
    answer CHAR(1) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(user_id, question_id)
);

-- ============================================================
-- 11. Coin Transactions Table
-- ============================================================
CREATE TABLE coin_transactions (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    amount INTEGER NOT NULL,
    balance_after INTEGER NOT NULL CHECK (balance_after >= 0),
    transaction_type transaction_type NOT NULL,
    reference_type VARCHAR(30),
    reference_id VARCHAR(50),
    description VARCHAR(200),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_coin_tx_user_date ON coin_transactions(user_id, created_at DESC);

-- ============================================================
-- 12. User Daily Stats (Aggregated)
-- ============================================================
CREATE TABLE user_daily_stats (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    stat_date DATE NOT NULL,
    total_sessions INTEGER DEFAULT 0,
    completed_sessions INTEGER DEFAULT 0,
    aborted_sessions INTEGER DEFAULT 0,
    total_focus_minutes INTEGER DEFAULT 0,
    total_break_minutes INTEGER DEFAULT 0,
    total_coins_earned INTEGER DEFAULT 0,
    top_abort_reason VARCHAR(20),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(user_id, stat_date)
);

CREATE INDEX idx_daily_stats_user_date ON user_daily_stats(user_id, stat_date DESC);

-- ============================================================
-- 13. User Auth Sessions (Refresh Tokens)
-- ============================================================
CREATE TABLE user_auth_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    refresh_token_hash VARCHAR(255) NOT NULL,
    device_info VARCHAR(500),
    ip_address VARCHAR(45),
    expires_at TIMESTAMPTZ NOT NULL,
    is_revoked BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_auth_sessions_user ON user_auth_sessions(user_id);
CREATE INDEX idx_auth_sessions_expires ON user_auth_sessions(expires_at);

-- ============================================================
-- 14. Shop Items
-- ============================================================
CREATE TABLE shop_items (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    item_type shop_item_type NOT NULL,
    set_name VARCHAR(50),
    tag VARCHAR(30),
    price INTEGER NOT NULL CHECK (price >= 0),
    color VARCHAR(30),
    preview_image_url VARCHAR(500),
    is_available BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_shop_items_type ON shop_items(item_type, is_available);

-- ============================================================
-- 15. User Inventory
-- ============================================================
CREATE TABLE user_inventory (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    item_id VARCHAR(50) NOT NULL REFERENCES shop_items(id) ON DELETE CASCADE,
    quantity INTEGER DEFAULT 1,
    acquired_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(user_id, item_id)
);

-- ============================================================
-- 16. Cat Equipment
-- ============================================================
CREATE TABLE user_cat_equipment (
    user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    hat_item_id VARCHAR(50) REFERENCES shop_items(id) ON DELETE SET NULL,
    accessory_item_id VARCHAR(50) REFERENCES shop_items(id) ON DELETE SET NULL,
    prop_item_id VARCHAR(50) REFERENCES shop_items(id) ON DELETE SET NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- Updated_at 자동 업데이트 트리거
-- ============================================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_sessions_updated_at BEFORE UPDATE ON sessions FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_achievement_definitions_updated_at BEFORE UPDATE ON achievement_definitions FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_user_achievements_updated_at BEFORE UPDATE ON user_achievements FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_mab_arms_updated_at BEFORE UPDATE ON mab_arms FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_golden_time_stats_updated_at BEFORE UPDATE ON golden_time_stats FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_user_optimal_difficulty_updated_at BEFORE UPDATE ON user_optimal_difficulty FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_user_daily_stats_updated_at BEFORE UPDATE ON user_daily_stats FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_shop_items_updated_at BEFORE UPDATE ON shop_items FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_user_cat_equipment_updated_at BEFORE UPDATE ON user_cat_equipment FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================
-- MBTI 프로필 초기 데이터 삽입
-- ============================================================
INSERT INTO mbti_profiles (type_code, name, nickname, description, study_style,
    optimal_focus_range_min, optimal_focus_range_max,
    optimal_break_range_min, optimal_break_range_max,
    optimal_rounds_min, optimal_rounds_max,
    best_study_hours, completion_tendency, distraction_vulnerability, tips) VALUES
('INTJ', 'INTJ', '전략가', '독립적이고 분석적인 사고를 가진 전략적 계획자', '장기 목표를 세우고 체계적으로 깊이 파고드는 학습', 35, 50, 5, 7, 3, 4, '[6,7,8,21,22]', 0.85, 0.2, '["혼자만의 조용한 공간에서 최고 집중력 발휘", "장기 목표를 시각화하면 동기부여"]'),
('INTP', 'INTP', '논리술사', '논리적 분석과 창의적 문제 해결을 즐기는 사색가', '이론적 개념을 탐구하고 분석하는 학습', 30, 45, 5, 10, 3, 4, '[22,23,0,1,2]', 0.70, 0.4, '["관심 분야에서 높은 집중력", "시간 관리 도구 활용 권장"]'),
('ENTJ', 'ENTJ', '통솔자', '효율적이고 목표 지향적인 리더', '명확한 목표와 계획에 따른 체계적 학습', 25, 45, 5, 7, 4, 5, '[6,7,8,9]', 0.90, 0.15, '["목표 달성에 강한 동기부여", "효율적인 시간 관리"]'),
('ENTP', 'ENTP', '변론가', '혁신적 아이디어와 토론을 즐기는 도전자', '다양한 아이디어를 탐색하고 연결하는 학습', 20, 35, 5, 10, 3, 4, '[10,11,14,15,16]', 0.65, 0.5, '["새로운 주제에 대한 호기심 활용", "루틴화로 지속성 확보"]'),
('INFJ', 'INFJ', '옹호자', '깊은 통찰력과 이상을 추구하는 조용한 지도자', '의미 있는 목표를 위한 헌신적 학습', 30, 50, 7, 10, 3, 4, '[5,6,7,21,22]', 0.80, 0.3, '["조용한 환경에서 최고 효율", "가치 있는 목표 설정"]'),
('INFP', 'INFP', '중재자', '이상적 가치와 창의성을 추구하는 치유자', '개인적 의미를 찾으며 깊이 있게 학습', 25, 40, 7, 10, 2, 3, '[22,23,0,6,7]', 0.60, 0.5, '["영감을 주는 환경 조성", "감정 상태 관리 중요"]'),
('ENFJ', 'ENFJ', '선도자', '타인을 이끌고 영감을 주는 카리스마 리더', '그룹 학습과 토론을 통한 학습', 25, 40, 5, 7, 3, 5, '[9,10,11,14,15]', 0.85, 0.25, '["타인과의 학습에서 동기부여", "개인 시간도 확보"]'),
('ENFP', 'ENFP', '활동가', '열정적이고 창의적인 자유로운 영혼', '다양한 경험과 아이디어 탐색 학습', 15, 30, 5, 10, 2, 4, '[10,11,14,15,16]', 0.55, 0.6, '["흥미로운 주제에서 높은 몰입", "작은 목표로 성취감 유지"]'),
('ISTJ', 'ISTJ', '현실주의자', '책임감 있고 철저한 실행가', '체계적이고 순차적인 학습', 35, 50, 5, 7, 4, 5, '[6,7,8,9,20,21]', 0.95, 0.1, '["명확한 일정과 계획 수립", "일관된 루틴 유지"]'),
('ISFJ', 'ISFJ', '수호자', '헌신적이고 세심한 보호자', '안정적 환경에서 꼼꼼한 학습', 30, 45, 7, 10, 3, 4, '[8,9,10,20,21]', 0.90, 0.2, '["편안한 환경에서 최고 효율", "휴식 시간 충분히 확보"]'),
('ESTJ', 'ESTJ', '경영자', '효율적이고 조직적인 관리자', '목표 중심의 체계적 학습', 25, 40, 5, 7, 4, 5, '[7,8,9,10]', 0.92, 0.15, '["명확한 목표 설정", "효율적인 시간 관리"]'),
('ESFJ', 'ESFJ', '집정관', '사교적이고 배려심 깊은 호스트', '그룹 활동과 협력적 학습', 25, 35, 5, 10, 3, 4, '[9,10,11,14,15]', 0.85, 0.3, '["친근한 학습 환경 조성", "적절한 사회적 교류"]'),
('ISTP', 'ISTP', '장인', '실용적이고 논리적인 분석가', '실습과 경험을 통한 학습', 20, 35, 5, 7, 2, 4, '[10,11,14,22,23]', 0.70, 0.35, '["실제 적용에서 높은 집중력", "자유로운 학습 환경"]'),
('ISFP', 'ISFP', '모험가', '유연하고 감각적인 예술가', '경험과 감각을 통한 학습', 20, 35, 7, 10, 2, 3, '[10,11,15,16,17]', 0.60, 0.45, '["창의적 활동에서 몰입", "편안한 환경 조성"]'),
('ESTP', 'ESTP', '사업가', '활동적이고 현실적인 문제 해결사', '직접적 경험과 실습 학습', 15, 30, 5, 7, 2, 4, '[10,11,14,15,16]', 0.65, 0.5, '["활동적인 학습 방식 선호", "짧은 집중 시간 활용"]'),
('ESFP', 'ESFP', '연예인', '활발하고 사교적인 즉흥 연기자', '재미있고 상호작용적인 학습', 15, 25, 5, 10, 2, 3, '[10,11,14,15,16,17]', 0.50, 0.6, '["재미있는 학습 방식 활용", "짧은 세션으로 시작"]');

-- ============================================================
-- 기본 도전과제 데이터 삽입
-- ============================================================
INSERT INTO achievement_definitions (id, name, description, category, rarity, icon, coin_reward, requirement, is_hidden, display_order) VALUES
-- Focus Category
('focus_first', '첫 걸음', '첫 집중 세션 완료', 'focus', 'common', 'bi-flag', 50, '{"type":"total_completed","value":1}', FALSE, 1),
('focus_10', '집중 입문자', '10회 집중 세션 완료', 'focus', 'common', 'bi-award', 100, '{"type":"total_completed","value":10}', FALSE, 2),
('focus_50', '집중 수련생', '50회 집중 세션 완료', 'focus', 'uncommon', 'bi-award-fill', 300, '{"type":"total_completed","value":50}', FALSE, 3),
('focus_100', '집중 숙련자', '100회 집중 세션 완료', 'focus', 'rare', 'bi-trophy', 500, '{"type":"total_completed","value":100}', FALSE, 4),
('focus_500', '집중 마스터', '500회 집중 세션 완료', 'focus', 'epic', 'bi-trophy-fill', 1000, '{"type":"total_completed","value":500}', FALSE, 5),
('focus_1000', '집중의 전설', '1000회 집중 세션 완료', 'focus', 'legendary', 'bi-gem', 2000, '{"type":"total_completed","value":1000}', FALSE, 6),

-- Streak Category
('streak_3', '3일 연속', '3일 연속 집중 성공', 'streak', 'common', 'bi-fire', 100, '{"type":"streak_days","value":3}', FALSE, 10),
('streak_7', '일주일 전사', '7일 연속 집중 성공', 'streak', 'uncommon', 'bi-fire', 250, '{"type":"streak_days","value":7}', FALSE, 11),
('streak_14', '2주 정복자', '14일 연속 집중 성공', 'streak', 'rare', 'bi-fire', 500, '{"type":"streak_days","value":14}', FALSE, 12),
('streak_30', '한달의 기적', '30일 연속 집중 성공', 'streak', 'epic', 'bi-lightning', 1000, '{"type":"streak_days","value":30}', FALSE, 13),
('streak_100', '100일의 여정', '100일 연속 집중 성공', 'streak', 'legendary', 'bi-lightning-fill', 3000, '{"type":"streak_days","value":100}', FALSE, 14),

-- Time Category
('time_1h', '1시간 집중', '총 1시간 집중 달성', 'time', 'common', 'bi-clock', 50, '{"type":"total_focus_minutes","value":60}', FALSE, 20),
('time_10h', '10시간 집중', '총 10시간 집중 달성', 'time', 'uncommon', 'bi-clock-fill', 200, '{"type":"total_focus_minutes","value":600}', FALSE, 21),
('time_50h', '50시간 집중', '총 50시간 집중 달성', 'time', 'rare', 'bi-hourglass', 500, '{"type":"total_focus_minutes","value":3000}', FALSE, 22),
('time_100h', '100시간 집중', '총 100시간 집중 달성', 'time', 'epic', 'bi-hourglass-split', 1000, '{"type":"total_focus_minutes","value":6000}', FALSE, 23),
('time_500h', '500시간의 노력', '총 500시간 집중 달성', 'time', 'legendary', 'bi-hourglass-bottom', 3000, '{"type":"total_focus_minutes","value":30000}', FALSE, 24),

-- Special Category
('special_early_bird', '얼리버드', '오전 6시 이전 세션 완료', 'special', 'uncommon', 'bi-sunrise', 150, '{"type":"session_before_hour","value":6}', FALSE, 30),
('special_night_owl', '밤의 올빼미', '자정 이후 세션 완료', 'special', 'uncommon', 'bi-moon', 150, '{"type":"session_after_hour","value":0}', FALSE, 31),
('special_weekend_warrior', '주말 전사', '주말에 5회 세션 완료', 'special', 'rare', 'bi-calendar-week', 300, '{"type":"weekend_sessions","value":5}', FALSE, 32),
('special_perfect_week', '완벽한 한 주', '일주일 동안 매일 세션 완료', 'special', 'epic', 'bi-star', 500, '{"type":"perfect_week","value":1}', FALSE, 33),

-- Milestone Category
('milestone_coins_1000', '동전 수집가', '총 1000 코인 획득', 'milestone', 'uncommon', 'bi-coin', 100, '{"type":"total_coins","value":1000}', FALSE, 40),
('milestone_coins_10000', '코인 부자', '총 10000 코인 획득', 'milestone', 'rare', 'bi-cash-coin', 500, '{"type":"total_coins","value":10000}', FALSE, 41),
('milestone_all_tasks', '올라운더', '모든 과제 유형 완료', 'milestone', 'rare', 'bi-check2-all', 300, '{"type":"all_task_types","value":1}', FALSE, 42),

-- Hidden Category
('hidden_comeback', '컴백 스토리', '7일 휴식 후 복귀 성공', 'hidden', 'rare', 'bi-arrow-return-right', 300, '{"type":"comeback_after_days","value":7}', TRUE, 50),
('hidden_perfectionist', '완벽주의자', '하루에 10회 이상 완료', 'hidden', 'epic', 'bi-bullseye', 500, '{"type":"daily_sessions","value":10}', TRUE, 51);

-- ============================================================
-- Row Level Security (RLS) 설정
-- ============================================================
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_achievements ENABLE ROW LEVEL SECURITY;
ALTER TABLE mab_arms ENABLE ROW LEVEL SECURITY;
ALTER TABLE golden_time_stats ENABLE ROW LEVEL SECURITY;
ALTER TABLE adaptive_difficulty_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_optimal_difficulty ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_survey_answers ENABLE ROW LEVEL SECURITY;
ALTER TABLE coin_transactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_daily_stats ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_auth_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_inventory ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_cat_equipment ENABLE ROW LEVEL SECURITY;

-- 사용자는 자신의 데이터만 접근 가능 (나중에 auth.uid()로 변경)
-- 현재는 서비스 역할 키로 접근하므로 정책은 필요에 따라 추가

-- ============================================================
-- 완료 메시지
-- ============================================================
-- 스키마 생성이 완료되었습니다!
-- 테이블 16개, 트리거 10개, 인덱스 다수가 생성되었습니다.
