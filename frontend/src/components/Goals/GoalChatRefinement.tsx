import { ChatMessage } from '../../hooks/useGoalStrategist'
import CopilotDrawer from '../Chat/CopilotDrawer'

interface GoalChatRefinementProps {
  chatHistory: ChatMessage[]
  onSendMessage: (message: string) => Promise<void>
  onClearHistory?: () => void
  isLoading: boolean
  country: string
  isExpanded?: boolean
  onToggleExpand?: () => void
  onClose?: () => void
}

export default function GoalChatRefinement({
  chatHistory,
  onSendMessage,
  onClearHistory,
  isLoading,
  country,
  onClose
}: GoalChatRefinementProps) {
  const promptChips = [
    'Should I pay down high-interest debt first or invest in equities?',
    'What if I increase monthly savings by $500?',
    'How does my debt balance affect my goal timeline and net worth?',
    country === 'INDIA' || country === 'IN'
      ? 'How do Section 80C and NPS caps affect my strategy?'
      : country === 'UK'
      ? 'How does the £20,000 ISA allowance apply here?'
      : 'How should I split savings between 401(k) and brokerage?',
    'What happens if portfolio volatility increases by 5%?',
    'Can I deduct mortgage / home loan interest under current tax rules?'
  ]

  return (
    <CopilotDrawer
      title="Autonomous Strategy Refinement"
      subtitle="Multi-turn interactive copilot with persistent read-only history."
      statusBadge="Autonomous Copilot"
      messages={chatHistory}
      isLoading={isLoading}
      loadingText="Evaluating scenario and consulting statutory guidelines..."
      onSendMessage={onSendMessage}
      onClearHistory={onClearHistory}
      onClose={onClose || (() => {})}
      suggestionChips={promptChips}
      inputPlaceholder="Ask a what-if question (e.g. 'What if I retire 2 years earlier?')..."
      storageKey="finnie_goal_copilot_width"
    />
  )
}
