"""Coherència: els KPI que mostra el dashboard han de ser els de environment.py.

Requereix el paquet oficial en local (es salta si no hi és).
"""

import json

import numpy as np
import pytest

from dashboard.pipeline import agents as A
from dashboard.pipeline.config import OUT_DIR, kit_dir, load_spec
from dashboard.pipeline.data import contiguous_blocks, load_hourly
from dashboard.pipeline.metrics import recompute
from dashboard.pipeline.oracle import oracle_plan
from dashboard.pipeline.simulate import load_env_class, run

try:
    KIT = kit_dir()
except FileNotFoundError:
    KIT = None
pytestmark = pytest.mark.skipif(KIT is None, reason="paquet oficial no disponible")


@pytest.fixture(scope="module")
def ctx():
    spec = load_spec(KIT)
    return load_hourly(KIT), spec, load_env_class(KIT)


def test_hourly_table(ctx):
    hourly, _, _ = ctx
    assert len(hourly) == 5993
    blocks = contiguous_blocks(hourly.index)
    assert sum(b["hours"] for b in blocks) == len(hourly)


@pytest.mark.parametrize("make", [lambda k: A.StandbyAgent(),
                                  lambda k: A.ClampWrapper(A.load_agent_class(k / "starter_kit" / "agent.py")())])
def test_recompute_matches_official(ctx, make):
    hourly, spec, env_class = ctx
    res = run(make(KIT), hourly, env_class, spec)
    mine = recompute(hourly.load_kw, hourly.pv_kw, hourly.precio_eur_per_kwh, hourly.co2_kg_per_kwh,
                     res["applied"], res["infr"])
    off = res["official"]
    assert mine["score"] == pytest.approx(off["score"], abs=0.011)
    assert mine["co2_pct"] == pytest.approx(off["co2_estalviat_pct"], abs=0.011)
    assert mine["cost_pct"] == pytest.approx(off["cost_estalviat_pct"], abs=0.011)
    assert mine["infr"] == off["infraccions"]


def test_masked_recompute_matches_official(ctx):
    hourly, spec, env_class = ctx
    env = env_class(hourly, spec=spec)
    agent = A.ClampWrapper(A.load_agent_class(KIT / "starter_kit" / "agent.py")())
    obs, done = env.reset(), False
    while not done:
        obs, done = env.step(agent.act(obs))
    mask = (hourly.index.month == 1)
    off = env.evaluate_results(mask=mask)
    soc = np.asarray(env.soc_series)
    d = soc - np.r_[env.soc_init, soc[:-1]]
    applied = np.where(d > 0, d / env.eta_c, d * env.eta_d)
    mine = recompute(hourly.load_kw, hourly.pv_kw, hourly.precio_eur_per_kwh, hourly.co2_kg_per_kwh,
                     applied, env.infraccions_per_step, mask=mask)
    assert mine["score"] == pytest.approx(off["score"], abs=0.011)


def test_oracle_is_feasible_and_dominates(ctx):
    hourly, spec, env_class = ctx
    plan = oracle_plan(hourly, spec)
    res = run(A.ReplayAgent(plan), hourly, env_class, spec)
    assert res["official"]["infraccions"] == 0
    ref = run(A.ClampWrapper(A.load_agent_class(KIT / "starter_kit" / "agent.py")()), hourly, env_class, spec)
    assert res["official"]["score"] >= ref["official"]["score"]


def test_generated_files_consistent():
    if not (OUT_DIR / "agents.json").exists():
        pytest.skip("executa abans python -m dashboard.pipeline.build")
    agents = json.loads((OUT_DIR / "agents.json").read_text(encoding="utf-8"))
    base = json.loads((OUT_DIR / "base.json").read_text(encoding="utf-8"))
    n = len(base["t"])
    for a in agents:
        assert len(a["applied"]) == n and len(a["soc"]) == n
        assert all(-500.001 <= p <= 500.001 for p in a["applied"])
        assert all(-0.01 <= s <= 2000.01 for s in a["soc"])
