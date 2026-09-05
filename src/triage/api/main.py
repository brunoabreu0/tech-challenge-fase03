"""FastAPI application for the medical triage NLP service."""

import logging
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator

from fastapi import FastAPI, HTTPException, Request, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from triage.api.metrics import (
    ERROR_COUNT,
    PREDICTION_COUNT,
    PREDICTION_LATENCY,
    REQUEST_COUNT,
    REQUEST_LATENCY,
)
from triage.api.schemas import HealthResponse, PredictRequest, PredictResponse
from triage.data.loader import LABEL_NAMES
from triage.data.preprocessor import clean_text
from triage.model.base import BaseClassifier
from triage.model.factory import ClassifierFactory
from triage.settings import get_settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Global classifier instance (loaded at startup)
# ---------------------------------------------------------------------------
_classifier: BaseClassifier | None = None
_model_name: str = "unknown"


def _load_classifier() -> tuple[BaseClassifier, str]:
    """Load the best available classifier.

    Tries ONNX first (faster), falls back to sklearn, then trains from scratch.

    Returns:
        Tuple of (classifier instance, model name string).
    """
    settings = get_settings()
    onnx_path = settings.model_dir / "classifier.onnx"
    sklearn_path = settings.model_dir / "classifier.joblib"

    if onnx_path.exists():
        logger.info("Loading ONNX model from %s", onnx_path)
        return ClassifierFactory.load("onnx", onnx_path), "onnx"

    if sklearn_path.exists():
        logger.info("Loading sklearn model from %s", sklearn_path)
        return ClassifierFactory.load("tfidf_lr", sklearn_path), "tfidf_lr"

    # Train a quick model on synthetic data so the API starts even without models
    logger.warning(
        "No pre-trained model found. Training on synthetic data for demo purposes. "
        "Run scripts/train.py for a proper model."
    )
    from triage.data.loader import generate_synthetic_dataset
    from triage.data.preprocessor import preprocess_texts

    df = generate_synthetic_dataset(n_samples=1500, random_seed=settings.random_seed)
    texts = preprocess_texts(df["text"].tolist())
    labels = df["label"].tolist()

    clf = ClassifierFactory.create("tfidf_lr")
    clf.fit(texts, labels)

    # Persist for next startup
    settings.model_dir.mkdir(parents=True, exist_ok=True)
    clf.save(settings.model_dir / "classifier.joblib")
    return clf, "tfidf_lr (synthetic)"


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Load the ML model on startup and free resources on shutdown."""
    global _classifier, _model_name
    logger.info("Starting Medical Triage API — loading classifier ...")
    _classifier, _model_name = _load_classifier()
    logger.info("Classifier ready: %s", _model_name)
    yield
    logger.info("Shutting down Medical Triage API.")
    _classifier = None


# ---------------------------------------------------------------------------
# FastAPI application
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Medical Triage NLP API",
    description=(
        "Automatic classification of medical reports (laudos médicos) into urgency levels: "
        "**normal**, **atencao** (attention), or **urgente** (urgent). "
        "\n\n"
        "Part of the FIAP Pós-Tech 9MLET — Tech Challenge Fase 3."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)


# ---------------------------------------------------------------------------
# Middleware — latency and request count tracking
# ---------------------------------------------------------------------------
@app.middleware("http")
async def metrics_middleware(request: Request, call_next) -> Response:
    """Record per-request latency and count metrics."""
    start = time.perf_counter()
    response = await call_next(request)
    duration = time.perf_counter() - start

    endpoint = request.url.path
    method = request.method
    status = str(response.status_code)

    REQUEST_COUNT.labels(method=method, endpoint=endpoint, http_status=status).inc()
    REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(duration)

    return response


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    tags=["System"],
)
async def health() -> HealthResponse:
    """Return the current health status of the API."""
    return HealthResponse(
        status="ok",
        model_loaded=_classifier is not None,
        model_name=_model_name,
    )


@app.post(
    "/predict",
    response_model=PredictResponse,
    summary="Classify medical report urgency",
    tags=["Triage"],
)
async def predict(request: PredictRequest) -> PredictResponse:
    """Classify a medical report text into an urgency level.

    - **normal** (0): No immediate action required.
    - **atencao** (1): Requires follow-up or monitoring.
    - **urgente** (2): Requires immediate medical attention.
    """
    if _classifier is None:
        ERROR_COUNT.labels(endpoint="/predict").inc()
        raise HTTPException(status_code=503, detail="Model not loaded.")

    try:
        cleaned = clean_text(request.text)

        start = time.perf_counter()
        with PREDICTION_LATENCY.time():
            proba_list = _classifier.predict_proba([cleaned])
        inference_ms = (time.perf_counter() - start) * 1000

        proba = proba_list[0]
        label_id = int(max(range(len(proba)), key=lambda i: proba[i]))
        label_name = LABEL_NAMES[label_id]
        confidence = float(proba[label_id])

        PREDICTION_COUNT.labels(predicted_label=label_name).inc()

        return PredictResponse(
            label=label_name,
            label_id=label_id,
            confidence=round(confidence, 4),
            latency_ms=round(inference_ms, 3),
            model=_model_name,
        )

    except Exception as exc:
        logger.exception("Error during prediction: %s", exc)
        ERROR_COUNT.labels(endpoint="/predict").inc()
        raise HTTPException(status_code=500, detail=f"Prediction error: {exc}") from exc


@app.get(
    "/metrics",
    summary="Prometheus metrics",
    tags=["System"],
    response_class=Response,
)
async def metrics() -> Response:
    """Expose Prometheus metrics for scraping."""
    data = generate_latest()
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)
