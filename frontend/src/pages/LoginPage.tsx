import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Activity, Mail, Lock, User, AlertCircle, Sun, Moon } from 'lucide-react'
import { useAuthStore } from '../store/auth'
import { useThemeStore } from '../store/theme'
import { authApi } from '../api/client'

export default function LoginPage() {
  const navigate = useNavigate()
  const { login } = useAuthStore()
  const { theme, toggleTheme } = useThemeStore()
  const [isRegister, setIsRegister] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    name: '',
  })

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setLoading(true)

    try {
      const response = isRegister
        ? await authApi.register(formData.email, formData.password, formData.name)
        : await authApi.login(formData.email, formData.password)

      const { user, token } = response.data
      login(user, token)
      navigate('/dashboard')
    } catch (err: any) {
      // Handle different error formats
      const errorData = err.response?.data
      let errorMessage = 'An error occurred'
      
      if (typeof errorData === 'string') {
        errorMessage = errorData
      } else if (errorData?.detail) {
        // FastAPI validation errors come as array or string
        if (Array.isArray(errorData.detail)) {
          errorMessage = errorData.detail.map((e: any) => 
            typeof e === 'string' ? e : e.msg || JSON.stringify(e)
          ).join(', ')
        } else if (typeof errorData.detail === 'string') {
          errorMessage = errorData.detail
        } else {
          errorMessage = JSON.stringify(errorData.detail)
        }
      } else if (errorData?.message) {
        errorMessage = errorData.message
      }
      
      setError(errorMessage)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-4 relative overflow-hidden">
      {/* Theme toggle */}
      <button
        onClick={toggleTheme}
        className="absolute top-4 right-4 theme-toggle flex items-center gap-2 z-10"
        title={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
      >
        {theme === 'dark' ? (
          <>
            <Sun className="w-5 h-5" />
            <span className="hidden sm:inline text-sm">Light</span>
          </>
        ) : (
          <>
            <Moon className="w-5 h-5" />
            <span className="hidden sm:inline text-sm">Dark</span>
          </>
        )}
      </button>

      {/* Animated background */}
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute -top-1/2 -left-1/2 w-full h-full bg-gradient-to-br from-primary-600/20 to-transparent rounded-full blur-3xl animate-pulse-slow" />
        <div className="absolute -bottom-1/2 -right-1/2 w-full h-full bg-gradient-to-tl from-emergency-600/10 to-transparent rounded-full blur-3xl animate-pulse-slow" style={{ animationDelay: '1.5s' }} />
      </div>

      {/* Login card */}
      <div className="w-full max-w-md relative animate-fade-in">
        <div 
          className="card backdrop-blur-xl shadow-2xl"
          style={{ 
            backgroundColor: theme === 'dark' ? 'rgba(17, 24, 39, 0.7)' : 'rgba(255, 255, 255, 0.9)',
            borderColor: theme === 'dark' ? 'rgba(55, 65, 81, 0.5)' : 'rgba(226, 232, 240, 0.8)'
          }}
        >
          {/* Header */}
          <div className="text-center mb-8">
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-primary-500 to-primary-700 shadow-lg shadow-primary-600/30 mb-4">
              <Activity className="w-8 h-8 text-white" />
            </div>
            <h1 className="text-2xl font-bold" style={{ color: 'var(--color-text-primary)' }}>
              Medical Triage Assistant
            </h1>
            <p style={{ color: 'var(--color-text-secondary)' }} className="mt-2">
              {isRegister ? 'Create your account' : 'Sign in to continue'}
            </p>
          </div>

          {/* Error message */}
          {error && (
            <div className="mb-6 p-4 bg-emergency-900/50 border border-emergency-700/50 rounded-lg flex items-start gap-3 animate-slide-up">
              <AlertCircle className="w-5 h-5 text-emergency-400 flex-shrink-0 mt-0.5" />
              <p className="text-sm text-emergency-300">{error}</p>
            </div>
          )}

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-5">
            {isRegister && (
              <div>
                <label className="block text-sm font-medium mb-2" style={{ color: 'var(--color-text-secondary)' }}>
                  Name
                </label>
                <div className="relative">
                  <User className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5" style={{ color: 'var(--color-text-muted)' }} />
                  <input
                    type="text"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    className="input-field pl-12"
                    placeholder="Your name"
                    required={isRegister}
                  />
                </div>
              </div>
            )}

            <div>
              <label className="block text-sm font-medium mb-2" style={{ color: 'var(--color-text-secondary)' }}>
                Email
              </label>
              <div className="relative">
                <Mail className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5" style={{ color: 'var(--color-text-muted)' }} />
                <input
                  type="email"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  className="input-field pl-12"
                  placeholder="you@example.com"
                  required
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium mb-2" style={{ color: 'var(--color-text-secondary)' }}>
                Password
              </label>
              <div className="relative">
                <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5" style={{ color: 'var(--color-text-muted)' }} />
                <input
                  type="password"
                  value={formData.password}
                  onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                  className="input-field pl-12"
                  placeholder="••••••••"
                  required
                  minLength={6}
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'Please wait...' : (isRegister ? 'Create Account' : 'Sign In')}
            </button>
          </form>

          {/* Toggle */}
          <p className="text-center mt-6" style={{ color: 'var(--color-text-secondary)' }}>
            {isRegister ? 'Already have an account?' : "Don't have an account?"}
            <button
              type="button"
              onClick={() => {
                setIsRegister(!isRegister)
                setError(null)
              }}
              className="ml-2 text-primary-500 hover:text-primary-400 font-medium"
            >
              {isRegister ? 'Sign in' : 'Register'}
            </button>
          </p>
        </div>
      </div>
    </div>
  )
}
