"""API schemas for request and response validation using Pydantic v2."""

from pydantic import BaseModel, Field


class PredictRequest(BaseModel):
    """Request body for the /predict endpoint."""

    text: str = Field(
        ...,
        min_length=1,
        max_length=10_000,
        description="Medical report text (laudo médico) to classify.",
        examples=["Paciente com dor torácica severa irradiando para o braço esquerdo."],
    )


class PredictResponse(BaseModel):
    """Response body for the /predict endpoint."""

    label: str = Field(
        ...,
        description="Predicted urgency level (normal | atencao | urgente).",
    )
    label_id: int = Field(
        ...,
        description="Integer label (0=normal, 1=atencao, 2=urgente).",
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Model confidence score for the predicted class.",
    )
    latency_ms: float = Field(
        ...,
        description="Inference time in milliseconds.",
    )
    model: str = Field(
        ...,
        description="Name of the model used for inference.",
    )


class HealthResponse(BaseModel):
    """Response body for the /health endpoint."""

    status: str = Field(default="ok")
    model_loaded: bool
    model_name: str
