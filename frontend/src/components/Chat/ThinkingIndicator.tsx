import './ThinkingIndicator.css'

export default function ThinkingIndicator() {
  return (
    <div className="thinking-bubble">
      <div className="thinking-dots">
        <span className="dot" />
        <span className="dot" />
        <span className="dot" />
      </div>
      <span className="thinking-status-text">
        Consulting financial guidelines &amp; synthesizing response…
      </span>
    </div>
  )
}
