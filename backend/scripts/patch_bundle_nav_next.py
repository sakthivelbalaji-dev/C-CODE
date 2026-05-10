#!/usr/bin/env python3
"""Patch pre-built SPA bundle so Submit does not auto-advance and a Next button loads syllabus-next."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist" / "assets"
JS = sorted(DIST.glob("index-*.js"))
if len(JS) != 1:
    raise SystemExit(f"Expected exactly one index-*.js in {DIST}, got {JS}")
path = JS[0]
t = path.read_text(encoding="utf-8")


def subst(old: str, new: str, label: str) -> None:
    global t
    if old not in t:
        raise SystemExit(f"Missing anchor: {label}")
    t = t.replace(old, new, 1)


subst(
    "let ie=async e=>{try{let t=await fetch(Qn(`/questions/${e}/syllabus-next`)),r=await Wi(t);",
    "let ie=async e=>{try{let sr=l?.role!==`staff`&&l?.id!=null?"
    "`?student_id=${l.id}`:``;"
    "let t=await fetch(Qn(`/questions/${e}/syllabus-next${sr}`)),r=await Wi(t);",
    "ie() syllabus-next",
)


def extract_force_block(s: str) -> str:
    i = s.find("if(a.forceAfterTimeLimit){let e=await ie(_.id);")
    if i < 0:
        raise SystemExit("forceAfterTimeLimit anchor")
    j = s.find("}else if(!w)", i)
    if j < 0:
        raise SystemExit("elseif !w anchor")
    return s[i:j]


raw_block = extract_force_block(t)
new_tl = (
    "if(a.forceAfterTimeLimit){ne(!1),o(`${b}Time limit reached "
    "\u2014 your last graded attempt was captured.\nPassed ${x}/${S} "
    "test cases.${O}\n\nStay on this question; click Next question when "
    "you are ready to advance in syllabus order.`)}"
)

if raw_block.count("await ie(_.id)") != 1:
    raise SystemExit("unexpected force-block shape")
subst(raw_block, new_tl, "forceAfter block")


def extract_succ_chain(s: str) -> str:
    idx = s.find("}else if(!w)")
    if idx < 0:
        raise SystemExit("else if(!w)")
    needle = "}else o(`${b}"
    k = s.find(needle, idx + 50)
    if k < 0:
        raise SystemExit("run-mode else opener")
    return s[idx:k]


succ = extract_succ_chain(t)
if "should_move_next" not in succ:
    raise SystemExit("success chain malformed")

replacement_succ = (
    "}else if(!w)ne(!0),o(`${b}Compilation successful.\nPassed ${x}/${S} test cases.${O}\n\n"
    "Not all tests passed \u2014 you stay on this question. Improve your solution and "
    "press Submit again.`)"
    "else ne(!1),o(`${b}Compilation successful.\nPassed ${x}/${S} test cases.${O}\n\n"
    "All tests passed. Stay on this page to review your code; "
    "click Next question when you are ready to advance in syllabus order.`)"
)
subst(succ, replacement_succ, "submit success branches")


needle_btn = "`children:`Submit`})]})]}),(0,F.jsxs)(`aside`"

if needle_btn not in t:
    raise SystemExit("submit button row anchor")

next_btn = (
    "`children:`Submit`}),"
    '(0,F.jsx)(`button`,{type:`button`,disabled:s||P||!_?.id,'
    'title:`Open the following question in syllabus order`,'
    "onClick:async()=>{if(!_?.id)return;"
    'let rr=await ie(_.id);'
    'rr.ok?o(`Opened the next syllabus question.`):'
    'rr.noNext?o(`No next question remains in syllabus order.`):'
    'o(`Could not load the next question. Try again.`)} '
    ',className:`rounded-xl border border-brand-line/70 bg-brand-surface/85 px-5 '
    'py-2.5 text-sm font-medium text-brand-text transition hover:bg-brand-line/35 '
    'disabled:opacity-50`,children:`Next question`}'
    "]})]}),(0,F.jsxs)(`aside`"

)
subst(needle_btn, next_btn, "inject Next button")


path.write_text(t, encoding="utf-8")
print("Patched:", path)
