"""Tests for the TF-IDF + Logistic Regression classifier."""

import tempfile
from pathlib import Path

import pytest

from triage.model.tfidf_lr import TFIDFLogisticClassifier

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
TRAIN_TEXTS = [
    "paciente com dor toracica severa urgente",
    "dificuldade respiratoria grave saturacao baixa",
    "pressao arterial elevada necessita acompanhamento atencao",
    "glicemia descompensada diabetico monitoramento",
    "checkup rotina exame normal sem alteracoes",
    "consulta preventiva resultados normais pressao ok",
    "trauma craniano perda consciencia urgente",
    "anafilaxia edema glote urgente imediato",
    "tosse produtiva febre baixa atencao",
    "dor lombar cronica limitando atividades atencao",
]
TRAIN_LABELS = [2, 2, 1, 1, 0, 0, 2, 2, 1, 1]


@pytest.fixture
def fitted_classifier() -> TFIDFLogisticClassifier:
    """Return a trained TFIDFLogisticClassifier."""
    clf = TFIDFLogisticClassifier()
    clf.fit(TRAIN_TEXTS, TRAIN_LABELS)
    return clf


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------
def test_classifier_creation() -> None:
    """Classifier should be created with a pipeline."""
    clf = TFIDFLogisticClassifier()
    assert clf.pipeline is not None
    assert clf._is_fitted is False


def test_fit_returns_self() -> None:
    """fit() should return the classifier instance."""
    clf = TFIDFLogisticClassifier()
    result = clf.fit(TRAIN_TEXTS, TRAIN_LABELS)
    assert result is clf


def test_fit_sets_fitted_flag() -> None:
    """fit() should set _is_fitted to True."""
    clf = TFIDFLogisticClassifier()
    clf.fit(TRAIN_TEXTS, TRAIN_LABELS)
    assert clf._is_fitted is True


def test_predict_returns_list(fitted_classifier: TFIDFLogisticClassifier) -> None:
    """predict() should return a list of integers."""
    texts = ["dor toracica urgente", "exame normal"]
    result = fitted_classifier.predict(texts)
    assert isinstance(result, list)
    assert len(result) == 2
    assert all(isinstance(label, int) for label in result)


def test_predict_labels_in_valid_range(
    fitted_classifier: TFIDFLogisticClassifier,
) -> None:
    """Predicted labels should be 0, 1, or 2."""
    result = fitted_classifier.predict(TRAIN_TEXTS)
    assert all(label in {0, 1, 2} for label in result)


def test_predict_proba_returns_probabilities(
    fitted_classifier: TFIDFLogisticClassifier,
) -> None:
    """predict_proba() should return probability vectors summing to ~1."""
    result = fitted_classifier.predict_proba(["dor toracica"])
    assert len(result) == 1
    assert len(result[0]) == 3  # 3 classes
    assert abs(sum(result[0]) - 1.0) < 1e-5


def test_predict_raises_before_fit() -> None:
    """predict() should raise RuntimeError if called before fit()."""
    clf = TFIDFLogisticClassifier()
    with pytest.raises(RuntimeError, match="not fitted"):
        clf.predict(["some text"])


def test_save_and_load_roundtrip(
    fitted_classifier: TFIDFLogisticClassifier,
) -> None:
    """Model should survive a save/load roundtrip with same predictions."""
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "model.joblib"
        fitted_classifier.save(path)

        loaded = TFIDFLogisticClassifier.load(path)
        original_pred = fitted_classifier.predict(TRAIN_TEXTS)
        loaded_pred = loaded.predict(TRAIN_TEXTS)
        assert original_pred == loaded_pred


def test_load_raises_file_not_found() -> None:
    """load() should raise FileNotFoundError for missing files."""
    with pytest.raises(FileNotFoundError):
        TFIDFLogisticClassifier.load(Path("/nonexistent/model.joblib"))


def test_get_feature_names(fitted_classifier: TFIDFLogisticClassifier) -> None:
    """get_feature_names() should return a non-empty list of strings."""
    features = fitted_classifier.get_feature_names()
    assert isinstance(features, list)
    assert len(features) > 0
    assert all(isinstance(f, str) for f in features)
