import { useEffect, useState } from 'react'
import AppNavbar from '../components/AppNavbar'
import { apiUrl } from '../lib/api'

function LeaderboardPage() {
  const [user, setUser] = useState(null)
  const [leaderboard, setLeaderboard] = useState([])
  const [error, setError] = useState('')

  useEffect(() => {
    const userRaw = localStorage.getItem('ccodelab_user')
    if (userRaw) {
      try {
        setUser(JSON.parse(userRaw))
      } catch {
        setUser(null)
      }
    }

    const loadLeaderboard = async () => {
      try {
        const response = await fetch(apiUrl('/attempts/leaderboard?limit=50'))
        if (!response.ok) {
          throw new Error('Leaderboard is unavailable right now.')
        }
        const data = await response.json()
        setLeaderboard(Array.isArray(data) ? data : [])
        setError('')
      } catch (loadError) {
        setLeaderboard([])
        setError(loadError.message || 'Leaderboard is unavailable right now.')
      }
    }

    loadLeaderboard()
  }, [])

  return (
    <main className="min-h-screen bg-brand-bg">
      <AppNavbar />
      <section className="mx-auto max-w-6xl px-4 py-8 md:px-6">
        <div className="rounded-2xl border border-brand-line bg-brand-surface p-6">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <h1 className="text-2xl font-bold">Leaderboard</h1>
              <p className="mt-1 text-sm text-brand-muted">Top performers ranked by cumulative score.</p>
            </div>
            <span className="rounded-full bg-brand-neonBlue/15 px-3 py-1 text-xs font-medium text-brand-neonBlue">
              Total {leaderboard.length}
            </span>
          </div>

          {error ? (
            <p className="mt-4 rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2 text-sm text-red-300">
              {error}
            </p>
          ) : leaderboard.length === 0 ? (
            <p className="mt-4 text-sm text-brand-muted">No leaderboard data yet.</p>
          ) : (
            <div className="mt-4 overflow-x-auto">
              <table className="min-w-full text-left text-sm">
                <thead>
                  <tr className="border-b border-brand-line text-brand-muted">
                    <th className="px-3 py-2 font-medium">Rank</th>
                    <th className="px-3 py-2 font-medium">Name</th>
                    <th className="px-3 py-2 font-medium">Email</th>
                    <th className="px-3 py-2 font-medium">Score</th>
                    <th className="px-3 py-2 font-medium">Correct</th>
                    <th className="px-3 py-2 font-medium">Attempts</th>
                    <th className="px-3 py-2 font-medium">Average</th>
                  </tr>
                </thead>
                <tbody>
                  {leaderboard.map((row, index) => {
                    const isCurrentUser = row.student_id === user?.id
                    return (
                      <tr
                        key={row.student_id}
                        className={`border-b border-brand-line/60 ${isCurrentUser ? 'bg-brand-neonBlue/10' : ''}`}
                      >
                        <td className="px-3 py-2 font-semibold text-brand-text">{index + 1}</td>
                        <td className="px-3 py-2 text-brand-text">{row.student_name || 'Student'}</td>
                        <td className="px-3 py-2 text-brand-muted">{row.student_email}</td>
                        <td className="px-3 py-2 text-brand-neonGreen">{row.total_score}</td>
                        <td className="px-3 py-2 text-brand-text">{row.total_correct}</td>
                        <td className="px-3 py-2 text-brand-text">{row.total_attempts}</td>
                        <td className="px-3 py-2 text-brand-text">{Math.round(row.average_score || 0)}%</td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </section>
    </main>
  )
}

export default LeaderboardPage
