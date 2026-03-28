import { useChat } from '../../hooks/useChat'
import ChatWindow from './ChatWindow'
import ChatInput from './ChatInput'
import './Chat.css'

export default function Chat() {
  const { messages, isLoading, sendMessage } = useChat()

  return (
    <div className="chat-container tab-panel">
      <h1 className="chat-title">Deep Q&amp;A</h1>
      <ChatWindow messages={messages} isLoading={isLoading} />
      <ChatInput onSend={sendMessage} isLoading={isLoading} />
    </div>
  )
}
