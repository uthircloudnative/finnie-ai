import { GoalConfig } from '../../hooks/useGoalStrategist'

interface StrategyLockInModalProps {
  isOpen: boolean
  onClose: () => void
  onConfirm: () => Promise<void>
  goal: GoalConfig | null
  confidenceScore: number
  isLoading: boolean
}

export default function StrategyLockInModal({
  isOpen,
  onClose,
  onConfirm,
  goal,
  confidenceScore,
  isLoading
}: StrategyLockInModalProps) {
  if (!isOpen || !goal) return null

  return (
    <div style={{
      position: 'fixed',
      inset: 0,
      background: 'rgba(0, 0, 0, 0.75)',
      backdropFilter: 'blur(8px)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 1000,
      padding: '1rem'
    }}>
      <div className="glass-card" style={{
        maxWidth: '520px',
        width: '100%',
        borderRadius: '20px',
        border: '1px solid var(--accent-cyan)',
        boxShadow: '0 20px 50px rgba(0, 240, 255, 0.15)',
        padding: '2rem',
        background: '#0d1117'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1.25rem' }}>
          <span style={{ fontSize: '1.8rem' }}>🔒</span>
          <div>
            <h2 style={{ margin: 0, fontSize: '1.35rem', color: 'var(--text-bright)' }}>
              Lock In Strategy
            </h2>
            <p style={{ margin: '0.2rem 0 0 0', fontSize: '0.85rem', color: 'var(--text-dim)' }}>
              Human-in-the-Loop Final Audit & Sign-off
            </p>
          </div>
        </div>

        <div style={{
          background: 'rgba(255, 255, 255, 0.03)',
          border: '1px solid var(--glass-border)',
          borderRadius: '12px',
          padding: '1.2rem',
          marginBottom: '1.5rem',
          display: 'flex',
          flexDirection: 'column',
          gap: '0.75rem',
          fontSize: '0.9rem'
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span style={{ color: 'var(--text-dim)' }}>Goal Name</span>
            <strong style={{ color: 'var(--accent-cyan)' }}>{goal.goal_name}</strong>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span style={{ color: 'var(--text-dim)' }}>Target Amount</span>
            <strong style={{ color: 'var(--text-bright)' }}>${goal.target_amount.toLocaleString()}</strong>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span style={{ color: 'var(--text-dim)' }}>Realization Year</span>
            <strong style={{ color: 'var(--text-bright)' }}>{goal.target_year}</strong>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span style={{ color: 'var(--text-dim)' }}>Monthly Savings Rate</span>
            <strong style={{ color: 'var(--text-bright)' }}>${goal.monthly_savings.toLocaleString()} / mo</strong>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span style={{ color: 'var(--text-dim)' }}>Audited Confidence Score</span>
            <strong style={{ color: confidenceScore >= 75 ? 'var(--accent-emerald)' : 'var(--accent-cyan)' }}>
              {confidenceScore.toFixed(1)}%
            </strong>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span style={{ color: 'var(--text-dim)' }}>Statutory Jurisdiction</span>
            <strong style={{ color: 'var(--text-bright)' }}>{goal.country} Tax Standards</strong>
          </div>
        </div>

        <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)', lineHeight: 1.5, marginBottom: '1.5rem' }}>
          Locking in persists this audited financial roadmap to your active account and activates ongoing portfolio variance tracking. You can revisit and refine this strategy at any time.
        </p>

        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem' }}>
          <button
            type="button"
            onClick={onClose}
            disabled={isLoading}
            style={{
              padding: '0.7rem 1.25rem',
              borderRadius: '10px',
              background: 'rgba(255, 255, 255, 0.05)',
              border: '1px solid var(--glass-border)',
              color: 'var(--text-dim)',
              cursor: isLoading ? 'not-allowed' : 'pointer',
              fontWeight: 500
            }}
          >
            Cancel
          </button>
          <button
            type="button"
            className="calculate-btn"
            onClick={onConfirm}
            disabled={isLoading}
            style={{
              padding: '0.7rem 1.5rem',
              borderRadius: '10px',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              cursor: isLoading ? 'not-allowed' : 'pointer',
              fontWeight: 600
            }}
          >
            {isLoading ? 'Locking In...' : 'Confirm & Lock In 🔒'}
          </button>
        </div>
      </div>
    </div>
  )
}
