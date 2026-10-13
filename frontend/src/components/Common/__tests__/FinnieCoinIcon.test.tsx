import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { AuthProvider } from '../../../context/AuthContext'
import FinnieCoinIcon, { resolveUserCurrencySymbol } from '../FinnieCoinIcon'

describe('FinnieCoinIcon Utility Component', () => {
  beforeEach(() => {
    sessionStorage.clear()
    localStorage.clear()
    vi.restoreAllMocks()
  })

  it('resolves currency symbols properly from profile and defaults', () => {
    expect(resolveUserCurrencySymbol('USD')).toBe('$')
    expect(resolveUserCurrencySymbol('INR')).toBe('₹')
    expect(resolveUserCurrencySymbol('EUR')).toBe('€')
    expect(resolveUserCurrencySymbol('GBP')).toBe('£')
    expect(resolveUserCurrencySymbol('CAD')).toBe('C$')
    expect(resolveUserCurrencySymbol('JPY')).toBe('¥')
    expect(resolveUserCurrencySymbol('₹')).toBe('₹')
    expect(resolveUserCurrencySymbol(null)).toBe('$')
    expect(resolveUserCurrencySymbol('')).toBe('$')
  })

  it('renders default spinning coin with 20px size and $ currency fallback', () => {
    const { container } = render(
      <AuthProvider>
        <FinnieCoinIcon />
      </AuthProvider>
    )

    const coin = container.querySelector('.finnie-coin-container')
    expect(coin).toBeInTheDocument()
    expect(coin).toHaveClass('finnie-coin-flipping')
    expect(coin).toHaveStyle({ width: '20px', height: '20px' })

    // Check Face B has currency symbol
    const currencyText = container.querySelector('.finnie-coin-currency')
    expect(currencyText).toBeInTheDocument()
    expect(currencyText?.textContent).toBe('$')

    // Check Face A has SVG market elements
    const svg = container.querySelector('.finnie-coin-svg')
    expect(svg).toBeInTheDocument()

    // Verify trendline exists
    const trendline = svg?.querySelector('path[stroke="#fef08a"]')
    expect(trendline).toBeInTheDocument()

    // Verify NO glow filter on the arrowhead
    const glowingApexDot = svg?.querySelector('circle[filter*="glow"]')
    expect(glowingApexDot).toBeNull()
  })

  it('renders with custom size and explicit currency override', () => {
    const { container } = render(
      <AuthProvider>
        <FinnieCoinIcon size={28} currencySymbol="€" isSpinning={false} />
      </AuthProvider>
    )

    const coin = container.querySelector('.finnie-coin-container')
    expect(coin).toBeInTheDocument()
    expect(coin).not.toHaveClass('finnie-coin-flipping')
    expect(coin).toHaveStyle({ width: '28px', height: '28px' })

    const currencyText = container.querySelector('.finnie-coin-currency')
    expect(currencyText?.textContent).toBe('€')
  })

  it('resolves user profile currency dynamically from AuthContext', async () => {
    sessionStorage.setItem('finnie_auth_token', 'mock_jwt_token')
    globalThis.fetch = vi.fn().mockImplementation((url: string) => {
      if (url.includes('/auth/me')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({
            id: 'usr_in_01',
            email: 'rajesh@finnie.ai',
            full_name: 'Rajesh',
            base_currency: 'INR'
          })
        })
      }
      return Promise.reject(new Error(`Unhandled: ${url}`))
    })

    const { container } = render(
      <AuthProvider>
        <FinnieCoinIcon />
      </AuthProvider>
    )

    // Wait for auth fetch to resolve
    await screen.findByRole('img', { name: /Finnie Sovereign Market Coin/i })
    
    // Check that INR was converted to ₹
    const currencyText = container.querySelector('.finnie-coin-currency')
    expect(currencyText).toBeInTheDocument()
    expect(currencyText?.textContent).toBe('₹')
  })
})
