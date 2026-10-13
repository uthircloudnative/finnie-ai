import { useChat } from '../../hooks/useChat'
import ChatWindow from './ChatWindow'
import ChatInput from './ChatInput'
import FinnieCoinIcon from '../Common/FinnieCoinIcon'
import './Chat.css'

export default function Chat() {
  const { messages, isLoading, sendMessage, clearMessages } = useChat()

  const handleSelectPrompt = (prompt: string) => {
    sendMessage(prompt)
  }

  return (
    <div className="chat-container tab-panel">
      {/* ── Polished Chat Header Section ── */}
      <div className="chat-header-section">
        <div className="chat-header-top">
          <div className="chat-title-group">
            <h1 className="chat-title">
              <span className="chat-title-icon">
                <FinnieCoinIcon size={24} />
              </span>
              Deep Q&amp;A
            </h1>
            <span className="chat-status-badge">Agentic Routing Enabled</span>
          </div>

          {messages.length > 0 && (
            <button
              type="button"
              className="chat-clear-btn"
              onClick={clearMessages}
              disabled={isLoading}
              title="Clear chat history"
            >
              Clear History
            </button>
          )}
        </div>
        <p className="chat-subtitle">
          Autonomous multi-agent financial reasoning, statutory tax guidance &amp; educational portfolio Q&amp;A.
        </p>
      </div>

      {/* ── Message Thread & Input ── */}
      <ChatWindow 
        messages={messages} 
        isLoading={isLoading} 
        onSelectPrompt={handleSelectPrompt} 
      />
      <ChatInput onSend={sendMessage} isLoading={isLoading} />
    </div>
  )
}
