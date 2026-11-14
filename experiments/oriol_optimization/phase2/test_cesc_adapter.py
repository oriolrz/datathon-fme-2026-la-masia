"""Checks de l'adaptador independent i la procedència del model del Cesc."""

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))

from experiments.oriol_optimization.phase2.cesc_compare import CescCallback,load_cesc,training_checks


class CescAdapterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.module,_=load_cesc()

    def test_embedded_parameters_match_calibration_only(self):
        result=training_checks(self.module)
        self.assertTrue(result["profile_reproduced_from_calibration"])
        self.assertTrue(result["residual_clip_reproduced"])

    def test_first_call_ignores_current_telemetry_and_inference_has_no_io(self):
        left,right=CescCallback(self.module,"first"),CescCallback(self.module,"first")
        obs={"timestamp":"2026-03-01 00:00:00","noves_dades_5min":{"ultim_consum_kw":1,"ultima_solar_kw":0}}
        poison={**obs,"noves_dades_5min":{"ultim_consum_kw":1e100,"ultima_solar_kw":1e99}}
        with patch("builtins.open",side_effect=AssertionError("Inferència amb E/S")):
            self.assertEqual(left(obs,24).tolist(),right(poison,24).tolist())
        self.assertEqual(left(obs,24)[1:].tolist(),[500.0]*23)

    def test_gap_discards_old_residual_without_future_timestamps(self):
        used,fresh=CescCallback(self.module,"first"),CescCallback(self.module,"first")
        used({"timestamp":"2026-03-01 00:00:00"},24)
        used({"timestamp":"2026-03-01 01:00:00","noves_dades_5min":{"ultim_consum_kw":100,"ultima_solar_kw":0}},24)
        obs={"timestamp":"2026-04-01 01:00:00","noves_dades_5min":{"ultim_consum_kw":100,"ultima_solar_kw":0}}
        self.assertEqual(used(obs,24).tolist(),fresh(obs,24).tolist())


if __name__=="__main__":unittest.main()
