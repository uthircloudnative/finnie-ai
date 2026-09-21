import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { AuthProvider } from '../../../context/AuthContext'
import MarketInsights from '../MarketInsights'

describe('MarketInsightsFlow Integration Tests', () => {
  beforeEach(() => {
    sessionStorage.clear()
    localStorage.clear()
    sessionStorage.setItem('finnie_auth_token', 'test_jwt_token')
    vi.restoreAllMocks()
  })

  it('renders Market Insights workspace with real-time sentiment headers', async () => {
    globalThis.fetch = vi.fn().mockImplementation((url: string) => {
      if (url.includes('/auth/me')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ id: 'user_1', email: 'test@finnie.ai', full_name: 'Test' })
        })
      }
      if (url.includes('/market/news')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({
            reply: 'Tech Stocks Rally on Strong AI Demand. Bullish momentum observed across major holdings.'
          })
        })
      }
      return Promise.reject(new Error(`Unhandled: ${url}`))
    })

    render(
      <AuthProvider>
        <MarketInsights />
      </AuthProvider>
    )

    expect(await screen.findByRole('heading', { name: /Market Insights/i })).toBeInTheDocument()
    expect(screen.getByText(/Real-time sentiment and news analysis/i)).toBeInTheDocument()
    expect(screen.getByText(/Tech Stocks Rally on Strong AI Demand/i)).toBeInTheDocument()
    expect(screen.getAllByText(/Bullish/i).length).toBeGreaterThanOrEqual(1)
  })
})
