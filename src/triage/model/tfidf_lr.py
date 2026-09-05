"""TF-IDF + Logistic Regression sklearn pipeline for medical text classification."""

import logging
from pathlib import Path

import joblib
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

from triage.model.base import BaseClassifier

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Default hyperparameters (tuned for 3-class medical text classification)
# ---------------------------------------------------------------------------
DEFAULT_TFIDF_PARAMS: dict = {
    "max_features": 20_000,
    "ngram_range": (1, 2),
    "sublinear_tf": True,
    "min_df": 2,
}

DEFAULT_LR_PARAMS: dict = {
    "C": 5.0,
    "max_iter": 1000,
    "solver": "lbfgs",
    "random_state": 42,
}


class TFIDFLogisticClassifier(BaseClassifier):
    """Text classifier using TF-IDF vectorisation and Logistic Regression.

    This is a lightweight, interpretable baseline suitable for medical text
    classification tasks. It uses a sklearn Pipeline which makes it easy to
    serialise with joblib and convert to ONNX.

    Labels:
        0 = normal
        1 = atencao
        2 = urgente
    """

    def __init__(
        self,
        tfidf_params: dict | None = None,
        lr_params: dict | None = None,
    ) -> None:
        """Initialise the TF-IDF + LR pipeline.

        Args:
            tfidf_params: Optional overrides for TfidfVectorizer parameters.
            lr_params: Optional overrides for LogisticRegression parameters.
        """
        _tfidf = {**DEFAULT_TFIDF_PARAMS, **(tfidf_params or {})}
        _lr = {**DEFAULT_LR_PARAMS, **(lr_params or {})}

        self.pipeline = Pipeline(
            steps=[
                ("tfidf", TfidfVectorizer(**_tfidf)),
                ("clf", LogisticRegression(**_lr)),
            ]
        )
        self._is_fitted = False

    def fit(self, texts: list[str], labels: list[int]) -> "TFIDFLogisticClassifier":
        """Train the TF-IDF + LR pipeline.

        Args:
            texts: List of medical report texts (preprocessed).
            labels: Integer urgency labels.

        Returns:
            Self (fitted), for method chaining.
        """
        logger.info("Fitting TF-IDF + LR pipeline on %d samples...", len(texts))
        self.pipeline.fit(texts, labels)
        self._is_fitted = True
        logger.info("Pipeline fitted successfully.")
        return self

    def predict(self, texts: list[str]) -> list[int]:
        """Predict urgency labels.

        Args:
            texts: List of medical report texts.

        Returns:
            List of predicted labels as Python ints.
        """
        self._check_fitted()
        return self.pipeline.predict(texts).tolist()

    def predict_proba(self, texts: list[str]) -> list[list[float]]:
        """Return class probability estimates.

        Args:
            texts: List of medical report texts.

        Returns:
            List of probability vectors [[p0, p1, p2], ...].
        """
        self._check_fitted()
        return self.pipeline.predict_proba(texts).tolist()

    def save(self, path: Path) -> None:
        """Serialise the fitted pipeline to disk using joblib.

        Args:
            path: Target .joblib file path.
        """
        self._check_fitted()
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self.pipeline, path)
        logger.info("Model saved to %s", path)

    @classmethod
    def load(cls, path: Path) -> "TFIDFLogisticClassifier":
        """Load a serialised pipeline from disk.

        Args:
            path: Source .joblib file path.

        Returns:
            Loaded TFIDFLogisticClassifier instance.

        Raises:
            FileNotFoundError: If the model file does not exist.
        """
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Model file not found: {path}")

        instance = cls.__new__(cls)
        instance.pipeline = joblib.load(path)
        instance._is_fitted = True
        logger.info("Model loaded from %s", path)
        return instance

    def get_feature_names(self) -> list[str]:
        """Return the TF-IDF vocabulary feature names.

        Returns:
            List of feature name strings.
        """
        self._check_fitted()
        return self.pipeline.named_steps["tfidf"].get_feature_names_out().tolist()

    def get_sklearn_pipeline(self) -> Pipeline:
        """Return the underlying sklearn Pipeline (needed for ONNX export).

        Returns:
            Fitted sklearn Pipeline.
        """
        self._check_fitted()
        return self.pipeline

    def _check_fitted(self) -> None:
        """Raise RuntimeError if the model has not been trained yet."""
        if not self._is_fitted:
            raise RuntimeError(
                "Classifier is not fitted. Call .fit() before making predictions."
            )

    @property
    def classes_(self) -> np.ndarray:
        """Return the class labels seen during fit."""
        self._check_fitted()
        return self.pipeline.named_steps["clf"].classes_
