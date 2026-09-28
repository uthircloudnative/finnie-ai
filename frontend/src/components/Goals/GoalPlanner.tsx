import React, { useState, useEffect } from 'react'
import { 
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, 
  ResponsiveContainer 
} from 'recharts'
import { useGoalStrategist, GoalConfig } from '../../hooks/useGoalStrategist'
import RoadmapRenderer from './RoadmapRenderer'
import GoalChatRefinement from './GoalChatRefinement'
import StrategyLockInModal from './StrategyLockInModal'
import './GoalPlanner.css'

export default function GoalPlanner() {
  const { 
    goal, 
    roadmap, 
    simulationResults, 
    isLoading, 
    chatHistory, 
    confidenceScore, 
    status, 
    calculate, 
    askRefinement, 
    clearChat,
    lockIn 
  } = useGoalStrategist()

  // --- Local State (Session Persisted) ---
  const [isCopilotOpen, setIsCopilotOpen] = useState<boolean>(() => {
    try {
      return sessionStorage.getItem('finnie_copilot_open') === 'true'
    } catch (_) {
      return false
    }
  })

  useEffect(() => {
    try {
      sessionStorage.setItem('finnie_copilot_open', String(isCopilotOpen))
    } catch (_) {}
  }, [isCopilotOpen])
  const [hasAutoCalculated, setHasAutoCalculated] = useState(false)
  const [isLockInModalOpen, setIsLockInModalOpen] = useState(false)
  const [formData, setFormData] = useState<GoalConfig>(() => {
    if (goal) return goal
    try {
      const raw = sessionStorage.getItem('finnie_goal_session')
      if (raw) {
        const parsed = JSON.parse(raw)
        if (parsed.goal) return parsed.goal
      }
    } catch (_) {}
    return {
      goal_name: 'Retirement Capital',
      target_amount: 1000000,
      target_year: 2040,
      monthly_savings: 1000,
      country: 'USA'
    }
  })

  // Sync initial goal from DB or session and trigger auto-calculate only if no roadmap exists
  useEffect(() => {
    if (goal && !hasAutoCalculated && !roadmap) {
      setFormData(goal)
      calculate(goal)
      setHasAutoCalculated(true)
    } else if (goal) {
      setFormData(goal)
    }
  }, [goal, hasAutoCalculated, roadmap, calculate])

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: name === 'target_amount' || name === 'target_year' || name === 'monthly_savings'
        ? Number(value)
        : value
    }))
  }

  const handleQuickPreset = (preset: { name: string; amount: number; year: number; savings: number; country: string }) => {
    setFormData({
      goal_name: preset.name,
      target_amount: preset.amount,
      target_year: preset.year,
      monthly_savings: preset.savings,
      country: preset.country
    })
  }

  const handleCalculate = async (e: React.FormEvent) => {
    e.preventDefault()
    await calculate(formData)
  }

  const handleLockInConfirm = async () => {
    const success = await lockIn()
    if (success) {
      setIsLockInModalOpen(false)
    }
  }

  // --- Data Preparation for Recharts ---
  const fanChartData = simulationResults ? simulationResults.years_axis.map((y: number, i: number) => ({
    year: y,
    p05: Math.round(simulationResults.p05_path[i]),
    p25: Math.round(simulationResults.p25_path[i]),
    p50: Math.round(simulationResults.median_path[i]),
    p75: Math.round(simulationResults.p75_path[i]),
    p95: Math.round(simulationResults.p95_path[i]),
  })) : []

  const confidencePercent = simulationResults?.confidence_score ?? confidenceScore ?? 0

  const statusBadge = confidencePercent >= 70 ? (
    <span className="roadmap-status-badge status-on-track">● ON TRACK</span>
  ) : confidencePercent >= 40 ? (
    <span className="roadmap-status-badge status-caution">▲ CAUTION</span>
  ) : (
    <span className="roadmap-status-badge status-at-risk">■ AT RISK</span>
  )

  return (
    <div className="tab-panel goal-planner-root">
      {/* ── 3-BAR EXPANSIVE WORKSPACE ── */}
      <div className="goal-workspace-3col">

        {/* ── COLUMN 1: GOAL TARGETS (WITH CO-LOCATED ACTIONS) ── */}
        <section className="glass-card column-targets">
          <div className="targets-card-header">
            <h3 className="targets-title">
              {/* Precision Crosshair Target Icon */}
              <svg className="fin-icon-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="12" cy="12" r="10" />
                <line x1="22" y1="12" x2="18" y2="12" />
                <line x1="6" y1="12" x2="2" y2="12" />
                <line x1="12" y1="6" x2="12" y2="2" />
                <line x1="12" y1="22" x2="12" y2="18" />
              </svg>
              Goal Targets
            </h3>
            <span className="targets-badge-pill">CONFIG</span>
          </div>

          <form className="targets-form-body" onSubmit={handleCalculate}>
            <div className="input-block">
              <label>Goal Title</label>
              <input 
                className="goal-input" 
                name="goal_name"
                value={formData.goal_name} 
                onChange={handleInputChange} 
                placeholder="e.g. Retirement Capital" 
              />
            </div>

            <div className="input-block">
              <label>Target Amount ($)</label>
              <input 
                className="goal-input" 
                name="target_amount"
                type="number" 
                step="10000"
                value={formData.target_amount} 
                onChange={handleInputChange} 
              />
            </div>

            <div className="input-block">
              <label>Target Horizon (Year)</label>
              <input 
                className="goal-input" 
                name="target_year"
                type="number" 
                min="2026" 
                max="2070"
                value={formData.target_year} 
                onChange={handleInputChange} 
              />
            </div>

            <div className="input-block">
              <label>Monthly Savings ($)</label>
              <input 
                className="goal-input" 
                name="monthly_savings"
                type="number" 
                step="100"
                value={formData.monthly_savings} 
                onChange={handleInputChange} 
              />
            </div>

            <div className="input-block">
              <label>Country of Residence</label>
              <select 
                className="goal-input" 
                name="country"
                value={formData.country} 
                onChange={handleInputChange} 
              >
                <option value="USA">United States (IRS Rules)</option>
                <option value="INDIA">India (80C / NPS Rules)</option>
                <option value="UK">United Kingdom (ISA Rules)</option>
                <option value="CANADA">Canada (RRSP / TFSA Rules)</option>
                <option value="GERMANY">Germany (Rürup / Sparer Rules)</option>
              </select>
            </div>

            {/* Institutional Benchmark Profiles */}
            <div className="benchmark-presets-section">
              <label>Benchmark Profiles</label>
              <div className="benchmark-pills-stack">
                <button
                  type="button"
                  className="benchmark-pill"
                  onClick={() => handleQuickPreset({ name: 'Retirement Capital', amount: 1000000, year: 2040, savings: 1000, country: 'USA' })}
                >
                  <span className="benchmark-name">Retirement Capital</span>
                  <span className="benchmark-spec">$1.0M · 2040</span>
                </button>
                <button
                  type="button"
                  className="benchmark-pill"
                  onClick={() => handleQuickPreset({ name: 'Real Estate Equity', amount: 250000, year: 2030, savings: 1500, country: 'USA' })}
                >
                  <span className="benchmark-name">Real Estate Equity</span>
                  <span className="benchmark-spec">$250k · 2030</span>
                </button>
                <button
                  type="button"
                  className="benchmark-pill"
                  onClick={() => handleQuickPreset({ name: 'Growth Portfolio', amount: 500000, year: 2035, savings: 800, country: 'USA' })}
                >
                  <span className="benchmark-name">Growth Portfolio</span>
                  <span className="benchmark-spec">$500k · 2035</span>
                </button>
              </div>
            </div>

            {/* ── CO-LOCATED ACTIONS RIGHT HERE INSIDE GOAL TARGETS ── */}
            <div className="targets-actions-cluster">
              {/* Primary Action 1: Calculate / Recalculate */}
              <button className="calculate-btn btn-primary-recalc" type="submit" disabled={isLoading}>
                <svg className="fin-icon-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                  <polyline points="23 6 13.5 15.5 8.5 10.5 1 18" />
                  <polyline points="17 6 23 6 23 12" />
                </svg>
                <span>{isLoading ? 'Calculating 10,000 Scenarios...' : (simulationResults ? 'Recalculate Roadmap' : 'Generate Roadmap')}</span>
              </button>

              {/* Primary Action 2: Lock In & Save Goal */}
              <button 
                className="btn-lockin-target" 
                type="button" 
                onClick={() => setIsLockInModalOpen(true)}
                disabled={!simulationResults || status === 'LOCKED' || isLoading}
              >
                <svg className="fin-icon-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                  <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
                  <path d="M7 11V7a5 5 0 0 1 10 0v4" />
                </svg>
                <span>{status === 'LOCKED' ? '✓ Strategy Locked & Saved' : 'Lock In & Save Goal'}</span>
              </button>
            </div>
          </form>
        </section>

        {/* ── COLUMN 2: EXPANSIVE CENTER STAGE (FAN CHART + SYNTHESIS) ── */}
        <section className="column-center-stage">
          {simulationResults ? (
            <>
              {/* Top Tier: 10,000-Scenario Stochastic Fan Chart Card */}
              <div className="glass-card center-chart-card">
                <div className="telemetry-bar-header">
                  <div className="telemetry-left">
                    {statusBadge}
                    <span className="roadmap-confidence-badge">
                      {confidencePercent.toFixed(1)}% Success Probability
                    </span>
                    <span className="telemetry-target-summary">
                      Target: <strong>${formData.target_amount.toLocaleString()} by {formData.target_year}</strong> (${formData.monthly_savings.toLocaleString()}/mo)
                    </span>
                  </div>
                  <div className="chart-header-actions">
                    {!isCopilotOpen && (
                      <button 
                        type="button" 
                        className="ask-finnie-toggle"
                        onClick={() => setIsCopilotOpen(true)}
                      >
                        <span className="toggle-icon">✦</span>
                        Ask Finnie
                      </button>
                    )}
                  </div>
                </div>

                <div className="chart-legend-subrow">
                  <span className="legend-item"><strong style={{ color: 'var(--accent-cyan)' }}>●</strong> Median Path</span>
                  <span className="legend-item"><strong style={{ color: 'rgba(0,240,255,0.4)' }}>▨</strong> 90% Confidence Interval</span>
                </div>

                <div className="chart-canvas-wrapper">
                  <ResponsiveContainer width="100%" height={155}>
                    <AreaChart data={fanChartData} margin={{ top: 10, right: 25, left: 10, bottom: 0 }}>
                      <defs>
                        <linearGradient id="band90Grad" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#00f0ff" stopOpacity={0.16}/>
                          <stop offset="95%" stopColor="#00f0ff" stopOpacity={0.02}/>
                        </linearGradient>
                        <linearGradient id="band50Grad" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#00f0ff" stopOpacity={0.32}/>
                          <stop offset="95%" stopColor="#00f0ff" stopOpacity={0.08}/>
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                      <XAxis dataKey="year" stroke="#64748b" tick={{ fontSize: 10 }} />
                      <YAxis stroke="#64748b" tick={{ fontSize: 10 }} tickFormatter={(val: number) => `$${(val / 1000).toFixed(0)}k`} />
                      <Tooltip 
                        contentStyle={{ 
                          background: 'rgba(10, 15, 29, 0.95)', 
                          border: '1px solid rgba(0, 240, 255, 0.3)',
                          borderRadius: '8px',
                          fontSize: '11px'
                        }} 
                        formatter={(val: any) => [typeof val === 'number' ? `$${val.toLocaleString()}` : String(val), 'Portfolio Value']}
                      />
                      <Area type="monotone" dataKey="p95" stroke="rgba(0, 240, 255, 0.4)" strokeWidth={1} fill="url(#band90Grad)" />
                      <Area type="monotone" dataKey="p75" stroke="rgba(0, 240, 255, 0.7)" strokeWidth={1} fill="url(#band50Grad)" />
                      <Area type="monotone" dataKey="p50" stroke="#00f0ff" strokeWidth={2.5} fill="none" name="Median Path" />
                      <Area type="monotone" dataKey="p25" stroke="rgba(0, 240, 255, 0.7)" strokeWidth={1} fill="none" />
                      <Area type="monotone" dataKey="p05" stroke="rgba(0, 240, 255, 0.4)" strokeWidth={1} fill="none" />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              </div>

              {/* Lower Tier: Strategic Roadmap Synthesis Card */}
              <div className="glass-card center-synthesis-card">
                <div className="synthesis-card-header">
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
                    <svg className="fin-icon-svg" style={{ color: 'var(--accent-cyan)' }} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <line x1="8" y1="6" x2="21" y2="6" />
                      <line x1="8" y1="12" x2="21" y2="12" />
                      <line x1="8" y1="18" x2="21" y2="18" />
                      <line x1="3" y1="6" x2="3.01" y2="6" />
                      <line x1="3" y1="12" x2="3.01" y2="12" />
                      <line x1="3" y1="18" x2="3.01" y2="18" />
                    </svg>
                    <h3 style={{ margin: 0, fontSize: '0.95rem', fontWeight: 700 }}>Strategic Roadmap Synthesis</h3>
                  </div>
                  <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                    <span className="compliance-shield-pill">
                      <svg className="fin-icon-svg" style={{ width: '11px', height: '11px' }} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
                      </svg>
                      SEC/FINRA COMPLIANT
                    </span>
                    {status === 'LOCKED' && (
                      <span className="status-locked-pill">🔒 COMMITTED</span>
                    )}
                  </div>
                </div>

                <div className="synthesis-content-scroll">
                  <RoadmapRenderer markdown={roadmap} />
                </div>
              </div>
            </>
          ) : (
            <div className="glass-card roadmap-empty center-empty-card" style={{ position: 'relative' }}>
              {!isCopilotOpen && (
                <div style={{ position: 'absolute', top: '1rem', right: '1rem' }}>
                  <button 
                    type="button" 
                    className="ask-finnie-toggle"
                    onClick={() => setIsCopilotOpen(true)}
                  >
                    <span className="toggle-icon">✦</span>
                    Ask Finnie
                  </button>
                </div>
              )}
              <div className="fin-empty-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="var(--accent-cyan)" strokeWidth="1.5">
                  <circle cx="12" cy="12" r="10" />
                  <line x1="22" y1="12" x2="18" y2="12" />
                  <line x1="6" y1="12" x2="2" y2="12" />
                  <line x1="12" y1="6" x2="12" y2="2" />
                  <line x1="12" y1="22" x2="12" y2="18" />
                </svg>
              </div>
              <h2 style={{ color: '#ffffff', margin: '0.75rem 0 0.35rem 0', fontSize: '1.25rem' }}>Ready to build your roadmap?</h2>
              <p style={{ color: '#cbd5e1', maxWidth: '440px', fontSize: '0.85rem', lineHeight: 1.5 }}>
                Configure your targets on the left or select a Benchmark Profile, then click <strong>Generate Roadmap</strong> to run the real-time simulation engine.
              </p>
            </div>
          )}
        </section>

        {/* ── COLUMN 3: STRATEGY COPILOT DRAWER (ON DEMAND & HORIZONTALLY EXPANDABLE) ── */}
        {isCopilotOpen && (
          <GoalChatRefinement 
            chatHistory={chatHistory} 
            onSendMessage={(text) => askRefinement(text, formData)} 
            onClearHistory={clearChat}
            isLoading={isLoading} 
            country={formData.country}
            onClose={() => setIsCopilotOpen(false)}
          />
        )}
      </div>

      {/* Human-in-the-Loop Lock-in Modal */}
      <StrategyLockInModal
        isOpen={isLockInModalOpen}
        onClose={() => setIsLockInModalOpen(false)}
        onConfirm={handleLockInConfirm}
        goal={goal || formData}
        confidenceScore={confidencePercent}
        isLoading={isLoading}
      />
    </div>
  )
}
