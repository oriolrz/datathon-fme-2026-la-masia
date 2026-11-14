"""Construeix un ZIP determinista i el valida fora del repositori amb el checker oficial."""

import argparse
import ast
import hashlib
import json
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ALLOWED_THIRD_PARTY = {"numpy", "pandas", "scipy", "sklearn", "joblib", "xgboost", "lightgbm"}
MAX_ZIP_BYTES = 25_000_000


def local_dependencies(root, entry="agent.py"):
    """Segueix imports estàtics locals, inclosos els __init__.py de cada paquet.

    No recorre carpetes senceres: només fitxers importats. Un import local
    absent falla encara que el codi el capturi amb try/except.
    Els futurs models/configuracions requereixen afegir un manifest explícit.
    """
    root = Path(root).resolve()
    pending, found = [Path(entry)], set()

    def enqueue_module(parts):
        base = Path(*parts)
        candidates = [base.with_suffix(".py"), base / "__init__.py"]
        source = next((path for path in candidates if (root / path).is_file()), None)
        if source is None:
            raise ValueError(f"Dependència local absent: {'.'.join(parts)}")
        pending.append(source)
        for depth in range(1, len(parts)):
            init = Path(*parts[:depth]) / "__init__.py"
            if not (root / init).is_file():
                raise ValueError(f"Falta {init}; els paquets locals han de ser explícits")
            pending.append(init)

    while pending:
        relative = pending.pop()
        if relative in found:
            continue
        source = root / relative
        if not source.is_file() or not source.resolve().is_relative_to(root):
            raise ValueError(f"Fitxer absent o fora del repositori: {relative}")
        found.add(relative)
        tree = ast.parse(source.read_text(encoding="utf-8"), filename=str(relative))
        for node in ast.walk(tree):
            modules = []
            if isinstance(node, ast.Import):
                modules = [alias.name.split(".") for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                if node.level:
                    package = relative.parent.parts
                    if node.level > len(package):
                        raise ValueError(f"Import relatiu fora del paquet: {relative}")
                    prefix = list(package[:len(package) - node.level + 1])
                    parts = prefix + (node.module.split(".") if node.module else [])
                else:
                    parts = node.module.split(".") if node.module else []
                if parts:
                    modules.append(parts)
                    for alias in node.names:
                        sub = root.joinpath(*parts, alias.name)
                        if sub.with_suffix(".py").is_file() or (sub / "__init__.py").is_file():
                            modules.append(parts + [alias.name])
            for parts in modules:
                name = parts[0]
                if (root / name).is_dir() or (root / f"{name}.py").is_file():
                    enqueue_module(parts)
                elif name not in sys.stdlib_module_names and name not in ALLOWED_THIRD_PARTY:
                    raise ValueError(f"Import no resolt o biblioteca no autoritzada: {'.'.join(parts)}")
    return sorted(found, key=lambda path: path.as_posix())


def build_archive(root, output):
    root, output = Path(root).resolve(), Path(output).resolve()
    files = local_dependencies(root)
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
        for relative in files:
            entry = zipfile.ZipInfo(relative.as_posix(), date_time=(2026, 11, 14, 0, 0, 0))
            entry.compress_type = zipfile.ZIP_DEFLATED
            entry.create_system = 3
            entry.external_attr = 0o100644 << 16
            archive.writestr(entry, (root / relative).read_bytes())
    if output.stat().st_size > MAX_ZIP_BYTES:
        raise ValueError("El ZIP supera els 25 MB")
    return files


def validate_archive(output, checker):
    """-I ignora PYTHONPATH; el cwd temporal impedeix importar el src del repo."""
    with tempfile.TemporaryDirectory(prefix="masia_checker_") as temporary:
        result = subprocess.run(
            [sys.executable, "-I", "-B", "-X", "utf8", str(Path(checker).resolve()), str(Path(output).resolve())],
            cwd=temporary, capture_output=True, text=True, encoding="utf-8", timeout=60,
        )
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--official-root", type=Path, default=ROOT.parent / "paquet_participants_datathon_upc")
    parser.add_argument("--output", type=Path, default=ROOT / "artifacts/submission.zip")
    args = parser.parse_args()
    output = args.output.resolve()
    checker = args.official_root.resolve() / "starter_kit/check_submission.py"
    if not checker.is_file():
        raise SystemExit(f"No existeix el checker oficial: {checker}")
    files = build_archive(ROOT, output)
    result = validate_archive(output, checker)
    log = result.stdout + result.stderr
    output.with_suffix(".checker.txt").write_text(log, encoding="utf-8")
    manifest = {
        "zip_name": output.name,
        "zip_sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
        "zip_bytes": output.stat().st_size,
        "files": {path.as_posix(): hashlib.sha256((ROOT / path).read_bytes()).hexdigest() for path in files},
        "checker_sha256": hashlib.sha256(checker.read_bytes()).hexdigest(),
        "checker_exit_code": result.returncode,
        "validation": "local_24_steps_isolated_not_web",
    }
    output.with_suffix(".manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(log)
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    if result.returncode:
        raise SystemExit(result.returncode)


if __name__ == "__main__":
    main()
