"""Motor físic oficial + adaptador EXPLÍCIT del contracte anunciat Hard.

El kit local ignora forecast_horizon i no emet meteorologia/caps. No es
modifica environment.py: només es limita la informació vista per l'agent.
"""

import argparse
import hashlib
import importlib.util
import json
import platform
import subprocess
import sys
from pathlib import Path
from time import perf_counter

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
OFFICIAL=ROOT.parent/"paquet_participants_datathon_upc"
OUT=ROOT/"artifacts/oriol_hard_mode"
sys.path.insert(0,str(ROOT))

HARD_SPEC={"capacity_kwh":6000.0,"power_kw":1500.0,"efficiency":.9,"soc_init":.5,
           "soc_min":0.0,"soc_max":1.0,"dt_hours":1.0,"forecast_horizon":3}


def read(path):return json.loads(Path(path).read_text(encoding="utf-8"))


def write(path,value):
    Path(path).parent.mkdir(parents=True,exist_ok=True)
    Path(path).write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+"\n",encoding="utf-8",newline="\n")


def official_env():
    spec=importlib.util.spec_from_file_location("official_hard_physics",OFFICIAL/"starter_kit/environment.py")
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module.CampusBatteryEnv


def scale_hard(frame):
    if frame.attrs.get("hard_pv_scale"):
        raise ValueError("La solar ja estava escalada")
    hard=frame.copy();hard["pv_kw"]=hard.pv_kw*12.0;hard.attrs["hard_pv_scale"]=12.0
    return hard


def load_hard(period="full"):
    from scripts.evaluate import load_hourly_data
    frame=scale_hard(load_hourly_data(OFFICIAL))
    if period=="calibration":return frame.loc[frame.index<"2026-03-01"]
    if period=="validation":return frame.loc[(frame.index>="2026-03-01")&(frame.index<"2026-06-01")]
    if period=="confirmation":return frame.loc[frame.index>="2026-06-01"]
    if period!="full":raise ValueError(period)
    return frame


def fit_training():
    import numpy as np
    frame=load_hard("calibration")
    grid=(frame.load_kw-frame.pv_kw).clip(lower=0)
    training={"mean_carbon":float((grid*frame.co2_kg_per_kwh).sum()/grid.sum()),
            "mean_price":float((grid*frame.precio_eur_per_kwh).sum()/grid.sum()),
            "train_hours":len(frame),"train_end_exclusive":"2026-03-01","pv_units":"Hard kW, ja escalats x12"}
    for name,column in [("load","load_kw"),("pv","pv_kw"),("price","precio_eur_per_kwh"),("carbon","co2_kg_per_kwh")]:
        grouped=frame[column].groupby([frame.index.dayofweek,frame.index.hour]).mean()
        training[name+"_profile"]=[[float(grouped.get((d,h),frame[column].mean())) for h in range(24)] for d in range(7)]
    residual=np.asarray([row.load_kw-training["load_profile"][ts.dayofweek][ts.hour] for ts,row in frame.iterrows()])
    training["load_residual_clip_kw"]=float(np.quantile(abs(residual),.95))
    training["max_pv_kw"]=float(frame.pv_kw.max())
    annual=[]
    for hour in range(24):
        rows=frame.loc[frame.index.hour==hour]
        angles=2*np.pi*rows.index.dayofyear.to_numpy()/365.25
        design=np.column_stack([np.ones(len(rows)),np.sin(angles),np.cos(angles)])
        ridge=np.diag([0.0,2.0,2.0])
        coefficients=np.linalg.solve(design.T@design+ridge,design.T@rows.pv_kw.to_numpy())
        annual.append(coefficients.tolist())
    training["pv_annual"]=annual
    return training


def hard_observation(raw):
    if raw is None:return None
    obs=dict(raw)
    for key in ["preus_properes_24h","co2_properes_24h"]:
        obs[key]=list(raw.get(key,[]))[:3]
    obs["noves_dades_5min"]=dict(raw.get("noves_dades_5min",{}))
    obs["cap_max_kwh"]=HARD_SPEC["capacity_kwh"]
    obs["power_max_kw"]=HARD_SPEC["power_kw"]
    return obs


def audit():
    import numpy as np
    import pandas as pd
    frame=load_hard();env=official_env()(frame,spec=HARD_SPEC)
    raw=env.reset();adapted=hard_observation(raw)
    net=frame.load_kw-frame.pv_kw
    gaps=frame.index.to_series().diff().dropna()
    report={"official_environment_sha256":hashlib.sha256((OFFICIAL/"starter_kit/environment.py").read_bytes()).hexdigest(),
            "raw_observation_keys":sorted(raw),"raw_telemetry_keys":sorted(raw["noves_dades_5min"]),
            "literal_snippet_forecast_lengths":[len(raw["preus_properes_24h"]),len(raw["co2_properes_24h"])],
            "adapter_forecast_lengths":[len(adapted["preus_properes_24h"]),len(adapted["co2_properes_24h"])],
            "adapter_added_fields":["cap_max_kwh","power_max_kw"],"meteorology_injected":False,
            "discrepancy":"El kit local ignora forecast_horizon=3; adapta només obs a regles publicades. No és un environment.py oficial actualitzat.",
            "spec_hard":HARD_SPEC,"solar_scale":12.0,"hours":len(frame),"start":str(frame.index[0]),"end":str(frame.index[-1]),
            "negative_net_hours":int((net<0).sum()),"solar_surplus_kwh":float((-net).clip(lower=0).sum()),
            "pv_generation_kwh":float(frame.pv_kw.sum()),"max_pv_kw":float(frame.pv_kw.max()),
            "gap_count":int(gaps.ne(pd.Timedelta(hours=1)).sum()),
            "max_gap_hours":float(gaps.max()/pd.Timedelta(hours=1)),
            "export_price":env.export_price,"initial_soc":float(env.soc),"dt_hours":env.dt}
    write(OUT/"environment_audit.json",report);print(json.dumps(report,ensure_ascii=False,indent=2))


def worker(model,period):
    import numpy as np
    import pandas as pd
    import scipy
    from experiments.oriol_hard_mode.policies import make_policy
    frame=load_hard(period);training=fit_training()
    configuration={"id":"standby","kind":"standby"} if model=="standby" else next(c for c in read(HERE/"protocol.json")["models"] if c["id"]==model)
    policy=make_policy(configuration,training)
    env=official_env()(frame,spec=HARD_SPEC,export_price=0.0)
    obs=hard_observation(env.reset());before=perf_counter()
    while obs is not None:
        action=policy.act(obs)
        if not np.isfinite(action):raise ValueError("Acció no finita")
        raw,_=env.step(action);obs=hard_observation(raw)
    metrics=env.evaluate_results()
    net=(frame.load_kw-frame.pv_kw).to_numpy();base=np.maximum(net,0)
    grid=np.asarray(env.grid);actions=np.asarray(env.actions)
    solar=frame.pv_kw.to_numpy();exports=np.asarray(env.exports)
    capture=np.minimum(np.maximum(actions,0),np.maximum(-net,0))
    battery_waste=np.maximum(-actions-np.maximum(net,0),0)
    metrics.update({"model":model,"configuration":configuration,"period":period,"steps":len(frame),"simulation_seconds":perf_counter()-before,
                    "failures":policy.failures,"lp_calls":policy.lp_calls,
                    "score_precise":float(100*(.7*(1-(grid@frame.co2_kg_per_kwh.to_numpy())/(base@frame.co2_kg_per_kwh.to_numpy()))+.3*(1-(grid@frame.precio_eur_per_kwh.to_numpy())/(base@frame.precio_eur_per_kwh.to_numpy())))),
                    "solar_surplus_base_kwh":float(np.maximum(-net,0).sum()),"exported_kwh":float(exports.sum()),
                    "surplus_captured_kwh":float(capture.sum()),"battery_export_waste_kwh":float(battery_waste.sum()),
                    "pv_locally_used_kwh":float(np.minimum(solar,frame.load_kw.to_numpy()).sum()+capture.sum()),"pv_generation_kwh":float(solar.sum()),
                    "soc_initial_kwh":env.soc_init,"soc_final_kwh":float(env.soc),
                    "soc_min_kwh":float(min(env.soc_series)),"soc_max_kwh":float(max(env.soc_series)),
                    "hours_soc_empty":int(np.sum(np.asarray(env.soc_series)<.01)),"hours_soc_full":int(np.sum(np.asarray(env.soc_series)>5999.99)),
                    "actions_sha256":hashlib.sha256(actions.astype('<f8').tobytes()).hexdigest(),
                    "monthly":{str(m):env.evaluate_results(mask=frame.index.to_period('M')==m) for m in frame.index.to_period('M').unique()},
                    "python":platform.python_version(),"numpy":np.__version__,"pandas":pd.__version__,"scipy":scipy.__version__})
    OUT.mkdir(parents=True,exist_ok=True)
    pd.DataFrame({"timestamp":frame.index.astype(str),"soc_kwh":env.soc_series,"action_kw":actions,
                  "grid_kw":grid,"exports_kw":exports}).to_csv(OUT/f"trace_{period}_{model}.csv",index=False)
    print(json.dumps(metrics,ensure_ascii=False,allow_nan=False))


def execute(model,period):
    before=perf_counter()
    result=subprocess.run([sys.executable,"-B","-X","utf8",str(Path(__file__).resolve()),"worker","--model",model,"--period",period],
                          cwd=ROOT,capture_output=True,text=True,encoding="utf-8",timeout=120)
    if result.returncode:raise RuntimeError(result.stdout+result.stderr)
    row=json.loads(result.stdout);row["process_seconds"]=perf_counter()-before
    write(OUT/f"{period}_{model}.json",row)
    print(f"{period:13} {model:24} score={row['score']:.2f} CO2={row['co2_estalviat_pct']:.2f}% cost={row['cost_estalviat_pct']:.2f}% infr={row['infraccions']} wall={row['process_seconds']:.2f}s",flush=True)
    return row


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase",choices=["audit","baseline","worker","calibrate","validate","confirm"])
    parser.add_argument("--model",default="naive3");parser.add_argument("--period",default="full")
    args=parser.parse_args()
    if args.phase=="audit":audit()
    elif args.phase=="worker":worker(args.model,args.period)
    elif args.phase=="baseline":
        rows=[execute(m,"full") for m in ["standby","naive3"]]
        write(OUT/"first_baseline.json",{"regime":"hard_physics_with_documented_obs_adapter","rows":rows})
    elif args.phase=="calibrate":
        write(HERE/"training.json",fit_training())
        rows=[execute(c["id"],"calibration") for c in read(HERE/"protocol.json")["models"]]
        chosen=[]
        for family in "ABCDE":
            eligible=[r for r in rows if r["configuration"]["family"]==family and r["infraccions"]==0 and r["failures"]==0]
            if eligible:chosen.append(max(eligible,key=lambda r:r["score_precise"])["model"])
        hashes={n:hashlib.sha256((HERE/n).read_bytes()).hexdigest() for n in ["policies.py","forecast.py","safety.py","lab.py","protocol.json","training.json"]}
        write(OUT/"calibration.json",{"rows":rows,"chosen":chosen,"source_sha256":hashes})
    elif args.phase=="validate":
        calibrated=read(OUT/"calibration.json")
        for n,h in calibrated["source_sha256"].items():
            if hashlib.sha256((HERE/n).read_bytes()).hexdigest()!=h:raise RuntimeError("Codi canviat després de calibrar")
        rows=[execute(m,"validation") for m in calibrated["chosen"]]
        good=[r for r in rows if r["infraccions"]==0 and r["failures"]==0 and r["process_seconds"]<45]
        ranking=sorted(good,key=lambda r:r["score_precise"],reverse=True)
        write(OUT/"validation.json",{"rows":rows,"ranking":[r["model"] for r in ranking],"source_sha256":calibrated["source_sha256"]})
    else:
        validated=read(OUT/"validation.json")
        for n,h in validated["source_sha256"].items():
            if hashlib.sha256((HERE/n).read_bytes()).hexdigest()!=h:raise RuntimeError("Codi canviat després de validar")
        rows=[execute(m,"confirmation") for m in read(OUT/"calibration.json")["chosen"]]
        write(OUT/"confirmation.json",{"rows":rows,"selected_before_confirmation":validated["ranking"][0]})


if __name__=="__main__":main()
