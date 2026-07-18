#!/usr/bin/env python3
"""Run all hardware-free protocol, daemon, harness, and safety-core checks."""

from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def run(command: list[str], **kwargs) -> None:
    print("+", " ".join(command), flush=True)
    subprocess.run(command, cwd=ROOT, check=True, **kwargs)


def main() -> None:
    base_python = (os.environ.get("ROVER_BEAN_PYTHON") or shutil.which("python3.12") or
                   shutil.which("python3.11"))
    if not base_python:
        raise SystemExit("Python 3.11 or 3.12 is required (or set ROVER_BEAN_PYTHON).")
    with tempfile.TemporaryDirectory(prefix="rover-bean-host-tests-") as temp:
        temp_path = Path(temp)
        venv = temp_path / "venv"
        run([base_python, "-m", "venv", str(venv)])
        python = venv / "bin" / "python"
        test_env = os.environ.copy()
        robotd_source = str(ROOT / "software" / "robotd" / "src")
        existing_path = test_env.get("PYTHONPATH")
        test_env["PYTHONPATH"] = (
            robotd_source + os.pathsep + existing_path if existing_path else robotd_source
        )
        run([str(python), "-m", "unittest", "discover", "-s", "software/robotd/tests", "-v"],
            env=test_env)
        run([str(python), "-m", "unittest", "discover", "-s", "commissioning/tests", "-v"],
            env=test_env)
        run([str(python), "-m", "unittest", "discover", "-s", "harness/tests", "-v"],
            env=test_env)
        run([str(python), "-m", "unittest", "discover", "-s", "software/appliance/tests", "-v"],
            env=test_env)
        run([str(python), "commissioning/fixture.py", "--check"])
        run([str(python), "software/appliance/appliance.py", "--check"])
        run(["bash", "-n", "software/install.sh"])
        run([str(python), "harness/generate_harness_docs.py", "--output", str(temp_path / "harness")])
        cmake = os.environ.get("ROVER_BEAN_CMAKE") or shutil.which("cmake")
        ctest = shutil.which("ctest")
        if cmake and ctest:
            build = temp_path / "safety-build"
            run([cmake, "-S", "firmware/pico2-safety", "-B", str(build)])
            run([cmake, "--build", str(build)])
            run([ctest, "--test-dir", str(build), "--output-on-failure"])
        else:
            compiler = os.environ.get("CC") or shutil.which("cc")
            if not compiler:
                raise SystemExit("CMake/CTest or a C11 compiler is required (or set CC).")
            safety_test = temp_path / "test_safety_core"
            run([
                compiler, "-std=c11", "-Wall", "-Wextra", "-Werror",
                "-Ifirmware/pico2-safety/include",
                "firmware/pico2-safety/src/safety_core.c",
                "firmware/pico2-safety/src/body_protocol.c",
                "firmware/pico2-safety/tests/test_safety_core.c",
                "-o", str(safety_test),
            ])
            run([str(safety_test)])
    print("ROVER_BEAN_HOST_TESTS_PASS")


if __name__ == "__main__":
    main()
