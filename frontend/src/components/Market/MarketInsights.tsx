import './MarketInsights.css'

const ASSETS = [
  { symbol: 'NVDA', change: '+4.2%', positive: true,  cta: 'Why is it moving?' },
  { symbol: 'BTC',  change: '+0.5%', positive: true,  cta: 'Explain Trend' },
  { symbol: 'TSLA', change: '-3.1%', positive: false, cta: 'Analyze Drop' },
]

export default function MarketInsights() {
  return (
    <div className="tab-panel">
      <h1 style={{ fontSize: '2rem', marginBottom: '2rem' }}>Market Insights</h1>
      <div className="glass-card">
        <div className="insights-header">
          <h3>Trending Assets</h3>
          <span className="badge">REAL-TIME — Phase 3</span>
        </div>
        <div className="asset-grid">
          {ASSETS.map((a) => (
            <div key={a.symbol} className="glass-card asset-card">
              <h4 className="asset-symbol">{a.symbol}</h4>
              <p className="asset-change" style={{ color: a.positive ? 'var(--accent-emerald)' : 'var(--accent-orange)' }}>
                {a.change} Today
              </p>
              <button
                className="btn-cyan asset-btn"
                onClick={() => alert('Market Insights Agent coming in Phase 3!')}
              >
                {a.cta}
              </button>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
