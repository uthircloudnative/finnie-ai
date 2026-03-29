/**
 * usePortfolio.ts — Hook for fetching and saving user holdings.
 * Follows the same pattern as useChat.ts (single responsibility, all API logic here).
 */
import { useState, useCallback, useEffect } from 'react'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'
const USER_ID = 'user_1' // Hardcoded for Phase 3 — replace with auth in future

export interface Holding {
  ticker: string
  shares: number
  country: string
  exchange: string
  added_date: string
}

export interface Exchange {
  country_name: string
  country_code: string
  exchange_name: string
  exchange_code: string
}

export interface HoldingInput {
  ticker: string
  shares: number
  country: string
  exchange: string
}

interface UsePortfolioReturn {
  holdings: Holding[]
  exchanges: Exchange[]
  isLoading: boolean
  isSaving: boolean
  error: string | null
  savePortfolio: (inputs: HoldingInput[]) => Promise<boolean>
  refetch: () => void
}

export function usePortfolio(): UsePortfolioReturn {
  const [holdings, setHoldings] = useState<Holding[]>([])
  const [exchanges, setExchanges] = useState<Exchange[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchHoldings = useCallback(async () => {
    setIsLoading(true)
    setError(null)
    try {
      // Parallel fetch for speed
      const [portRes, metaRes] = await Promise.all([
        fetch(`${API_BASE}/portfolio/${USER_ID}`),
        fetch(`${API_BASE}/metadata/exchanges`)
      ])

      if (!portRes.ok || !metaRes.ok) throw new Error('Failed to fetch portfolio data')

      const [portData, metaData] = await Promise.all([
        portRes.json(),
        metaRes.json()
      ])

      setHoldings(portData.holdings ?? [])
      setExchanges(metaData ?? [])
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load portfolio')
    } finally {
      setIsLoading(false)
    }
  }, [])

  // Auto-fetch on mount
  useEffect(() => { fetchHoldings() }, [fetchHoldings])

  const savePortfolio = useCallback(async (inputs: HoldingInput[]): Promise<boolean> => {
    setIsSaving(true)
    setError(null)
    try {
      const res = await fetch(`${API_BASE}/portfolio/save`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: USER_ID, holdings: inputs }),
      })
      if (!res.ok) {
        const data = await res.json().catch(() => ({}))
        throw new Error(data.detail ?? `Server error ${res.status}`)
      }
      const data = await res.json()
      setHoldings(data.holdings ?? [])
      return true
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save portfolio')
      return false
    } finally {
      setIsSaving(false)
    }
  }, [])

  return { holdings, exchanges, isLoading, isSaving, error, savePortfolio, refetch: fetchHoldings }
}
