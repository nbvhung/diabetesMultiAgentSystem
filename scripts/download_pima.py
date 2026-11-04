"""Download public historical research data, never substitute synthetic training data."""
from pathlib import Path
import hashlib
from urllib.request import urlopen
ROOT=Path(__file__).resolve().parents[1]
URL='https://raw.githubusercontent.com/jbrownlee/Datasets/master/pima-indians-diabetes.data.csv'
EXPECTED='6bfe5d0f379d17a0e0819b996407e3c09bf80febd4287f2ed212190dfff154af'
data=urlopen(URL,timeout=30).read()
if hashlib.sha256(data).hexdigest()!=EXPECTED: raise RuntimeError('Source changed; review provenance, do not silently replace')
p=ROOT/'data/raw/pima.csv'; p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
print('Verified standard Pima CSV SHA256:',EXPECTED)
