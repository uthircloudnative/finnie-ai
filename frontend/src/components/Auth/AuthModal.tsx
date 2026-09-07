import React, { useState } from 'react'
import { useAuth } from '../../context/AuthContext'
import './AuthModal.css'

interface AuthModalProps {
  isOpen: boolean
  onClose?: () => void
}

export const AuthModal: React.FC<AuthModalProps> = ({ isOpen, onClose }) => {
  const { login, register, error } = useAuth()
  const [mode, setMode] = useState<'login' | 'register'>('login')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [fullName, setFullName] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [localError, setLocalError] = useState<string | null>(null)

  if (!isOpen) return null

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLocalError(null)
    if (!email || !password || (mode === 'register' && !fullName)) {
      setLocalError('Please fill in all required fields.')
      return
    }

    setIsSubmitting(true)
    let success = false
    if (mode === 'login') {
      success = await login(email, password)
    } else {
      success = await register(email, password, fullName)
    }
    setIsSubmitting(false)

    if (success && onClose) {
      onClose()
    }
  }

  return (
    <div className="auth-modal-overlay">
      <div className="auth-modal-card glass-card">
        {onClose && (
          <button className="modal-close-btn" onClick={onClose}>
            ✕
          </button>
        )}

        <div className="auth-modal-header">
          <div className="auth-logo-badge">🤖 Finnie AI</div>
          <h2>{mode === 'login' ? 'Welcome Back' : 'Create Your Account'}</h2>
          <p className="auth-modal-subtitle">
            {mode === 'login'
              ? 'Sign in to access your multi-market portfolio insights'
              : 'Join Finnie AI for tailored, multi-market financial guidance'}
          </p>
        </div>

        <div className="auth-mode-tabs">
          <button
            className={`auth-tab-btn ${mode === 'login' ? 'active' : ''}`}
            onClick={() => { setMode('login'); setLocalError(null) }}
          >
            Sign In
          </button>
          <button
            className={`auth-tab-btn ${mode === 'register' ? 'active' : ''}`}
            onClick={() => { setMode('register'); setLocalError(null) }}
          >
            Register
          </button>
        </div>

        {(localError || error) && (
          <div className="auth-error-banner">
            ⚠️ {localError || error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="auth-form">
          {mode === 'register' && (
            <div className="form-group">
              <label>Full Name</label>
              <input
                type="text"
                placeholder="Jane Doe"
                value={fullName}
                onChange={e => setFullName(e.target.value)}
                required
              />
            </div>
          )}

          <div className="form-group">
            <label>Email Address</label>
            <input
              type="email"
              placeholder="investor@finnie.ai"
              value={email}
              onChange={e => setEmail(e.target.value)}
              required
            />
          </div>

          <div className="form-group">
            <label>Password</label>
            <input
              type="password"
              placeholder="••••••••"
              value={password}
              onChange={e => setPassword(e.target.value)}
              required
            />
          </div>

          <button type="submit" className="auth-submit-btn" disabled={isSubmitting}>
            {isSubmitting
              ? 'Connecting...'
              : mode === 'login'
              ? 'Sign In'
              : 'Create Account'}
          </button>
        </form>

        <div className="auth-compliance-footer">
          🔒 Secure 256-bit JWT Encryption · Not Financial Advice ($NFA)
        </div>
      </div>
    </div>
  )
}
