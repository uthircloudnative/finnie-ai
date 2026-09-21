import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { AuthProvider } from '../../../context/AuthContext'
import PortfolioAnalyst from '../PortfolioAnalyst'

describe('PortfolioAnalystFlow Integration Tests', () => {
  beforeEach(() => {
    sessionStorage.clear()
    localStorage.clear()
    sessionStorage.setItem('finnie_auth_token', 'test_jwt_token')
    vi.restoreAllMocks()
  })

  it('renders Portfolio Analyst workspace with risk headers and country filters', async () => {
    globalThis.fetch = vi.fn().mockImplementation((url: string) => {
      if (url.includes('/auth/me')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ id: 'user_1', email: 'test@finnie.ai', full_name: 'Test' })
        })
      }
      if (url.includes('/portfolio/analysis')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({
            analysis: 'Your portfolio exhibits moderate beta and strong diversification.',
            market_beta: 1.15,
            annualized_volatility: 18.5,
            diversification_score: 8.5,
            country: 'US',
            benchmark_name: 'S&P 500 (^GSPC)',
            tickers: ['AAPL', 'MSFT'],
            vol_thresholds: [15, 25]
          })
        })
      }
      return Promise.reject(new Error(`Unhandled: ${url}`))
    })

    render(
      <AuthProvider>
        <PortfolioAnalyst />
      </AuthProvider>
    )

    expect(await screen.findByRole('heading', { name: /Portfolio Analyst/i })).toBeInTheDocument()
    expect(screen.getByText(/Deep risk analysis fueled by yfinance/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Ask Finnie/i })).toBeInTheDocument()
  })
})
