import { useState } from 'react'
import Sidebar from './components/Sidebar/Sidebar'
import Dashboard from './components/Dashboard/Dashboard'
import Chat from './components/Chat/Chat'
import PortfolioAnalyst from './components/Portfolio/PortfolioAnalyst'
import MyHoldings from './components/Portfolio/MyHoldings'
import MarketInsights from './components/Market/MarketInsights'
import GoalPlanner from './components/Goals/GoalPlanner'
import './App.css'

export type TabId = 'dashboard' | 'chat' | 'holdings' | 'portfolio' | 'market' | 'goals'

function App() {
  const [activeTab, setActiveTab] = useState<TabId>('chat')

  const renderTab = () => {
    switch (activeTab) {
      case 'dashboard':  return <Dashboard />
      case 'chat':       return <Chat />
      case 'holdings':   return <MyHoldings />
      case 'portfolio':  return <PortfolioAnalyst />
      case 'market':     return <MarketInsights />
      case 'goals':      return <GoalPlanner />
    }
  }

  return (
    <div className="app-layout">
      <Sidebar activeTab={activeTab} onTabChange={setActiveTab} />
      <main className="app-content">
        {renderTab()}
      </main>
    </div>
  )
}

export default App
