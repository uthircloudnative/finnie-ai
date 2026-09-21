import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
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
})
