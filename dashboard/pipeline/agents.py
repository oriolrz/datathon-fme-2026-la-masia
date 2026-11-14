"""Registre d'agents que el dashboard compara.

Cada entrada crea un objecte amb `act(obs) -> float`. Els agents dels companys
es carreguen directament des d'una branca de Git (sense tocar-ne els fitxers),
o des d'un fitxer local, de manera que el dashboard sempre mostra codi real.

Afegir un agent sense tocar codi:
    python -m dashboard.pipeline.build --agent nom=ruta/agent.py
    python -m dashboard.pipeline.build --git-agent nom=origin/feat/dani-optimizer
"""

from __future__ import annotations

import importlib.util
import io
import subprocess
import sys
import tarfile
from dataclasses import dataclass, field
from math import sqrt
from pathlib import Path
from typing import Callable

from .config import CACHE_DIR, REPO_ROOT

ETA = sqrt(0.9)
CAP = 2000.0
PMAX = 500.0
EPS = 1e-4


def clamp(action: float, soc: float) -> float:
    hi = max(0.0, min(PMAX, (CAP - soc) / ETA - EPS))
    lo = -max(0.0, min(PMAX, soc * ETA - EPS))
    return float(max(lo, min(hi, action)))


@dataclass
class AgentDef:
    id: str
    label: str
    description: str
    owner: str
    kind: str                 # "referència" | "equip" | "límit teòric"
    factory: Callable[[], object] = field(repr=False)
    source: str = ""
    implementable: bool = True
    color: str = ""


# ----------------------------------------------------------------- utilitats
_PURGE_PREFIXES = ("agent", "src", "policy", "safety", "fallback", "forecast", "mpc")


def _purge_modules():
    for name in list(sys.modules):
        if name.split(".")[0] in _PURGE_PREFIXES:
            del sys.modules[name]


def load_agent_class(agent_file: Path):
    """Importa BatteryAgent d'un fitxer amb el seu directori com a arrel d'imports."""
    agent_file = Path(agent_file).resolve()
    root = str(agent_file.parent)
    _purge_modules()
    sys.path.insert(0, root)
    try:
        spec = importlib.util.spec_from_file_location("agent", agent_file)
        module = importlib.util.module_from_spec(spec)
        sys.modules["agent"] = module
        spec.loader.exec_module(module)
        cls = module.BatteryAgent
    finally:
        sys.path.remove(root)
    return cls


def checkout_git_ref(ref: str, name: str) -> tuple[Path, str]:
    """Extreu el contingut d'una branca/commit a .cache/agents/<name> i retorna (dir, sha)."""
    sha = subprocess.check_output(["git", "rev-parse", "--short", ref], cwd=REPO_ROOT, text=True).strip()
    target = CACHE_DIR / "agents" / f"{name}-{sha}"
    if not (target / "agent.py").exists():
        target.mkdir(parents=True, exist_ok=True)
        data = subprocess.check_output(["git", "archive", "--format=tar", ref], cwd=REPO_ROOT)
        with tarfile.open(fileobj=io.BytesIO(data)) as tar:
            members = [m for m in tar.getmembers()
                       if m.name == "agent.py" or m.name.startswith("src/")]
            tar.extractall(target, members=members, filter="data")
    return target, sha


class StandbyAgent:
    def act(self, obs):
        return 0.0


class ClampWrapper:
    def __init__(self, inner):
        self.inner = inner

    def act(self, obs):
        return clamp(self.inner.act(obs), float(obs["soc_kwh"]))


class ReplayAgent:
    """Reprodueix un pla d'accions precalculat (p. ex. l'òptim amb informació perfecta)."""

    def __init__(self, plan):
        self.plan = list(plan)
        self.t = 0

    def act(self, obs):
        a = self.plan[self.t] if self.t < len(self.plan) else 0.0
        self.t += 1
        return clamp(a, float(obs["soc_kwh"]))


# ----------------------------------------------------------------- registre
def builtin_agents(kit: Path) -> list[AgentDef]:
    starter = kit / "starter_kit" / "agent.py"
    defs = [
        AgentDef("standby", "Sense bateria (0 kW)", "Bateria sempre en repòs: equival al baseline oficial.",
                 "oficial", "referència", lambda: StandbyAgent(), "builtin", color="#8a94a6"),
        AgentDef("plantilla_oficial", "Plantilla oficial", "starter_kit/agent.py sense cap canvi (regles horàries).",
                 "organització", "referència", lambda: load_agent_class(starter)(), "starter_kit/agent.py",
                 color="#c0841a"),
        AgentDef("plantilla_clamp", "Plantilla + clamp exacte",
                 "La mateixa plantilla amb el límit físic exacte (eta=sqrt(0.9), eps=1e-4).",
                 "La MasIA", "referència", lambda: ClampWrapper(load_agent_class(starter)()),
                 "starter_kit/agent.py + clamp", color="#d6a243"),
    ]
    return defs


def file_agent(name: str, path: str, owner: str = "equip") -> AgentDef:
    p = Path(path)
    if not p.is_absolute():
        p = REPO_ROOT / p
    return AgentDef(name, name, f"Agent local {p.name}", owner, "equip",
                    lambda: load_agent_class(p)(), str(p.relative_to(REPO_ROOT)) if p.is_relative_to(REPO_ROOT) else str(p))


def git_agent(name: str, ref: str, label: str | None = None, description: str = "",
              owner: str = "equip", color: str = "") -> AgentDef:
    target, sha = checkout_git_ref(ref, name)
    return AgentDef(name, label or name, description or f"agent.py de {ref}", owner, "equip",
                    lambda: load_agent_class(target / "agent.py")(), f"{ref}@{sha}", color=color)


# Agents de l'equip que el build inclou per defecte (si la branca existeix).
TEAM_DEFAULTS = [
    dict(name="oriol_v1", ref="origin/feat/oriol-integration",
         label="La MasIA v1 (tramès 13:26)",
         description="Llindars 24h CO2+preu amb clamp central. Versió del PR #6 enviada al leaderboard.",
         owner="Oriol", color="#2f6fed"),
]
