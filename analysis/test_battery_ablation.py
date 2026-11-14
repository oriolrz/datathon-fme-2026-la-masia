"""Proves diagnòstiques; aquests fixtures no són mètriques oficials."""

from datetime import datetime, timedelta
import math
import unittest

import numpy as np
import pandas as pd

from forecast_battery_ablation import (
    DiagnosticThresholdPolicy, ForecastSource, ReferenceAgent, VARIANTS,
    chronological_lengths, safe_observation,
)


def obs(values=(1, 1, 3), soc=1000, ts=datetime(2026, 3, 1)):
    return {"timestamp": ts, "hour": ts.hour, "day_of_week": ts.weekday(), "soc_kwh": soc,
            "preus_properes_24h": list(values), "co2_properes_24h": [v / 10 for v in values],
            "noves_dades_5min": {"ultim_consum_kw": 1400, "ultima_solar_kw": 100}}


class BatteryAblationTests(unittest.TestCase):
    def test_reference_ignores_current_and_forecast_labels(self):
        left = obs()
        right = dict(left, load_kw=1e100, pv_kw=-1e100, forecast_net_load=[1e100] * 24,
                     noves_dades_5min={"ultim_consum_kw": 1e100, "ultima_solar_kw": 0})
        self.assertEqual(ReferenceAgent().act(left), ReferenceAgent().act(right))

    def test_no_forecast_is_exactly_the_reference(self):
        for soc in (0, .001, 1, 1000, 1999, 1999.999, 2000):
            for values in ((1,), (1, 3), (1, 1, 3), (3, 1, 1), (1, 1, 1), tuple(range(1, 25))):
                current = obs(values, soc)
                self.assertEqual(DiagnosticThresholdPolicy().act(current), ReferenceAgent().act(current))

    def test_future_forecast_entries_really_change_decision(self):
        policy = DiagnosticThresholdPolicy()
        current = obs()
        self.assertGreater(policy.act(current, [1000, 1000, 1000]), 0)
        # Mateixa predicció de t: canvien només els futurs.
        self.assertEqual(policy.act(current, [1000, 1, 1]), 0)

    def test_current_forecast_limits_discharge(self):
        policy = DiagnosticThresholdPolicy()
        current = obs((3, 1, 1))
        self.assertEqual(policy.act(current), -500)
        self.assertEqual(policy.act(current, [10, 1000, 1000]), -10)
        self.assertTrue(policy.cap_bound)

    def test_flat_forecast_is_neutral_above_power_limit(self):
        policy = DiagnosticThresholdPolicy()
        for values in ((1, 1, 3), (3, 1, 1), (1, 1, 1)):
            self.assertEqual(policy.act(obs(values)), policy.act(obs(values), [1000] * 3))

    def test_only_contiguous_timestamps_are_admitted(self):
        times = pd.date_range("2026-03-01", periods=3, freq="1h").append(
            pd.date_range("2026-04-01", periods=3, freq="1h"))
        np.testing.assert_array_equal(chronological_lengths(times), [3, 2, 1, 3, 2, 1])
        for t, length in enumerate(chronological_lengths(times)):
            for h in range(length):
                self.assertEqual(times[t + h], times[t] + pd.Timedelta(hours=h))

    def test_safe_view_truncates_and_removes_first_label_without_mutating_obs(self):
        current = obs(tuple(range(1, 25)))
        safe = safe_observation(current, 2, first=True)
        self.assertEqual(len(safe["preus_properes_24h"]), 2)
        self.assertEqual(len(safe["co2_properes_24h"]), 2)
        self.assertEqual(safe["noves_dades_5min"], {})
        self.assertEqual(len(current["preus_properes_24h"]), 24)
        self.assertEqual(current["noves_dades_5min"]["ultim_consum_kw"], 1400)

    def test_d_is_a_at_t_and_c_in_all_future_positions(self):
        a, c, d = ForecastSource("A"), ForecastSource("C"), ForecastSource("D")
        for h in range(5):
            current = obs(ts=datetime(2026, 3, 1) + timedelta(hours=h))
            pa, pc, pd_ = a.predict(current), c.predict(current), d.predict(current)
            self.assertEqual(pd_, [pa[0]] + pc[1:])

    def test_first_realization_cannot_decide_first_action(self):
        for variant in VARIANTS:
            current = obs()
            poisoned = dict(current, noves_dades_5min={"ultim_consum_kw": 1e100, "ultima_solar_kw": 0})
            a = DiagnosticThresholdPolicy().act(current, ForecastSource(variant).predict(current))
            b = DiagnosticThresholdPolicy().act(poisoned, ForecastSource(variant).predict(poisoned))
            self.assertEqual(a, b)

    def test_forecast_actions_respect_soc_physics(self):
        policy = DiagnosticThresholdPolicy()
        eta = math.sqrt(.9)
        for soc in (0, .001, 1, 1000, 1999, 1999.999, 2000):
            for values in ((1, 1, 3), (3, 1, 1)):
                for prediction in ([0, 0, 0], [10, 1000, 1000], [1000, 1000, 1000]):
                    action = policy.act(obs(values, soc), prediction)
                    self.assertTrue(math.isfinite(action))
                    self.assertLessEqual(abs(action), 500)
                    next_soc = soc + action * eta if action >= 0 else soc + action / eta
                    self.assertGreaterEqual(next_soc, -1e-10)
                    self.assertLessEqual(next_soc, 2000 + 1e-10)

    def test_short_forecasts_are_rejected_and_short_exogenous_horizons_rest(self):
        with self.assertRaises(AssertionError):
            DiagnosticThresholdPolicy().act(obs(), [1000])
        self.assertEqual(DiagnosticThresholdPolicy().act(obs((1, 3)), [1000, 1000]), 0)


if __name__ == "__main__":
    unittest.main()
