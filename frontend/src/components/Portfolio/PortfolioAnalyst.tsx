import { useState } from 'react'
import { useAnalysis } from '../../hooks/useAnalysis'
import { useChat } from '../../hooks/useChat'
import ChatWindow from '../Chat/ChatWindow'
import ChatInput from '../Chat/ChatInput'
import './PortfolioAnalyst.css'

export default function PortfolioAnalyst() {
  const { analysis, analysisResults, isLoading, error, refetch } = useAnalysis()
  const [isChatOpen, setIsChatOpen] = useState(false)
  
  const chat = useChat()

  const handleSendMessage = (text: string) => {
    // Pass the current metrics as context to the AI
    chat.sendMessage(text, 'PORTFOLIO_ANALYST', analysisResults)
  }

  return (
    <div className={`analyst-workspace-root ${isChatOpen ? 'sidebar-open' : 'sidebar-closed'}`}>
      
      {/* ── Main Content Column ────────────────────────────────────────── */}
      <div className="analyst-main-content tab-panel">
        <div className="analyst-header">
          <div className="header-title-group">
            <h1>Portfolio Analyst</h1>
            <p className="analyst-subtitle">Deep risk analysis fueled by yfinance & RAG.</p>
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
              disabled={isLoading}
              title="Run new analysis"
            >
              {isLoading ? '⌛ Analyzing...' : '🔄 Refresh Report'}
            </button>
          </div>
        </div>

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
                <div className="glass-card metric-card">
                  <span className="metric-label">Market Beta</span>
                  <span className="metric-value">{analysisResults.beta}</span>
                  <div className="beta-bar-container">
                    <div 
                      className={`beta-bar-fill ${analysisResults.beta > 1.1 ? 'aggressive' : analysisResults.beta < 0.9 ? 'conservative' : 'balanced'}`}
                      style={{ width: `${Math.min(Math.max((analysisResults.beta / 2) * 100, 5), 100)}%` }}
                    ></div>
                  </div>
                  <span className="metric-sub">{analysisResults.beta > 1.1 ? 'Aggressive' : analysisResults.beta < 0.9 ? 'Conservative' : 'Market-Aligned'}</span>
                </div>

                <div className="glass-card metric-card">
                  <span className="metric-label">Annual Volatility</span>
                  <span className="metric-value">{analysisResults.volatility}%</span>
                  <div className="vol-indicator">
                    <div className="vol-dot"></div>
                    <span>1yr Standard Deviation</span>
                  </div>
                </div>

                <div className="glass-card metric-card">
                  <span className="metric-label">Diversification</span>
                  <span className="metric-value">{analysisResults.diversification_score}/10</span>
                  <span className="metric-sub">{analysisResults.tickers?.length || 0} Assets trackable</span>
                </div>
              </div>

              <div className="glass-card analyst-report-card">
                <div className="report-header">
                  <span className="report-badge">Finnie's Insight</span>
                  <span className="report-date">Generated: {new Date().toLocaleTimeString()}</span>
                </div>
                <div className="report-text">
                  {analysis?.split('\n').map((line, i) => (
                    <p key={i}>{line}</p>
                  ))}
                </div>
              </div>
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

      {/* ── Interaction Sidebar ────────────────────────────────────────── */}
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
