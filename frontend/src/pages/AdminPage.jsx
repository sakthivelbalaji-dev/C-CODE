import { useEffect, useMemo, useState } from 'react'
import AppNavbar from '../components/AppNavbar'
import { apiUrl } from '../lib/api'

function minutesBetween(startIso, endIso) {
  const start = new Date(startIso).getTime()
  const end = new Date(endIso).getTime()
  if (!Number.isFinite(start) || !Number.isFinite(end)) return null
  const delta = Math.max(0, end - start)
  const mins = delta / 60000
  return mins < 1 ? '<1' : mins.toFixed(1)
}

function AdminPage() {
  const [students, setStudents] = useState([])
  const [questions, setQuestions] = useState([])
  const [attempts, setAttempts] = useState([])
  const [status, setStatus] = useState('')

  useEffect(() => {
    const loadPerformanceData = async () => {
      try {
        const [studentsResponse, questionsResponse, attemptsResponse] = await Promise.all([
          fetch(apiUrl('/auth/students?role=student')),
          fetch(apiUrl('/questions/')),
          fetch(apiUrl('/attempts/')),
        ])

        if (studentsResponse.ok) {
          const studentsData = await studentsResponse.json()
          setStudents(Array.isArray(studentsData) ? studentsData : [])
        } else {
          setStudents([])
          setStatus('Unable to load students right now.')
        }

        if (questionsResponse.ok) {
          const questionsData = await questionsResponse.json()
          setQuestions(Array.isArray(questionsData) ? questionsData : [])
        } else {
          setQuestions([])
          setStatus((prev) => prev || 'Unable to load questions right now.')
        }

        if (attemptsResponse.ok) {
          const attemptsData = await attemptsResponse.json()
          setAttempts(Array.isArray(attemptsData) ? attemptsData : [])
        } else {
          setAttempts([])
          setStatus('Unable to load student attempts right now.')
        }

      } catch {
        setStudents([])
        setQuestions([])
        setAttempts([])
        setStatus('Could not load student performance data from server.')
      }
    }

    loadPerformanceData()
  }, [])

  const summary = useMemo(() => {
    const totalAttempts = attempts.length
    const totalCorrect = attempts.filter((item) => item.is_correct).length
    const avgScore = totalAttempts
      ? Math.round(attempts.reduce((sum, item) => sum + (item.score || 0), 0) / totalAttempts)
      : 0
    return { totalAttempts, totalCorrect, avgScore, totalStudents: students.length, totalQuestions: questions.length }
  }, [attempts, students.length, questions.length])

  const questionProgressRows = useMemo(() => {
    if (!students.length || !questions.length) return []

    const attemptByStudentQuestion = new Map()
    for (const attempt of attempts) {
      const key = `${attempt.student_id}::${attempt.question_id}`
      if (!attemptByStudentQuestion.has(key)) {
        attemptByStudentQuestion.set(key, [])
      }
      attemptByStudentQuestion.get(key).push(attempt)
    }

    for (const list of attemptByStudentQuestion.values()) {
      list.sort((a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime())
    }

    const rows = []
    for (const student of students) {
      for (const question of questions) {
        const key = `${student.id}::${question.id}`
        const grouped = attemptByStudentQuestion.get(key) || []
        const firstAttempt = grouped[0] || null
        const firstCorrect = grouped.find((item) => item.is_correct) || null
        const completed = Boolean(firstCorrect)
        let minutesTaken = '-'
        if (completed && firstAttempt && firstCorrect) {
          minutesTaken = minutesBetween(firstAttempt.created_at, firstCorrect.created_at) ?? '-'
        }

        let statusLabel = 'Not Started'
        if (completed) statusLabel = 'Completed'
        else if (grouped.length > 0) statusLabel = 'In Progress'

        rows.push({
          studentId: student.id,
          studentName: student.name || 'Student',
          studentEmail: student.email,
          questionId: question.id,
          questionTitle: question.title,
          statusLabel,
          minutesTaken,
          attemptsCount: grouped.length,
        })
      }
    }
    return rows
  }, [students, questions, attempts])

  return (
    <main className="min-h-screen bg-brand-bg">
      <AppNavbar />
      <section className="mx-auto max-w-7xl space-y-5 px-4 py-6 md:px-6">
        <header className="rounded-2xl border border-brand-line bg-brand-surface p-5">
          <p className="text-xs uppercase tracking-[0.12em] text-brand-muted">Staff</p>
          <h1 className="mt-1 text-2xl font-semibold text-brand-text">Student Performance</h1>
          <p className="mt-2 text-sm text-brand-muted">
            Staff accounts are read-only here. Coding routes are restricted to students.
          </p>
        </header>

        <div className="grid gap-4 sm:grid-cols-3">
          <div className="rounded-xl border border-brand-line bg-brand-surface p-4">
            <p className="text-sm text-brand-muted">Students</p>
            <p className="mt-1 text-2xl font-semibold text-brand-neonBlue">{summary.totalStudents}</p>
          </div>
          <div className="rounded-xl border border-brand-line bg-brand-surface p-4">
            <p className="text-sm text-brand-muted">Questions</p>
            <p className="mt-1 text-2xl font-semibold text-brand-text">{summary.totalQuestions}</p>
          </div>
          <div className="rounded-xl border border-brand-line bg-brand-surface p-4">
            <p className="text-sm text-brand-muted">Total Attempts</p>
            <p className="mt-1 text-2xl font-semibold text-brand-neonGreen">{summary.totalAttempts}</p>
          </div>
        </div>

        <div className="grid gap-4 sm:grid-cols-2">
          <div className="rounded-xl border border-brand-line bg-brand-surface p-4">
            <p className="text-sm text-brand-muted">Correct Attempts</p>
            <p className="mt-1 text-2xl font-semibold text-brand-neonGreen">{summary.totalCorrect}</p>
          </div>
          <div className="rounded-xl border border-brand-line bg-brand-surface p-4">
            <p className="text-sm text-brand-muted">Average Score</p>
            <p className="mt-1 text-2xl font-semibold text-brand-text">{summary.avgScore}%</p>
          </div>
        </div>

        <section className="rounded-2xl border border-brand-line bg-brand-surface p-5">
          <h2 className="text-lg font-semibold">Student Question Completion</h2>
          <p className="mt-1 text-sm text-brand-muted">
            For every student and every question: completed/not completed and minutes to finish.
          </p>
          <div className="mt-4 overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="text-brand-muted">
                <tr>
                  <th className="pb-2">Student</th>
                  <th className="pb-2">Email</th>
                  <th className="pb-2">Question</th>
                  <th className="pb-2">Status</th>
                  <th className="pb-2">Minutes To Complete</th>
                  <th className="pb-2">Attempts</th>
                </tr>
              </thead>
              <tbody>
                {questionProgressRows.map((row) => (
                  <tr key={`${row.studentId}-${row.questionId}`} className="border-t border-brand-line">
                    <td className="py-3">{row.studentName}</td>
                    <td className="py-3">{row.studentEmail}</td>
                    <td className="py-3">{row.questionTitle}</td>
                    <td
                      className={`py-3 ${
                        row.statusLabel === 'Completed'
                          ? 'text-brand-neonGreen'
                          : row.statusLabel === 'In Progress'
                            ? 'text-amber-300'
                            : 'text-brand-muted'
                      }`}
                    >
                      {row.statusLabel}
                    </td>
                    <td className="py-3">{row.minutesTaken}</td>
                    <td className="py-3">{row.attemptsCount}</td>
                  </tr>
                ))}
                {questionProgressRows.length === 0 && (
                  <tr className="border-t border-brand-line">
                    <td className="py-3 text-brand-muted" colSpan={6}>
                      No progress rows available yet.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </section>

        {status && <p className="text-sm text-amber-300">{status}</p>}
      </section>
    </main>
  )
}

export default AdminPage
