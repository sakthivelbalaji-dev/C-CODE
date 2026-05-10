import { useCallback, useEffect, useMemo, useState } from 'react'
import AppNavbar from '../components/AppNavbar'
import { apiUrl } from '../lib/api'

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

  /** One row per student: how many distinct questions passed (≥1 correct attempt) vs total in bank. */
  const studentCompletionSummary = useMemo(() => {
    if (!students.length || !questions.length) return []
    const totalQuestions = questions.length
    const solvedQuestionIdsByStudent = new Map()
    for (const attempt of attempts) {
      if (!attempt.is_correct) continue
      const sid = attempt.student_id
      if (!solvedQuestionIdsByStudent.has(sid)) {
        solvedQuestionIdsByStudent.set(sid, new Set())
      }
      solvedQuestionIdsByStudent.get(sid).add(attempt.question_id)
    }

    const rows = students.map((student) => {
      const solved = solvedQuestionIdsByStudent.get(student.id) || new Set()
      const completedCount = solved.size
      const pct =
        totalQuestions > 0 ? Math.min(100, Math.round((completedCount / totalQuestions) * 100)) : 0
      return {
        studentId: student.id,
        studentName: student.name || 'Student',
        completedCount,
        totalQuestions,
        pct,
      }
    })
    rows.sort(
      (a, b) =>
        b.completedCount - a.completedCount || a.studentName.localeCompare(b.studentName, undefined, { sensitivity: 'base' }),
    )
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
                Each row is one student. <strong className="text-brand-text/90">Completed</strong> counts questions with at least
                one <span className="text-brand-neonGreen">fully correct</span> attempt, out of{' '}
                <strong className="text-brand-text/90">{summary.totalQuestions || questions.length}</strong> questions in the bank.
              </p>
              <div className="mt-4 overflow-x-auto">
                <table className="w-full text-left text-sm">
                  <thead className="text-brand-muted">
                    <tr>
                      <th className="pb-2">Student</th>
                      <th className="pb-2">Completed</th>
                      <th className="pb-2">Progress</th>
                    </tr>
                  </thead>
                  <tbody>
                    {studentCompletionSummary.map((row) => (
                      <tr key={row.studentId} className="border-t border-brand-line">
                        <td className="py-3 font-medium text-brand-text">{row.studentName}</td>
                        <td className="py-3 tabular-nums text-brand-text">
                          <span className="text-brand-neonGreen">{row.completedCount}</span>
                          <span className="text-brand-muted"> / {row.totalQuestions}</span>
                        </td>
                        <td className="py-3">
                          <div className="flex min-w-[140px] items-center gap-3">
                            <div className="h-2 flex-1 overflow-hidden rounded-full bg-black/30 ring-1 ring-white/10">
                              <div
                                className="h-full rounded-full bg-gradient-to-r from-brand-neonBlue/90 to-brand-neonGreen/90"
                                style={{ width: `${row.pct}%` }}
                              />
                            </div>
                            <span className="w-10 shrink-0 tabular-nums text-xs text-brand-muted">{row.pct}%</span>
                          </div>
                        </td>
                      </tr>
                    ))}
                    {studentCompletionSummary.length === 0 && (
                      <tr className="border-t border-brand-line">
                        <td className="py-3 text-brand-muted" colSpan={3}>
                          {students.length === 0
                            ? 'No students loaded.'
                            : questions.length === 0
                              ? 'No questions in the bank.'
                              : 'No completion data yet.'}
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
