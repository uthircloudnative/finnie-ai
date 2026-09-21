import React from 'react'
import './GoodbyeScreen.css'

interface GoodbyeScreenProps {
  onLogin: () => void
}

export const GoodbyeScreen: React.FC<GoodbyeScreenProps> = ({ onLogin }) => {
  return (
    <div className="goodbye-screen-overlay" data-testid="goodbye-screen">
      <div className="goodbye-card">
        {/* Glowing Avatar Orb */}
        <div className="goodbye-avatar-wrap">
          <div className="goodbye-avatar-glow" />
          <div className="goodbye-avatar">👤</div>
        </div>

        {/* Heading */}
        <h1 className="goodbye-heading">See you soon! 👋</h1>

        {/* Generic Reassurance Body */}
        <p className="goodbye-message">
          You have successfully signed out. Your financial information and portfolio data are stored securely.
        </p>

        {/* Security Status Badge */}
        <div className="goodbye-status-badge">
          <span className="goodbye-badge-icon">🔒</span>
          <span>Session ended securely · All data protected</span>
        </div>

        {/* Single Primary Action */}
        <div className="goodbye-actions">
          <button
            className="goodbye-btn goodbye-btn-primary"
            onClick={onLogin}
          >
            🔑 Log In
          </button>
        </div>

        {/* Security Tip */}
        <p className="goodbye-security-tip">
          💡 Security Tip: Close your browser tab if you are on a shared computer
        </p>

        {/* Compliance Footer */}
        <div className="goodbye-footer">
          <span>🔒 256-Bit TLS · Not Financial Advice ($NFA)</span>
        </div>
      </div>
    </div>
  )
}
