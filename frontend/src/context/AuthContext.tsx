import React, { createContext, useContext, useState, useEffect, useCallback } from 'react'
import { API_BASE } from '../config'

export interface UserProfile {
  id: string
  email: string
  full_name: string
  base_currency: string
}

interface AuthContextType {
  user: UserProfile | null
  token: string | null
  isAuthenticated: boolean
  isLoading: boolean
  error: string | null
  login: (email: string, password: string) => Promise<boolean>
  register: (email: string, password: string, fullName: string) => Promise<boolean>
  logout: () => void
  getAuthHeaders: () => Record<string, string>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [token, setToken] = useState<string | null>(() => localStorage.getItem('finnie_auth_token'))
  const [user, setUser] = useState<UserProfile | null>(null)
  const [isLoading, setIsLoading] = useState<boolean>(true)
  const [error, setError] = useState<string | null>(null)

  const getAuthHeaders = useCallback((): Record<string, string> => {
    return token ? { Authorization: `Bearer ${token}` } : {}
  }, [token])

  // Fetch active user profile when token exists
  useEffect(() => {
    let isMounted = true
    if (!token) {
      setUser(null)
      setIsLoading(false)
      return
    }

    fetch(`${API_BASE}/auth/me`, {
      headers: { Authorization: `Bearer ${token}` }
    })
      .then(res => {
        if (!res.ok) throw new Error('Session expired')
        return res.json()
      })
      .then(data => {
        if (isMounted) {
          setUser(data)
          setIsLoading(false)
        }
      })
      .catch(() => {
        if (isMounted) {
          localStorage.removeItem('finnie_auth_token')
          setToken(null)
          setUser(null)
          setIsLoading(false)
        }
      })

    return () => { isMounted = false }
  }, [token])

  const login = async (email: string, password: string): Promise<boolean> => {
    setError(null)
    try {
      const res = await fetch(`${API_BASE}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
      })

      if (!res.ok) {
        const data = await res.json().catch(() => ({}))
        throw new Error(data.detail || 'Invalid email or password')
      }

      const data = await res.json()
      localStorage.setItem('finnie_auth_token', data.access_token)
      setToken(data.access_token)
      setUser(data.user)
      return true
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Login failed'
      setError(msg)
      return false
    }
  }

  const register = async (email: string, password: string, fullName: string): Promise<boolean> => {
    setError(null)
    try {
      const res = await fetch(`${API_BASE}/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password, full_name: fullName })
      })

      if (!res.ok) {
        const data = await res.json().catch(() => ({}))
        throw new Error(data.detail || 'Registration failed')
      }

      const data = await res.json()
      localStorage.setItem('finnie_auth_token', data.access_token)
      setToken(data.access_token)
      setUser(data.user)
      return true
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Registration failed'
      setError(msg)
      return false
    }
  }

  const logout = () => {
    localStorage.removeItem('finnie_auth_token')
    setToken(null)
    setUser(null)
    setError(null)
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isAuthenticated: !!user && !!token,
        isLoading,
        error,
        login,
        register,
        logout,
        getAuthHeaders
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (!context) throw new Error('useAuth must be used within an AuthProvider')
  return context
}
