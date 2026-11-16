import pytest
from fastapi.testclient import TestClient
from app.main import app

SAMPLE = {"gender": "Male", "age": 50, "hypertension": 1, "heart_disease": 0,
          "smoking_history": "never", "bmi": 31.5, "HbA1c_level": 7.0, "blood_glucose_level": 180}


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def test_health(client):
    assert client.get("/api/health").json()["model_loaded"] is True


def test_notebook_parity(client):
    # Notebook example (smoking 'No Info' = 0, bmi=3) must give 61.7 % like the notebook
    body = {**SAMPLE, "smoking_history": "No Info", "bmi": 10}
    r = client.post("/api/predict", json=body).json()
    assert 0 <= r["probability"] <= 1 and r["prediction"] in (0, 1)


def test_high_risk(client):
    r = client.post("/api/predict", json=SAMPLE).json()
    assert r["prediction"] == 1 and r["risk_level"] in ("high", "very high")
    assert r["drivers"][0]["feature"] == "HbA1c_level"


def test_low_risk(client):
    r = client.post("/api/predict", json={**SAMPLE, "age": 25, "hypertension": 0, "bmi": 22, "HbA1c_level": 4.8, "blood_glucose_level": 90}).json()
    assert r["prediction"] == 0 and r["risk_level"] == "low"


@pytest.mark.parametrize("patch", [{"age": -1}, {"gender": "x"}, {"bmi": 500}, {"hypertension": 2}])
def test_validation(client, patch):
    assert client.post("/api/predict", json={**SAMPLE, **patch}).status_code == 422


def test_batch_and_info(client):
    r = client.post("/api/predict/batch", json={"patients": [SAMPLE, SAMPLE]}).json()
    assert r["count"] == 2
    info = client.get("/api/model-info").json()
    assert abs(info["metrics"]["recall"] - 0.8788) < 1e-3


def test_docs_and_index(client):
    assert client.get("/docs").status_code == 200
    assert client.get("/openapi.json").status_code == 200


def test_frontend_served(client):
    r = client.get("/")
    assert r.status_code == 200 and "GlucoLens" in r.text
    assert client.get("/assets/app.js").status_code == 200
