/**
 * usePortfolio.ts — Hook for fetching and saving user holdings.
 * Follows the same pattern as useChat.ts (single responsibility, all API logic here).
 */
import { useState, useCallback, useEffect } from 'react'

const API_BASE = 'http://localhost:8000'
const USER_ID = 'user_1' // Hardcoded for Phase 3 — replace with auth in future

export interface Holding {
  ticker: string
  shares: number
  added_date: string
}

export interface HoldingInput {
  ticker: string
  shares: number
}

interface UsePortfolioReturn {
  holdings: Holding[]
  isLoading: boolean
  isSaving: boolean
  error: string | null
  savePortfolio: (inputs: HoldingInput[]) => Promise<boolean>
  refetch: () => void
}

export function usePortfolio(): UsePortfolioReturn {
  const [holdings, setHoldings] = useState<Holding[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchHoldings = useCallback(async () => {
    setIsLoading(true)
    setError(null)
    try {
      const res = await fetch(`${API_BASE}/portfolio/${USER_ID}`)
      if (!res.ok) throw new Error(`Server error ${res.status}`)
      const data = await res.json()
      setHoldings(data.holdings ?? [])
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load holdings')
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

  return { holdings, isLoading, isSaving, error, savePortfolio, refetch: fetchHoldings }
}
