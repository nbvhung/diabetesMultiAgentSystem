"""Export training-range serving metadata without fitting or training."""
from pathlib import Path
import sys,json
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from backend.app.ml.pipeline import ART,RES,FEATURES,VERSION,load_data,sha,save_json
config=json.loads((ART/'preprocessing_config.json').read_text())
assert sha(ART.parents[2]/'data/raw/pima.csv')==config['dataset_sha256']
splits=json.loads((RES/'splits.json').read_text()); df=load_data().iloc[splits['train']]
save_json(ART/'serving.json',{'model_version':VERSION,'features':FEATURES,'training_bounds':{c:[float(df[c].min()),float(df[c].max())] for c in FEATURES},'training_split_sha256':sha(RES/'splits.json'),'manifest_sha256':sha(ART/'manifest.json')})
print('Prepared serving.json from frozen training split; no fit/training performed.')
