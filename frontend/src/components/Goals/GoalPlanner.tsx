import './GoalPlanner.css'

export default function GoalPlanner() {
  return (
    <div className="tab-panel">
      <h1 style={{ fontSize: '2rem', marginBottom: '2rem' }}>Goal Strategist</h1>
      <div className="grid-12">
        {/* Confidence gauge */}
        <div className="glass-card" style={{ gridColumn: 'span 4', textAlign: 'center' }}>
          <h3 style={{ marginBottom: '1.5rem' }}>Success Confidence</h3>
          <div className="goal-gauge">
            <div className="gauge-fill" />
          </div>
          <div className="gauge-value">82%</div>
          <p style={{ color: 'var(--text-dim)', marginBottom: '1rem' }}>Probability of $1M by 2030</p>
          <p className="coming-soon-note">🎯 Monte Carlo powered by Goal Strategist Agent — Phase 3</p>
        </div>

        {/* Fan chart placeholder */}
        <div className="glass-card" style={{ gridColumn: 'span 8' }}>
          <h3>Monte Carlo Simulation</h3>
          <div className="fan-chart-placeholder">
            <p>📈 Projection Fan Chart</p>
            <p className="coming-soon-note">10,000-scenario simulation — Phase 3</p>
          </div>
        </div>

        {/* What-if sliders */}
        <div className="glass-card" style={{ gridColumn: 'span 12' }}>
          <h3 style={{ marginBottom: '1.5rem' }}>What-If Sliders</h3>
          <div className="sliders-row">
            <div className="slider-group">
              <label className="slider-label">MONTHLY CONTRIBUTION ($)</label>
              <input type="range" className="slider" defaultValue={500} min={100} max={5000} />
              <span className="slider-value">$500</span>
            </div>
            <div className="slider-group">
              <label className="slider-label">RISK TOLERANCE</label>
              <input type="range" className="slider" defaultValue={60} min={0} max={100} />
              <span className="slider-value">Moderate</span>
            </div>
            <div className="slider-group">
              <label className="slider-label">TARGET YEAR</label>
              <input type="range" className="slider" defaultValue={2030} min={2026} max={2045} />
              <span className="slider-value">2030</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
