import json
import os
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

try:
    import resource
except ImportError:  # pragma: no cover - Windows
    resource = None

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Question
from ..schemas import JudgeCaseResult, JudgeRequest, JudgeResponse, JudgeRunResult
from ..test_case_policy import is_hidden_test_case

router = APIRouter(prefix="/judge", tags=["judge"])

COMPILE_TIMEOUT_SECONDS = 8
RUN_TIMEOUT_SECONDS = 2
MEMORY_LIMIT_MB = 256
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
DEFAULT_FALLBACK_CASES = [
    {"input": "Mia\n19\n", "output": "Mia 19", "is_hidden": False},
    {"input": "Alex\n21\n", "output": "Alex 21", "is_hidden": False},
    {"input": "Zoe\n20\n", "output": "Zoe 20", "is_hidden": True},
]


@router.post("/c", response_model=JudgeResponse)
def judge_c_code(payload: JudgeRequest, db: Session = Depends(get_db)):
    try:
        compiler = _resolve_compiler()
        if not compiler:
            return JudgeResponse(compile_ok=False, compile_output="No C compiler found. Install gcc or clang and add it to PATH.", custom_output=None, results=[], run_results=[], passed_case_count=0, total_case_count=0, status="Compilation Error", runtime_ms=0)
        if not payload.code.strip():
            return JudgeResponse(compile_ok=False, compile_output="Code is empty", custom_output=None, results=[], run_results=[], passed_case_count=0, total_case_count=0, status="Compilation Error", runtime_ms=0)

        question = None
        if payload.question_id is not None:
            question = db.query(Question).filter(Question.id == payload.question_id).first()
            if not question:
                return JudgeResponse(compile_ok=False, compile_output="Question not found", custom_output=None, results=[], run_results=[], passed_case_count=0, total_case_count=0, status="Runtime Error", runtime_ms=0)

        test_cases_raw = list(payload.test_cases)
        if question:
            try:
                test_cases_raw = json.loads(question.test_cases_json or "[]")
            except json.JSONDecodeError:
                test_cases_raw = []
            if not isinstance(test_cases_raw, list):
                test_cases_raw = []
            if not test_cases_raw:
                test_cases_raw = _fallback_cases_from_question(question)

        submit_mode = (payload.mode or "run").strip().lower() == "submit"
        eval_cases = [c for c in test_cases_raw if isinstance(c, dict)]

        with tempfile.TemporaryDirectory(prefix="ccodelab_") as temp_dir:
            source_file = Path(temp_dir) / "main.c"
            binary_file = Path(temp_dir) / ("main.exe" if os.name == "nt" else "main")
            source_file.write_text(payload.code, encoding="utf-8")

            compile_ok, compile_output = _compile_source(compiler, source_file, binary_file)
            if not compile_ok:
                return JudgeResponse(compile_ok=False, compile_output=compile_output, custom_output=None, results=[], run_results=[], passed_case_count=0, total_case_count=0, status="Compilation Error", runtime_ms=0)

            custom_output = None
            if payload.custom_input is not None:
                custom_result = _run_binary(binary_file, payload.custom_input)
                custom_output = str(custom_result.get("output", ""))

            case_results: list[JudgeCaseResult] = []
            run_results: list[JudgeRunResult] = []
            runtime_ms = 0
            final_status = "Accepted"
            for index, case in enumerate(eval_cases):
                case_input = str(case.get("input", ""))
                expected_output = _normalize_output(str(case.get("output", "")))
                run_result = _run_binary(binary_file, case_input)
                runtime_ms += int(run_result["runtime_ms"])
                got_output = _normalize_output(str(run_result["output"]))
                if run_result["status"] == "Time Limit Exceeded":
                    passed = False
                    final_status = "Time Limit Exceeded"
                elif run_result["status"] == "Runtime Error":
                    passed = False
                    if final_status == "Accepted":
                        final_status = "Runtime Error"
                else:
                    passed = got_output == expected_output
                    if not passed and final_status == "Accepted":
                        final_status = "Wrong Answer"

                hidden_case = question is not None and is_hidden_test_case(case)
                if hidden_case:
                    # Do not reveal I/O for graded hidden cases (still shows pass/fail).
                    show_input = show_expected = show_got = "— hidden —"
                else:
                    show_input, show_expected, show_got = case_input, expected_output, got_output

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
                if not submit_mode:
                    run_results.append(
                        JudgeRunResult(index=index + 1, status="Passed" if passed else "Failed", passed=passed)
                    )
                if submit_mode and final_status in ("Time Limit Exceeded", "Runtime Error"):
                    break

            passed_n = sum(1 for row in case_results if row.passed)
            total_n = len(case_results)
            if total_n > 0 and passed_n == total_n:
                final_status = "Accepted"

            return JudgeResponse(
                compile_ok=True,
                compile_output=compile_output,
                custom_output=custom_output.strip() if custom_output is not None else None,
                results=case_results,
                run_results=[] if submit_mode else run_results,
                passed_case_count=passed_n,
                total_case_count=total_n,
                status=final_status,
                runtime_ms=runtime_ms,
            )
    except Exception as exc:
        return JudgeResponse(compile_ok=False, compile_output=f"Judge internal error: {exc}", custom_output=None, results=[], run_results=[], passed_case_count=0, total_case_count=0, status="Runtime Error", runtime_ms=0)


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


def _normalize_output(value: str) -> str:
    return value.replace("\r\n", "\n").strip()


def _run_binary(binary_file: Path, program_input: str) -> dict[str, str | int]:
    process_env = _build_process_env()
    started = time.perf_counter()
    try:
        preexec_fn = None
        if os.name != "nt":
            # Best-effort memory limit for POSIX workers.
            preexec_fn = _build_preexec_memory_limiter()
        process = subprocess.run(
            [str(binary_file)],
            input=program_input,
            capture_output=True,
            text=True,
            timeout=RUN_TIMEOUT_SECONDS,
            check=False,
            env=process_env,
            cwd=str(binary_file.parent),
            preexec_fn=preexec_fn,
        )
    except subprocess.TimeoutExpired:
        elapsed = int((time.perf_counter() - started) * 1000)
        return {"output": "", "status": "Time Limit Exceeded", "runtime_ms": elapsed}
    except OSError as error:
        elapsed = int((time.perf_counter() - started) * 1000)
        return {"output": f"Execution error: {error}", "status": "Runtime Error", "runtime_ms": elapsed}

    elapsed = int((time.perf_counter() - started) * 1000)
    output = process.stdout or ""
    error_text = process.stderr or ""
    if process.returncode != 0:
        runtime_msg = error_text.strip() or output.strip() or "Runtime error"
        return {"output": runtime_msg, "status": "Runtime Error", "runtime_ms": elapsed}
    return {"output": output, "status": "OK", "runtime_ms": elapsed}


def _build_process_env() -> dict[str, str]:
    env = os.environ.copy()
    if WINLIBS_BIN.exists():
        env["PATH"] = f"{WINLIBS_BIN}{os.pathsep}{env.get('PATH', '')}"
    return env


def _fallback_cases_from_question(question: Question) -> list[dict]:
    cases: list[dict] = []
    sample_in = (question.sample_input or "").strip()
    sample_out = (question.expected_output or "").strip()
    if sample_in or sample_out:
        cases.append({"input": sample_in, "output": sample_out, "is_hidden": False})

    if not cases:
        try:
            examples = json.loads(question.examples_json or "[]")
        except json.JSONDecodeError:
            examples = []
        if isinstance(examples, list):
            for row in examples:
                if not isinstance(row, dict):
                    continue
                ex_in = str(row.get("input", "")).strip()
                ex_out = str(row.get("output", "")).strip()
                if ex_in or ex_out:
                    cases.append({"input": ex_in, "output": ex_out, "is_hidden": False})

    if not cases:
        cases = list(DEFAULT_FALLBACK_CASES)

    return cases


def _build_preexec_memory_limiter():
    if resource is None:
        return None
    memory_limit_bytes = MEMORY_LIMIT_MB * 1024 * 1024

    def _set_limits():
        resource.setrlimit(resource.RLIMIT_AS, (memory_limit_bytes, memory_limit_bytes))

    return _set_limits
