"""ZIP candidat i simulació completa aïllada; cap accés a la plataforma web."""

import argparse
import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
from time import perf_counter

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = ROOT / "artifacts/oriol_optimization"
OFFICIAL = ROOT.parent / "paquet_participants_datathon_upc"


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def worker():
    # -I elimina la carpeta del script i PYTHONPATH; només afegim el ZIP extret.
    extracted = Path.cwd().resolve()
    sys.path.insert(0, str(extracted))
    candidate = load(extracted / "agent.py", "isolated_candidate")
    helper = load(ROOT / "scripts/evaluate.py", "official_preprocessing")
    environment = load(OFFICIAL / "starter_kit/environment.py", "official_zip_environment")
    hourly = helper.load_hourly_data(OFFICIAL)
    result = helper.simulate(candidate.BatteryAgent, hourly, environment.CampusBatteryEnv)
    for name, module in list(sys.modules.items()):
        if name == "src" or name.startswith("src.") or name == "experiments" or name.startswith("experiments."):
            if not Path(module.__file__).resolve().is_relative_to(extracted):
                raise RuntimeError(f"Import local fora del ZIP: {name}")
    print(json.dumps(result, allow_nan=False))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--worker", action="store_true")
    args = parser.parse_args()
    if args.worker:
        worker()
        return
    sys.path.insert(0, str(ROOT))
    from scripts.package import validate_archive

    frozen = read(HERE / "candidate_config.json")
    selection = read(OUT / "validation_selection.json")
    expected = next(row for row in read(OUT / "diagnostic_results.json")["rows"] if row["policy"] == selection["winner"])
    if frozen["configuration"] != expected["configuration"] or frozen["parameters"] != expected["parameters"]:
        raise RuntimeError("La configuració no coincideix amb la candidata avaluada")
    if hashlib.sha256((HERE / "policies.py").read_bytes()).hexdigest() != selection["source_sha256"]["policies.py"]:
        raise RuntimeError("Les polítiques han canviat després de seleccionar")
    payload = {
        "agent.py": (HERE / "candidate_agent.py").read_bytes(),
        "candidate_config.json": (HERE / "candidate_config.json").read_bytes(),
        "experiments/__init__.py": b'"""Paquet local de la candidata."""\n',
        "experiments/oriol_optimization/__init__.py": (HERE / "__init__.py").read_bytes(),
        "experiments/oriol_optimization/policies.py": (HERE / "policies.py").read_bytes(),
        **{name: (ROOT / name).read_bytes() for name in ["src/__init__.py", "src/fallback.py", "src/safety.py"]},
    }
    archive_path = OUT / "candidate_submission.zip"
    with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, data in sorted(payload.items()):
            entry = zipfile.ZipInfo(name, date_time=(2026, 11, 14, 0, 0, 0))
            entry.compress_type = zipfile.ZIP_DEFLATED
            entry.create_system = 3
            entry.external_attr = 0o100644 << 16
            archive.writestr(entry, data)
    if archive_path.stat().st_size >= 25_000_000:
        raise RuntimeError("ZIP massa gran")
    checker = validate_archive(archive_path, OFFICIAL / "starter_kit/check_submission.py")
    (OUT / "candidate_checker.txt").write_text(checker.stdout + checker.stderr, encoding="utf-8")
    if checker.returncode:
        raise RuntimeError(checker.stdout + checker.stderr)
    started = perf_counter()
    with tempfile.TemporaryDirectory(prefix="masia_mpc_candidate_") as directory:
        with zipfile.ZipFile(archive_path) as archive:
            archive.extractall(directory)
        execution = subprocess.run([sys.executable, "-I", "-B", "-X", "utf8", str(Path(__file__).resolve()), "--worker"],
                                   cwd=directory, capture_output=True, text=True, encoding="utf-8", timeout=60)
        wall_seconds = perf_counter() - started
    if execution.returncode:
        raise RuntimeError(execution.stdout + execution.stderr)
    measured = json.loads(execution.stdout)
    for key in ["score", "co2_estalviat_pct", "cost_estalviat_pct", "infraccions", "actions_sha256", "soc_final_kwh", "steps"]:
        if measured[key] != expected[key]:
            raise RuntimeError(f"ZIP diferent del codi font: {key}")
    if measured["infraccions"] or measured["policy_failures"] or wall_seconds >= 45:
        raise RuntimeError("Candidata sense marge de runtime/seguretat")
    report = {
        "zip_sha256": hashlib.sha256(archive_path.read_bytes()).hexdigest(),
        "zip_bytes": archive_path.stat().st_size,
        "files_sha256": {name: hashlib.sha256(data).hexdigest() for name, data in payload.items()},
        "checker_return_code": checker.returncode,
        "full_isolated_process_seconds": wall_seconds,
        "matches_frozen_source_actions": True,
        "metrics": measured,
        "stable_commit": "99f3f4358cd85caf136cb0da5df51b2396ef7c21",
    }
    (OUT / "candidate_delivery.json").write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
