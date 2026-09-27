import { useState, useCallback, useEffect } from 'react'
import { useAuth } from '../context/AuthContext'
import { API_ENDPOINTS } from '../config'

export interface GoalConfig {
  id?: number
  goal_name: string
  target_amount: number
  target_year: number
  monthly_savings: number
  country: string
  thread_id?: string
  status?: string
  confidence_score?: number
  strategy_report?: string
}

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: string
}

interface UseGoalStrategistReturn {
  goal: GoalConfig | null
  roadmap: string | null
  simulationResults: any | null
  isLoading: boolean
  isStreaming: boolean
  error: string | null
  threadId: string | null
  confidenceScore: number
  status: string
  thoughts: string[]
  chatHistory: ChatMessage[]
  calculate: (config: GoalConfig, prompt?: string) => Promise<void>
  askRefinement: (prompt: string) => Promise<void>
  lockIn: (userAdjustments?: Record<string, any>) => Promise<boolean>
  refresh: () => void
}

export function useGoalStrategist(): UseGoalStrategistReturn {
  const { getAuthHeaders } = useAuth()
  const [goal, setGoal] = useState<GoalConfig | null>(null)
  const [roadmap, setRoadmap] = useState<string | null>(null)
  const [simulationResults, setSimulationResults] = useState<any | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [isStreaming, setIsStreaming] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [threadId, setThreadId] = useState<string | null>(null)
  const [confidenceScore, setConfidenceScore] = useState<number>(0)
  const [status, setStatus] = useState<string>('DRAFT')
  const [thoughts, setThoughts] = useState<string[]>([])
  const [chatHistory, setChatHistory] = useState<ChatMessage[]>([])

  const fetchGoal = useCallback(async () => {
    setIsLoading(true)
    setError(null)
    try {
      const res = await fetch(API_ENDPOINTS.GOALS, { headers: getAuthHeaders() })
      if (!res.ok) throw new Error('Failed to fetch goal')
      const data = await res.json()
      if (data.status !== 'no_goal') {
        setGoal(data)
        if (data.thread_id) setThreadId(data.thread_id)
        if (data.status) setStatus(data.status)
        if (data.confidence_score) setConfidenceScore(data.confidence_score)
        if (data.strategy_report) setRoadmap(data.strategy_report)
      } else {
        // Restore uncommitted draft config from local session if available
        try {
          const cachedDraft = localStorage.getItem('finnie_draft_goal')
          if (cachedDraft) {
            const parsed = JSON.parse(cachedDraft)
            setGoal(parsed)
          }
        } catch (_) {}
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error fetching goal')
    } finally {
      setIsLoading(false)
    }
  }, [getAuthHeaders])

  const calculate = useCallback(async (config: GoalConfig, prompt?: string) => {
    setIsLoading(true)
    setIsStreaming(true)
    setError(null)
    setThoughts(['Initializing autonomous simulation engine...', 'Evaluating portfolio risk metrics...'])

    // Cache latest parameters in local session
    try {
      localStorage.setItem('finnie_draft_goal', JSON.stringify(config))
    } catch (_) {}

    const payload = {
      goal_name: config.goal_name,
      target_amount: config.target_amount,
      target_year: config.target_year,
      monthly_savings: config.monthly_savings,
      country: config.country,
      thread_id: threadId || config.thread_id,
      prompt: prompt || undefined
    }

    try {
      const res = await fetch(API_ENDPOINTS.GOALS_CALCULATE, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...getAuthHeaders() },
        body: JSON.stringify(payload)
      })

      if (!res.ok) {
        const data = await res.json().catch(() => ({}))
        throw new Error(data.detail ?? 'Failed to calculate roadmap')
      }

      const data = await res.json()
      setRoadmap(data.reply)
      if (data.analysis_results?.simulation) {
        setSimulationResults(data.analysis_results.simulation)
      }
      if (data.thread_id) setThreadId(data.thread_id)
      if (data.confidence_score !== undefined) setConfidenceScore(data.confidence_score)
      if (data.status) setStatus(data.status)
      setGoal(config)
      setThoughts(prev => [...prev, 'Roadmap synthesized and verified with statutory compliance.'])

      if (prompt) {
        const newAssistantMsg: ChatMessage = {
          id: `msg_${Date.now()}`,
          role: 'assistant',
          content: data.reply,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        }
        setChatHistory(prev => [...prev, newAssistantMsg])
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Calculation error')
    } finally {
      setIsLoading(false)
      setIsStreaming(false)
    }
  }, [getAuthHeaders, threadId])

  const askRefinement = useCallback(async (promptText: string) => {
    if (!promptText.trim() || !goal) return

    const userMsg: ChatMessage = {
      id: `usr_${Date.now()}`,
      role: 'user',
      content: promptText.trim(),
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    }
    setChatHistory(prev => [...prev, userMsg])
    await calculate(goal, promptText.trim())
  }, [goal, calculate])

  const lockIn = useCallback(async (userAdjustments?: Record<string, any>): Promise<boolean> => {
    if (!threadId) {
      setError('Cannot lock in goal without an active strategy thread.')
      return false
    }

    setIsLoading(true)
    setError(null)
    try {
      const res = await fetch(API_ENDPOINTS.GOALS_LOCK_IN, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...getAuthHeaders() },
        body: JSON.stringify({
          thread_id: threadId,
          approved: true,
          user_adjustments: userAdjustments
        })
      })

      if (!res.ok) {
        const data = await res.json().catch(() => ({}))
        throw new Error(data.detail ?? 'Failed to lock in strategy')
      }

      const data = await res.json()
      setStatus('LOCKED')
      if (data.goal) {
        setGoal(data.goal)
      }
      return true
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Lock-in error')
      return false
    } finally {
      setIsLoading(false)
    }
  }, [getAuthHeaders, threadId])

  useEffect(() => {
    fetchGoal()
  }, [fetchGoal])

  return {
    goal,
    roadmap,
    simulationResults,
    isLoading,
    isStreaming,
    error,
    threadId,
    confidenceScore,
    status,
    thoughts,
    chatHistory,
    calculate,
    askRefinement,
    lockIn,
    refresh: fetchGoal
  }
}
