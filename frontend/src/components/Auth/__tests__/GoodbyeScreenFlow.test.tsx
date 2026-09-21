import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { AuthProvider } from '../../../context/AuthContext'
import App from '../../../App'

describe('SPEC-07: Goodbye Confirmation Page & Session Termination Flow', () => {
  beforeEach(() => {
    sessionStorage.clear()
    localStorage.clear()
    vi.restoreAllMocks()
  })

  it('AC-1, AC-2, AC-3, AC-5: Signing out presents GoodbyeScreen with generic reassurance and single Log In button', async () => {
    const user = userEvent.setup()

    // 1. Simulate an existing active session in sessionStorage
    sessionStorage.setItem('finnie_auth_token', 'valid_authenticated_jwt')

    globalThis.fetch = vi.fn().mockImplementation((url: string) => {
      if (url.includes('/auth/me')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({
            id: 'user_active',
            email: 'investor@finnie.ai',
            full_name: 'Prajosh Investor',
            base_currency: 'USD'
          })
        })
      }
      return Promise.reject(new Error(`Unhandled URL: ${url}`))
    })

    render(
      <AuthProvider>
        <App />
      </AuthProvider>
    )

    // Wait for the authenticated user to be visible in the sidebar
    await waitFor(() => {
      expect(screen.getByText('👤 Prajosh Investor')).toBeInTheDocument()
    })

    // 2. Click "Sign Out"
    const signOutBtn = screen.getByRole('button', { name: /Sign Out/i })
    await user.click(signOutBtn)

    // 3. Verify GoodbyeScreen is displayed (AC-1)
    expect(await screen.findByRole('heading', { name: /See you soon! 👋/i })).toBeInTheDocument()

    // 4. Verify generic reassurance copy and security status badge (AC-2)
    expect(screen.getByText(/Your financial information and portfolio data are stored securely\./i)).toBeInTheDocument()
    expect(screen.getByText(/Session ended securely · All data protected/i)).toBeInTheDocument()
    expect(screen.getByText(/Close your browser tab if you are on a shared computer/i)).toBeInTheDocument()
    expect(screen.getByText(/Not Financial Advice \(\$NFA\)/i)).toBeInTheDocument()

    // 5. Verify single Log In button is present and NO "Another User" button exists (AC-3)
    const logInBtns = screen.getAllByRole('button', { name: /Log In/i })
    expect(logInBtns.length).toBe(1)
    expect(screen.queryByRole('button', { name: /another user/i })).toBeNull()

    // 6. Verify sessionStorage and localStorage have been purged (AC-5)
    expect(sessionStorage.getItem('finnie_auth_token')).toBeNull()
    expect(localStorage.getItem('finnie_auth_token')).toBeNull()
  })

  it('AC-4: Clicking Log In on GoodbyeScreen transitions back to the Login Modal', async () => {
    const user = userEvent.setup()

    // 1. Simulate an active session
    sessionStorage.setItem('finnie_auth_token', 'valid_authenticated_jwt')

    globalThis.fetch = vi.fn().mockImplementation((url: string) => {
      if (url.includes('/auth/me')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({
            id: 'user_active',
            email: 'investor@finnie.ai',
            full_name: 'Prajosh Investor',
            base_currency: 'USD'
          })
        })
      }
      return Promise.reject(new Error(`Unhandled URL: ${url}`))
    })

    render(
      <AuthProvider>
        <App />
      </AuthProvider>
    )

    await waitFor(() => {
      expect(screen.getByText('👤 Prajosh Investor')).toBeInTheDocument()
    })

    // Sign out
    await user.click(screen.getByRole('button', { name: /Sign Out/i }))

    // Confirm goodbye screen is visible
    const logInBtn = await screen.findByRole('button', { name: /Log In/i })
    expect(logInBtn).toBeInTheDocument()

    // 2. Click "Log In" button
    await user.click(logInBtn)

    // 3. Assert AuthModal opens with Login prompt
    await waitFor(() => {
      expect(screen.getByRole('heading', { name: /Welcome Back/i })).toBeInTheDocument()
      expect(screen.getByPlaceholderText('investor@finnie.ai')).toBeInTheDocument()
    })
  })

  it('AC-4b: Logging in after GoodbyeScreen immediately closes the modal without presenting a second login screen', async () => {
    const user = userEvent.setup()

    // 1. Initial session
    sessionStorage.setItem('finnie_auth_token', 'initial_token')

    globalThis.fetch = vi.fn().mockImplementation((url: string) => {
      if (url.includes('/auth/me')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({
            id: 'user_active',
            email: 'investor@finnie.ai',
            full_name: 'Prajosh Investor',
            base_currency: 'USD'
          })
        })
      }
      if (url.includes('/auth/login')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({
            access_token: 'relogged_token_789',
            token_type: 'bearer',
            user: {
              id: 'user_active',
              email: 'investor@finnie.ai',
              full_name: 'Prajosh Investor',
              base_currency: 'USD'
            }
          })
        })
      }
      return Promise.reject(new Error(`Unhandled URL: ${url}`))
    })

    render(
      <AuthProvider>
        <App />
      </AuthProvider>
    )

    await waitFor(() => {
      expect(screen.getByText('👤 Prajosh Investor')).toBeInTheDocument()
    })

    // Sign out to reach GoodbyeScreen
    await user.click(screen.getByRole('button', { name: /Sign Out/i }))
    expect(await screen.findByRole('heading', { name: /See you soon! 👋/i })).toBeInTheDocument()

    // Click Log In on GoodbyeScreen
    await user.click(screen.getByRole('button', { name: /Log In/i }))

    // Type credentials
    const emailInput = await screen.findByPlaceholderText('investor@finnie.ai')
    const passwordInput = screen.getByPlaceholderText('••••••••')
    await user.type(emailInput, 'investor@finnie.ai')
    await user.type(passwordInput, 'securePassword123')

    // Submit login
    const submitBtn = screen.getByTestId('auth-submit-btn')
    await user.click(submitBtn)

    // Verify modal is dismissed completely, NOT presented again
    await waitFor(() => {
      expect(screen.queryByRole('heading', { name: /Welcome Back/i })).toBeNull()
      expect(screen.getByText('👤 Prajosh Investor')).toBeInTheDocument()
    })
  })
})
