"""Read only locally generated, integrity checked Phase 07 experiment artifacts."""
import hashlib
import json
from pathlib import Path
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

ROOT = Path(__file__).resolve().parents[3]
RESULTS = ROOT / 'experiments/results'
FIGURES = ROOT / 'experiments/figures'
NAMES = {'prediction', 'rag', 'mas', 'rl', 'safety', 'e2e', 'diabetes_rag', 'diabetes_mas', 'diabetes_llm', 'diabetes_safety', 'final_mas', 'final_workflows'}
router = APIRouter(prefix='/api/v1/experiments', tags=['experiments'])


def read_report(name):
    if name not in NAMES:
        raise HTTPException(404, 'EXPERIMENT_NOT_FOUND')
    try:
        report = json.loads((RESULTS / f'{name}.json').read_text(encoding='utf-8'))
        manifest = json.loads((RESULTS / f'{name}.manifest.json').read_text(encoding='utf-8'))
        if manifest['status'] != 'measured' or manifest['experiment'] != name:
            raise ValueError('Unmeasured artifact')
        required={f'experiments/results/{name}{suffix}' for suffix in ['.json','.csv','_rows.csv']}
        if not required <= set(manifest['outputs']) or not isinstance(report['summary'],list) or not report['summary']:
            raise ValueError('Incomplete experiment artifact')
        for relative, digest in manifest['outputs'].items():
            path = (ROOT / relative).resolve()
            if not path.is_relative_to(RESULTS.resolve()) and not path.is_relative_to(FIGURES.resolve()):
                raise ValueError('Invalid artifact path')
            if hashlib.sha256(path.read_bytes()).hexdigest() != digest:
                raise ValueError('Artifact modified after evaluation')
        return {'name': name, 'report': report, 'manifest': manifest}
    except (OSError, ValueError, KeyError, TypeError):
        raise HTTPException(503, 'EXPERIMENT_UNAVAILABLE_OR_UNVERIFIED') from None


@router.get('')
def experiments():
    items = []
    for name in sorted(NAMES):
        try:
            items.append(read_report(name))
        except HTTPException:
            items.append({'name': name, 'status': 'unavailable', 'report': None})
    return {'scope': 'Research benchmark; missing results are never imputed', 'experiments': items}


@router.get('/{name}/figure')
def figure(name: str):
    item = read_report(name)
    path = FIGURES / f'{name}.png'
    if f'experiments/figures/{name}.png' not in item['manifest']['outputs']:
        raise HTTPException(404, 'FIGURE_UNAVAILABLE')
    return FileResponse(path, media_type='image/png')
