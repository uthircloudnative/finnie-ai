import React from 'react'
import type { TabId } from '../../App'
import { useAuth } from '../../context/AuthContext'
import './TopNav.css'

interface TopNavProps {
  activeTab: TabId
  onTabChange: (tab: TabId) => void
  onOpenAuthModal?: () => void
}

interface NavItem {
  id: TabId
  label: string
  icon: React.ReactNode
}

const NAV_ITEMS: NavItem[] = [
  {
    id: 'dashboard',
    label: 'Dashboard',
    icon: (
      <svg className="top-nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" />
        <polyline points="9 22 9 12 15 12 15 22" />
      </svg>
    ),
  },
  {
    id: 'chat',
    label: 'Deep Q&A',
    icon: (
      <svg className="top-nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
      </svg>
    ),
  },
  {
    id: 'holdings',
    label: 'My Holdings',
    icon: (
      <svg className="top-nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <rect x="2" y="7" width="20" height="14" rx="2" ry="2" />
        <path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16" />
      </svg>
    ),
  },
  {
    id: 'portfolio',
    label: 'Portfolio Analyst',
    icon: (
      <svg className="top-nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
      </svg>
    ),
  },
  {
    id: 'market',
    label: 'Market Insights',
    icon: (
      <svg className="top-nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="12" cy="12" r="10" />
        <line x1="2" y1="12" x2="22" y2="12" />
        <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" />
      </svg>
    ),
  },
  {
    id: 'goals',
    label: 'Goal Planner',
    icon: (
      <svg className="top-nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="12" cy="12" r="10" />
        <circle cx="12" cy="12" r="6" />
        <circle cx="12" cy="12" r="2" />
      </svg>
    ),
  },
]

export default function TopNav({ activeTab, onTabChange }: TopNavProps) {
  const { user, isAuthenticated, logout } = useAuth()

  return (
    <header className="top-navbar">
      {/* Brand */}
      <div className="nav-brand">
        <div className="brand-mark">F</div>
        <span className="brand-name">FINNIE AI</span>
      </div>

      {/* Center Navigation Tabs */}
      <nav className="nav-tabs-group" aria-label="Main Navigation">
        {NAV_ITEMS.map((item) => (
          <button
            key={item.id}
            type="button"
            className={`nav-tab-item ${activeTab === item.id ? 'active' : ''}`}
            onClick={() => onTabChange(item.id)}
          >
            {item.icon}
            <span>{item.label}</span>
          </button>
        ))}
      </nav>

      {/* Right User & Actions */}
      <div className="nav-right-actions">
        {isAuthenticated && user && (
          <div className="user-profile-pill">
            <span className="user-name">👤 {user.full_name}</span>
            <button className="auth-action-btn logout-btn" onClick={logout}>
              Sign Out
            </button>
          </div>
        )}
      </div>
    </header>
  )
}
