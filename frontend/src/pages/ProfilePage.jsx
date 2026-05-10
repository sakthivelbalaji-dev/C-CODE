import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { Area, AreaChart, ResponsiveContainer, Tooltip, XAxis } from 'recharts'
import AppNavbar from '../components/AppNavbar'
import { apiUrl } from '../lib/api'
import { getAttemptOutcomePresentation } from '../lib/attemptLabels'

function ProfilePage() {
  const [user, setUser] = useState(null)
  const [attempts, setAttempts] = useState([])
  const [questionMap, setQuestionMap] = useState({})
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    const userRaw = localStorage.getItem('ccodelab_user')
    if (!userRaw) {
      setError('Please login to view your profile.')
      setLoading(false)
      return
    }

    const parsedUser = JSON.parse(userRaw)
    setUser(parsedUser)

    const loadProfile = async () => {
      try {
        const [attemptsResponse, questionsResponse] = await Promise.all([
          fetch(apiUrl(`/attempts/?student_id=${parsedUser.id}`)),
          fetch(apiUrl('/questions/')),
        ])

        if (!attemptsResponse.ok) {
          throw new Error('Unable to load student attempts')
        }

        const attemptsData = await attemptsResponse.json()
        setAttempts(attemptsData)

        if (questionsResponse.ok) {
          const questionsData = await questionsResponse.json()
          const mappedQuestions = Object.fromEntries(questionsData.map((item) => [item.id, item.title]))
          setQuestionMap(mappedQuestions)
        }
      } catch (loadError) {
        setError(loadError.message || 'Unable to load profile data.')
      } finally {
        setLoading(false)
      }
    }

    loadProfile()
  }, [])

  const averageScore = useMemo(() => {
    if (!attempts.length) return 0
    return Math.round(attempts.reduce((sum, item) => sum + item.score, 0) / attempts.length)
  }, [attempts])

  const chartData = useMemo(() => {
    return [...attempts]
      .reverse()
      .slice(0, 10)
      .map((item, index) => ({
        label: `A${index + 1}`,
        score: item.score,
      }))
  }, [attempts])

  const recentAttempts = useMemo(() => attempts.slice(0, 8), [attempts])

  return (
    <main className="min-h-screen bg-brand-bg">
      <AppNavbar />
      <section className="mx-auto max-w-6xl space-y-5 px-4 py-6 md:px-6">
        <div className="rounded-2xl border border-brand-line bg-brand-surface p-6 md:p-8">
          <div className="border-b border-brand-line pb-5">
            <h1 className="text-2xl font-bold tracking-tight text-brand-text">Student Profile</h1>
            <p className="mt-1.5 text-sm text-brand-muted">Overview of your identity and aggregate results.</p>
          </div>
          <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4 lg:items-stretch">
            <ProfileCard label="Name" value={user?.name || '—'} />
            <ProfileCard label="Email" value={user?.email || '—'} compactValue />
            <ProfileCard label="Total tests" value={attempts.length.toString()} monoValue />
            <ProfileCard label="Average score" value={`${averageScore}%`} monoValue />
          </div>
        </div>

        <div className="rounded-2xl border border-brand-line bg-brand-surface p-6 md:p-8">
          <div className="border-b border-brand-line pb-4">
            <h2 className="text-lg font-semibold tracking-tight text-brand-text">Progress chart</h2>
            <p className="mt-1 text-sm text-brand-muted">Last up to 10 attempts (older → newer left to right).</p>
          </div>
          <div className="mt-6 h-64 min-h-[16rem] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chartData}>
                <defs>
                  <linearGradient id="scoreFill" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#38bdf8" stopOpacity={0.6} />
                    <stop offset="95%" stopColor="#38bdf8" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <XAxis dataKey="label" stroke="#94a3b8" />
                <Tooltip />
                <Area type="monotone" dataKey="score" stroke="#38bdf8" fill="url(#scoreFill)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="rounded-2xl border border-brand-line bg-brand-surface p-6 md:p-8">
          <div className="flex flex-wrap items-end justify-between gap-3 border-b border-brand-line pb-4">
            <div>
              <h2 className="text-lg font-semibold tracking-tight text-brand-text">Recent attempts</h2>
              <p className="mt-1 text-sm text-brand-muted">Newest first. Scores use tabular figures for alignment.</p>
            </div>
          </div>
          <div className="mt-5 -mx-1 overflow-x-auto px-1 [scrollbar-gutter:stable]">
            <table className="w-full min-w-[44rem] table-fixed border-collapse text-left text-sm">
              <colgroup>
                <col className="w-[7rem]" />
                <col />
                <col className="w-[5rem]" />
                <col className="min-w-[10rem] sm:min-w-[11rem]" />
                <col className="w-[7rem] sm:w-[8rem]" />
              </colgroup>
              <thead>
                <tr className="text-[11px] font-semibold uppercase tracking-wider text-brand-muted">
                  <th className="border-b border-brand-line py-3 pr-3 text-left">Attempt</th>
                  <th className="border-b border-brand-line px-3 py-3 text-left">Question</th>
                  <th className="border-b border-brand-line px-3 py-3 text-right font-semibold">Score</th>
                  <th className="border-b border-brand-line py-3 pl-3 text-left">Status</th>
                  <th className="border-b border-brand-line py-3 pl-3 text-right sm:text-left">Try again</th>
                </tr>
              </thead>
              <tbody className="text-brand-text">
                {recentAttempts.map((attempt) => {
                  const outcome = getAttemptOutcomePresentation(attempt.is_correct, attempt.feedback)
                  const statusClass =
                    outcome.variant === 'success'
                      ? 'text-brand-neonGreen'
                      : outcome.variant === 'timeout'
                        ? 'text-amber-400'
                        : 'text-red-400'
                  const qTitle =
                    questionMap[attempt.question_id] || `Question ${attempt.question_id}`
                  return (
                    <tr key={attempt.id} className="border-b border-brand-line/70 last:border-b-0">
                      <td className="py-3.5 pr-3 align-middle font-mono tabular-nums text-[13px] text-brand-muted">
                        #{attempt.id}
                      </td>
                      <td className="max-w-0 px-3 py-3.5 align-middle">
                        <span className="line-clamp-2 text-[13px] leading-snug text-brand-text" title={qTitle}>
                          {qTitle}
                        </span>
                      </td>
                      <td className="whitespace-nowrap px-3 py-3.5 text-right align-middle font-mono text-[13px] tabular-nums font-semibold text-brand-neonBlue">
                        {attempt.score}
                      </td>
                      <td className={`py-3.5 pl-3 align-middle text-[13px] leading-snug ${statusClass}`}>
                        {outcome.label}
                      </td>
                      <td className="py-3.5 pl-3 align-middle">
                        <Link
                          to={`/question?retry=${attempt.question_id}`}
                          className="inline-flex rounded-lg border border-brand-neonBlue/50 bg-brand-neonBlue/10 px-2.5 py-1 text-center text-[12px] font-semibold text-brand-neonBlue transition hover:bg-brand-neonBlue/20"
                        >
                          Try again
                        </Link>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
          {!loading && !recentAttempts.length && (
            <p className="mt-3 text-sm text-brand-muted">No attempts yet. Start solving problems to build profile stats.</p>
          )}
          {error && <p className="mt-3 text-sm text-red-400">{error}</p>}
        </div>
      </section>
    </main>
  )
}

function ProfileCard({ label, value, monoValue = false, compactValue = false }) {
  const valueClass = [
    monoValue ? 'font-mono tabular-nums' : '',
    compactValue ? 'break-all text-base sm:text-[15px] leading-snug' : 'break-words text-lg leading-snug',
    'font-semibold text-brand-text',
  ]
    .filter(Boolean)
    .join(' ')

  return (
    <div className="flex min-h-[5.75rem] flex-col rounded-xl border border-brand-line bg-brand-card p-4 sm:min-h-[6rem]">
      <p className="text-[11px] font-semibold uppercase tracking-wider text-brand-muted">{label}</p>
      <p className={`mt-3 flex-1 ${valueClass}`}>{value}</p>
    </div>
  )
}

export default ProfilePage
