/**
 * useChat.ts — Custom hook managing Finnie chat state & API calls.
 * Separates all business logic from the UI components (STANDARDS.md §3.1).
 */
import { useState, useCallback } from 'react'
import { useAuth } from '../context/AuthContext'
import { API_BASE } from '../config'

export interface Message {
  id: string
  role: 'user' | 'ai'
  content: string
  timestamp: Date
}

interface UseChatReturn {
  messages: Message[]
  isLoading: boolean
  error: string | null
  sendMessage: (text: string, preferredWorker?: string, analysisContext?: any) => Promise<void>
}

export function useChat(): UseChatReturn {
  const { getAuthHeaders } = useAuth()
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 'welcome',
      role: 'ai',
      content: "Hi! I'm Finnie, your personal finance guide. Ask me anything about investing — ETFs, index funds, compound interest, and more. I'll give you grounded, factual answers.",
      timestamp: new Date(),
    },
  ])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const sendMessage = useCallback(async (text: string, preferredWorker?: string, analysisContext?: any) => {
    if (!text.trim() || isLoading) return

    // 1. Append the user's message immediately for instant feedback
    const userMessage: Message = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: text.trim(),
      timestamp: new Date(),
    }
    setMessages((prev) => [...prev, userMessage])
    setIsLoading(true)
    setError(null)

    // 2. Call the FastAPI /chat endpoint
    try {
      const response = await fetch(`${API_BASE}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...getAuthHeaders() },
        body: JSON.stringify({ 
          message: text.trim(),
          preferred_worker: preferredWorker,
          analysis_context: analysisContext
        }),
      })

      if (!response.ok) {
        const data = await response.json().catch(() => ({}))
        throw new Error(data.detail ?? `Server error ${response.status}`)
      }

      const data = await response.json()

      // 3. Append Finnie's reply
      const aiMessage: Message = {
        id: `ai-${Date.now()}`,
        role: 'ai',
        content: data.reply,
        timestamp: new Date(),
      }
      setMessages((prev) => [...prev, aiMessage])
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Something went wrong'
      setError(msg)

      // Show error inline as an AI message so the user knows what happened
      setMessages((prev) => [
        ...prev,
        {
          id: `err-${Date.now()}`,
          role: 'ai',
          content: `⚠️ ${msg}. Please try again or check that the backend server is running on port 8000.`,
          timestamp: new Date(),
        },
      ])
    } finally {
      setIsLoading(false)
    }
  }, [isLoading, getAuthHeaders])

  return { messages, isLoading, error, sendMessage }
}
