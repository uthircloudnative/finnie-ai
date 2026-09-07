import type { TabId } from '../../App'
import { useAuth } from '../../context/AuthContext'
import './Sidebar.css'

interface NavItem {
  id: TabId
  icon: string
  label: string
}

const NAV_ITEMS: NavItem[] = [
  { id: 'dashboard', icon: '🏠', label: 'Dashboard' },
  { id: 'chat',      icon: '💬', label: 'Deep Q&A' },
  { id: 'holdings',  icon: '💼', label: 'My Holdings' },
  { id: 'portfolio', icon: '📈', label: 'Portfolio Analyst' },
  { id: 'market',    icon: '🌐', label: 'Market Insights' },
  { id: 'goals',     icon: '🎯', label: 'Goal Planner' },
]

interface SidebarProps {
  activeTab: TabId
  onTabChange: (tab: TabId) => void
  onOpenAuthModal: () => void
}

export default function Sidebar({ activeTab, onTabChange, onOpenAuthModal }: SidebarProps) {
  const { user, isAuthenticated, logout } = useAuth()

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

      {/* User Profile & System Status */}
      <div className="sidebar-footer">
        <div className="glass-card status-card">
          {isAuthenticated && user ? (
            <div className="user-profile-box">
              <p className="status-label">LOGGED IN AS</p>
              <p className="status-value user-name">👤 {user.full_name}</p>
              <button className="auth-action-btn logout-btn" onClick={logout}>
                Sign Out
              </button>
            </div>
          ) : (
            <div className="user-profile-box">
              <p className="status-label">ACCOUNT</p>
              <button className="auth-action-btn login-btn" onClick={onOpenAuthModal}>
                🔑 Sign In / Register
              </button>
            </div>
          )}
        </div>
      </div>
    </aside>
  )
}
