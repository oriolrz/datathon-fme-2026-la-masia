"""Punt d'entrada: python -m dashboard.pipeline.build [--agent nom=ruta] [--git-agent nom=ref]

Genera dashboard/web/public/data/{meta,base,agents}.json a partir del simulador oficial.
S'atura si el recàlcul propi dels KPI no coincideix amb CampusBatteryEnv.evaluate_results.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone

import numpy as np

from . import agents as A
from .config import ALPHA_CO2, BETA_COST, OUT_DIR, PENALTY_CODE, PENALTY_STATEMENT, REPO_ROOT, kit_dir, load_spec
from .data import contiguous_blocks, load_hourly
from .metrics import recompute
from .oracle import oracle_plan
from .simulate import load_env_class, run


def _git(*args) -> str:
    try:
        return subprocess.check_output(["git", *args], cwd=REPO_ROOT, text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return ""


def _r(a, nd):
    return [round(float(x), nd) for x in a]


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--agent", action="append", default=[], help="nom=ruta/agent.py")
    ap.add_argument("--git-agent", action="append", default=[], help="nom=branca_o_commit")
    ap.add_argument("--no-team", action="store_true", help="no incloure els agents per defecte de l'equip")
    ap.add_argument("--no-oracle", action="store_true")
    args = ap.parse_args(argv)

    kit = kit_dir()
    spec = load_spec(kit)
    env_class = load_env_class(kit)
    print(f"[build] paquet oficial: {kit}")
    hourly = load_hourly(kit)
    print(f"[build] {len(hourly)} hores, {hourly.index[0]} -> {hourly.index[-1]}")

    defs = A.builtin_agents(kit)
    if not args.no_team:
        for d in A.TEAM_DEFAULTS:
            try:
                defs.append(A.git_agent(d["name"], d["ref"], d["label"], d["description"], d["owner"], d["color"]))
            except Exception as exc:  # branca inexistent en aquest clon
                print(f"[build] AVÍS: no s'ha pogut carregar {d['name']} ({d['ref']}): {exc}")
    for item in args.git_agent:
        name, ref = item.split("=", 1)
        defs.append(A.git_agent(name, ref))
    for item in args.agent:
        name, path = item.split("=", 1)
        defs.append(A.file_agent(name, path))
    if not args.no_oracle:
        print("[build] resolent l'òptim teòric (LP amb informació perfecta)...")
        plan = oracle_plan(hourly, spec)
        defs.append(A.AgentDef(
            "oracle", "Òptim teòric (informació perfecta)",
            "Programa lineal que coneix el consum, la solar, el preu i el CO2 futurs de tot el període. "
            "No és implementable: marca el sostre de puntuació possible amb aquesta bateria.",
            "La MasIA", "límit teòric", lambda plan=plan: A.ReplayAgent(plan), "pipeline/oracle.py",
            implementable=False, color="#1f9d6b"))

    load = hourly["load_kw"].to_numpy()
    pv = hourly["pv_kw"].to_numpy()
    price = hourly["precio_eur_per_kwh"].to_numpy()
    co2 = hourly["co2_kg_per_kwh"].to_numpy()

    out_agents = []
    for d in defs:
        agent = d.factory()
        res = run(agent, hourly, env_class, spec)
        mine = recompute(load, pv, price, co2, res["applied"], res["infr"])
        off = res["official"]
        for k_off, k_me, tol in [("score", "score", 0.011), ("co2_estalviat_pct", "co2_pct", 0.011),
                                 ("cost_estalviat_pct", "cost_pct", 0.011), ("infraccions", "infr", 0)]:
            if abs(off[k_off] - mine[k_me]) > tol:
                raise SystemExit(f"[build] INCOHERÈNCIA a {d.id}: {k_off} oficial={off[k_off]} propi={mine[k_me]}")
        print(f"[build] {d.id:18s} score={off['score']:6.2f}  CO2={off['co2_estalviat_pct']:5.2f}%  "
              f"cost={off['cost_estalviat_pct']:5.2f}%  infr={off['infraccions']:3d}  {res['runtime_s']:.2f}s")
        out_agents.append({
            "id": d.id, "label": d.label, "description": d.description, "owner": d.owner, "kind": d.kind,
            "source": d.source, "implementable": d.implementable, "color": d.color,
            "runtime_s": round(res["runtime_s"], 3),
            "official": off,
            "requested": _r(res["requested"], 2),
            "applied": _r(res["applied"], 2),
            "soc": _r(res["soc"], 1),
            "infr_idx": [int(i) for i in np.nonzero(res["infr"])[0]],
            "infr_n": [int(x) for x in res["infr"][res["infr"] > 0]],
        })

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    base = {
        "t": [ts.strftime("%Y-%m-%dT%H") for ts in hourly.index],
        "load": _r(load, 1), "pv": _r(pv, 1), "price": _r(price, 5), "co2": _r(co2, 5),
    }
    meta = {
        "schema_version": 2,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "git_commit": _git("rev-parse", "--short", "HEAD"),
        "git_branch": _git("rev-parse", "--abbrev-ref", "HEAD"),
        "python": sys.version.split()[0],
        "environment_sha256": hashlib.sha256((kit / "starter_kit" / "environment.py").read_bytes()).hexdigest()[:16],
        "dataset": "train",
        "dataset_note": "Dades d'entrenament oficials (setembre 2025 – agost 2026, sense els darrers 7 dies de cada mes). "
                        "No són el test ocult ni el leaderboard.",
        "hours": len(hourly),
        "start": hourly.index[0].isoformat(), "end": hourly.index[-1].isoformat(),
        "blocks": contiguous_blocks(hourly.index),
        "spec": spec,
        "score": {"alpha": ALPHA_CO2, "beta": BETA_COST, "penalty_code": PENALTY_CODE,
                  "penalty_statement": PENALTY_STATEMENT, "export_price": 0.0},
        "discrepancies": [
            "Penalització per infracció: environment.py resta 0,20 punts; l'ENUNCIAT.md diu 1,00.",
            "Preu d'exportació: environment.py i l'enunciat diuen 0 €/kWh; una secció de la web esmenta 0,04 €/kWh.",
            "Previsions de 24 h: el simulador local agafa les 24 files següents, encara que travessin un salt de dates.",
        ],
    }
    (OUT_DIR / "meta.json").write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8")
    (OUT_DIR / "base.json").write_text(json.dumps(base, separators=(",", ":")), encoding="utf-8")
    (OUT_DIR / "agents.json").write_text(json.dumps(out_agents, ensure_ascii=False, separators=(",", ":")),
                                         encoding="utf-8")
    print(f"[build] escrit a {OUT_DIR}")


if __name__ == "__main__":
    main()
