import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { AuthProvider, useAuth } from '../../../context/AuthContext'
import { AuthModal } from '../AuthModal'
import App from '../../../App'

// Test harness component to inspect AuthContext state
const TestAuthConsumer = () => {
  const { user, token, isAuthenticated, logout, login } = useAuth()
  return (
    <div>
      <div data-testid="auth-status">{isAuthenticated ? 'AUTHENTICATED' : 'UNAUTHENTICATED'}</div>
      <div data-testid="token-val">{token || 'NO_TOKEN'}</div>
      <div data-testid="user-name">{user?.full_name || 'NO_USER'}</div>
      <button onClick={() => login('investor@finnie.ai', 'password123')}>Test Login</button>
      <button onClick={logout}>Test Logout</button>
    </div>
  )
}

describe('SPEC-06: Session-Scoped Authentication & Login Gate Integration', () => {
  beforeEach(() => {
    sessionStorage.clear()
    localStorage.clear()
    vi.restoreAllMocks()
  })

  it('AC-2 & AC-4: Unauthenticated visit displays AuthModal in mandatory gate mode (no close button)', async () => {
    // When visiting without session token
    render(
      <AuthProvider>
        <App />
      </AuthProvider>
    )

    // The login modal header must be visible
    expect(await screen.findByRole('heading', { name: /Welcome Back/i })).toBeInTheDocument()
    expect(screen.getByPlaceholderText('investor@finnie.ai')).toBeInTheDocument()

    // The close button (✕) MUST NOT exist in gate mode
    const closeBtn = screen.queryByRole('button', { name: '✕' })
    expect(closeBtn).toBeNull()
  })

  it('AC-1: Successful login saves token to sessionStorage and cleans up legacy localStorage', async () => {
    const user = userEvent.setup()

    // Put a stale legacy token in localStorage to verify cleanup
    localStorage.setItem('finnie_auth_token', 'stale_legacy_token')

    // Mock login and profile endpoints
    globalThis.fetch = vi.fn().mockImplementation((url: string) => {
      if (url.includes('/auth/login')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({
            access_token: 'fresh_session_jwt_token_123',
            token_type: 'bearer',
            user: {
              id: 'user_456',
              email: 'investor@finnie.ai',
              full_name: 'Test Investor',
              base_currency: 'USD'
            }
          })
        })
      }
      if (url.includes('/auth/me')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({
            id: 'user_456',
            email: 'investor@finnie.ai',
            full_name: 'Test Investor',
            base_currency: 'USD'
          })
        })
      }
      return Promise.reject(new Error(`Unhandled URL: ${url}`))
    })

    render(
      <AuthProvider>
        <TestAuthConsumer />
      </AuthProvider>
    )

    // Legacy localStorage token must have been cleaned up on mount
    expect(localStorage.getItem('finnie_auth_token')).toBeNull()

    // Trigger login
    await user.click(screen.getByRole('button', { name: 'Test Login' }))

    // Assert sessionStorage has fresh token
    await waitFor(() => {
      expect(sessionStorage.getItem('finnie_auth_token')).toBe('fresh_session_jwt_token_123')
      expect(screen.getByTestId('auth-status')).toHaveTextContent('AUTHENTICATED')
      expect(screen.getByTestId('user-name')).toHaveTextContent('Test Investor')
    })

    // Confirm localStorage remains clean
    expect(localStorage.getItem('finnie_auth_token')).toBeNull()
  })

  it('AC-3: Active tab rehydration restores session from sessionStorage', async () => {
    // Simulate user already having active session in sessionStorage
    sessionStorage.setItem('finnie_auth_token', 'valid_tab_session_jwt')

    // Mock /auth/me profile verification
    globalThis.fetch = vi.fn().mockImplementation((url: string) => {
      if (url.includes('/auth/me')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({
            id: 'user_rehydrated',
            email: 'rehydrated@finnie.ai',
            full_name: 'Rehydrated Investor',
            base_currency: 'USD'
          })
        })
      }
      return Promise.reject(new Error(`Unhandled URL: ${url}`))
    })

    render(
      <AuthProvider>
        <TestAuthConsumer />
      </AuthProvider>
    )

    await waitFor(() => {
      expect(screen.getByTestId('auth-status')).toHaveTextContent('AUTHENTICATED')
      expect(screen.getByTestId('user-name')).toHaveTextContent('Rehydrated Investor')
    })
  })

  it('AC-5: Explicit sign out purges sessionStorage and localStorage and resets state', async () => {
    const user = userEvent.setup()
    sessionStorage.setItem('finnie_auth_token', 'active_session_token')
    localStorage.setItem('finnie_auth_token', 'defensive_token')

    globalThis.fetch = vi.fn().mockImplementation((url: string) => {
      if (url.includes('/auth/me')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({
            id: 'user_active',
            email: 'active@finnie.ai',
            full_name: 'Active Investor',
            base_currency: 'USD'
          })
        })
      }
      return Promise.reject(new Error(`Unhandled URL: ${url}`))
    })

    render(
      <AuthProvider>
        <TestAuthConsumer />
      </AuthProvider>
    )

    await waitFor(() => {
      expect(screen.getByTestId('auth-status')).toHaveTextContent('AUTHENTICATED')
    })

    // Click Sign Out
    await user.click(screen.getByRole('button', { name: 'Test Logout' }))

    // Assert both storages are purged
    expect(sessionStorage.getItem('finnie_auth_token')).toBeNull()
    expect(localStorage.getItem('finnie_auth_token')).toBeNull()
    expect(screen.getByTestId('auth-status')).toHaveTextContent('UNAUTHENTICATED')
  })

  it('AC-4: Authenticated user opening AuthModal can dismiss it via close button', async () => {
    const onCloseMock = vi.fn()

    // Pre-populate sessionStorage with active token
    sessionStorage.setItem('finnie_auth_token', 'active_token')

    globalThis.fetch = vi.fn().mockImplementation((url: string) => {
      if (url.includes('/auth/me')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({
            id: 'user_active',
            email: 'active@finnie.ai',
            full_name: 'Active Investor',
            base_currency: 'USD'
          })
        })
      }
      return Promise.reject(new Error(`Unhandled URL: ${url}`))
    })

    render(
      <AuthProvider>
        <AuthModal
          isOpen={true}
          onClose={onCloseMock}
        />
      </AuthProvider>
    )

    // Close button should be rendered once authenticated
    const closeBtn = await screen.findByRole('button', { name: '✕' })
    expect(closeBtn).toBeInTheDocument()

    await userEvent.click(closeBtn)
    expect(onCloseMock).toHaveBeenCalledTimes(1)
  })
})

describe('SPEC-08: Forgot Password Flow & Security Audit UI Integration', () => {
  beforeEach(() => {
    sessionStorage.clear()
    localStorage.clear()
    vi.restoreAllMocks()
  })

  it('AC-9 & AC-14: Clicking "Forgot password?" navigates to code request step, and "← Back to Sign In" returns to login', async () => {
    const user = userEvent.setup()

    render(
      <AuthProvider>
        <AuthModal isOpen={true} />
      </AuthProvider>
    )

    // Initially in Login mode
    expect(screen.getByRole('heading', { name: /Welcome Back/i })).toBeInTheDocument()

    // Click "Forgot password?"
    const forgotLink = screen.getByRole('button', { name: /Forgot password\?/i })
    await user.click(forgotLink)

    // Heading changes to "Reset Your Password"
    expect(screen.getByRole('heading', { name: /Reset Your Password/i })).toBeInTheDocument()
    expect(screen.getByTestId('auth-request-code-btn')).toBeInTheDocument()

    // Click "← Back to Sign In"
    const backBtn = screen.getByRole('button', { name: /← Back to Sign In/i })
    await user.click(backBtn)

    // Returns to Login mode
    expect(screen.getByRole('heading', { name: /Welcome Back/i })).toBeInTheDocument()
  })

  it('AC-10: Submitting email transitions to verify_and_reset view with 6-digit OTP input and cooldown', async () => {
    const user = userEvent.setup()

    globalThis.fetch = vi.fn().mockImplementation((url: string) => {
      if (url.includes('/auth/forgot-password')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({
            message: 'If the email exists, a verification code has been sent.',
            expires_in_minutes: 15
          })
        })
      }
      return Promise.reject(new Error(`Unhandled URL: ${url}`))
    })

    render(
      <AuthProvider>
        <AuthModal isOpen={true} />
      </AuthProvider>
    )

    // Navigate to Forgot Password
    await user.click(screen.getByRole('button', { name: /Forgot password\?/i }))

    // Type email and submit
    const emailInput = screen.getByPlaceholderText('investor@finnie.ai')
    await user.type(emailInput, 'investor@finnie.ai')
    await user.click(screen.getByTestId('auth-request-code-btn'))

    // Transitions to verify_and_reset view
    await waitFor(() => {
      expect(screen.getByRole('heading', { name: /Enter Security Code/i })).toBeInTheDocument()
      expect(screen.getByTestId('auth-otp-input')).toBeInTheDocument()
      expect(screen.getByTestId('auth-reset-submit-btn')).toBeInTheDocument()
    })

    // Resend button should show active cooldown
    expect(screen.getByTestId('auth-resend-btn')).toBeDisabled()
  })

  it('AC-11: Validates short password and mismatched confirmation client-side', async () => {
    const user = userEvent.setup()

    globalThis.fetch = vi.fn().mockImplementation((url: string) => {
      if (url.includes('/auth/forgot-password')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ message: 'Code sent', expires_in_minutes: 15 })
        })
      }
      return Promise.reject(new Error(`Unhandled URL: ${url}`))
    })

    render(
      <AuthProvider>
        <AuthModal isOpen={true} />
      </AuthProvider>
    )

    // Advance to verify_and_reset
    await user.click(screen.getByRole('button', { name: /Forgot password\?/i }))
    await user.type(screen.getByPlaceholderText('investor@finnie.ai'), 'investor@finnie.ai')
    await user.click(screen.getByTestId('auth-request-code-btn'))

    await waitFor(() => {
      expect(screen.getByTestId('auth-otp-input')).toBeInTheDocument()
    })

    // Type incomplete OTP (< 6 digits)
    await user.type(screen.getByTestId('auth-otp-input'), '123')
    const passwordInputs = screen.getAllByPlaceholderText('••••••••••••')
    await user.type(passwordInputs[0], 'short')
    await user.type(passwordInputs[1], 'short')
    await user.click(screen.getByTestId('auth-reset-submit-btn'))

    expect(screen.getByText(/Please enter the complete 6-digit verification code/i)).toBeInTheDocument()

    // Complete 6 digits, but short password
    await user.type(screen.getByTestId('auth-otp-input'), '456')
    await user.click(screen.getByTestId('auth-reset-submit-btn'))
    expect(screen.getByText(/New password must be at least 8 characters long/i)).toBeInTheDocument()

    // Password mismatch
    await user.clear(passwordInputs[0])
    await user.type(passwordInputs[0], 'ValidPass123')
    await user.clear(passwordInputs[1])
    await user.type(passwordInputs[1], 'MismatchPass456')
    await user.click(screen.getByTestId('auth-reset-submit-btn'))
    expect(screen.getByText(/Passwords do not match/i)).toBeInTheDocument()
  })

  it('AC-12 & AC-13: Successful password reset shows success screen and returns to sign in', async () => {
    const user = userEvent.setup()

    globalThis.fetch = vi.fn().mockImplementation((url: string) => {
      if (url.includes('/auth/forgot-password')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ message: 'Code sent', expires_in_minutes: 15 })
        })
      }
      if (url.includes('/auth/reset-password')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({
            message: 'Password has been reset successfully. Please sign in with your new credentials.'
          })
        })
      }
      return Promise.reject(new Error(`Unhandled URL: ${url}`))
    })

    render(
      <AuthProvider>
        <AuthModal isOpen={true} />
      </AuthProvider>
    )

    // Advance to step 2
    await user.click(screen.getByRole('button', { name: /Forgot password\?/i }))
    await user.type(screen.getByPlaceholderText('investor@finnie.ai'), 'investor@finnie.ai')
    await user.click(screen.getByTestId('auth-request-code-btn'))

    await waitFor(() => {
      expect(screen.getByTestId('auth-otp-input')).toBeInTheDocument()
    })

    // Fill valid form
    await user.type(screen.getByTestId('auth-otp-input'), '654321')
    const passwordInputs = screen.getAllByPlaceholderText('••••••••••••')
    await user.type(passwordInputs[0], 'BrandNewSecurePassword123')
    await user.type(passwordInputs[1], 'BrandNewSecurePassword123')
    await user.click(screen.getByTestId('auth-reset-submit-btn'))

    // Should transition to success screen
    await waitFor(() => {
      expect(screen.getByRole('heading', { name: /Password Reset Complete!/i })).toBeInTheDocument()
      expect(screen.getByTestId('auth-proceed-login-btn')).toBeInTheDocument()
    })

    // Clicking Proceed to Sign In returns to login
    await user.click(screen.getByTestId('auth-proceed-login-btn'))
    expect(screen.getByRole('heading', { name: /Welcome Back/i })).toBeInTheDocument()
  })
})

