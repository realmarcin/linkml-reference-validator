"""Exercise real installed extra-module refusal/restoration, #2933, 2026-11-15.

Input: current distribution verifier. Output: exclusive synthetic source, wheel,
venv and three subprocess logs under the requested private namespace. No actual
candidate installation or runtime code is changed; no network is used.
"""

import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import sys
import venv
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[2]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    if output.exists() or not output.is_relative_to(ROOT / ".temp"):
        raise ValueError("Use a new private output namespace")
    helper = ROOT / "scripts/adhoc/verify_source_candidate_distribution_20261115.py"
    helper_raw = helper.read_bytes()
    output.mkdir(parents=True, exist_ok=False)
    copied_helper = output / "scripts/adhoc" / helper.name
    copied_helper.parent.mkdir(parents=True)
    copied_helper.write_bytes(helper_raw)
    package_name = "linkml_reference_validator"
    source = output / "src" / package_name
    source.mkdir(parents=True)
    members = {"__init__.py": b'"""Synthetic package, no imports."""\n',
               "module.py": b'VALUE = "retained"\n'}
    wheel = output / "synthetic.whl"
    with ZipFile(wheel, "w") as archive:
        for name, raw in members.items():
            (source / name).write_bytes(raw)
            archive.writestr(f"{package_name}/{name}", raw)
    environment = output / "environment"
    venv.EnvBuilder(with_pip=False).create(environment)
    installed = environment / f"lib/python{sys.version_info.major}.{sys.version_info.minor}/site-packages" / package_name
    installed.mkdir(parents=True)
    for name, raw in members.items():
        (installed / name).write_bytes(raw)
    command = [str(environment / "bin/python"), str(copied_helper), str(wheel), "--installed"]
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
    env.pop("PYTHONPATH", None)
    results = {}

    def run(name):
        result = subprocess.run(command, cwd=output, env=env, capture_output=True, text=True)
        (output / f"{name}.stdout").write_text(result.stdout)
        (output / f"{name}.stderr").write_text(result.stderr)
        results[name] = {"exit_code": result.returncode,
                         "stdout_sha256": sha256(result.stdout.encode()).hexdigest(),
                         "stderr_sha256": sha256(result.stderr.encode()).hexdigest()}
        return result

    before = run("positive-before")
    if before.returncode != 0 or json.loads(before.stdout)["exact_members"] != 2:
        raise ValueError("Positive-before verification failed")
    extra = installed / "stale_extra.py"
    extra.write_text('STALE = "unexpected importable module"\n')
    try:
        refusal = run("extra-module")
    finally:
        extra.unlink()
        after = run("positive-after")
    passed = (refusal.returncode != 0 and not refusal.stdout
              and "Installed Python membership differs" in refusal.stderr
              and after.returncode == 0 and json.loads(after.stdout)["exact_members"] == 2)
    report = {"verifier_sha256": sha256(helper_raw).hexdigest(), "results": results,
              "extra_removed": not extra.exists(), "control_passed": passed}
    (output / "receipt.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    if not passed:
        raise ValueError("Unexpected installed extra module was admitted or restoration failed")
    if helper.read_bytes() != helper_raw:
        raise ValueError("Verifier changed during control")


if __name__ == "__main__":
    main()
