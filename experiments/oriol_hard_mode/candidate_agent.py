"""Entrada del ZIP Hard; no substitueix l'agent Standard de l'arrel."""

import json
from pathlib import Path

from experiments.oriol_hard_mode.policies import HardAgent


class BatteryAgent:
    def __init__(self,forecast_provider=None,policy=None):
        folder=Path(__file__).resolve().parent
        configuration=json.loads((folder/'candidate_config.json').read_text(encoding='utf-8'))['configuration']
        training=json.loads((folder/'training.json').read_text(encoding='utf-8'))
        self.controller=HardAgent(training,configuration,forecast_provider,policy)

    @property
    def policy_failures(self):
        return self.controller.failures

    def act(self,obs:dict)->float:
        return self.controller.act(obs)
