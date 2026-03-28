import './Dashboard.css'

export default function Dashboard() {
  return (
    <div className="tab-panel">
      {/* Header */}
      <div className="dashboard-header">
        <div>
          <h1>Executive Overview</h1>
          <p className="subtitle">Here's your financial pulse.</p>
        </div>
        <div className="header-actions">
          <button className="btn-ghost">Export PDF</button>
          <button className="btn-cyan">Rebalance Now</button>
        </div>
      </div>

      {/* Main Grid */}
      <div className="grid-12">
        {/* Portfolio Value Card */}
        <div className="glass-card portfolio-card">
          <h3>Total Portfolio Value</h3>
          <div className="portfolio-value">
            $874,250
            <span className="gain"> +3.45%</span>
          </div>
          {/* Bar chart mockup */}
          <div className="chart-bars">
            {[40, 60, 50, 80, 75, 90, 85].map((h, i) => (
              <div key={i} className="bar" style={{ height: `${h}%` }} />
            ))}
          </div>
        </div>

        {/* Supervisor Intelligence Brief */}
        <div className="glass-card intel-card">
          <div className="intel-header">
            <div className="agent-orb" />
            <span className="badge">SUPERVISOR</span>
          </div>
          <h3>Intelligence Brief</h3>
          <p className="intel-body">
            "Opportunity detected in <strong>Semiconductors</strong>. Your cash reserve is currently 15% — consider deploying 5% into diversified index positions."
          </p>
          <div className="confidence-row">
            <p className="confidence-label">Confidence Score: <strong>94%</strong></p>
          </div>
        </div>
      </div>
    </div>
  )
}
