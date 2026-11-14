"""Empaquetatge determinista i benchmark Hard del ZIP en un procés aïllat.

Aquest script és una eina local i queda fora del lliurable.
"""

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from time import perf_counter
import zipfile

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
OUT=ROOT/'artifacts/oriol_hard_mode'


def read(path):return json.loads(Path(path).read_text(encoding='utf-8'))


def write(path,value):
    Path(path).parent.mkdir(parents=True,exist_ok=True)
    Path(path).write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8',newline='\n')


def check_frozen():
    frozen=read(OUT/'validation.json')
    for name,expected in frozen['source_sha256'].items():
        if hashlib.sha256((HERE/name).read_bytes()).hexdigest()!=expected:
            raise RuntimeError(f'Font canviada després de validar: {name}')
    return frozen


def build():
    sys.path.insert(0,str(ROOT))
    from scripts.package import local_dependencies,validate_archive

    validated=check_frozen()
    selected=validated['ranking'][0]
    configuration=next(c for c in read(HERE/'protocol.json')['models'] if c['id']==selected)
    frozen={'selected_by':'validation_before_confirmation','configuration':configuration,
            'source_sha256':validated['source_sha256'],'telemetry_pv_units':'Hard kW already x12'}
    write(HERE/'candidate_config.json',frozen)
    output=OUT/'hard_candidate_submission.zip'
    payload={'agent.py':(HERE/'candidate_agent.py').read_bytes(),
             'training.json':(HERE/'training.json').read_bytes(),
             'candidate_config.json':(HERE/'candidate_config.json').read_bytes(),
             'experiments/__init__.py':b'',
             'experiments/oriol_hard_mode/__init__.py':b''}
    for name in ['safety.py','forecast.py','policies.py']:
        payload['experiments/oriol_hard_mode/'+name]=(HERE/name).read_bytes()
    with tempfile.TemporaryDirectory(prefix='masia_hard_manifest_') as temporary:
        for name,content in payload.items():
            path=Path(temporary)/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(content)
        required={p.as_posix() for p in local_dependencies(temporary)}
        if required!={n for n in payload if n.endswith('.py')}:
            raise RuntimeError('El manifest no coincideix amb les dependències locals')
    with zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED) as archive:
        for name,content in sorted(payload.items()):
            entry=zipfile.ZipInfo(name,date_time=(2026,11,14,0,0,0));entry.compress_type=zipfile.ZIP_DEFLATED
            entry.create_system=3;entry.external_attr=0o100644<<16;archive.writestr(entry,content)
    if output.stat().st_size>=25_000_000:raise RuntimeError('El ZIP supera el límit general publicat')
    checker=ROOT.parent/'paquet_participants_datathon_upc/starter_kit/check_submission.py'
    result=validate_archive(output,checker)
    output.with_suffix('.checker.txt').write_text(result.stdout+result.stderr,encoding='utf-8')
    manifest={'zip':str(output),'zip_bytes':output.stat().st_size,
              'zip_sha256':hashlib.sha256(output.read_bytes()).hexdigest(),
              'files':{n:hashlib.sha256(b).hexdigest() for n,b in sorted(payload.items())},
              'checker_sha256':hashlib.sha256(checker.read_bytes()).hexdigest(),
              'checker_exit_code':result.returncode,'checker_scope':'official_local_generic_24_steps_not_hard_web',
              'selected':selected,'dependencies':{'numpy':'2.4.1','scipy':'1.17.0'},
              'web_hard_validation':'pending_no_upload_or_submission'}
    write(output.with_suffix('.manifest.json'),manifest)
    print(result.stdout+result.stderr);print(json.dumps(manifest,ensure_ascii=False,indent=2))
    if result.returncode:raise SystemExit(result.returncode)


def isolated(archive,extraction):
    # -I i cwd temporal; l'agent s'importa ABANS d'accedir a eines del repo.
    with zipfile.ZipFile(archive) as packed:packed.extractall(extraction)
    sys.path.insert(0,str(extraction))
    import agent
    controller=agent.BatteryAgent()
    spec=importlib.util.spec_from_file_location('local_hard_harness',HERE/'lab.py')
    lab=importlib.util.module_from_spec(spec);spec.loader.exec_module(lab)
    import numpy as np

    frame=lab.load_hard();env=lab.official_env()(frame,spec=lab.HARD_SPEC,export_price=0.)
    obs=lab.hard_observation(env.reset());before=perf_counter()
    while obs is not None:
        action=controller.act(obs)
        if not isinstance(action,float) or not np.isfinite(action):raise RuntimeError('Sortida no finita o no float')
        obs,_=env.step(action);obs=lab.hard_observation(obs)
    seconds=perf_counter()-before
    modules={name:str(Path(module.__file__).resolve()) for name,module in sys.modules.items()
             if (name=='agent' or name.startswith('experiments.oriol_hard_mode')) and getattr(module,'__file__',None)}
    if any(not Path(p).is_relative_to(extraction) for p in modules.values()):raise RuntimeError('Import local fora del ZIP')
    reference=read(OUT/('full_'+read(HERE/'candidate_config.json')['configuration']['id']+'.json'))
    action_hash=hashlib.sha256(np.asarray(env.actions,dtype='<f8').tobytes()).hexdigest()
    if action_hash!=reference['actions_sha256']:raise RuntimeError('El ZIP no reprodueix les accions de la font congelada')
    metrics=env.evaluate_results()
    if metrics['infraccions'] or controller.policy_failures:raise RuntimeError('Infraccions o fallades en el ZIP final')
    metrics.update({'steps':len(frame),'simulation_seconds':seconds,'failures':controller.policy_failures,
                    'actions_sha256':action_hash,'matches_frozen_source':True,'local_module_paths':modules,
                    'regime':'official_physics_with_documented_hard_observation_adapter'})
    print(json.dumps(metrics,ensure_ascii=False,allow_nan=False))


def benchmark():
    check_frozen()
    archive=OUT/'hard_candidate_submission.zip'
    before=perf_counter()
    with tempfile.TemporaryDirectory(prefix='masia_hard_isolated_') as temporary:
        result=subprocess.run([sys.executable,'-I','-B','-X','utf8',str(Path(__file__).resolve()),'isolated',
                               '--archive',str(archive),'--extraction',temporary],cwd=temporary,
                              capture_output=True,text=True,encoding='utf-8',timeout=60)
    wall=perf_counter()-before
    if result.returncode:raise RuntimeError(result.stdout+result.stderr)
    metrics=json.loads(result.stdout);metrics['process_seconds']=wall
    metrics['zip_sha256']=hashlib.sha256(archive.read_bytes()).hexdigest()
    write(OUT/'final_zip_benchmark.json',metrics)
    print(json.dumps(metrics,ensure_ascii=False,indent=2))
    if wall>=45:raise RuntimeError('Procés complet sense el marge local de 45s')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase',choices=['build','benchmark','isolated'])
    parser.add_argument('--archive',type=Path);parser.add_argument('--extraction',type=Path)
    args=parser.parse_args()
    if args.phase=='build':build()
    elif args.phase=='benchmark':benchmark()
    else:isolated(args.archive,args.extraction.resolve())


if __name__=='__main__':main()
