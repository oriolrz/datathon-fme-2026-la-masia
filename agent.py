"""Punt d'entrada de La MasIA per al simulador oficial UPC Sostenible."""

from math import isfinite

from src.fallback import choose_action as fallback_action
from src.safety import clamp_action, valid_soc


class BatteryAgent:
    """Reserva estable per defecte; política opcional amb el contracte del Dani.

    Per comparar una candidata: BatteryAgent(policy=choose_action).
    La integració definitiva del nou mòdul requereix validar-lo i empaquetar-lo.
    """

    def __init__(self, policy=None):
        if policy is not None and not callable(policy):
            raise TypeError("policy ha de ser callable o None")
        self.policy = policy
        self.policy_failures = 0

    def act(self, obs: dict) -> float:
        if not isinstance(obs, dict):
            return 0.0
        # Guardar el SOC real abans de cridar una política externa.
        soc = obs.get("soc_kwh")
        if not valid_soc(soc):
            return 0.0

        if self.policy is None:
            desired = fallback_action(obs)
        else:
            try:
                desired = float(self.policy(obs, load_forecast=None))
                if not isfinite(desired):
                    raise ValueError("La política ha retornat una consigna no finita")
            except Exception:
                # Només es recuperen errors de la candidata; el comptador els exposa.
                self.policy_failures += 1
                desired = fallback_action(obs)
        return clamp_action(desired, soc)
