"""Física Hard i control de la informació observable, sense canviar Standard."""

import math
import random
import sys
import unittest
import copy
import json
import tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))

import numpy as np
import pandas as pd

from experiments.oriol_hard_mode.safety import clamp_action,power_bounds
from experiments.oriol_hard_mode.lab import HARD_SPEC,hard_observation,official_env,scale_hard
from experiments.oriol_hard_mode.policies import HardAgent,NaiveHardMPC,solve_hard_plan,solve_scenarios
from experiments.oriol_hard_mode.forecast import Forecaster


def observation(soc=3000,n=3):
    return {"timestamp":"2026-01-01 00:00:00","soc_kwh":soc,"preus_properes_24h":[.05,.2,.15][:n],
            "co2_properes_24h":[.05,.2,.15][:n],"noves_dades_5min":{"ultim_consum_kw":1000,"ultima_solar_kw":0}}


class HardSafetyTests(unittest.TestCase):
    def test_extreme_soc_and_power(self):
        rng=random.Random(20261114)
        for soc in [0,1e-10,3000,6000-1e-10,6000]+[rng.uniform(0,6000) for _ in range(1000)]:
            for request in [-1e9,-1500,-123.4,0,123.4,1500,1e9]:
                action=clamp_action(request,observation(soc))
                self.assertTrue(math.isfinite(action));self.assertLessEqual(abs(action),1500)
                after=soc+(action*math.sqrt(.9) if action>=0 else action/math.sqrt(.9))
                self.assertGreaterEqual(after,0);self.assertLessEqual(after,6000)

    def test_invalid_inputs_and_explicit_dynamic_limits(self):
        for obs in [{},None,{"soc_kwh":float('nan')},{"soc_kwh":6001},{"soc_kwh":-1}]:
            self.assertEqual(clamp_action(1500,obs),0.0)
        for action in [None,'bad',float('inf'),float('nan')]:
            self.assertEqual(clamp_action(action,observation()),0.0)
        obs={**observation(1000),"cap_max_kwh":2000,"power_max_kw":500}
        self.assertEqual(power_bounds(obs),(-500,500))

    def test_zero_clipping_against_official_physics(self):
        frame=pd.DataFrame({"load_kw":[1000.0],"pv_kw":[0.0],"precio_eur_per_kwh":[.1],"co2_kg_per_kwh":[.1]},
                           index=pd.DatetimeIndex(['2026-01-01'],name='Fecha'))
        env=official_env()(frame,spec=HARD_SPEC)
        for soc in [0,1e-10,3000,6000-1e-10,6000]:
            for request in [-1e9,-1500,0,1500,1e9]:
                env.reset();env.soc=soc;env.step(clamp_action(request,observation(soc)))
                self.assertEqual(env.clipped+env.violations,0)

    def test_negative_net_and_free_solar_cycle(self):
        actions,result=solve_hard_plan(np.array([1.,2.]),0,np.array([-1500.,1500.]))
        np.testing.assert_allclose(actions,[1500,-1350],atol=1e-5)
        np.testing.assert_allclose(result.x[-2:],[0,150],atol=1e-5)


class HardContractTests(unittest.TestCase):
    def test_generated_json_has_canonical_lf_bytes(self):
        from experiments.oriol_hard_mode.lab import write as write_lab
        from experiments.oriol_hard_mode.deliver import write as write_delivery
        with tempfile.TemporaryDirectory(prefix='masia_hard_newline_') as folder:
            for writer in [write_lab,write_delivery]:
                path=Path(folder)/'sample.json'
                writer(path,{'missatge':'validació','score':1.23})
                content=path.read_bytes()
                self.assertNotIn(b'\r',content)
                self.assertTrue(content.endswith(b'\n'))
                self.assertEqual(json.loads(content),{'missatge':'validació','score':1.23})

    def test_solar_scaled_exactly_once(self):
        frame=pd.DataFrame({'pv_kw':[0.,100.]})
        hard=scale_hard(frame)
        np.testing.assert_array_equal(hard.pv_kw.to_numpy(),[0,1200]);np.testing.assert_array_equal(frame.pv_kw.to_numpy(),[0,100])
        with self.assertRaises(ValueError):scale_hard(hard)

    def test_raw_kit_discrepancy_and_adapter(self):
        frame=pd.DataFrame({'load_kw':[1000.]*24,'pv_kw':[0.]*24,'precio_eur_per_kwh':[.1]*24,'co2_kg_per_kwh':[.1]*24},
                           index=pd.date_range('2026-01-01',periods=24,freq='h',name='Fecha'))
        env=official_env()(frame,spec=HARD_SPEC);raw=env.reset();adapted=hard_observation(raw)
        self.assertEqual(len(raw['preus_properes_24h']),24)
        self.assertEqual(len(adapted['preus_properes_24h']),3)
        self.assertNotIn('irradiancia_wm2',adapted['noves_dades_5min'])
        self.assertNotIn('cap_max_kwh',raw)
        self.assertEqual(adapted['cap_max_kwh'],6000)

    def test_hidden_market_tail_is_never_used(self):
        training={'mean_price':.1,'mean_carbon':.1}
        left,right=observation(),observation()
        right['preus_properes_24h'] += [1e99]*21
        right['co2_properes_24h'] += [float('nan')]*21
        self.assertEqual(NaiveHardMPC(training).act(left),NaiveHardMPC(training).act(right))

    def test_short_and_missing_vectors_return_finite_actions(self):
        policy=NaiveHardMPC({'mean_price':.1,'mean_carbon':.1})
        for n in range(4):
            self.assertTrue(math.isfinite(policy.act(observation(n=n))))

    def test_soc_persists_at_temporal_gap(self):
        frame=pd.DataFrame({'load_kw':[1000.,1000.],'pv_kw':[0.,0.],'precio_eur_per_kwh':[.1,.1],'co2_kg_per_kwh':[.1,.1]},
                           index=pd.DatetimeIndex(['2026-01-01','2026-02-01'],name='Fecha'))
        env=official_env()(frame,spec=HARD_SPEC)
        obs,_=env.step(1000)
        self.assertAlmostEqual(obs['soc_kwh'],3000+1000*math.sqrt(.9))


class HardForecastAndIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        folder=Path(__file__).resolve().parent
        cls.training=json.loads((folder/'training.json').read_text(encoding='utf-8'))
        cls.configurations=json.loads((folder/'protocol.json').read_text(encoding='utf-8'))['models']
        cls.config=next(c for c in cls.configurations if c['id']=='mpc24_annual')

    def test_initial_and_gap_telemetry_are_ignored(self):
        for mode in ['profile','adaptive','annual']:
            left,right=Forecaster(self.training,mode),Forecaster(self.training,mode)
            for ts in ['2026-06-01 12:00:00','2026-06-01 13:00:00','2026-08-01 12:00:00']:
                a=observation();a['timestamp']=ts;b=copy.deepcopy(a)
                if '13:00' not in ts:
                    b['noves_dades_5min']={'ultim_consum_kw':1e9,'ultima_solar_kw':1e9}
                fa,fb=left.forecast(a),right.forecast(b)
                for key in ['load_kw','pv_kw','price','carbon']:
                    np.testing.assert_array_equal(fa[key],fb[key])

    def test_only_three_observable_market_values_influence_all_models(self):
        for config in self.configurations:
            if config['kind']=='naive':continue
            left,right=HardAgent(self.training,config),HardAgent(self.training,config)
            for hour in range(4):
                a=observation();a['timestamp']=f'2026-06-01 {hour:02}:00:00';b=copy.deepcopy(a)
                b['preus_properes_24h'] += [float('nan')]*21
                b['co2_properes_24h'] += [1e99]*21
                self.assertEqual(left.act(a),right.act(b))
                np.testing.assert_array_equal(left.last_forecasts['price'][:3],a['preus_properes_24h'])

    def test_lagged_pv_changes_forecast_without_rescaling(self):
        predictor=Forecaster(self.training,'adaptive')
        first=observation();first['timestamp']='2026-06-01 12:00:00'
        forecast=predictor.forecast(first)
        base=float(forecast['pv_kw'][0]);self.assertGreater(base,100)
        second=copy.deepcopy(first);second['timestamp']='2026-06-01 13:00:00'
        second['noves_dades_5min']['ultima_solar_kw']=base
        predictor.forecast(second)
        self.assertAlmostEqual(predictor.pv_ratio,1.0)

    def test_telemetry_is_causal_and_stays_finite(self):
        predictor=Forecaster(self.training,'annual')
        for hour in range(24):
            obs=observation();obs['timestamp']=f'2026-06-01 {hour:02}:00:00'
            obs['noves_dades_5min']={'ultim_consum_kw':float('nan'),'ultima_solar_kw':float('inf')}
            forecast=predictor.forecast(obs)
            for key in ['load_kw','pv_kw','price','carbon']:
                self.assertEqual(forecast[key].shape,(24,))
                self.assertTrue(np.isfinite(forecast[key]).all())
                self.assertTrue((forecast[key]>=0).all())

    def test_short_market_vectors_and_extreme_soc_all_families(self):
        for config in self.configurations:
            if config['kind']=='naive':continue
            for soc in [0,3000,6000]:
                for n in range(4):
                    policy=HardAgent(self.training,config);obs=observation(soc,n)
                    action=policy.act(obs);self.assertIsInstance(action,float)
                    self.assertTrue(math.isfinite(action))
                    lower,upper=power_bounds(obs)
                    self.assertLessEqual(action,upper);self.assertGreaterEqual(action,lower)
                    self.assertEqual(policy.failures,0)

    def test_external_forecast_and_policy_hooks_keep_final_clamp(self):
        def forecast(obs,horizon):return {'load_kw':np.full(horizon,500.),'pv_kw':np.zeros(horizon)}
        def policy(obs,forecasts):
            np.testing.assert_array_equal(forecasts['load_kw'],np.full(24,500.))
            return -1e9
        agent=HardAgent(self.training,self.config,forecast,policy)
        obs=observation(10)
        self.assertEqual(agent.act(obs),power_bounds(obs)[0]);self.assertEqual(agent.failures,0)

    def test_broken_external_modules_use_standalone_fallback(self):
        def broken(*args,**kwargs):raise RuntimeError('Error de prova del mòdul extern')
        agent=HardAgent(self.training,self.config,broken,broken)
        self.assertTrue(math.isfinite(agent.act(observation())))
        self.assertEqual(agent.failures,2)

    def test_scenario_shared_actions_are_feasible_in_each_branch(self):
        # Les primeres dues accions es decideixen abans de conèixer l'escenari.
        load=np.array([1000.,1200.,1500.,1000.]);pv=np.array([1400.,1000.,0.,0.])
        actions=solve_scenarios(np.array([.5,.7,1.5,1.]),3000,load,pv,6000,1500,2)
        self.assertTrue(np.isfinite(actions).all())
        for load_factor,pv_factor in [(1.10,.65),(1.,1.),(.90,1.35)]:
            soc=3000.
            for action in actions[:2]:
                soc+=action*math.sqrt(.9) if action>=0 else action/math.sqrt(.9)
                self.assertGreaterEqual(soc,0);self.assertLessEqual(soc,6000)

    def test_training_metadata_excludes_validation_and_confirmation(self):
        self.assertEqual(self.training['train_end_exclusive'],'2026-03-01')
        self.assertEqual(self.training['train_hours'],2784)


if __name__=='__main__':unittest.main()
