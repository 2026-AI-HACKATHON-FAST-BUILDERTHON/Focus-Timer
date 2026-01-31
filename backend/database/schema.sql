-- ============================================================
-- Focus Timer Database Schema
-- Designed for: MySQL 8.0+
-- Normalization: 3NF with strategic denormalization for performance
-- ============================================================

-- Create database
CREATE DATABASE IF NOT EXISTS focus_timer
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE focus_timer;

-- ============================================================
-- 1. Users Table
-- Primary user authentication and profile
-- ============================================================
CREATE TABLE users (
    id CHAR(36) PRIMARY KEY,  -- UUID
    email VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    nickname VARCHAR(100),
    mbti_type CHAR(4),  -- INTJ, ENFP, etc.
    coin_balance INT UNSIGNED DEFAULT 0,
    total_coins_earned INT UNSIGNED DEFAULT 0,  -- Denormalized for leaderboard
    current_streak_days INT UNSIGNED DEFAULT 0,
    best_streak_days INT UNSIGNED DEFAULT 0,
    persona_type VARCHAR(30),  -- Cached classification
    is_active BOOLEAN DEFAULT TRUE,  -- Soft delete flag
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    last_session_at TIMESTAMP NULL,

    UNIQUE INDEX idx_users_email (email),
    INDEX idx_users_coin_balance (coin_balance DESC),
    INDEX idx_users_last_session (last_session_at DESC),
    INDEX idx_users_mbti (mbti_type),
    INDEX idx_users_persona (persona_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ============================================================
-- 2. Sessions Table
-- Core focus timer session data
-- ============================================================
CREATE TABLE sessions (
    id CHAR(36) PRIMARY KEY,  -- UUID
    user_id CHAR(36) NOT NULL,
    task_type ENUM('reading', 'practice', 'creation', 'routine') NOT NULL,
    difficulty TINYINT UNSIGNED NOT NULL,  -- 1-5
    goal VARCHAR(500),
    status ENUM('in_progress', 'completed', 'aborted') NOT NULL DEFAULT 'in_progress',
    abort_reason ENUM('phone', 'tired', 'bored', 'anxious', 'environment', 'urgent', 'other'),
    abort_detail VARCHAR(500),

    -- Time tracking
    total_focus_sec INT UNSIGNED DEFAULT 0,
    total_break_sec INT UNSIGNED DEFAULT 0,
    rounds_completed TINYINT UNSIGNED DEFAULT 0,

    -- Plan details
    planned_focus_min SMALLINT UNSIGNED NOT NULL DEFAULT 25,
    planned_break_min SMALLINT UNSIGNED NOT NULL DEFAULT 5,
    planned_rounds TINYINT UNSIGNED NOT NULL DEFAULT 4,
    mode_plan JSON,  -- Full plan as JSON for flexibility

    -- Reward
    coin_reward INT UNSIGNED DEFAULT 0,

    -- Temporal context (for analytics)
    start_hour TINYINT UNSIGNED NOT NULL,  -- 0-23
    day_of_week TINYINT UNSIGNED NOT NULL,  -- 0=Monday, 6=Sunday

    -- AI recommendation context
    used_ai_recommendation BOOLEAN DEFAULT FALSE,
    ai_predicted_completion_prob DECIMAL(4,3),

    -- Audit
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,

    -- Query pattern indexes
    INDEX idx_sessions_user_created (user_id, created_at DESC),
    INDEX idx_sessions_user_status (user_id, status),
    INDEX idx_sessions_user_date (user_id, created_at, status),
    INDEX idx_sessions_user_task (user_id, task_type),
    INDEX idx_sessions_golden_time (user_id, start_hour, day_of_week, status),
    INDEX idx_sessions_completed_at (completed_at DESC),
    INDEX idx_sessions_difficulty (difficulty, status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ============================================================
-- 3. Achievement Definitions Table
-- Master table for all 57+ achievements (reference data)
-- ============================================================
CREATE TABLE achievement_definitions (
    id VARCHAR(50) PRIMARY KEY,  -- 'focus_first_session', 'streak_7days', etc.
    name VARCHAR(100) NOT NULL,
    description VARCHAR(500) NOT NULL,
    category ENUM('focus', 'streak', 'time', 'milestone', 'special', 'hidden') NOT NULL,
    rarity ENUM('common', 'uncommon', 'rare', 'epic', 'legendary') NOT NULL,
    icon VARCHAR(50) NOT NULL,  -- Bootstrap icon class
    coin_reward INT UNSIGNED NOT NULL,
    requirement JSON NOT NULL,  -- {"type": "total_sessions", "value": 10}
    is_hidden BOOLEAN DEFAULT FALSE,
    display_order SMALLINT UNSIGNED DEFAULT 0,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    INDEX idx_achievements_category (category, display_order),
    INDEX idx_achievements_rarity (rarity)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ============================================================
-- 4. User Achievements Table
-- Progress tracking per user per achievement
-- ============================================================
CREATE TABLE user_achievements (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id CHAR(36) NOT NULL,
    achievement_id VARCHAR(50) NOT NULL,
    current_value INT UNSIGNED DEFAULT 0,
    target_value INT UNSIGNED NOT NULL,
    progress DECIMAL(5,4) AS (
        LEAST(1.0, current_value / target_value)
    ) STORED,
    is_unlocked BOOLEAN DEFAULT FALSE,
    unlocked_at TIMESTAMP NULL,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    UNIQUE INDEX idx_user_achievement (user_id, achievement_id),

    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (achievement_id) REFERENCES achievement_definitions(id) ON DELETE CASCADE,

    INDEX idx_user_achievements_unlocked (user_id, is_unlocked),
    INDEX idx_user_achievements_progress (user_id, progress DESC)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ============================================================
-- 5. MAB Arms State Table
-- Thompson Sampling Multi-Armed Bandit per user
-- ============================================================
CREATE TABLE mab_arms (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id CHAR(36) NOT NULL,
    arm_key VARCHAR(20) NOT NULL,  -- "25_5_4" (focus_break_rounds)

    -- Arm parameters
    focus_minutes TINYINT UNSIGNED NOT NULL,
    break_minutes TINYINT UNSIGNED NOT NULL,
    rounds TINYINT UNSIGNED NOT NULL,

    -- Beta distribution parameters (Thompson Sampling)
    alpha DECIMAL(10,2) DEFAULT 1.0,  -- Success count + 1
    beta DECIMAL(10,2) DEFAULT 1.0,   -- Failure count + 1

    -- Computed metrics
    expected_value DECIMAL(5,4) AS (
        alpha / (alpha + beta)
    ) STORED,
    total_trials INT UNSIGNED AS (
        FLOOR(alpha + beta - 2)
    ) STORED,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    UNIQUE INDEX idx_mab_user_arm (user_id, arm_key),

    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,

    INDEX idx_mab_expected_value (user_id, expected_value DESC),
    INDEX idx_mab_focus_range (user_id, focus_minutes)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ============================================================
-- 6. Golden Time Stats Table
-- Hour/Day completion statistics per user
-- ============================================================
CREATE TABLE golden_time_stats (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id CHAR(36) NOT NULL,
    hour TINYINT UNSIGNED NOT NULL,  -- 0-23
    day_of_week TINYINT UNSIGNED NOT NULL,  -- 0-6

    success_count INT UNSIGNED DEFAULT 0,
    total_count INT UNSIGNED DEFAULT 0,
    completion_rate DECIMAL(5,4) AS (
        CASE WHEN total_count > 0 THEN success_count / total_count ELSE 0 END
    ) STORED,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    UNIQUE INDEX idx_golden_time_user_slot (user_id, hour, day_of_week),

    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,

    INDEX idx_golden_time_rate (user_id, completion_rate DESC),
    INDEX idx_golden_time_hour (user_id, hour)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ============================================================
-- 7. Adaptive Difficulty History Table
-- Tracks difficulty performance for optimal difficulty calculation
-- ============================================================
CREATE TABLE adaptive_difficulty_history (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id CHAR(36) NOT NULL,
    difficulty TINYINT UNSIGNED NOT NULL,
    success BOOLEAN NOT NULL,
    session_id CHAR(36),

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE SET NULL,

    INDEX idx_difficulty_user_recent (user_id, created_at DESC),
    INDEX idx_difficulty_success (user_id, difficulty, success)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ============================================================
-- 8. User Optimal Difficulty Cache
-- Precomputed optimal difficulty per user
-- ============================================================
CREATE TABLE user_optimal_difficulty (
    user_id CHAR(36) PRIMARY KEY,
    optimal_difficulty DECIMAL(3,1) DEFAULT 3.0,
    recommended_difficulty TINYINT UNSIGNED AS (
        ROUND(optimal_difficulty)
    ) STORED,
    recent_success_rate DECIMAL(5,4),
    sample_size INT UNSIGNED DEFAULT 0,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ============================================================
-- 9. MBTI Profiles Reference Table
-- Reference data for 16 MBTI types
-- ============================================================
CREATE TABLE mbti_profiles (
    type_code CHAR(4) PRIMARY KEY,  -- INTJ, ENFP, etc.
    name VARCHAR(50) NOT NULL,
    nickname VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    study_style TEXT,

    -- Optimal ranges
    optimal_focus_range_min TINYINT UNSIGNED NOT NULL,
    optimal_focus_range_max TINYINT UNSIGNED NOT NULL,
    optimal_break_range_min TINYINT UNSIGNED NOT NULL,
    optimal_break_range_max TINYINT UNSIGNED NOT NULL,
    optimal_rounds_min TINYINT UNSIGNED NOT NULL,
    optimal_rounds_max TINYINT UNSIGNED NOT NULL,

    best_study_hours JSON,  -- [6, 7, 8, 21, 22]
    completion_tendency DECIMAL(3,2),  -- 0.00-1.00
    distraction_vulnerability DECIMAL(3,2),
    tips JSON  -- ["tip1", "tip2", "tip3"]
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ============================================================
-- 10. User Survey Answers Table
-- MBTI survey responses
-- ============================================================
CREATE TABLE user_survey_answers (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id CHAR(36) NOT NULL,
    question_id VARCHAR(20) NOT NULL,  -- q1_energy, q2_study_env, etc.
    dimension CHAR(2) NOT NULL,  -- EI, SN, TF, JP
    answer CHAR(1) NOT NULL,  -- E, I, S, N, T, F, J, P

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE INDEX idx_survey_user_question (user_id, question_id),

    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ============================================================
-- 11. Coin Transactions Table
-- Audit trail for coin balance changes
-- ============================================================
CREATE TABLE coin_transactions (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id CHAR(36) NOT NULL,
    amount INT NOT NULL,  -- Positive for earn, negative for spend
    balance_after INT UNSIGNED NOT NULL,
    transaction_type ENUM(
        'session_reward',
        'achievement_reward',
        'purchase',
        'refund',
        'bonus',
        'adjustment'
    ) NOT NULL,
    reference_type VARCHAR(30),  -- 'session', 'achievement', 'item'
    reference_id VARCHAR(50),
    description VARCHAR(200),

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,

    INDEX idx_coin_tx_user_date (user_id, created_at DESC),
    INDEX idx_coin_tx_type (user_id, transaction_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ============================================================
-- 12. User Daily Stats (Aggregated)
-- Pre-aggregated daily statistics for trend analysis
-- ============================================================
CREATE TABLE user_daily_stats (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id CHAR(36) NOT NULL,
    stat_date DATE NOT NULL,

    total_sessions INT UNSIGNED DEFAULT 0,
    completed_sessions INT UNSIGNED DEFAULT 0,
    aborted_sessions INT UNSIGNED DEFAULT 0,
    total_focus_minutes INT UNSIGNED DEFAULT 0,
    total_break_minutes INT UNSIGNED DEFAULT 0,
    total_coins_earned INT UNSIGNED DEFAULT 0,

    completion_rate DECIMAL(5,4) AS (
        CASE WHEN total_sessions > 0
             THEN completed_sessions / total_sessions
             ELSE 0 END
    ) STORED,

    -- Top abort reason of the day
    top_abort_reason VARCHAR(20),

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    UNIQUE INDEX idx_daily_stats_user_date (user_id, stat_date),

    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,

    INDEX idx_daily_stats_date_range (user_id, stat_date DESC)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ============================================================
-- 13. User Sessions (JWT Refresh Tokens)
-- ============================================================
CREATE TABLE user_auth_sessions (
    id CHAR(36) PRIMARY KEY,
    user_id CHAR(36) NOT NULL,
    refresh_token_hash VARCHAR(255) NOT NULL,
    device_info VARCHAR(500),
    ip_address VARCHAR(45),
    expires_at TIMESTAMP NOT NULL,
    is_revoked BOOLEAN DEFAULT FALSE,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,

    INDEX idx_user_sessions_user (user_id),
    INDEX idx_user_sessions_expires (expires_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ============================================================
-- 14. Shop Items (for coin spending)
-- ============================================================
CREATE TABLE shop_items (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    item_type ENUM('hat', 'accessory', 'prop', 'theme', 'sound') NOT NULL,
    set_name VARCHAR(50),
    tag VARCHAR(30),
    price INT UNSIGNED NOT NULL,
    color VARCHAR(30),
    preview_image_url VARCHAR(500),
    is_available BOOLEAN DEFAULT TRUE,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    INDEX idx_shop_items_type (item_type, is_available),
    INDEX idx_shop_items_price (price)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ============================================================
-- 15. User Inventory
-- ============================================================
CREATE TABLE user_inventory (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id CHAR(36) NOT NULL,
    item_id VARCHAR(50) NOT NULL,
    quantity INT UNSIGNED DEFAULT 1,
    acquired_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE INDEX idx_inventory_user_item (user_id, item_id),

    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (item_id) REFERENCES shop_items(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ============================================================
-- 16. Cat Equipment (cosmetic slots)
-- ============================================================
CREATE TABLE user_cat_equipment (
    user_id CHAR(36) PRIMARY KEY,
    hat_item_id VARCHAR(50),
    accessory_item_id VARCHAR(50),
    prop_item_id VARCHAR(50),

    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (hat_item_id) REFERENCES shop_items(id) ON DELETE SET NULL,
    FOREIGN KEY (accessory_item_id) REFERENCES shop_items(id) ON DELETE SET NULL,
    FOREIGN KEY (prop_item_id) REFERENCES shop_items(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ============================================================
-- Views for Common Query Patterns
-- ============================================================

-- User Stats Summary View
CREATE OR REPLACE VIEW v_user_stats AS
SELECT
    u.id AS user_id,
    u.nickname,
    u.mbti_type,
    u.persona_type,
    u.coin_balance,
    u.current_streak_days,
    u.best_streak_days,
    COUNT(s.id) AS total_sessions,
    SUM(CASE WHEN s.status = 'completed' THEN 1 ELSE 0 END) AS completed_sessions,
    ROUND(SUM(CASE WHEN s.status = 'completed' THEN 1 ELSE 0 END) / NULLIF(COUNT(s.id), 0), 3) AS completion_rate,
    SUM(s.total_focus_sec) / 60 AS total_focus_minutes,
    (SELECT COUNT(*) FROM user_achievements ua WHERE ua.user_id = u.id AND ua.is_unlocked = TRUE) AS unlocked_achievements
FROM users u
LEFT JOIN sessions s ON u.id = s.user_id AND s.status IS NOT NULL
WHERE u.is_active = TRUE
GROUP BY u.id;


-- Golden Hours View (Top 3 hours per user)
CREATE OR REPLACE VIEW v_golden_hours AS
SELECT
    user_id,
    hour,
    completion_rate,
    total_count,
    RANK() OVER (PARTITION BY user_id ORDER BY completion_rate DESC, total_count DESC) as hour_rank
FROM golden_time_stats
WHERE total_count >= 3;


-- Recent Performance View (Last 7 days)
CREATE OR REPLACE VIEW v_recent_performance AS
SELECT
    user_id,
    COUNT(*) AS sessions_7d,
    SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) AS completed_7d,
    ROUND(SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0), 3) AS completion_rate_7d,
    SUM(total_focus_sec) / 60 AS focus_minutes_7d
FROM sessions
WHERE created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
  AND status IS NOT NULL
GROUP BY user_id;


-- Leaderboard View
CREATE OR REPLACE VIEW v_leaderboard AS
SELECT
    u.id,
    u.nickname,
    u.coin_balance,
    u.total_coins_earned,
    u.best_streak_days,
    (SELECT COUNT(*) FROM user_achievements ua WHERE ua.user_id = u.id AND ua.is_unlocked = TRUE) AS achievement_count,
    RANK() OVER (ORDER BY u.total_coins_earned DESC) as coin_rank
FROM users u
WHERE u.is_active = TRUE
ORDER BY u.total_coins_earned DESC;


-- ============================================================
-- Insert MBTI Profile Reference Data
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
-- Insert Default Achievement Definitions
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
