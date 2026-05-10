/**
 * Parses typical gcc/clang stderr lines into Monaco marker shapes.
 * Examples:
 *   main.c:6:14: error: expected ';' before '}' token
 *   ./main.c:12: warning: unused variable [-Wunused-variable]
 */

function clamp(n, low, high) {
  return Math.min(Math.max(n, low), high)
}

function compactHint(message) {
  const t = String(message).replace(/\s+/g, ' ').trim()
  if (!t.length) return 'Compiler diagnostic'
  if (t.length <= 76) return t
  return `${t.slice(0, 73)}…`
}

function markdownTooltip(fullMessage) {
  const v = String(fullMessage || '').trim() || '(no detail)'
  return { value: v, isTrusted: false }
}

/**
 * Clear squiggles and gutter/inline decorations from a compile pass.
 * @returns {string[]} new decoration ids (always empty — use for ref assignment).
 */
export function clearCompileFeedback(editor, monacoNamespace, prevDecorationIds) {
  clearCompilerMarkers(editor, monacoNamespace)
  if (typeof editor?.deltaDecorations === 'function') {
    return editor.deltaDecorations(prevDecorationIds ?? [], [])
  }
  return []
}

/**
 * @param {string} raw
 * @returns {Array<{ lineNumber: number, column: number, severityRaw: string, message: string }>}
 */
export function parseGccDiagnostics(raw) {
  if (!raw || typeof raw !== 'string') {
    return []
  }
  const markers = []

  for (const line of raw.split(/\r?\n/)) {
    const trimmed = line.trimEnd()
    if (!trimmed) {
      continue
    }

    let m = trimmed.match(/:(\d+):(\d+):\s*((?:fatal\s+)?error|warning|note):\s*(.+)$/i)
    if (m) {
      markers.push({
        lineNumber: parseInt(m[1], 10),
        column: parseInt(m[2], 10),
        severityRaw: m[3].trim(),
        message: m[4].trim(),
      })
      continue
    }

    m = trimmed.match(/:(\d+):\s*((?:fatal\s+)?error|warning|note):\s*(.+)$/i)
    if (m) {
      markers.push({
        lineNumber: parseInt(m[1], 10),
        column: 1,
        severityRaw: m[2].trim(),
        message: m[3].trim(),
      })
    }
  }

  return markers
}

/** @typedef {import('monaco-editor')} MonacoNs */

/**
 * @param {{ getModel(): import('monaco-editor').editor.ITextModel | null }} editor
 * @param {unknown} monacoNamespace
 * @param {string} compileOutput
 * @returns {{ affectedLines: number[], first: { lineNumber: number, column: number } | null, decorationIds: string[] }}
 */
export function applyCompilerMarkers(editor, monacoNamespace, compileOutput, prevDecorationIds = []) {
  /** @type {string[]} */
  let decorationIds = []

  const monaco =
    typeof monacoNamespace === 'undefined' ||
    monacoNamespace === null ||
    typeof monacoNamespace?.editor?.setModelMarkers !== 'function'
      ? null
      : /** @type {MonacoNs} */ (monacoNamespace)

  const model = typeof editor?.getModel === 'function' ? editor.getModel() : null
  if (!monaco || !model) {
    if (typeof editor?.deltaDecorations === 'function') {
      decorationIds = editor.deltaDecorations(prevDecorationIds || [], [])
    }
    return { affectedLines: [], first: null, decorationIds }
  }

  monaco.editor.setModelMarkers(model, 'compiler', [])

  const parsed = parseGccDiagnostics(compileOutput)
  const lineCount = model.getLineCount()

  /** @type {import('monaco-editor').editor.IMarkerData[]} */
  const monacoMarkers = []

  /** @type {import('monaco-editor').editor.IModelDeltaDecoration[]} */
  const decorations = []

  const RangeCtor = /** @type {typeof import('monaco-editor').Range} */ (monacoNamespace.Range)

  const affectedLines = []
  /** @type {{ lineNumber: number, column: number } | null} */
  let firstErrorCaret = null
  /** First warning/note line for scrolling when there is no hard error */
  /** @type {{ lineNumber: number, column: number } | null} */
  let firstWarnCaret = null
  /** @type {{ lineNumber: number, column: number } | null} */
  let firstHintCaret = null

  for (const d of parsed) {
    let lineNum = clamp(d.lineNumber, 1, Math.max(lineCount, 1))
    const startCol = Math.max(1, d.column || 1)
    const maxColForLine = model.getLineLength(lineNum) + 1
    const safeStart = clamp(startCol, 1, maxColForLine)
    /** Highlight from error column through end of line (clear message for students). */
    const endCol = Math.max(safeStart + 1, maxColForLine)

    let sev = monaco.MarkerSeverity.Error
    const low = String(d.severityRaw || '').toLowerCase()
    if (low.includes('warning')) {
      sev = monaco.MarkerSeverity.Warning
    } else if (low.includes('note')) {
      sev = monaco.MarkerSeverity.Hint
    }

    if (sev === monaco.MarkerSeverity.Error && !firstErrorCaret) {
      firstErrorCaret = { lineNumber: lineNum, column: safeStart }
    } else if (sev === monaco.MarkerSeverity.Warning && !firstWarnCaret) {
      firstWarnCaret = { lineNumber: lineNum, column: safeStart }
    } else if (sev === monaco.MarkerSeverity.Hint && !firstHintCaret) {
      firstHintCaret = { lineNumber: lineNum, column: safeStart }
    }

    const tooltip = `**Compile issue** (line ${lineNum}:${safeStart})\n\n${d.message}`

    monacoMarkers.push({
      severity: sev,
      message: `Line ${lineNum}, column ${safeStart}: ${d.message}`,
      startLineNumber: lineNum,
      startColumn: safeStart,
      endLineNumber: lineNum,
      endColumn: endCol,
    })

    const isWarnOnly = low.includes('warning') && !low.includes('error')

    decorations.push({
      range: new RangeCtor(lineNum, safeStart, lineNum, endCol),
      options: {
        glyphMarginClassName: isWarnOnly ? 'ccl-compile-glyph-warn' : 'ccl-compile-glyph-error',
        glyphMarginHoverMessage: markdownTooltip(tooltip),
        hoverMessage: markdownTooltip(tooltip),
        after: {
          content: `  \u00B7 ${compactHint(d.message)}`,
          inlineClassName: isWarnOnly ? 'ccl-compile-hint-after-warn' : 'ccl-compile-hint-after',
        },
        zIndex: 3,
        minimap: { color: isWarnOnly ? '#f59e0b88' : '#ef444488', position: 1 },
        overviewRuler: {
          color: isWarnOnly ? '#f59e0baa' : '#ef4444aa',
          position:
            typeof monacoNamespace.editor?.OverviewRulerLane?.Right === 'number'
              ? monacoNamespace.editor.OverviewRulerLane.Right
              : 4,
        },
      },
    })

    affectedLines.push(lineNum)
  }

  monaco.editor.setModelMarkers(model, 'compiler', monacoMarkers)

  if (typeof editor.deltaDecorations === 'function') {
    decorationIds = editor.deltaDecorations(prevDecorationIds || [], decorations)
  }

  if (parsed.length === 0) {
    return { affectedLines: [], first: null, decorationIds }
  }

  const uniqueLines = affectedLines.length ? [...new Set(affectedLines)].sort((a, b) => a - b) : []
  const firstCaretReveal = firstErrorCaret || firstWarnCaret || firstHintCaret
  return { affectedLines: uniqueLines, first: firstCaretReveal, decorationIds }
}

/**
 * Remove compiler markers from editor model (e.g. after successful build).
 */
export function clearCompilerMarkers(editor, monacoNamespace) {
  const monaco =
    typeof monacoNamespace === 'undefined' ||
    monacoNamespace === null ||
    typeof monacoNamespace?.editor?.setModelMarkers !== 'function'
      ? null
      : /** @type {MonacoNs} */ (monacoNamespace)

  const model = typeof editor?.getModel === 'function' ? editor.getModel() : null
  if (!monaco || !model) {
    return
  }
  monaco.editor.setModelMarkers(model, 'compiler', [])
}
