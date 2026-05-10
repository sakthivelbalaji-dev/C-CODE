import { useState } from 'react'
import { useEffect } from 'react'
import { useRef } from 'react'
import { useSearchParams } from 'react-router-dom'
import Editor from '@monaco-editor/react'
import AppNavbar from '../components/AppNavbar'
import { apiUrl } from '../lib/api'
import { applyCompilerMarkers, clearCompileFeedback } from '../lib/gccDiagnostics'
import { TIME_EXPIRED_NO_SUBMISSION_FEEDBACK_PREFIX } from '../lib/attemptLabels'

async function parseResponseJson(response) {
  const raw = await response.text()
  try {
    return raw ? JSON.parse(raw) : {}
  } catch {
    const preview = raw.replace(/\s+/g, ' ').trim().slice(0, 360)
    const detail = preview.length > 0 ? preview : '(empty response body)'
    throw new Error(`Server returned non-JSON (${response.status}): ${detail}`)
  }
}

const defaultCode = ''

const DEFAULT_ALGORITHM =
  'Read the inputs in order, apply the logic the statement describes, and print exactly like the samples.'
const DEFAULT_FUNCTIONS =
  'Use #include <stdio.h> with scanf and printf. Add for/while loops or if/else whenever the problem needs them.'

const ACCENT_PAD = {
  sky: 'border-l-sky-400/90 bg-gradient-to-r from-sky-500/[0.06] to-transparent',
  green: 'border-l-emerald-400/90 bg-gradient-to-r from-emerald-500/[0.06] to-transparent',
  amber: 'border-l-amber-400/90 bg-gradient-to-r from-amber-500/[0.06] to-transparent',
  violet: 'border-l-violet-400/90 bg-gradient-to-r from-violet-500/[0.06] to-transparent',
  cyan: 'border-l-cyan-400/90 bg-gradient-to-r from-cyan-500/[0.06] to-transparent',
}

function formatCountdown(totalSeconds) {
  const sec = Math.max(0, Math.floor(Number(totalSeconds) || 0))
  const m = Math.floor(sec / 60)
  const s = sec % 60
  return `${m}:${String(s).padStart(2, '0')}`
}

function readPersistedStudentPayload() {
  try {
    const raw = localStorage.getItem('ccodelab_user')
    return raw ? JSON.parse(raw) : null
  } catch {
    return null
  }
}

/** Clears timer storage so reopening the question gets a full timer (reattempt). */
function clearQuestionTimerStorage(mergedUser, questionId) {
  if (questionId == null) return
  if (mergedUser?.role === 'staff') return
  const studentId = typeof mergedUser?.id === 'number' ? mergedUser.id : null
  const persist = studentId != null ? window.localStorage : window.sessionStorage
  const keyPrefix = studentId != null ? `${studentId}_` : 'anon_'
  const id = String(questionId)
  persist.removeItem(`ccodelab_q_started_${keyPrefix}${id}`)
  persist.removeItem(`ccodelab_q_remaining_${keyPrefix}${id}`)
}

function InfoBlock({ accent, title, body, fallback = '', defaultText = '' }) {
  const raw = (body && String(body).trim()) || (fallback && String(fallback).trim()) || defaultText
  const text = typeof raw === 'string' ? raw.trim() : ''
  if (!text) {
    return null
  }
  return (
    <div
      className={`rounded-xl border border-brand-line/50 px-4 py-3.5 text-[14px] leading-relaxed text-brand-muted ring-1 ring-inset ring-white/[0.03] ${ACCENT_PAD[accent] || ''} border-l-[3px]`}
    >
      <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-brand-text/80">{title}</p>
      <p className="mt-2 whitespace-pre-line text-[14px] leading-relaxed text-brand-muted">{text}</p>
    </div>
  )
}

function QuestionPage() {
  const [searchParams] = useSearchParams()
  const [code, setCode] = useState(defaultCode)
  const [customInput, setCustomInput] = useState('')
  const [outputConsole, setOutputConsole] = useState('Ready to run...')
  const [isProcessing, setIsProcessing] = useState(false)
  const [currentUser, setCurrentUser] = useState(null)
  const [questionList, setQuestionList] = useState([])
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0)
  const [difficulty, setDifficulty] = useState('easy')
  const [question, setQuestion] = useState({
    id: null,
    title: 'Square a Number',
    difficulty: 'easy',
    description: 'Read an integer n and print its square.',
    input_format: 'First line contains one integer n.',
    output_format: 'Print n*n on a single line.',
    constraints: 'The user enters one integers n (think small enough to square safely).',
    algorithm_hint:
      'Read n, multiply n*n once, print the product so it matches the sample lines.',
    functions_hint:
      'Use stdio: scanf with %d and printf with %d. Wrap in main and return 0.',
    examples: [
      { input: '5', output: '25' },
      { input: '9', output: '81' },
    ],
    test_cases: [
      { input: '2', output: '4' },
      { input: '7', output: '49' },
      { input: '10', output: '100' },
    ],
    time_limit_minutes: 15,
  })
  /** `null` = computing, `"staff"` = no graded limit, number = seconds remaining */
  const [timerRemain, setTimerRemain] = useState(null)
  const [testCaseResults, setTestCaseResults] = useState([])
  const testCaseSectionRef = useRef(null)
  const editorRef = useRef(null)
  const monacoRef = useRef(null)
  const compileDecorIdsRef = useRef([])
  const runProcessRef = useRef(
    /** @type {(mode: string, opts?: { forceAfterTimeLimit?: boolean }) => Promise<void>} */ (
      async () => {}
    ),
  )
  /** Prevents firing auto-submit repeatedly while timer stays at 0 on the same question */
  const expiryAutoSubmitFiredRef = useRef(false)
  const prevTimerRemainForExpiryRef = useRef(null)
  const pendingExpirySubmitRef = useRef(false)
  const isProcessingRef = useRef(false)
  const initCompleteRef = useRef(false)
  /** Set when last graded submit did not pass all tests; cleared on full pass. */
  const [showTryAgainHint, setShowTryAgainHint] = useState(false)
  const [nextLoading, setNextLoading] = useState(false)

  useEffect(() => {
    compileDecorIdsRef.current = clearCompileFeedback(
      editorRef.current,
      monacoRef.current,
      compileDecorIdsRef.current,
    )
  }, [question?.id])

  useEffect(() => {
    expiryAutoSubmitFiredRef.current = false
    prevTimerRemainForExpiryRef.current = null
    pendingExpirySubmitRef.current = false
  }, [question?.id])

  isProcessingRef.current = isProcessing

  const fireAutoSubmitOnTimeUp = () => {
    if (expiryAutoSubmitFiredRef.current) return
    const merged = currentUser || readPersistedStudentPayload()
    if (merged?.role === 'staff') return
    if (question?.id == null) return
    expiryAutoSubmitFiredRef.current = true
    pendingExpirySubmitRef.current = false
    setOutputConsole('Time limit reached — submitting your code and moving to the next syllabus question…')
    void runProcessRef.current('submit', { forceAfterTimeLimit: true })
  }

  useEffect(() => {
    if (timerRemain === 'staff' || timerRemain === null) return
    if (question?.id == null) return
    if ((currentUser || readPersistedStudentPayload())?.role === 'staff') return

    const prev = prevTimerRemainForExpiryRef.current
    prevTimerRemainForExpiryRef.current = timerRemain

    const atZero = typeof timerRemain === 'number' && timerRemain <= 0
    if (!atZero) return

    const crossedFromPositive = typeof prev === 'number' && prev > 0

    if (!crossedFromPositive) return

    if (isProcessingRef.current) {
      pendingExpirySubmitRef.current = true
      return
    }

    fireAutoSubmitOnTimeUp()
  }, [timerRemain, question?.id, currentUser])

  useEffect(() => {
    if (isProcessing) return
    if (!pendingExpirySubmitRef.current) return
    if (!(typeof timerRemain === 'number' && timerRemain <= 0)) return
    if (question?.id == null) return
    if ((currentUser || readPersistedStudentPayload())?.role === 'staff') return
    fireAutoSubmitOnTimeUp()
  }, [isProcessing, timerRemain, question?.id, currentUser])

  useEffect(() => {
    const persisted = readPersistedStudentPayload()
    const mergedUser = currentUser || persisted || null

    if (mergedUser?.role === 'staff') {
      setTimerRemain('staff')
      return undefined
    }

    const studentId =
      typeof mergedUser?.id === 'number' && mergedUser.role !== 'staff' ? mergedUser.id : null

    const questionKey = question?.id != null ? String(question.id) : 'sandbox'
    const rawMin = Number(question?.time_limit_minutes)
    const limitMinutes = Number.isFinite(rawMin) ? Math.min(Math.max(rawMin, 1), 24 * 60) : 15
    const limitSec = Math.floor(limitMinutes * 60)

    const persist = studentId != null ? window.localStorage : window.sessionStorage
    const keyPrefix = studentId != null ? `${studentId}_` : 'anon_'
    const remainingKey = `ccodelab_q_remaining_${keyPrefix}${questionKey}`
    const legacyStartedKey = `ccodelab_q_started_${keyPrefix}${questionKey}`

    let initialRemain = Number.parseInt(String(persist.getItem(remainingKey) ?? ''), 10)
    if (!Number.isFinite(initialRemain) || initialRemain < 0 || initialRemain > limitSec) {
      initialRemain = limitSec
    }
    persist.setItem(remainingKey, String(initialRemain))
    persist.removeItem(legacyStartedKey)

    const latestRemainRef = { current: initialRemain }
    setTimerRemain(initialRemain)

    let cancelledKick = false
    if (initialRemain <= 0 && mergedUser?.role !== 'staff' && question?.id != null) {
      queueMicrotask(() => {
        if (cancelledKick) return
        if ((currentUser || readPersistedStudentPayload())?.role === 'staff') return
        fireAutoSubmitOnTimeUp()
      })
    }

    const intervalId = window.setInterval(() => {
      setTimerRemain((prev) => {
        if (typeof prev !== 'number') return prev
        const next = Math.max(0, prev - 1)
        latestRemainRef.current = next
        persist.setItem(remainingKey, String(next))
        return next
      })
    }, 1000)

    return () => {
      cancelledKick = true
      window.clearInterval(intervalId)
      persist.setItem(remainingKey, String(Math.max(0, latestRemainRef.current)))
    }
  }, [question?.id, question?.time_limit_minutes, currentUser])

  const timerExpiredForGrade =
    timerRemain !== 'staff' && typeof timerRemain === 'number' && timerRemain <= 0

  const scrollToTestCases = () => {
    if (testCaseSectionRef.current) {
      testCaseSectionRef.current.scrollIntoView({ behavior: 'smooth', block: 'start' })
    }
  }

  useEffect(() => {
    let cancelled = false

    const bootstrap = async () => {
      const userRaw = localStorage.getItem('ccodelab_user')
      const user = userRaw ? JSON.parse(userRaw) : null
      if (!cancelled) {
        setCurrentUser(user)
      }

      try {
        const retryOnly = searchParams.get('retry')
        const qParam = searchParams.get('question') || retryOnly
        if (qParam) {
          const qid = Number(qParam)
          if (Number.isFinite(qid)) {
            const direct = await fetch(apiUrl(`/questions/${qid}`))
            if (!cancelled && direct.ok) {
              const q = await direct.json()
              if (retryOnly) {
                clearQuestionTimerStorage(user, q.id)
              }
              setQuestion(q)
              setDifficulty(q.difficulty || 'easy')
              const listResponse = await fetch(
                apiUrl(`/questions/?difficulty=${encodeURIComponent(q.difficulty || 'easy')}`),
              )
              if (!cancelled && listResponse.ok) {
                const listData = await listResponse.json()
                if (Array.isArray(listData) && listData.length > 0) {
                  setQuestionList(listData)
                  const idx = listData.findIndex((item) => item.id === q.id)
                  setCurrentQuestionIndex(idx >= 0 ? idx : 0)
                } else {
                  setQuestionList([q])
                  setCurrentQuestionIndex(0)
                }
              }
              if (user?.id) {
                const draftKey = `ccodelab_draft_${user.id}_${q.id}`
                setCode(localStorage.getItem(draftKey) ?? '')
              } else {
                setCode('')
              }
              setOutputConsole(
                retryOnly
                  ? 'Try again on this question — when all tests pass, your progress updates.'
                  : 'Opened the selected question.',
              )
              setShowTryAgainHint(Boolean(retryOnly))
              return
            }
          }
        }

        if (user?.id && user.role !== 'staff') {
          const resumeResponse = await fetch(apiUrl(`/questions/resume/next?student_id=${user.id}`))
          if (!cancelled && resumeResponse.ok) {
            const resumePayload = await resumeResponse.json()
            if (resumePayload.next_question) {
              const q = resumePayload.next_question
              setQuestion(q)
              setDifficulty(q.difficulty || 'easy')
              const listResponse = await fetch(apiUrl(`/questions/?difficulty=${encodeURIComponent(q.difficulty)}`))
              if (!cancelled && listResponse.ok) {
                const listData = await listResponse.json()
                if (Array.isArray(listData) && listData.length > 0) {
                  setQuestionList(listData)
                  const idx = listData.findIndex((item) => item.id === q.id)
                  setCurrentQuestionIndex(idx >= 0 ? idx : 0)
                } else {
                  setQuestionList([q])
                  setCurrentQuestionIndex(0)
                }
              }
              const draftKey = `ccodelab_draft_${user.id}_${q.id}`
              const savedCode = localStorage.getItem(draftKey)
              if (!cancelled) {
                setCode(savedCode ?? '')
                setOutputConsole('Continuing where you left off.')
              }
              return
            }
            if (!cancelled && resumePayload.all_complete) {
              setOutputConsole(resumePayload.message || 'You have completed all questions.')
            }
          }
        }

        const response = await fetch(apiUrl(`/questions/?difficulty=${difficulty}`))
        if (!cancelled && response.ok) {
          const data = await response.json()
          if (Array.isArray(data) && data.length > 0) {
            setQuestionList(data)
            setCurrentQuestionIndex(0)
            setQuestion(data[0])
          } else {
            setQuestionList([])
            setCurrentQuestionIndex(0)
            setOutputConsole(`No ${difficulty} questions available right now.`)
          }
        }
      } catch {
        /* keep fallback UI if backend is unavailable */
      } finally {
        if (!cancelled) {
          initCompleteRef.current = true
        }
      }
    }

    bootstrap()
    return () => {
      cancelled = true
    }
  }, [searchParams])

  useEffect(() => {
    if (!initCompleteRef.current) {
      return
    }

    let cancelled = false

    const loadByDifficulty = async () => {
      try {
        const userRaw = localStorage.getItem('ccodelab_user')
        const user = userRaw ? JSON.parse(userRaw) : null

        const response = await fetch(apiUrl(`/questions/?difficulty=${difficulty}`))
        if (!response.ok || cancelled) {
          return
        }
        const data = await response.json()
        if (!Array.isArray(data) || data.length === 0) {
          setQuestionList([])
          setOutputConsole(`No ${difficulty} questions available right now.`)
          return
        }

        let pick = data[0]

        if (user?.id && user.role !== 'staff') {
          const attemptsRes = await fetch(apiUrl(`/attempts/?student_id=${user.id}`))
          if (!cancelled && attemptsRes.ok) {
            const attempts = await attemptsRes.json()
            const solvedIds = new Set(
              attempts.filter((row) => row.is_correct).map((row) => row.question_id),
            )
            const nextInTier = data.find((q) => !solvedIds.has(q.id))
            if (nextInTier) {
              pick = nextInTier
            }
          }
        }

        setQuestionList(data)
        const pickIndex = data.findIndex((q) => q.id === pick.id)
        setCurrentQuestionIndex(pickIndex >= 0 ? pickIndex : 0)
        setQuestion(pick)

        if (user?.id) {
          const draftKey = `ccodelab_draft_${user.id}_${pick.id}`
          setCode(localStorage.getItem(draftKey) ?? '')
        }
      } catch {
        /* ignore */
      }
    }

    loadByDifficulty()
    return () => {
      cancelled = true
    }
  }, [difficulty])

  useEffect(() => {
    if (!currentUser?.id || !question?.id) {
      return
    }
    const handle = window.setTimeout(() => {
      localStorage.setItem(`ccodelab_draft_${currentUser.id}_${question.id}`, code)
    }, 400)
    return () => window.clearTimeout(handle)
  }, [code, question.id, currentUser?.id])

  useEffect(() => {
    const cases = (question.test_cases || []).map((testCase, index) => ({
      name: `Case ${index + 1}`,
      input: testCase.input || '',
      expected: testCase.output || '',
      got: '-',
      status: 'Pending',
    }))
    setTestCaseResults(cases)
  }, [question])

  /**
   * Next question in syllabus order (not “next unsolved”) — used after timed auto-submit.
   * @returns {Promise<{ ok: boolean, noNext: boolean, retryable: boolean }>}
   */
  const advanceToSyllabusNextQuestion = async (fromQuestionId) => {
    try {
      const user = currentUser || readPersistedStudentPayload()
      const sid =
        typeof user?.id === 'number' && user?.role !== 'staff' ? user.id : null
      const nextPath =
        sid != null
          ? `/questions/${fromQuestionId}/syllabus-next?student_id=${sid}`
          : `/questions/${fromQuestionId}/syllabus-next`
      const res = await fetch(apiUrl(nextPath))
      const body = await parseResponseJson(res)
      if (!res.ok || !body?.id) {
        const noNext = res.status === 404
        return { ok: false, noNext, retryable: !noNext }
      }

      compileDecorIdsRef.current = clearCompileFeedback(
        editorRef.current,
        monacoRef.current,
        compileDecorIdsRef.current,
      )

      setQuestion(body)
      if (body.difficulty) {
        setDifficulty(body.difficulty)
      }

      const listResponse = await fetch(
        apiUrl(`/questions/?difficulty=${encodeURIComponent(body.difficulty || 'easy')}`),
      )
      if (listResponse.ok) {
        const listData = await listResponse.json()
        if (Array.isArray(listData) && listData.length > 0) {
          setQuestionList(listData)
          const idx = listData.findIndex((item) => item.id === body.id)
          setCurrentQuestionIndex(idx >= 0 ? idx : 0)
        } else {
          setQuestionList([body])
          setCurrentQuestionIndex(0)
        }
      } else {
        setQuestionList([body])
        setCurrentQuestionIndex(0)
      }

      if (user?.id) {
        const nextDraftKey = `ccodelab_draft_${user.id}_${body.id}`
        setCode(localStorage.getItem(nextDraftKey) ?? '')
      } else {
        setCode('')
      }
      setCustomInput('')
      return { ok: true, noNext: false, retryable: false }
    } catch {
      return { ok: false, noNext: false, retryable: true }
    }
  }

  const runProcess = async (mode, options = {}) => {
    scrollToTestCases()

    if (!code.trim()) {
      compileDecorIdsRef.current = clearCompileFeedback(
        editorRef.current,
        monacoRef.current,
        compileDecorIdsRef.current,
      )
      if (options.forceAfterTimeLimit && question?.id) {
        setTestCaseResults((prev) =>
          prev.map((item) => ({
            ...item,
            status: 'Pending',
            got: '-',
          })),
        )

        const mergedUser = currentUser || readPersistedStudentPayload()
        const totalCases = Array.isArray(question.test_cases) ? question.test_cases.length : 0
        if (
          mergedUser?.id &&
          mergedUser.role !== 'staff'
        ) {
          const payload = {
            student_id: mergedUser.id,
            question_id: question.id,
            submitted_code: '/* Time expired — no code was submitted before the deadline */',
            score: 0,
            passed_cases: 0,
            failed_cases: totalCases,
            is_correct: false,
            feedback: `${TIME_EXPIRED_NO_SUBMISSION_FEEDBACK_PREFIX} Reattempt is allowed; the timer resets when you open this question again.`,
          }
          try {
            const saveResponse = await fetch(apiUrl('/attempts/'), {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify(payload),
            })
            if (saveResponse.ok) {
              const attemptRecord = await saveResponse.json()
              localStorage.setItem('ccodelab_latest_attempt', JSON.stringify(attemptRecord))
            }
          } catch {
            /* profile sync best-effort; timer still clears for reattempt */
          }
        }
        clearQuestionTimerStorage(mergedUser, question.id)

        const nav = await advanceToSyllabusNextQuestion(question.id)
        if (!nav.ok) {
          expiryAutoSubmitFiredRef.current = false
          setOutputConsole(
            nav.noNext
              ? 'Time limit reached — nothing to submit. Recorded as failed on your profile. You were on the last question in this syllabus.'
              : 'Time limit reached — could not open the next question. Try again shortly.',
          )
        } else {
          setOutputConsole(
            'Time limit reached with an empty editor — recorded as a failed attempt on your profile (reattempt available). Moved you to the next syllabus question.',
          )
        }
        return
      }
      setOutputConsole('Editor is blank. Please write your code first.')
      setTestCaseResults((prev) =>
        prev.map((item) => ({
          ...item,
          status: 'Pending',
        })),
      )
      return
    }

    if (testCaseResults.length === 0) {
      setOutputConsole('No test cases available for this question.')
      return
    }

    if (mode === 'submit' && timerExpiredForGrade && !options.forceAfterTimeLimit) {
      setOutputConsole('Graded submit is unavailable — time for this question has ended. Use Run to keep practicing.')
      return
    }

    setIsProcessing(true)
    compileDecorIdsRef.current = clearCompileFeedback(
      editorRef.current,
      monacoRef.current,
      compileDecorIdsRef.current,
    )
    setOutputConsole(mode === 'run' ? 'Compiling and running...' : 'Compiling and submitting...')
    setTestCaseResults((prev) =>
      prev.map((item) => ({
        ...item,
        status: 'Running',
        got: '-',
      })),
    )

    try {
      const response = await fetch(apiUrl('/judge/c'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          code,
          question_id: question.id,
          custom_input: customInput,
          mode,
          test_cases: question.test_cases || [],
        }),
      })

      const data = await parseResponseJson(response)
      if (!response.ok) {
        throw new Error(data.detail || 'Judge request failed')
      }

      if (!data.compile_ok) {
        const compileText = data.compile_output || 'Unknown compile error.'
        const { affectedLines, first, decorationIds } = applyCompilerMarkers(
          editorRef.current,
          monacoRef.current,
          compileText,
          compileDecorIdsRef.current,
        )
        compileDecorIdsRef.current = decorationIds
        let header =
          affectedLines.length > 0 || first
            ? `Compilation failed (red underlines in the editor`
            : `Compilation failed`
        if (first) {
          header += ` — first error at line ${first.lineNumber}, column ${first.column}`
        } else if (affectedLines.length > 0) {
          header += ` — lines: ${affectedLines.join(', ')}`
        }
        header += affectedLines.length > 0 || first ? `).\n\n` : `:\n\n`
        setOutputConsole(`${header}${compileText}`)
        setTestCaseResults((prev) =>
          prev.map((item) => ({
            ...item,
            status: 'Compile Error',
            got: '-',
          })),
        )
        window.requestAnimationFrame(() => {
          const ed = editorRef.current
          if (ed && first) {
            ed.revealLineInCenter(first.lineNumber)
            ed.setPosition({ lineNumber: first.lineNumber, column: first.column })
            ed.focus()
          }
        })
        if (mode === 'submit' && options.forceAfterTimeLimit && question?.id) {
          const nav = await advanceToSyllabusNextQuestion(question.id)
          if (nav.ok) {
            setOutputConsole((prev) => `${prev}\n\nTime limit — opening the next syllabus question.`)
          } else if (nav.retryable) {
            expiryAutoSubmitFiredRef.current = false
            setOutputConsole((prev) =>
              `${prev}\n\nTime limit — could not advance to the next question. You can retry from the console message above.`,
            )
          } else if (nav.noNext) {
            setOutputConsole((prev) =>
              `${prev}\n\nTime limit — submission failed to compile; that was also the last syllabus question.`,
            )
          }
        }
        return
      }

      compileDecorIdsRef.current = clearCompileFeedback(
        editorRef.current,
        monacoRef.current,
        compileDecorIdsRef.current,
      )

      /** Warnings/format issues still compile but stderr often has gcc file:line:col lines */
      const stderrText = (data.compile_output || '').trim()
      const { affectedLines: warnLines, first: warnFirst, decorationIds: warnDecorIds } =
        applyCompilerMarkers(
          editorRef.current,
          monacoRef.current,
          stderrText,
          compileDecorIdsRef.current,
        )
      compileDecorIdsRef.current = warnDecorIds

      const compilerEditorHint =
        warnLines.length > 0 || warnFirst
          ? `Compiler flagged line ${warnFirst ? `${warnFirst.lineNumber} (column ${warnFirst.column})` : `${warnLines.join(', ')}`} — open the 💡 in the gutter or hover underlines.\n`
          : ''

      if (warnFirst || warnLines.length > 0) {
        window.requestAnimationFrame(() => {
          const ed = editorRef.current
          const target = warnFirst
          if (ed && target) {
            ed.revealLineInCenter(target.lineNumber)
            ed.setPosition({ lineNumber: target.lineNumber, column: target.column })
            ed.focus()
          }
        })
      }

      const nextResults = data.results.map((item) => ({
        name: `Case ${item.index}`,
        input: item.input || '',
        expected: item.expected || '',
        got: item.got || '',
        status: item.status || 'Completed',
      }))
      setTestCaseResults(nextResults)
      window.requestAnimationFrame(scrollToTestCases)

      const passedCount = data.results.filter((item) => item.passed).length
      const totalCount = data.results.length
      const allTestsPassed = totalCount > 0 && passedCount === totalCount
      const customOutputText = data.custom_output ? `\nCustom Output:\n${data.custom_output}` : ''
      if (mode === 'submit') {
        let attemptData = null
        if (currentUser?.id && question?.id) {
          const payload = {
            student_id: currentUser.id,
            question_id: question.id,
            submitted_code: code,
            score: totalCount ? Math.round((passedCount / totalCount) * 100) : 0,
            passed_cases: passedCount,
            failed_cases: totalCount - passedCount,
            is_correct: allTestsPassed,
            feedback: `Passed ${passedCount}/${totalCount} test cases.`,
          }
          const saveResponse = await fetch(apiUrl('/attempts/'), {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
          })
          if (saveResponse.ok) {
            attemptData = await saveResponse.json()
            localStorage.setItem('ccodelab_latest_attempt', JSON.stringify(attemptData))
          }
        }

        if (options.forceAfterTimeLimit) {
          const nav = await advanceToSyllabusNextQuestion(question.id)
          if (nav.ok) {
            setShowTryAgainHint(false)
            setOutputConsole(
              `${compilerEditorHint}Time limit reached — your last attempt was submitted automatically.\nPassed ${passedCount}/${totalCount} test cases.${customOutputText}\n\nOpening the next syllabus question.`,
            )
          } else if (nav.noNext) {
            setShowTryAgainHint(false)
            setOutputConsole(
              `${compilerEditorHint}Time limit reached — your last attempt was submitted.\nPassed ${passedCount}/${totalCount} test cases.${customOutputText}\n\nThat was the final question in this syllabus order.`,
            )
          } else if (nav.retryable) {
            expiryAutoSubmitFiredRef.current = false
            setShowTryAgainHint(false)
            setOutputConsole(
              `${compilerEditorHint}Time limit reached — your last attempt was submitted.\nPassed ${passedCount}/${totalCount} test cases.${customOutputText}\n\nCould not load the next question; try again.`,
            )
          }
        } else if (!allTestsPassed) {
          setShowTryAgainHint(true)
          setOutputConsole(
            `${compilerEditorHint}Compilation successful.\nPassed ${passedCount}/${totalCount} test cases.${customOutputText}\n\nNot all tests passed — you stay on this question. Improve your solution and press Submit again; when you pass, your result and syllabus progress update.`,
          )
        } else if (attemptData?.should_move_next && attemptData?.next_question_id) {
          setShowTryAgainHint(false)
          const nextQuestionResponse = await fetch(apiUrl(`/questions/${attemptData.next_question_id}`))
          if (nextQuestionResponse.ok) {
            const nextQuestion = await nextQuestionResponse.json()
            setQuestion(nextQuestion)
            if (nextQuestion.difficulty) {
              setDifficulty(nextQuestion.difficulty)
            }
            if (currentUser?.id) {
              const nextDraftKey = `ccodelab_draft_${currentUser.id}_${nextQuestion.id}`
              setCode(localStorage.getItem(nextDraftKey) ?? '')
            } else {
              setCode('')
            }
            setCustomInput('')
            setOutputConsole(
              `${compilerEditorHint}Compilation successful.\nPassed ${passedCount}/${totalCount} test cases.${customOutputText}\n\nLoading next question...`,
            )
          } else {
            setOutputConsole(
              `${compilerEditorHint}Compilation successful.\nPassed ${passedCount}/${totalCount} test cases.${customOutputText}\n\nNext question could not be loaded.`,
            )
          }
        } else {
          setShowTryAgainHint(false)
          const hasNextQuestion = currentQuestionIndex < questionList.length - 1
          if (hasNextQuestion) {
            const nextIndex = currentQuestionIndex + 1
            setCurrentQuestionIndex(nextIndex)
            setQuestion(questionList[nextIndex])
            setCode('')
            setCustomInput('')
            setOutputConsole(
              `${compilerEditorHint}Compilation successful.\nPassed ${passedCount}/${totalCount} test cases.${customOutputText}\n\nLoading next question...`,
            )
          } else {
            setOutputConsole(
              `${compilerEditorHint}Compilation successful.\nPassed ${passedCount}/${totalCount} test cases.${customOutputText}\n\nYou completed all available questions.`,
            )
          }
        }
      } else {
        setOutputConsole(
          `${compilerEditorHint}Compilation successful.\nPassed ${passedCount}/${totalCount} test cases.${customOutputText}`,
        )
      }
    } catch (error) {
      compileDecorIdsRef.current = clearCompileFeedback(
        editorRef.current,
        monacoRef.current,
        compileDecorIdsRef.current,
      )
      setOutputConsole(error.message || 'Failed to connect to code judge server.')
      setTestCaseResults((prev) =>
        prev.map((item) => ({
          ...item,
          status: 'Error',
          got: '-',
        })),
      )
    } finally {
      setIsProcessing(false)
    }
  }

  runProcessRef.current = runProcess

  const handleNextSyllabusClick = async () => {
    if (!question?.id) return
    setNextLoading(true)
    try {
      const nav = await advanceToSyllabusNextQuestion(question.id)
      if (nav.ok) {
        setOutputConsole('Moved to the next syllabus question.')
        setShowTryAgainHint(false)
      } else if (nav.noNext) {
        setOutputConsole('You are on the last question in this syllabus order (or no unsolved questions left).')
      } else {
        setOutputConsole('Could not open the next question. Try again shortly.')
      }
    } finally {
      setNextLoading(false)
    }
  }

  const panelClass =
    'min-w-0 rounded-2xl bg-brand-card/35 p-6 shadow-[0_12px_40px_-18px_rgba(0,0,0,0.55)] ring-1 ring-brand-line/60'

  return (
    <main className="min-h-screen bg-brand-bg">
      <AppNavbar />
      <section className="mx-auto grid max-w-[1680px] gap-5 px-4 py-6 md:gap-6 md:px-6 lg:auto-rows-fr lg:items-start lg:[grid-template-columns:minmax(300px,0.94fr)_minmax(390px,1.38fr)_minmax(278px,0.92fr)]">
        <article
          className={`scrollbar-workspace ${panelClass} lg:max-h-[calc(100dvh-5.25rem)] lg:overflow-y-auto lg:pr-1`}
        >
          <div className="mb-5 flex flex-wrap items-center justify-between gap-3">
            <span className="rounded-full bg-brand-neonBlue/15 px-3.5 py-1.5 text-xs font-medium capitalize tracking-wide text-brand-neonBlue ring-1 ring-brand-neonBlue/25">
              {difficulty}
            </span>
            <select
              value={difficulty}
              onChange={(event) => setDifficulty(event.target.value)}
              className="rounded-lg border border-brand-line/70 bg-brand-surface/90 px-3 py-2 text-sm capitalize text-brand-text shadow-inner outline-none transition focus:border-brand-neonBlue focus:ring-1 focus:ring-brand-neonBlue/40"
            >
              <option value="easy">Easy</option>
              <option value="medium">Medium</option>
              <option value="tough">Tough</option>
            </select>
          </div>
          <p className="text-[11px] font-semibold uppercase tracking-[0.12em] text-brand-muted">Problem</p>
          <h1 className="mt-1.5 text-balance text-xl font-semibold leading-snug tracking-tight text-brand-text md:text-[1.35rem]">
            {question.title}
          </h1>
          <p className="mt-4 leading-relaxed text-[15px] text-brand-muted">{question.description}</p>

          <div className="mt-7 space-y-3">
            <InfoBlock
              accent="sky"
              title="Input format"
              body={question.input_format}
              fallback="Provided by instructor."
            />
            <InfoBlock
              accent="green"
              title="Output format"
              body={question.output_format}
              fallback="Provided by instructor."
            />
            <InfoBlock
              accent="amber"
              title="About the input"
              body={question.constraints}
              fallback="Use the samples below together with Input format."
            />
            <InfoBlock
              accent="violet"
              title="Suggested approach"
              body={question.algorithm_hint}
              defaultText={DEFAULT_ALGORITHM}
            />
            <InfoBlock accent="cyan" title="Useful C ideas" body={question.functions_hint} defaultText={DEFAULT_FUNCTIONS} />

            {(question.examples || []).length > 0 && (
              <div className="rounded-xl bg-black/25 p-4 ring-1 ring-white/5">
                <p className="text-xs font-semibold uppercase tracking-wide text-brand-muted">Examples</p>
                <div className="mt-3 space-y-3">
                  {(question.examples || []).map((example, index) => (
                    <div
                      key={`${example.input}-${index}`}
                      className="rounded-lg bg-brand-bg/55 px-3.5 py-3 ring-1 ring-brand-line/40"
                    >
                      <p className="text-[11px] font-medium uppercase tracking-wide text-brand-muted/90">
                        Sample {index + 1}
                      </p>
                      <p className="mt-2 font-mono text-[12px] leading-relaxed text-slate-300">
                        In:{' '}
                        <span className="text-brand-neonBlue/90">{example.input || '-'}</span>
                      </p>
                      <p className="mt-1 font-mono text-[12px] leading-relaxed text-slate-300">
                        Out:{' '}
                        <span className="text-brand-neonGreen/90">{example.output || '-'}</span>
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </article>

        <article
          className={`scrollbar-workspace ${panelClass} space-y-5 lg:sticky lg:top-[4.75rem] lg:max-h-[calc(100dvh-5.25rem)] lg:overflow-y-auto lg:pr-1`}
        >
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-[11px] font-semibold uppercase tracking-[0.12em] text-brand-muted">Workspace</p>
              <h2 className="mt-0.5 text-lg font-semibold text-brand-text">Code editor</h2>
            </div>
            <div className="flex flex-wrap items-center justify-end gap-2">
              {timerRemain === 'staff' ? (
                <span
                  title="Staff mode: submits are not time-limited"
                  className="shrink-0 rounded-full bg-slate-500/15 px-3 py-1.5 text-xs font-medium tracking-wide text-slate-300 ring-1 ring-slate-500/30"
                >
                  No graded time limit
                </span>
              ) : timerRemain !== null ? (
                <span
                  title={`${Number(question.time_limit_minutes) || 15} minutes allocated for this question`}
                  className={`shrink-0 rounded-full px-3 py-1.5 font-mono text-[12px] font-semibold tabular-nums ring-1 transition ${
                    timerExpiredForGrade
                      ? 'bg-rose-500/15 text-rose-200 ring-rose-400/35'
                      : typeof timerRemain === 'number' && timerRemain <= 120
                        ? 'bg-amber-500/12 text-amber-200 ring-amber-400/35'
                        : 'bg-brand-neonBlue/15 text-brand-neonBlue ring-brand-neonBlue/25'
                  }`}
                  aria-live="polite"
                >
                  Time left&nbsp;
                  <span className="text-[13px]">{formatCountdown(timerRemain ?? 0)}</span>
                </span>
              ) : (
                <span className="shrink-0 rounded-full bg-brand-neonBlue/15 px-3 py-1.5 font-mono text-xs text-brand-muted ring-1 ring-brand-neonBlue/20">
                  Time left …
                </span>
              )}
              <span className="shrink-0 rounded-full bg-brand-neonBlue/15 px-3 py-1.5 text-xs font-medium text-brand-neonBlue ring-1 ring-brand-neonBlue/25">
                C (C11)
              </span>
            </div>
          </div>
          {timerExpiredForGrade && (
            <p className="rounded-lg border border-rose-500/35 bg-rose-500/[0.08] px-3 py-2 text-[13px] leading-snug text-rose-100/95">
              Time limit reached for graded submit — use <strong className="font-semibold text-rose-50">Run</strong> to keep trying.
            </p>
          )}
          {showTryAgainHint && !timerExpiredForGrade && (
            <p className="rounded-lg border border-amber-500/40 bg-amber-500/[0.08] px-3 py-2 text-[13px] leading-snug text-amber-100/95">
              <strong className="font-semibold text-amber-50">Try again:</strong> you are still on this question. Fix your code and press{' '}
              <strong className="font-semibold text-amber-50">Submit</strong> — when every test passes, your score and progress update automatically.
            </p>
          )}
          <div className="overflow-hidden rounded-xl ring-1 ring-black/40">
            <Editor
              height="420px"
              theme="vs-dark"
              defaultLanguage="c"
              value={code}
              onChange={(value) => setCode(value || '')}
              onMount={(editor, monaco) => {
                editorRef.current = editor
                monacoRef.current = monaco
              }}
              options={{
                minimap: { enabled: false },
                glyphMargin: true,
                overviewRulerLanes: 4,
                fontSize: 14,
                scrollBeyondLastLine: false,
              }}
            />
          </div>

          <div className="space-y-4">
            <label className="block">
              <span className="mb-2 block text-xs font-semibold uppercase tracking-wide text-brand-muted">
                Custom input
              </span>
              <textarea
                rows="4"
                placeholder="stdin for Run / optional try-out…"
                value={customInput}
                onChange={(event) => setCustomInput(event.target.value)}
                className="w-full rounded-xl border border-brand-line/70 bg-brand-bg/80 px-3.5 py-3 text-sm text-brand-text shadow-inner outline-none transition placeholder:text-brand-muted/50 focus:border-brand-neonBlue/80 focus:ring-1 focus:ring-brand-neonBlue/35"
              />
            </label>
            <div>
              <span className="mb-2 block text-xs font-semibold uppercase tracking-wide text-brand-muted">
                Console
              </span>
              <div className="scrollbar-workspace max-h-[140px] overflow-auto whitespace-pre-wrap rounded-xl bg-[#070b14] px-4 py-3 font-mono text-[12px] leading-relaxed text-emerald-400/95 ring-1 ring-white/10">
                {outputConsole}
              </div>
            </div>
          </div>

          <div className="flex flex-wrap gap-3 pt-1">
            <button
              type="button"
              disabled={isProcessing}
              onClick={() => runProcess('run')}
              className="rounded-xl border border-brand-neonBlue/60 bg-brand-neonBlue/10 px-5 py-2.5 text-sm font-medium text-brand-neonBlue transition hover:bg-brand-neonBlue/20 disabled:opacity-50"
            >
              Run
            </button>
            <button
              type="button"
              disabled={isProcessing || timerExpiredForGrade}
              title={
                timerExpiredForGrade
                  ? 'Time limit ended — graded submit ran automatically'
                  : 'Submit for graded test cases (also runs automatically when time runs out)'
              }
              onClick={() => runProcess('submit')}
              className="rounded-xl bg-brand-neonGreen px-5 py-2.5 text-sm font-semibold text-slate-900 shadow-[0_0_20px_-4px_rgba(34,197,94,0.55)] transition hover:brightness-110 disabled:opacity-50"
            >
              Submit
            </button>
            <button
              type="button"
              disabled={isProcessing || nextLoading || !question?.id}
              title="Go to the next question in syllabus order (skips questions you already solved when signed in)"
              onClick={() => void handleNextSyllabusClick()}
              className="rounded-xl bg-amber-500 px-5 py-2.5 text-sm font-semibold text-slate-900 shadow-[0_0_20px_-4px_rgba(245,158,11,0.55)] transition hover:brightness-110 disabled:opacity-50"
            >
              {nextLoading ? '…' : 'Next'}
            </button>
          </div>
        </article>

        <aside
          ref={testCaseSectionRef}
          className={`scrollbar-workspace ${panelClass} lg:max-h-[calc(100dvh-5.25rem)] lg:overflow-y-auto lg:pr-1`}
        >
          <p className="text-[11px] font-semibold uppercase tracking-[0.12em] text-brand-muted">Judge</p>
          <h3 className="mt-1 text-lg font-semibold text-brand-text">Test cases</h3>
          <div className="mt-5 flex flex-col gap-3.5">
            {testCaseResults.map((item) => (
              <div
                key={item.name}
                className="rounded-xl bg-black/22 px-4 py-4 ring-1 ring-white/[0.06]"
              >
                <p className="text-[13px] font-semibold text-brand-text">{item.name}</p>
                <dl className="mt-3 space-y-2 text-[11px] leading-snug">
                  <div>
                    <dt className="text-brand-muted">Input</dt>
                    <dd className="scrollbar-workspace mt-0.5 max-h-24 overflow-auto break-words font-mono text-slate-300">
                      {item.input || '—'}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-brand-muted">Expected</dt>
                    <dd className="scrollbar-workspace mt-0.5 max-h-24 overflow-auto break-words font-mono text-slate-300">
                      {item.expected || '—'}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-brand-neonBlue/80">Got</dt>
                    <dd className="scrollbar-workspace mt-0.5 max-h-24 overflow-auto break-words font-mono text-sky-200/90">
                      {item.got || '—'}
                    </dd>
                  </div>
                </dl>
                <p
                  className={`mt-3 inline-flex rounded-md px-2 py-1 text-[11px] font-semibold uppercase tracking-wide ${
                    item.status === 'Running'
                      ? 'bg-amber-500/15 text-amber-300'
                      : item.status === 'Passed' || item.status === 'Completed' || item.status === 'Submitted'
                        ? 'bg-brand-neonGreen/15 text-brand-neonGreen'
                        : item.status === 'Failed' ||
                            item.status === 'Compile Error' ||
                            item.status === 'Error'
                          ? 'bg-red-500/15 text-red-300'
                          : 'bg-slate-500/15 text-brand-muted'
                  }`}
                >
                  {item.status}
                </p>
              </div>
            ))}
          </div>
        </aside>
      </section>
    </main>
  )
}

export default QuestionPage
