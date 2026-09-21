import React, { useState, useEffect } from 'react'
import { useAuth } from '../../context/AuthContext'
import './AuthModal.css'

interface AuthModalProps {
  isOpen: boolean
  onClose?: () => void
}

type AuthMode = 'login' | 'register' | 'forgot'
type ForgotStep = 'request_code' | 'verify_and_reset' | 'success'

export const AuthModal: React.FC<AuthModalProps> = ({ isOpen, onClose }) => {
  const { login, register, error, isAuthenticated, requestPasswordReset, resetPassword } = useAuth()
  const [mode, setMode] = useState<AuthMode>('login')
  const [forgotStep, setForgotStep] = useState<ForgotStep>('request_code')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [code, setCode] = useState('')
  const [fullName, setFullName] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [localError, setLocalError] = useState<string | null>(null)
  const [cooldown, setCooldown] = useState(0)

  // 60-second cooldown timer for resending OTP
  useEffect(() => {
    if (cooldown <= 0) return
    const timer = setInterval(() => {
      setCooldown(prev => (prev > 1 ? prev - 1 : 0))
    }, 1000)
    return () => clearInterval(timer)
  }, [cooldown])

  if (!isOpen) return null

  const handleModeChange = (newMode: AuthMode) => {
    setMode(newMode)
    setLocalError(null)
    if (newMode === 'forgot') {
      setForgotStep('request_code')
    }
  }

  const handleLoginOrRegister = async (e: React.FormEvent) => {
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

    if (success) {
      setEmail('')
      setPassword('')
      setConfirmPassword('')
      setCode('')
      setFullName('')
      setLocalError(null)
      if (onClose) {
        onClose()
      }
    }
  }

  const handleRequestCode = async (e: React.FormEvent) => {
    e.preventDefault()
    setLocalError(null)
    if (!email.trim()) {
      setLocalError('Please enter your email address.')
      return
    }

    setIsSubmitting(true)
    const res = await requestPasswordReset(email.trim())
    setIsSubmitting(false)

    if (res.success) {
      setForgotStep('verify_and_reset')
      setCooldown(60)
    } else {
      setLocalError(res.message || 'Failed to send verification code.')
    }
  }

  const handleResendCode = async () => {
    if (cooldown > 0 || isSubmitting) return
    setLocalError(null)
    setIsSubmitting(true)
    const res = await requestPasswordReset(email.trim())
    setIsSubmitting(false)

    if (res.success) {
      setCooldown(60)
    } else {
      setLocalError(res.message || 'Failed to resend verification code.')
    }
  }

  const handleResetPassword = async (e: React.FormEvent) => {
    e.preventDefault()
    setLocalError(null)

    if (!code.trim() || code.trim().length !== 6) {
      setLocalError('Please enter the complete 6-digit verification code.')
      return
    }
    if (password.length < 8) {
      setLocalError('New password must be at least 8 characters long.')
      return
    }
    if (password !== confirmPassword) {
      setLocalError('Passwords do not match.')
      return
    }

    setIsSubmitting(true)
    const res = await resetPassword(email.trim(), code.trim(), password)
    setIsSubmitting(false)

    if (res.success) {
      setForgotStep('success')
    } else {
      setLocalError(res.message || 'Password reset failed.')
    }
  }

  return (
    <div className={`auth-modal-overlay ${!isAuthenticated ? 'gate-mode' : ''}`}>
      <div className="auth-modal-card glass-card">
        {isAuthenticated && onClose && (
          <button className="modal-close-btn" onClick={onClose}>
            ✕
          </button>
        )}

        {/* ── Header ──────────────────────────────────────────────── */}
        <div className="auth-modal-header">
          <div className="auth-logo-badge">🤖 Finnie AI</div>
          <h2>
            {mode === 'login'
              ? 'Welcome Back'
              : mode === 'register'
              ? 'Create Your Account'
              : forgotStep === 'success'
              ? 'Password Reset Complete! 🎉'
              : forgotStep === 'verify_and_reset'
              ? 'Enter Security Code'
              : 'Reset Your Password'}
          </h2>
          <p className="auth-modal-subtitle">
            {mode === 'login'
              ? 'Sign in to access your multi-market portfolio insights'
              : mode === 'register'
              ? 'Join Finnie AI for tailored, multi-market financial guidance'
              : forgotStep === 'success'
              ? 'Your password has been updated securely. Sign in to continue.'
              : forgotStep === 'verify_and_reset'
              ? `Verification code sent to ${email}. Valid for 15 minutes.`
              : 'Enter your account email to receive a 6-digit verification code'}
          </p>
        </div>

        {/* ── Tabs (Only shown in login / register modes) ─────────── */}
        {mode !== 'forgot' && (
          <div className="auth-mode-tabs">
            <button
              className={`auth-tab-btn ${mode === 'login' ? 'active' : ''}`}
              onClick={() => handleModeChange('login')}
            >
              Sign In
            </button>
            <button
              className={`auth-tab-btn ${mode === 'register' ? 'active' : ''}`}
              onClick={() => handleModeChange('register')}
            >
              Register
            </button>
          </div>
        )}

        {/* ── Error Banner ────────────────────────────────────────── */}
        {(localError || error) && (
          <div className="auth-error-banner">
            ⚠️ {localError || error}
          </div>
        )}

        {/* ── Mode 1 & 2: Login / Register Form ──────────────────── */}
        {mode !== 'forgot' && (
          <form onSubmit={handleLoginOrRegister} className="auth-form">
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
              <div className="auth-label-row">
                <label>Password</label>
                {mode === 'login' && (
                  <button
                    type="button"
                    className="auth-link-inline"
                    onClick={() => handleModeChange('forgot')}
                  >
                    Forgot password?
                  </button>
                )}
              </div>
              <input
                type="password"
                placeholder="••••••••"
                value={password}
                onChange={e => setPassword(e.target.value)}
                required
              />
            </div>

            <button
              type="submit"
              className="auth-submit-btn"
              data-testid="auth-submit-btn"
              disabled={isSubmitting}
            >
              {isSubmitting
                ? 'Connecting...'
                : mode === 'login'
                ? 'Sign In'
                : 'Create Account'}
            </button>
          </form>
        )}

        {/* ── Mode 3, Step 1: Forgot Password — Request Code ──────── */}
        {mode === 'forgot' && forgotStep === 'request_code' && (
          <form onSubmit={handleRequestCode} className="auth-form">
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

            <button
              type="submit"
              className="auth-submit-btn"
              data-testid="auth-request-code-btn"
              disabled={isSubmitting}
            >
              {isSubmitting ? 'Sending Code...' : '📧 Send Verification Code'}
            </button>

            <button
              type="button"
              className="auth-back-btn"
              onClick={() => handleModeChange('login')}
            >
              ← Back to Sign In
            </button>
          </form>
        )}

        {/* ── Mode 3, Step 2: Forgot Password — Verify Code & Reset ── */}
        {mode === 'forgot' && forgotStep === 'verify_and_reset' && (
          <form onSubmit={handleResetPassword} className="auth-form">
            <div className="form-group">
              <label>6-Digit Security Code</label>
              <input
                type="text"
                className="auth-code-input"
                data-testid="auth-otp-input"
                maxLength={6}
                placeholder="123456"
                value={code}
                onChange={e => setCode(e.target.value.replace(/\D/g, ''))}
                required
              />
            </div>

            <div className="form-group">
              <label>New Password (min. 8 characters)</label>
              <input
                type="password"
                placeholder="••••••••••••"
                value={password}
                onChange={e => setPassword(e.target.value)}
                required
              />
            </div>

            <div className="form-group">
              <label>Confirm New Password</label>
              <input
                type="password"
                placeholder="••••••••••••"
                value={confirmPassword}
                onChange={e => setConfirmPassword(e.target.value)}
                required
              />
            </div>

            <div className="auth-resend-row">
              <button
                type="button"
                className="auth-resend-btn"
                data-testid="auth-resend-btn"
                disabled={cooldown > 0 || isSubmitting}
                onClick={handleResendCode}
              >
                {cooldown > 0
                  ? `Resend code in ${cooldown}s`
                  : "Didn't receive code? Resend Code"}
              </button>
            </div>

            <button
              type="submit"
              className="auth-submit-btn"
              data-testid="auth-reset-submit-btn"
              disabled={isSubmitting}
            >
              {isSubmitting ? 'Resetting Password...' : '🔒 Reset Password'}
            </button>

            <button
              type="button"
              className="auth-back-btn"
              onClick={() => handleModeChange('login')}
            >
              ← Back to Sign In
            </button>
          </form>
        )}

        {/* ── Mode 3, Step 3: Success Screen ──────────────────────── */}
        {mode === 'forgot' && forgotStep === 'success' && (
          <div className="auth-success-view">
            <div className="auth-success-icon">✅</div>
            <p className="auth-success-text">
              Your password has been reset successfully. Please sign in with your new credentials.
            </p>
            <button
              type="button"
              className="auth-submit-btn"
              data-testid="auth-proceed-login-btn"
              onClick={() => {
                setPassword('')
                setConfirmPassword('')
                setCode('')
                setLocalError(null)
                handleModeChange('login')
              }}
            >
              🔑 Proceed to Sign In
            </button>
          </div>
        )}

        <div className="auth-compliance-footer">
          🔒 Secure 256-bit JWT Encryption · Not Financial Advice ($NFA)
        </div>
      </div>
    </div>
  )
}
