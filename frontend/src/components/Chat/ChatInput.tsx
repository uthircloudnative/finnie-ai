import { useState, type KeyboardEvent } from 'react'
import './ChatInput.css'

interface ChatInputProps {
  onSend: (text: string) => void
  isLoading: boolean
}

export default function ChatInput({ onSend, isLoading }: ChatInputProps) {
  const [value, setValue] = useState('')

  const handleSend = () => {
    if (!value.trim() || isLoading) return
    onSend(value)
    setValue('')
  }

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="chat-input-wrapper">
      <div className="chat-input-bar">
        <input
          className="chat-input"
          type="text"
          placeholder="Ask Finnie a question… (Agentic Routing Enabled)"
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={isLoading}
          autoFocus
        />
        <button
          className="btn-cyan send-btn"
          onClick={handleSend}
          disabled={isLoading || !value.trim()}
        >
          {isLoading ? '…' : '→'}
        </button>
      </div>
      <p className="nfa-disclaimer">
        $NFA — Finnie is an AI assistant, not a licensed financial advisor. All answers are grounded in public educational sources.
      </p>
    </div>
  )
}
