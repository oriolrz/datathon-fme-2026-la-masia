"""Rutes i constants del pipeline del dashboard.

Les dades oficials NO es copien al repositori: es llegeixen del paquet de
participants que cada membre té al seu ordinador.
Ordre de cerca del paquet:
  1. variable d'entorn UPC_KIT_DIR
  2. dashboard/config.local.json  ->  {"kit_dir": "C:/ruta/paquet_participants_datathon_upc"}
  3. ~/Documents/DATATHON/paquet_participants_datathon_upc
"""

from __future__ import annotations

import json
import os
from pathlib import Path

DASHBOARD_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = DASHBOARD_DIR.parent
OUT_DIR = DASHBOARD_DIR / "web" / "public" / "data"
CACHE_DIR = DASHBOARD_DIR / ".cache"


def kit_dir() -> Path:
    candidates = []
    if os.environ.get("UPC_KIT_DIR"):
        candidates.append(Path(os.environ["UPC_KIT_DIR"]))
    local = DASHBOARD_DIR / "config.local.json"
    if local.exists():
        candidates.append(Path(json.loads(local.read_text(encoding="utf-8"))["kit_dir"]))
    candidates.append(Path.home() / "Documents" / "DATATHON" / "paquet_participants_datathon_upc")
    for c in candidates:
        if (c / "starter_kit" / "environment.py").exists() and (c / "data" / "train").exists():
            return c
    raise FileNotFoundError(
        "No trobo el paquet oficial. Defineix UPC_KIT_DIR o dashboard/config.local.json. "
        f"Provats: {[str(c) for c in candidates]}"
    )


def load_spec(kit: Path) -> dict:
    return json.loads((kit / "starter_kit" / "battery_spec.json").read_text(encoding="utf-8"))


# Pesos oficials del score (environment.py / enunciat)
ALPHA_CO2 = 0.7
BETA_COST = 0.3
PENALTY_CODE = 0.20      # punts per infracció segons environment.py (0.002 * 100)
PENALTY_STATEMENT = 1.00  # punts per infracció segons l'ENUNCIAT.md (discrepància)
