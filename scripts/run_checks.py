"""Run Phase 00 checks and capture actual output; exit nonzero on failure."""
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
LOG = ROOT / "docs" / "validation"
LOG.mkdir(parents=True, exist_ok=True)
results = {}
def run(name, args, cwd=ROOT):
    result = subprocess.run(args, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    (LOG / f"{name}.log").write_text("COMMAND: " + subprocess.list2cmdline(args) + "\nEXIT_CODE: " + str(result.returncode) + "\n" + result.stdout + result.stderr, encoding="utf-8")
    results[name] = result.returncode == 0
    print(name, "PASS" if results[name] else "FAIL")

run("pytest", [sys.executable, "-m", "pytest", "-v"])
run("structure_env", [sys.executable, "scripts/verify_phase00.py"])
run("alembic_heads", [sys.executable, "-m", "alembic", "heads"])
run("db_import", [sys.executable, "-c", "from backend.app.db.session import Base, engine; print('PASS: lazy engine imports; no business tables:', len(Base.metadata.tables)); engine.dispose()"])
run("frontend_build", ["npm.cmd" if os.name == "nt" else "npm", "run", "build"], ROOT / "frontend")
run("versions", [sys.executable, "-c", "import platform,importlib.metadata as m; print(platform.python_version()); print({n:m.version(n) for n in ['fastapi','pydantic','pytest','SQLAlchemy','alembic','psycopg']})"])
# Use an ephemeral loopback port and own only the child process we launch.
with socket.socket() as sock:
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
with (LOG / "uvicorn.log").open("w", encoding="utf-8") as stream:
    process = subprocess.Popen([sys.executable, "-m", "uvicorn", "backend.app.main:app", "--host", "127.0.0.1", "--port", str(port)], cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT)
    try:
        deadline = time.monotonic() + 15
        while True:
            try:
                with urlopen(f"http://127.0.0.1:{port}/health", timeout=1) as response:
                    health = json.load(response)
                    assert response.status == 200 and health["status"] == "ok"
                break
            except Exception:
                if time.monotonic() >= deadline or process.poll() is not None:
                    raise
                time.sleep(0.2)
        with urlopen(f"http://127.0.0.1:{port}/api/v1/system/capabilities", timeout=2) as response:
            capabilities = json.load(response)
            assert capabilities["components"]["prediction_agent"] == "stub"
        (LOG / "live_http.json").write_text(json.dumps({"health": health, "capabilities": capabilities}, indent=2), encoding="utf-8")
        results["live_http"] = True
    except Exception as exc:
        results["live_http"] = False
        (LOG / "live_http_error.log").write_text(str(exc), encoding="utf-8")
    finally:
        process.terminate()
        process.wait(timeout=10)
print("live_http", "PASS" if results["live_http"] else "FAIL")
(LOG / "results.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
sys.exit(0 if all(results.values()) else 1)
