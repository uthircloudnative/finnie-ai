import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { AuthProvider } from '../../../context/AuthContext'
import GoalPlanner from '../GoalPlanner'

describe('SPEC-11 Liability-Aware Goal Planner Flow Tests', () => {
  beforeEach(() => {
    sessionStorage.clear()
    localStorage.clear()
    sessionStorage.setItem('finnie_auth_token', 'test_jwt_token')
    vi.restoreAllMocks()
  })

  it('renders Country Selector and switches currency symbols dynamically', async () => {
    globalThis.fetch = vi.fn().mockImplementation((url: string) => {
      if (url.includes('/auth/me')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ id: 'user_1', email: 'test@finnie.ai', full_name: 'Test' })
        })
      }
      if (url.includes('/goals')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({
            goal_name: 'Retirement Fund',
            target_amount: 1000000,
            target_year: 2040,
            monthly_savings: 1000,
            country: 'USA'
          })
        })
      }
      return Promise.reject(new Error(`Unhandled: ${url}`))
    })

    render(
      <AuthProvider>
        <GoalPlanner />
      </AuthProvider>
    )

    expect(await screen.findByRole('button', { name: /Generate Roadmap/i })).toBeInTheDocument()
    expect(screen.getByText(/Country of Residence/i)).toBeInTheDocument()
    expect(screen.getByText(/Target Amount \(\$\)/i)).toBeInTheDocument()

    // Switch country to India
    const countrySelect = screen.getByDisplayValue(/United States/i)
    fireEvent.change(countrySelect, { target: { value: 'INDIA' } })

    expect(screen.getByText(/Target Amount \(₹\)/i)).toBeInTheDocument()
  })

  it('expands Cash Flow & Liabilities accordion and calculates solvency live', async () => {
    globalThis.fetch = vi.fn().mockImplementation((url: string) => {
      if (url.includes('/auth/me')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ id: 'user_1', email: 'test@finnie.ai', full_name: 'Test' })
        })
      }
      if (url.includes('/goals/cashflow')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({
            monthly_take_home: 7000,
            fixed_living_costs: 3000,
            monthly_discretionary_spend: 1000,
            country: 'USA'
          })
        })
      }
      if (url.includes('/goals/liabilities')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve([
            {
              id: 1,
              liability_type: 'Credit Card',
              lender_name: 'Sapphire Preferred',
              current_balance: 6000,
              interest_rate_apr: 24.5,
              monthly_payment: 200,
              remaining_months: 36
            }
          ])
        })
      }
      if (url.includes('/goals')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({
            goal_name: 'Financial Independence',
            target_amount: 1500000,
            target_year: 2045,
            monthly_savings: 1500,
            country: 'USA'
          })
        })
      }
      return Promise.reject(new Error(`Unhandled: ${url}`))
    })

    render(
      <AuthProvider>
        <GoalPlanner />
      </AuthProvider>
    )

    expect(await screen.findByRole('button', { name: /Generate Roadmap/i })).toBeInTheDocument()

    // Click accordion header to expand
    const accordionBtn = screen.getByRole('button', { name: /Cash Flow & Liabilities/i })
    fireEvent.click(accordionBtn)

    expect(screen.getByText(/Monthly Take-Home/i)).toBeInTheDocument()
    expect(screen.getByText(/Discretionary Spend/i)).toBeInTheDocument()
    expect(screen.getByText(/Active Liabilities/i)).toBeInTheDocument()
  })

  it('renders Twin Synchronized Charts and Action Levers upon simulation response', async () => {
    globalThis.fetch = vi.fn().mockImplementation((url: string) => {
      if (url.includes('/auth/me')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ id: 'user_1', email: 'test@finnie.ai', full_name: 'Test' })
        })
      }
      if (url.includes('/goals/calculate')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({
            reply: '### Strategic Roadmap Synthesis\nPhase 1: Clear credit card debt.',
            analysis_results: {
              simulation: {
                confidence_score: 82.0,
                years_axis: [2026, 2027, 2028, 2029, 2030],
                median_path: [10000, 25000, 45000, 70000, 105000],
                p05_path: [8000, 18000, 32000, 48000, 70000],
                p25_path: [9000, 21000, 38000, 58000, 85000],
                p75_path: [11000, 28000, 52000, 82000, 125000],
                p95_path: [12000, 32000, 60000, 96000, 150000],
                debt_path: [26000, 18000, 10000, 2000, 0],
                net_worth_path: [-16000, 7000, 35000, 68000, 105000],
                debt_free_year: 2030,
                total_interest_paid: 3400.0,
                final_median: 105000
              }
            },
            thread_id: 'goal_user_1_twin',
            confidence_score: 82.0,
            status: 'READY_TO_LOCK'
          })
        })
      }
      if (url.includes('/goals')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ status: 'no_goal' })
        })
      }
      return Promise.reject(new Error(`Unhandled: ${url}`))
    })

    render(
      <AuthProvider>
        <GoalPlanner />
      </AuthProvider>
    )

    const calcBtn = await screen.findByRole('button', { name: /Generate Roadmap/i })
    fireEvent.click(calcBtn)

    // Check Twin Chart Card 1 & Card 2 headers
    expect(await screen.findByText(/CHART 1: PROJECTED INVESTMENT GROWTH/i)).toBeInTheDocument()
    expect(screen.getByText(/CHART 2: REAL NET WORTH & LOAN PAYOFF PROGRESS/i)).toBeInTheDocument()
    expect(screen.getByText(/Debt-Free by 2030/i)).toBeInTheDocument()

    // Check Upfront Action Levers
    expect(screen.getByText(/STRATEGY 1: DEBT AVALANCHE/i)).toBeInTheDocument()
    expect(screen.getByText(/STRATEGY 2: POST-LOAN STEP-UP/i)).toBeInTheDocument()
  })
})
