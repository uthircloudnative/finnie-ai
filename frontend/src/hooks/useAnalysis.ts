import { useState, useCallback, useEffect } from 'react'
import { API_BASE } from '../config'
const USER_ID = 'user_1'

interface UseAnalysisReturn {
  analysis: string | null
  analysisResults: any | null
  isLoading: boolean
  error: string | null
  refetch: () => void
}

export function useAnalysis(): UseAnalysisReturn {
  const [analysis, setAnalysis] = useState<string | null>(null)
  const [analysisResults, setAnalysisResults] = useState<any | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchAnalysis = useCallback(async () => {
    setIsLoading(true)
    setError(null)
    try {
      const res = await fetch(`${API_BASE}/portfolio/analysis/${USER_ID}`)
      if (!res.ok) {
        const data = await res.json().catch(() => ({}))
        throw new Error(data.detail ?? `Server error ${res.status}`)
      }
      const data = await res.json()
      setAnalysis(data.reply)
      setAnalysisResults(data.analysis_results)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch analysis')
    } finally {
      setIsLoading(false)
    }
  }, [])

  // Auto-fetch on mount
  useEffect(() => {
    fetchAnalysis()
  }, [fetchAnalysis])

  return { analysis, analysisResults, isLoading, error, refetch: fetchAnalysis }
}
