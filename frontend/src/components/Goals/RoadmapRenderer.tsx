import React from 'react'

interface RoadmapRendererProps {
  markdown: string | null | undefined
}

/**
 * Parses inline markdown: **bold**, *italic*, `code`, and status badges.
 */
export function renderInline(text: string): React.ReactNode[] {
  // Pattern to match bold, italic, code, or status keywords (with or without underscores)
  const tokenRegex = /(\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`|\bON[_\s]TRACK\b|\bCAUTION\b|\bAT[_\s]RISK\b)/gi
  const parts = text.split(tokenRegex)

  return parts.map((part, index) => {
    if (part.startsWith('**') && part.endsWith('**')) {
      return <strong key={index} style={{ color: 'var(--text-bright)', fontWeight: 600 }}>{part.slice(2, -2)}</strong>
    }
    if (part.startsWith('*') && part.endsWith('*')) {
      return <em key={index}>{part.slice(1, -1)}</em>
    }
    if (part.startsWith('`') && part.endsWith('`')) {
      return <code key={index} className="inline-code">{part.slice(1, -1)}</code>
    }
    const normalized = part.toUpperCase().replace('_', ' ')
    if (normalized === 'ON TRACK') {
      return <span key={index} className="roadmap-status-badge status-on-track">● ON TRACK</span>
    }
    if (normalized === 'CAUTION') {
      return <span key={index} className="roadmap-status-badge status-caution">▲ CAUTION</span>
    }
    if (normalized === 'AT RISK') {
      return <span key={index} className="roadmap-status-badge status-at-risk">■ AT RISK</span>
    }
    return part
  })
}

/**
 * Parses multiline chat message strings with bold, italics, bullets, and linebreaks.
 */
export function renderFormattedContent(text: string): React.ReactNode {
  if (!text) return null
  const lines = text.split('\n')
  return lines.map((line, idx) => {
    const trimmed = line.trim()
    if (!trimmed) {
      return <span key={idx} style={{ display: 'block', height: '0.45rem' }} />
    }
    if (trimmed.startsWith('- ') || trimmed.startsWith('• ') || trimmed.startsWith('* ')) {
      const bulletContent = trimmed.replace(/^[-•*]\s+/, '')
      return (
        <div key={idx} style={{ display: 'flex', gap: '0.45rem', marginTop: '0.2rem', marginBottom: '0.2rem' }}>
          <span style={{ color: 'var(--accent-cyan)', flexShrink: 0 }}>•</span>
          <div>{renderInline(bulletContent)}</div>
        </div>
      )
    }
    return (
      <span key={idx} style={{ display: 'block', marginBottom: idx === lines.length - 1 ? 0 : '0.35rem' }}>
        {renderInline(line)}
      </span>
    )
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

    // Executive Status & Confidence Banner Detection
    // Matches e.g. **Status**: AT_RISK · **Confidence Score**: 0.0%
    const statusBannerMatch = trimmed.match(/(?:\*\*Status\*\*|Status):\s*([A-Za-z_]+)\s*(?:[·|\-])\s*(?:\*\*Confidence Score\*\*|Confidence Score):\s*([0-9.]+%?)/i)
    if (statusBannerMatch) {
      flushList()
      const rawStatus = statusBannerMatch[1].toUpperCase().replace('_', ' ')
      const scoreStr = statusBannerMatch[2]
      const statusClass = rawStatus === 'ON TRACK' ? 'status-on-track' : (rawStatus === 'CAUTION' ? 'status-caution' : 'status-at-risk')
      const statusIcon = rawStatus === 'ON TRACK' ? '●' : (rawStatus === 'CAUTION' ? '▲' : '■')
      
      elements.push(
        <div key={`status-banner-${i}`} className="roadmap-status-strip">
          <div className="status-pill-group">
            <span className="status-pill-label">STRATEGIC STATUS</span>
            <span className={`roadmap-status-badge ${statusClass}`}>{statusIcon} {rawStatus}</span>
          </div>
          <div className="status-pill-group">
            <span className="status-pill-label">CONFIDENCE SCORE</span>
            <span className="roadmap-confidence-badge">{scoreStr.includes('%') ? scoreStr : `${scoreStr}%`}</span>
          </div>
        </div>
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
          <span className="disclaimer-badge">
            <svg style={{ width: '12px', height: '12px', display: 'inline-block', verticalAlign: 'middle', marginRight: '4px' }} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
            </svg>
            Statutory Compliance Note
          </span>
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
