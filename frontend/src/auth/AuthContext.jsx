import { createContext, useContext, useState, useEffect } from 'react'
import {
  login as cognitoLogin,
  logout as cognitoLogout,
  getCurrentUser,
  isCognitoConfigured,
} from './cognito'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!isCognitoConfigured()) {
      // No Cognito — skip auth (local dev)
      setUser({ email: 'local', token: null })
      setLoading(false)
      return
    }
    getCurrentUser().then((u) => {
      setUser(u)
      setLoading(false)
    })
  }, [])

  const login = async (email, password) => {
    const session = await cognitoLogin(email, password)
    setUser({
      email,
      token: session.getIdToken().getJwtToken(),
    })
  }

  const logout = () => {
    cognitoLogout()
    setUser(null)
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        token: user?.token || null,
        login,
        logout,
        loading,
        isAuthenticated: !!user,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
