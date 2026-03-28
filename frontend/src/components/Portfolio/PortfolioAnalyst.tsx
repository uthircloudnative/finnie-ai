import './PortfolioAnalyst.css'

const RATIOS = [
  { label: 'Sharpe Ratio',     value: '1.84',   color: 'var(--accent-emerald)' },
  { label: 'Alpha (vs S&P)',   value: '+2.1%',  color: 'var(--accent-emerald)' },
  { label: 'Beta (Volatility)', value: '1.45',  color: 'var(--text-main)' },
  { label: 'Max Drawdown',     value: '-18.4%', color: 'var(--accent-orange)' },
]

export default function PortfolioAnalyst() {
  return (
    <div className="tab-panel">
      <h1 style={{ fontSize: '2rem', marginBottom: '2rem' }}>Portfolio Analyst</h1>
      <div className="grid-12">
        {/* Diversification Score */}
        <div className="glass-card" style={{ gridColumn: 'span 7', textAlign: 'center' }}>
          <h3>Diversification Score</h3>
          <div className="divers-score">42 / 100</div>
          <p style={{ color: 'var(--text-dim)' }}>Critical Sector Concentration Detected</p>
          <p className="coming-soon-note">📊 Live analysis coming in Phase 3</p>
        </div>

        {/* Key Ratios */}
        <div className="glass-card" style={{ gridColumn: 'span 5' }}>
          <h3 style={{ marginBottom: '1.5rem' }}>Key Ratios</h3>
          {RATIOS.map((r) => (
            <div key={r.label} className="ratio-row">
              <span style={{ color: 'var(--text-dim)' }}>{r.label}</span>
              <span style={{ color: r.color, fontWeight: 600 }}>{r.value}</span>
            </div>
          ))}
          <p className="coming-soon-note">🤖 Real data via Portfolio Agent — Phase 3</p>
        </div>
      </div>
    </div>
  )
}
