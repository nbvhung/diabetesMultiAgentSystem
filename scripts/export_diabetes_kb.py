"""Export the actual verified KB. No network, database writes or model training."""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.app.research.corpus import Corpus
from backend.app.research.kb_export import export

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, default=ROOT / 'kb_diabetes.cypher')
    args = parser.parse_args()
    result = export(Corpus(), args.output)
    args.output.with_suffix('.manifest.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result, indent=2))
