"""Verify source→wheel→installed Python bytes for #1996, 2026-11-15.

Inputs: explicit wheel and this repository's source tree; optionally current
interpreter's installed package. Output: hash manifest on stdout, no mutations.
This validates bytes rather than trusting a package version or installer exit.
"""

import argparse
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
import sys
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[2]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("wheel", type=Path)
    parser.add_argument("--installed", action="store_true")
    args = parser.parse_args()
    raw = args.wheel.read_bytes()
    source_root = ROOT / "src/linkml_reference_validator"
    sources = {path: path.read_bytes() for path in source_root.rglob("*.py")}
    if not sources or any(path.is_symlink() for path in sources):
        raise ValueError("No source package or unsafe source path")
    captured = {args.wheel: raw, **sources}
    rows = []
    package = None
    installed_python = None
    if args.installed:
        import linkml_reference_validator
        package = Path(linkml_reference_validator.__file__).resolve().parent
        if not package.is_relative_to(Path(sys.prefix).resolve()):
            raise ValueError("The package must be installed inside this interpreter's environment")
        installed_python = {path.relative_to(package) for path in package.rglob("*.py")}
        if installed_python != {path.relative_to(source_root) for path in sources}:
            raise ValueError("Installed Python membership differs from source tree")
    with ZipFile(BytesIO(raw)) as archive:
        names = archive.namelist()
        if len(names) != len(set(names)):
            raise ValueError("Duplicate wheel member")
        wheel_python = {name for name in names if name.startswith("linkml_reference_validator/") and name.endswith(".py")}
        expected_python = {str(path.relative_to(ROOT / "src")) for path in sources}
        if wheel_python != expected_python:
            raise ValueError("Wheel Python membership differs from source tree")
        for path, source in sorted(sources.items()):
            member = str(path.relative_to(ROOT / "src"))
            if archive.read(member) != source:
                raise ValueError(f"Wheel source differs: {member}")
            item = {"member": member, "sha256": sha256(source).hexdigest()}
            if package is not None:
                installed_path = package / path.relative_to(source_root)
                installed = installed_path.read_bytes()
                if installed_path.is_symlink() or installed != source:
                    raise ValueError(f"Installed source differs: {member}")
                captured[installed_path] = installed
                item["installed_path"] = str(installed_path)
            rows.append(item)
    if any(path.read_bytes() != expected for path, expected in captured.items()):
        raise ValueError("Captured candidate bytes changed during verification")
    if set(source_root.rglob("*.py")) != set(sources):
        raise ValueError("Source Python membership changed during verification")
    if package is not None and {
        path.relative_to(package) for path in package.rglob("*.py")
    } != installed_python:
        raise ValueError("Installed Python membership changed during verification")
    print(json.dumps({"wheel": str(args.wheel), "wheel_sha256": sha256(raw).hexdigest(),
                      "python": sys.version, "executable": sys.executable,
                      "installed_package": str(package) if package else None,
                      "exact_members": len(rows), "inputs_unchanged": True, "members": rows}, indent=2))


if __name__ == "__main__":
    main()
