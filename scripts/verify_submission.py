"""Executa el ZIP final sobre tot el train en un procés aïllat i compara la traça."""

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

ROOT = Path(__file__).resolve().parents[1]


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def worker(official):
    # El cwd és exclusivament l'extracció del ZIP. -I ha eliminat PYTHONPATH
    # i la carpeta d'aquest script de sys.path: cap import de src del repo.
    extracted = Path.cwd().resolve()
    sys.path.insert(0, str(extracted))
    agent_module = load_module(extracted / "agent.py", "packaged_battery_agent")
    helper = load_module(ROOT / "scripts/evaluate.py", "evaluation_helpers")
    env_module = load_module(official / "starter_kit/environment.py", "packaged_environment")
    hourly = helper.load_hourly_data(official)
    result = helper.simulate(agent_module.BatteryAgent, hourly, env_module.CampusBatteryEnv)
    # Verificar també la procedència real dels imports auxiliars.
    for name, module in list(sys.modules.items()):
        if name == "src" or name.startswith("src."):
            if not Path(module.__file__).resolve().is_relative_to(extracted):
                raise RuntimeError(f"Import fora del ZIP: {name}")
    official_names = ["data/train/contador.csv", "data/train/inversor.csv", "data/train/precio_pvpc.csv",
                      "data/train/co2_red.csv", "starter_kit/environment.py", "starter_kit/battery_spec.json"]
    result["official_sha256"] = {name: helper.sha256(official / name) for name in official_names}
    print(json.dumps(result, allow_nan=False))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--official-root", type=Path, default=ROOT.parent / "paquet_participants_datathon_upc")
    parser.add_argument("--zip", type=Path, default=ROOT / "artifacts/submission.zip")
    parser.add_argument("--expected-metrics", type=Path, default=ROOT / "artifacts/evaluation/metrics.json")
    parser.add_argument("--output", type=Path, default=ROOT / "artifacts/validation/zip_simulation.json")
    parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.worker:
        worker(args.official_root.resolve())
        return
    expected = json.loads(args.expected_metrics.read_text(encoding="utf-8"))
    source = next(row for row in expected["rows"]
                  if row["period"] == "train_full" and row["policy"] == "battery_agent_fallback")
    archive_path = args.zip.resolve()
    # Confirmar que el codi empaquetat és el mateix que va produir les mètriques.
    with zipfile.ZipFile(archive_path) as archive:
        for name in archive.namelist():
            if name not in expected["source_sha256"]:
                raise ValueError(f"Fitxer del ZIP sense benchmark: {name}")
            if hashlib.sha256(archive.read(name)).hexdigest() != expected["source_sha256"][name]:
                raise ValueError(f"El ZIP i el benchmark tenen codi diferent: {name}")
        started = perf_counter()
        with tempfile.TemporaryDirectory(prefix="masia_full_zip_") as temporary:
            destination = Path(temporary).resolve()
            for member in archive.infolist():
                if not (destination / member.filename).resolve().is_relative_to(destination):
                    raise ValueError("Ruta no vàlida dins el ZIP")
            archive.extractall(destination)
            completed = subprocess.run(
                [sys.executable, "-I", "-B", "-X", "utf8", str(Path(__file__).resolve()),
                 "--worker", "--official-root", str(args.official_root.resolve())],
                cwd=destination, capture_output=True, text=True, encoding="utf-8", timeout=60,
            )
            seconds = perf_counter() - started
    if completed.returncode:
        raise RuntimeError(completed.stdout + completed.stderr)
    result = json.loads(completed.stdout)
    compare_keys = ["score", "co2_estalviat_pct", "cost_estalviat_pct", "co2_estalviat_kg",
                    "cost_estalviat_eur", "infraccions", "steps", "soc_final_kwh", "actions_sha256"]
    for key in compare_keys:
        if result[key] != source[key]:
            raise ValueError(f"El ZIP difereix del codi font: {key}")
    for name, fingerprint in result["official_sha256"].items():
        if fingerprint != expected["official_sha256"][name]:
            raise ValueError(f"Els inputs oficials han canviat: {name}")
    if result["infraccions"] or result["policy_failures"] or seconds >= 60:
        raise ValueError("El ZIP falla seguretat o timeout")
    result.update({
        "zip_sha256": hashlib.sha256(archive_path.read_bytes()).hexdigest(),
        "matches_source_actions_and_metrics": True,
        "isolated_process_seconds": round(seconds, 6),
        "runtime_scope": "Extracció ZIP + procés Python + imports + preprocessament + simulació completa + mètriques.",
        "data_role": "train_explored_not_independent_validation",
    })
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
