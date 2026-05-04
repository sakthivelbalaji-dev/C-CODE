import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Question
from ..schemas import JudgeCaseResult, JudgeRequest, JudgeResponse
from ..test_case_policy import is_hidden_test_case

router = APIRouter(prefix="/judge", tags=["judge"])

COMPILE_TIMEOUT_SECONDS = 8
RUN_TIMEOUT_SECONDS = 2
WINLIBS_BIN = (
    Path.home()
    / "AppData"
    / "Local"
    / "Microsoft"
    / "WinGet"
    / "Packages"
    / "BrechtSanders.WinLibs.POSIX.UCRT_Microsoft.Winget.Source_8wekyb3d8bbwe"
    / "mingw64"
    / "bin"
)


@router.post("/c", response_model=JudgeResponse)
def judge_c_code(payload: JudgeRequest, db: Session = Depends(get_db)):
    compiler = _resolve_compiler()
    if not compiler:
        raise HTTPException(
            status_code=500,
            detail="No C compiler found. Install gcc or clang and add it to PATH.",
        )

    if not payload.code.strip():
        raise HTTPException(status_code=400, detail="Code is empty")

    question = None
    if payload.question_id is not None:
        question = db.query(Question).filter(Question.id == payload.question_id).first()
        if not question:
            raise HTTPException(status_code=404, detail="Question not found")

    test_cases_raw = list(payload.test_cases)
    if question:
        test_cases_raw = json.loads(question.test_cases_json or "[]")
        if not isinstance(test_cases_raw, list):
            test_cases_raw = []

    mode = (payload.mode or "run").strip().lower()
    submit_mode = mode == "submit"

    eval_cases = [c for c in test_cases_raw if isinstance(c, dict)]
    if question and not submit_mode:
        eval_cases = [c for c in eval_cases if not is_hidden_test_case(c)]

    with tempfile.TemporaryDirectory(prefix="ccodelab_") as temp_dir:
        source_file = Path(temp_dir) / "main.c"
        binary_file = Path(temp_dir) / ("main.exe" if os.name == "nt" else "main")
        source_file.write_text(payload.code, encoding="utf-8")

        compile_ok, compile_output = _compile_source(compiler, source_file, binary_file)
        if not compile_ok:
            return JudgeResponse(
                compile_ok=False,
                compile_output=compile_output,
                custom_output=None,
                results=[],
                passed_case_count=0,
                total_case_count=0,
            )

        custom_output = None
        if payload.custom_input is not None:
            custom_output = _run_binary(binary_file, payload.custom_input)

        case_results: list[JudgeCaseResult] = []
        for index, case in enumerate(eval_cases):
            case_input = str(case.get("input", ""))
            expected_output = str(case.get("output", "")).strip()
            got_output = _run_binary(binary_file, case_input).strip()
            passed = got_output == expected_output
            hidden_case = question is not None and submit_mode and is_hidden_test_case(case)
            if question is None or not hidden_case:
                show_input = case_input
                show_expected = expected_output
                show_got = got_output
            else:
                show_input = ""
                show_expected = ""
                show_got = ""
            case_results.append(
                JudgeCaseResult(
                    index=index + 1,
                    input=show_input,
                    expected=show_expected,
                    got=show_got,
                    status="Passed" if passed else "Failed",
                    passed=passed,
                    hidden=hidden_case,
                )
            )

        passed_n = sum(1 for row in case_results if row.passed)
        return JudgeResponse(
            compile_ok=True,
            compile_output=compile_output,
            custom_output=custom_output.strip() if custom_output is not None else None,
            results=case_results,
            passed_case_count=passed_n,
            total_case_count=len(case_results),
        )


def _resolve_compiler() -> str | None:
    for name in ("gcc",):
        path = shutil.which(name)
        if path:
            return path
    winlibs_gcc = WINLIBS_BIN / "gcc.exe"
    if winlibs_gcc.exists():
        return str(winlibs_gcc)
    for name in ("clang", "cc"):
        path = shutil.which(name)
        if path:
            return path
    windows_fallbacks = [
        r"C:\Program Files\LLVM\bin\clang.exe",
        r"C:\Program Files\LLVM\bin\gcc.exe",
    ]
    for compiler_path in windows_fallbacks:
        if os.path.exists(compiler_path):
            return compiler_path
    return None


def _compile_source(compiler: str, source_file: Path, binary_file: Path) -> tuple[bool, str]:
    # Include -Wall so format/uninit issues surface in stderr while many builds still exit 0
    command = [
        compiler,
        str(source_file),
        "-O2",
        "-std=c11",
        "-Wall",
        "-Wformat=2",
        "-o",
        str(binary_file),
    ]
    process_env = _build_process_env()
    try:
        process = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=COMPILE_TIMEOUT_SECONDS,
            check=False,
            env=process_env,
            cwd=str(source_file.parent),
        )
    except subprocess.TimeoutExpired:
        return False, "Compilation timed out."
    except FileNotFoundError:
        return False, "Compiler not found. Install gcc and ensure it is available in PATH."
    except OSError as error:
        return False, f"Compiler execution error: {error}"

    compile_output = (process.stderr or process.stdout or "").strip()
    if process.returncode != 0:
        return False, compile_output or "Compilation failed."
    return True, compile_output or "Compilation successful."


def _run_binary(binary_file: Path, program_input: str) -> str:
    process_env = _build_process_env()
    try:
        process = subprocess.run(
            [str(binary_file)],
            input=program_input,
            capture_output=True,
            text=True,
            timeout=RUN_TIMEOUT_SECONDS,
            check=False,
            env=process_env,
            cwd=str(binary_file.parent),
        )
    except subprocess.TimeoutExpired:
        return "Execution timed out."
    except OSError as error:
        return f"Execution error: {error}"

    output = process.stdout.strip()
    error_text = process.stderr.strip()
    if process.returncode != 0 and error_text:
        return error_text
    return output


def _build_process_env() -> dict[str, str]:
    env = os.environ.copy()
    if WINLIBS_BIN.exists():
        env["PATH"] = f"{WINLIBS_BIN}{os.pathsep}{env.get('PATH', '')}"
    return env
