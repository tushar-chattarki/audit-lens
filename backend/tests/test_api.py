import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add backend directory to sys.path
sys.path.append(str(Path(__file__).parent.parent))

from main import app

client = TestClient(app)

def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "HEALTHY"

def test_get_review_job():
    response = client.get("/api/review/REV-2025-001")
    assert response.status_code == 200
    data = response.json()
    assert data["review_metadata"]["bank_name"] == "GreenPeak Bank Ltd."
    assert data["summary_kpis"]["total_findings"] == 5
    assert len(data["findings"]) == 5

def test_update_reviewer_signoff():
    payload = {
        "reviewer_status": "Accepted",
        "reviewer_comment": "Verified cash mismatch with treasury department."
    }
    response = client.patch("/api/review/REV-2025-001/findings/F-002", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["reviewer_status"] == "Accepted"
    assert data["reviewer_comment"] == "Verified cash mismatch with treasury department."
