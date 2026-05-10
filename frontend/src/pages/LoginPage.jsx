import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { apiUrl } from '../lib/api'
import {
  ALLOWED_EMAIL_DOMAIN,
  EMAIL_DOMAIN_REJECT_MESSAGE,
  isAllowedInstitutionalEmail,
} from '../lib/emailPolicy'

/** Must match backend app/staff_policy.py default allowlist for UX hints only */
const STAFF_ALLOWED_EMAIL_HINTS = [
  'hod.aids@rajalakshmi.edu.in',
  'staff.aids@rajalakshmi.edu.in',
]

function LoginPage() {
  const navigate = useNavigate()
  const [authMode, setAuthMode] = useState('login')
  const [role, setRole] = useState('student')
  const [form, setForm] = useState({ name: '', email: '', password: '' })
  const [message, setMessage] = useState('')
  const [loading, setLoading] = useState(false)

  const isSignup = authMode === 'signup'
  const isStaffPath = role === 'staff'

  const handleChange = (key, value) => {
    setForm((prev) => ({ ...prev, [key]: value }))
  }

  const handleSubmit = async (event) => {
    event.preventDefault()
    setLoading(true)
    setMessage('')

    if (!isAllowedInstitutionalEmail(form.email)) {
      setMessage(EMAIL_DOMAIN_REJECT_MESSAGE)
      setLoading(false)
      return
    }

    const endpoint = isSignup ? '/auth/signup' : '/auth/login'
    const emailNorm = form.email.trim().toLowerCase()
    const payload = isSignup
      ? { name: form.name || role, email: emailNorm, password: form.password, role }
      : { email: emailNorm, password: form.password, role }

    try {
      const response = await fetch(apiUrl(endpoint), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })
      const responseText = await response.text()
      let data = {}
      if (responseText) {
        try {
          data = JSON.parse(responseText)
        } catch {
          data = {}
        }
      }
      if (!response.ok) {
        throw new Error(data.detail || `Authentication failed (${response.status})`)
      }
      if (!data?.id) {
        throw new Error('Unexpected server response. Please try again.')
      }
      localStorage.setItem('ccodelab_user', JSON.stringify(data))
      navigate(data.role === 'staff' || data.role === 'admin' ? '/admin' : '/dashboard')
    } catch (error) {
      if (error instanceof TypeError) {
        setMessage('Cannot reach backend API. Start both servers with: npm run dev:full')
      } else {
        setMessage(error.message)
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="grid min-h-screen bg-brand-bg lg:grid-cols-2">
      <section className="relative hidden overflow-hidden border-r border-brand-line bg-heroGlow p-12 lg:flex lg:flex-col lg:justify-between">
        <div className="absolute inset-0 bg-gradient-to-br from-brand-neonBlue/20 to-brand-neonGreen/10" />
        <div className="relative">
          <h1 className="text-4xl font-bold text-brand-text">C Code Lab</h1>
          <p className="mt-4 max-w-md text-brand-muted">
            Practice C programming in a test-driven coding environment designed for students.
          </p>
        </div>
        <div className="relative rounded-xl border border-brand-neonBlue/40 bg-brand-surface/70 p-6 shadow-neon">
          <p className="font-mono text-sm text-brand-neonBlue">$ gcc solution.c -o solution</p>
          <p className="mt-2 font-mono text-sm text-brand-neonGreen">Build Successful. Ready to run tests.</p>
        </div>
      </section>

      <section className="flex items-center justify-center p-6">
        <div className="w-full max-w-md rounded-2xl border border-brand-line bg-brand-surface p-8 shadow-neon">
          <div className="rounded-lg border border-brand-line bg-brand-card p-1">
            <div className="grid grid-cols-2 gap-1">
              {['student', 'staff'].map((item) => (
                <button
                  key={item}
                  type="button"
                  onClick={() => setRole(item)}
                  className={`rounded-md px-3 py-2 text-sm capitalize transition ${
                    role === item ? 'bg-brand-neonBlue text-slate-900' : 'text-brand-muted hover:bg-brand-surface'
                  }`}
                >
                  {item}
                </button>
              ))}
            </div>
          </div>

          <h2 className="mt-5 text-2xl font-semibold">
            {isStaffPath
              ? `Staff ${isSignup ? 'Signup' : 'Login'}`
              : `${role === 'student' ? 'Student' : 'Staff'} ${isSignup ? 'Signup' : 'Login'}`}
          </h2>
          <p className="mt-2 text-sm text-brand-muted">
            {isStaffPath
              ? isSignup
                ? 'First time: create your password here using one of the two staff emails below. After that, use Login.'
                : 'Sign in with your staff email and password. Students must use the Student tab. First visit: use Sign up below.'
              : isSignup
                ? 'Create your account to start coding.'
                : 'Sign in to continue your coding journey.'}{' '}
            <span className="block pt-1 font-medium text-brand-text/85">
              Only @{ALLOWED_EMAIL_DOMAIN} addresses are permitted (no Gmail / other domains).
            </span>
            {isStaffPath && (
              <span className="mt-2 block text-xs text-brand-muted">
                Authorised staff emails only:{' '}
                <span className="font-mono text-brand-text/90">{STAFF_ALLOWED_EMAIL_HINTS.join(' · ')}</span>
                . Any other address is rejected by the server.
              </span>
            )}
          </p>

          <form onSubmit={handleSubmit} className="mt-8 space-y-4">
            {isSignup && (
              <label className="block text-sm">
                <span className="mb-1 block text-brand-muted">Name</span>
                <input
                  type="text"
                  value={form.name}
                  onChange={(e) => handleChange('name', e.target.value)}
                  placeholder={isStaffPath ? 'Your display name' : `${role} name`}
                  className="w-full rounded-lg border border-brand-line bg-brand-card px-3 py-2 text-brand-text outline-none transition focus:border-brand-neonBlue"
                  required
                />
              </label>
            )}
            <label className="block text-sm">
              <span className="mb-1 block text-brand-muted">Email</span>
              <input
                type="email"
                placeholder={`name@${ALLOWED_EMAIL_DOMAIN}`}
                value={form.email}
                onChange={(e) => handleChange('email', e.target.value)}
                className="w-full rounded-lg border border-brand-line bg-brand-card px-3 py-2 text-brand-text outline-none transition focus:border-brand-neonBlue"
                required
              />
            </label>

            <label className="block text-sm">
              <span className="mb-1 block text-brand-muted">Password</span>
              <input
                type="password"
                placeholder="********"
                value={form.password}
                onChange={(e) => handleChange('password', e.target.value)}
                className="w-full rounded-lg border border-brand-line bg-brand-card px-3 py-2 text-brand-text outline-none transition focus:border-brand-neonBlue"
                required
              />
            </label>

            <button
              type="submit"
              disabled={loading}
              className="block w-full rounded-lg bg-brand-neonBlue px-4 py-2 text-center font-semibold text-slate-900 transition hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-70"
            >
              {loading ? 'Please wait...' : isSignup ? 'Create Account' : 'Login'}
            </button>
          </form>

          <button
            type="button"
            onClick={() => setAuthMode((prev) => (prev === 'login' ? 'signup' : 'login'))}
            className={`mt-4 w-full rounded-lg border px-4 py-2.5 text-center text-sm font-medium transition ${
              isStaffPath && !isSignup
                ? 'border-brand-neonGreen/50 bg-brand-neonGreen/10 text-brand-neonGreen hover:bg-brand-neonGreen/20'
                : 'border-transparent text-brand-neonBlue hover:text-brand-neonGreen'
            }`}
          >
            {isSignup ? 'Already have an account? Login' : "Don't have an account? Sign up"}
          </button>
          {message && <p className="mt-3 text-sm text-red-400">{message}</p>}
        </div>
      </section>
    </main>
  )
}

export default LoginPage
