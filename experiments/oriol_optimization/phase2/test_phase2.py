"""Proves de forecast causal, salts, horitzó i formulació dels nous controls."""

import copy
import math
import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))

import numpy as np

from experiments.oriol_optimization.phase2.model import AdvancedMPC, ForecastAdapter, soft_terminal_plan
from experiments.oriol_optimization.phase2.bench import data_and_training, offline_bound, read

TRAINING={"weighted":{"mean_price":.1,"mean_carbon":.1},
          "unweighted":{"mean_price":.1,"mean_carbon":.1},
          "mean_net":1000,"profile":[[1000.0]*24 for _ in range(7)]}


def obs(soc=1000,n=24,ts="2026-01-01 00:00:00"):
    return {"timestamp":ts,"soc_kwh":soc,"preu_actual":.09,"co2_actual":.09,
            "preus_properes_24h":[.09]+[.1]*(n-1),"co2_properes_24h":[.09]+[.1]*(n-1),
            "noves_dades_5min":{"ultim_consum_kw":100.0,"ultima_solar_kw":0.0}}


class Phase2Tests(unittest.TestCase):
    def test_persistence_ignores_stale_telemetry_after_gap(self):
        adapter=ForecastAdapter(TRAINING["profile"],"persistence")
        np.testing.assert_equal(adapter.predict(obs(),3),[1000]*3)
        np.testing.assert_equal(adapter.predict(obs(ts="2026-01-01 01:00:00"),3),[100]*3)
        np.testing.assert_equal(adapter.predict(obs(ts="2026-02-01 01:00:00"),3),[1000]*3)

    def test_external_forecast_adapter_rejects_bad_values(self):
        for callback in [lambda obs,horizon:[float("nan")]*horizon,lambda obs,horizon:[1.0]]:
            adapter=ForecastAdapter(TRAINING["profile"],callback=callback)
            np.testing.assert_equal(adapter.predict(obs(),3),[1000]*3)
            self.assertEqual(adapter.failures,1)

    def test_causal_models_ignore_unobserved_future_fields(self):
        protocol=read(Path(__file__).with_name("protocol.json"))
        for config in protocol["models"]:
            if config["forecast"]=="perfect": continue
            first,second=AdvancedMPC(config,TRAINING),AdvancedMPC(config,TRAINING)
            one,two=obs(),obs()
            two["future_load_kw"]=[0]*24
            two["private_score_normalizers"]={"price":1000,"carbon":1000}
            self.assertEqual(first.act(one),second.act(two))

    def test_short_planning_horizon_does_not_assume_episode_end(self):
        config={"forecast":"constant","terminal":"fixed","horizon":6,"normalization":"weighted"}
        nonterminal=AdvancedMPC(config,TRAINING).act(obs(0,20))
        terminal=AdvancedMPC(config,TRAINING).act(obs(0,5))
        self.assertGreater(nonterminal,400)
        self.assertAlmostEqual(terminal,0.0,places=5)

    def test_online_normalization_uses_previous_price_with_previous_load(self):
        config={"forecast":"constant","terminal":"fixed","horizon":24,"normalization":"online"}
        policy=AdvancedMPC(config,copy.deepcopy(TRAINING))
        first=obs(); first["preu_actual"]=.2; first["co2_actual"]=.15
        policy.act(first)
        initial=policy.energy
        second=obs(ts="2026-01-01 01:00:00"); second["preu_actual"]=5
        policy.act(second)
        self.assertEqual(policy.energy,initial+100)
        self.assertAlmostEqual(policy.parameters["mean_price"],(initial*.1+100*.2)/(initial+100))
        before=policy.energy
        policy.act(obs(ts="2026-02-01 01:00:00"))
        self.assertEqual(policy.energy,before)

    def test_all_deployable_models_are_finite_at_extreme_soc(self):
        protocol=read(Path(__file__).with_name("protocol.json"))
        for config in protocol["models"]:
            if config["forecast"]=="perfect":continue
            for soc in [0.0,1e-9,1000.0,2000-1e-9,2000.0]:
                policy=AdvancedMPC(config,TRAINING)
                action=policy.act(obs(soc))
                self.assertTrue(math.isfinite(action))
                self.assertLessEqual(abs(action),500)
                next_soc=soc+(action*np.sqrt(.9) if action>=0 else action/np.sqrt(.9))
                self.assertGreaterEqual(next_soc,0)
                self.assertLessEqual(next_soc,2000)
                self.assertEqual(policy.failures,0)

    def test_soft_terminal_retains_partial_reserve_without_fake_cycles(self):
        action=soft_terminal_plan(np.array([1.0,1.01]),1000,np.array([500,500]))
        self.assertTrue(math.isfinite(action))
        self.assertLessEqual(abs(action),500)

    def test_offline_reference_has_feasible_physics_and_small_dual_gap(self):
        result=offline_bound("calibration")
        self.assertLess(result["soc_balance_max_residual_kwh"],1e-6)
        self.assertLess(result["max_simultaneous_power_kw"],1e-6)
        self.assertLess(result["primal_dual_gap"],1e-4)
        self.assertGreaterEqual(result["grid_constraint_min_slack_kw"],-1e-6)
        self.assertGreaterEqual(result["numerical_upper_bound_score"],result["score_precise"])


if __name__=="__main__":
    unittest.main()
