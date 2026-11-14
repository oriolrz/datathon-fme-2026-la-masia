"""Proves matemàtiques, de causalitat i de física de les candidates."""

import math
import random
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(HERE))

import numpy as np
import pandas as pd

from policies import MPCPolicy, MarginalPolicy, ReservePolicy, solve_plan
from scripts.evaluate import load_module

PARAMETERS = {"mean_carbon": 0.09, "mean_price": 0.15}


def observation(soc=1000.0, n=24):
    return {"soc_kwh": soc, "timestamp": "2026-01-01 00:00:00",
            "preus_properes_24h": [.04] + [.18] * (n - 1),
            "co2_properes_24h": [.04] + [.18] * (n - 1)}


class FormulationTests(unittest.TestCase):
    def test_profitable_cycle_accounts_for_round_trip_loss(self):
        actions, _ = solve_plan(np.array([1.0, 2.0]), 0, [500, 500])
        np.testing.assert_allclose(actions, [500.0, -450.0], atol=1e-5)

    def test_unprofitable_cycle_is_not_executed(self):
        actions, _ = solve_plan(np.array([1.0, 1.05]), 0, [500, 500])
        np.testing.assert_allclose(actions, [0.0, 0.0], atol=1e-5)

    def test_pv_surplus_can_be_stored_without_export_payment(self):
        actions, result = solve_plan(np.array([1.0, 2.0]), 0, [-500, 500])
        np.testing.assert_allclose(actions, [500.0, -450.0], atol=1e-5)
        np.testing.assert_allclose(result.x[-2:], [0.0, 50.0], atol=1e-5)

    def test_terminal_energy_has_an_opportunity_value(self):
        no_value, _ = solve_plan(np.array([1.0]), 1000, [500], terminal_value=0)
        with_value, _ = solve_plan(np.array([1.0]), 1000, [500], terminal_value=2)
        self.assertLess(no_value[0], 0)
        self.assertGreater(with_value[0], 0)

    def test_score_objective_normalizes_by_energy_weighted_bases(self):
        grid_base = np.array([1000, 600, 900], dtype=float)
        grid_agent = np.array([1200, 500, 650], dtype=float)
        carbon = np.array([.05, .15, .20])
        price = np.array([.10, .20, .30])
        co2_base, cost_base, energy = grid_base @ carbon, grid_base @ price, grid_base.sum()
        values = .7 * carbon / (co2_base / energy) + .3 * price / (cost_base / energy)
        direct = 100 * (.7 * (1 - grid_agent @ carbon / co2_base) + .3 * (1 - grid_agent @ price / cost_base))
        marginal = 100 / energy * ((grid_base - grid_agent) @ values)
        self.assertAlmostEqual(direct, marginal, places=12)


class RobustnessTests(unittest.TestCase):
    def test_finite_safe_actions_at_soc_extremes_and_short_horizons(self):
        rng = random.Random(20261114)
        for cls in [MarginalPolicy, ReservePolicy, MPCPolicy]:
            policy = cls(PARAMETERS)
            for i in range(120):
                soc = [0, 2000, 1e-10, 2000 - 1e-10][i % 4] if i < 24 else rng.uniform(0, 2000)
                obs = observation(soc, i % 24 + 1)
                obs["preus_properes_24h"] = [rng.uniform(.01, .4) for _ in obs["preus_properes_24h"]]
                obs["co2_properes_24h"] = [rng.uniform(.02, .23) for _ in obs["co2_properes_24h"]]
                action = policy.act(obs)
                self.assertIsInstance(action, float)
                self.assertTrue(math.isfinite(action))
                self.assertLessEqual(abs(action), 500)
                next_soc = soc + (action * math.sqrt(.9) if action >= 0 else action / math.sqrt(.9))
                self.assertGreaterEqual(next_soc, 0)
                self.assertLessEqual(next_soc, 2000)
            self.assertEqual(policy.failures, 0)

    def test_candidates_do_not_read_future_or_stale_demand(self):
        for cls in [MarginalPolicy, ReservePolicy, MPCPolicy]:
            policy = cls(PARAMETERS)
            obs = observation()
            first = policy.act(obs)
            obs["timestamp"] = "2026-05-01 00:00:00"
            obs["noves_dades_5min"] = {"ultim_consum_kw": -999999, "ultima_solar_kw": 999999}
            self.assertAlmostEqual(policy.act(obs), first)

    def test_official_environment_low_load_and_temporal_gap(self):
        official = ROOT.parent / "paquet_participants_datathon_upc"
        env_class = load_module(official / "starter_kit/environment.py", "optimization_test_env").CampusBatteryEnv
        dates = pd.date_range("2026-01-01", periods=120, freq="h").append(pd.date_range("2026-02-01", periods=120, freq="h"))
        phase = np.arange(240) % 24
        data = pd.DataFrame({"load_kw": 100 + phase * 25, "pv_kw": np.maximum(0, 250 - abs(phase - 12) * 50),
                             "precio_eur_per_kwh": .1 + .05 * np.cos(phase / 24 * 2 * np.pi),
                             "co2_kg_per_kwh": .1 + .06 * np.cos(phase / 24 * 2 * np.pi)}, index=pd.DatetimeIndex(dates, name="Fecha"))
        for cls in [MarginalPolicy, ReservePolicy, MPCPolicy]:
            env, policy = env_class(data), cls(PARAMETERS)
            obs = env.reset()
            while obs is not None:
                obs, _ = env.step(policy.act(obs))
            self.assertEqual(env.evaluate_results()["infraccions"], 0)
            self.assertEqual(policy.failures, 0)


if __name__ == "__main__":
    unittest.main()
