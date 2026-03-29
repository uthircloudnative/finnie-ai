import { useState, useCallback, useEffect } from 'react'
import { usePortfolio, type HoldingInput } from '../../hooks/usePortfolio'
import './MyHoldings.css'

interface RowState {
  id: string // UUID for React key stability
  ticker: string
  shares: string // Keep as string for controlled input
  exchange: string // e.g. "NASDAQ" or "NSE"
  isNew?: boolean // Flag for auto-focusing new rows
}

function emptyRow(isNew = false): RowState {
  return { id: crypto.randomUUID(), ticker: '', shares: '', exchange: 'NYSE', isNew }
}

export default function MyHoldings() {
  const { holdings, exchanges, isLoading, isSaving, error, savePortfolio } = usePortfolio()

  const [rows, setRows] = useState<RowState[]>([emptyRow()])
  const [saveSuccess, setSaveSuccess] = useState(false)
  const [isDirty, setIsDirty] = useState(false) // true = form has unsaved changes
  const [hydrated, setHydrated] = useState(false)

  // 1. Properly hydrate the form rows from the backend data ONCE on mount or load
  useEffect(() => {
    if (!hydrated && !isLoading && holdings.length > 0) {
      setRows(holdings.map(h => ({ 
        id: crypto.randomUUID(), 
        ticker: h.ticker, 
        shares: String(h.shares),
        exchange: h.exchange || 'NYSE'
      })))
      setHydrated(true)
    }
  }, [holdings, isLoading, hydrated])

  const addRow = () => {
    setIsDirty(true)
    setRows(prev => [...prev, emptyRow(true)])
  }

  const removeRow = (id: string) => {
    setIsDirty(true)
    setRows(prev => {
      const next = prev.filter(r => r.id !== id)
      // Always keep at least one row, but mark it as 'new' for focus
      return next.length > 0 ? next : [emptyRow(true)]
    })
  }

  const updateRow = useCallback((id: string, field: 'ticker' | 'shares' | 'exchange', value: string) => {
    setSaveSuccess(false)
    setIsDirty(true)
    setRows(prev => prev.map(r => r.id === id ? { ...r, [field]: value } : r))
  }, [])

  const handleSave = async () => {
    setSaveSuccess(false)
    
    // Filter out invalid rows (missing ticker or non-positive shares)
    const inputs: HoldingInput[] = rows
      .filter(r => r.ticker.trim() && r.shares.trim())
      .map(r => {
        // Find the country code from the selected exchange
        const ex = exchanges.find(e => e.exchange_code === r.exchange)
        return { 
          ticker: r.ticker.trim().toUpperCase(), 
          shares: parseFloat(r.shares),
          exchange: r.exchange,
          country: ex?.country_code || 'US'
        }
      })
      .filter(r => r.shares > 0)

    if (inputs.length === 0) return

    const ok = await savePortfolio(inputs)
    if (ok) {
      setSaveSuccess(true)
      setIsDirty(false)
      // Sync form rows back to exactly what the backend saved
      // This also cleans up IDs and ensures formatting is identical
      setRows(inputs.map(i => ({ 
        id: crypto.randomUUID(), 
        ticker: i.ticker, 
        shares: String(i.shares),
        exchange: i.exchange
      })))
    }
  }

  const validRowCount = rows.filter(r => r.ticker.trim() && parseFloat(r.shares) > 0).length

  return (
    <div className="tab-panel">
      <div className="holdings-header">
        <h1>My Holdings</h1>
        <p className="holdings-subtitle">
          Enter your current stock positions. Weights are calculated automatically based on live market prices.
        </p>
      </div>

      {/* Form Table */}
      <div className="glass-card holdings-form-card">
        <div className="holdings-table-head">
          <span>Ticker</span>
          <span>Market / Exchange</span>
          <span>Shares</span>
          <span>Action</span>
        </div>

        <div className="holdings-rows">
          {rows.map(row => (
            <div key={row.id} className="holdings-row">
              <input
                id={`ticker-${row.id}`}
                className="holdings-input holdings-ticker"
                type="text"
                placeholder="e.g. AAPL"
                value={row.ticker}
                maxLength={10}
                autoFocus={row.isNew}
                onChange={e => updateRow(row.id, 'ticker', e.target.value.toUpperCase())}
              />
              <select
                className="holdings-input holdings-exchange"
                value={row.exchange}
                onChange={e => updateRow(row.id, 'exchange', e.target.value)}
              >
                {exchanges.map(ex => (
                  <option key={`${ex.country_code}-${ex.exchange_code}`} value={ex.exchange_code}>
                    {ex.country_code === 'US' ? '🇺🇸' : 
                     ex.country_code === 'IN' ? '🇮🇳' : 
                     ex.country_code === 'GB' ? '🇬🇧' : 
                     ex.country_code === 'CA' ? '🇨🇦' : 
                     ex.country_code === 'DE' ? '🇩🇪' : '🌍'} {ex.exchange_name}
                  </option>
                ))}
              </select>
              <input
                id={`shares-${row.id}`}
                className="holdings-input holdings-shares"
                type="number"
                min="0"
                step="any"
                placeholder="e.g. 10"
                value={row.shares}
                onChange={e => updateRow(row.id, 'shares', e.target.value)}
              />
              <button
                id={`remove-row-${row.id}`}
                className="holdings-remove-btn"
                onClick={() => removeRow(row.id)}
                title="Remove this holding"
              >
                🗑
              </button>
            </div>
          ))}
        </div>

        <div className="holdings-form-footer">
          <button id="add-holding-row" className="holdings-add-btn" onClick={addRow}>
            + Add Row
          </button>
          <span className="holdings-count">
            {validRowCount} holding{validRowCount !== 1 ? 's' : ''} ready
          </span>
        </div>
      </div>

      {/* Error Banner */}
      {error && (
        <div className="holdings-error">
          ⚠️ {error}
        </div>
      )}

      {/* Success Banner */}
      {saveSuccess && (
        <div className="holdings-success">
          ✅ Portfolio saved! Head to <strong>Portfolio Analyst</strong> to run your analysis.
        </div>
      )}

      {/* Save Button */}
      <button
        id="save-portfolio-btn"
        className={`holdings-save-btn ${isSaving ? 'saving' : ''}`}
        onClick={handleSave}
        disabled={isSaving || validRowCount === 0}
      >
        {isSaving ? 'Saving…' : 'Save Portfolio'}
      </button>

      {/* Saved Holdings Summary — always visible but marked 'Modified' if dirty */}
      {!isLoading && holdings.length > 0 && (
        <div className={`glass-card holdings-saved-card ${isDirty ? 'dirty' : ''}`}>
          <div className="holdings-saved-header">
            <h3>{isDirty ? 'Currently Saved (Last State)' : 'Currently Saved'}</h3>
            {isDirty && <span className="dirty-badge">Changes Pending</span>}
          </div>
          <p className="holdings-saved-note">
            Last saved on {holdings[0]?.added_date}. Weights will be computed live from market prices during analysis.
          </p>
          <div className="holdings-saved-list">
            {holdings.map(h => (
              <div key={`${h.ticker}-${h.exchange}`} className="holdings-saved-row">
                <span className="holdings-saved-ticker">{h.ticker}</span>
                <span className="holdings-saved-market">{h.exchange} ({h.country})</span>
                <span className="holdings-saved-shares">{h.shares} shares</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {isLoading && (
        <div className="holdings-loading">Loading your saved portfolio…</div>
      )}
    </div>
  )
}
