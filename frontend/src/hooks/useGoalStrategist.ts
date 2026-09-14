import { useState, useCallback, useEffect } from 'react'
import { useAuth } from '../context/AuthContext'
import { API_BASE } from '../config'

export interface GoalConfig {
  goal_name: string
  target_amount: number
  target_year: number
  monthly_savings: number
  country: string
}

interface UseGoalStrategistReturn {
  goal: GoalConfig | null
  roadmap: string | null
  simulationResults: any | null
  isLoading: boolean
  error: string | null
  calculate: (config: GoalConfig) => Promise<void>
  refresh: () => void
}

export function useGoalStrategist(): UseGoalStrategistReturn {
  const { getAuthHeaders } = useAuth()
  const [goal, setGoal] = useState<GoalConfig | null>(null)
  const [roadmap, setRoadmap] = useState<string | null>(null)
  const [simulationResults, setSimulationResults] = useState<any | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchGoal = useCallback(async () => {
    setIsLoading(true)
    setError(null)
    try {
      const res = await fetch(`${API_BASE}/goals`, { headers: getAuthHeaders() })
      if (!res.ok) throw new Error('Failed to fetch goal')
      const data = await res.json()
      if (data.status !== 'no_goal') {
        setGoal(data)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error fetching goal')
    } finally {
      setIsLoading(false)
    }
  }, [getAuthHeaders])

  const calculate = useCallback(async (config: GoalConfig) => {
    setIsLoading(true)
    setError(null)
    try {
      const res = await fetch(`${API_BASE}/goals/calculate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...getAuthHeaders() },
        body: JSON.stringify(config),
      })
      if (!res.ok) {
        const data = await res.json().catch(() => ({}))
        throw new Error(data.detail ?? 'Failed to calculate roadmap')
      }
      const data = await res.json()
      setRoadmap(data.reply)
      setSimulationResults(data.analysis_results?.simulation)
      setGoal(config)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Calculation error')
    } finally {
      setIsLoading(false)
    }
  }, [getAuthHeaders])

  useEffect(() => {
    fetchGoal()
  }, [fetchGoal])

  return { 
    goal, 
    roadmap, 
    simulationResults, 
    isLoading, 
    error, 
    calculate, 
    refresh: fetchGoal 
  }
}
