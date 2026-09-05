"""Export the trained sklearn model to ONNX format using skl2onnx."""

import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from triage.model.tfidf_lr import TFIDFLogisticClassifier
from triage.settings import get_settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)


def export_to_onnx(joblib_path: Path, onnx_path: Path) -> None:
    """Convert a fitted TFIDFLogisticClassifier to ONNX format.

    The resulting ONNX model accepts a batch of strings and outputs:
    - output_label: predicted integer labels
    - output_probability: list of class probability dicts

    Args:
        joblib_path: Path to the saved .joblib model file.
        onnx_path: Destination path for the .onnx file.
    """
    try:
        from skl2onnx import convert_sklearn
        from skl2onnx.common.data_types import StringTensorType
    except ImportError as exc:
        raise ImportError(
            "skl2onnx is required for ONNX export. Run: pip install skl2onnx"
        ) from exc

    logger.info("Loading sklearn model from %s ...", joblib_path)
    clf = TFIDFLogisticClassifier.load(joblib_path)
    pipeline = clf.get_sklearn_pipeline()

    logger.info("Converting to ONNX ...")
    # Input: variable-length batch of strings (shape [N, 1])
    initial_type = [("input", StringTensorType([None, 1]))]
    onnx_model = convert_sklearn(
        pipeline,
        initial_types=initial_type,
        target_opset=17,
        options={type(pipeline.named_steps["clf"]): {"zipmap": True}},
    )

    onnx_path.parent.mkdir(parents=True, exist_ok=True)
    with open(onnx_path, "wb") as f:
        f.write(onnx_model.SerializeToString())

    size_kb = onnx_path.stat().st_size / 1024
    logger.info("✅ ONNX model saved to %s (%.1f KB)", onnx_path, size_kb)


def main() -> None:
    """Export the trained model to ONNX."""
    settings = get_settings()
    joblib_path = settings.model_dir / "classifier.joblib"
    onnx_path = settings.model_dir / "classifier.onnx"

    if not joblib_path.exists():
        logger.error(
            "Sklearn model not found at %s. Run scripts/train.py first.", joblib_path
        )
        sys.exit(1)

    export_to_onnx(joblib_path, onnx_path)


if __name__ == "__main__":
    main()
