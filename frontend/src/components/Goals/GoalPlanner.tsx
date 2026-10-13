import React, { useState, useEffect, useMemo, useRef } from 'react'
import { 
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, 
  ResponsiveContainer 
} from 'recharts'
import { useGoalStrategist, GoalConfig, LiabilityItem } from '../../hooks/useGoalStrategist'
import RoadmapRenderer from './RoadmapRenderer'
import GoalChatRefinement from './GoalChatRefinement'
import StrategyLockInModal from './StrategyLockInModal'
import FinnieCoinIcon from '../Common/FinnieCoinIcon'
import './GoalPlanner.css'

export default function GoalPlanner() {
  const { 
    goal, 
    roadmap, 
    simulationResults, 
    isLoading, 
    chatHistory, 
    confidenceScore, 
    status, 
    liabilities: hookLiabilities,
    cashflow: hookCashflow,
    calculate, 
    askRefinement, 
    clearChat,
    lockIn,
    addLiability,
    deleteLiability,
    saveCashflow
  } = useGoalStrategist()

  // --- Local State (Session Persisted) ---
  const [isCopilotOpen, setIsCopilotOpen] = useState<boolean>(() => {
    try {
      return sessionStorage.getItem('finnie_copilot_open') === 'true'
    } catch (_) {
      return false
    }
  })

  useEffect(() => {
    try {
      sessionStorage.setItem('finnie_copilot_open', String(isCopilotOpen))
    } catch (_) {}
  }, [isCopilotOpen])

  const [hasAutoCalculated, setHasAutoCalculated] = useState(false)
  const [hasSyncedInitialGoal, setHasSyncedInitialGoal] = useState(false)
  const [isLockInModalOpen, setIsLockInModalOpen] = useState(false)
  const [isCashflowOpen, setIsCashflowOpen] = useState(false)
  const [isAddingLiability, setIsAddingLiability] = useState(false)
  const [isAvalancheApplied, setIsAvalancheApplied] = useState(false)
  const [isStepUpApplied, setIsStepUpApplied] = useState(false)

  // Horizontal drag-resizing width state (persisted across sessions like CopilotDrawer)
  const [formWidth, setFormWidth] = useState<number>(() => {
    try {
      const saved = sessionStorage.getItem('finnie_goal_targets_width')
      if (saved) {
        const parsed = Number(saved)
        if (!isNaN(parsed) && parsed >= 300 && parsed <= 720) {
          return parsed
        }
      }
    } catch (_) {}
    return 310
  })

  const isResizingFormRef = useRef(false)
  const startFormXRef = useRef(0)
  const startFormWidthRef = useRef(formWidth)

  useEffect(() => {
    try {
      sessionStorage.setItem('finnie_goal_targets_width', String(formWidth))
    } catch (_) {}
  }, [formWidth])

  // Horizontal drag resizing logic for Goal Targets window
  const handleMouseDownResizeForm = (e: React.MouseEvent) => {
    e.preventDefault()
    isResizingFormRef.current = true
    startFormXRef.current = e.clientX
    startFormWidthRef.current = formWidth

    const handleMouseMove = (moveEvent: MouseEvent) => {
      if (!isResizingFormRef.current) return
      // Moving right increases width
      const delta = moveEvent.clientX - startFormXRef.current
      const maxAllowed = Math.min(window.innerWidth * 0.55, 680)
      const newWidth = Math.min(Math.max(startFormWidthRef.current + delta, 300), maxAllowed)
      setFormWidth(Math.round(newWidth))
    }

    const handleMouseUp = () => {
      isResizingFormRef.current = false
      window.removeEventListener('mousemove', handleMouseMove)
      window.removeEventListener('mouseup', handleMouseUp)
    }

    window.addEventListener('mousemove', handleMouseMove)
    window.addEventListener('mouseup', handleMouseUp)
  }

  const toggleExpandForm = () => {
    setFormWidth(prev => (prev > 420 ? 310 : 540))
  }

  const isFormExpanded = formWidth > 420

  // Auto-contract form when Copilot opens so active windows fit cleanly
  useEffect(() => {
    if (isCopilotOpen) {
      setFormWidth(310)
    }
  }, [isCopilotOpen])

  // New liability draft form
  const [newLiability, setNewLiability] = useState<LiabilityItem>({
    liability_type: 'Credit Card',
    lender_name: '',
    current_balance: 5000,
    interest_rate_apr: 22.9,
    monthly_payment: 150,
    remaining_months: 36
  })

  const [formData, setFormData] = useState<GoalConfig>(() => {
    if (goal) return goal
    try {
      const raw = sessionStorage.getItem('finnie_goal_session')
      if (raw) {
        const parsed = JSON.parse(raw)
        if (parsed.goal) return parsed.goal
      }
    } catch (_) {}
    return {
      goal_name: 'Retirement Capital',
      target_amount: 1000000,
      target_year: 2040,
      monthly_savings: 1000,
      country: 'USA',
      monthly_take_home: 6000,
      fixed_living_costs: 3200,
      monthly_discretionary_spend: 1000,
      liabilities: []
    }
  })

  // Sync initial goal, cashflow and liabilities from hook once on initial arrival
  useEffect(() => {
    if (goal && !hasSyncedInitialGoal) {
      setFormData(prev => ({
        ...prev,
        ...goal,
        monthly_take_home: goal.monthly_take_home ?? hookCashflow?.monthly_take_home ?? prev.monthly_take_home,
        fixed_living_costs: goal.fixed_living_costs ?? hookCashflow?.fixed_living_costs ?? prev.fixed_living_costs,
        monthly_discretionary_spend: goal.monthly_discretionary_spend ?? hookCashflow?.monthly_discretionary_spend ?? prev.monthly_discretionary_spend,
        liabilities: goal.liabilities?.length ? goal.liabilities : (hookLiabilities.length ? hookLiabilities : prev.liabilities)
      }))
      setHasSyncedInitialGoal(true)
      if (!roadmap && !hasAutoCalculated) {
        calculate(goal)
        setHasAutoCalculated(true)
      }
    }
  }, [goal, hookCashflow, hookLiabilities, hasSyncedInitialGoal, hasAutoCalculated, roadmap, calculate])

  // Sync hook liabilities to form data if form has none
  useEffect(() => {
    if (hookLiabilities.length > 0 && (!formData.liabilities || formData.liabilities.length === 0)) {
      setFormData(prev => ({ ...prev, liabilities: hookLiabilities }))
    }
  }, [hookLiabilities, formData.liabilities])

  // Currency symbol resolution based on selected country
  const currencySymbol = useMemo(() => {
    switch (formData.country?.toUpperCase()) {
      case 'INDIA':
      case 'IN':
        return '₹'
      case 'UK':
      case 'GB':
        return '£'
      case 'CANADA':
      case 'CA':
        return 'C$'
      case 'GERMANY':
      case 'DE':
        return '€'
      default:
        return '$'
    }
  }, [formData.country])

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target
    const numericFields = [
      'target_amount', 'target_year', 'monthly_savings', 
      'monthly_take_home', 'fixed_living_costs', 'monthly_discretionary_spend'
    ]
    setFormData(prev => ({
      ...prev,
      [name]: numericFields.includes(name) ? Number(value) : value
    }))
  }

  const handleQuickPreset = (preset: { name: string; amount: number; year: number; savings: number; country: string }) => {
    setFormData(prev => ({
      ...prev,
      goal_name: preset.name,
      target_amount: preset.amount,
      target_year: preset.year,
      monthly_savings: preset.savings,
      country: preset.country
    }))
  }

  const handleCalculate = async (e: React.FormEvent) => {
    e.preventDefault()
    // Auto-contract form to standard 310px so Center Stage generated results receive full spotlight
    setFormWidth(310)
    if (formData.monthly_take_home) {
      saveCashflow({
        monthly_take_home: formData.monthly_take_home,
        fixed_living_costs: formData.fixed_living_costs || 0,
        monthly_discretionary_spend: formData.monthly_discretionary_spend || 0,
        country: formData.country
      })
    }
    await calculate(formData)
  }

  const handleToggleCashflow = () => {
    const next = !isCashflowOpen
    setIsCashflowOpen(next)
    // Auto-expand form to 540px when viewing cash flow if copilot is closed and form is compact
    if (next && !isCopilotOpen && formWidth <= 350) {
      setFormWidth(540)
    }
  }

  const handleStartAddLiability = () => {
    setIsAddingLiability(true)
    if (!isCopilotOpen && formWidth <= 350) {
      setFormWidth(540)
    }
  }

  const handleLockInConfirm = async () => {
    const success = await lockIn()
    if (success) {
      setIsLockInModalOpen(false)
    }
  }

  // --- Liability Management ---
  const handleAddLiabilitySubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!newLiability.lender_name.trim()) return

    const created = await addLiability({
      ...newLiability,
      country: formData.country
    })

    if (created) {
      setFormData(prev => ({
        ...prev,
        liabilities: [...(prev.liabilities || []), created]
      }))
    }
    setIsAddingLiability(false)
    setNewLiability({
      liability_type: 'Credit Card',
      lender_name: '',
      current_balance: 5000,
      interest_rate_apr: 22.9,
      monthly_payment: 150,
      remaining_months: 36
    })
  }

  const handleDeleteLiability = async (id?: number, index?: number) => {
    if (id !== undefined) {
      await deleteLiability(id)
    }
    setFormData(prev => ({
      ...prev,
      liabilities: (prev.liabilities || []).filter((l, i) => (id !== undefined ? l.id !== id : i !== index))
    }))
  }

  // --- Upfront Action Levers ---
  const handleApplyDebtAvalanche = () => {
    const nextState = !isAvalancheApplied
    setIsAvalancheApplied(nextState)
    // When enabled, increase committed savings or prompt Strategist
    const promptText = nextState
      ? 'Apply Debt Avalanche strategy: aggressively target debts with APR > 10% first before index equity investing.'
      : 'Reset strategy to baseline contribution schedule.'
    askRefinement(promptText, formData)
  }

  const handleApplyPostLoanStepUp = () => {
    const nextState = !isStepUpApplied
    setIsStepUpApplied(nextState)
    const promptText = nextState
      ? 'Enable Post-Loan Auto-Step-Up: automatically roll over retired monthly loan EMIs directly into monthly equity savings once loans reach zero balance.'
      : 'Disable Post-Loan Auto-Step-Up and maintain flat savings schedule.'
    askRefinement(promptText, formData)
  }

  // --- Real-Time Solvency Math ---
  const activeLiabilities = formData.liabilities || []
  const totalMonthlyDebtPayments = activeLiabilities.reduce((sum, l) => sum + (l.monthly_payment || 0), 0)
  const totalDebtBalance = activeLiabilities.reduce((sum, l) => sum + (l.current_balance || 0), 0)
  const freeCashFlow = (formData.monthly_take_home || 0) - (formData.fixed_living_costs || 0) - (formData.monthly_discretionary_spend || 0)
  const netMargin = freeCashFlow - (formData.monthly_savings || 0) - totalMonthlyDebtPayments
  const isSolvent = netMargin >= 0

  // High APR liabilities check
  const hasHighAprDebt = activeLiabilities.some(l => l.interest_rate_apr >= 10.0)

  // --- Data Preparation for Recharts ---
  const fanChartData = simulationResults ? simulationResults.years_axis.map((y: number, i: number) => ({
    year: y,
    p05: Math.round(simulationResults.p05_path?.[i] ?? 0),
    p25: Math.round(simulationResults.p25_path?.[i] ?? 0),
    p50: Math.round(simulationResults.median_path?.[i] ?? 0),
    p75: Math.round(simulationResults.p75_path?.[i] ?? 0),
    p95: Math.round(simulationResults.p95_path?.[i] ?? 0),
  })) : []

  const amortizationData = simulationResults ? simulationResults.years_axis.map((y: number, i: number) => ({
    year: y,
    debt: Math.round(simulationResults.debt_path?.[i] ?? 0),
    net_worth: Math.round(simulationResults.net_worth_path?.[i] ?? (simulationResults.median_path?.[i] ?? 0)),
  })) : []

  const confidencePercent = simulationResults?.confidence_score ?? confidenceScore ?? 0

  const statusBadge = confidencePercent >= 70 ? (
    <span className="roadmap-status-badge status-on-track">● ON TRACK</span>
  ) : confidencePercent >= 40 ? (
    <span className="roadmap-status-badge status-caution">▲ CAUTION</span>
  ) : (
    <span className="roadmap-status-badge status-at-risk">■ AT RISK</span>
  )

  return (
    <div className="tab-panel goal-planner-root">
      {/* ── 3-BAR EXPANSIVE WORKSPACE ── */}
      <div className="goal-workspace-3col">

        {/* ── COLUMN 1: GOAL TARGETS & CASH FLOW (WITH CO-LOCATED ACTIONS) ── */}
        <section 
          className={`glass-card column-targets ${isFormExpanded ? 'expanded' : ''}`}
          style={{ width: `${formWidth}px` }}
        >
          {/* Horizontal Drag Resize Handle (Right Border) */}
          <div
            className="targets-resize-handle"
            onMouseDown={handleMouseDownResizeForm}
            title="Drag horizontally to resize Goal Targets window"
          >
            <div className="resize-handle-bar" />
          </div>

          <div className="targets-card-header">
            <h3 className="targets-title">
              {/* Precision Crosshair Target Icon */}
              <svg className="fin-icon-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="12" cy="12" r="10" />
                <line x1="22" y1="12" x2="18" y2="12" />
                <line x1="6" y1="12" x2="2" y2="12" />
                <line x1="12" y1="6" x2="12" y2="2" />
                <line x1="12" y1="22" x2="12" y2="18" />
              </svg>
              Goal Targets
            </h3>
            <div className="targets-header-actions">
              <button
                type="button"
                className={`btn-expand-form ${isFormExpanded ? 'active' : ''}`}
                onClick={toggleExpandForm}
                title={isFormExpanded ? 'Contract to standard width (310px)' : 'Expand to middle of screen (540px)'}
                aria-label={isFormExpanded ? 'Contract to standard width' : 'Expand to middle of screen'}
              >
                <svg className="fin-icon-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2">
                  {isFormExpanded ? (
                    <>
                      <polyline points="4 14 10 14 10 20" />
                      <polyline points="20 10 14 10 14 4" />
                      <line x1="14" y1="10" x2="21" y2="3" />
                      <line x1="3" y1="21" x2="10" y2="14" />
                    </>
                  ) : (
                    <>
                      <polyline points="15 3 21 3 21 9" />
                      <polyline points="9 21 3 21 3 15" />
                      <line x1="21" y1="3" x2="14" y2="10" />
                      <line x1="3" y1="21" x2="10" y2="14" />
                    </>
                  )}
                </svg>
                <span>{isFormExpanded ? '⤡ Compact' : '⤢ Expand'}</span>
              </button>
              <span className="targets-badge-pill">CONFIG</span>
            </div>
          </div>

          <form className="targets-form-body" onSubmit={handleCalculate}>
            {/* 1. Upfront Country Scope Selector */}
            <div className="input-block">
              <label>Country of Residence</label>
              <select 
                className="goal-input country-select-highlight" 
                name="country"
                value={formData.country} 
                onChange={handleInputChange} 
              >
                <option value="USA">🇺🇸 United States (USD · IRS Rules)</option>
                <option value="INDIA">🇮🇳 India (INR · 80C / NPS Rules)</option>
                <option value="UK">🇬🇧 United Kingdom (GBP · ISA Rules)</option>
                <option value="CANADA">🇨🇦 Canada (CAD · RRSP / TFSA Rules)</option>
                <option value="GERMANY">🇩🇪 Germany (EUR · Sparer Rules)</option>
              </select>
            </div>

            {/* 2. Core Goal Inputs */}
            <div className="input-block">
              <label>Goal Title</label>
              <input 
                className="goal-input" 
                name="goal_name"
                value={formData.goal_name} 
                onChange={handleInputChange} 
                placeholder="e.g. Retirement Capital" 
              />
            </div>

            <div className="input-block">
              <label>Target Amount ({currencySymbol})</label>
              <input 
                className="goal-input" 
                name="target_amount"
                type="number" 
                step="10000"
                value={formData.target_amount} 
                onChange={handleInputChange} 
              />
            </div>

            <div className="input-block">
              <label>Target Horizon (Year)</label>
              <input 
                className="goal-input" 
                name="target_year"
                type="number" 
                min="2026" 
                max="2070"
                value={formData.target_year} 
                onChange={handleInputChange} 
              />
            </div>

            <div className="input-block">
              <label>Monthly Savings ({currencySymbol})</label>
              <input 
                className="goal-input" 
                name="monthly_savings"
                type="number" 
                step="100"
                value={formData.monthly_savings} 
                onChange={handleInputChange} 
              />
            </div>

            {/* 3. Progressive Disclosure: Cash Flow & Liabilities */}
            <div className="cashflow-accordion-card">
              <button
                type="button"
                className="cashflow-accordion-header"
                onClick={handleToggleCashflow}
                aria-expanded={isCashflowOpen}
              >
                <div className="accordion-title-cluster">
                  <svg 
                    className={`fin-icon-svg accordion-arrow ${isCashflowOpen ? 'expanded' : ''}`}
                    viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"
                  >
                    <polyline points="9 18 15 12 9 6" />
                  </svg>
                  <span>Cash Flow & Liabilities</span>
                </div>
                <span className="accordion-count-badge">
                  {activeLiabilities.length > 0 ? `${activeLiabilities.length} Debt${activeLiabilities.length > 1 ? 's' : ''}` : 'Optional'}
                </span>
              </button>

              {isCashflowOpen && (
                <div className="cashflow-accordion-body">
                  {/* Monthly Cash Flow Inflows & Outflows */}
                  <div className="cashflow-inputs-grid">
                    <div className="input-block">
                      <label>Monthly Take-Home ({currencySymbol})</label>
                      <input
                        className="goal-input"
                        name="monthly_take_home"
                        type="number"
                        step="100"
                        value={formData.monthly_take_home || ''}
                        onChange={handleInputChange}
                        placeholder="e.g. 6000"
                      />
                    </div>
                    <div className="input-block">
                      <label>Fixed Living Costs ({currencySymbol})</label>
                      <input
                        className="goal-input"
                        name="fixed_living_costs"
                        type="number"
                        step="100"
                        value={formData.fixed_living_costs || ''}
                        onChange={handleInputChange}
                        placeholder="e.g. 3200"
                      />
                    </div>
                    <div className="input-block">
                      <label>Discretionary Spend ({currencySymbol})</label>
                      <input
                        className="goal-input"
                        name="monthly_discretionary_spend"
                        type="number"
                        step="50"
                        value={formData.monthly_discretionary_spend || ''}
                        onChange={handleInputChange}
                        placeholder="e.g. 1000"
                      />
                    </div>
                  </div>

                  {/* Real-Time Solvency Meter */}
                  <div className={`solvency-meter-box ${isSolvent ? 'solvent' : 'deficit'}`}>
                    <div className="solvency-meter-header">
                      <span className="solvency-status-dot"></span>
                      <strong className="solvency-title">
                        {isSolvent ? 'Solvency Positive' : 'Cash-Flow Deficit'}
                      </strong>
                    </div>
                    <div className="solvency-metrics-row">
                      <span>Free Cash Flow: <strong>{currencySymbol}{Math.round(freeCashFlow).toLocaleString()}/mo</strong></span>
                      <span>Debt Service: <strong>{currencySymbol}{Math.round(totalMonthlyDebtPayments).toLocaleString()}/mo</strong></span>
                    </div>
                    <div className="solvency-net-badge">
                      {isSolvent 
                        ? `Available Margin: +${currencySymbol}${Math.round(netMargin).toLocaleString()}/mo`
                        : `Deficit: -${currencySymbol}${Math.round(Math.abs(netMargin)).toLocaleString()}/mo (Outflows exceed Net Pay)`}
                    </div>
                  </div>

                  {/* Active Liabilities List */}
                  <div className="liabilities-header-row">
                    <label>Active Liabilities ({activeLiabilities.length})</label>
                    {!isAddingLiability && (
                      <button
                        type="button"
                        className="btn-add-liability-micro"
                        onClick={handleStartAddLiability}
                      >
                        + Add Debt
                      </button>
                    )}
                  </div>

                  {activeLiabilities.length > 0 && (
                    <div className="liabilities-stack">
                      {activeLiabilities.map((item, idx) => (
                        <div key={item.id ?? idx} className="liability-item-row">
                          <div className="liability-info-left">
                            <span className="liability-type-badge">{item.liability_type}</span>
                            <span className="liability-lender-title">{item.lender_name}</span>
                            <span className="liability-detail-sub">
                              {currencySymbol}{item.current_balance.toLocaleString()} @ 
                              <span className={item.interest_rate_apr >= 10 ? 'apr-alert' : ''}> {item.interest_rate_apr}% APR</span>
                            </span>
                          </div>
                          <div className="liability-action-right">
                            <span className="liability-monthly-payment">{currencySymbol}{item.monthly_payment}/mo</span>
                            <button
                              type="button"
                              className="btn-remove-liability"
                              onClick={() => handleDeleteLiability(item.id, idx)}
                              title="Delete liability"
                            >
                              ✕
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Inline Add Liability Micro-Form */}
                  {isAddingLiability && (
                    <div className="add-liability-form-inline">
                      <div className="form-sub-header">Add Outstanding Debt</div>
                      <div className="input-block">
                        <label>Debt Type</label>
                        <select
                          className="goal-input"
                          value={newLiability.liability_type}
                          onChange={(e) => setNewLiability(prev => ({ ...prev, liability_type: e.target.value }))}
                        >
                          <option value="Credit Card">Credit Card</option>
                          <option value="Auto Loan">Auto Loan</option>
                          <option value="Home Mortgage">Home Mortgage</option>
                          <option value="Student Loan">Student Loan</option>
                          <option value="Personal Loan">Personal Loan</option>
                        </select>
                      </div>
                      <div className="input-block">
                        <label>Lender / Account Name</label>
                        <input
                          className="goal-input"
                          value={newLiability.lender_name}
                          onChange={(e) => setNewLiability(prev => ({ ...prev, lender_name: e.target.value }))}
                          placeholder="e.g. Chase Sapphire, Wells Fargo"
                        />
                      </div>
                      <div className="form-row-2col">
                        <div className="input-block">
                          <label>Balance ({currencySymbol})</label>
                          <input
                            className="goal-input"
                            type="number"
                            value={newLiability.current_balance}
                            onChange={(e) => setNewLiability(prev => ({ ...prev, current_balance: Number(e.target.value) }))}
                          />
                        </div>
                        <div className="input-block">
                          <label>APR (%)</label>
                          <input
                            className="goal-input"
                            type="number"
                            step="0.1"
                            value={newLiability.interest_rate_apr}
                            onChange={(e) => setNewLiability(prev => ({ ...prev, interest_rate_apr: Number(e.target.value) }))}
                          />
                        </div>
                      </div>
                      <div className="form-row-2col">
                        <div className="input-block">
                          <label>Payment ({currencySymbol}/mo)</label>
                          <input
                            className="goal-input"
                            type="number"
                            value={newLiability.monthly_payment}
                            onChange={(e) => setNewLiability(prev => ({ ...prev, monthly_payment: Number(e.target.value) }))}
                          />
                        </div>
                        <div className="input-block">
                          <label>Months Left</label>
                          <input
                            className="goal-input"
                            type="number"
                            value={newLiability.remaining_months}
                            onChange={(e) => setNewLiability(prev => ({ ...prev, remaining_months: Number(e.target.value) }))}
                          />
                        </div>
                      </div>
                      <div className="form-btn-actions">
                        <button type="button" className="btn-save-liability" onClick={handleAddLiabilitySubmit}>
                          Save Debt
                        </button>
                        <button type="button" className="btn-cancel-liability" onClick={() => setIsAddingLiability(false)}>
                          Cancel
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Institutional Benchmark Profiles */}
            <div className="benchmark-presets-section">
              <label>Benchmark Profiles</label>
              <div className="benchmark-pills-stack">
                <button
                  type="button"
                  className="benchmark-pill"
                  onClick={() => handleQuickPreset({ name: 'Retirement Capital', amount: 1000000, year: 2040, savings: 1000, country: 'USA' })}
                >
                  <span className="benchmark-name">Retirement Capital</span>
                  <span className="benchmark-spec">$1.0M · 2040</span>
                </button>
                <button
                  type="button"
                  className="benchmark-pill"
                  onClick={() => handleQuickPreset({ name: 'Real Estate Equity', amount: 250000, year: 2030, savings: 1500, country: 'USA' })}
                >
                  <span className="benchmark-name">Real Estate Equity</span>
                  <span className="benchmark-spec">$250k · 2030</span>
                </button>
                <button
                  type="button"
                  className="benchmark-pill"
                  onClick={() => handleQuickPreset({ name: 'Growth Portfolio', amount: 500000, year: 2035, savings: 800, country: 'USA' })}
                >
                  <span className="benchmark-name">Growth Portfolio</span>
                  <span className="benchmark-spec">$500k · 2035</span>
                </button>
              </div>
            </div>

            {/* ── CO-LOCATED ACTIONS RIGHT HERE INSIDE GOAL TARGETS ── */}
            <div className="targets-actions-cluster">
              {/* Primary Action 1: Calculate / Recalculate */}
              <button className="calculate-btn btn-primary-recalc" type="submit" disabled={isLoading}>
                <svg className="fin-icon-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                  <polyline points="23 6 13.5 15.5 8.5 10.5 1 18" />
                  <polyline points="17 6 23 6 23 12" />
                </svg>
                <span>{isLoading ? 'Calculating 10,000 Scenarios...' : (simulationResults ? 'Recalculate Roadmap' : 'Generate Roadmap')}</span>
              </button>

              {/* Primary Action 2: Lock In & Save Goal */}
              <button 
                className="btn-lockin-target" 
                type="button" 
                onClick={() => setIsLockInModalOpen(true)}
                disabled={!simulationResults || status === 'LOCKED' || isLoading}
              >
                <svg className="fin-icon-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                  <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
                  <path d="M7 11V7a5 5 0 0 1 10 0v4" />
                </svg>
                <span>{status === 'LOCKED' ? 'Strategy Locked & Saved' : 'Lock In & Save Goal'}</span>
              </button>
            </div>
          </form>
        </section>

        {/* ── COLUMN 2: EXPANSIVE CENTER STAGE (TWIN CHARTS + LEVERS + SYNTHESIS) ── */}
        <section className="column-center-stage">
          {simulationResults ? (
            <>
              {/* Top Tier: CARD 1 — Invested Wealth Fan Chart */}
              <div className="glass-card center-chart-card">
                <div className="telemetry-bar-header">
                  <div className="telemetry-left">
                    {statusBadge}
                    <span className="roadmap-confidence-badge">
                      {confidencePercent.toFixed(1)}% Chance of Reaching Goal
                    </span>
                    <span className="telemetry-target-summary">
                      Target: <strong>{currencySymbol}{formData.target_amount.toLocaleString()} by {formData.target_year}</strong> ({currencySymbol}{formData.monthly_savings.toLocaleString()}/mo)
                    </span>
                  </div>
                  <div className="chart-header-actions">
                    {!isCopilotOpen && (
                      <button 
                        type="button" 
                        className="ask-finnie-toggle"
                        onClick={() => setIsCopilotOpen(true)}
                      >
                        <FinnieCoinIcon size={16} />
                        Ask Finnie
                      </button>
                    )}
                  </div>
                </div>

                <div className="chart-legend-subrow">
                  <span className="chart-subhead-title">CHART 1: PROJECTED INVESTMENT GROWTH</span>
                  <div className="legend-items-right">
                    <span className="legend-item"><strong style={{ color: 'var(--accent-cyan)' }}>●</strong> Expected Outcome (Most Likely Path)</span>
                    <span className="legend-item"><strong style={{ color: 'rgba(0,240,255,0.4)' }}>▨</strong> Likely Range (Market Highs & Lows)</span>
                  </div>
                </div>

                <div className="chart-canvas-wrapper">
                  <ResponsiveContainer width="100%" height={145}>
                    <AreaChart data={fanChartData} syncId="finnie-goal-charts" margin={{ top: 8, right: 25, left: 10, bottom: 0 }}>
                      <defs>
                        <linearGradient id="band90Grad" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#00f0ff" stopOpacity={0.16}/>
                          <stop offset="95%" stopColor="#00f0ff" stopOpacity={0.02}/>
                        </linearGradient>
                        <linearGradient id="band50Grad" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#00f0ff" stopOpacity={0.32}/>
                          <stop offset="95%" stopColor="#00f0ff" stopOpacity={0.08}/>
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                      <XAxis dataKey="year" stroke="#64748b" tick={{ fontSize: 10 }} />
                      <YAxis stroke="#64748b" tick={{ fontSize: 10 }} tickFormatter={(val: number) => `${currencySymbol}${(val / 1000).toFixed(0)}k`} />
                      <Tooltip 
                        contentStyle={{ 
                          background: 'rgba(10, 15, 29, 0.95)', 
                          border: '1px solid rgba(0, 240, 255, 0.3)',
                          borderRadius: '8px',
                          fontSize: '11px'
                        }} 
                        formatter={(val: any) => [typeof val === 'number' ? `${currencySymbol}${val.toLocaleString()}` : String(val), 'Projected Investments']}
                      />
                      <Area type="monotone" dataKey="p95" stroke="rgba(0, 240, 255, 0.4)" strokeWidth={1} fill="url(#band90Grad)" />
                      <Area type="monotone" dataKey="p75" stroke="rgba(0, 240, 255, 0.7)" strokeWidth={1} fill="url(#band50Grad)" />
                      <Area type="monotone" dataKey="p50" stroke="#00f0ff" strokeWidth={2.5} fill="none" name="Expected Outcome" />
                      <Area type="monotone" dataKey="p25" stroke="rgba(0, 240, 255, 0.7)" strokeWidth={1} fill="none" />
                      <Area type="monotone" dataKey="p05" stroke="rgba(0, 240, 255, 0.4)" strokeWidth={1} fill="none" />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              </div>

              {/* Middle Tier: CARD 2 — Real Net Worth & Loan Payoff Journey */}
              <div className="glass-card center-chart-card card-amortization">
                <div className="telemetry-bar-header">
                  <div className="telemetry-left">
                    <span className="debt-status-badge">
                      {simulationResults.debt_free_year 
                        ? `Debt-Free by ${simulationResults.debt_free_year}` 
                        : 'Debt-Free: No Loans Reported'}
                    </span>
                    <span className="interest-saved-badge">
                      Estimated Interest Cost: {currencySymbol}{Math.round(simulationResults.total_interest_paid ?? 0).toLocaleString()}
                    </span>
                    <span className="telemetry-target-summary">
                      Remaining Loans: <strong>{currencySymbol}{totalDebtBalance.toLocaleString()}</strong> ({activeLiabilities.length} account{activeLiabilities.length === 1 ? '' : 's'})
                    </span>
                  </div>
                </div>

                <div className="chart-legend-subrow">
                  <span className="chart-subhead-title">CHART 2: REAL NET WORTH & LOAN PAYOFF PROGRESS</span>
                  <div className="legend-items-right">
                    <span className="legend-item"><strong style={{ color: '#10b981' }}>●</strong> Real Net Worth (What You Own − What You Owe)</span>
                    <span className="legend-item"><strong style={{ color: '#ef4444' }}>●</strong> Total Remaining Loans</span>
                  </div>
                </div>

                <div className="chart-canvas-wrapper">
                  <ResponsiveContainer width="100%" height={145}>
                    <AreaChart data={amortizationData} syncId="finnie-goal-charts" margin={{ top: 8, right: 25, left: 10, bottom: 0 }}>
                      <defs>
                        <linearGradient id="netWorthGrad" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#10b981" stopOpacity={0.25}/>
                          <stop offset="95%" stopColor="#10b981" stopOpacity={0.03}/>
                        </linearGradient>
                        <linearGradient id="debtGrad" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#ef4444" stopOpacity={0.25}/>
                          <stop offset="95%" stopColor="#ef4444" stopOpacity={0.03}/>
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                      <XAxis dataKey="year" stroke="#64748b" tick={{ fontSize: 10 }} />
                      <YAxis stroke="#64748b" tick={{ fontSize: 10 }} tickFormatter={(val: number) => `${currencySymbol}${(val / 1000).toFixed(0)}k`} />
                      <Tooltip 
                        contentStyle={{ 
                          background: 'rgba(10, 15, 29, 0.95)', 
                          border: '1px solid rgba(16, 185, 129, 0.3)',
                          borderRadius: '8px',
                          fontSize: '11px'
                        }} 
                        formatter={(val: any, name: any) => [
                          typeof val === 'number' ? `${currencySymbol}${val.toLocaleString()}` : String(val), 
                          name === 'net_worth' ? 'Real Net Worth' : 'Remaining Loans'
                        ]}
                      />
                      <Area type="monotone" dataKey="net_worth" stroke="#10b981" strokeWidth={2.2} fill="url(#netWorthGrad)" name="net_worth" />
                      <Area type="monotone" dataKey="debt" stroke="#ef4444" strokeWidth={2.2} fill="url(#debtGrad)" name="debt" />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              </div>

              {/* Action Levers: Smart Moves to Reach Goal Faster */}
              <div className="glass-card action-levers-card">
                <div className="levers-header">
                  <div className="levers-title">
                    <svg className="fin-icon-svg" style={{ color: 'var(--accent-cyan)', width: '16px', height: '16px' }} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" />
                    </svg>
                    <strong>Smart Moves to Hit Your Goal Faster (Action Levers)</strong>
                  </div>
                  <span className="levers-subtitle">Turn on these proven strategies to see how paying off debt early boosts your wealth</span>
                </div>
                <div className="levers-grid">
                  {/* Lever 1: Debt Avalanche */}
                  <div className={`lever-pill-box ${isAvalancheApplied ? 'applied' : ''} ${hasHighAprDebt ? 'recommended' : ''}`}>
                    <div className="lever-top-row">
                      <span className="lever-badge">STRATEGY 1: DEBT AVALANCHE</span>
                      {hasHighAprDebt && <span className="lever-tag-alert">HIGH-INTEREST LOAN DETECTED</span>}
                    </div>
                    <div className="lever-name">Pay Off High-Interest Debt First</div>
                    <div className="lever-description">
                      Focus extra cash on expensive loans (over 10% interest, like credit cards) before extra investing. Clearing high interest gives you an immediate guaranteed return and protects your wealth.
                    </div>
                    <button
                      type="button"
                      className={`btn-apply-lever ${isAvalancheApplied ? 'active' : ''}`}
                      onClick={handleApplyDebtAvalanche}
                    >
                      {isAvalancheApplied ? 'Strategy Active' : 'Try This Strategy'}
                    </button>
                  </div>

                  {/* Lever 2: Post-Loan Step-Up */}
                  <div className={`lever-pill-box ${isStepUpApplied ? 'applied' : ''}`}>
                    <div className="lever-top-row">
                      <span className="lever-badge">STRATEGY 2: POST-LOAN STEP-UP</span>
                      <span className="lever-tag-auto">AUTO-BOOST WEALTH</span>
                    </div>
                    <div className="lever-name">Turn Old Loan Payments Into Investments</div>
                    <div className="lever-description">
                      Once a loan is fully paid off, don&apos;t let that money disappear into everyday spending. Automatically roll that former monthly payment straight into your investments to hit your goal even sooner.
                    </div>
                    <button
                      type="button"
                      className={`btn-apply-lever ${isStepUpApplied ? 'active' : ''}`}
                      onClick={handleApplyPostLoanStepUp}
                    >
                      {isStepUpApplied ? 'Strategy Active' : 'Try This Strategy'}
                    </button>
                  </div>
                </div>
              </div>

              {/* Lower Tier: Strategic Roadmap Synthesis Card */}
              <div className="glass-card center-synthesis-card">
                <div className="synthesis-card-header">
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
                    <svg className="fin-icon-svg" style={{ color: 'var(--accent-cyan)' }} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <line x1="8" y1="6" x2="21" y2="6" />
                      <line x1="8" y1="12" x2="21" y2="12" />
                      <line x1="8" y1="18" x2="21" y2="18" />
                      <line x1="3" y1="6" x2="3.01" y2="6" />
                      <line x1="3" y1="12" x2="3.01" y2="12" />
                      <line x1="3" y1="18" x2="3.01" y2="18" />
                    </svg>
                    <h3 style={{ margin: 0, fontSize: '0.95rem', fontWeight: 700 }}>Strategic Roadmap Synthesis</h3>
                  </div>
                  <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                    <span className="compliance-shield-pill">
                      <svg className="fin-icon-svg" style={{ width: '11px', height: '11px' }} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
                      </svg>
                      SEC/FINRA COMPLIANT
                    </span>
                    {status === 'LOCKED' && (
                      <span className="status-locked-pill">
                        <svg className="fin-icon-svg" style={{ width: '11px', height: '11px', marginRight: '4px' }} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                          <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
                          <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
                        </svg>
                        COMMITTED
                      </span>
                    )}
                  </div>
                </div>

                <div className="synthesis-content-scroll">
                  <RoadmapRenderer markdown={roadmap} />
                </div>
              </div>
            </>
          ) : (
            <div className="glass-card roadmap-empty center-empty-card" style={{ position: 'relative' }}>
              {!isCopilotOpen && (
                <div style={{ position: 'absolute', top: '1rem', right: '1rem' }}>
                  <button 
                    type="button" 
                    className="ask-finnie-toggle"
                    onClick={() => setIsCopilotOpen(true)}
                  >
                    <FinnieCoinIcon size={16} />
                    Ask Finnie
                  </button>
                </div>
              )}
              <div className="fin-empty-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="var(--accent-cyan)" strokeWidth="1.5">
                  <circle cx="12" cy="12" r="10" />
                  <line x1="22" y1="12" x2="18" y2="12" />
                  <line x1="6" y1="12" x2="2" y2="12" />
                  <line x1="12" y1="6" x2="12" y2="2" />
                  <line x1="12" y1="22" x2="12" y2="18" />
                </svg>
              </div>
              <h2 style={{ color: '#ffffff', margin: '0.75rem 0 0.35rem 0', fontSize: '1.25rem' }}>Ready to build your roadmap?</h2>
              <p style={{ color: '#cbd5e1', maxWidth: '440px', fontSize: '0.85rem', lineHeight: 1.5 }}>
                Configure your targets on the left or select a Benchmark Profile, then click <strong>Generate Roadmap</strong> to run the real-time simulation engine.
              </p>
            </div>
          )}
        </section>

        {/* ── COLUMN 3: STRATEGY COPILOT DRAWER (ON DEMAND & HORIZONTALLY EXPANDABLE) ── */}
        {isCopilotOpen && (
          <GoalChatRefinement 
            chatHistory={chatHistory} 
            onSendMessage={(text) => askRefinement(text, formData)} 
            onClearHistory={clearChat}
            isLoading={isLoading} 
            country={formData.country}
            onClose={() => setIsCopilotOpen(false)}
          />
        )}
      </div>

      {/* Human-in-the-Loop Lock-in Modal */}
      <StrategyLockInModal
        isOpen={isLockInModalOpen}
        onClose={() => setIsLockInModalOpen(false)}
        onConfirm={handleLockInConfirm}
        goal={goal || formData}
        confidenceScore={confidencePercent}
        isLoading={isLoading}
      />
    </div>
  )
}
