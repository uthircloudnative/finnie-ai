import { useState, useCallback, useEffect } from 'react'
import { useAuth } from '../context/AuthContext'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

interface UseMarketInsightsReturn {
  pulse: string | null
  isLoading: boolean
  error: string | null
  refetch: () => void
}

export function useMarketInsights(): UseMarketInsightsReturn {
  const { getAuthHeaders } = useAuth()
  const [pulse, setPulse] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchPulse = useCallback(async () => {
    setIsLoading(true)
    setError(null)
    try {
      const res = await fetch(`${API_BASE}/market/news`, { headers: getAuthHeaders() })
      if (!res.ok) throw new Error(`Server error ${res.status}`)
      const data = await res.json()
      setPulse(data.reply)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load market pulse')
    } finally {
      setIsLoading(false)
    }
  }, [getAuthHeaders])

  useEffect(() => {
    fetchPulse()
  }, [fetchPulse])

  return { pulse, isLoading, error, refetch: fetchPulse }
}
