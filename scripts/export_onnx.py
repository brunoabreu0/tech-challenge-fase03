"""Export the trained sklearn model to ONNX format using skl2onnx."""

import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from triage.model.exporter import export_to_onnx
from triage.settings import get_settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)


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
