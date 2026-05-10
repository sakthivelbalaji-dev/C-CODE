import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import AppNavbar from '../components/AppNavbar'
import { apiUrl } from '../lib/api'
import { getAttemptOutcomePresentation } from '../lib/attemptLabels'

function ResultPage() {
  const [attempts, setAttempts] = useState([])
  const [latestAttempt, setLatestAttempt] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    const userRaw = localStorage.getItem('ccodelab_user')
    if (!userRaw) {
      setError('Please login to see results.')
      return
    }
    const user = JSON.parse(userRaw)

    const loadResults = async () => {
      try {
        const response = await fetch(apiUrl(`/attempts/?student_id=${user.id}`))
        if (!response.ok) {
          throw new Error('Unable to load results')
        }
        const data = await response.json()
        setAttempts(data)
        setLatestAttempt(data[0] || null)
      } catch (loadError) {
        setError(loadError.message)
      }
    }

    loadResults()
  }, [])

  const passPercent = useMemo(() => {
    if (!latestAttempt) return 0
    const total = latestAttempt.passed_cases + latestAttempt.failed_cases
    if (!total) return 0
    return Math.round((latestAttempt.passed_cases / total) * 100)
  }, [latestAttempt])

  const latestVerdict = useMemo(() => {
    if (!latestAttempt) {
      return { headline: 'No result yet', variant: 'muted' }
    }
    const { variant } = getAttemptOutcomePresentation(latestAttempt.is_correct, latestAttempt.feedback)
    if (variant === 'success') return { headline: 'Correct answer', variant: 'success' }
    if (variant === 'timeout') return { headline: 'Failed — timed out (you can retry)', variant: 'timeout' }
    return { headline: 'Wrong answer', variant: 'failure' }
  }, [latestAttempt])

  const verdictClass =
    latestVerdict.variant === 'success'
      ? 'text-brand-neonGreen'
      : latestVerdict.variant === 'timeout'
        ? 'text-amber-400'
        : latestVerdict.variant === 'failure'
          ? 'text-red-400'
          : 'text-brand-muted'

  const failPercent = 100 - passPercent

  return (
    <main className="min-h-screen bg-brand-bg">
      <AppNavbar />
      <section className="mx-auto max-w-5xl px-4 py-8 md:px-6">
        <div className="rounded-2xl border border-brand-line bg-brand-surface p-6">
          <h1 className="text-3xl font-bold">Result Summary</h1>
          <p className="mt-2 text-brand-muted">
            {latestAttempt ? 'Your latest coding test performance.' : 'No submissions yet.'}
          </p>

          <div className="mt-6 grid gap-4 md:grid-cols-3">
            <div className="rounded-xl border border-brand-line bg-brand-card p-4">
              <p className="text-sm text-brand-muted">Score</p>
              <p className="mt-2 text-2xl font-bold text-brand-neonBlue">
                {latestAttempt ? `${latestAttempt.score} / 100` : '0 / 100'}
              </p>
            </div>
            <div className="rounded-xl border border-brand-line bg-brand-card p-4">
              <p className="text-sm text-brand-muted">Passed</p>
              <p className="mt-2 text-2xl font-bold text-brand-neonGreen">{latestAttempt?.passed_cases || 0}</p>
            </div>
            <div className="rounded-xl border border-brand-line bg-brand-card p-4">
              <p className="text-sm text-brand-muted">Failed</p>
              <p className="mt-2 text-2xl font-bold text-red-400">{latestAttempt?.failed_cases || 0}</p>
            </div>
          </div>

          <div className="mt-6 space-y-4">
            <div>
              <div className="mb-1 flex justify-between text-sm">
                <span>Passed Test Cases</span>
                <span>{passPercent}%</span>
              </div>
              <div className="h-2 rounded-full bg-brand-card">
                <div className="h-full rounded-full bg-brand-neonGreen" style={{ width: `${passPercent}%` }} />
              </div>
            </div>
            <div>
              <div className="mb-1 flex justify-between text-sm">
                <span>Failed Test Cases</span>
                <span>{failPercent}%</span>
              </div>
              <div className="h-2 rounded-full bg-brand-card">
                <div className="h-full rounded-full bg-red-400" style={{ width: `${failPercent}%` }} />
              </div>
            </div>
          </div>

          <div className="mt-6 rounded-xl border border-brand-line bg-brand-card p-4">
            <p className={`font-semibold ${verdictClass}`}>{latestVerdict.headline}</p>
            <p className="mt-1 text-sm text-brand-muted">
              {latestAttempt?.feedback || 'Submit a question to get judge feedback here.'}
            </p>
          </div>

          <p className="mt-4 text-sm text-brand-muted">Total submissions: {attempts.length}</p>
          {error && <p className="mt-2 text-sm text-red-400">{error}</p>}

          <div className="mt-6 flex flex-wrap gap-3">
            <Link
              to={
                latestAttempt?.question_id != null
                  ? `/question?retry=${latestAttempt.question_id}`
                  : '/question'
              }
              className="rounded-lg border border-brand-neonBlue px-4 py-2 text-brand-neonBlue transition hover:bg-brand-neonBlue/10"
            >
              Try again
            </Link>
            <Link
              to="/dashboard"
              className="rounded-lg bg-brand-neonBlue px-4 py-2 font-semibold text-slate-900 transition hover:brightness-110"
            >
              Go to Dashboard
            </Link>
          </div>
        </div>
      </section>
    </main>
  )
}

export default ResultPage
