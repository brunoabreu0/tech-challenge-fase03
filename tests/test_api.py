"""Tests for the FastAPI medical triage inference API."""

import pytest
from fastapi.testclient import TestClient

import triage.api.main as api_module
from triage.data.loader import generate_synthetic_dataset
from triage.data.preprocessor import preprocess_texts
from triage.model.factory import ClassifierFactory


@pytest.fixture(autouse=True)
def inject_classifier() -> None:
    """Pre-load a trained classifier into the API module for all tests."""
    df = generate_synthetic_dataset(n_samples=90, random_seed=42)
    texts = preprocess_texts(df["text"].tolist())
    labels = df["label"].tolist()
    clf = ClassifierFactory.create("tfidf_lr")
    clf.fit(texts, labels)
    api_module._classifier = clf
    api_module._model_name = "tfidf_lr (test)"
    yield
    api_module._classifier = None
    api_module._model_name = "unknown"


@pytest.fixture
def client() -> TestClient:
    """Return a TestClient with the FastAPI app."""
    return TestClient(api_module.app)


def test_health_endpoint_returns_200(client: TestClient) -> None:
    """GET /health should return 200 OK."""
    response = client.get("/health")
    assert response.status_code == 200


def test_health_response_structure(client: TestClient) -> None:
    """GET /health should return expected JSON structure."""
    response = client.get("/health")
    data = response.json()
    assert "status" in data
    assert "model_loaded" in data
    assert "model_name" in data
    assert data["status"] == "ok"


def test_predict_endpoint_returns_200(client: TestClient) -> None:
    """POST /predict with valid text should return 200."""
    response = client.post(
        "/predict",
        json={"text": "paciente com dor toracica severa"},
    )
    assert response.status_code == 200


def test_predict_response_structure(client: TestClient) -> None:
    """POST /predict should return correct response schema."""
    response = client.post(
        "/predict",
        json={"text": "exame de rotina sem alteracoes"},
    )
    data = response.json()
    assert "label" in data
    assert "label_id" in data
    assert "confidence" in data
    assert "latency_ms" in data
    assert "model" in data


def test_predict_label_is_valid(client: TestClient) -> None:
    """Predicted label should be one of the three valid urgency levels."""
    response = client.post(
        "/predict",
        json={"text": "paciente urgente hemorragia grave"},
    )
    data = response.json()
    assert data["label"] in {"normal", "atencao", "urgente"}


def test_predict_label_id_is_valid(client: TestClient) -> None:
    """Predicted label_id should be 0, 1, or 2."""
    response = client.post(
        "/predict",
        json={"text": "pressao alta necessita acompanhamento"},
    )
    data = response.json()
    assert data["label_id"] in {0, 1, 2}


def test_predict_confidence_in_range(client: TestClient) -> None:
    """Confidence should be between 0.0 and 1.0."""
    response = client.post(
        "/predict",
        json={"text": "paciente estavel sem queixas"},
    )
    data = response.json()
    assert 0.0 <= data["confidence"] <= 1.0


def test_predict_empty_text_returns_422(client: TestClient) -> None:
    """POST /predict with empty text should return 422 Unprocessable Entity."""
    response = client.post("/predict", json={"text": ""})
    assert response.status_code == 422


def test_predict_missing_text_returns_422(client: TestClient) -> None:
    """POST /predict without text field should return 422."""
    response = client.post("/predict", json={})
    assert response.status_code == 422


def test_metrics_endpoint_returns_200(client: TestClient) -> None:
    """GET /metrics should return 200 with Prometheus text format."""
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "text/plain" in response.headers["content-type"]


def test_metrics_contains_prometheus_data(client: TestClient) -> None:
    """GET /metrics should contain Prometheus metric names."""
    # Make a prediction first to generate metrics
    client.post("/predict", json={"text": "dor toracica"})
    response = client.get("/metrics")
    content = response.text
    assert "triage_api" in content


def test_openapi_docs_available(client: TestClient) -> None:
    """GET /docs should return 200 (OpenAPI Swagger UI)."""
    response = client.get("/docs")
    assert response.status_code == 200
