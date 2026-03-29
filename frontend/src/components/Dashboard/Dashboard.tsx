import { useDashboard } from '../../hooks/useDashboard'
import './Dashboard.css'

// Simple frontend map for Native Currency formatting based on ISO country codes
const CURRENCY_MAP: Record<string, { symbol: string, code: string, flag: string, name: string }> = {
  'US': { symbol: '$', code: 'USD', flag: '🇺🇸', name: 'United States' },
  'IN': { symbol: '₹', code: 'INR', flag: '🇮🇳', name: 'India' },
  'UK': { symbol: '£', code: 'GBP', flag: '🇬🇧', name: 'United Kingdom' },
  'SG': { symbol: 'S$', code: 'SGD', flag: '🇸🇬', name: 'Singapore' }
}

export default function Dashboard() {
  const { dashboardData, isLoading, error } = useDashboard()

  if (isLoading) {
    return <div className="loading-spinner">🌐 Syncing Global Portfolio...</div>
  }

  if (error || dashboardData?.error) {
    return (
      <div className="empty-state" style={{ borderColor: '#ff6b6b' }}>
        <div className="empty-icon">⚠️</div>
        <h3>Sync Error</h3>
        <p style={{ color: 'var(--text-dim)' }}>We couldn't reach the live market feeds. Please try again later.</p>
      </div>
    )
  }

  if (!dashboardData || dashboardData.total_assets === 0) {
    return (
      <div className="empty-state">
        <div className="empty-icon">🌍</div>
        <h2>Your Global Wealth Tracker</h2>
        <p style={{ color: 'var(--text-dim)', maxWidth: '400px', marginTop: '1rem' }}>
          This dashboard automatically syncs with live market data to give you an overview of your localized wealth. 
          Head over to <strong>My Holdings</strong> to add your first assets!
        </p>
      </div>
    )
  }

  const { total_assets, total_countries, portfolios } = dashboardData

  return (
    <div className="tab-panel dashboard-container">
      {/* Layer 1: Executive KPI Header */}
      <div className="dashboard-header">
        <div>
          <h1>Global Net Worth</h1>
          <p style={{ color: 'var(--text-dim)' }}>Real-time localized valuations across all active markets.</p>
        </div>
        <div className="vanity-pill">
          Tracking {total_assets} global asset{total_assets > 1 ? 's' : ''} across {total_countries} juridstiction{total_countries > 1 ? 's' : ''}.
        </div>
      </div>

      {/* Layer 2: Geographic Native Renders */}
      {Object.values(portfolios).map((portfolio) => {
        const isUp = portfolio.daily_pnl >= 0
        const sign = isUp ? '+' : ''
        const colorClass = isUp ? 'positive' : 'negative'
        
        // Lookup formatting or Default
        const meta = CURRENCY_MAP[portfolio.country_code] || { symbol: '', code: portfolio.country_code, flag: '🌐', name: portfolio.country_code }
        
        return (
          <div key={portfolio.country_code} className="country-section">
            <h2 className="country-header">{meta.flag} {meta.name} Holdings</h2>
            
            {/* The Big Native Wealth Card */}
            <div className="wealth-card">
              <div>
                <div className="wealth-label">Total Localized Value</div>
                <div className="wealth-value">
                  {meta.symbol}{portfolio.total_value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                  <span style={{ fontSize: '1rem', color: 'var(--text-dim)', marginLeft: '8px' }}>{meta.code}</span>
                </div>
              </div>

              <div className="pnl-badge">
                <div className={`pnl-amount ${colorClass}`}>
                  {sign}{meta.symbol}{portfolio.daily_pnl.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                  <span style={{ fontSize: '0.8rem', marginLeft: '6px' }}>({sign}{portfolio.daily_pnl_percent}%)</span>
                </div>
                <div className="pnl-label">24h Gain/Loss Returns</div>
              </div>
            </div>

            {/* Structured Table */}
            <div className="glass-card" style={{ padding: 0, overflow: 'hidden' }}>
              <table className="asset-table">
                <thead>
                  <tr>
                    <th>Asset (Ticker)</th>
                    <th>Current Shares</th>
                    <th>Live Price</th>
                    <th>24h Market Change</th>
                    <th style={{ textAlign: 'right' }}>Total Value</th>
                  </tr>
                </thead>
                <tbody>
                  {portfolio.assets.map((asset) => {
                    const assetIsUp = asset.asset_pnl >= 0
                    const assetSign = assetIsUp ? '+' : ''
                    
                    return (
                      <tr key={asset.ticker}>
                        <td><strong>{asset.ticker}</strong></td>
                        <td>{asset.shares.toLocaleString()}</td>
                        <td>{meta.symbol}{asset.current_price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</td>
                        <td className={assetIsUp ? 'positive' : 'negative'}>
                          {assetSign}{meta.symbol}{asset.asset_pnl.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })} 
                          <span style={{ marginLeft: '4px', opacity: 0.7 }}>({assetSign}{asset.asset_pnl_percent}%)</span>
                        </td>
                        <td style={{ textAlign: 'right', fontWeight: 500 }}>
                          {meta.symbol}{asset.total_value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          </div>
        )
      })}
    </div>
  )
}
