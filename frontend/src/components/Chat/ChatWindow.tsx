import { useEffect, useRef } from 'react'
import type { Message } from '../../hooks/useChat'
import ThinkingIndicator from './ThinkingIndicator'
import './ChatWindow.css'

interface ChatWindowProps {
  messages: Message[]
  isLoading: boolean
}

export default function ChatWindow({ messages, isLoading }: ChatWindowProps) {
  const bottomRef = useRef<HTMLDivElement>(null)

  // Auto-scroll to latest message
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isLoading])

  return (
    <div className="chat-window">
      {messages.map((msg) => (
        <div key={msg.id} className={`message-row ${msg.role}`}>
          {msg.role === 'ai' && <div className="agent-orb" />}
          <div className={`bubble bubble-${msg.role}`}>
            {msg.content}
          </div>
        </div>
      ))}

      {isLoading && (
        <div className="message-row ai">
          <div className="agent-orb" />
          <ThinkingIndicator />
        </div>
      )}

      <div ref={bottomRef} />
    </div>
  )
}
