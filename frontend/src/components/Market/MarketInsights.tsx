import { useState } from 'react'
import { useMarketInsights } from '../../hooks/useMarketInsights'
import CopilotDrawer from '../Chat/CopilotDrawer'
import { useChat } from '../../hooks/useChat'
import './MarketInsights.css'

export default function MarketInsights() {
  const { pulse, isLoading, error, refetch } = useMarketInsights()
  const chat = useChat()
  const [isChatOpen, setIsChatOpen] = useState(false)

  const handleSendMessage = (message: string) => {
    chat.sendMessage(message, 'MARKET_INSIGHTS')
  }

  return (
    <div className={`insights-workspace ${isChatOpen ? 'sidebar-open' : 'sidebar-closed'}`}>
      {/* ── Left Column: Market Pulse Dashboard ────────────────────────── */}
      <div className="insights-main-content tab-panel">
        <div className="insights-header-section">
          <div className="header-top-row">
            <h1>Market Insights</h1>
            {!isChatOpen && (
              <button 
                className="ask-finnie-toggle"
                onClick={() => setIsChatOpen(true)}
              >
                <span className="toggle-icon">✦</span>
                Ask Finnie
              </button>
            )}
          </div>
          <p className="insights-subtitle">
            Real-time sentiment and news analysis for your global portfolio.
          </p>
        </div>

        <div className="glass-card pulse-card">
          <div className="pulse-card-header">
            <div className="pulse-title-group">
              <span className="pulse-icon">●</span>
              <h3>Portfolio Market Pulse</h3>
            </div>
            <button className="refresh-btn" onClick={refetch} disabled={isLoading}>
              {isLoading ? 'Syncing…' : 'Refresh'}
            </button>
          </div>

          {isLoading ? (
            <div className="pulse-loading">
              <div className="shimmer-line" />
              <div className="shimmer-line short" />
              <div className="shimmer-line" />
              <p>Finnie is scanning global news feeds…</p>
            </div>
          ) : error ? (
            <div className="pulse-error">⚠️ {error}</div>
          ) : (
            <div className="pulse-content">
              {/* Note: The 'pulse' content is pre-formatted markdown from the Finnie agent */}
              <div className="markdown-body">
                {pulse?.split('\n').map((line, i) => (
                  <p key={i}>{line}</p>
                ))}
              </div>
            </div>
          )}
        </div>

        <div className="insights-footer-note">
          <p>
            Data provided by Alpha Vantage News & Sentiment. 
            Sentiment scores range from -1.0 (Bearish) to 1.0 (Bullish).
          </p>
        </div>
      </div>

      {/* ── Right Column: Ticker Deep-Dive Assistant ────────────────────── */}
      {isChatOpen && (
        <CopilotDrawer
          title="Ticker Deep-Dive"
          subtitle="Real-time sentiment and market pulse assistant."
          statusBadge="Live Assistant"
          messages={chat.messages}
          isLoading={chat.isLoading}
          loadingText="Finnie is analyzing global news and sentiment..."
          onSendMessage={handleSendMessage}
          onClearHistory={chat.clearMessages}
          onClose={() => setIsChatOpen(false)}
          inputPlaceholder="Ask about ticker news, sentiment, or macro trends..."
          storageKey="finnie_market_copilot_width"
          disclaimerText="$NFA — Finnie is an AI assistant, not a licensed financial advisor. All answers are grounded in public educational sources."
        />
      )}
    </div>
  )
}
