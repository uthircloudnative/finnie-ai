import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { AuthProvider } from '../../../context/AuthContext'
import GoalPlanner from '../GoalPlanner'

describe('GoalPlannerFlow Integration Tests', () => {
  beforeEach(() => {
    sessionStorage.clear()
    localStorage.clear()
    sessionStorage.setItem('finnie_auth_token', 'test_jwt_token')
    vi.restoreAllMocks()
  })

  it('renders Goal Planner configurator form with default financial goals', async () => {
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
            target_amount: 1500000,
            target_year: 2045,
            monthly_savings: 1200,
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
    expect(screen.getByText(/Ready to build your roadmap/i)).toBeInTheDocument()
    expect(screen.getByText(/Target Amount/i)).toBeInTheDocument()
  })

  it('renders Roadmap, ThoughtStream, Lock-in button, and Micro-Chat upon calculation', async () => {
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
            reply: '### 🎯 Your Strategic Roadmap: Retirement\nOn track with $30,500 annual IRS limits.',
            analysis_results: {
              simulation: {
                confidence_score: 84.5,
                years_axis: [2026, 2027, 2028],
                median_path: [10000, 25000, 45000],
                p05_path: [8000, 18000, 30000],
                p25_path: [9000, 21000, 38000],
                p75_path: [11000, 28000, 52000],
                p95_path: [12000, 32000, 60000],
                final_median: 45000
              }
            },
            thread_id: 'goal_user_1_retirement',
            confidence_score: 84.5,
            country: 'USA',
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

    expect(await screen.findByRole('button', { name: /Lock In & Save Goal/i })).toBeInTheDocument()
    expect(await screen.findByText(/Autonomous Agent Thought Stream/i)).toBeInTheDocument()
    expect(await screen.findByText(/Autonomous Strategy Refinement/i)).toBeInTheDocument()
  })

  it('opens StrategyLockInModal on Lock In button click', async () => {
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
            reply: 'Roadmap ready.',
            analysis_results: {
              simulation: {
                confidence_score: 91.0,
                years_axis: [2026, 2027],
                median_path: [50000, 100000],
                p05_path: [40000, 80000],
                p25_path: [45000, 90000],
                p75_path: [55000, 110000],
                p95_path: [60000, 120000],
                final_median: 100000
              }
            },
            thread_id: 'goal_user_1_retirement',
            confidence_score: 91.0,
            country: 'USA',
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

    const lockInBtn = await screen.findByRole('button', { name: /Lock In & Save Goal/i })
    fireEvent.click(lockInBtn)

    expect(await screen.findByText(/Human-in-the-Loop Final Audit/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Confirm & Lock In/i })).toBeInTheDocument()
  })
})
