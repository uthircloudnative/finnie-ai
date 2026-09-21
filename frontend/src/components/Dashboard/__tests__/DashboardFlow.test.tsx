import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { AuthProvider } from '../../../context/AuthContext'
import Dashboard from '../Dashboard'

describe('DashboardFlow Integration Tests', () => {
  beforeEach(() => {
    sessionStorage.clear()
    localStorage.clear()
    sessionStorage.setItem('finnie_auth_token', 'test_jwt_token')
    vi.restoreAllMocks()
  })

  it('renders empty state when user has 0 assets', async () => {
    globalThis.fetch = vi.fn().mockImplementation((url: string) => {
      if (url.includes('/auth/me')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ id: 'user_1', email: 'test@finnie.ai', full_name: 'Test' })
        })
      }
      if (url.includes('/dashboard')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({
            total_assets: 0,
            total_countries: 0,
            portfolios: {}
          })
        })
      }
      return Promise.reject(new Error(`Unhandled: ${url}`))
    })

    render(
      <AuthProvider>
        <Dashboard />
      </AuthProvider>
    )

    expect(await screen.findByText(/Your Global Wealth Tracker/i)).toBeInTheDocument()
    expect(screen.getByText(/Head over to/i)).toBeInTheDocument()
  })

  it('renders localized wealth metrics and asset breakdown on successful data fetch', async () => {
    globalThis.fetch = vi.fn().mockImplementation((url: string) => {
      if (url.includes('/auth/me')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ id: 'user_1', email: 'test@finnie.ai', full_name: 'Test' })
        })
      }
      if (url.includes('/dashboard')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({
            total_assets: 2,
            total_countries: 1,
            portfolios: {
              US: {
                country_code: 'US',
                total_value: 15420.50,
                daily_pnl: 320.10,
                daily_pnl_percent: 2.12,
                assets: [
                  {
                    ticker: 'AAPL',
                    shares: 50,
                    current_price: 220.50,
                    prev_close: 215.00,
                    asset_pnl: 275.00,
                    asset_pnl_percent: 2.56,
                    total_value: 11025.00
                  }
                ]
              }
            }
          })
        })
      }
      return Promise.reject(new Error(`Unhandled: ${url}`))
    })

    render(
      <AuthProvider>
        <Dashboard />
      </AuthProvider>
    )

    expect(await screen.findByText('AAPL')).toBeInTheDocument()
    expect(screen.getByText('50')).toBeInTheDocument()
    expect(screen.getByText(/United States Holdings/i)).toBeInTheDocument()
  })

  it('renders error state when dashboard network request fails', async () => {
    globalThis.fetch = vi.fn().mockImplementation((url: string) => {
      if (url.includes('/auth/me')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ id: 'user_1', email: 'test@finnie.ai', full_name: 'Test' })
        })
      }
      if (url.includes('/dashboard')) {
        return Promise.resolve({
          ok: false,
          status: 500
        })
      }
      return Promise.reject(new Error(`Unhandled: ${url}`))
    })

    render(
      <AuthProvider>
        <Dashboard />
      </AuthProvider>
    )

    expect(await screen.findByText(/Sync Error/i)).toBeInTheDocument()
  })
})
