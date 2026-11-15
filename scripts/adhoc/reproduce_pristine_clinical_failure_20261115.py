"""Reproduce the inherited live-API test under OS denial, #1996, 2026-11-15.

Inputs: exact clean v0.2.1 checkout, current isolated Python environment.
Output: provenance and unmodified native pytest stdout/exit; no test patches.
The caller must use the retained deny_network_tests_20261115.sb profile.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

BASE = "ae3979a14b9c99cc681ab1731e20c9df580b567f"
NODE = (
    "tests/test_clinicaltrials_integration.py::"
    "TestClinicalTrialsLiveAPI::test_fetch_real_clinical_trial"
)
INPUTS = (
    "tests/test_clinicaltrials_integration.py",
    "tests/conftest.py",
    "src/linkml_reference_validator/etl/sources/clinicaltrials.py",
    "src/linkml_reference_validator/models.py",
    "pytest.ini",
    "pyproject.toml",
    "uv.lock",
)


def git(root, *args):
    return subprocess.check_output(["git", "-C", str(root), *args], text=True).strip()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", type=Path, required=True)
    args = parser.parse_args()
    root = args.baseline.resolve()
    if git(root, "rev-parse", "HEAD") != BASE or git(root, "status", "--porcelain"):
        parser.error("baseline must be pristine at exact v0.2.1")
    captured = {name: (root / name).read_bytes() for name in INPUTS}
    env = os.environ.copy()
    env["PYTHONPATH"] = str(root / "src")
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    command = [sys.executable, "-m", "pytest", NODE, "-vv", "--tb=long"]
    print(json.dumps({
        "baseline": str(root),
        "head": BASE,
        "command": command,
        "pythonpath": env["PYTHONPATH"],
        "inputs": {name: hashlib.sha256(raw).hexdigest() for name, raw in captured.items()},
        "network_boundary": "inherited OS sandbox deny network; no provider patches",
    }, indent=2), flush=True)
    result = subprocess.run(command, cwd=root, env=env)
    if (
        git(root, "rev-parse", "HEAD") != BASE
        or git(root, "status", "--porcelain")
        or any((root / name).read_bytes() != raw for name, raw in captured.items())
    ):
        raise ValueError("pristine baseline changed during reproduction")
    print(json.dumps({"native_exit_code": result.returncode, "baseline_unchanged": True}), flush=True)
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
