import React, { useState } from 'react'
import { ChatMessage } from '../../hooks/useGoalStrategist'

interface GoalChatRefinementProps {
  chatHistory: ChatMessage[]
  onSendMessage: (message: string) => Promise<void>
  isLoading: boolean
  country: string
}

export default function GoalChatRefinement({
  chatHistory,
  onSendMessage,
  isLoading,
  country
}: GoalChatRefinementProps) {
  const [input, setInput] = useState('')

  const promptChips = [
    'What if I increase monthly savings by $500?',
    country === 'INDIA' || country === 'IN'
      ? 'How do Section 80C and NPS caps affect my strategy?'
      : country === 'UK'
      ? 'How does the £20,000 ISA allowance apply here?'
      : 'How should I split savings between 401(k) and brokerage?',
    'What happens if portfolio volatility increases by 5%?',
    'What is my estimated capital accumulation at retirement?'
  ]

  const handleSubmit = async (e?: React.FormEvent) => {
    if (e) e.preventDefault()
    if (!input.trim() || isLoading) return
    const text = input.trim()
    setInput('')
    await onSendMessage(text)
  }

  const handleChipClick = async (chipText: string) => {
    if (isLoading) return
    await onSendMessage(chipText)
  }

  return (
    <div className="glass-card goal-refinement-container" style={{
      padding: '1.25rem',
      borderRadius: '16px',
      background: 'rgba(15, 17, 26, 0.75)',
      border: '1px solid var(--glass-border)',
      height: '100%',
      display: 'flex',
      flexDirection: 'column',
      justifyContent: 'space-between',
      boxSizing: 'border-box'
    }}>
      <div>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.85rem' }}>
          <div>
            <h3 style={{ margin: 0, fontSize: '1.05rem', color: 'var(--text-bright)' }}>
              💬 Autonomous Strategy Refinement
            </h3>
            <p style={{ margin: '0.2rem 0 0 0', fontSize: '0.8rem', color: '#94a3b8' }}>
              Test what-if trade-offs or horizon shifts with in-session memory.
            </p>
          </div>
          <span style={{
            fontSize: '0.72rem',
            padding: '4px 10px',
            borderRadius: '999px',
            background: 'rgba(0, 240, 255, 0.08)',
            border: '1px solid rgba(0, 240, 255, 0.25)',
            color: 'var(--accent-cyan)',
            fontWeight: 600
          }}>
            Multi-Turn Copilot
          </span>
        </div>

        {/* Suggested Prompt Chips */}
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.4rem', marginBottom: '1rem' }}>
          {promptChips.map((chip, idx) => (
            <button
              key={idx}
              type="button"
              onClick={() => handleChipClick(chip)}
              disabled={isLoading}
              style={{
                background: 'rgba(255, 255, 255, 0.04)',
                border: '1px solid rgba(255, 255, 255, 0.1)',
                borderRadius: '999px',
                padding: '5px 11px',
                color: '#cbd5e1',
                fontSize: '0.75rem',
                cursor: isLoading ? 'not-allowed' : 'pointer',
                transition: 'all 0.2s ease'
              }}
              onMouseEnter={e => {
                e.currentTarget.style.borderColor = 'var(--accent-cyan)'
                e.currentTarget.style.color = '#ffffff'
                e.currentTarget.style.background = 'rgba(0, 240, 255, 0.08)'
              }}
              onMouseLeave={e => {
                e.currentTarget.style.borderColor = 'rgba(255, 255, 255, 0.1)'
                e.currentTarget.style.color = '#cbd5e1'
                e.currentTarget.style.background = 'rgba(255, 255, 255, 0.04)'
              }}
            >
              {chip}
            </button>
          ))}
        </div>
      </div>

      {/* Multi-Turn Message Thread */}
      <div style={{
        display: 'flex',
        flexDirection: 'column',
        gap: '0.75rem',
        flex: 1,
        maxHeight: '340px',
        minHeight: '160px',
        overflowY: 'auto',
        paddingRight: '0.4rem',
        marginBottom: '1rem'
      }}>
        {chatHistory.length === 0 ? (
          <div style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            height: '100%',
            color: '#64748b',
            textAlign: 'center',
            padding: '1.5rem',
            fontSize: '0.82rem',
            border: '1px dashed rgba(255, 255, 255, 0.06)',
            borderRadius: '12px'
          }}>
            <span style={{ fontSize: '1.5rem', marginBottom: '0.4rem' }}>💡</span>
            Click a suggested scenario chip above or ask any strategic question below to iterate in real time.
          </div>
        ) : (
          chatHistory.map(msg => (
            <div
              key={msg.id}
              style={{
                alignSelf: msg.role === 'user' ? 'flex-end' : 'flex-start',
                maxWidth: '88%',
                padding: '0.75rem 1rem',
                borderRadius: msg.role === 'user' ? '14px 14px 2px 14px' : '14px 14px 14px 2px',
                background: msg.role === 'user' ? 'rgba(0, 240, 255, 0.12)' : 'rgba(255, 255, 255, 0.05)',
                border: msg.role === 'user' ? '1px solid rgba(0, 240, 255, 0.3)' : '1px solid rgba(255, 255, 255, 0.1)'
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', gap: '1rem', marginBottom: '0.3rem' }}>
                <span style={{
                  fontSize: '0.72rem',
                  fontWeight: 600,
                  textTransform: 'uppercase',
                  color: msg.role === 'user' ? 'var(--accent-cyan)' : '#38bdf8'
                }}>
                  {msg.role === 'user' ? 'You' : 'Finnie Strategist'}
                </span>
                <span style={{ fontSize: '0.68rem', color: '#64748b' }}>
                  {msg.timestamp}
                </span>
              </div>
              <p style={{
                margin: 0,
                fontSize: '0.86rem',
                lineHeight: 1.5,
                color: '#f8fafc',
                whiteSpace: 'pre-wrap'
              }}>
                {msg.content}
              </p>
            </div>
          ))
        )}
      </div>

      {/* Input Form */}
      <form onSubmit={handleSubmit} style={{ display: 'flex', gap: '0.75rem' }}>
        <input
          type="text"
          className="goal-input"
          value={input}
          onChange={e => setInput(e.target.value)}
          placeholder="Ask a what-if question (e.g. 'What if I retire 2 years earlier?')..."
          disabled={isLoading}
          style={{
            flex: 1,
            padding: '0.75rem 1rem',
            borderRadius: '10px',
            background: 'rgba(0, 0, 0, 0.3)',
            border: '1px solid var(--glass-border)',
            color: 'var(--text-bright)',
            fontSize: '0.9rem'
          }}
        />
        <button
          type="submit"
          className="calculate-btn"
          disabled={isLoading || !input.trim()}
          style={{
            padding: '0.75rem 1.4rem',
            whiteSpace: 'nowrap',
            display: 'flex',
            alignItems: 'center',
            gap: '0.4rem',
            cursor: isLoading || !input.trim() ? 'not-allowed' : 'pointer'
          }}
        >
          {isLoading ? 'Thinking...' : 'Send ⚡'}
        </button>
      </form>
    </div>
  )
}
