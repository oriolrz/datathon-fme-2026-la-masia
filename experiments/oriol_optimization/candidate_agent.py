"""Entrada lliurable de la candidata congelada; no substitueix agent.py estable."""

import json
from pathlib import Path

from experiments.oriol_optimization.policies import MPCPolicy


class BatteryAgent:
    def __init__(self):
        frozen = json.loads(Path(__file__).with_name("candidate_config.json").read_text(encoding="utf-8"))
        configuration = frozen["configuration"]
        if configuration["kind"] != "mpc":
            raise ValueError("Aquest lliurable correspon al MPC seleccionat")
        self.controller = MPCPolicy(
            frozen["parameters"],
            terminal_factor=configuration.get("terminal_factor", 0.0),
            terminal_target=configuration.get("terminal_target"),
        )

    @property
    def policy_failures(self):
        return self.controller.failures

    def act(self, obs: dict) -> float:
        return self.controller.act(obs)
