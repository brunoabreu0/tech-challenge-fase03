"""Tests for the FastAPI medical triage inference API."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import triage.api.main as api_module
from triage.data.loader import generate_synthetic_dataset
from triage.data.preprocessor import preprocess_texts
from triage.model.exporter import export_to_onnx
from triage.model.factory import ClassifierFactory
from triage.model.tfidf_lr import TFIDFLogisticClassifier
from triage.settings import Settings


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
    assert data["model_loaded"] is True


def test_predict_endpoint_returns_200(client: TestClient) -> None:
    """POST /predict with valid input should return 200 OK."""
    response = client.post(
        "/predict",
        json={"text": "Paciente com dor torácica aguda e sudorese intensa."},
    )
    assert response.status_code == 200


def test_predict_response_structure(client: TestClient) -> None:
    """POST /predict should return expected schema."""
    response = client.post(
        "/predict",
        json={"text": "Paciente com cefaleia leve há duas semanas."},
    )
    data = response.json()
    assert "label" in data
    assert "label_id" in data
    assert "confidence" in data
    assert "latency_ms" in data
    assert "model" in data


def test_predict_label_is_valid(client: TestClient) -> None:
    """Predicted label should be one of the three clinical urgency classes."""
    response = client.post(
        "/predict",
        json={"text": "Febre alta súbita com confusão mental."},
    )
    data = response.json()
    assert data["label"] in {"normal", "atencao", "urgente"}


def test_predict_label_id_is_valid(client: TestClient) -> None:
    """Predicted label_id should be in {0, 1, 2}."""
    response = client.post(
        "/predict",
        json={"text": "Retorno de rotina para avaliação de exames normais."},
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


def test_predict_when_classifier_is_not_loaded(client: TestClient) -> None:
    """POST /predict should return 503 if model is not loaded."""
    api_module._classifier = None
    response = client.post("/predict", json={"text": "dor no peito"})
    assert response.status_code == 503
    assert "Model not loaded" in response.json()["detail"]


def test_metrics_endpoint_returns_200(client: TestClient) -> None:
    """GET /metrics should return 200 with Prometheus text format."""
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "text/plain" in response.headers["content-type"]


def test_metrics_contains_prometheus_data(client: TestClient) -> None:
    """GET /metrics should contain Prometheus metric names."""
    client.post("/predict", json={"text": "dor toracica"})
    response = client.get("/metrics")
    content = response.text
    assert "triage_api" in content


def test_openapi_docs_available(client: TestClient) -> None:
    """GET /docs should return 200 (OpenAPI Swagger UI)."""
    response = client.get("/docs")
    assert response.status_code == 200


def test_load_classifier_prefers_onnx(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """_load_classifier should load ONNX model first if present."""
    # Create fake onnx model
    df = generate_synthetic_dataset(n_samples=60, random_seed=42)
    clf = TFIDFLogisticClassifier()
    clf.fit(preprocess_texts(df["text"].tolist()), df["label"].tolist())

    joblib_path = tmp_path / "classifier.joblib"
    onnx_path = tmp_path / "classifier.onnx"
    clf.save(joblib_path)
    export_to_onnx(joblib_path, onnx_path)

    custom_settings = Settings(model_dir=tmp_path)
    monkeypatch.setattr(api_module, "get_settings", lambda: custom_settings)

    model, name = api_module._load_classifier()
    assert name == "onnx"
    assert model is not None


def test_load_classifier_fallback_to_sklearn(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """_load_classifier should load sklearn joblib if onnx is missing."""
    df = generate_synthetic_dataset(n_samples=60, random_seed=42)
    clf = TFIDFLogisticClassifier()
    clf.fit(preprocess_texts(df["text"].tolist()), df["label"].tolist())

    joblib_path = tmp_path / "classifier.joblib"
    clf.save(joblib_path)

    custom_settings = Settings(model_dir=tmp_path)
    monkeypatch.setattr(api_module, "get_settings", lambda: custom_settings)

    model, name = api_module._load_classifier()
    assert name == "tfidf_lr"
    assert model is not None


def test_load_classifier_trains_synthetic_if_empty(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """_load_classifier should train and save synthetic model if empty."""
    custom_settings = Settings(model_dir=tmp_path / "empty_models")
    monkeypatch.setattr(api_module, "get_settings", lambda: custom_settings)

    model, name = api_module._load_classifier()
    assert "synthetic" in name
    assert (custom_settings.model_dir / "classifier.joblib").exists()


@pytest.mark.anyio
async def test_lifespan_context_manager() -> None:
    """Lifespan should load model at enter and clear at exit."""
    async with api_module.lifespan(api_module.app):
        assert api_module._classifier is not None
    assert api_module._classifier is None
