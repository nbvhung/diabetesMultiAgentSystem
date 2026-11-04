"""Execute notebooks in order, then tests; log actual return codes."""
from pathlib import Path
import subprocess,sys,json
ROOT=Path(__file__).resolve().parents[1]
LOG=ROOT/'docs/validation/phase02'; LOG.mkdir(parents=True,exist_ok=True)
checks={}
for name,args in [('notebooks',[sys.executable,'-m','jupyter','nbconvert','--to','notebook','--execute','--inplace',*[f'notebooks/{s}.ipynb' for s in ['01_diabetes_eda_and_split','02_diabetes_dl_training','03_diabetes_model_evaluation']],'--ExecutePreprocessor.timeout=600']),('pytest',[sys.executable,'-m','pytest','backend/tests','-v'])]:
    p=subprocess.run(args,cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace')
    (LOG/(name+'.log')).write_text('COMMAND: '+subprocess.list2cmdline(args)+'\nEXIT_CODE: '+str(p.returncode)+'\n'+p.stdout+p.stderr,encoding='utf-8')
    checks[name]=p.returncode==0; print(name,p.returncode,flush=True)
(LOG/'results.json').write_text(json.dumps(checks,indent=2))
sys.exit(0 if all(checks.values()) else 1)
