import { useEffect, useRef } from 'react'
import type { Message } from '../../hooks/useChat'
import ThinkingIndicator from './ThinkingIndicator'
import { renderFormattedContent } from '../Goals/RoadmapRenderer'
import FinnieCoinIcon from '../Common/FinnieCoinIcon'
import './ChatWindow.css'

interface ChatWindowProps {
  messages: Message[]
  isLoading: boolean
  onSelectPrompt?: (prompt: string) => void
}

const STARTER_PROMPT_CHIPS = [
  'What is dollar-cost averaging and how does it lower volatility?',
  'Explain asset allocation differences for aggressive vs conservative growth',
  'How do statutory retirement account caps benefit my long-term compounding?',
  'Compare index funds vs actively managed mutual funds'
]

function formatTimestamp(ts: Date | string | undefined): string {
  if (!ts) return ''
  try {
    const d = typeof ts === 'string' ? new Date(ts) : ts
    return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  } catch {
    return ''
  }
}

export default function ChatWindow({ messages, isLoading, onSelectPrompt }: ChatWindowProps) {
  const bottomRef = useRef<HTMLDivElement>(null)

  // Auto-scroll to latest message
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isLoading])

  return (
    <div className="chat-window">
      {messages.length === 0 ? (
        <div className="chat-empty-state">
          <div className="chat-empty-coin-wrapper">
            <FinnieCoinIcon size={44} />
          </div>
          <h2 className="chat-empty-title">Deep Financial Q&amp;A</h2>
          <p className="chat-empty-desc">
            Ask any question on asset allocation, tax-advantaged structures, market volatility, or financial planning.
          </p>
          {onSelectPrompt && (
            <div className="chat-prompt-chips">
              {STARTER_PROMPT_CHIPS.map((chip) => (
                <button
                  key={chip}
                  type="button"
                  className="chat-prompt-chip"
                  onClick={() => onSelectPrompt(chip)}
                >
                  {chip}
                </button>
              ))}
            </div>
          )}
        </div>
      ) : (
        messages.map((msg) => {
          const roleLabel = msg.role === 'user' ? 'You' : 'Finnie AI'
          const timeStr = formatTimestamp(msg.timestamp)

          return (
            <div key={msg.id} className={`message-row ${msg.role}`}>
              {msg.role === 'ai' && (
                <div className="chat-ai-avatar">
                  <FinnieCoinIcon size={24} />
                </div>
              )}
              <div className={`bubble bubble-${msg.role}`}>
                <div className="bubble-header">
                  <span className="bubble-role">{roleLabel}</span>
                  {timeStr && <span className="bubble-time">{timeStr}</span>}
                </div>
                <div className="bubble-body">
                  {renderFormattedContent(msg.content)}
                </div>
              </div>
            </div>
          )
        })
      )}

      {isLoading && (
        <div className="message-row ai">
          <div className="chat-ai-avatar">
            <FinnieCoinIcon size={24} isSpinning={true} />
          </div>
          <ThinkingIndicator />
        </div>
      )}

      <div ref={bottomRef} />
    </div>
  )
}
