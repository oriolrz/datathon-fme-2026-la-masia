"""Forecast causal propi: perfils de calibratge + correcció t−1.

Solar i telemetria ja són Hard ×12. No s'utilitza meteorologia absent al kit.
No es llegeix cap CSV en inferència; les hores de mercat 4..24 es prediuen.
"""

from datetime import datetime,timedelta
from math import cos,sin,pi,exp,isfinite

import numpy as np


def parse_timestamp(obs):
    value=obs.get("timestamp")
    try:
        return value.to_pydatetime() if hasattr(value,"to_pydatetime") else datetime.fromisoformat(str(value))
    except (ValueError,TypeError):
        hour=int(obs.get("hour",0));day=int(obs.get("day_of_week",0))
        return datetime(2000,1,3)+timedelta(days=max(0,min(6,day)),hours=max(0,min(23,hour)))


class Forecaster:
    def __init__(self,training,mode="adaptive"):
        self.training=training
        self.mode=mode
        self.previous=None
        self.load_residual=0.0
        self.pv_ratio=1.0
        self.ratio_timestamp=None

    def profile(self,name,ts):
        if name=="pv" and self.mode=="annual":
            angle=2*pi*ts.timetuple().tm_yday/365.25
            coefficients=self.training["pv_annual"][ts.hour]
            value=coefficients[0]+coefficients[1]*sin(angle)+coefficients[2]*cos(angle)
            return max(0.0,min(self.training["max_pv_kw"]*1.5,value))
        return float(self.training[name+"_profile"][ts.weekday()][ts.hour])

    def forecast(self,obs,horizon=24):
        now=parse_timestamp(obs)
        contiguous=False
        if self.previous is not None:
            try:contiguous=(now-self.previous).total_seconds()==3600
            except TypeError:pass
        if not contiguous:
            self.load_residual=0.0;self.pv_ratio=1.0;self.ratio_timestamp=None
        elif self.mode!="profile":
            telemetry=obs.get("noves_dades_5min",{})
            try:
                load=float(telemetry["ultim_consum_kw"]);pv=float(telemetry["ultima_solar_kw"])
                if all(isfinite(v) and v>=0 for v in [load,pv]):
                    residual=load-self.profile("load",self.previous)
                    bound=self.training["load_residual_clip_kw"]
                    self.load_residual=.5*self.load_residual+.5*max(-bound,min(bound,residual))
                    base=self.profile("pv",self.previous)
                    if base>100.0:
                        self.pv_ratio=max(.1,min(2.5,pv/base));self.ratio_timestamp=self.previous
            except (KeyError,ValueError,TypeError):pass
        self.previous=now
        timestamps=[now+timedelta(hours=i) for i in range(horizon)]
        load=np.asarray([max(0.0,self.profile("load",ts)+self.load_residual*exp(-i/6)) for i,ts in enumerate(timestamps)])
        age=(now-self.ratio_timestamp).total_seconds()/3600 if self.ratio_timestamp is not None else 0
        pv=np.asarray([max(0.0,self.profile("pv",ts)*(1+(self.pv_ratio-1)*exp(-(age+i)/6))) for i,ts in enumerate(timestamps)])
        price=np.asarray([max(1e-5,self.profile("price",ts)) for ts in timestamps])
        carbon=np.asarray([max(1e-5,self.profile("carbon",ts)) for ts in timestamps])
        try:
            known_p=np.asarray(obs.get("preus_properes_24h",[]),dtype=float)[:3]
            known_c=np.asarray(obs.get("co2_properes_24h",[]),dtype=float)[:3]
            n=min(len(known_p),len(known_c),3,horizon)
            if not np.isfinite(known_p[:n]).all() or not np.isfinite(known_c[:n]).all():n=0
        except (ValueError,TypeError):n=0
        if n:
            if self.mode!="profile":
                residual_p=float(np.mean(known_p[:n]-price[:n]))
                residual_c=float(np.mean(known_c[:n]-carbon[:n]))
                for i in range(n,horizon):
                    price[i]=max(1e-5,price[i]+residual_p*exp(-(i-n+1)/6))
                    carbon[i]=max(1e-5,carbon[i]+residual_c*exp(-(i-n+1)/6))
            price[:n]=known_p[:n];carbon[:n]=known_c[:n]
        return {"load_kw":load,"pv_kw":pv,"price":price,"carbon":carbon,"known_market_hours":n,
                "timestamp":now,"contiguous":contiguous}
