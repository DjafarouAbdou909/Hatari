import joblib
import pandas as pd
import pytest
from fastapi.testclient import TestClient

from hatari.api import app as api
from hatari.models.train import MODEL_FILE, fit
from hatari.service.analyzer import Analyzer, ModelNotFound


@pytest.fixture(scope="module")
def small_analyzer(tmp_path_factory):
    suspicious = [f"You won {i}000 pounds, send the fee now and call 0800{i:06d}" for i in range(15)]
    legitimate = [f"See you at {i} for lunch with the team" for i in range(15)]
    frame = pd.DataFrame({"text": suspicious + legitimate, "suspicious": [True] * 15 + [False] * 15,
                          "language": "en", "group": [f"s{i}" for i in range(15)] + [f"l{i}" for i in range(15)]})
    directory = tmp_path_factory.mktemp("models")
    joblib.dump(fit(frame), directory / MODEL_FILE)
    return Analyzer(directory)


@pytest.fixture
def client(small_analyzer, monkeypatch):
    monkeypatch.setattr(api, "get_analyzer", lambda: small_analyzer)
    return TestClient(api.app)


def test_health_reports_a_loaded_model(client):
    assert client.get("/health").json() == {"status": "ok", "model_loaded": True}


def test_analyze_returns_the_four_parts(client):
    response = client.post("/analyze", json={"message": "You won 5000 pounds, send the fee now and call 08001234567"})
    assert response.status_code == 200
    body = response.json()
    assert {"risk", "model", "signals", "categories", "explanation", "recommendations", "warnings"} == set(body)
    assert 0 <= body["risk"]["score"] <= 100
    assert all(signal["evidence"] for signal in body["signals"])


@pytest.mark.parametrize("payload", [{}, {"message": ""}, {"message": "   "}, {"message": "a" * 5001}, {"message": 12}])
def test_invalid_messages_are_rejected(client, payload):
    assert client.post("/analyze", json=payload).status_code == 422


def test_missing_model_gives_503(monkeypatch):
    def missing():
        raise ModelNotFound("absent")

    monkeypatch.setattr(api, "get_analyzer", missing)
    test_client = TestClient(api.app)
    assert test_client.post("/analyze", json={"message": "hello there"}).status_code == 503
    assert test_client.get("/health").json() == {"status": "degraded", "model_loaded": False}
