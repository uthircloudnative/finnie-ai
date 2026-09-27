interface ThoughtStreamProps {
  thoughts: string[]
  isStreaming: boolean
}

export default function ThoughtStream({ thoughts, isStreaming }: ThoughtStreamProps) {
  if (!thoughts || thoughts.length === 0) return null

  return (
    <div className="thought-stream-card" style={{
      display: 'flex',
      flexDirection: 'column',
      gap: '0.5rem',
      padding: '0.85rem 1.15rem',
      borderRadius: '12px',
      background: 'rgba(255, 255, 255, 0.03)',
      border: '1px solid rgba(0, 240, 255, 0.15)',
      marginBottom: '1rem'
    }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
          <span style={{ fontSize: '1rem', animation: isStreaming ? 'pulse 1.2s infinite' : 'none' }}>
            {isStreaming ? '⚡' : '🧠'}
          </span>
          <span style={{
            fontSize: '0.8rem',
            fontWeight: 600,
            letterSpacing: '0.05em',
            textTransform: 'uppercase',
            color: 'var(--accent-cyan)'
          }}>
            Autonomous Agent Thought Stream
          </span>
        </div>
        {isStreaming && (
          <span style={{
            fontSize: '0.75rem',
            color: 'var(--accent-cyan)',
            padding: '2px 8px',
            borderRadius: '999px',
            background: 'rgba(0, 240, 255, 0.1)',
            border: '1px solid rgba(0, 240, 255, 0.3)'
          }}>
            Running
          </span>
        )}
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem', marginTop: '0.25rem' }}>
        {thoughts.map((thought, idx) => (
          <div key={idx} style={{
            fontSize: '0.82rem',
            color: idx === thoughts.length - 1 && isStreaming ? 'var(--text-bright)' : 'var(--text-dim)',
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem'
          }}>
            <span style={{ color: 'var(--accent-cyan)', fontSize: '0.7rem' }}>›</span>
            <span>{thought}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
