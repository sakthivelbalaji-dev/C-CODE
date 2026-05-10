#!/usr/bin/env python3
"""
Generate `Executive-Summary-C-Code-Lab.html` at the repo root (`c-code-lab/`),
structured like `Executive Summary.pdf`: narrative, flowchart, timeline, mapping table,
sample questions, references.

Run from repo:  python backend/scripts/generate_executive_summary_html.py
Requires DATABASE_URL in env unless you rely on the script's dev fallback below.
"""

from __future__ import annotations

import html
import os
import sys
from pathlib import Path

# Allow import without live Postgres when generating docs only.
os.environ.setdefault("DATABASE_URL", "postgresql://generator:generator@localhost:5432/generator")

_REPO = Path(__file__).resolve().parents[2]
_OUT = _REPO / "Executive-Summary-C-Code-Lab.html"


def _marks_for(diff: str) -> int:
    d = diff.lower().strip()
    if d == "easy":
        return 2
    if d == "medium":
        return 4
    return 6


def main() -> None:
    backend = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(backend))

    from app.question_content import problem_display_title  # noqa: E402
    from app.topic_question_seeds import (  # noqa: E402
        QUESTIONS_PER_TOPIC,
        _TOPIC_SEEDS,
        _difficulty_for_problem,
    )

    rows_html: list[str] = []
    catalog_q = 1
    easy_n = medium_n = hard_n = 0

    for module, topic, keys in _TOPIC_SEEDS:
        assert len(keys) == QUESTIONS_PER_TOPIC
        for i, key in enumerate(keys):
            diff = _difficulty_for_problem(module, key)
            if diff == "easy":
                easy_n += 1
            elif diff == "medium":
                medium_n += 1
            else:
                hard_n += 1
            marks = _marks_for(diff)
            syllabus_cell = html.escape(f"{module} — {topic}")
            short_title = html.escape(problem_display_title(key.strip().lower()))
            rows_html.append(
                "<tr>"
                f"<td>{catalog_q}</td>"
                f"<td>{syllabus_cell}</td>"
                f"<td>{short_title}</td>"
                "<td>Programming task</td>"
                f"<td>{marks}</td>"
                f"<td>{html.escape(diff)}</td>"
                "</tr>"
            )
            catalog_q += 1

    total_q = catalog_q - 1
    pct_easy = round(100 * easy_n / total_q)
    pct_medium = round(100 * medium_n / total_q)
    pct_hard = round(100 * hard_n / total_q) if hard_n else 0
    if hard_n == 0:
        mix_sentence = (
            f"<strong>{pct_easy}% easy</strong> and <strong>{pct_medium}% medium</strong> "
            "(no items classified hard in current seed rules)."
        )
    else:
        mix_sentence = (
            f"<strong>{pct_easy}% easy</strong>, <strong>{pct_medium}% medium</strong>, "
            f"and <strong>{pct_hard}% hard</strong>."
        )

    table_body = "\n".join(rows_html)

    doc = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <title>Executive Summary — C Code Lab</title>
  <script type="module">
    import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
    mermaid.initialize({{ startOnLoad: true, theme: 'neutral', securityLevel: 'loose' }});
  </script>
  <style>
    :root {{ font-family: "Segoe UI", system-ui, sans-serif; color: #1a1a1a; line-height: 1.5; }}
    body {{ max-width: 900px; margin: 2rem auto; padding: 0 1.25rem 4rem; }}
    h1 {{ font-size: 1.75rem; border-bottom: 2px solid #2563eb; padding-bottom: 0.35rem; }}
    h2 {{ font-size: 1.2rem; margin-top: 2rem; color: #1e3a8a; }}
    p {{ margin: 0.75rem 0; }}
    ul {{ margin: 0.5rem 0 0.5rem 1.25rem; }}
    .box {{ background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 1rem 1.25rem; margin: 1rem 0; }}
    table.mapping {{ width: 100%; border-collapse: collapse; font-size: 0.82rem; margin: 1rem 0; }}
    table.mapping th, table.mapping td {{ border: 1px solid #cbd5e1; padding: 0.4rem 0.5rem; text-align: left; vertical-align: top; }}
    table.mapping thead {{ background: #1e40af; color: #fff; }}
    table.mapping tbody tr:nth-child(even) {{ background: #f1f5f9; }}
    .muted {{ color: #64748b; font-size: 0.92rem; }}
    .samples {{ white-space: pre-wrap; font-size: 0.88rem; background: #0f172a; color: #e2e8f0; padding: 1rem; border-radius: 8px; overflow-x: auto; }}
    @media print {{
      body {{ max-width: 100%; }}
      h2 {{ page-break-after: avoid; }}
      table.mapping {{ page-break-inside: avoid; }}
    }}
  </style>
</head>
<body>
  <h1>Executive Summary</h1>

  <p>
    We aligned <strong>C Code Lab</strong> with the syllabus in <strong>C Foundation (Updated)</strong>
    (Phases&nbsp;1–5: Foundation, Logic &amp; Flow Control, Functions, Data Collections, Problem Practice).
    The live question bank is generated from editable seeds in <code>backend/app/topic_question_seeds.py</code>:
    <strong>{total_q} catalog questions</strong> ({QUESTIONS_PER_TOPIC} per syllabus topic × 22 topics).
    Catalog numbers <strong>Q1…Q{total_q}</strong> follow global syllabus order; public/hidden judge cases distinguish
    sample vs graded tests in the LMS.
  </p>

  <p>
    <strong>Difficulty mix</strong> (automatic rules in seeds): approximately {mix_sentence}
    For exam-style marking we map: easy&nbsp;=&nbsp;2, medium&nbsp;=&nbsp;4, hard&nbsp;=&nbsp;6 marks per question
    (illustrative; tune to your institute).
  </p>

  <h2>Our output includes</h2>
  <ul>
    <li><strong>Question mapping:</strong> Each syllabus topic row has exactly five drills; 18 foundational templates appear once bank-wide,
    46 templates appear twice (practice + reinforcement), covering I/O, control flow, functions, arrays, strings, matrices, and mixed practice.</li>
    <li><strong>Exam / handout format:</strong> Matches the published-questions PDF pipeline: numbered titles, phase/module, difficulty,
    problem description, input/output format, constraints, sample I/O, and full test-case lists for staff PDF export.</li>
    <li><strong>Quality checks:</strong> Pedagogical ordering of repeats (not alphabetical), duplicate-stem tooling for admins, sequential Q labels,
    hidden-test policy for submits, and optional DB dedupe for legacy banks.</li>
  </ul>

  <div class="box">
    <p class="muted" style="margin-top:0">Process overview (mirror of classic exam-design flowcharts).</p>
    <pre class="mermaid">
flowchart TD
  A[Syllabus — C Foundation PDF] --> B[Map 22 topics × 5 slots]
  B --> C[Assign templates &amp; duplicates policy]
  C --> D[Seed DB / API + Monaco judge]
  D --> E[Difficulty &amp; hints layer]
  E --> F[Admin PDF export + LMS]
  F --> G[Iterate from staff feedback]
    </pre>
  </div>

  <div class="box">
    <p class="muted" style="margin-top:0">Indicative production timeline (adjust dates).</p>
    <pre class="mermaid">
gantt
    title C Code Lab — syllabus to bank
    dateFormat  YYYY-MM-DD
    section Preparation
    Syllabus &amp; seeds           :done, a1, 2026-05-01, 3d
    Judge &amp; hidden-case policy :done, a2, 2026-05-03, 2d
    section Build
    Topic seed authoring       :active, a3, 2026-05-06, 4d
    PDF + dedupe tooling       :a4, 2026-05-10, 3d
    section Delivery
    Pilot class &amp; tune marks   :a5, 2026-05-14, 5d
    </pre>
  </div>

  <h2>Table — Questions &amp; syllabus mapping</h2>
  <p class="muted">Auto-generated from <code>_TOPIC_SEEDS</code>. Column <em>Drill</em> is the display title of the seeded template.</p>
  <table class="mapping">
    <thead>
      <tr><th>Q&nbsp;No</th><th>Syllabus topic</th><th>Drill</th><th>Type</th><th>Marks</th><th>Difficulty</th></tr>
    </thead>
    <tbody>
{table_body}
    </tbody>
  </table>

  <h2>Representative samples (abbreviated)</h2>
  <div class="samples">Q&nbsp;example — Leap year (Phase&nbsp;2): stdin year → print Leap or Not (includes 2100 / 2000 checks in seeds).

Q&nbsp;example — Armstrong check (repeat pool): positive integer → Yes/No by digit-power sum.

Q&nbsp;example — Bubble sort drill: sort N integers ascending; wording allows bubble swaps or instructor-approved alternate.

Full prompts, constraints, samples, and all test vectors live in the database / PDF export — same layout as your reference bundle.</div>

  <h2>Deliverables</h2>
  <ul>
    <li>In-app syllabus progression, Run/Submit judging, attempts history.</li>
    <li>Admin: bulk PDF (<code>/api/admin/questions/export/pdf</code>), optional unique-stem PDF, duplicate-row cleanup.</li>
    <li>This document: regenerate anytime with<br/>
      <code>python backend/scripts/generate_executive_summary_html.py</code></li>
  </ul>

  <h2>References (typical C exercise sources)</h2>
  <ul>
    <li>w3resource — arrays, recursion, sorting: <a href="https://www.w3resource.com/c-programming-exercises/">w3resource C exercises</a></li>
    <li>Programiz — Armstrong, Fibonacci, patterns: <a href="https://www.programiz.com/c-programming/examples">Programiz examples</a></li>
  </ul>

  <p class="muted" style="margin-top:2rem;">Generated file: Executive-Summary-C-Code-Lab.html — Print to PDF from your browser if you need a PDF twin of the Word-style executive summary.</p>
</body>
</html>"""

    _OUT.write_text(doc, encoding="utf-8")
    print(f"Wrote {_OUT}")


if __name__ == "__main__":
    main()
