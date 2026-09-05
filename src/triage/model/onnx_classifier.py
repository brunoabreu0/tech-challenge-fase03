"""ONNX Runtime wrapper for the exported medical triage classifier."""

import logging
from pathlib import Path

import numpy as np

from triage.model.base import BaseClassifier

logger = logging.getLogger(__name__)


class ONNXClassifier(BaseClassifier):
    """Inference wrapper that runs a pre-exported ONNX model via ONNX Runtime.

    Provides the same BaseClassifier interface as TFIDFLogisticClassifier,
    but uses ONNX Runtime for significantly faster CPU inference.

    Note:
        This class is read-only — it does NOT support training (.fit()).
        Export a trained TFIDFLogisticClassifier to ONNX first using
        ``scripts/export_onnx.py``.
    """

    def __init__(self) -> None:
        """Initialise an empty ONNXClassifier (must call .load() to use)."""
        self._session = None
        self._input_name: str | None = None
        self._label_output_name: str | None = None
        self._proba_output_name: str | None = None

    def fit(self, texts: list[str], labels: list[int]) -> "ONNXClassifier":
        """Not supported for ONNX models.

        Raises:
            NotImplementedError: Always.
        """
        raise NotImplementedError(
            "ONNXClassifier does not support training. "
            "Export a trained TFIDFLogisticClassifier to ONNX first."
        )

    def predict(self, texts: list[str]) -> list[int]:
        """Run inference and return predicted labels.

        Args:
            texts: List of medical report texts.

        Returns:
            List of predicted integer labels.
        """
        self._check_loaded()
        inputs = {self._input_name: np.array(texts)}
        outputs = self._session.run([self._label_output_name], inputs)
        return outputs[0].tolist()

    def predict_proba(self, texts: list[str]) -> list[list[float]]:
        """Return class probability estimates from the ONNX model.

        Args:
            texts: List of medical report texts.

        Returns:
            List of probability vectors.
        """
        self._check_loaded()
        inputs = {self._input_name: np.array(texts)}
        outputs = self._session.run([self._proba_output_name], inputs)
        # ONNX ZipMap output is a list of dicts {label_int: prob}
        proba_dicts: list[dict] = outputs[0]
        return [
            [d.get(k, 0.0) for k in sorted(d.keys())] for d in proba_dicts
        ]

    def save(self, path: Path) -> None:
        """Not supported — ONNX models are saved via the export script.

        Raises:
            NotImplementedError: Always.
        """
        raise NotImplementedError(
            "Use scripts/export_onnx.py to save an ONNX model."
        )

    @classmethod
    def load(cls, path: Path) -> "ONNXClassifier":
        """Load an ONNX model from disk.

        Args:
            path: Path to the .onnx file.

        Returns:
            Loaded ONNXClassifier instance ready for inference.

        Raises:
            FileNotFoundError: If the ONNX file does not exist.
            ImportError: If onnxruntime is not installed.
        """
        try:
            import onnxruntime as rt
        except ImportError as exc:
            raise ImportError(
                "onnxruntime is not installed. Run: pip install onnxruntime"
            ) from exc

        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"ONNX model file not found: {path}")

        instance = cls()
        instance._session = rt.InferenceSession(
            str(path),
            providers=["CPUExecutionProvider"],
        )
        instance._input_name = instance._session.get_inputs()[0].name
        instance._label_output_name = instance._session.get_outputs()[0].name
        instance._proba_output_name = instance._session.get_outputs()[1].name

        logger.info("ONNX model loaded from %s", path)
        return instance

    def _check_loaded(self) -> None:
        """Raise RuntimeError if no ONNX session is loaded."""
        if self._session is None:
            raise RuntimeError(
                "No ONNX session loaded. Call ONNXClassifier.load(path) first."
            )
