import React, { useMemo } from 'react'
import { useAuth } from '../../context/AuthContext'
import './FinnieCoinIcon.css'

export interface FinnieCoinIconProps {
  size?: number | string
  currencySymbol?: string
  isSpinning?: boolean
  className?: string
  title?: string
}

const ISO_CURRENCY_SYMBOL_MAP: Record<string, string> = {
  USD: '$',
  EUR: '€',
  GBP: '£',
  INR: '₹',
  JPY: '¥',
  CNY: '¥',
  CAD: 'C$',
  AUD: 'A$',
  CHF: 'Fr',
  SGD: 'S$',
  HKD: 'HK$',
  NZD: 'NZ$',
  KRW: '₩',
  BRL: 'R$',
  MXN: 'Mex$',
  SEK: 'kr',
  NOK: 'kr',
  AED: 'د.إ',
  SAR: '﷼'
}

export function resolveUserCurrencySymbol(baseCurrency?: string | null): string {
  if (baseCurrency) {
    const clean = baseCurrency.trim().toUpperCase()
    if (ISO_CURRENCY_SYMBOL_MAP[clean]) {
      return ISO_CURRENCY_SYMBOL_MAP[clean]
    }
    if (clean.length <= 3) {
      return baseCurrency
    }
  }

  if (typeof navigator !== 'undefined' && navigator.language) {
    const lang = navigator.language.toLowerCase()
    if (lang.includes('in') || lang.startsWith('hi')) return '₹'
    if (lang.includes('gb') || lang.startsWith('en-gb')) return '£'
    if (lang.includes('jp') || lang.startsWith('ja')) return '¥'
    if (lang.includes('ca')) return 'C$'
    if (lang.includes('au')) return 'A$'
    if (lang.includes('de') || lang.includes('fr') || lang.includes('es') || lang.includes('it') || lang.includes('nl')) return '€'
  }

  return '$'
}

export const FinnieCoinIcon: React.FC<FinnieCoinIconProps> = ({
  size = 20,
  currencySymbol,
  isSpinning = true,
  className = '',
  title = 'Finnie Sovereign Market Coin'
}) => {
  const auth = useAuth()

  const displaySymbol = useMemo(() => {
    if (currencySymbol) return currencySymbol
    return resolveUserCurrencySymbol(auth?.user?.base_currency)
  }, [currencySymbol, auth?.user?.base_currency])

  const dimension = typeof size === 'number' ? `${size}px` : size

  // Scale currency font proportionally to preserve margin inside coin border
  const fontRatio = displaySymbol.length > 2 ? 0.36 : (displaySymbol.length > 1 ? 0.44 : 0.52)

  return (
    <span
      className={`finnie-coin-container ${isSpinning ? 'finnie-coin-flipping' : ''} ${className}`}
      style={{ width: dimension, height: dimension }}
      title={title}
      aria-label={title}
      role="img"
    >
      <span className="finnie-coin-inner">
        {/* Face A (Front): Market Trendline with Milestone Data Nodes */}
        <span className="finnie-coin-face finnie-coin-front">
          <svg
            viewBox="0 0 24 24"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
            className="finnie-coin-svg"
          >
            <defs>
              <linearGradient id="finnieCoinGrad" x1="0" y1="0" x2="24" y2="24" gradientUnits="userSpaceOnUse">
                <stop offset="0%" stopColor="#fef08a" />
                <stop offset="50%" stopColor="#fbbf24" />
                <stop offset="100%" stopColor="#d97706" />
              </linearGradient>
            </defs>

            {/* Ground Baseline */}
            <line
              x1="3.5"
              y1="19.2"
              x2="20.5"
              y2="19.2"
              stroke="url(#finnieCoinGrad)"
              strokeWidth="0.9"
              strokeLinecap="round"
              opacity="0.35"
            />

            {/* 4 Asset Columns */}
            <rect x="4.6" y="14.8" width="2.2" height="4.4" rx="0.4" fill="url(#finnieCoinGrad)" opacity="0.75" />
            <rect x="8.5" y="12.2" width="2.2" height="7.0" rx="0.4" fill="url(#finnieCoinGrad)" opacity="0.75" />
            <rect x="12.4" y="9.5" width="2.2" height="9.7" rx="0.4" fill="url(#finnieCoinGrad)" opacity="0.75" />
            <rect x="16.3" y="6.8" width="2.2" height="12.4" rx="0.4" fill="url(#finnieCoinGrad)" opacity="0.75" />

            {/* Ultra-Thin 3-Step Trendline (1.0px) */}
            <path
              d="M3.8 16.5 L5.7 14 L8.0 14.8 L12.0 10.2 L14.2 11.2 L19.8 4.6"
              stroke="#fef08a"
              strokeWidth="1.0"
              strokeLinecap="round"
              strokeLinejoin="round"
            />

            {/* Small Milestone Node Circles at Intersections */}
            <circle cx="5.7" cy="14" r="1.1" fill="#fef08a" stroke="#b45309" strokeWidth="0.4" />
            <circle cx="8.0" cy="14.8" r="0.9" fill="#fbbf24" />
            <circle cx="12.0" cy="10.2" r="1.1" fill="#fef08a" stroke="#b45309" strokeWidth="0.4" />
            <circle cx="14.2" cy="11.2" r="0.9" fill="#fbbf24" />

            {/* Crisp Arrowhead without glow */}
            <path
              d="M16.8 4.6 H19.8 V7.6"
              stroke="#ffffff"
              strokeWidth="1.1"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        </span>

        {/* Face B (Back): Localized User Profile Currency Symbol */}
        <span className="finnie-coin-face finnie-coin-back">
          <span
            className="finnie-coin-currency"
            style={{ fontSize: `calc(${dimension} * ${fontRatio})` }}
          >
            {displaySymbol}
          </span>
        </span>
      </span>
    </span>
  )
}

export default FinnieCoinIcon
