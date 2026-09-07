/**
 * useCountryPortfolio.ts
 * ──────────────────────
 * Manages country-scoped Portfolio Analyst state.
 *
 * Session caching strategy (token-preserving):
 * - On page load, ALL country analyses are fired in PARALLEL in one go.
 * - Tab switching is always instant — it only reads from the in-memory cache.
 * - No LLM call is ever made on a tab click.
 * - "Refresh Report" is the ONLY action that clears cache and re-runs the backend.
 *
 * Loading UX:
 * - Each country tracks its own loading state independently.
 * - The displayed loading spinner reflects only the selected country.
 * - Background fetches for other countries happen silently.
 */
import { useState, useCallback, useEffect, useRef } from 'react'
import { usePortfolio, type Holding } from './usePortfolio'
import { useAuth } from '../context/AuthContext'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

// Country metadata for display
const COUNTRY_META: Record<string, { flag: string; name: string }> = {
  US: { flag: '🇺🇸', name: 'US' },
  IN: { flag: '🇮🇳', name: 'India' },
  GB: { flag: '🇬🇧', name: 'UK' },
  CA: { flag: '🇨🇦', name: 'Canada' },
  DE: { flag: '🇩🇪', name: 'Germany' },
}

export interface CountryTab {
  code: string        // "ALL" | "US" | "IN" …
  label: string       // "All Markets" | "🇺🇸 US" …
  holdingCount: number
}

export interface AnalysisResult {
  beta: number
  volatility: number
  diversification_score: number | null
  tickers: string[]
  country: string
  benchmark: string
  benchmark_name: string
  vol_thresholds: [number, number]
  sectors: Record<string, number>
  country_betas: Record<string, { beta: number; benchmark_name: string }>
  unique_countries: string[]
}

interface CacheEntry {
  analysis: string
  results: AnalysisResult
}

interface UseCountryPortfolioReturn {
  tabs: CountryTab[]
  selectedCountry: string
  setSelectedCountry: (code: string) => void
  analysis: string | null
  analysisResults: AnalysisResult | null
  isLoading: boolean        // true only when the SELECTED country is loading
  isBatchLoading: boolean   // true when ANY background fetch is still in flight
  error: string | null
  refetch: () => void
  fetchDiversification: (countryCode?: string) => Promise<{ score: number | null; error: string | null }>
}

export function useCountryPortfolio(): UseCountryPortfolioReturn {
  const { holdings } = usePortfolio()
  const { getAuthHeaders } = useAuth()
  const [selectedCountry, setSelectedCountryState] = useState<string>('ALL')

  // Per-country cache stored in a ref (survives re-renders, cleared on Refresh)
  const cache = useRef<Record<string, CacheEntry>>({})

  // Track which countries are currently being fetched (for loading indicators)
  const [loadingCountries, setLoadingCountries] = useState<Set<string>>(new Set())
  const [errors, setErrors] = useState<Record<string, string>>({})

  // Derived view state for the selected country
  const selectedCache = cache.current[selectedCountry]
  const analysis = selectedCache?.analysis ?? null
  const analysisResults = selectedCache?.results ?? null
  const isLoading = loadingCountries.has(selectedCountry)
  const isBatchLoading = loadingCountries.size > 0
  const error = errors[selectedCountry] ?? null

  // ── Derive country tabs from actual holdings ──────────────────────────
  const tabs: CountryTab[] = [
    { code: 'ALL', label: '🌍 All Markets', holdingCount: holdings.length },
    ...Array.from(
      holdings.reduce((acc, h: Holding) => {
        const code = h.country.toUpperCase()
        acc.set(code, (acc.get(code) ?? 0) + 1)
        return acc
      }, new Map<string, number>())
    ).map(([code, count]) => {
      const meta = COUNTRY_META[code]
      return {
        code,
        label: meta ? `${meta.flag} ${meta.name}` : code,
        holdingCount: count,
      }
    }),
  ]

  // ── Core fetch function (never called on tab switch, only on load/refresh) ──
  const fetchSingle = useCallback(async (countryCode: string): Promise<void> => {
    // Already in cache — skip entirely (silent no-op)
    if (cache.current[countryCode]) return

    // Mark as loading
    setLoadingCountries(prev => new Set([...prev, countryCode]))
    setErrors(prev => { const e = { ...prev }; delete e[countryCode]; return e })

    try {
      const url =
        countryCode === 'ALL'
          ? `${API_BASE}/portfolio/analysis`
          : `${API_BASE}/portfolio/analysis?country=${countryCode}`

      const res = await fetch(url, { headers: getAuthHeaders() })
      if (!res.ok) {
        const data = await res.json().catch(() => ({}))
        throw new Error(data.detail ?? `Server error ${res.status}`)
      }
      const data = await res.json()

      // Write to cache — triggers a re-render because we need the UI to update
      cache.current[countryCode] = {
        analysis: data.reply,
        results: data.analysis_results as AnalysisResult,
      }

      // Force re-render so selectedCache reflects new data
      setLoadingCountries(prev => {
        const next = new Set(prev)
        next.delete(countryCode)
        return next
      })
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Failed to fetch analysis'
      setErrors(prev => ({ ...prev, [countryCode]: msg }))
      setLoadingCountries(prev => {
        const next = new Set(prev)
        next.delete(countryCode)
        return next
      })
    }
  }, [getAuthHeaders])

  // ── Batch-load: fires ALL + each country in parallel on mount ────────
  const batchLoad = useCallback((countryCodes: string[]) => {
    const allCodes = ['ALL', ...countryCodes]
    // Fire all in parallel — fetchSingle is a no-op if already cached
    allCodes.forEach(code => { fetchSingle(code) })
  }, [fetchSingle])

  // ── Tab switch: ALWAYS instant — just updates selected state ─────────
  const setSelectedCountry = useCallback((code: string) => {
    setSelectedCountryState(code)
    // If somehow not cached yet (edge case), fire a single fetch for it
    if (!cache.current[code]) {
      fetchSingle(code)
    }
  }, [fetchSingle])

  // ── Refresh: clear cache, re-run batch load for all current tabs ──────
  const refetch = useCallback(() => {
    cache.current = {}
    setErrors({})
    const countryCodes = holdings
      .map(h => h.country.toUpperCase())
      .filter((v, i, a) => a.indexOf(v) === i) // unique
    batchLoad(countryCodes)
  }, [batchLoad, holdings])

  // ── Auto-batch-load once holdings arrive ─────────────────────────────
  const hasLoaded = useRef(false)
  useEffect(() => {
    if (holdings.length === 0 || hasLoaded.current) return
    hasLoaded.current = true
    const countryCodes = holdings
      .map(h => h.country.toUpperCase())
      .filter((v, i, a) => a.indexOf(v) === i)
    batchLoad(countryCodes)
  }, [holdings, batchLoad])

  // ── Dedicated diversification fetch (on-demand tile retry) ───────────
  const fetchDiversification = useCallback(async (countryCode?: string): Promise<{ score: number | null; error: string | null }> => {
    const targetCountry = countryCode || selectedCountry
    const url = targetCountry === 'ALL'
      ? `${API_BASE}/portfolio/diversification`
      : `${API_BASE}/portfolio/diversification?country=${targetCountry}`

    try {
      const res = await fetch(url, { headers: getAuthHeaders() })
      if (!res.ok) {
        return { score: null, error: 'Experiencing technical issue, try again later' }
      }
      const data = await res.json()
      if (data.error || data.diversification_score === null) {
        return { score: null, error: data.error || 'Experiencing technical issue, try again later' }
      }

      // Update in-memory cache entry for instant UI reactive state update
      if (cache.current[targetCountry]?.results) {
        cache.current[targetCountry] = {
          ...cache.current[targetCountry],
          results: {
            ...cache.current[targetCountry].results,
            diversification_score: data.diversification_score,
            sectors: data.sectors || cache.current[targetCountry].results.sectors
          }
        }
        // Trigger a React re-render by updating state
        setSelectedCountryState(prev => prev)
      }
      return { score: data.diversification_score, error: null }
    } catch (err) {
      return { score: null, error: 'Experiencing technical issue, try again later' }
    }
  }, [selectedCountry, getAuthHeaders])

  return {
    tabs,
    selectedCountry,
    setSelectedCountry,
    analysis,
    analysisResults,
    isLoading,
    isBatchLoading,
    error,
    refetch,
    fetchDiversification,
  }
}
