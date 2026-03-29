import { useAnalysis } from '../../hooks/useAnalysis'
import { useChat } from '../../hooks/useChat'
import ChatWindow from '../Chat/ChatWindow'
import ChatInput from '../Chat/ChatInput'
import './PortfolioAnalyst.css'

export default function PortfolioAnalyst() {
  const { analysis, analysisResults, isLoading, error, refetch } = useAnalysis()
  
  // Use independent chat state for the analyst tab
  const { 
    messages, 
    isLoading: isChatLoading, 
    sendMessage 
  } = useChat()

  const handleSendMessage = (text: string) => {
    // Pass the current metrics as context to the AI
    sendMessage(text, 'PORTFOLIO_ANALYST', analysisResults)
  }

  return (
    <div className="tab-panel">
      <div className="analyst-header">
        <h1>Portfolio Analyst</h1>
        <button 
          className="refresh-btn" 
          onClick={refetch} 
          disabled={isLoading}
          title="Run new analysis"
        >
          {isLoading ? '⌛ Analyzing...' : '🔄 Refresh Report'}
        </button>
      </div>

      <div className="analyst-content">
        {isLoading && (
          <div className="glass-card analyst-loading-card">
            <div className="shimmer-line"></div>
            <div className="shimmer-line short"></div>
            <div className="shimmer-line"></div>
            <p>Finnie is crunching numbers, calculating risk, and retrieving theory...</p>
          </div>
        )}

        {error && (
          <div className="glass-card analyst-error-card">
            <h3>⚠️ Analysis Error</h3>
            <p>{error}</p>
            <button className="holdings-add-btn" onClick={refetch}>Try Again</button>
          </div>
        )}

        {!isLoading && !error && analysisResults && (
          <div className="analyst-workspace">
            {/* Left Column: Dashboard Results */}
            <div className="analyst-dashboard">
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
            </div>

            {/* Right Column: Interaction Sidebar */}
            <div className="glass-card analyst-chat-container">
              <div className="chat-header-minimal">
                <span className="chat-subtitle">Ask me about your risk metrics...</span>
              </div>
              <ChatWindow messages={messages} isLoading={isChatLoading} />
              <div className="chat-input-wrapper">
                <ChatInput onSend={handleSendMessage} isLoading={isChatLoading} />
              </div>
            </div>
          </div>
        )}

        {!isLoading && !error && !analysis && (
          <div className="glass-card empty-analysis-card">
            <h3>No Analysis Found</h3>
            <p>Click 'Refresh Report' to run your first portfolio check.</p>
          </div>
        )}
      </div>
    </div>
  )
}
