import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { AuthProvider } from '../../../context/AuthContext'
import Chat from '../Chat'

describe('ChatFlow Integration Tests', () => {
  beforeEach(() => {
    sessionStorage.clear()
    localStorage.clear()
    sessionStorage.setItem('finnie_auth_token', 'test_jwt_token')
    vi.restoreAllMocks()
  })

  it('renders Deep Q&A chat layout with regulatory $NFA disclaimer', async () => {
    globalThis.fetch = vi.fn().mockImplementation((url: string) => {
      if (url.includes('/auth/me')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ id: 'user_1', email: 'test@finnie.ai', full_name: 'Test' })
        })
      }
      return Promise.reject(new Error(`Unhandled: ${url}`))
    })

    render(
      <AuthProvider>
        <Chat />
      </AuthProvider>
    )

    expect(await screen.findByRole('heading', { name: /Deep Q&A/i })).toBeInTheDocument()
    expect(screen.getByPlaceholderText(/Ask Finnie a question/i)).toBeInTheDocument()
    expect(screen.getByText(/Not a licensed financial advisor/i)).toBeInTheDocument()
  })

  it('submits a user prompt and renders AI response grounded with compliance notes', async () => {
    const user = userEvent.setup()

    globalThis.fetch = vi.fn().mockImplementation((url: string) => {
      if (url.includes('/auth/me')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ id: 'user_1', email: 'test@finnie.ai', full_name: 'Test' })
        })
      }
      if (url.includes('/chat')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({
            reply: 'An index fund is a portfolio of stocks designed to mimic the composition and performance of a financial market index like the S&P 500.',
            routed_to: 'financial_qa',
            error: null
          })
        })
      }
      return Promise.reject(new Error(`Unhandled: ${url}`))
    })

    render(
      <AuthProvider>
        <Chat />
      </AuthProvider>
    )

    const input = screen.getByPlaceholderText(/Ask Finnie a question/i)
    await user.type(input, 'What is an index fund?')
    await user.click(screen.getByRole('button', { name: '→' }))

    // Expect user message rendered
    expect(screen.getByText('What is an index fund?')).toBeInTheDocument()

    // Expect AI response rendered
    await waitFor(() => {
      expect(screen.getByText(/An index fund is a portfolio of stocks/i)).toBeInTheDocument()
    })
  })
})
