import type { TabId } from '../../App'
import './Sidebar.css'

interface NavItem {
  id: TabId
  icon: string
  label: string
}

const NAV_ITEMS: NavItem[] = [
  { id: 'dashboard', icon: '🏠', label: 'Dashboard' },
  { id: 'chat',      icon: '💬', label: 'Deep Q&A' },
  { id: 'portfolio', icon: '📈', label: 'Portfolio Analyst' },
  { id: 'market',    icon: '🌐', label: 'Market Insights' },
  { id: 'goals',     icon: '🎯', label: 'Goal Planner' },
]

interface SidebarProps {
  activeTab: TabId
  onTabChange: (tab: TabId) => void
}

export default function Sidebar({ activeTab, onTabChange }: SidebarProps) {
  return (
    <aside className="sidebar">
      {/* Logo */}
      <div className="sidebar-logo">
        <div className="logo-icon" />
        <span>FINNIE AI</span>
      </div>

      {/* Navigation */}
      <nav className="sidebar-nav">
        {NAV_ITEMS.map((item) => (
          <button
            key={item.id}
            className={`nav-item ${activeTab === item.id ? 'active' : ''}`}
            onClick={() => onTabChange(item.id)}
          >
            <span className="nav-icon">{item.icon}</span>
            <span>{item.label}</span>
          </button>
        ))}
      </nav>

      {/* System Status */}
      <div className="sidebar-footer">
        <div className="glass-card status-card">
          <p className="status-label">SYSTEM STATUS</p>
          <p className="status-value">● ALL AGENTS ACTIVE</p>
        </div>
      </div>
    </aside>
  )
}
