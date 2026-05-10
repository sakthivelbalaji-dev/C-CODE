#!/usr/bin/env python3
"""Patch SPA bundle: Submit does not advance; add Next button; syllabus-next carries student_id."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist" / "assets"
JS = sorted(DIST.glob("index-*.js"))
if len(JS) != 1:
    raise SystemExit(f"Expected exactly one index-*.js in {DIST}, got {JS}")

path = JS[0]
t = path.read_text(encoding="utf-8")

old_ie = (
    "let ie=async e=>{try{let t=await fetch(Qn(`/questions/${e}/syllabus-next`)),r=await Wi(t);"
)
new_ie = (
    "let ie=async e=>{try{let sr=l?.role!==`staff`&&l?.id!=null?"
    "`?student_id=${l.id}`:``;"
    "let t=await fetch(Qn(`/questions/${e}/syllabus-next${sr}`)),r=await Wi(t);"
)
if old_ie not in t:
    raise SystemExit("missing ie() anchor (already patched?)")
t = t.replace(old_ie, new_ie, 1)

# Compile-error path must not jump to ie(); keep user on question.
compile_needle = (
    "}),e==="
    + chr(96)
    + "submit"
    + chr(96)
    + "&&a.forceAfterTimeLimit&&_?.id){let e=await ie(_.id);"
)
ci = t.find(compile_needle)
if ci < 0:
    raise SystemExit("compile-error time-limit anchor missing")
cj = t.find("return}D.current", ci)
old_compile = t[ci:cj]
new_compile = (
    "}),e==="
    + chr(96)
    + "submit"
    + chr(96)
    + "&&a.forceAfterTimeLimit&&_?.id){"
    + "o(e=>`${e}"
    + chr(92)
    + "n"
    + chr(92)
    + "n"
    + "Time limit reached. Stay on this question; click Next when you are ready "
    + "to advance.`)}"
)

if len(old_compile) < 200 or "opening the next syllabus question" not in old_compile:
    raise SystemExit("unexpected compile-error block")

t = t[:ci] + new_compile + t[cj:]

# Graded-submit success branches: drop auto-navigation.
marker_start = "if(a.forceAfterTimeLimit){let e=await ie(_.id);"
si = t.find(marker_start)
if si < 0:
    raise SystemExit("missing post-submit forceAfter anchor")

needle_run = (
    chr(96)
    + ")}else o(`${b}Compilation successful."
    + chr(92)
    + "nPassed ${x}/${S} test cases.${O}`)}catch(e){D.current="
)
ei = t.find(needle_run, si)
if ei < 0:
    raise SystemExit("could not find end of submit branch before catch")

old_mid = t[si:ei]
new_mid = (
    "if(a.forceAfterTimeLimit){ne(!1),o(`${b}Time limit reached \u2014 your last graded "
    "attempt was captured."
    + chr(92)
    + "nPassed ${x}/${S} test cases.${O}"
    + chr(92)
    + "n"
    + chr(92)
    + "nStay on this question; click Next when you are ready to advance.`)}else if(!w)"
    "ne(!0),o(`${b}Compilation successful."
    + chr(92)
    + "nPassed ${x}/${S} test cases.${O}"
    + chr(92)
    + "n"
    + chr(92)
    + "nNot all tests passed \u2014 stay on this question. Improve your solution and "
    "press Submit again.`)}else ne(!1),o(`${b}Compilation successful."
    + chr(92)
    + "nPassed ${x}/${S} test cases.${O}"
    + chr(92)
    + "n"
    + chr(92)
    + "nAll tests passed; your result is recorded. Stay here to review; click Next for "
    "the next syllabus question.`)}"
)

if len(old_mid) < 400 or "should_move_next" not in old_mid:
    raise SystemExit("unexpected submit-success block shape")
if old_mid == new_mid:
    raise SystemExit("noop")
t = t[:si] + new_mid + t[ei:]

old_buttons = (
    "rgba(34,197,94,0.55)] transition hover:brightness-110 disabled:opacity-50`,children:"
    "`Submit`})]})]}),"
    "(0,F.jsxs)(`aside`,{ref:w,"
)
next_btn = (
    "rgba(34,197,94,0.55)] transition hover:brightness-110 disabled:opacity-50`,children:"
    "`Submit`}),"
    "(0,F.jsx)(`button`,{type:`button`,disabled:s||P||!_?.id,"
    'title:`Open the following question in syllabus order`,'
    "onClick:async()=>{if(!_?.id)return;"
    "let rr=await ie(_.id);"
    "rr.ok?o(`Opened the next question.`):"
    "rr.noNext?o(`No next question in syllabus order.`):"
    'o(`Could not load the next question. Try again.`)},'
    "className:`rounded-xl border border-brand-line/70 bg-brand-surface/85 px-5 "
    "py-2.5 text-sm font-medium text-brand-text transition hover:bg-brand-line/35 "
    "disabled:opacity-50`,children:`Next`})]})]}),"
    "(0,F.jsxs)(`aside`,{ref:w,"
)

if old_buttons not in t:
    raise SystemExit("missing Submit button row anchor")
t = t.replace(old_buttons, next_btn, 1)

# Timer expires with blank editor — do not syllabus-jump unless user clicks Next.
zi = "Zi(e,_.id);let n=await ie(_.id);"
if zi in t:
    zi_idx = t.index(zi)
    zb = t.index("`Editor is blank", zi_idx)
    old_zi = t[zi_idx:zb]
    new_zi = (
        "Zi(e,_.id);o(`Time limit reached with an empty editor \u2014 recorded as "
        "a failed attempt on your profile (reattempt available). Stay on this question; "
        "click Next when you want to advance.`);return}"
    )
    if len(old_zi) < 100 or "Moved you to the next syllabus question" not in old_zi:
        raise SystemExit("unexpected empty-editor timer block")
    t = t[:zi_idx] + new_zi + t[zb:]

path.write_text(t, encoding="utf-8")
print("Patched:", path)
