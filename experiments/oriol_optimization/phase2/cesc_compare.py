"""Adaptador independent del forecast C del Cesc, fixat a un commit concret.

No escriu src/forecast.py ni modifica les comparacions ja congelades.
"""

import argparse
import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from time import perf_counter

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
sys.path.insert(0,str(ROOT))
from experiments.oriol_optimization.phase2.bench import OUT,OFFICIAL,data_and_training,raw_score,write

SOURCE_COMMIT="acc09c06b30d9dcf78f38c88e9c554b2c2f8f57c"


def load_cesc():
    source=subprocess.check_output(["git","show",f"{SOURCE_COMMIT}:src/forecast.py"],cwd=ROOT)
    path=OUT/f"cesc_forecast_{SOURCE_COMMIT[:8]}.py"
    path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists():
        if path.read_bytes()!=source: raise ValueError("Snapshot del forecast alterat")
    else:
        path.write_bytes(source)
    spec=importlib.util.spec_from_file_location("cesc_forecast_pinned",path)
    module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module,hashlib.sha256(source).hexdigest()


def training_checks(module):
    import numpy as np
    import pandas as pd
    data,_=data_and_training("calibration")
    target=data.load_kw-data.pv_kw
    profile=target.groupby([target.index.dayofweek,target.index.hour]).median()
    expected=np.asarray([[round(float(profile.loc[(d,h)]),6) for h in range(24)] for d in range(7)])
    params=module.TRAINED_PARAMETERS
    if params["train_hours"]!=len(data) or params["train_end_exclusive"]!="2026-03-01":
        raise ValueError("Entrenament de forecast fora del calibratge")
    np.testing.assert_allclose(expected,np.asarray(params["weekly"]),atol=1e-6,rtol=0)
    residual=np.asarray([target.iloc[i]-expected[t.weekday(),t.hour] for i,t in enumerate(data.index)])
    expected_clip=round(float(np.quantile(abs(residual),.95)),6)
    if abs(params["residual_clip"]-expected_clip)>1e-6: raise ValueError("Clip no reproduïble amb calibratge")
    # El hash del Cesc usa datetime64[us]; aquí pandas carrega datetime64[ns].
    # Canonitzar la resolució verifica els mateixos targets, no només agregats.
    canonical=target.copy()
    canonical.index=canonical.index.as_unit("us")
    canonical_hash=hashlib.sha256(pd.util.hash_pandas_object(canonical).values.tobytes()).hexdigest()
    if canonical_hash!=params["train_target_sha256"]: raise ValueError("Targets de calibratge diferents del model del Cesc")
    return {"training_hours":len(data),"training_end_exclusive":params["train_end_exclusive"],
            "profile_reproduced_from_calibration":True,"residual_clip_reproduced":True,
            "local_train_target_sha256":hashlib.sha256(pd.util.hash_pandas_object(target).values.tobytes()).hexdigest(),
            "canonical_microsecond_target_sha256":canonical_hash,
            "exact_calibration_targets_verified":True,
            "cesc_train_target_sha256":params["train_target_sha256"]}


class CescCallback:
    def __init__(self,module,mode):
        self.model=module.NetLoadForecaster(method="C")
        self.mode=mode

    def __call__(self,obs,horizon=24):
        import numpy as np
        forecast=np.asarray(self.model.forecast(obs,horizon),dtype=float)
        if self.mode=="first":
            forecast[1:]=500.0
        return forecast


def worker(mode,period):
    import numpy as np
    from scripts.evaluate import load_module
    from experiments.oriol_optimization.phase2.model import AdvancedMPC

    module,fingerprint=load_cesc()
    provenance=training_checks(module)
    data,training=data_and_training(period)
    env_class=load_module(OFFICIAL/"starter_kit/environment.py","cesc_mpc_environment") .CampusBatteryEnv
    env=env_class(data)
    config={"id":"cesc_"+mode,"forecast":"seasonal","terminal":"fixed","horizon":24,"normalization":"weighted"}
    policy=AdvancedMPC(config,training,CescCallback(module,mode))
    obs=env.reset(); error=0.0; waste=0.0
    before=perf_counter()
    while obs is not None:
        action=policy.act(obs)
        if not np.isfinite(action):raise ValueError("Acció no finita")
        net=float(data.load_kw.iloc[env.t]-data.pv_kw.iloc[env.t])
        error+=abs(policy.last_forecast[0]-net)
        waste+=max(0.0,-action-max(net,0.0))
        obs,_=env.step(action)
    row=env.evaluate_results()
    row.update({"id":"cesc_"+mode,"period":period,"steps":len(data),"score_precise":raw_score(data,np.asarray(env.grid)),
                "simulation_seconds":perf_counter()-before,"failures":policy.failures,
                "adapter_failures":policy.forecaster.failures,"forecast_mae_kw":error/len(data),
                "discharge_export_waste_kwh":waste,"soc_final_kwh":float(env.soc),
                "actions_sha256":hashlib.sha256(np.asarray(env.actions,dtype="<f8").tobytes()).hexdigest(),
                "source_commit":SOURCE_COMMIT,"forecast_source_sha256":fingerprint,"training_audit":provenance,
                "alignment":"Només t emparellat" if mode=="first" else "Assumeix hores consecutives; no verifica timestamps futurs",
                "monthly":{str(m):env.evaluate_results(mask=data.index.to_period("M")==m) for m in data.index.to_period("M").unique()}})
    print(json.dumps(row,allow_nan=False))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--worker",action="store_true"); parser.add_argument("--mode",choices=["first","24"])
    parser.add_argument("--period",default="calibration")
    args=parser.parse_args()
    if args.worker:
        worker(args.mode,args.period);return
    rows=[]
    for period in ["calibration","validation","confirmation"]:
        for mode in ["first","24"]:
            before=perf_counter()
            run=subprocess.run([sys.executable,"-B","-X","utf8",str(Path(__file__).resolve()),"--worker","--mode",mode,"--period",period],
                               cwd=ROOT,capture_output=True,text=True,encoding="utf-8",timeout=100)
            if run.returncode:raise RuntimeError(run.stdout+run.stderr)
            row=json.loads(run.stdout);row["process_seconds"]=perf_counter()-before
            if row["infraccions"] or row["failures"] or row["adapter_failures"]:raise RuntimeError("Candidata amb fallades")
            write(OUT/f"{period}_cesc_{mode}.json",row);rows.append(row)
            print(f"{period:13} cesc_{mode:5} score={row['score_precise']:.8f} MAE={row['forecast_mae_kw']:.2f} wall={row['process_seconds']:.2f}s",flush=True)
    write(OUT/"cesc_results.json",{"source_commit":SOURCE_COMMIT,"method":"C","tuned_parameters":False,"rows":rows})


if __name__=="__main__":main()
