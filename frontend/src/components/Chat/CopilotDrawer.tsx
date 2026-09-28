import React, { useState, useRef, useEffect } from 'react'
import { renderFormattedContent } from '../Goals/RoadmapRenderer'
import './CopilotDrawer.css'

export interface CopilotMessage {
  id?: string
  role: 'user' | 'ai' | 'assistant'
  content: string
  timestamp?: string | Date
}

export interface CopilotDrawerProps {
  title?: string
  subtitle?: string
  statusBadge?: string
  messages: CopilotMessage[]
  isLoading: boolean
  loadingText?: string
  onSendMessage: (message: string) => Promise<void> | void
  onClearHistory?: () => void
  onClose: () => void
  suggestionChips?: string[]
  onChipClick?: (chip: string) => void
  initialWidth?: number
  storageKey?: string
  inputPlaceholder?: string
  disclaimerText?: string
}

function formatMessageTimestamp(ts?: string | Date): string {
  if (!ts) return ''
  if (typeof ts === 'string') return ts
  if (ts instanceof Date) {
    return ts.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  }
  return String(ts)
}

export default function CopilotDrawer({
  title = 'Autonomous Copilot',
  subtitle = 'Multi-turn interactive copilot with persistent read-only history.',
  statusBadge,
  messages,
  isLoading,
  loadingText = 'Finnie is thinking and evaluating scenarios...',
  onSendMessage,
  onClearHistory,
  onClose,
  suggestionChips,
  onChipClick,
  initialWidth = 380,
  storageKey = 'finnie_copilot_width',
  inputPlaceholder = 'Ask Finnie a question...',
  disclaimerText
}: CopilotDrawerProps) {
  const [input, setInput] = useState('')
  const [width, setWidth] = useState<number>(() => {
    if (!storageKey) return initialWidth
    try {
      const saved = sessionStorage.getItem(storageKey)
      if (saved) {
        const parsed = Number(saved)
        if (!isNaN(parsed) && parsed >= 320 && parsed <= 720) {
          return parsed
        }
      }
    } catch (_) {}
    return initialWidth
  })

  const messagesEndRef = useRef<HTMLDivElement>(null)
  const isResizingRef = useRef(false)
  const startXRef = useRef(0)
  const startWidthRef = useRef(width)

  // Save width changes to session storage
  useEffect(() => {
    if (storageKey) {
      try {
        sessionStorage.setItem(storageKey, String(width))
      } catch (_) {}
    }
  }, [width, storageKey])

  // Auto-scroll to latest response
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isLoading])

  // Horizontal drag resizing logic
  const handleMouseDownResize = (e: React.MouseEvent) => {
    e.preventDefault()
    isResizingRef.current = true
    startXRef.current = e.clientX
    startWidthRef.current = width

    const handleMouseMove = (moveEvent: MouseEvent) => {
      if (!isResizingRef.current) return
      const delta = startXRef.current - moveEvent.clientX
      const newWidth = Math.min(Math.max(startWidthRef.current + delta, 320), 720)
      setWidth(newWidth)
    }

    const handleMouseUp = () => {
      isResizingRef.current = false
      window.removeEventListener('mousemove', handleMouseMove)
      window.removeEventListener('mouseup', handleMouseUp)
    }

    window.addEventListener('mousemove', handleMouseMove)
    window.addEventListener('mouseup', handleMouseUp)
  }

  const toggleExpand = () => {
    setWidth(prev => (prev > 450 ? 380 : 580))
  }

  const handleSubmit = async (e?: React.FormEvent) => {
    if (e) e.preventDefault()
    if (!input.trim() || isLoading) return
    const text = input.trim()
    setInput('')
    await onSendMessage(text)
  }

  const handleChip = async (chip: string) => {
    if (isLoading) return
    if (onChipClick) {
      onChipClick(chip)
    } else {
      await onSendMessage(chip)
    }
  }

  const isExpanded = width > 450

  return (
    <aside
      className="copilot-drawer-root"
      style={{ width: `${width}px` }}
      aria-label="Assistant Copilot Drawer"
    >
      {/* Horizontal Drag Resize Handle */}
      <div
        className="copilot-resize-handle"
        onMouseDown={handleMouseDownResize}
        title="Drag horizontally to resize chat window"
      >
        <div className="resize-handle-bar" />
      </div>

      {/* Header */}
      <div className="copilot-header">
        <div className="copilot-title-group">
          <div className="copilot-title-row">
            <h3 className="copilot-title">
              <span className="copilot-title-icon">✦</span>
              {title}
            </h3>
            {statusBadge && (
              <span className="copilot-status-badge">{statusBadge}</span>
            )}
          </div>
          {subtitle && <p className="copilot-subtitle">{subtitle}</p>}
        </div>

        <div className="copilot-controls-group">
          <button
            type="button"
            className={`copilot-control-btn ${isExpanded ? 'active' : ''}`}
            onClick={toggleExpand}
            title={isExpanded ? 'Collapse width to standard' : 'Expand width horizontally'}
          >
            <span>{isExpanded ? '⤡ Compact' : '⤢ Expand'}</span>
          </button>

          {onClearHistory && messages.length > 0 && (
            <button
              type="button"
              className="copilot-clear-btn"
              onClick={onClearHistory}
              title="Clear conversation history"
              disabled={isLoading}
            >
              <span>Clear</span>
            </button>
          )}

          <button
            type="button"
            className="copilot-close-btn"
            onClick={onClose}
            title="Close Assistant"
            aria-label="Close Assistant"
          >
            <span>✕ Close</span>
          </button>
        </div>
      </div>

      {/* Optional Questionnaire / Suggested Chips */}
      {suggestionChips && suggestionChips.length > 0 && (
        <div className="copilot-chips-container">
          {suggestionChips.map((chip, idx) => (
            <button
              key={idx}
              type="button"
              className="copilot-chip"
              onClick={() => handleChip(chip)}
              disabled={isLoading}
            >
              {chip}
            </button>
          ))}
        </div>
      )}

      {/* Message Thread (Read-Only Multi-Turn History) */}
      <div className="copilot-thread">
        {messages.length === 0 ? (
          <div className="copilot-empty-state">
            <span className="copilot-empty-icon">✦</span>
            {suggestionChips && suggestionChips.length > 0
              ? 'Click a suggested question chip above or ask any question below to interact.'
              : 'Ask any question below to start an interactive consultation.'}
          </div>
        ) : (
          messages.map((msg, index) => {
            const roleClass = msg.role === 'user' ? 'user' : 'ai'
            const roleLabel = msg.role === 'user' ? 'You' : 'Finnie Copilot'
            return (
              <div
                key={msg.id || index}
                className={`copilot-bubble ${roleClass}`}
              >
                <div className="copilot-bubble-header">
                  <span className="copilot-bubble-role">
                    {roleLabel}
                    {msg.role === 'assistant' && (
                      <span className="copilot-readonly-tag">Read-Only</span>
                    )}
                  </span>
                  {msg.timestamp && (
                    <span className="copilot-bubble-time">
                      {formatMessageTimestamp(msg.timestamp)}
                    </span>
                  )}
                </div>
                <div className="copilot-bubble-body">
                  {renderFormattedContent(msg.content)}
                </div>
              </div>
            )
          })
        )}

        {isLoading && (
          <div className="copilot-thinking">
            <span className="copilot-thinking-orb">✦</span>
            <span>{loadingText}</span>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Footer & Input Bar */}
      <div className="copilot-footer">
        <form onSubmit={handleSubmit} className="copilot-input-form">
          <input
            type="text"
            className="copilot-input"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={inputPlaceholder}
            disabled={isLoading}
          />
          <button
            type="submit"
            className="copilot-send-btn"
            disabled={isLoading || !input.trim()}
          >
            {isLoading ? 'Thinking…' : 'Send ⚡'}
          </button>
        </form>

        {disclaimerText && (
          <p className="copilot-disclaimer">{disclaimerText}</p>
        )}
      </div>
    </aside>
  )
}
