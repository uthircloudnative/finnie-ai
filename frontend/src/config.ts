/**
 * Centralized Application & API Configuration
 * ==============================================
 * Single source of truth for backend endpoints and runtime environment settings.
 */

export const API_BASE: string = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export const API_ENDPOINTS = {
  // Auth
  REGISTER: `${API_BASE}/auth/register`,
  LOGIN: `${API_BASE}/auth/login`,
  ME: `${API_BASE}/auth/me`,
  FORGOT_PASSWORD: `${API_BASE}/auth/forgot-password`,
  RESET_PASSWORD: `${API_BASE}/auth/reset-password`,

  // Core Features
  CHAT: `${API_BASE}/chat`,
  DASHBOARD: `${API_BASE}/dashboard`,
  PORTFOLIO: `${API_BASE}/portfolio`,
  PORTFOLIO_SAVE: `${API_BASE}/portfolio/save`,
  PORTFOLIO_ANALYSIS: `${API_BASE}/portfolio/analysis`,
  PORTFOLIO_DIVERSIFICATION: `${API_BASE}/portfolio/diversification`,
  MARKET_NEWS: `${API_BASE}/market/news`,
  GOALS: `${API_BASE}/goals`,
  GOALS_CALCULATE: `${API_BASE}/goals/calculate`,
  HEALTH: `${API_BASE}/health`,
} as const
