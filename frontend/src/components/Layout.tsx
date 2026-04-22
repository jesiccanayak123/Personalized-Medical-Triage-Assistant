import { Outlet, Link, useLocation, useNavigate } from 'react-router-dom'
import { 
  LayoutDashboard, 
  Users, 
  LogOut,
  Activity,
  Menu,
  Sun,
  Moon
} from 'lucide-react'
import { useState } from 'react'
import { useAuthStore } from '../store/auth'
import { useThemeStore } from '../store/theme'
import { authApi } from '../api/client'
import clsx from 'clsx'

const navItems = [
  { path: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { path: '/patients', label: 'Patients', icon: Users },
]

export default function Layout() {
  const location = useLocation()
  const navigate = useNavigate()
  const { user, logout } = useAuthStore()
  const { theme, toggleTheme } = useThemeStore()
  const [sidebarOpen, setSidebarOpen] = useState(false)

  const handleLogout = async () => {
    try {
      await authApi.logout()
    } catch (e) {
      // Ignore errors on logout
    }
    logout()
    navigate('/login')
  }

  return (
    <div className="min-h-screen flex">
      {/* Mobile sidebar backdrop */}
      {sidebarOpen && (
        <div 
          className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside className={clsx(
        "sidebar fixed lg:static inset-y-0 left-0 z-50 w-64 backdrop-blur-xl transform transition-transform duration-200",
        sidebarOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0"
      )}>
        <div className="flex flex-col h-full">
          {/* Logo */}
          <div className="h-16 flex items-center px-6" style={{ borderBottom: '1px solid var(--color-border)' }}>
            <Activity className="w-8 h-8 text-primary-500" />
            <span className="ml-3 text-lg font-semibold bg-gradient-to-r from-primary-400 to-primary-600 bg-clip-text text-transparent">
              MedTriage
            </span>
          </div>

          {/* Navigation */}
          <nav className="flex-1 p-4 space-y-1">
            {navItems.map((item) => {
              const Icon = item.icon
              const isActive = location.pathname.startsWith(item.path)
              
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  onClick={() => setSidebarOpen(false)}
                  className={clsx(
                    "flex items-center px-4 py-3 rounded-lg transition-all duration-200",
                    isActive
                      ? "bg-primary-600/20 text-primary-500 border border-primary-600/30"
                      : "hover:bg-[var(--color-bg-hover)]"
                  )}
                  style={{
                    color: isActive ? undefined : 'var(--color-text-secondary)'
                  }}
                >
                  <Icon className="w-5 h-5" />
                  <span className="ml-3 font-medium">{item.label}</span>
                </Link>
              )
            })}
          </nav>

          {/* User section */}
          <div className="p-4" style={{ borderTop: '1px solid var(--color-border)' }}>
            <div className="flex items-center justify-between">
              <div className="flex items-center min-w-0">
                <div className="w-10 h-10 rounded-full bg-gradient-to-br from-primary-500 to-primary-700 flex items-center justify-center text-white font-semibold">
                  {user?.name?.[0] || user?.email?.[0] || '?'}
                </div>
                <div className="ml-3 min-w-0">
                  <p className="text-sm font-medium truncate" style={{ color: 'var(--color-text-primary)' }}>
                    {user?.name || 'User'}
                  </p>
                  <p className="text-xs truncate" style={{ color: 'var(--color-text-muted)' }}>
                    {user?.email}
                  </p>
                </div>
              </div>
              <button
                onClick={handleLogout}
                className="p-2 rounded-lg transition-colors hover:bg-[var(--color-bg-hover)]"
                style={{ color: 'var(--color-text-secondary)' }}
                title="Logout"
              >
                <LogOut className="w-5 h-5" />
              </button>
            </div>
          </div>
        </div>
      </aside>

      {/* Main content */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Top bar */}
        <header 
          className="h-16 backdrop-blur-sm flex items-center justify-between px-4 lg:px-6"
          style={{ 
            backgroundColor: 'var(--color-card)', 
            borderBottom: '1px solid var(--color-border)' 
          }}
        >
          <div className="flex items-center">
            <button
              className="lg:hidden p-2 rounded-lg hover:bg-[var(--color-bg-hover)]"
              style={{ color: 'var(--color-text-secondary)' }}
              onClick={() => setSidebarOpen(true)}
            >
              <Menu className="w-6 h-6" />
            </button>
            <div className="ml-4 lg:ml-0">
              <h1 className="text-lg font-semibold" style={{ color: 'var(--color-text-primary)' }}>
                {navItems.find(item => location.pathname.startsWith(item.path))?.label || 'Medical Triage'}
              </h1>
            </div>
          </div>

          {/* Theme toggle */}
          <button
            onClick={toggleTheme}
            className="theme-toggle flex items-center gap-2"
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
        </header>

        {/* Page content */}
        <main className="flex-1 overflow-auto p-4 lg:p-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
