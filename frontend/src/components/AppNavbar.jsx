import { Link, useLocation, useNavigate } from 'react-router-dom'

const navItems = [
  { label: 'Dashboard', path: '/dashboard' },
  { label: 'Leaderboard', path: '/leaderboard' },
  { label: 'Question', path: '/question' },
  { label: 'Result', path: '/result' },
  { label: 'Syllabus', path: '/syllabus' },
  { label: 'Staff', path: '/admin' },
  { label: 'Profile', path: '/profile' },
]

function AppNavbar() {
  const location = useLocation()
  const navigate = useNavigate()
  let user = null
  try {
    const raw = localStorage.getItem('ccodelab_user')
    user = raw ? JSON.parse(raw) : null
  } catch {
    user = null
  }

  const staffLike = user?.role === 'staff' || user?.role === 'admin'

  const filteredNavItems = navItems.filter((item) => {
    if (staffLike) {
      return item.path === '/admin' || item.path === '/leaderboard'
    }
    if (item.path === '/admin') return false
    return true
  })

  const initials = user?.name
    ? user.name
        .split(' ')
        .slice(0, 2)
        .map((part) => part[0]?.toUpperCase())
        .join('')
    : 'ST'

  const handleSignOut = () => {
    localStorage.removeItem('ccodelab_user')
    localStorage.removeItem('ccodelab_latest_attempt')
    navigate('/login')
  }

  return (
    <header className="sticky top-0 z-20 border-b border-brand-line bg-brand-surface/95 backdrop-blur">
      <div className="mx-auto flex w-full max-w-7xl items-center justify-between px-4 py-3 md:px-6">
        <Link to={staffLike ? '/admin' : '/dashboard'} className="text-lg font-semibold text-brand-neonBlue">
          C Code Lab
        </Link>
        <nav className="flex max-w-[70%] flex-wrap items-center justify-end gap-1.5 sm:max-w-none sm:gap-2 md:flex-nowrap">
          {filteredNavItems.map((item) => {
            const isActive = location.pathname === item.path
            return (
              <Link
                key={item.path}
                to={item.path}
                className={`rounded-md px-3 py-2 text-sm transition ${
                  isActive
                    ? 'bg-brand-neonBlue/20 text-brand-neonBlue'
                    : 'text-brand-muted hover:bg-brand-card hover:text-brand-text'
                }`}
              >
                {item.label}
              </Link>
            )
          })}
        </nav>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={handleSignOut}
            className="rounded-md border border-brand-line px-3 py-2 text-xs text-brand-muted transition hover:border-brand-neonBlue hover:text-brand-neonBlue"
          >
            Sign out
          </button>
          <div className="h-9 w-9 rounded-full bg-brand-neonBlue/20 text-center text-sm font-semibold leading-9 text-brand-neonBlue">
            {initials}
          </div>
        </div>
      </div>
    </header>
  )
}

export default AppNavbar
