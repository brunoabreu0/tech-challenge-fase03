"""Factory for instantiating medical triage classifiers by name."""

import logging
from pathlib import Path

from triage.model.base import BaseClassifier

logger = logging.getLogger(__name__)

_REGISTRY: dict[str, type[BaseClassifier]] = {}


def _register() -> None:
    """Lazy-import classifiers to avoid loading heavy deps at import time."""
    global _REGISTRY
    from triage.model.onnx_classifier import ONNXClassifier
    from triage.model.tfidf_lr import TFIDFLogisticClassifier

    _REGISTRY = {
        "tfidf_lr": TFIDFLogisticClassifier,
        "onnx": ONNXClassifier,
    }


class ClassifierFactory:
    """Factory for creating and loading medical triage classifiers.

    Usage::

        # Create a new (unfitted) classifier
        clf = ClassifierFactory.create("tfidf_lr")

        # Load a pre-trained model from disk
        clf = ClassifierFactory.load("tfidf_lr", path=Path("models/classifier.joblib"))
        clf = ClassifierFactory.load("onnx", path=Path("models/classifier.onnx"))
    """

    @staticmethod
    def create(name: str, **kwargs) -> BaseClassifier:
        """Instantiate a new (unfitted) classifier.

        Args:
            name: Classifier key (``"tfidf_lr"`` or ``"onnx"``).
            **kwargs: Extra keyword arguments forwarded to the classifier constructor.

        Returns:
            New classifier instance.

        Raises:
            ValueError: If the name is not registered.
        """
        _register()
        name = name.lower()
        if name not in _REGISTRY:
            available = list(_REGISTRY.keys())
            raise ValueError(f"Unknown classifier '{name}'. Available: {available}")
        logger.info("Creating classifier: %s", name)
        return _REGISTRY[name](**kwargs)

    @staticmethod
    def load(name: str, path: Path) -> BaseClassifier:
        """Load a pre-trained classifier from disk.

        Args:
            name: Classifier key (``"tfidf_lr"`` or ``"onnx"``).
            path: Path to the serialised model file.

        Returns:
            Loaded classifier instance ready for inference.

        Raises:
            ValueError: If the name is not registered.
        """
        _register()
        name = name.lower()
        if name not in _REGISTRY:
            available = list(_REGISTRY.keys())
            raise ValueError(f"Unknown classifier '{name}'. Available: {available}")
        logger.info("Loading classifier '%s' from %s", name, path)
        return _REGISTRY[name].load(path)
