"""Polítiques Hard independents; cap import dels mòduls del Dani o Cesc."""

import numpy as np
from functools import lru_cache

from experiments.oriol_hard_mode.safety import ETA, clamp_action, limits
from experiments.oriol_hard_mode.forecast import Forecaster


@lru_cache(maxsize=16)
def constraint_template(n):
    from scipy.sparse import coo_matrix
    rows,cols,data=[],[],[]
    for i in range(n):
        for col,value in [(i,-ETA),(n+i,1/ETA),(2*n+i,1)]:
            rows.append(i);cols.append(col);data.append(value)
        if i:
            rows.append(i);cols.append(2*n+i-1);data.append(-1)
    equality=coo_matrix((data,(rows,cols)),shape=(n,4*n)).tocsr()
    rows,cols,data=[],[],[]
    for i in range(n):
        for col,value in [(i,1),(n+i,-1),(3*n+i,-1)]:
            rows.append(i);cols.append(col);data.append(value)
    inequality=coo_matrix((data,(rows,cols)),shape=(n,4*n)).tocsr()
    return equality,inequality


def solve_hard_plan(values, soc, net, capacity=6000.0, power=1500.0,
                    terminal_target=None, terminal_value=0.0):
    from scipy.optimize import linprog

    n=len(values)
    objective=np.zeros(4*n)
    objective[:2*n]=1e-8
    objective[3*n:]=values
    objective[3*n-1]=-terminal_value
    equality,inequality=constraint_template(n)
    rhs=np.zeros(n);rhs[0]=soc
    bounds=[(0,power)]*(2*n)+[(0,capacity)]*n+[(0,None)]*n
    if terminal_target is not None:
        bounds[3*n-1]=(terminal_target,terminal_target)
    result=linprog(objective,A_eq=equality,b_eq=rhs,A_ub=inequality,b_ub=-np.asarray(net),
                   bounds=bounds,method="highs",options={"time_limit":.5 if n<=72 else 15.0})
    if not result.success or not np.isfinite(result.x).all():
        raise RuntimeError(f"LP Hard no resolt: {result.status}")
    c,d=result.x[:n],result.x[n:2*n]
    if np.any(np.minimum(c,d)>1e-5):
        raise RuntimeError("Càrrega i descàrrega simultànies")
    return c-d,result


class NaiveHardMPC:
    """Port de comparació: només 3 valors, demanda 1.500 i terminal 50%."""

    def __init__(self,training):
        self.training=training
        self.failures=0
        self.lp_calls=0

    def act(self,obs):
        state=limits(obs)
        if state is None:return 0.0
        capacity,power,soc=state
        try:
            p=np.asarray(obs.get("preus_properes_24h",[]),dtype=float)[:3]
            c=np.asarray(obs.get("co2_properes_24h",[]),dtype=float)[:3]
            n=min(len(p),len(c))
            if n==0 or not np.isfinite(p[:n]).all() or not np.isfinite(c[:n]).all():return 0.0
            values=.7*c[:n]/self.training["mean_carbon"]+.3*p[:n]/self.training["mean_price"]
            if np.any(values<=0):return 0.0
            self.lp_calls+=1
            actions,_=solve_hard_plan(values,soc,np.full(n,power),capacity,power,
                                       terminal_target=capacity*.5 if n==3 else None)
            return clamp_action(actions[0],obs)
        except (TypeError,ValueError,RuntimeError):
            self.failures+=1
            return 0.0


class Standby:
    failures=0
    lp_calls=0
    def act(self,obs):return 0.0


@lru_cache(maxsize=8)
def scenario_template(n,shared):
    from scipy.sparse import block_diag,coo_matrix,vstack

    equality,inequality=constraint_template(n)
    eq=block_diag([equality]*3,format="csr")
    rows,cols,data=[],[],[]
    row=0
    for scenario in [1,2]:
        for step in range(shared):
            for offset in [0,n]:
                rows.extend([row,row]);cols.extend([scenario*4*n+offset+step,offset+step]);data.extend([1,-1]);row+=1
    coupling=coo_matrix((data,(rows,cols)),shape=(row,12*n)).tocsr()
    return vstack([eq,coupling],format="csr"),block_diag([inequality]*3,format="csr")


def solve_scenarios(values,soc,load,pv,capacity,power,shared_steps=2):
    """Tres escenaris equiprobables; les primeres decisions són comunes.

    No és una garantia worst-case: és un MPC per escenaris finit i causal.
    """
    from scipy.optimize import linprog

    n=len(values);shared=min(shared_steps,n)
    equality,inequality=scenario_template(n,shared)
    objective=[];bounds=[];net=[]
    for load_factor,pv_factor in [(1.10,.65),(1.0,1.0),(.90,1.35)]:
        c=np.zeros(4*n);c[:2*n]=1e-8;c[3*n:]=values/3.0
        objective.extend(c.tolist())
        scenario_bounds=[(0,power)]*(2*n)+[(0,capacity)]*n+[(0,None)]*n
        if n>=3:scenario_bounds[3*n-1]=(capacity*.5,capacity*.5)
        bounds.extend(scenario_bounds)
        net.extend(np.clip(load*load_factor-pv*pv_factor,-power,power).tolist())
    rhs=np.zeros(3*n+4*shared);rhs[0]=soc;rhs[n]=soc;rhs[2*n]=soc
    result=linprog(np.asarray(objective),A_eq=equality,b_eq=rhs,A_ub=inequality,b_ub=-np.asarray(net),
                   bounds=bounds,method="highs",options={"time_limit":.5})
    if not result.success or not np.isfinite(result.x).all():raise RuntimeError("LP escenaris no resolt")
    for scenario in range(3):
        block=result.x[scenario*4*n:(scenario+1)*4*n]
        if np.any(np.minimum(block[:n],block[n:2*n])>1e-5):raise RuntimeError("Cicle simultani en escenari")
    return result.x[:n]-result.x[n:2*n]


class HardAgent:
    """Wrapper d'integració independent; callbacks explícits i clamp final.

    forecast_provider(obs,horizon=24)->dict(load_kw,pv_kw,price?,carbon?).
    policy(obs,forecasts=None)->float. Cap import automàtic de codi aliè.
    """

    def __init__(self,training,configuration,forecast_provider=None,policy=None):
        self.training=training;self.configuration=configuration
        self.forecaster=Forecaster(training,configuration.get("forecast","adaptive"))
        self.forecast_provider=forecast_provider;self.policy=policy
        self.failures=0;self.lp_calls=0;self.last_forecasts=None
        self.plan=[];self.previous_caps=None

    def solar_action(self,forecasts,state):
        capacity,power,soc=state
        net=forecasts["load_kw"]-forecasts["pv_kw"]
        values=.7*forecasts["carbon"]/self.training["mean_carbon"]+.3*forecasts["price"]/self.training["mean_price"]
        if net[0]<0:return min(power,-net[0])
        future_free=float(np.maximum(-net[1:9],0).sum())*ETA
        headroom_target=max(0.0,capacity-future_free)
        if soc>headroom_target:
            return -min(power,max(net[0],0),(soc-headroom_target)*ETA)
        current=values[0];mean=float(np.mean(values))
        if current>mean+.05:
            reserve=capacity*.25 if max(values[1:])>current*1.2 else 0.0
            return -min(power,max(net[0],0),max(0.0,soc-reserve)*ETA)
        if current<mean-.15 and max(values[1:])*.9>current+.05:
            target=min(capacity*.5,headroom_target)
            return min(power,max(0.0,target-soc)/ETA)
        return 0.0

    def act(self,obs):
        state=limits(obs)
        if state is None:return 0.0
        safe_obs=dict(obs)
        capacity,power,soc=state
        forecasts=self.forecaster.forecast(obs,24)
        if self.forecast_provider is not None:
            try:
                external=self.forecast_provider(obs,horizon=24)
                for key in ["load_kw","pv_kw"]:
                    candidate=np.asarray(external[key],dtype=float)
                    if candidate.shape!=(24,) or not np.isfinite(candidate).all() or np.any(candidate<0):
                        raise ValueError("Forecast extern no finit o amb unitats/format incorrectes")
                    forecasts[key]=candidate.copy()
            except Exception:self.failures+=1
        self.last_forecasts=forecasts
        if self.policy is not None:
            try:
                action=float(self.policy(obs,forecasts=forecasts))
                if not np.isfinite(action):raise ValueError("Política externa no finita")
                return clamp_action(action,safe_obs)
            except Exception:
                self.failures+=1
                return clamp_action(self.solar_action(forecasts,state),safe_obs)
        if self.configuration["kind"]=="heuristic":
            return clamp_action(self.solar_action(forecasts,state),safe_obs)
        known=forecasts["known_market_hours"]
        if known==0:return 0.0
        n=known if known<3 else self.configuration.get("horizon",24)
        values=.7*forecasts["carbon"]/self.training["mean_carbon"]+.3*forecasts["price"]/self.training["mean_price"]
        if not np.isfinite(values).all() or np.any(values<=0):
            self.failures+=1
            return clamp_action(self.solar_action(forecasts,state),safe_obs)
        if not forecasts["contiguous"] or self.previous_caps!=(capacity,power) or known<3:self.plan=[]
        self.previous_caps=(capacity,power)
        if self.plan:
            return clamp_action(self.plan.pop(0),safe_obs)
        try:
            self.lp_calls+=1
            if self.configuration["kind"]=="scenarios":
                shared=self.configuration.get("replan_every",2)
                actions=solve_scenarios(values[:n],soc,forecasts["load_kw"][:n],forecasts["pv_kw"][:n],capacity,power,shared)
                self.plan=actions[1:min(shared,n)].tolist()
            else:
                target=capacity*.5 if self.configuration.get("terminal")=="target" and known==3 else None
                terminal_value=0.0
                if self.configuration.get("terminal")=="shadow" and known==3:
                    tail=values[3:] if n==3 else values[12:]
                    terminal_value=self.configuration.get("terminal_factor",.8)*ETA*float(np.mean(tail))
                net=np.clip(forecasts["load_kw"][:n]-forecasts["pv_kw"][:n],-power,power)
                actions,_=solve_hard_plan(values[:n],soc,net,capacity,power,target,terminal_value)
            return clamp_action(actions[0],safe_obs)
        except (ValueError,RuntimeError):
            self.failures+=1
            return clamp_action(self.solar_action(forecasts,state),safe_obs)


def make_policy(configuration,training):
    if configuration["kind"]=="standby":return Standby()
    if configuration["kind"]=="naive":return NaiveHardMPC(training)
    return HardAgent(training,configuration)
