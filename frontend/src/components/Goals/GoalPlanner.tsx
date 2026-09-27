import React, { useState, useEffect } from 'react'
import { 
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, 
  ResponsiveContainer 
} from 'recharts'
import { useGoalStrategist, GoalConfig } from '../../hooks/useGoalStrategist'
import RoadmapRenderer from './RoadmapRenderer'
import ThoughtStream from './ThoughtStream'
import GoalChatRefinement from './GoalChatRefinement'
import StrategyLockInModal from './StrategyLockInModal'
import './GoalPlanner.css'

export default function GoalPlanner() {
  const { 
    goal, 
    roadmap, 
    simulationResults, 
    isLoading, 
    isStreaming, 
    thoughts, 
    chatHistory, 
    confidenceScore, 
    status, 
    calculate, 
    askRefinement, 
    lockIn 
  } = useGoalStrategist()

  // --- Local Form State ---
  const [isEditing, setIsEditing] = useState(true)
  const [activeTab, setActiveTab] = useState<'roadmap' | 'chart'>('roadmap')
  const [hasAutoCalculated, setHasAutoCalculated] = useState(false)
  const [isLockInModalOpen, setIsLockInModalOpen] = useState(false)
  const [formData, setFormData] = useState<GoalConfig>({
    goal_name: 'Retirement',
    target_amount: 1000000,
    target_year: 2040,
    monthly_savings: 1000,
    country: 'USA'
  })

  // Sync initial goal from DB and trigger auto-calculate exactly once
  useEffect(() => {
    if (goal && !hasAutoCalculated) {
      setFormData(goal)
      setIsEditing(false)
      calculate(goal)
      setHasAutoCalculated(true)
    }
  }, [goal, hasAutoCalculated, calculate])

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
    setIsEditing(false)
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
    <div className="tab-panel">
      <div className="insights-header-section" style={{ marginBottom: '1.5rem' }}>
        <div className="header-top-row">
          <h1>Goal Strategist</h1>
          <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
            {status === 'LOCKED' ? (
              <div className="header-badge" style={{ background: 'rgba(16, 185, 129, 0.15)', borderColor: 'var(--accent-emerald)', color: 'var(--accent-emerald)' }}>
                🔒 Strategy Locked
              </div>
            ) : (
              <div className="header-badge">
                📐 Autonomous Financial GPS
              </div>
            )}
          </div>
        </div>
        <p className="insights-subtitle">
          Define your Financial North Star across any country with IRS-grounded AI intelligence and in-session memory.
        </p>
      </div>

      {/* ── Active Viewport Layout ───────────────────────────────────────── */}
      {simulationResults && !isEditing ? (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          {/* Live Agent Thought Stream */}
          <ThoughtStream thoughts={thoughts} isStreaming={isStreaming} />

          {/* Executive Telemetry & Action Bar */}
          <div className="goal-executive-bar">
            <div className="executive-meta-left">
              {statusBadge}
              <span className="roadmap-confidence-badge">
                {confidencePercent.toFixed(1)}% Success Probability
              </span>
              <div style={{ display: 'flex', gap: '0.75rem', fontSize: '0.85rem', color: '#cbd5e1' }}>
                <span><strong>Goal:</strong> {formData.goal_name}</span>
                <span>•</span>
                <span><strong>Target:</strong> ${formData.target_amount.toLocaleString()} ({formData.target_year})</span>
                <span>•</span>
                <span><strong>Savings:</strong> ${formData.monthly_savings.toLocaleString()}/mo</span>
                <span>•</span>
                <span><strong>Rules:</strong> {formData.country}</span>
              </div>
            </div>

            <div className="executive-actions-right">
              {/* Workspace Tab Buttons */}
              <button
                type="button"
                className={`workspace-tab-btn ${activeTab === 'roadmap' ? 'active' : ''}`}
                onClick={() => setActiveTab('roadmap')}
              >
                📜 Strategic Roadmap
              </button>
              <button
                type="button"
                className={`workspace-tab-btn ${activeTab === 'chart' ? 'active' : ''}`}
                onClick={() => setActiveTab('chart')}
              >
                📈 Simulation Chart
              </button>

              {status !== 'LOCKED' && (
                <button
                  type="button"
                  className="calculate-btn"
                  onClick={() => setIsLockInModalOpen(true)}
                  style={{
                    margin: 0,
                    padding: '0.5rem 1.1rem',
                    fontSize: '0.85rem',
                    background: 'linear-gradient(135deg, rgba(0,240,255,0.2), rgba(16,185,129,0.25))',
                    border: '1px solid var(--accent-emerald)',
                    color: 'var(--accent-emerald)'
                  }}
                >
                  Lock In & Save Goal 🔒
                </button>
              )}

              <button
                type="button"
                className="workspace-tab-btn"
                onClick={() => setIsEditing(true)}
              >
                ✏️ Edit Inputs
              </button>
            </div>
          </div>

          {/* Draft In-Session State Guidance */}
          {status !== 'LOCKED' && (
            <div className="draft-status-banner">
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <span>ℹ️</span>
                <span>
                  <strong>Draft Strategy:</strong> This simulation is held in active session memory. To permanently commit this roadmap to your financial dashboard, click <strong>Lock In & Save Goal</strong>.
                </span>
              </div>
              <button
                type="button"
                onClick={() => setIsLockInModalOpen(true)}
                style={{
                  background: 'none',
                  border: 'none',
                  color: 'var(--accent-cyan)',
                  textDecoration: 'underline',
                  cursor: 'pointer',
                  fontSize: '0.80rem',
                  fontWeight: 600,
                  whiteSpace: 'nowrap'
                }}
              >
                Lock In Now →
              </button>
            </div>
          )}

          {/* Side-by-Side Dual-Pane Workspace */}
          <div className="roadmap-workspace-grid">
            {/* Left Pane: Roadmap or Simulation Chart */}
            <div className="workspace-left-pane">
              <div className="glass-card roadmap-report" style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.85rem', borderBottom: '1px solid var(--glass-border)', paddingBottom: '0.6rem' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <span>{activeTab === 'roadmap' ? '📜' : '📈'}</span>
                    <h3 style={{ margin: 0, color: 'var(--text-bright)', fontSize: '1.05rem' }}>
                      {activeTab === 'roadmap' ? 'Strategic Roadmap Synthesis' : '10,000 Monte Carlo Simulation Paths'}
                    </h3>
                  </div>
                  <span style={{ fontSize: '0.75rem', color: '#94a3b8' }}>
                    {activeTab === 'roadmap' ? 'Grounded in statutory rules' : '90% Confidence Interval'}
                  </span>
                </div>

                <div className="scrollable-pane-content">
                  {activeTab === 'roadmap' ? (
                    <RoadmapRenderer markdown={roadmap} />
                  ) : (
                    <div>
                      <div className="chart-container" style={{ height: '340px' }}>
                        <ResponsiveContainer width="100%" height="100%">
                          <AreaChart data={fanChartData}>
                            <defs>
                              <linearGradient id="colorMedian" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="5%" stopColor="var(--accent-cyan)" stopOpacity={0.3}/>
                                <stop offset="95%" stopColor="var(--accent-cyan)" stopOpacity={0}/>
                              </linearGradient>
                            </defs>
                            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                            <XAxis 
                              dataKey="year" 
                              stroke="var(--text-dim)" 
                              fontSize={10} 
                              label={{ value: 'Years', position: 'bottom', fill: 'var(--text-dim)', fontSize: 10 }}
                            />
                            <YAxis 
                              stroke="var(--text-dim)" 
                              fontSize={10} 
                              tickFormatter={(v) => `$${(v/1000000).toFixed(1)}M`}
                            />
                            <Tooltip 
                              contentStyle={{ background: '#0a0a0a', border: '1px solid var(--glass-border)', borderRadius: '8px', color: '#ffffff' }}
                              formatter={(v: any) => [`$${Number(v).toLocaleString()}`, '']}
                            />
                            <Area type="monotone" dataKey="p95" stroke="none" fill="var(--accent-cyan)" fillOpacity={0.05} />
                            <Area type="monotone" dataKey="p75" stroke="none" fill="var(--accent-cyan)" fillOpacity={0.1} />
                            <Area type="monotone" dataKey="p50" stroke="var(--accent-cyan)" fill="url(#colorMedian)" strokeWidth={2} />
                            <Area type="monotone" dataKey="p25" stroke="none" fill="var(--accent-cyan)" fillOpacity={0.1} />
                            <Area type="monotone" dataKey="p05" stroke="none" fill="var(--accent-cyan)" fillOpacity={0.05} />
                          </AreaChart>
                        </ResponsiveContainer>
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'center', gap: '1.5rem', marginTop: '0.75rem' }}>
                        <div style={{ fontSize: '0.75rem', color: '#cbd5e1' }}>
                          <span style={{ color: 'var(--accent-cyan)', fontWeight: 700 }}>●</span> Median Path
                        </div>
                        <div style={{ fontSize: '0.75rem', color: '#94a3b8' }}>
                          <span style={{ opacity: 0.3 }}>●</span> 90% Confidence Interval
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Right Pane: Autonomous Refinement Chat */}
            <div className="workspace-right-pane">
              <GoalChatRefinement
                chatHistory={chatHistory}
                onSendMessage={askRefinement}
                isLoading={isLoading}
                country={formData.country}
              />
            </div>
          </div>
        </div>
      ) : (
        /* ── Standard 2-Column Configuration Layout ─────────────────────── */
        <div className="goal-workspace">
          {/* Left Column: Strategic Configurator */}
          <div className="goal-config-column">
            <div className="glass-card">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                <h3 style={{ margin: 0 }}>Goal Configuration</h3>
                {simulationResults && (
                  <button
                    type="button"
                    onClick={() => setIsEditing(false)}
                    style={{
                      background: 'none',
                      border: 'none',
                      color: 'var(--accent-cyan)',
                      fontSize: '0.8rem',
                      cursor: 'pointer'
                    }}
                  >
                    View Active Results →
                  </button>
                )}
              </div>

              <form className="config-form" onSubmit={handleCalculate}>
                <div className="input-block">
                  <label>Goal Name</label>
                  <input 
                    className="goal-input" 
                    name="goal_name"
                    value={formData.goal_name} 
                    onChange={handleInputChange} 
                    placeholder="e.g. Dream House" 
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
                  <label>Target Year</label>
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

                {/* Quick-Start Preset Buttons for Empty or First-Time Users */}
                <div className="quick-preset-container">
                  <span style={{ fontSize: '0.70rem', color: '#94a3b8', fontWeight: 700, letterSpacing: '0.08em', textTransform: 'uppercase' }}>
                    Quick-Start Templates
                  </span>
                  <div className="preset-chips-row">
                    <button
                      type="button"
                      className="goal-preset-btn"
                      onClick={() => handleQuickPreset({ name: 'Retirement Fund', amount: 1000000, year: 2040, savings: 1000, country: 'USA' })}
                    >
                      🏖️ Retirement ($1M)
                    </button>
                    <button
                      type="button"
                      className="goal-preset-btn"
                      onClick={() => handleQuickPreset({ name: 'First Home', amount: 250000, year: 2030, savings: 1500, country: 'USA' })}
                    >
                      🏡 First Home ($250k)
                    </button>
                    <button
                      type="button"
                      className="goal-preset-btn"
                      onClick={() => handleQuickPreset({ name: 'Wealth Accumulation', amount: 500000, year: 2035, savings: 800, country: 'USA' })}
                    >
                      🚀 Wealth ($500k)
                    </button>
                  </div>
                </div>

                <button className="calculate-btn" type="submit" disabled={isLoading}>
                  {isLoading ? '🧠 Calculating 10,000 Scenarios...' : '⚡ Generate Roadmap'}
                </button>
              </form>
            </div>

            <div className="glass-card" style={{ padding: '1.25rem' }}>
              <h4 style={{ color: 'var(--text-dim)', fontSize: '0.85rem', marginBottom: '0.5rem' }}>TIP</h4>
              <p style={{ fontSize: '0.85rem', color: '#cbd5e1' }}>
                Changing your country shifts the simulation to use local tax brackets 
                and statutory contribution ceilings via the Strategic RAG engine.
              </p>
            </div>
          </div>

          {/* Right Column: Strategic Workspace Placeholder */}
          <div className="goal-analytics-column">
            <ThoughtStream thoughts={thoughts} isStreaming={isStreaming} />

            {isLoading ? (
              <div className="glass-card roadmap-empty">
                <div className="roadmap-empty-icon" style={{ animation: 'pulse 1.5s infinite' }}>🧠</div>
                <h2 style={{ color: '#ffffff' }}>Generating your strategic roadmap...</h2>
                <p style={{ color: '#cbd5e1' }}>Simulating 10,000 Monte Carlo paths and validating against {formData.country} tax rules.</p>
              </div>
            ) : (
              <div className="glass-card roadmap-empty">
                <div className="roadmap-empty-icon">📈</div>
                <h2 style={{ color: '#ffffff' }}>Ready to build your roadmap?</h2>
                <p style={{ color: '#cbd5e1' }}>Configure your targets on the left or select a Quick-Start template, then click <strong>Generate Roadmap</strong> to run the real-time simulation engine.</p>
              </div>
            )}
          </div>
        </div>
      )}

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
