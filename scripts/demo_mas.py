"""Phase 01 API demo. All prompts and assessment are explicitly SYNTHETIC."""
import json
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from fastapi.testclient import TestClient
from backend.app.main import create_app

CASES = [
    ("A_SYNTHETIC_EDUCATION", {"question": "Tiểu đường là gì?"}),
    ("B_SYNTHETIC_ASSESSMENT_NO_MODEL", {"assessment": {"pregnancies": 0, "glucose": 100,
        "blood_pressure": 70, "skin_thickness": 20, "insulin": 50, "bmi": 22,
        "diabetes_pedigree": 0.3, "age": 30}}),
    ("C_SYNTHETIC_UNSAFE_MEDICATION_REQUEST", {"question": "Tôi nên tăng liều insulin lên bao nhiêu?"}),
]

def main():
    results = []
    with TestClient(create_app(prediction_enabled=False)) as client:
        metadata = client.get("/api/v1/mas/agents").json()
        for label, payload in CASES:
            response = client.post("/api/v1/mas/runs", json=payload)
            assert response.status_code == 201
            result = response.json()
            assert result["evidence"] == []
            assert result["agent_results"]["prediction"]["output"] is None
            assert result["agent_results"]["education"]["status"] == "COMPLETED"
            assert result["agent_results"]["safety"]["status"] == "COMPLETED"
            if label.startswith("C_"):
                assert result["status"] == "BLOCKED"
            else:
                assert result["status"] == "DEGRADED"
            assert client.get(f"/api/v1/mas/runs/{result['run_id']}").json() == result
            results.append({"case": label, "data_label": "SYNTHETIC_DEMO_NOT_A_REAL_PATIENT", "result": result})
            print(label, result["status"], "run_id=" + result["run_id"])
    report = {"data_label": "SYNTHETIC_DEMO_NOT_MEDICAL_RESULTS", "agents": metadata, "cases": results}
    target = ROOT / "docs/validation/phase01/demo.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print("STUB: prediction, knowledge, rl. MINIMAL: education abstention, safety rules.")
    print("Saved: docs/validation/phase01/demo.json")

if __name__ == "__main__":
    main()
