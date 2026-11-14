"""Auditoria dels forecasts congelats; els targets només entren al càlcul d'errors.

No retorna targets a cap agent ni altera la selecció feta amb validació.
"""

import hashlib
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[1]))

from experiments.oriol_hard_mode.forecast import Forecaster
from experiments.oriol_hard_mode.lab import load_hard,read,write,OUT


def main():
    training=read(HERE/'training.json')
    report={'purpose':'diagnostic_after_selection_no_tuning','periods':{},'data_fingerprint':{}}
    for period in ['calibration','validation','confirmation']:
        frame=load_hard(period)
        digest=hashlib.sha256()
        digest.update('\n'.join(frame.index.astype(str)).encode('utf-8'))
        digest.update(frame.to_numpy(dtype='<f8').tobytes())
        report['data_fingerprint'][period]={'hours':len(frame),'first':str(frame.index[0]),'last':str(frame.index[-1]),
                                             'sha256_index_and_columns':digest.hexdigest(),'columns':frame.columns.tolist()}
        if period=='calibration':continue
        modes={mode:Forecaster(training,mode) for mode in ['profile','adaptive','annual']}
        errors={mode:{key:[] for key in ['load_now_kw','pv_now_kw','price_unknown_eur_kwh','carbon_unknown_kg_kwh']} for mode in modes}
        for i,(timestamp,row) in enumerate(frame.iterrows()):
            # Només la telemetria anterior i les 3 files de mercat observables.
            previous=frame.iloc[max(0,i-1)]
            obs={'timestamp':timestamp,'preus_properes_24h':frame.precio_eur_per_kwh.iloc[i:i+3].tolist(),
                 'co2_properes_24h':frame.co2_kg_per_kwh.iloc[i:i+3].tolist(),
                 'noves_dades_5min':{'ultim_consum_kw':previous.load_kw,'ultima_solar_kw':previous.pv_kw}}
            for mode,predictor in modes.items():
                forecasts=predictor.forecast(obs)
                errors[mode]['load_now_kw'].append(float(forecasts['load_kw'][0]-row.load_kw))
                errors[mode]['pv_now_kw'].append(float(forecasts['pv_kw'][0]-row.pv_kw))
                # Diagnòstic només: alineament cronològic explícit, sense travessar salts.
                for horizon in range(3,24):
                    target_timestamp=timestamp+pd.Timedelta(hours=horizon)
                    if target_timestamp not in frame.index:continue
                    target=frame.loc[target_timestamp]
                    errors[mode]['price_unknown_eur_kwh'].append(float(forecasts['price'][horizon]-target.precio_eur_per_kwh))
                    errors[mode]['carbon_unknown_kg_kwh'].append(float(forecasts['carbon'][horizon]-target.co2_kg_per_kwh))
        report['periods'][period]={mode:{key:{'n':len(values),'mae':float(np.mean(np.abs(values))),
                                                             'rmse':float(np.sqrt(np.mean(np.square(values))))}
                                         for key,values in fields.items()} for mode,fields in errors.items()}
    write(OUT/'forecast_diagnostics.json',report)
    for period,rows in report['periods'].items():
        for mode,row in rows.items():print(period,mode,{key:round(value['mae'],5) for key,value in row.items()})


if __name__=='__main__':main()
