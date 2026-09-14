import { useState, useEffect } from 'react'
import { 
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, 
  ResponsiveContainer, PieChart, Pie, Cell 
} from 'recharts'
import { useGoalStrategist, GoalConfig } from '../../hooks/useGoalStrategist'
import RoadmapRenderer from './RoadmapRenderer'
import './GoalPlanner.css'

export default function GoalPlanner() {
  const { goal, roadmap, simulationResults, isLoading, calculate } = useGoalStrategist()

  // --- Local Form State ---
  const [isEditing, setIsEditing] = useState(true)
  const [hasAutoCalculated, setHasAutoCalculated] = useState(false)
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

  const handleCalculate = async (e: React.FormEvent) => {
    e.preventDefault()
    await calculate(formData)
    setIsEditing(false)
  }

  // --- Data Preparation for Recharts ---
  // The fan chart data should be formatted as { year, p05, p50, p95 }
  const fanChartData = simulationResults ? simulationResults.years_axis.map((y: number, i: number) => ({
    year: y,
    p05: Math.round(simulationResults.p05_path[i]),
    p25: Math.round(simulationResults.p25_path[i]),
    p50: Math.round(simulationResults.median_path[i]),
    p75: Math.round(simulationResults.p75_path[i]),
    p95: Math.round(simulationResults.p95_path[i]),
  })) : []

  // Gauge data (Success probability)
  const confidencePercent = simulationResults?.confidence_score ?? 0
  const gaugeData = [
    { value: confidencePercent, color: 'var(--accent-cyan)' },
    { value: 100 - confidencePercent, color: 'var(--glass-border)' }
  ]

  return (
    <div className="tab-panel">
      <div className="insights-header-section" style={{ marginBottom: '2.5rem' }}>
        <div className="header-top-row">
          <h1>Goal Strategist</h1>
          <div className="header-badge">📐 High-Fidelity Simulation</div>
        </div>
        <p className="insights-subtitle">
          Define your Financial North Star across any country with IRS-grounded AI intelligence.
        </p>
      </div>

      <div className="goal-workspace">
        {/* ── Left Column: The Strategic Configurator ────────────────── */}
        <div className="goal-config-column">
          {(!isEditing && goal) ? (
            <div className="glass-card config-summary">
              <h3 style={{ marginBottom: '1.2rem', color: 'var(--text-bright)' }}>Current Configuration</h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.8rem', fontSize: '0.9rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: 'var(--text-dim)' }}>Name</span>
                  <strong style={{ color: 'var(--accent-cyan)' }}>{formData.goal_name}</strong>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: 'var(--text-dim)' }}>Target Amount</span>
                  <strong>${formData.target_amount.toLocaleString()}</strong>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: 'var(--text-dim)' }}>Target Year</span>
                  <strong>{formData.target_year}</strong>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: 'var(--text-dim)' }}>Monthly Savings</span>
                  <strong>${formData.monthly_savings.toLocaleString()}</strong>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: 'var(--text-dim)' }}>Regulatory Ruleset</span>
                  <strong>{formData.country} Tax Law</strong>
                </div>
              </div>
              <button 
                className="calculate-btn" 
                style={{ 
                  marginTop: '1.5rem', 
                  background: 'rgba(255,255,255,0.05)', 
                  border: '1px solid var(--glass-border)',
                  color: 'var(--text-bright)'
                }} 
                onClick={() => setIsEditing(true)}
              >
                ✏️ Edit Configuration
              </button>
            </div>
          ) : (
            <div className="glass-card">
              <h3>Goal Configuration</h3>
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
                    min="2025" 
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
                    <option value="IN">India (80C / NPS Rules)</option>
                    <option value="UK">United Kingdom (ISA Rules)</option>
                    <option value="SG">Singapore (CPF Rules)</option>
                  </select>
                </div>

                <button className="calculate-btn" type="submit" disabled={isLoading}>
                  {isLoading ? '🧠 Calculating 10,000 Scenarios...' : '⚡ Generate Roadmap'}
                </button>
              </form>
            </div>
          )}

          <div className="glass-card" style={{ padding: '1.25rem' }}>
            <h4 style={{ color: 'var(--text-dim)', fontSize: '0.85rem', marginBottom: '0.5rem' }}>TIP</h4>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
              Changing your country will shift the simulation to use local tax brackets 
              and contribution limits via the Strategic RAG engine.
            </p>
          </div>
        </div>

        {/* ── Right Column: Strategic Workspace ──────────────────────── */}
        <div className="goal-analytics-column">
          {isLoading && !simulationResults ? (
            <div className="glass-card roadmap-empty">
              <div className="roadmap-empty-icon" style={{ animation: "pulse 1.5s infinite" }}>🧠</div>
              <h2>Generating your strategic roadmap...</h2>
              <p>Simulating 10,000 Monte Carlo paths and validating against {formData.country} tax rules.</p>
            </div>
          ) : simulationResults ? (
            <>
              <div className="grid-12" style={{ gap: '1.5rem', width: '100%' }}>
                {/* Confidence Gauge */}
                <div className="glass-card" style={{ gridColumn: 'span 4' }}>
                  <h3>Confidence Score</h3>
                  <div className="gauge-container">
                    <ResponsiveContainer width={200} height={200}>
                      <PieChart>
                        <Pie
                          data={gaugeData}
                          innerRadius={65}
                          outerRadius={85}
                          startAngle={180}
                          endAngle={0}
                          dataKey="value"
                        >
                          {gaugeData.map((entry, index) => (
                            <Cell key={index} fill={entry.color} />
                          ))}
                        </Pie>
                      </PieChart>
                    </ResponsiveContainer>
                    <div className="gauge-value" style={{ position: 'absolute', top: '75px' }}>
                      {confidencePercent}%
                    </div>
                    <p className="gauge-label">Probability of Success</p>
                  </div>
                </div>

                {/* Probability Distribution Fan Chart */}
                <div className="glass-card" style={{ gridColumn: 'span 8' }}>
                  <h3>Success Probability Projection</h3>
                  <div className="chart-container">
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
                          contentStyle={{ background: '#0a0a0a', border: '1px solid var(--glass-border)', borderRadius: '8px' }}
                          formatter={(v: any) => [`$${Number(v).toLocaleString()}`, '']}
                        />
                        {/* 5th to 95th Percentile Fan */}
                        <Area type="monotone" dataKey="p95" stroke="none" fill="var(--accent-cyan)" fillOpacity={0.05} />
                        <Area type="monotone" dataKey="p75" stroke="none" fill="var(--accent-cyan)" fillOpacity={0.1} />
                        <Area type="monotone" dataKey="p50" stroke="var(--accent-cyan)" fill="url(#colorMedian)" strokeWidth={2} />
                        <Area type="monotone" dataKey="p25" stroke="none" fill="var(--accent-cyan)" fillOpacity={0.1} />
                        <Area type="monotone" dataKey="p05" stroke="none" fill="var(--accent-cyan)" fillOpacity={0.05} />
                      </AreaChart>
                    </ResponsiveContainer>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'center', gap: '1rem', marginTop: '0.5rem' }}>
                    <div style={{ fontSize: '0.7rem', color: 'var(--text-dim)' }}><span style={{ color: 'var(--accent-cyan)' }}>●</span> Median Path</div>
                    <div style={{ fontSize: '0.7rem', color: 'var(--text-dim)' }}><span style={{ opacity: 0.2 }}>●</span> 90% Confidence Interval</div>
                  </div>
                </div>
              </div>

              {/* The AI Roadmap Report */}
              <div className="glass-card roadmap-report">
                <RoadmapRenderer markdown={roadmap} />
              </div>
            </>
          ) : (
            <div className="glass-card roadmap-empty">
              <div className="roadmap-empty-icon">📈</div>
              <h2>Ready to build your roadmap?</h2>
              <p>Configure your targets on the left and click **Generate Roadmap** 
              to run the real-time simulation engine.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
