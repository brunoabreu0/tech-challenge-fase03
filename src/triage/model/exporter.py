"""ONNX export utilities for trained scikit-learn triage models."""

import logging
from pathlib import Path
from typing import Any

from triage.model.tfidf_lr import TFIDFLogisticClassifier

logger = logging.getLogger(__name__)


def export_to_onnx(joblib_path: Path, onnx_path: Path) -> Path:
    """Convert a fitted TFIDFLogisticClassifier from joblib to ONNX format.

    The exported ONNX model accepts a batch of strings (shape [N, 1]) and outputs:
    - label: predicted class integer
    - probabilities: list of class probability dicts (ZipMap)

    Args:
        joblib_path: Path to the serialised sklearn model (.joblib).
        onnx_path: Destination path for the .onnx file.

    Returns:
        The path to the generated ONNX file.

    Raises:
        ImportError: If skl2onnx is not installed.
        FileNotFoundError: If the source joblib file does not exist.
    """
    try:
        from skl2onnx import convert_sklearn
        from skl2onnx.common.data_types import StringTensorType
    except ImportError as exc:
        raise ImportError(
            "skl2onnx is required for ONNX export. Run: pip install skl2onnx"
        ) from exc

    joblib_path = Path(joblib_path)
    onnx_path = Path(onnx_path)

    if not joblib_path.exists():
        raise FileNotFoundError(f"Sklearn model not found: {joblib_path}")

    logger.info("Loading sklearn model from %s ...", joblib_path)
    clf = TFIDFLogisticClassifier.load(joblib_path)
    pipeline = clf.get_sklearn_pipeline()

    logger.info("Converting pipeline to ONNX ...")
    initial_type: list[tuple[str, Any]] = [("input", StringTensorType([None, 1]))]
    onnx_model = convert_sklearn(
        pipeline,
        initial_types=initial_type,
        target_opset=17,
        options={type(pipeline.named_steps["clf"]): {"zipmap": True}},
    )

    onnx_path.parent.mkdir(parents=True, exist_ok=True)
    onnx_path.write_bytes(onnx_model.SerializeToString())

    size_kb = onnx_path.stat().st_size / 1024
    logger.info("✅ ONNX model saved to %s (%.1f KB)", onnx_path, size_kb)
    return onnx_path
