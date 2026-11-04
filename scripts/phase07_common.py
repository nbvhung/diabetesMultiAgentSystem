"""Shared provenance and artifact writer. No sample metrics or silent synthetic tools."""
from pathlib import Path
from datetime import datetime, timezone
import csv, hashlib, json, platform, subprocess, sys
import importlib.metadata

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
RES = ROOT / 'experiments/results'
FIG = ROOT / 'experiments/figures'
SEED = 42


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def source_version():
    files = []
    for folder in ('backend', 'scripts', 'frontend/src', 'frontend/e2e', 'experiments/configs'):
        files.extend(p for p in (ROOT / folder).rglob('*') if p.is_file() and p.suffix in {'.py', '.tsx', '.ts', '.css', '.json'} and '__pycache__' not in p.parts)
    files.extend(ROOT / p for p in ('pyproject.toml', 'frontend/package.json', 'frontend/package-lock.json', 'frontend/vite.config.ts', 'frontend/vitest.config.ts', 'frontend/playwright.config.ts', 'frontend/tsconfig.json'))
    checksums = {p.relative_to(ROOT).as_posix(): sha(p) for p in sorted(set(files)) if p.exists()}
    digest = hashlib.sha256(json.dumps(checksums, sort_keys=True).encode()).hexdigest()
    git = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=ROOT, capture_output=True, text=True)
    return 'source-sha256:' + digest, git.stdout.strip() if git.returncode == 0 else None, checksums


def save(name, summary, rows, scope, *, datasets, config, seed=SEED, extra=None):
    RES.mkdir(parents=True, exist_ok=True)
    FIG.mkdir(parents=True, exist_ok=True)
    report = {'scope': scope, 'summary': summary, 'rows': rows, **(extra or {})}
    path = RES / f'{name}.json'
    path.write_text(json.dumps(report, indent=2, allow_nan=False), encoding='utf-8')
    for suffix, records in [('', summary), ('_rows', rows)]:
        target = RES / f'{name}{suffix}.csv'
        keys = list(dict.fromkeys(k for row in records for k in row))
        with target.open('w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=keys)
            writer.writeheader()
            for row in records:
                writer.writerow({k: json.dumps(v, sort_keys=True) if isinstance(v, (dict, list)) else v for k, v in row.items()})
    version, commit, source_hashes = source_version()
    outputs = [path, RES / f'{name}.csv', RES / f'{name}_rows.csv']
    if (FIG / f'{name}.png').exists(): outputs.append(FIG / f'{name}.png')
    manifest = {'experiment': name, 'status': 'measured', 'timestamp': datetime.now(timezone.utc).isoformat(),
                'code_version': version, 'git_commit': commit, 'source_files': source_hashes,
                'config': config, 'dataset_version': {p: sha(ROOT / p) for p in datasets}, 'seed': seed,
                'environment': {'python': platform.python_version(), **{name:importlib.metadata.version(name) for name in ['torch','scikit-learn','numpy','pandas','matplotlib','fastapi','sqlalchemy','neo4j','psycopg']}},
                'outputs': {p.relative_to(ROOT).as_posix(): sha(p) for p in outputs}}
    (RES / f'{name}.manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    print(json.dumps({'experiment': name, 'summary': summary}, indent=2), flush=True)
    return report


def plot_bars(name, summary, label, metrics, title):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import numpy as np
    FIG.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(1, len(metrics), figsize=(max(7, len(metrics) * 4), 4), squeeze=False)
    for ax, metric in zip(axes[0], metrics):
        values = [row[metric] for row in summary]
        ax.bar(np.arange(len(summary)), values, color=['#3e8065', '#95b795', '#d4b770', '#b38d7c'][:len(summary)])
        ax.set_xticks(range(len(summary)), [row[label] for row in summary], rotation=15, ha='right', fontsize=8)
        ax.set_title(metric.replace('_', ' '), fontsize=10)
        ax.grid(axis='y', alpha=.15)
        ax.set_axisbelow(True)
    fig.suptitle(title, fontsize=11)
    fig.tight_layout()
    fig.savefig(FIG / f'{name}.png', dpi=150)
    plt.close(fig)


def dataset_scenarios():
    return json.loads((ROOT / 'experiments/configs/phase07_scenarios.json').read_text(encoding='utf-8'))['scenarios']


class UnavailableGraph:
    """Explicit fault injection, never used as the normal retrieval backend."""
    def candidates(self, *args):
        from backend.app.knowledge.store import KnowledgeUnavailable
        raise KnowledgeUnavailable('SYNTHETIC_NEO4J_OUTAGE')
    def summary(self):
        from backend.app.knowledge.store import KnowledgeUnavailable
        raise KnowledgeUnavailable('SYNTHETIC_NEO4J_OUTAGE')


SYNTHETIC = dict(pregnancies=0, glucose=100, blood_pressure=70, skin_thickness=20,
                 insulin=50, bmi=22, diabetes_pedigree=.3, age=30)


def make_registry(model, graph, policy, repository):
    from backend.app.mas.registry import AgentRegistry
    from backend.app.mas.agents.prediction import PredictionAgent
    from backend.app.mas.agents.knowledge import KnowledgeAgent, EducationAgent
    from backend.app.mas.agents.rl_decision import RLDecisionAgent
    from backend.app.mas.agents.safety import SafetyAgent
    from backend.app.rag.retrieval import Retrieval
    registry = AgentRegistry()
    for agent in (PredictionAgent(model, repository), KnowledgeAgent(Retrieval(graph)), RLDecisionAgent(policy), EducationAgent(), SafetyAgent()):
        registry.register(agent)
    return registry


def admitted(evidence):
    from backend.app.knowledge.store import documents
    corpus = {c['id']: c for c in documents()}
    return all(e.evidence_id in corpus and all(getattr(e, key) == corpus[e.evidence_id][field] for key, field in [('excerpt','text'), ('source_title','title'), ('publisher','publisher'), ('section','section')]) and str(e.source_url) == corpus[e.evidence_id]['url'] for e in evidence)
