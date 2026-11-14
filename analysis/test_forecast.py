"""Proves de contracte/causalitat; els fixtures no són dades de validació."""

import ast
from datetime import datetime, timedelta
import math
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src import forecast


PARAMETERS = {
    "weekly": tuple(tuple(1000.0 + 100 * d + h for h in range(24)) for d in range(7)),
    "global": 1200.0, "residual_clip": 500.0, "train_hours": 100,
}
START = datetime(2026, 3, 2, 0)  # Dilluns


def observation(ts=START, load=1300.0, solar=0.0):
    return {
        "timestamp": ts, "hour": ts.hour, "day_of_week": ts.weekday(),
        "noves_dades_5min": {"ultim_consum_kw": load, "ultima_solar_kw": solar},
    }


class ForecastContractTests(unittest.TestCase):
    def model(self, method="C"):
        return forecast.NetLoadForecaster(method, PARAMETERS)

    def test_alignment_includes_current_and_crosses_midnight(self):
        ts = datetime(2026, 3, 8, 23)  # Diumenge; següent hora dilluns
        pred = self.model("B").forecast(observation(ts), 24)
        self.assertEqual(pred[0], 1623.0)
        self.assertEqual(pred[1], 1000.0)
        self.assertEqual(pred[5], 1004.0)
        self.assertEqual(pred[23], 1022.0)

    def test_first_observation_does_not_reveal_current_target(self):
        for method in ("A", "B", "C"):
            with self.subTest(method=method):
                normal = self.model(method).forecast(observation(load=1), 24)
                poisoned = self.model(method).forecast(observation(load=1e100, solar=1e99), 24)
                self.assertEqual(normal, poisoned)

    def test_persistence_uses_only_previous_real_telemetry(self):
        model = self.model("A")
        self.assertEqual(model.forecast(observation(load=9999), 6), [1200.0] * 6)
        pred = model.forecast(observation(START + timedelta(hours=1), load=1400, solar=100), 24)
        self.assertEqual(pred, [1300.0] * 24)

    def test_correction_uses_source_calendar_and_decays(self):
        model = self.model("C")
        model.forecast(observation(), 24)
        values = model.forecast(observation(START + timedelta(hours=1), load=1300), 24)
        expected = 1001 + 300 * 2 ** (-1 / 6)
        self.assertAlmostEqual(values[0], expected)
        self.assertAlmostEqual(values[23], 1100 + 300 * 2 ** (-24 / 6))

    def test_recent_median_resists_a_single_large_residual(self):
        model = self.model("C")
        model.forecast(observation(), 24)
        for h, residual in ((1, 10), (2, 10), (3, 1e9)):
            values = model.forecast(observation(START + timedelta(hours=h), load=1000 + h - 1 + residual), 24)
        self.assertAlmostEqual(values[0], 1003 + 10 * 2 ** (-1 / 6))

    def test_gap_discards_correction_and_persistence_remains_explicitly_stale(self):
        a, c, b = self.model("A"), self.model("C"), self.model("B")
        for model in (a, b, c):
            model.forecast(observation(), 24)
            model.forecast(observation(START + timedelta(hours=1), load=1400), 24)
        obs = observation(START + timedelta(days=8), load=1800, solar=50)
        self.assertEqual(c.forecast(obs), b.forecast(obs))
        self.assertEqual(a.forecast(obs), [1750.0] * 24)

    def test_same_timestamp_is_idempotent_even_if_payload_changes(self):
        model = self.model()
        model.forecast(observation(), 24)
        ts = START + timedelta(hours=1)
        first = model.forecast(observation(ts, load=1350), 6)
        repeated = model.forecast(observation(ts, load=9999), 24)
        self.assertEqual(first, repeated[:6])

    def test_reset_and_backward_time_start_a_new_episode(self):
        model = self.model()
        model.forecast(observation(), 24)
        model.forecast(observation(START + timedelta(hours=1), load=1500), 24)
        self.assertEqual(model.forecast(observation()), self.model().forecast(observation()))
        model.forecast(observation(START + timedelta(hours=1), load=1500), 24)
        model.reset()
        self.assertEqual(model.forecast(observation()), self.model().forecast(observation()))

    def test_missing_and_nonfinite_telemetry_never_becomes_zero(self):
        for invalid in (None, {}, {"ultim_consum_kw": None, "ultima_solar_kw": 0},
                        {"ultim_consum_kw": float("nan"), "ultima_solar_kw": 0},
                        {"ultim_consum_kw": 1200, "ultima_solar_kw": float("inf")},
                        {"ultim_consum_kw": -2, "ultima_solar_kw": 0}):
            model = self.model("A")
            model.forecast(observation())
            model.forecast(observation(START + timedelta(hours=1), load=1400, solar=100))
            obs = observation(START + timedelta(hours=2))
            obs["noves_dades_5min"] = invalid
            self.assertEqual(model.forecast(obs), [1300.0] * 24)

    def test_missing_timestamp_breaks_attribution_and_uses_calendar_fallback(self):
        model = self.model()
        model.forecast(observation())
        model.forecast(observation(START + timedelta(hours=1), load=1400))
        self.assertEqual(model.forecast({"hour": 23, "day_of_week": 6}, 1), [1623.0])
        obs = observation(START + timedelta(hours=3), load=9999)
        self.assertEqual(model.forecast(obs), self.model().forecast(obs))

    def test_invalid_observations_and_lengths_are_finite(self):
        for method in ("A", "B", "C"):
            for obs in (None, {}, {"timestamp": "bad"}, {"timestamp": None},
                        {"timestamp": START.isoformat()}, observation(load=1e308, solar=0)):
                for horizon in (0, 1, 6, 24, 48):
                    result = self.model(method).forecast(obs, horizon)
                    self.assertEqual(len(result), horizon)
                    self.assertTrue(all(isinstance(v, float) and math.isfinite(v) for v in result))

    def test_invalid_horizons_are_rejected(self):
        for horizon in (-1, 1.2, True, "24", None):
            with self.assertRaises(ValueError):
                self.model().forecast(observation(), horizon)

    def test_future_and_unobservable_fields_are_ignored(self):
        left, right = self.model(), self.model()
        left.forecast(observation())
        right.forecast(observation())
        obs = observation(START + timedelta(hours=1))
        changed = dict(obs, preus_properes_24h=[1e100] * 24, co2_properes_24h=[-1e100],
                       meteorologia_futura=[1e100], load_kw=1e100, pv_kw=1e100, soc_kwh=0)
        self.assertEqual(left.forecast(obs), right.forecast(changed))

    def test_interleaved_agents_keep_independent_histories(self):
        left, right = self.model("A"), self.model("A")
        left.forecast(observation())
        right.forecast(observation())
        ts = START + timedelta(hours=1)
        self.assertEqual(left.forecast(observation(ts, load=1100), 1), [1100.0])
        self.assertEqual(right.forecast(observation(ts, load=1700), 1), [1700.0])

    def test_aware_time_uses_elapsed_hours_through_dst(self):
        ts = datetime(2026, 3, 29, 1, tzinfo=ZoneInfo("Europe/Madrid"))
        pred = self.model("B").forecast(observation(ts), 2)
        self.assertEqual(pred, [1601.0, 1603.0])

    def test_embedded_profile_and_facade_need_no_files(self):
        self.assertEqual(forecast.TRAINED_PARAMETERS["train_hours"], 2784)
        self.assertEqual(forecast.TRAINED_PARAMETERS["train_end_exclusive"], "2026-03-01")
        forecast.reset_forecast()
        independent = forecast.NetLoadForecaster()
        # Imports ja resolts; qualsevol intent de llegir CSV/model falla.
        with patch("builtins.open", side_effect=AssertionError("Inferència amb E/S")):
            for h in range(4):
                obs = observation(START + timedelta(hours=h), load=1300 + h)
                self.assertEqual(forecast.forecast_net_load(obs, 24), independent.forecast(obs, 24))
        forecast.reset_forecast()
        self.assertEqual(forecast.forecast_net_load(observation()), forecast.NetLoadForecaster().forecast(observation()))

    def test_source_has_no_data_loading_or_training_calls(self):
        tree = ast.parse((ROOT / "src/forecast.py").read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                name = node.func.id if isinstance(node.func, ast.Name) else getattr(node.func, "attr", "")
                self.assertNotIn(name, {"open", "read_csv", "read_bytes", "load", "fit", "read_text"})


if __name__ == "__main__":
    unittest.main()
