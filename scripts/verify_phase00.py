"""Structural and placeholder check; no clinical or runtime integration claims."""
from pathlib import Path
import re
ROOT = Path(__file__).resolve().parents[1]
required = ["AGENTS.md", "README.md", ".gitignore", ".env.example", "pyproject.toml",
    "backend/app/main.py", "backend/app/core", "backend/app/api", "backend/app/schemas",
    "backend/app/db", "backend/app/mas/coordinator.py", "backend/app/mas/state.py",
    "backend/app/mas/messages.py", "backend/app/mas/registry.py", "backend/app/mas/agents",
    "backend/app/ml", "backend/app/knowledge", "backend/app/rag", "backend/app/rl",
    "backend/app/rules", "backend/app/observability", "backend/tests", "frontend/src",
    "frontend/package.json", "notebooks", "data/raw", "data/processed", "data/synthetic",
    "artifacts/models", "artifacts/policies", "experiments/configs", "experiments/results",
    "experiments/figures", "scripts", "infra/docker", "docs/architecture.md",
    "docs/agent_contracts.md", "docs/phase_status.md", "docs/requirements_traceability.md", "docs/decisions"]
for item in required:
    assert (ROOT / item).exists(), item
entries = dict(line.split("=", 1) for line in (ROOT / ".env.example").read_text().splitlines() if "=" in line)
for key, value in entries.items():
    if any(word in key for word in ("PASSWORD", "SECRET", "TOKEN", "KEY")):
        assert value.startswith("REPLACE_"), key
assert "REPLACE_USER:REPLACE_PASSWORD" in entries["DATABASE_URL"]
text = (ROOT / ".env.example").read_text()
assert not re.search(r"-----BEGIN .*PRIVATE KEY-----|sk-[A-Za-z0-9]{20,}|AKIA[A-Z0-9]{16}", text)
print(f"PASS: {len(required)} required paths; environment placeholders only. This is not a general secret audit.")
