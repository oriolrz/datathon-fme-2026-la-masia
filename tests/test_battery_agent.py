"""Proves de física, robustesa, contracte i execució amb el simulador oficial."""

import copy
import importlib.util
import math
import os
import random
import time
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from agent import BatteryAgent
from src.safety import EPSILON_KW, ETA, clamp_action, power_bounds

ROOT = Path(__file__).resolve().parents[1]
OFFICIAL = Path(os.environ.get("UPC_OFFICIAL_ROOT", str(ROOT.parent / "paquet_participants_datathon_upc")))


def observation(soc=1000.0, length=24):
    return {
        "timestamp": "2026-01-15 12:00:00", "hour": 12, "day_of_week": 3,
        "soc_kwh": soc, "soc_pct": soc / 2000, "soc_percent": soc / 20,
        "preu_actual": 0.03, "co2_actual": 0.03,
        "preus_properes_24h": ([0.03] + [0.20] * 23)[:length],
        "co2_properes_24h": ([0.03] + [0.20] * 23)[:length],
        "noves_dades_5min": {"ultim_consum_kw": 1000.0, "ultima_solar_kw": 0.0},
    }


def assert_physics(test, action, soc):
    test.assertIsInstance(action, float)
    test.assertTrue(math.isfinite(action))
    test.assertLessEqual(abs(action), 500.0)
    # Càlcul independent dels límits i la dinàmica, sense usar power_bounds.
    eta = math.sqrt(0.9)
    next_soc = soc + (action * eta if action >= 0 else action / eta)
    test.assertGreaterEqual(next_soc, 0.0)
    test.assertLessEqual(next_soc, 2000.0)
    if action > 0:
        test.assertLessEqual(action, (2000.0 - soc) / eta)
    if action < 0:
        test.assertLessEqual(-action, soc * eta)


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class SafetyTests(unittest.TestCase):
    def test_exact_efficiency_and_epsilon(self):
        self.assertEqual(ETA, math.sqrt(0.9))
        self.assertEqual(power_bounds(100.0)[0], -(100 * math.sqrt(0.9) - EPSILON_KW))
        self.assertEqual(power_bounds(1900.0)[1], 100 / math.sqrt(0.9) - EPSILON_KW)
        self.assertEqual(power_bounds(1000), (-500.0, 500.0))

    def test_soc_extremes_and_floating_point_neighbours(self):
        socs = [0.0, math.nextafter(0.0, 1.0), 1e-9, 1e-4, 100.0,
                1000.0, 1900.0, 2000 - 1e-9, math.nextafter(2000.0, 0.0), 2000.0]
        for soc in socs:
            for request in [-1e300, -501, -500, -1, 0, 1, 500, 501, 1e300]:
                with self.subTest(soc=soc, request=request):
                    assert_physics(self, clamp_action(request, soc), soc)
        self.assertEqual(clamp_action(-500, 0), 0)
        self.assertEqual(clamp_action(500, 2000), 0)

    def test_invalid_soc_and_actions_standby(self):
        for soc in [None, "bad", float("nan"), float("inf"), -1, 2001]:
            self.assertEqual(clamp_action(500, soc), 0.0)
        for action in [None, "bad", float("nan"), float("inf"), -float("inf")]:
            self.assertEqual(clamp_action(action, 1000), 0.0)


class AgentTests(unittest.TestCase):
    def test_randomized_10009_states_match_prototype_and_physics(self):
        prototype = load_module(ROOT / "prototypes/upc/agent_v0_24h.py", "prototype_test").BatteryAgent()
        agent = BatteryAgent()
        rng = random.Random(20261114)
        for index in range(10009):
            soc = rng.choice([0.0, 2000.0]) if index < 9 else rng.uniform(0, 2000)
            obs = observation(soc, rng.randint(1, 24))
            obs["preus_properes_24h"] = [rng.uniform(.003, .40) for _ in obs["preus_properes_24h"]]
            obs["co2_properes_24h"] = [rng.uniform(.02, .23) for _ in obs["co2_properes_24h"]]
            actual = agent.act(obs)
            assert_physics(self, actual, soc)
            self.assertEqual(actual, prototype.act(obs))

    def test_incomplete_or_malformed_forecasts_are_finite(self):
        agent = BatteryAgent()
        for length in range(25):
            assert_physics(self, agent.act(observation(length=length)), 1000.0)
        for value in [None, "bad", {}, [float("nan")] * 24, [float("inf")] * 24,
                      [None] * 24, [0.0] * 24, [1e308] * 24]:
            for field in ("preus_properes_24h", "co2_properes_24h"):
                obs = observation()
                obs[field] = value
                self.assertEqual(agent.act(obs), 0.0)
        obs = observation()
        obs["co2_properes_24h"] = obs["co2_properes_24h"][:3]
        assert_physics(self, agent.act(obs), 1000.0)
        for obs in [{}, None, {"soc_kwh": float("nan")}, {"soc_kwh": -1}]:
            self.assertEqual(agent.act(obs), 0.0)

    def test_gap_does_not_use_stale_telemetry_or_mutate_observation(self):
        agent = BatteryAgent()
        obs = observation()
        before = copy.deepcopy(obs)
        expected = agent.act(obs)
        self.assertEqual(obs, before)
        obs["timestamp"] = "2026-03-01 12:00:00"
        obs["noves_dades_5min"] = {"ultim_consum_kw": -1e9, "ultima_solar_kw": 1e9}
        self.assertEqual(agent.act(obs), expected)
        obs["timestamp"] = pd.Timestamp("2026-06-01 12:00:00")
        self.assertEqual(agent.act(obs), expected)

    def test_candidate_contract_clamped_and_failures_visible(self):
        calls = []

        def candidate(obs, load_forecast=None):
            calls.append(load_forecast)
            return -1e9

        agent = BatteryAgent(policy=candidate)
        assert_physics(self, agent.act(observation(100)), 100)
        self.assertEqual(calls, [None])
        self.assertEqual(agent.policy_failures, 0)

        def broken(obs, load_forecast=None):
            raise RuntimeError("Error sintètic de candidata")

        for policy in [broken, lambda obs, load_forecast=None: float("nan"),
                       lambda obs, load_forecast=None: float("inf"),
                       lambda obs, load_forecast=None: None]:
            agent = BatteryAgent(policy=policy)
            self.assertEqual(agent.act(observation()), BatteryAgent().act(observation()))
            self.assertEqual(agent.policy_failures, 1)


class OfficialEnvironmentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Fallar, no saltar silenciosament, si manca el kit necessari per validar.
        cls.env_class = load_module(OFFICIAL / "starter_kit/environment.py", "official_env_test").CampusBatteryEnv

    def test_extreme_requests_no_clipping_in_official_engine(self):
        data = pd.DataFrame({
            "load_kw": [1000.0], "pv_kw": [0.0],
            "precio_eur_per_kwh": [.1], "co2_kg_per_kwh": [.1],
        }, index=pd.DatetimeIndex(["2026-01-01"], name="Fecha"))
        env = self.env_class(data)
        for soc in [0.0, 1e-10, 100, 1000, 1900, 2000 - 1e-10, 2000.0]:
            for request in [-1e9, -500, 0, 500, 1e9]:
                env.reset()
                env.soc = soc
                env.step(clamp_action(request, soc))
                self.assertEqual(env.clipped + env.violations, 0)

    def test_complete_2016_step_simulation_under_timeout(self):
        n = 2016
        hour = np.arange(n) % 24
        data = pd.DataFrame({
            "load_kw": 700.0 + 500.0 * np.sin(hour / 24 * 2 * np.pi),
            "pv_kw": np.maximum(0, 120 * np.sin((hour - 6) / 12 * np.pi)),
            "precio_eur_per_kwh": .12 + .09 * np.cos(hour / 24 * 2 * np.pi),
            "co2_kg_per_kwh": .12 + .08 * np.cos(hour / 24 * 2 * np.pi),
        }, index=pd.date_range("2026-01-01", periods=n, freq="1h", name="Fecha"))
        before = time.perf_counter()
        agent = BatteryAgent()
        env = self.env_class(data)
        obs = env.reset()
        while obs is not None:
            obs, _ = env.step(agent.act(obs))
        metrics = env.evaluate_results()
        self.assertEqual(env.t, n)
        self.assertEqual(metrics["infraccions"], 0)
        self.assertTrue(all(math.isfinite(v) for v in metrics.values()))
        self.assertLess(time.perf_counter() - before, 60.0)


if __name__ == "__main__":
    unittest.main()
