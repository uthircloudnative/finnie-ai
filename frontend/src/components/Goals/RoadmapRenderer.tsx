import React from 'react'

interface RoadmapRendererProps {
  markdown: string | null | undefined
}

/**
 * Parses inline markdown: **bold**, *italic*, `code`, and status badges.
 */
function renderInline(text: string): React.ReactNode[] {
  // Pattern to match bold, italic, code, or status keywords
  const tokenRegex = /(\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`|\bON TRACK\b|\bCAUTION\b|\bAT RISK\b)/g
  const parts = text.split(tokenRegex)

  return parts.map((part, index) => {
    if (part.startsWith('**') && part.endsWith('**')) {
      return <strong key={index}>{part.slice(2, -2)}</strong>
    }
    if (part.startsWith('*') && part.endsWith('*')) {
      return <em key={index}>{part.slice(1, -1)}</em>
    }
    if (part.startsWith('`') && part.endsWith('`')) {
      return <code key={index} className="inline-code">{part.slice(1, -1)}</code>
    }
    if (part === 'ON TRACK') {
      return <span key={index} className="roadmap-status-badge status-on-track">● ON TRACK</span>
    }
    if (part === 'CAUTION') {
      return <span key={index} className="roadmap-status-badge status-caution">▲ CAUTION</span>
    }
    if (part === 'AT RISK') {
      return <span key={index} className="roadmap-status-badge status-at-risk">■ AT RISK</span>
    }
    return part
  })
}

/**
 * RoadmapRenderer Component
 * ==========================
 * Renders LLM Goal Strategist markdown outputs into structured,
 * glass-finance styled HTML elements (H3, H4, UL/LI, status chips, disclaimers).
 */
export default function RoadmapRenderer({ markdown }: RoadmapRendererProps) {
  if (!markdown) return null

  const lines = markdown.split('\n')
  const elements: React.ReactNode[] = []

  let currentList: { type: 'ul' | 'ol'; items: string[] } | null = null

  const flushList = () => {
    if (!currentList) return
    const listItems = currentList.items.map((item, idx) => (
      <li key={idx} className="roadmap-list-item">
        {renderInline(item)}
      </li>
    ))

    if (currentList.type === 'ul') {
      elements.push(<ul key={`list-${elements.length}`} className="roadmap-list">{listItems}</ul>)
    } else {
      elements.push(<ol key={`list-${elements.length}`} className="roadmap-list-ordered">{listItems}</ol>)
    }
    currentList = null
  }

  for (let i = 0; i < lines.length; i++) {
    const rawLine = lines[i]
    const trimmed = rawLine.trim()

    // Empty line
    if (!trimmed) {
      flushList()
      continue
    }

    // Horizontal rule
    if (trimmed === '---' || trimmed === '***') {
      flushList()
      elements.push(<hr key={`hr-${i}`} className="roadmap-divider" />)
      continue
    }

    // Headers
    if (trimmed.startsWith('### ')) {
      flushList()
      elements.push(
        <h3 key={`h3-${i}`} className="roadmap-h3">
          {renderInline(trimmed.replace(/^###\s+/, ''))}
        </h3>
      )
      continue
    }

    if (trimmed.startsWith('#### ')) {
      flushList()
      elements.push(
        <h4 key={`h4-${i}`} className="roadmap-h4">
          {renderInline(trimmed.replace(/^####\s+/, ''))}
        </h4>
      )
      continue
    }

    if (trimmed.startsWith('# ') || trimmed.startsWith('## ')) {
      flushList()
      elements.push(
        <h3 key={`h-${i}`} className="roadmap-h3">
          {renderInline(trimmed.replace(/^#+\s+/, ''))}
        </h3>
      )
      continue
    }

    // Bullet lists (- or * )
    const bulletMatch = trimmed.match(/^[-*]\s+(.*)$/)
    if (bulletMatch) {
      if (!currentList || currentList.type !== 'ul') {
        flushList()
        currentList = { type: 'ul', items: [] }
      }
      currentList.items.push(bulletMatch[1])
      continue
    }

    // Numbered lists (1. 2. )
    const numberMatch = trimmed.match(/^\d+\.\s+(.*)$/)
    if (numberMatch) {
      if (!currentList || currentList.type !== 'ol') {
        flushList()
        currentList = { type: 'ol', items: [] }
      }
      currentList.items.push(numberMatch[1])
      continue
    }

    // Compliance / Disclaimer callout
    if (trimmed.startsWith('$NFA') || trimmed.startsWith('NFA:')) {
      flushList()
      elements.push(
        <div key={`nfa-${i}`} className="roadmap-disclaimer">
          <span className="disclaimer-badge">⚖️ Compliance Note</span>
          <p className="disclaimer-text">{renderInline(trimmed)}</p>
        </div>
      )
      continue
    }

    // Regular paragraph
    flushList()
    elements.push(
      <p key={`p-${i}`} className="roadmap-paragraph">
        {renderInline(trimmed)}
      </p>
    )
  }

  // Flush any open trailing list
  flushList()

  return <div className="roadmap-rendered-content">{elements}</div>
}
