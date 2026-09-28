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
  calculate: (config: GoalConfig, prompt?: string, historyForRequest?: ChatMessage[]) => Promise<void>
  askRefinement: (prompt: string, configOverride?: GoalConfig) => Promise<void>
  clearChat: () => void
  lockIn: (userAdjustments?: Record<string, any>) => Promise<boolean>
  refresh: () => void
}

interface GoalSessionCache {
  goal: GoalConfig | null
  roadmap: string | null
  simulationResults: any | null
  threadId: string | null
  confidenceScore: number
  status: string
  chatHistory: ChatMessage[]
}

const SESSION_KEY = 'finnie_goal_session'

const loadSessionCache = (): Partial<GoalSessionCache> => {
  try {
    const raw = sessionStorage.getItem(SESSION_KEY)
    if (raw) return JSON.parse(raw)
  } catch (_) {}
  return {}
}

const saveSessionCache = (data: Partial<GoalSessionCache>) => {
  try {
    const existing = loadSessionCache()
    sessionStorage.setItem(SESSION_KEY, JSON.stringify({ ...existing, ...data }))
  } catch (_) {}
}

export function useGoalStrategist(): UseGoalStrategistReturn {
  const { getAuthHeaders } = useAuth()
  const initialCache = loadSessionCache()

  const [goal, setGoal] = useState<GoalConfig | null>(() => {
    if (initialCache.goal) return initialCache.goal
    try {
      const draft = localStorage.getItem('finnie_draft_goal')
      if (draft) return JSON.parse(draft)
    } catch (_) {}
    return null
  })
  const [roadmap, setRoadmap] = useState<string | null>(initialCache.roadmap || null)
  const [simulationResults, setSimulationResults] = useState<any | null>(initialCache.simulationResults || null)
  const [isLoading, setIsLoading] = useState(false)
  const [isStreaming, setIsStreaming] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [threadId, setThreadId] = useState<string | null>(initialCache.threadId || null)
  const [confidenceScore, setConfidenceScore] = useState<number>(initialCache.confidenceScore || 0)
  const [status, setStatus] = useState<string>(initialCache.status || 'DRAFT')
  const [thoughts, setThoughts] = useState<string[]>([])
  const [chatHistory, setChatHistory] = useState<ChatMessage[]>(initialCache.chatHistory || [])

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
        saveSessionCache({
          goal: data,
          threadId: data.thread_id,
          status: data.status,
          confidenceScore: data.confidence_score,
          roadmap: data.strategy_report
        })
      } else {
        // If DB has no committed goal, check session cache to preserve in-flight roadmap and chat
        const cached = loadSessionCache()
        if (cached.goal) setGoal(cached.goal)
        if (cached.roadmap) setRoadmap(cached.roadmap)
        if (cached.simulationResults) setSimulationResults(cached.simulationResults)
        if (cached.threadId) setThreadId(cached.threadId)
        if (cached.confidenceScore) setConfidenceScore(cached.confidenceScore)
        if (cached.status) setStatus(cached.status)
        if (cached.chatHistory) setChatHistory(cached.chatHistory)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error fetching goal')
    } finally {
      setIsLoading(false)
    }
  }, [getAuthHeaders])

  const calculate = useCallback(async (config: GoalConfig, prompt?: string, historyForRequest?: ChatMessage[]) => {
    setIsLoading(true)
    setIsStreaming(true)
    setError(null)
    setThoughts(['Initializing autonomous simulation engine...', 'Evaluating portfolio risk metrics...'])

    // Cache latest parameters in local and session storage
    try {
      localStorage.setItem('finnie_draft_goal', JSON.stringify(config))
      saveSessionCache({ goal: config })
    } catch (_) {}

    const payload = {
      goal_name: config.goal_name,
      target_amount: config.target_amount,
      target_year: config.target_year,
      monthly_savings: config.monthly_savings,
      country: config.country,
      thread_id: threadId || config.thread_id,
      prompt: prompt || undefined,
      has_baseline: Boolean(roadmap && simulationResults),
      chat_history: historyForRequest 
        ? historyForRequest.map(m => ({ role: m.role, content: m.content })) 
        : (chatHistory.length > 0 ? chatHistory.map(m => ({ role: m.role, content: m.content })) : undefined)
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
      const newThreadId = data.thread_id || threadId
      if (newThreadId) setThreadId(newThreadId)

      if (!prompt) {
        // Direct "Generate Roadmap" click from form: updates Center Stage!
        setRoadmap(data.reply)
        let sim = null
        if (data.analysis_results?.simulation) {
          sim = data.analysis_results.simulation
          setSimulationResults(sim)
        }
        const conf = data.confidence_score !== undefined ? data.confidence_score : 0
        setConfidenceScore(conf)
        const st = data.status || 'READY_TO_LOCK'
        setStatus(st)
        setGoal(config)
        setThoughts(prev => [...prev, 'Roadmap synthesized and verified with statutory compliance.'])

        saveSessionCache({
          roadmap: data.reply,
          simulationResults: sim,
          confidenceScore: conf,
          status: st,
          goal: config,
          threadId: newThreadId
        })
      } else {
        // Chat question / refinement: strictly stays in the chat window!
        let sim = simulationResults
        if (!data.is_off_topic && data.analysis_results?.simulation && simulationResults) {
          sim = data.analysis_results.simulation
          setSimulationResults(sim)
          if (data.confidence_score !== undefined) setConfidenceScore(data.confidence_score)
        }
        setThoughts(prev => [...prev, 'Strategist evaluated what-if scenario.'])

        const newAssistantMsg: ChatMessage = {
          id: `msg_${Date.now()}`,
          role: 'assistant',
          content: data.reply,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        }
        const updatedChat = [...(historyForRequest || chatHistory), newAssistantMsg]
        setChatHistory(updatedChat)

        saveSessionCache({
          chatHistory: updatedChat,
          simulationResults: sim,
          threadId: newThreadId
        })
      }
    } catch (err) {
      const errMsg = err instanceof Error ? err.message : 'Calculation error'
      setError(errMsg)
      if (prompt) {
        const errorMsg: ChatMessage = {
          id: `msg_err_${Date.now()}`,
          role: 'assistant',
          content: `⚠️ Strategic calculation error: ${errMsg}. Please verify parameters and try again.`,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        }
        const updatedChat = [...(historyForRequest || chatHistory), errorMsg]
        setChatHistory(updatedChat)
        saveSessionCache({ chatHistory: updatedChat })
      }
    } finally {
      setIsLoading(false)
      setIsStreaming(false)
    }
  }, [getAuthHeaders, threadId, roadmap, simulationResults, chatHistory])

  const askRefinement = useCallback(async (promptText: string, configOverride?: GoalConfig) => {
    if (!promptText.trim()) return

    const activeConfig: GoalConfig = configOverride || goal || {
      goal_name: 'Retirement Capital',
      target_amount: 1000000,
      target_year: 2040,
      monthly_savings: 1000,
      country: 'USA'
    }

    const userMsg: ChatMessage = {
      id: `usr_${Date.now()}`,
      role: 'user',
      content: promptText.trim(),
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    }
    const updatedHistory = [...chatHistory, userMsg]
    setChatHistory(updatedHistory)
    await calculate(activeConfig, promptText.trim(), updatedHistory)
  }, [goal, chatHistory, calculate])

  const clearChat = useCallback(() => {
    setChatHistory([])
    saveSessionCache({ chatHistory: [] })
  }, [])

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
      saveSessionCache({
        status: 'LOCKED',
        goal: data.goal || goal
      })
      return true
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Lock-in error')
      return false
    } finally {
      setIsLoading(false)
    }
  }, [getAuthHeaders, threadId, goal])

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
    clearChat,
    lockIn,
    refresh: fetchGoal
  }
}
