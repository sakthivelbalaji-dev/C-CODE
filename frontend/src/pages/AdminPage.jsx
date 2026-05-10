import { useCallback, useEffect, useMemo, useState } from 'react'
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

function readStaffUser() {
  try {
    const raw = localStorage.getItem('ccodelab_user')
    if (!raw) return null
    const u = JSON.parse(raw)
    if (u?.role === 'staff' || u?.role === 'admin') return u
    return null
  } catch {
    return null
  }
}

async function fetchBlobDownload(pathWithQuery, filename) {
  const res = await fetch(apiUrl(pathWithQuery))
  if (!res.ok) {
    const text = await res.text()
    throw new Error(text.replace(/\s+/g, ' ').trim().slice(0, 200) || res.statusText)
  }
  const blob = await res.blob()
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.rel = 'noopener'
  document.body.appendChild(a)
  a.click()
  a.remove()
  URL.revokeObjectURL(url)
}

export default function AdminPage() {
  const [students, setStudents] = useState([])
  const [questions, setQuestions] = useState([])
  const [attempts, setAttempts] = useState([])
  const [status, setStatus] = useState('')

  const [adminTab, setAdminTab] = useState('performance')
  const [catalogQuestions, setCatalogQuestions] = useState([])
  const [catalogLoading, setCatalogLoading] = useState(false)
  const [catalogStatus, setCatalogStatus] = useState('')
  const [dedupePreview, setDedupePreview] = useState(null)
  const [dedupeBusy, setDedupeBusy] = useState(false)
  const [toolsBusy, setToolsBusy] = useState(false)

  const staffUser = readStaffUser()
  const adminQs = (path) =>
    staffUser?.id != null ? `${path}?admin_id=${staffUser.id}` : path

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

  const loadCatalogForAdmin = useCallback(async () => {
    if (!staffUser?.id) {
      setCatalogStatus('Not signed in as staff.')
      return
    }
    setCatalogLoading(true)
    setCatalogStatus('')
    try {
      const res = await fetch(apiUrl(adminQs('/admin/questions')))
      if (!res.ok) {
        const detail = await res.text()
        throw new Error(detail.replace(/\s+/g, ' ').slice(0, 180) || res.statusText)
      }
      const data = await res.json()
      setCatalogQuestions(Array.isArray(data) ? data : [])
      setCatalogStatus(`Loaded ${Array.isArray(data) ? data.length : 0} questions (syllabus order).`)
    } catch (e) {
      setCatalogQuestions([])
      setCatalogStatus(e?.message || 'Failed to load catalog.')
    } finally {
      setCatalogLoading(false)
    }
  }, [staffUser?.id])

  useEffect(() => {
    if (adminTab === 'catalog' && staffUser?.id) {
      void loadCatalogForAdmin()
    }
  }, [adminTab, staffUser?.id, loadCatalogForAdmin])

  const downloadPdf = async (uniqueProblems) => {
    if (!staffUser?.id) {
      setCatalogStatus('Sign in as staff to export.')
      return
    }
    setToolsBusy(true)
    setCatalogStatus('')
    try {
      const base = `/admin/questions/export/pdf?admin_id=${staffUser.id}`
      const path = uniqueProblems ? `${base}&unique_problems=true` : base
      const name = uniqueProblems ? 'published-questions-unique.pdf' : 'published-questions.pdf'
      await fetchBlobDownload(path, name)
      setCatalogStatus(`Download started: ${name}`)
    } catch (e) {
      setCatalogStatus(e?.message || 'PDF export failed.')
    } finally {
      setToolsBusy(false)
    }
  }

  const runDedupeDryRun = async () => {
    if (!staffUser?.id) return
    setDedupeBusy(true)
    setDedupePreview(null)
    setCatalogStatus('')
    try {
      const res = await fetch(
        apiUrl(`/admin/questions/deduplicate-by-problem-stem?admin_id=${staffUser.id}&confirm=false`),
        { method: 'POST' },
      )
      const data = await res.json().catch(() => ({}))
      if (!res.ok) {
        throw new Error(data?.detail || res.statusText)
      }
      setDedupePreview(data)
    } catch (e) {
      setCatalogStatus(e?.message || 'Dedupe check failed.')
    } finally {
      setDedupeBusy(false)
    }
  }

  const runDedupeConfirm = async () => {
    if (!staffUser?.id) return
    if (!window.confirm('Delete duplicate question rows permanently? Attempts on deleted rows are removed. This cannot be undone.')) {
      return
    }
    setDedupeBusy(true)
    setCatalogStatus('')
    try {
      const res = await fetch(
        apiUrl(`/admin/questions/deduplicate-by-problem-stem?admin_id=${staffUser.id}&confirm=true`),
        { method: 'POST' },
      )
      const data = await res.json().catch(() => ({}))
      if (!res.ok) {
        throw new Error(data?.detail || res.statusText)
      }
      setDedupePreview(null)
      setCatalogStatus(
        `Deleted ${data?.deleted_count ?? 0} duplicate row(s). Kept ${data?.kept_count ?? '—'}.`,
      )
      void loadCatalogForAdmin()
      const qRes = await fetch(apiUrl('/questions/'))
      if (qRes.ok) {
        const qData = await qRes.json()
        if (Array.isArray(qData)) setQuestions(qData)
      }
    } catch (e) {
      setCatalogStatus(e?.message || 'Dedupe failed.')
    } finally {
      setDedupeBusy(false)
    }
  }

  const summary = useMemo(() => {
    const totalAttempts = attempts.length
    const totalCorrect = attempts.filter((item) => item.is_correct).length
    const avgScore = totalAttempts
      ? Math.round(attempts.reduce((sum, item) => sum + (item.score || 0), 0) / totalAttempts)
      : 0
    return {
      totalAttempts,
      totalCorrect,
      avgScore,
      totalStudents: students.length,
      totalQuestions: questions.length,
    }
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

  const tabBtn = (id, label) => (
    <button
      type="button"
      key={id}
      onClick={() => setAdminTab(id)}
      className={`rounded-lg px-4 py-2 text-sm font-medium transition ${
        adminTab === id
          ? 'bg-brand-neonBlue/20 text-brand-neonBlue ring-1 ring-brand-neonBlue/40'
          : 'text-brand-muted hover:bg-brand-card hover:text-brand-text'
      }`}
    >
      {label}
    </button>
  )

  return (
    <main className="min-h-screen bg-brand-bg">
      <AppNavbar />
      <section className="mx-auto max-w-7xl space-y-5 px-4 py-6 md:px-6">
        <header className="rounded-2xl border border-brand-line bg-brand-surface p-5">
          <p className="text-xs uppercase tracking-[0.12em] text-brand-muted">Staff</p>
          <h1 className="mt-1 text-2xl font-semibold text-brand-text">Admin</h1>
          <p className="mt-2 text-sm text-brand-muted">
            Student analytics and question-bank tools (PDF export, duplicate cleanup) use your staff session.
          </p>
          <div className="mt-4 flex flex-wrap gap-2 border-b border-brand-line/80 pb-4">
            {tabBtn('performance', 'Student performance')}
            {tabBtn('catalog', 'Question catalog (legacy tools)')}
          </div>
        </header>

        {adminTab === 'performance' && (
          <>
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
          </>
        )}

        {adminTab === 'catalog' && (
          <div className="space-y-5">
            <section className="rounded-2xl border border-brand-line bg-brand-surface p-5">
              <h2 className="text-lg font-semibold text-brand-text">Published questions PDF</h2>
              <p className="mt-1 text-sm text-brand-muted">
                Same exports as the server <code className="text-brand-neonBlue/90">/api/admin/questions/export/pdf</code>{' '}
                — full bank or one row per unique problem stem.
              </p>
              <div className="mt-4 flex flex-wrap gap-3">
                <button
                  type="button"
                  disabled={toolsBusy || !staffUser?.id}
                  onClick={() => void downloadPdf(false)}
                  className="rounded-xl border border-brand-neonBlue/50 bg-brand-neonBlue/10 px-4 py-2.5 text-sm font-medium text-brand-neonBlue transition hover:bg-brand-neonBlue/20 disabled:opacity-50"
                >
                  {toolsBusy ? '…' : 'Download full PDF'}
                </button>
                <button
                  type="button"
                  disabled={toolsBusy || !staffUser?.id}
                  onClick={() => void downloadPdf(true)}
                  className="rounded-xl border border-emerald-500/40 bg-emerald-500/10 px-4 py-2.5 text-sm font-medium text-emerald-300 transition hover:bg-emerald-500/15 disabled:opacity-50"
                >
                  {toolsBusy ? '…' : 'Download unique-problems PDF'}
                </button>
              </div>
            </section>

            <section className="rounded-2xl border border-brand-line bg-brand-surface p-5">
              <h2 className="text-lg font-semibold text-brand-text">Duplicate rows by problem name</h2>
              <p className="mt-1 text-sm text-brand-muted">
                Dry run lists database IDs that would be removed; confirm deletes duplicates (keeps first in syllabus
                order per drill title after <code className="text-xs">Qn:</code>).
              </p>
              <div className="mt-4 flex flex-wrap gap-3">
                <button
                  type="button"
                  disabled={dedupeBusy || !staffUser?.id}
                  onClick={() => void runDedupeDryRun()}
                  className="rounded-xl border border-amber-500/40 bg-amber-500/10 px-4 py-2.5 text-sm font-medium text-amber-200 transition hover:bg-amber-500/15 disabled:opacity-50"
                >
                  {dedupeBusy ? '…' : 'Run duplicate check'}
                </button>
                <button
                  type="button"
                  disabled={dedupeBusy || !staffUser?.id || !dedupePreview?.dry_run}
                  onClick={() => void runDedupeConfirm()}
                  className="rounded-xl border border-rose-500/50 bg-rose-500/10 px-4 py-2.5 text-sm font-medium text-rose-200 transition hover:bg-rose-500/20 disabled:opacity-50"
                >
                  Delete duplicates now
                </button>
              </div>
              {dedupePreview?.dry_run && (
                <div className="mt-4 rounded-xl bg-black/30 p-4 font-mono text-xs text-slate-300 ring-1 ring-white/10">
                  <p>
                    Would delete <strong className="text-amber-200">{dedupePreview.would_delete_count}</strong> row(s).
                    Would keep <strong className="text-emerald-300">{dedupePreview.would_keep_count}</strong>.
                  </p>
                  {Array.isArray(dedupePreview.would_delete_ids) && dedupePreview.would_delete_ids.length > 0 && (
                    <pre className="mt-2 max-h-40 overflow-auto whitespace-pre-wrap text-[11px] leading-relaxed">
                      IDs: {dedupePreview.would_delete_ids.join(', ')}
                    </pre>
                  )}
                </div>
              )}
            </section>

            <section className="rounded-2xl border border-brand-line bg-brand-surface p-5">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <h2 className="text-lg font-semibold text-brand-text">Catalog preview (admin API)</h2>
                <button
                  type="button"
                  disabled={catalogLoading}
                  onClick={() => void loadCatalogForAdmin()}
                  className="rounded-lg border border-brand-line px-3 py-1.5 text-xs text-brand-muted transition hover:border-brand-neonBlue hover:text-brand-neonBlue"
                >
                  {catalogLoading ? 'Refreshing…' : 'Refresh'}
                </button>
              </div>
              <p className="mt-1 text-sm text-brand-muted">
                Ordered list from <code className="text-xs">GET /api/admin/questions</code> (includes hints and metadata).
              </p>
              {catalogStatus && (
                <p className={`mt-3 text-sm ${catalogStatus.includes('Failed') ? 'text-rose-300' : 'text-emerald-300/90'}`}>
                  {catalogStatus}
                </p>
              )}
              <div className="mt-4 max-h-[min(480px,55vh)] overflow-auto rounded-xl border border-brand-line/60">
                <table className="w-full min-w-[640px] text-left text-sm">
                  <thead className="sticky top-0 bg-brand-surface text-[11px] uppercase tracking-wide text-brand-muted">
                    <tr>
                      <th className="px-3 py-2">#</th>
                      <th className="px-3 py-2">ID</th>
                      <th className="px-3 py-2">Module</th>
                      <th className="px-3 py-2">Title</th>
                      <th className="px-3 py-2">Difficulty</th>
                    </tr>
                  </thead>
                  <tbody>
                    {catalogQuestions.map((q, i) => (
                      <tr key={q.id} className="border-t border-brand-line/80">
                        <td className="px-3 py-2.5 tabular-nums text-brand-muted">{i + 1}</td>
                        <td className="px-3 py-2.5 font-mono text-xs text-brand-muted">{q.id}</td>
                        <td className="px-3 py-2.5 text-xs text-slate-400">{(q.module || '—').slice(0, 48)}</td>
                        <td className="px-3 py-2.5 text-brand-text">{q.title}</td>
                        <td className="px-3 py-2.5 capitalize text-brand-muted">{q.difficulty || '—'}</td>
                      </tr>
                    ))}
                    {catalogQuestions.length === 0 && !catalogLoading && (
                      <tr className="border-t border-brand-line">
                        <td className="px-3 py-6 text-brand-muted" colSpan={5}>
                          {staffUser?.id ? 'No rows loaded yet.' : 'Sign in as staff.'}
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </section>
          </div>
        )}
      </section>
    </main>
  )
}
