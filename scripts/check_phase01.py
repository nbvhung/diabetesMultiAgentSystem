"""Phase 01 verification; captures actual commands without overwriting Phase 00 logs."""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
LOG = ROOT / "docs/validation/phase01"
LOG.mkdir(parents=True, exist_ok=True)
results = {}
def run(name, command, cwd=ROOT):
    completed = subprocess.run(command, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    (LOG / f"{name}.log").write_text("UTC: " + datetime.now(timezone.utc).isoformat() + "\nCOMMAND: " + subprocess.list2cmdline(command) + "\nEXIT_CODE: " + str(completed.returncode) + "\n" + completed.stdout + completed.stderr, encoding="utf-8")
    results[name] = completed.returncode == 0
    print(name, "PASS" if results[name] else "FAIL", flush=True)

run("pytest", [sys.executable, "-m", "pytest", "backend/tests", "-v"])
run("demo", [sys.executable, "scripts/demo_mas.py"])
run("structure_env", [sys.executable, "scripts/verify_phase00.py"])
run("frontend_build", ["npm.cmd" if os.name == "nt" else "npm", "run", "build"], ROOT / "frontend")

with socket.socket() as sock:
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
base = f"http://127.0.0.1:{port}"
with (LOG / "uvicorn.log").open("w", encoding="utf-8") as stream:
    command = [sys.executable, "-m", "uvicorn", "backend.app.main:app", "--host", "127.0.0.1", "--port", str(port)]
    stream.write("COMMAND: " + subprocess.list2cmdline(command) + "\n")
    stream.flush()
    process = subprocess.Popen(command, cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT)
    try:
        def get(path):
            with urlopen(base + path, timeout=3) as response:
                assert response.status == 200
                return json.load(response)
        deadline = time.monotonic() + 15
        while True:
            try:
                health = get("/health")
                assert health["status"] == "ok" and health["phase"] == "01"
                break
            except Exception:
                if time.monotonic() >= deadline or process.poll() is not None:
                    raise
                time.sleep(0.2)
        agents = get("/api/v1/mas/agents")
        assert len(agents["agents"]) == 5
        capabilities = get("/api/v1/system/capabilities")
        assert capabilities["components"]["coordinator"] == "available"
        body = json.dumps({"question": "Synthetic demo: what is diabetes?"}).encode("utf-8")
        request = Request(base + "/api/v1/mas/runs", data=body, headers={"Content-Type": "application/json"}, method="POST")
        with urlopen(request, timeout=5) as response:
            assert response.status == 201
            result = json.load(response)
        assert result["status"] == "DEGRADED" and result["evidence"] == []
        assert get(f"/api/v1/mas/runs/{result['run_id']}") == result
        trace = get(f"/api/v1/mas/runs/{result['run_id']}/trace")
        assert trace["agent_trace"] == result["agent_trace"]
        (LOG / "live_http.json").write_text(json.dumps({"data_label": "SYNTHETIC_HTTP_CHECK", "health": health,
            "capabilities": capabilities, "run": result, "trace": trace, "agent_count": len(agents["agents"])}, ensure_ascii=False, indent=2), encoding="utf-8")
        results["live_http"] = True
    except Exception as exc:
        results["live_http"] = False
        (LOG / "live_http_error.log").write_text(str(exc), encoding="utf-8")
    finally:
        process.terminate()
        process.wait(timeout=10)
print("live_http", "PASS" if results["live_http"] else "FAIL", flush=True)
(LOG / "results.json").write_text(json.dumps({"captured_at_utc": datetime.now(timezone.utc).isoformat(), "checks": results}, indent=2), encoding="utf-8")
sys.exit(0 if all(results.values()) else 1)
