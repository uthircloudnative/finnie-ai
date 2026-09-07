import { useState } from 'react'
import { useCountryPortfolio } from '../../hooks/useCountryPortfolio'
import { useChat } from '../../hooks/useChat'
import ChatWindow from '../Chat/ChatWindow'
import ChatInput from '../Chat/ChatInput'
import './PortfolioAnalyst.css'

// ── Insight section definitions ─────────────────────────────────────────────
const INSIGHT_SECTIONS = [
  { key: 'risk',    icon: '📈', color: 'cyan',    patterns: ['risk profile', 'your risk', '1.', 'beta', 'volatility'] },
  { key: 'divers', icon: '🎯', color: 'emerald', patterns: ['diversification', '2.', 'sector', 'spread'] },
  { key: 'advice', icon: '💡', color: 'amber',   patterns: ['means for you', '3.', 'consider', 'advice', 'what this'] },
]

/**
 * Parses the LLM response into up to 3 labelled sections.
 * Handles both "1. **Title**: body" and "**Title**\nbody" formats.
 * Returns raw sections with title + body, or falls back to a single section.
 */
function parseInsightSections(raw: string): Array<{ icon: string; color: string; title: string; body: string }> {
  // Strip leading numbers like "1. " or "1) "
  const clean = raw.replace(/^\d+[.)\s]+/gm, '')

  // Split on lines that are bold headers: **Something**: or **Something**\n
  const headerRegex = /\*\*([^*]+)\*\*[:\s]*/g
  const matches = [...clean.matchAll(headerRegex)]

  if (matches.length >= 2) {
    return matches.map((match, i) => {
      const title = match[1].trim()
      const start = (match.index ?? 0) + match[0].length
      const end = matches[i + 1]?.index ?? clean.length
      const body = clean.slice(start, end).trim().replace(/\*\*?/g, '')
      const meta = INSIGHT_SECTIONS.find(s =>
        s.patterns.some(p => title.toLowerCase().includes(p))
      ) ?? INSIGHT_SECTIONS[i % INSIGHT_SECTIONS.length]
      return { icon: meta.icon, color: meta.color, title, body }
    })
  }

  // Fallback: show as one plain section
  return [{
    icon: '📊',
    color: 'blue',
    title: "Finnie's Analysis",
    body: raw.replace(/\*\*?/g, '').trim(),
  }]
}

// ── Shared helper functions ─────────────────────────────────────────────────

// ── Volatility risk tier (country-calibrated) ───────────────────────────────
function getVolTier(vol: number, thresholds: [number, number]): { label: string; cls: string } {
  const [low, high] = thresholds
  if (vol < low)  return { label: 'Low Risk',    cls: 'vol-low' }
  if (vol < high) return { label: 'Medium Risk', cls: 'vol-medium' }
  return              { label: 'High Risk',    cls: 'vol-high' }
}

// ── Diversification tier ────────────────────────────────────────────────────
function getDiversTier(score: number | null | undefined): { label: string; cls: string } {
  if (score === null || score === undefined) return { label: 'Pending', cls: 'divers-medium' }
  if (score >= 7.5) return { label: 'Well-Diversified', cls: 'divers-high' }
  if (score >= 4)   return { label: 'Moderate',         cls: 'divers-medium' }
  return                   { label: 'Concentrated',     cls: 'divers-low' }
}

// ── Beta stance label (shared) ──────────────────────────────────────────────
function getBetaStance(beta: number): { label: string; cls: string } {
  if (beta > 1.1) return { label: 'Aggressive',     cls: 'aggressive' }
  if (beta < 0.9) return { label: 'Conservative',   cls: 'conservative' }
  return                 { label: 'Market-Aligned', cls: 'balanced' }
}

export default function PortfolioAnalyst() {
  const {
    tabs,
    selectedCountry,
    setSelectedCountry,
    analysis,
    analysisResults,
    isLoading,
    isBatchLoading,
    error,
    refetch,
    fetchDiversification,
  } = useCountryPortfolio()

  const [isFetchingDiversification, setIsFetchingDiversification] = useState(false)
  const [diversificationError, setDiversificationError] = useState<string | null>(null)

  const handleGetDiversification = async () => {
    setIsFetchingDiversification(true)
    setDiversificationError(null)
    const { score, error: fetchErr } = await fetchDiversification(selectedCountry)
    setIsFetchingDiversification(false)
    if (fetchErr || score === null) {
      setDiversificationError(fetchErr || 'Experiencing technical issue, try again later')
    }
  }

  const [isChatOpen, setIsChatOpen] = useState(false)
  const chat = useChat()

  const handleSendMessage = (text: string) => {
    chat.sendMessage(text, 'PORTFOLIO_ANALYST', analysisResults)
  }

  const thresholds: [number, number] = analysisResults?.vol_thresholds ?? [15, 25]
  const isAllMarkets = selectedCountry === 'ALL'

  // ── Context banner text ─────────────────────────────────────────────────
  const bannerText = isAllMarkets
    ? `Showing all ${analysisResults?.tickers?.length ?? '...'} holdings across ${analysisResults?.unique_countries?.length ?? '...'} markets`
    : `${analysisResults?.benchmark_name ? `Benchmark: ${analysisResults.benchmark_name}` : ''} · ${analysisResults?.tickers?.length ?? '...'} stocks`

  return (
    <div className={`analyst-workspace-root ${isChatOpen ? 'sidebar-open' : 'sidebar-closed'}`}>

      {/* ── Main Content ─────────────────────────────────────────────── */}
      <div className="analyst-main-content tab-panel">
        <div className="analyst-header">
          <div className="header-title-group">
            <h1>Portfolio Analyst</h1>
            <p className="analyst-subtitle">Deep risk analysis fueled by yfinance &amp; RAG.</p>
          </div>

          <div className="header-actions">
            <button
              className={`ask-finnie-toggle ${isChatOpen ? 'active' : ''}`}
              onClick={() => setIsChatOpen(!isChatOpen)}
            >
              <span className="toggle-icon">💬</span>
              {isChatOpen ? 'Close Assistant' : 'Ask Finnie'}
            </button>

            <button
              className="refresh-btn"
              onClick={refetch}
              disabled={isLoading || isBatchLoading}
              title={isBatchLoading ? 'Loading all markets in background…' : 'Re-run fresh analysis'}
            >
              {isBatchLoading
                ? '⏳ Loading markets…'
                : isLoading
                ? '⌛ Analyzing…'
                : '🔄 Refresh Analysis'
              }
            </button>
          </div>
        </div>

        {/* ── Country Tab Bar ──────────────────────────────────────── */}
        {tabs.length > 0 && (
          <div className="country-tab-bar">
            {tabs.map((tab) => (
              <button
                key={tab.code}
                className={`country-tab ${selectedCountry === tab.code ? 'active' : ''}`}
                onClick={() => setSelectedCountry(tab.code)}
              >
                {tab.label}
                <span className="country-tab-badge">{tab.holdingCount}</span>
              </button>
            ))}
          </div>
        )}

        {/* ── Context Banner ───────────────────────────────────────── */}
        {analysisResults && (
          <div className="country-context-banner">
            <span className="banner-dot" />
            {bannerText}
          </div>
        )}

        <div className="analyst-results-area">
          {isLoading && (
            <div className="glass-card analyst-loading-card">
              <div className="shimmer-line" />
              <div className="shimmer-line short" />
              <div className="shimmer-line" />
              <p>Finnie is crunching numbers, calculating risk, and retrieving theory...</p>
            </div>
          )}

          {error && (
            <div className="glass-card analyst-error-card">
              <h3>⚠️ Analysis Error</h3>
              <p>{error}</p>
              <button className="btn-cyan" onClick={refetch} style={{ marginTop: '1rem' }}>Try Again</button>
            </div>
          )}

          {!isLoading && !error && analysisResults && (
            <>
              <div className="metrics-grid">

                {/* ── Beta Card: All-Markets shows per-country rows ── */}
                {isAllMarkets && analysisResults.country_betas ? (
                  <div className="glass-card metric-card metric-card--wide">
                    <span className="metric-label">Market Exposure</span>
                    <div className="country-beta-rows">
                      {Object.entries(analysisResults.country_betas).map(([country, info]) => {
                        const stance = getBetaStance(info.beta)
                        return (
                          <div key={country} className="country-beta-row">
                            <div className="country-beta-header">
                              <span className="country-beta-label">
                                {country} · Beta <strong>{info.beta}</strong>
                              </span>
                              <span className={`country-beta-vs ${stance.cls}`}>
                                vs {info.benchmark_name}
                              </span>
                            </div>
                            <div className="beta-bar-container">
                              <div
                                className={`beta-bar-fill ${stance.cls}`}
                                style={{ width: `${Math.min(Math.max((info.beta / 2) * 100, 5), 100)}%` }}
                              />
                            </div>
                            <span className={`metric-sub ${stance.cls}`}>{stance.label}</span>
                          </div>
                        )
                      })}
                    </div>
                  </div>
                ) : (
                  /* Single-country Beta card */
                  <div className="glass-card metric-card">
                    <span className="metric-label">Market Beta</span>
                    <span className="metric-value">{analysisResults.beta}</span>
                    <div className="beta-bar-container">
                      <div
                        className={`beta-bar-fill ${getBetaStance(analysisResults.beta).cls}`}
                        style={{ width: `${Math.min(Math.max((analysisResults.beta / 2) * 100, 5), 100)}%` }}
                      />
                    </div>
                    <span className={`metric-sub`}>
                      {getBetaStance(analysisResults.beta).label}
                      {analysisResults.benchmark_name && (
                        <span className="benchmark-tag"> · vs {analysisResults.benchmark_name}</span>
                      )}
                    </span>
                  </div>
                )}

                {/* ── Volatility Card ───────────────────────────────── */}
                <div className="glass-card metric-card">
                  <span className="metric-label">Annual Volatility</span>
                  <span className="metric-value">{analysisResults.volatility}%</span>
                  <div className="vol-tier-bar-container">
                    <div
                      className={`vol-tier-bar-fill ${getVolTier(analysisResults.volatility, thresholds).cls}`}
                      style={{ width: `${Math.min((analysisResults.volatility / 40) * 100, 100)}%` }}
                    />
                  </div>
                  <div className="vol-indicator">
                    <div className={`vol-dot ${getVolTier(analysisResults.volatility, thresholds).cls}`} />
                    <span className={`vol-tier-label ${getVolTier(analysisResults.volatility, thresholds).cls}`}>
                      {getVolTier(analysisResults.volatility, thresholds).label}
                    </span>
                    <span className="vol-std-label">&nbsp;· 1yr Std Dev</span>
                  </div>
                </div>

                {/* ── Diversification Card ─────────────────────────── */}
                <div className="glass-card metric-card">
                  <span className="metric-label">Diversification</span>
                  {analysisResults.diversification_score === null || analysisResults.diversification_score === undefined ? (
                    <div className="divers-tile-fallback">
                      {isFetchingDiversification ? (
                        <div className="divers-tile-status loading">
                          <div className="spinner-mini" />
                          <span>Calculating score...</span>
                        </div>
                      ) : diversificationError ? (
                        <div className="divers-tile-status error">
                          <span className="divers-error-msg">⚠️ {diversificationError}</span>
                          <button className="divers-retry-btn" onClick={handleGetDiversification}>
                            Try Again
                          </button>
                        </div>
                      ) : (
                        <div className="divers-tile-status get-score">
                          <p className="divers-tile-desc">Sector data pending</p>
                          <button className="divers-action-btn" onClick={handleGetDiversification}>
                            📊 Get Diversification Score
                          </button>
                        </div>
                      )}
                    </div>
                  ) : (
                    <>
                      <span className="metric-value">{analysisResults.diversification_score}/10</span>
                      <div className="divers-bar-container">
                        <div
                          className={`divers-bar-fill ${getDiversTier(analysisResults.diversification_score).cls}`}
                          style={{ width: `${(analysisResults.diversification_score / 10) * 100}%` }}
                        />
                      </div>
                      <div className="divers-footer">
                        <span className={`divers-tier-label ${getDiversTier(analysisResults.diversification_score).cls}`}>
                          {getDiversTier(analysisResults.diversification_score).label}
                        </span>
                        <span className="metric-sub">
                          {analysisResults.tickers?.length || 0} stocks analysed
                        </span>
                      </div>
                      {/* Sector breakdown */}
                      {analysisResults.sectors && Object.keys(analysisResults.sectors).length > 0 && (
                        <div className="sector-breakdown">
                          {Object.entries(analysisResults.sectors).map(([sector, count]) => (
                            <span key={sector} className="sector-chip">
                              {sector} {count}
                            </span>
                          ))}
                        </div>
                      )}
                    </>
                  )}
                </div>
              </div>

              {/* ── Finnie's Insight: Structured Section Cards ─── */}
              {analysis && (() => {
                const sections = parseInsightSections(analysis)
                // Extract $NFA footer if present
                const nfaMatch = analysis.match(/\$NFA[^\n]*/i)
                const nfaText = nfaMatch ? nfaMatch[0] : null

                return (
                  <div className="insight-sections">
                    {sections.map((sec, i) => (
                      <div key={i} className={`glass-card insight-card insight-card--${sec.color}`}>
                        <div className="insight-card-header">
                          <span className="insight-icon">{sec.icon}</span>
                          <h3 className="insight-title">{sec.title}</h3>
                        </div>
                        <div className="insight-body">
                          {sec.body.split('\n').filter(l => l.trim()).map((line, j) => (
                            <p key={j}>{line}</p>
                          ))}
                        </div>
                      </div>
                    ))}
                    {nfaText && (
                      <div className="nfa-footer">
                        <span className="nfa-badge">⚖️ $NFA</span>
                        <span className="nfa-text">{nfaText.replace(/\$NFA[:\s]*/i, '')}</span>
                      </div>
                    )}
                  </div>
                )
              })()}
            </>
          )}

          {!isLoading && !error && !analysis && (
            <div className="glass-card empty-analysis-card">
              <h3>No Analysis Found</h3>
              <p>Click 'Refresh Report' to run your first portfolio check.</p>
            </div>
          )}
        </div>
      </div>

      {/* ── Interaction Sidebar ───────────────────────────────────────────── */}
      {isChatOpen && (
        <div className="workspace-sidebar">
          <div className="workspace-sidebar-header">
            <div className="workspace-sidebar-title-group">
              <span className="workspace-sidebar-icon">📊</span>
              <h3>Portfolio Deep-Dive</h3>
            </div>
            <span className="workspace-sidebar-status">Live Expert</span>
          </div>

          <div className="workspace-sidebar-chat-wrapper">
            <ChatWindow messages={chat.messages} isLoading={chat.isLoading} />
            <ChatInput onSend={handleSendMessage} isLoading={chat.isLoading} />
          </div>
        </div>
      )}
    </div>
  )
}
