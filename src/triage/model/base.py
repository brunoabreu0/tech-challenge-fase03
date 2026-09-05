"""Abstract base class for all triage classifiers."""

from abc import ABC, abstractmethod
from pathlib import Path


class BaseClassifier(ABC):
    """Contract for all medical triage text classifiers.

    Subclasses must implement: fit, predict, save, load.
    """

    @abstractmethod
    def fit(self, texts: list[str], labels: list[int]) -> "BaseClassifier":
        """Train the classifier on the provided data.

        Args:
            texts: List of medical report texts.
            labels: List of integer urgency labels (0=normal, 1=atencao, 2=urgente).

        Returns:
            Self, for method chaining.
        """

    @abstractmethod
    def predict(self, texts: list[str]) -> list[int]:
        """Predict urgency labels for a list of texts.

        Args:
            texts: List of medical report texts.

        Returns:
            List of predicted integer labels.
        """

    @abstractmethod
    def predict_proba(self, texts: list[str]) -> list[list[float]]:
        """Return class probability estimates for each text.

        Args:
            texts: List of medical report texts.

        Returns:
            List of probability vectors (one per sample, length = n_classes).
        """

    @abstractmethod
    def save(self, path: Path) -> None:
        """Persist the trained model to disk.

        Args:
            path: Target file path (format depends on implementation).
        """

    @classmethod
    @abstractmethod
    def load(cls, path: Path) -> "BaseClassifier":
        """Load a trained model from disk.

        Args:
            path: Source file path.

        Returns:
            Loaded classifier instance.
        """
