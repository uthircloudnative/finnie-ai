import { useState } from 'react'
import { useMarketInsights } from '../../hooks/useMarketInsights'
import ChatWindow from '../Chat/ChatWindow'
import ChatInput from '../Chat/ChatInput'
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
            <button 
              className={`ask-finnie-toggle ${isChatOpen ? 'active' : ''}`}
              onClick={() => setIsChatOpen(!isChatOpen)}
            >
              <span className="toggle-icon">🧠</span>
              {isChatOpen ? 'Close Assistant' : 'Ask Finnie'}
            </button>
          </div>
          <p className="insights-subtitle">
            Real-time sentiment and news analysis for your global portfolio.
          </p>
        </div>

        <div className="glass-card pulse-card">
          <div className="pulse-card-header">
            <div className="pulse-title-group">
              <span className="pulse-icon">📡</span>
              <h3>Portfolio Market Pulse</h3>
            </div>
            <button className="refresh-btn" onClick={refetch} disabled={isLoading}>
              {isLoading ? '🔄' : 'Refresh'}
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
        <div className="workspace-sidebar">
          <div className="workspace-sidebar-header">
            <div className="workspace-sidebar-title-group">
              <span className="workspace-sidebar-icon">🔍</span>
              <h3>Ticker Deep-Dive</h3>
            </div>
            <span className="workspace-sidebar-status">Live Assistant</span>
          </div>
          
          <div className="workspace-sidebar-chat-wrapper">
            <ChatWindow messages={chat.messages} isLoading={chat.isLoading} />
            <ChatInput 
              onSend={handleSendMessage} 
              isLoading={chat.isLoading} 
            />
          </div>
        </div>
      )}
    </div>
  )
}
