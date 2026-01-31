import React, { useState, useEffect } from 'react';
import styled from 'styled-components';
import * as api from '../services/api';
import Loader from '../components/common/Loader';

const AnalysisPage: React.FC = () => {
  const [level, setLevel] = useState<api.LevelInfo | null>(null);
  const [heatmap, setHeatmap] = useState<api.GoldenTimeHeatmapResponse | null>(null);
  const [persona, setPersona] = useState<api.PersonaAnalysisResponse | null>(null);
  const [trends, setTrends] = useState<api.TrendAnalysisResponse | null>(null);
  const [insights, setInsights] = useState<api.AIInsightsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'overview' | 'goldentime' | 'persona'>('overview');

  useEffect(() => {
    fetchAllData();
  }, []);

  const fetchAllData = async () => {
    setLoading(true);
    try {
      // 통합 API로 1번 호출 (5개 API → 1개로 최적화)
      const dashboard = await api.getDashboard();

      setLevel(dashboard.level);
      setHeatmap(dashboard.heatmap);
      setPersona(dashboard.persona);
      setTrends(dashboard.trends);
      setInsights(dashboard.insights);
    } catch (error) {
      console.error('Failed to fetch analytics:', error);
    } finally {
      setLoading(false);
    }
  };

  const dayNames = ['월', '화', '수', '목', '금', '토', '일'];

  const getHeatmapColor = (rate: number) => {
    if (rate === 0) return '#E2E8F0';
    if (rate < 0.3) return '#C4B5FD';
    if (rate < 0.5) return '#A78BFA';
    if (rate < 0.7) return '#8B5CF6';
    if (rate < 0.85) return '#7C3AED';
    return '#6D28D9';
  };

  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case 'improving':
        return 'bi-graph-up-arrow';
      case 'declining':
        return 'bi-graph-down-arrow';
      default:
        return 'bi-dash-lg';
    }
  };

  const getTrendColor = (trend: string) => {
    switch (trend) {
      case 'improving':
        return '#48BB78';
      case 'declining':
        return '#F56565';
      default:
        return '#A0AEC0';
    }
  };

  const getInsightIcon = (type: string) => {
    switch (type) {
      case 'success':
        return { icon: 'bi-check-circle-fill', color: '#48BB78' };
      case 'warning':
        return { icon: 'bi-exclamation-triangle-fill', color: '#ECC94B' };
      case 'achievement':
        return { icon: 'bi-trophy-fill', color: '#9F7AEA' };
      default:
        return { icon: 'bi-lightbulb-fill', color: '#4299E1' };
    }
  };

  if (loading) {
    return (
      <LoadingWrapper>
        <Loader />
      </LoadingWrapper>
    );
  }

  return (
    <StyledWrapper>
      {/* Level Card */}
      {level && (
        <div className="level-card">
          <div className="level-icon">
            <i className="bi bi-clock-fill"></i>
          </div>
          <div className="level-info">
            <div className="level-header">
              <div className="level-badge">Lv.{level.level}</div>
              <div className="level-name">{level.level_name}</div>
            </div>
            <div className="level-progress">
              <div
                className="progress-bar"
                style={{ width: `${level.progress_percent}%` }}
              ></div>
            </div>
            <div className="level-stats">
              <span>{level.current_achievements}/{level.total_achievements} 업적</span>
              <span>다음 레벨까지 {level.next_level_threshold - level.current_achievements}개</span>
            </div>
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="tabs">
        <button
          className={`tab ${activeTab === 'overview' ? 'active' : ''}`}
          onClick={() => setActiveTab('overview')}
        >
          <i className="bi bi-grid-1x2-fill"></i> 개요
        </button>
        <button
          className={`tab ${activeTab === 'goldentime' ? 'active' : ''}`}
          onClick={() => setActiveTab('goldentime')}
        >
          <i className="bi bi-clock-fill"></i> 골든타임
        </button>
        <button
          className={`tab ${activeTab === 'persona' ? 'active' : ''}`}
          onClick={() => setActiveTab('persona')}
        >
          <i className="bi bi-person-badge-fill"></i> 페르소나
        </button>
      </div>

      {/* Overview Tab */}
      {activeTab === 'overview' && (
        <div className="tab-content">
          {/* AI Insights */}
          {insights && insights.insights.length > 0 && (
            <section className="section">
              <h2><i className="bi bi-cpu-fill"></i> AI 인사이트</h2>
              <div className="insights-list">
                {insights.insights.map((insight, idx) => {
                  const { icon, color } = getInsightIcon(insight.type);
                  return (
                    <div key={idx} className="insight-card" style={{ borderLeftColor: color }}>
                      <div className="insight-icon" style={{ color }}>
                        <i className={icon}></i>
                      </div>
                      <div className="insight-content">
                        <h4>{insight.title}</h4>
                        <p>{insight.message}</p>
                      </div>
                    </div>
                  );
                })}
              </div>
            </section>
          )}

          {/* Trend Summary */}
          {trends && (
            <section className="section">
              <h2><i className="bi bi-graph-up"></i> 주간 트렌드</h2>
              <div className="trend-cards">
                <div className="trend-card">
                  <div className="trend-icon" style={{ color: getTrendColor(trends.weekly_trend) }}>
                    <i className={getTrendIcon(trends.weekly_trend)}></i>
                  </div>
                  <div className="trend-label">주간 추세</div>
                  <div className="trend-value" style={{ color: getTrendColor(trends.weekly_trend) }}>
                    {trends.weekly_trend === 'improving' ? '상승' :
                     trends.weekly_trend === 'declining' ? '하락' : '유지'}
                  </div>
                </div>
                <div className="trend-card">
                  <div className="trend-icon">
                    <i className="bi bi-fire"></i>
                  </div>
                  <div className="trend-label">연속 성공</div>
                  <div className="trend-value">{trends.streak_days}일</div>
                </div>
                <div className="trend-card">
                  <div className="trend-icon">
                    <i className="bi bi-percent"></i>
                  </div>
                  <div className="trend-label">완주율 변화</div>
                  <div
                    className="trend-value"
                    style={{ color: trends.completion_rate_change >= 0 ? '#48BB78' : '#F56565' }}
                  >
                    {trends.completion_rate_change >= 0 ? '+' : ''}
                    {Math.round(trends.completion_rate_change * 100)}%
                  </div>
                </div>
              </div>

              {/* Simple Bar Chart */}
              <div className="chart-container">
                <div className="chart-bars">
                  {trends.daily_data.slice(-7).map((day, idx) => (
                    <div key={idx} className="chart-bar-wrapper">
                      <div
                        className="chart-bar"
                        style={{
                          height: `${Math.max(5, (day.focus_minutes / 120) * 100)}%`,
                          backgroundColor: day.completed > 0 ? '#6C63FF' : '#E2E8F0'
                        }}
                      >
                        <span className="bar-value">{day.focus_minutes}분</span>
                      </div>
                      <span className="bar-label">{day.day_name}</span>
                    </div>
                  ))}
                </div>
              </div>
            </section>
          )}
        </div>
      )}

      {/* Golden Time Tab */}
      {activeTab === 'goldentime' && heatmap && (
        <div className="tab-content">
          <section className="section">
            <h2><i className="bi bi-clock-fill"></i> 골든타임 히트맵</h2>
            <p className="section-desc">색이 진할수록 완주율이 높은 시간대입니다.</p>

            {/* Golden Hours Badges */}
            {heatmap.golden_hours.length > 0 && (
              <div className="golden-badges">
                <span className="badge-label">골든타임:</span>
                {heatmap.golden_hours.map((hour) => (
                  <span key={hour} className="golden-badge">
                    <i className="bi bi-star-fill"></i> {hour}시
                  </span>
                ))}
              </div>
            )}

            {/* Heatmap Grid */}
            <div className="heatmap-container">
              <div className="heatmap-header">
                <div className="heatmap-corner"></div>
                {dayNames.map((day) => (
                  <div key={day} className="heatmap-day">{day}</div>
                ))}
              </div>
              <div className="heatmap-body">
                {[6, 9, 12, 15, 18, 21, 0].map((hour) => (
                  <div key={hour} className="heatmap-row">
                    <div className="heatmap-hour">{hour}시</div>
                    {dayNames.map((_, dayIdx) => {
                      const cellData = heatmap.heatmap_data.find(
                        (d) => d.hour === hour && d.day === dayIdx
                      );
                      const rate = cellData?.completion_rate || 0;
                      return (
                        <div
                          key={dayIdx}
                          className="heatmap-cell"
                          style={{ backgroundColor: getHeatmapColor(rate) }}
                          title={`${hour}시 ${dayNames[dayIdx]}: ${Math.round(rate * 100)}% (${cellData?.total_sessions || 0}세션)`}
                        >
                          {cellData && cellData.total_sessions > 0 && (
                            <span className="cell-value">{Math.round(rate * 100)}%</span>
                          )}
                        </div>
                      );
                    })}
                  </div>
                ))}
              </div>
            </div>

            {/* Best Day */}
            {heatmap.best_day_name && (
              <div className="best-day-card">
                <i className="bi bi-calendar-check-fill"></i>
                <span>최고의 요일: <strong>{heatmap.best_day_name}요일</strong></span>
              </div>
            )}

            <div className="heatmap-legend">
              <span>낮음</span>
              <div className="legend-colors">
                <div style={{ backgroundColor: '#E2E8F0' }}></div>
                <div style={{ backgroundColor: '#C4B5FD' }}></div>
                <div style={{ backgroundColor: '#A78BFA' }}></div>
                <div style={{ backgroundColor: '#8B5CF6' }}></div>
                <div style={{ backgroundColor: '#7C3AED' }}></div>
                <div style={{ backgroundColor: '#6D28D9' }}></div>
              </div>
              <span>높음</span>
            </div>
          </section>
        </div>
      )}

      {/* Persona Tab */}
      {activeTab === 'persona' && persona && (
        <div className="tab-content">
          <section className="section">
            <div className="persona-card">
              <div className="persona-header">
                <div className="persona-icon-large">
                  <i className={persona.persona_icon}></i>
                </div>
                <div className="persona-title">
                  <h3>{persona.persona_name}</h3>
                  <div className="confidence-badge">
                    신뢰도: {Math.round(persona.confidence * 100)}%
                  </div>
                </div>
              </div>
              <p className="persona-description">{persona.description}</p>

              <div className="persona-stats">
                <div className="stat">
                  <i className="bi bi-check-circle"></i>
                  <span className="stat-value">{Math.round(persona.completion_rate * 100)}%</span>
                  <span className="stat-label">완주율</span>
                </div>
                <div className="stat">
                  <i className="bi bi-hourglass-split"></i>
                  <span className="stat-value">{Math.round(persona.avg_focus_minutes)}분</span>
                  <span className="stat-label">평균 집중</span>
                </div>
              </div>

              {/* Strengths */}
              <div className="trait-section">
                <h4><i className="bi bi-hand-thumbs-up-fill"></i> 강점</h4>
                <div className="trait-list">
                  {persona.strengths.map((s, idx) => (
                    <span key={idx} className="trait trait-strength">{s}</span>
                  ))}
                </div>
              </div>

              {/* Weaknesses */}
              {persona.weaknesses.length > 0 && (
                <div className="trait-section">
                  <h4><i className="bi bi-exclamation-circle-fill"></i> 주의점</h4>
                  <div className="trait-list">
                    {persona.weaknesses.map((w, idx) => (
                      <span key={idx} className="trait trait-weakness">{w}</span>
                    ))}
                  </div>
                </div>
              )}

              {/* Tips */}
              <div className="tips-section">
                <h4><i className="bi bi-lightbulb-fill"></i> 맞춤 팁</h4>
                <ul className="tips-list">
                  {persona.tips.map((tip, idx) => (
                    <li key={idx}>{tip}</li>
                  ))}
                </ul>
              </div>
            </div>
          </section>
        </div>
      )}

      {/* No Data Message */}
      {!loading && !heatmap && !persona && !trends && (
        <div className="no-data">
          <i className="bi bi-inbox"></i>
          <h3>아직 분석할 데이터가 없어요</h3>
          <p>세션을 더 진행하면 AI가 당신만의 패턴을 분석해드려요.</p>
        </div>
      )}
    </StyledWrapper>
  );
};

const LoadingWrapper = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  color: #718096;

`;

const StyledWrapper = styled.div`
  padding: 20px;
  background: #FFFFFF;
  border-radius: 0 0 24px 24px;

  /* Level Card */
  .level-card {
    background: linear-gradient(135deg, #F0F4FF 0%, #E8EDFF 100%);
    border-radius: 16px;
    padding: 16px;
    display: flex;
    align-items: center;
    gap: 14px;
    margin-bottom: 20px;
    border: 1px solid #E2E8F0;
  }

  .level-icon {
    width: 50px;
    height: 50px;
    background: linear-gradient(135deg, #6C63FF 0%, #5046E5 100%);
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 22px;
    color: #FFFFFF;
  }

  .level-info {
    flex: 1;
  }

  .level-header {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 8px;
  }

  .level-badge {
    background: #6C63FF;
    color: #fff;
    padding: 3px 10px;
    border-radius: 12px;
    font-size: 11px;
    font-weight: 600;
  }

  .level-name {
    font-size: 15px;
    font-weight: 600;
    color: #2D3748;
  }

  .level-progress {
    height: 6px;
    background: #E2E8F0;
    border-radius: 3px;
    overflow: hidden;
    margin-bottom: 6px;
  }

  .progress-bar {
    height: 100%;
    background: linear-gradient(90deg, #6C63FF, #9F7AEA);
    border-radius: 3px;
    transition: width 0.5s ease;
  }

  .level-stats {
    display: flex;
    justify-content: space-between;
    font-size: 11px;
    color: #718096;
  }

  /* Tabs */
  .tabs {
    display: flex;
    gap: 6px;
    margin-bottom: 16px;
    overflow-x: auto;
    padding-bottom: 4px;
  }

  .tab {
    flex: 1;
    padding: 10px 12px;
    background: #F0F4FF;
    border: none;
    border-radius: 10px;
    color: #718096;
    font-size: 13px;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 6px;
    white-space: nowrap;

    &.active {
      background: #6C63FF;
      color: #fff;
    }

    &:hover:not(.active) {
      background: #E8EDFF;
    }

    i {
      font-size: 14px;
    }
  }

  /* Sections */
  .section {
    background: #FAFBFF;
    border-radius: 14px;
    padding: 16px;
    margin-bottom: 16px;
    border: 1px solid #E2E8F0;

    h2 {
      font-size: 15px;
      font-weight: 600;
      margin-bottom: 14px;
      display: flex;
      align-items: center;
      gap: 8px;
      color: #2D3748;

      i {
        color: #6C63FF;
      }
    }
  }

  .section-desc {
    color: #718096;
    font-size: 12px;
    margin-bottom: 14px;
  }

  /* Insights */
  .insights-list {
    display: flex;
    flex-direction: column;
    gap: 10px;
  }

  .insight-card {
    background: #FFFFFF;
    border-radius: 10px;
    padding: 12px;
    display: flex;
    gap: 10px;
    border-left: 3px solid;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  }

  .insight-icon {
    font-size: 18px;
  }

  .insight-content {
    flex: 1;

    h4 {
      font-size: 13px;
      font-weight: 600;
      margin-bottom: 3px;
      color: #2D3748;
    }

    p {
      font-size: 12px;
      color: #718096;
      line-height: 1.4;
    }
  }

  /* Trend Cards */
  .trend-cards {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 10px;
    margin-bottom: 16px;
  }

  .trend-card {
    background: #FFFFFF;
    border-radius: 10px;
    padding: 12px;
    text-align: center;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  }

  .trend-icon {
    font-size: 20px;
    margin-bottom: 6px;
    color: #6C63FF;
  }

  .trend-label {
    font-size: 11px;
    color: #718096;
    margin-bottom: 3px;
  }

  .trend-value {
    font-size: 15px;
    font-weight: 700;
    color: #2D3748;
  }

  /* Chart */
  .chart-container {
    background: #FFFFFF;
    border-radius: 10px;
    padding: 24px 16px 16px 16px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  }

  .chart-bars {
    display: flex;
    justify-content: space-between;
    align-items: flex-end;
    height: 100px;
    gap: 6px;
    margin-top: 8px;
  }

  .chart-bar-wrapper {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    height: 100%;
  }

  .chart-bar {
    width: 100%;
    max-width: 32px;
    border-radius: 6px 6px 0 0;
    position: relative;
    transition: height 0.3s ease;
    display: flex;
    align-items: flex-start;
    justify-content: center;
  }

  .bar-value {
    position: absolute;
    top: -18px;
    font-size: 9px;
    color: #718096;
    white-space: nowrap;
  }

  .bar-label {
    margin-top: 6px;
    font-size: 11px;
    color: #718096;
  }

  /* Heatmap */
  .golden-badges {
    display: flex;
    align-items: center;
    gap: 6px;
    margin-bottom: 14px;
    flex-wrap: wrap;
  }

  .badge-label {
    color: #718096;
    font-size: 12px;
  }

  .golden-badge {
    background: linear-gradient(135deg, #F6E05E 0%, #ECC94B 100%);
    color: #744210;
    padding: 4px 10px;
    border-radius: 14px;
    font-size: 11px;
    font-weight: 600;
    display: flex;
    align-items: center;
    gap: 3px;

    i {
      font-size: 10px;
    }
  }

  .heatmap-container {
    background: #FFFFFF;
    border-radius: 10px;
    padding: 12px;
    overflow-x: auto;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  }

  .heatmap-header {
    display: grid;
    grid-template-columns: 40px repeat(7, 1fr);
    gap: 3px;
    margin-bottom: 3px;
  }

  .heatmap-corner {
    width: 40px;
  }

  .heatmap-day {
    text-align: center;
    font-size: 10px;
    color: #718096;
    padding: 3px;
  }

  .heatmap-body {
    display: flex;
    flex-direction: column;
    gap: 3px;
  }

  .heatmap-row {
    display: grid;
    grid-template-columns: 40px repeat(7, 1fr);
    gap: 3px;
  }

  .heatmap-hour {
    font-size: 10px;
    color: #718096;
    display: flex;
    align-items: center;
    justify-content: flex-end;
    padding-right: 6px;
  }

  .heatmap-cell {
    aspect-ratio: 1;
    border-radius: 4px;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    transition: transform 0.2s;
    min-height: 28px;

    &:hover {
      transform: scale(1.1);
      z-index: 1;
    }
  }

  .cell-value {
    font-size: 8px;
    font-weight: 600;
    color: #FFFFFF;
  }

  .best-day-card {
    background: linear-gradient(135deg, #F0FFF4 0%, #C6F6D5 100%);
    border-radius: 10px;
    padding: 12px;
    display: flex;
    align-items: center;
    gap: 10px;
    margin-top: 14px;
    margin-bottom: 14px;

    i {
      font-size: 20px;
      color: #48BB78;
    }

    span {
      font-size: 13px;
      color: #276749;
    }

    strong {
      color: #22543D;
    }
  }

  .heatmap-legend {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 6px;
    margin-top: 14px;
    font-size: 10px;
    color: #718096;
  }

  .legend-colors {
    display: flex;
    gap: 2px;

    div {
      width: 16px;
      height: 10px;
      border-radius: 2px;
    }
  }

  /* Persona */
  .persona-card {
    background: #FFFFFF;
    border-radius: 14px;
    padding: 16px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  }

  .persona-header {
    display: flex;
    align-items: center;
    gap: 14px;
    margin-bottom: 14px;
  }

  .persona-icon-large {
    width: 60px;
    height: 60px;
    background: linear-gradient(135deg, #6C63FF 0%, #9F7AEA 100%);
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 28px;
    color: #FFFFFF;
  }

  .persona-title {
    h3 {
      font-size: 20px;
      font-weight: 700;
      margin-bottom: 6px;
      color: #2D3748;
    }
  }

  .confidence-badge {
    background: #F0F4FF;
    padding: 3px 10px;
    border-radius: 12px;
    font-size: 11px;
    color: #6C63FF;
    display: inline-block;
  }

  .persona-description {
    color: #718096;
    font-size: 13px;
    line-height: 1.5;
    margin-bottom: 16px;
  }

  .persona-stats {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 12px;
    margin-bottom: 20px;
  }

  .stat {
    background: #F0F4FF;
    border-radius: 10px;
    padding: 14px;
    text-align: center;

    i {
      font-size: 20px;
      color: #6C63FF;
      margin-bottom: 6px;
      display: block;
    }

    .stat-value {
      font-size: 20px;
      font-weight: 700;
      display: block;
      margin-bottom: 3px;
      color: #2D3748;
    }

    .stat-label {
      font-size: 11px;
      color: #718096;
    }
  }

  .trait-section {
    margin-bottom: 16px;

    h4 {
      font-size: 12px;
      font-weight: 600;
      margin-bottom: 10px;
      display: flex;
      align-items: center;
      gap: 6px;
      color: #4A5568;

      i {
        font-size: 14px;
      }
    }
  }

  .trait-list {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
  }

  .trait {
    padding: 6px 12px;
    border-radius: 14px;
    font-size: 12px;
    font-weight: 500;
  }

  .trait-strength {
    background: rgba(72, 187, 120, 0.15);
    color: #276749;
  }

  .trait-weakness {
    background: rgba(237, 137, 54, 0.15);
    color: #C05621;
  }

  .tips-section {
    h4 {
      font-size: 12px;
      font-weight: 600;
      margin-bottom: 10px;
      display: flex;
      align-items: center;
      gap: 6px;
      color: #D69E2E;

      i {
        font-size: 14px;
      }
    }
  }

  .tips-list {
    list-style: none;
    padding: 0;
    margin: 0;

    li {
      background: #FAFBFF;
      border-radius: 10px;
      padding: 12px;
      margin-bottom: 6px;
      font-size: 12px;
      line-height: 1.4;
      color: #4A5568;
      position: relative;
      padding-left: 24px;

      &::before {
        content: '';
        position: absolute;
        left: 12px;
        top: 50%;
        transform: translateY(-50%);
        width: 5px;
        height: 5px;
        background: #6C63FF;
        border-radius: 50%;
      }
    }
  }

  /* No Data */
  .no-data {
    text-align: center;
    padding: 40px 20px;
    color: #718096;

    i {
      font-size: 48px;
      margin-bottom: 14px;
      display: block;
      color: #CBD5E0;
    }

    h3 {
      font-size: 16px;
      margin-bottom: 6px;
      color: #4A5568;
    }

    p {
      font-size: 13px;
    }
  }

  /* Mobile */
  @media (max-width: 480px) {
    padding: 16px;

    .trend-cards {
      gap: 8px;
    }

    .trend-card {
      padding: 10px 6px;
    }

    .trend-value {
      font-size: 13px;
    }

    .persona-header {
      flex-direction: column;
      text-align: center;
    }

    .persona-stats {
      grid-template-columns: repeat(2, 1fr);
    }
  }
`;

export default AnalysisPage;
