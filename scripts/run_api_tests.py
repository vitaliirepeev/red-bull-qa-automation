from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def run_phase(repository_root: Path, arguments: list[str]) -> int:
    return subprocess.run(
        [sys.executable, "-m", "pytest", *arguments],
        cwd=repository_root,
        check=False,
    ).returncode


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run parallel-safe API tests, followed by serial API tests."
    )
    parser.add_argument("--workers", type=int, default=5)
    parser.add_argument("--alluredir", default="allure-results-api")
    args = parser.parse_args()

    repository_root = Path(__file__).resolve().parent.parent

    print(f"Phase 1/2: parallel API tests ({args.workers} workers)", flush=True)
    parallel_exit_code = run_phase(
        repository_root,
        [
            "-n",
            str(args.workers),
            "-m",
            "api and not serial",
            "-q",
            f"--alluredir={args.alluredir}",
            "--clean-alluredir",
        ],
    )

    print("Phase 2/2: serial API tests (one worker)", flush=True)
    serial_exit_code = run_phase(
        repository_root,
        [
            "-n",
            "0",
            "-m",
            "api and serial",
            "-q",
            f"--alluredir={args.alluredir}",
        ],
    )

    return 1 if parallel_exit_code or serial_exit_code else 0


if __name__ == "__main__":
    raise SystemExit(main())
