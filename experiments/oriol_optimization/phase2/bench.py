"""Comparacions fase 2; oracles explícits, resultats precisos i finestres iguals."""

import argparse
import hashlib
import json
import platform
import subprocess
import sys
from pathlib import Path
from time import perf_counter

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OUT = ROOT / "artifacts/oriol_phase2"
OFFICIAL = ROOT.parent / "paquet_participants_datathon_upc"
sys.path.insert(0, str(ROOT))


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write(path, value):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def data_and_training(period):
    import numpy as np
    from scripts.evaluate import load_hourly_data

    data = load_hourly_data(OFFICIAL)
    cal = data.loc[data.index < "2026-03-01"]
    net = (cal.load_kw - cal.pv_kw).clip(lower=0)
    profile = cal.assign(net=net).groupby([cal.index.dayofweek, cal.index.hour]).net.mean()
    training = {
        "weighted": {"mean_carbon": float((net*cal.co2_kg_per_kwh).sum()/net.sum()),
                     "mean_price": float((net*cal.precio_eur_per_kwh).sum()/net.sum())},
        "unweighted": {"mean_carbon": float(cal.co2_kg_per_kwh.mean()), "mean_price": float(cal.precio_eur_per_kwh.mean())},
        "mean_net": float(net.mean()),
        "profile": [[float(profile.get((day,hour), net.mean())) for hour in range(24)] for day in range(7)],
    }
    if period == "calibration":
        data = cal
    elif period == "validation":
        data = data.loc[(data.index >= "2026-03-01") & (data.index < "2026-06-01")]
    elif period == "confirmation":
        data = data.loc[data.index >= "2026-06-01"]
    elif period != "full":
        raise ValueError(period)
    return data, training


def raw_score(data, grid):
    import numpy as np

    base = np.maximum(data.load_kw.to_numpy()-data.pv_kw.to_numpy(),0)
    carbon, price = data.co2_kg_per_kwh.to_numpy(), data.precio_eur_per_kwh.to_numpy()
    return float(100*(.7*(1-(grid@carbon)/(base@carbon))+.3*(1-(grid@price)/(base@price))))


def simulate(configuration, period):
    import numpy as np
    import pandas as pd
    import scipy
    from scripts.evaluate import load_module
    from experiments.oriol_optimization.policies import MPCPolicy
    from experiments.oriol_optimization.phase2.model import AdvancedMPC

    data, training = data_and_training(period)
    env_class = load_module(OFFICIAL / "starter_kit/environment.py", "phase2_official_env").CampusBatteryEnv
    env = env_class(data)
    if configuration["id"] == "current":
        policy = MPCPolicy(training["weighted"], terminal_factor=0, terminal_target=1000)
    else:
        callback = None
        if configuration["forecast"] == "perfect":
            # Diagnòstic uniquement: aquest callback no forma part del lliurable.
            callback = lambda obs,horizon: (data.load_kw-data.pv_kw).iloc[env.t:env.t+horizon].to_numpy()
        policy = AdvancedMPC(configuration, training, callback)
    obs = env.reset()
    forecast_abs_error, forecast_steps, export_waste = 0.0, 0, 0.0
    before = perf_counter()
    while obs is not None:
        action = policy.act(obs)
        if not np.isfinite(action):
            raise ValueError("Acció no finita")
        net = float(data.load_kw.iloc[env.t]-data.pv_kw.iloc[env.t])
        forecast = getattr(policy,"last_forecast",None)
        forecast_abs_error += abs((500.0 if forecast is None else forecast[0])-net)
        forecast_steps += 1
        export_waste += max(0.0, -action-max(net,0))
        obs,_ = env.step(action)
    result = env.evaluate_results()
    result.update({
        "id": configuration["id"], "configuration": configuration, "period": period, "steps": len(data),
        "oracle": configuration["forecast"] == "perfect", "score_precise": raw_score(data,np.asarray(env.grid)),
        "simulation_seconds": perf_counter()-before,
        "failures": getattr(policy,"failures",0), "lp_calls": policy.lp_calls,
        "forecast_mae_kw": forecast_abs_error/forecast_steps, "discharge_export_waste_kwh": export_waste,
        "soc_final_kwh": float(env.soc), "soc_min_kwh": float(min(env.soc_series)), "soc_max_kwh": float(max(env.soc_series)),
        "actions_sha256": hashlib.sha256(np.asarray(env.actions,dtype="<f8").tobytes()).hexdigest(),
        "monthly": {str(month):env.evaluate_results(mask=data.index.to_period("M")==month)
                    for month in data.index.to_period("M").unique()},
        "python":platform.python_version(), "numpy":np.__version__,"pandas":pd.__version__,"scipy":scipy.__version__,
    })
    return result


def offline_bound(period, normalization="oracle"):
    import numpy as np
    from experiments.oriol_optimization.policies import solve_plan

    data,training = data_and_training(period)
    n=len(data)
    net=(data.load_kw-data.pv_kw).to_numpy()
    base=np.maximum(net,0)
    carbon,price=data.co2_kg_per_kwh.to_numpy(),data.precio_eur_per_kwh.to_numpy()
    params=training["weighted"] if normalization=="weighted" else {"mean_carbon":(base@carbon)/base.sum(),"mean_price":(base@price)/base.sum()}
    values=.7*carbon/params["mean_carbon"]+.3*price/params["mean_price"]
    before=perf_counter()
    actions,res=solve_plan(values,1000.0,net)
    c,d,e,g=res.x[:n],res.x[n:2*n],res.x[2*n:3*n],res.x[3*n:]
    reconstructed=np.r_[1000.0,e[:-1]]+np.sqrt(.9)*c-d/np.sqrt(.9)
    rhs_eq=np.r_[1000.0,np.zeros(n-1)]
    upper=np.r_[np.full(2*n,500.0),np.full(n,2000.0)]
    dual=float(res.eqlin.marginals@rhs_eq+res.ineqlin.marginals@(-net)+res.upper.marginals[:3*n]@upper)
    report={"id":"offline_"+normalization,"period":period,"oracle":True,"steps":n,
            "score_precise":raw_score(data,g),"score":round(raw_score(data,g),2),
            "solver_seconds":perf_counter()-before,"primal_dual_gap":float(abs(res.fun-dual)),
            "soc_balance_max_residual_kwh":float(max(abs(e-reconstructed))),
            "soc_min_kwh":float(min(e)),"soc_max_kwh":float(max(e)),
            "max_simultaneous_power_kw":float(np.minimum(c,d).max()),
            "max_power_kw":float(max(c.max(),d.max())),
            "grid_constraint_min_slack_kw":float(min(g-net-c+d)),
            "foreknowledge":"Demanda, PV, preus i CO2 de tot el període; SOC final lliure.",
            "normalization":normalization,"parameters":{k:float(v) for k,v in params.items()}}
    if normalization=="oracle":
        report["numerical_upper_bound_score"]=float(100*(1-(dual-1e-8*1000*n)/base.sum()))
    return report


def execute(model,period):
    before=perf_counter()
    process=subprocess.run([sys.executable,"-B","-X","utf8",str(Path(__file__).resolve()),"worker","--model",model,"--period",period],
                           cwd=ROOT,capture_output=True,text=True,encoding="utf-8",timeout=100)
    if process.returncode:
        raise RuntimeError(process.stdout+process.stderr)
    row=json.loads(process.stdout)
    row["process_seconds"]=perf_counter()-before
    write(OUT/f"{period}_{model}.json",row)
    print(f"{period:13} {model:23} score={row['score_precise']:.8f} wall={row['process_seconds']:.2f}s",flush=True)
    return row


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase",choices=["worker","bounds","calibrate","validate","confirm"])
    parser.add_argument("--model",default="current")
    parser.add_argument("--period",default="calibration")
    args=parser.parse_args()
    protocol=read(HERE/"protocol.json")
    if args.phase=="worker":
        if args.model.startswith("offline_"):
            result=offline_bound(args.period,args.model.split("_",1)[1])
        else:
            config=next(c for c in protocol["models"] if c["id"]==args.model)
            result=simulate(config,args.period)
        print(json.dumps(result,allow_nan=False)); return
    if args.phase=="bounds":
        rows=[execute(model,period) for period in ["calibration","validation","confirmation","full"]
              for model in ["offline_oracle","offline_weighted"]]
        write(OUT/"bounds.json",rows); return
    if args.phase=="calibrate":
        rows=[execute(c["id"],"calibration") for c in protocol["models"]]
        shortlist=["current","perfect24","seasonal24","persistence24"]
        for family in ["terminal","horizon","normalization"]:
            options=[r for r in rows if r["configuration"]["family"]==family and r["infraccions"]==0 and r["failures"]==0]
            if options:
                # Empats a 1e-6 punts: ordre declarat, no soroll de runtime.
                shortlist.append(max(options,key=lambda r:round(r["score_precise"],6))["id"])
        write(OUT/"calibration.json",{"rows":rows,"shortlist":shortlist}); return
    if args.phase=="validate":
        models=read(OUT/"calibration.json")["shortlist"]
        rows=[execute(m,"validation") for m in models]
        baseline=next(r for r in rows if r["id"]=="current")
        eligible=[r for r in rows if not r["oracle"] and r["infraccions"]==0 and r["failures"]==0
                  and r["process_seconds"]<protocol["max_local_process_seconds"]
                  and r["score_precise"]>=baseline["score_precise"]+protocol["meaningful_gain_points"]
                  and all(v["score"]>=baseline["monthly"][m]["score"]-protocol["monthly_max_loss_points"] for m,v in r["monthly"].items())]
        winner=max(eligible,key=lambda r:r["score_precise"])["id"] if eligible else "current"
        write(OUT/"validation.json",{"rows":rows,"winner":winner,"meaningful_improvement":bool(eligible)}); return
    selected=read(OUT/"validation.json")["winner"]
    models=list(dict.fromkeys(["current","perfect24","seasonal24","persistence24",selected]))
    rows=[execute(m,"confirmation") for m in models]
    write(OUT/"confirmation.json",{"rows":rows,"frozen_selection":selected})


if __name__=="__main__":
    main()
