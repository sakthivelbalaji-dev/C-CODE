"""Patch built SPA bundle: hidden test_case_count rows + time-limit count.

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

    old_effect = (
        "(0,S.useEffect)(()=>{C((_.test_cases||[]).map((e,t)=>({name:`Case ${t+1}`,"
        "input:e.input||``,expected:e.output||``,got:`-`,status:`Pending`})))},[_]);"
    )
    new_effect = (
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

    for label, old, new in (
        ("useEffect", old_effect, new_effect),
        ("guard", old_guard, new_guard),
        ("timeLimit", old_time, new_time),
    ):
        if old not in s:
            raise SystemExit(f"Missing chunk ({label}): {old[:80]}...")
        s = s.replace(old, new, 1)

    path.write_text(s, encoding="utf-8")
    print("patched", path)


if __name__ == "__main__":
    main()
