"""Patch built SPA bundle: test-case guard/time-limit helpers for hidden suites.

Run after ``npm run build`` whenever ``backend/dist/assets/index-*.js`` is regenerated
(Vite hashes the filename).
"""
from pathlib import Path


def main() -> None:
    assets = Path(__file__).resolve().parent.parent / "dist" / "assets"
    paths = sorted(assets.glob("index-*.js"))
    if not paths:
        raise SystemExit(f"No index-*.js under {assets}")
    path = paths[0]
    s = path.read_text(encoding="utf-8")

    patched_effect = (
        "(0,S.useEffect)(()=>{C((_.test_cases||[]).map((e,t)=>({name:`Case ${t+1}`,"
        "input:e.input||``,expected:e.output||``,got:`-`,status:`Pending`})))},[_]);"
    )
    legacy_effect = (
        "(0,S.useEffect)(()=>{let tc=_.test_cases||[],n=Number(_.test_case_count)||0,"
        "len=Math.max(tc.length,n);C(Array.from({length:len},(_,t)=>{let e2=tc[t];"
        "return e2?{name:`Case ${t+1}`,input:e2.input||``,expected:e2.output||``,"
        "got:`-`,status:`Pending`}:{name:`Case ${t+1}`,input:``,expected:``,got:`-`,"
        "status:`Pending`}}))},[_]);"
    )

    old_guard = (
        "if(x.length===0){o(`No test cases available for this question.`);return}"
    )
    new_guard = (
        "if(x.length===0&&!(Number(_.test_case_count)>0)){"
        "o(`No test cases available for this question.`);return}"
    )

    old_time = (
        "let e=l||Xi(),t=Array.isArray(_.test_cases)?_.test_cases.length:0;if(e?.id&&e.role!==`staff`){"
    )
    new_time = (
        "let e=l||Xi(),t=Math.max(Array.isArray(_.test_cases)?_.test_cases.length:0,"
        "Number(_.test_case_count)||0);if(e?.id&&e.role!==`staff`){"
    )

    if legacy_effect in s:
        s = s.replace(legacy_effect, patched_effect, 1)
        print("replaced legacy padded test-case useEffect")
    elif patched_effect not in s:
        raise SystemExit("Missing expected useEffect snippet for test cases")

    if old_guard in s:
        s = s.replace(old_guard, new_guard, 1)
    elif new_guard not in s:
        raise SystemExit(f"Missing guard snippet")

    if old_time in s:
        s = s.replace(old_time, new_time, 1)
    elif new_time not in s:
        raise SystemExit(f"Missing timeLimit snippet")

    path.write_text(s, encoding="utf-8")
    print("patched", path)


if __name__ == "__main__":
    main()
