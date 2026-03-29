import { useState, useCallback, useEffect } from 'react'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'
const USER_ID = 'user_1'

export interface AssetRow {
  ticker: string
  shares: number
  current_price: number
  prev_close: number
  asset_pnl: number
  asset_pnl_percent: number
  total_value: number
}

export interface PortfolioGroup {
  country_code: string
  total_value: number
  daily_pnl: number
  daily_pnl_percent: number
  assets: AssetRow[]
}

export interface DashboardPayload {
  total_assets: number
  total_countries: number
  portfolios: Record<string, PortfolioGroup>
  error?: boolean
}

interface UseDashboardReturn {
  dashboardData: DashboardPayload | null
  isLoading: boolean
  error: string | null
  refresh: () => void
}

export function useDashboard(): UseDashboardReturn {
  const [dashboardData, setDashboardData] = useState<DashboardPayload | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchDashboard = useCallback(async () => {
    setIsLoading(true)
    setError(null)
    try {
      const res = await fetch(`${API_BASE}/dashboard/${USER_ID}`)
      if (!res.ok) throw new Error('Failed to fetch dashboard data')
      const data: DashboardPayload = await res.json()
      setDashboardData(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error fetching dashboard')
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchDashboard()
  }, [fetchDashboard])

  return { dashboardData, isLoading, error, refresh: fetchDashboard }
}
