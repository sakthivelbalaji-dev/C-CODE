import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import AppNavbar from '../components/AppNavbar'
import { apiUrl } from '../lib/api'
import { getAttemptOutcomeLabel } from '../lib/attemptLabels'

const cards = [
  {
    title: 'Start Test',
    description: 'Begin a timed coding test with hidden test cases.',
    cta: 'Start',
    to: '/question',
    icon: '▶',
  },
  {
    title: 'Practice Mode',
    description: 'Solve practice questions with instant feedback.',
    cta: 'Practice',
    to: '/question',
    icon: '</>',
  },
  {
    title: 'View Results',
    description: 'Check previous attempts and score trends.',
    cta: 'Results',
    to: '/result',
    icon: '📊',
  },
  {
    title: 'C Syllabus',
    description: 'View module-wise topics and example questions.',
    cta: 'Open Syllabus',
    to: '/syllabus',
    icon: '📘',
  },
]

function DashboardPage() {
  const [user, setUser] = useState(null)
  const [attempts, setAttempts] = useState([])

  useEffect(() => {
    const userRaw = localStorage.getItem('ccodelab_user')
    if (!userRaw) return
    const parsedUser = JSON.parse(userRaw)
    setUser(parsedUser)

    const loadAttempts = async () => {
      try {
        const response = await fetch(apiUrl(`/attempts/?student_id=${parsedUser.id}`))
        if (!response.ok) return
        const data = await response.json()
        setAttempts(Array.isArray(data) ? data : [])
      } catch {
        setAttempts([])
      }
    }

    loadAttempts()
  }, [])

  const averageScore = useMemo(() => {
    if (!attempts.length) return 0
    return Math.round(attempts.reduce((sum, attempt) => sum + attempt.score, 0) / attempts.length)
  }, [attempts])

  const latestAttempt = attempts[0]

  return (
    <main className="min-h-screen bg-brand-bg">
      <AppNavbar />
      <section className="mx-auto max-w-7xl px-4 py-10 md:px-6">
        <h1 className="text-3xl font-bold">Welcome back, {user?.name || 'Student'}!</h1>
        <p className="mt-2 text-brand-muted">Pick a mode and continue improving your C programming skills.</p>

        <div className="mt-5 grid gap-4 sm:grid-cols-3">
          <div className="rounded-xl border border-brand-line bg-brand-surface p-4">
            <p className="text-sm text-brand-muted">Total Attempts</p>
            <p className="mt-1 text-2xl font-semibold text-brand-neonBlue">{attempts.length}</p>
          </div>
          <div className="rounded-xl border border-brand-line bg-brand-surface p-4">
            <p className="text-sm text-brand-muted">Average Score</p>
            <p className="mt-1 text-2xl font-semibold text-brand-neonGreen">{averageScore}%</p>
          </div>
          <div className="rounded-xl border border-brand-line bg-brand-surface p-4">
            <p className="text-sm text-brand-muted">Latest Result</p>
            <p className="mt-1 text-sm text-brand-text">
              {latestAttempt
                ? `${latestAttempt.score} (${getAttemptOutcomeLabel(latestAttempt.is_correct, latestAttempt.feedback)})`
                : 'No submissions yet'}
            </p>
          </div>
        </div>

        <div className="mt-8 grid gap-5 md:grid-cols-2 xl:grid-cols-4">
          {cards.map((card) => (
            <article
              key={card.title}
              className="rounded-2xl border border-brand-line bg-brand-surface p-6 transition hover:-translate-y-1 hover:border-brand-neonBlue/60 hover:shadow-neon"
            >
              <div className="text-2xl">{card.icon}</div>
              <h2 className="mt-4 text-xl font-semibold">{card.title}</h2>
              <p className="mt-2 text-sm text-brand-muted">{card.description}</p>
              <Link
                to={card.to}
                className="mt-5 inline-block rounded-lg bg-brand-neonBlue px-4 py-2 text-sm font-semibold text-slate-900 transition hover:brightness-110"
              >
                {card.cta}
              </Link>
            </article>
          ))}
        </div>

      </section>
    </main>
  )
}

export default DashboardPage
