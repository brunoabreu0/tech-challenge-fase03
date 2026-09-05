"""Unit tests for the ONNX classifier wrapper and export pipeline."""

from pathlib import Path

import pytest

from triage.data.loader import generate_synthetic_dataset
from triage.data.preprocessor import preprocess_texts
from triage.model.exporter import export_to_onnx
from triage.model.factory import ClassifierFactory
from triage.model.onnx_classifier import ONNXClassifier
from triage.model.tfidf_lr import TFIDFLogisticClassifier


def test_onnx_fit_raises_not_implemented() -> None:
    """ONNXClassifier does not support training (.fit())."""
    clf = ONNXClassifier()
    with pytest.raises(NotImplementedError, match="does not support training"):
        clf.fit(["dor de cabeca"], [0])


def test_onnx_save_raises_not_implemented(tmp_path: Path) -> None:
    """ONNXClassifier does not support .save()."""
    clf = ONNXClassifier()
    with pytest.raises(NotImplementedError, match="scripts/export_onnx.py"):
        clf.save(tmp_path / "model.onnx")


def test_onnx_predict_unloaded_raises_runtime_error() -> None:
    """Calling predict without loading a session raises RuntimeError."""
    clf = ONNXClassifier()
    with pytest.raises(RuntimeError, match="No ONNX session loaded"):
        clf.predict(["dor no peito"])


def test_onnx_predict_proba_unloaded_raises_runtime_error() -> None:
    """Calling predict_proba without loading a session raises RuntimeError."""
    clf = ONNXClassifier()
    with pytest.raises(RuntimeError, match="No ONNX session loaded"):
        clf.predict_proba(["dor no peito"])


def test_onnx_load_nonexistent_raises_file_not_found(tmp_path: Path) -> None:
    """Loading a non-existent ONNX file raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError, match="not found"):
        ONNXClassifier.load(tmp_path / "missing.onnx")


def test_onnx_export_load_and_predict_roundtrip(tmp_path: Path) -> None:
    """Roundtrip test: train sklearn, export to ONNX, run inference and parity."""
    # 1. Train lightweight sklearn model
    df = generate_synthetic_dataset(n_samples=90, random_seed=42)
    texts = preprocess_texts(df["text"].tolist())
    labels = df["label"].tolist()

    clf_sklearn = TFIDFLogisticClassifier()
    clf_sklearn.fit(texts, labels)

    joblib_path = tmp_path / "classifier.joblib"
    onnx_path = tmp_path / "classifier.onnx"
    clf_sklearn.save(joblib_path)

    # 2. Export to ONNX
    export_to_onnx(joblib_path, onnx_path)
    assert onnx_path.exists()
    assert onnx_path.stat().st_size > 0

    # 3. Load via ONNXClassifier
    clf_onnx = ONNXClassifier.load(onnx_path)

    test_queries = [
        "paciente com dor torácica aguda e sudorese",
        "exame de rotina anual sem alterações",
        "febre moderada há dois dias e tosse leve",
    ]
    test_clean = preprocess_texts(test_queries)

    # 4. Predict parity check
    preds_sk = clf_sklearn.predict(test_clean)
    preds_ox = clf_onnx.predict(test_clean)
    assert preds_ox == preds_sk

    # 5. Predict proba parity check
    proba_sk = clf_sklearn.predict_proba(test_clean)
    proba_ox = clf_onnx.predict_proba(test_clean)
    assert len(proba_ox) == len(test_queries)
    for p_sk, p_ox in zip(proba_sk, proba_ox, strict=True):
        assert len(p_ox) == 3
        # Class probabilities should match closely
        for val_sk, val_ox in zip(p_sk, p_ox, strict=True):
            assert abs(val_sk - val_ox) < 0.05


def test_factory_with_onnx(tmp_path: Path) -> None:
    """Test ClassifierFactory creates and loads ONNX models properly."""
    # Test create
    instance = ClassifierFactory.create("onnx")
    assert isinstance(instance, ONNXClassifier)

    # Test unknown name raises ValueError
    with pytest.raises(ValueError, match="Unknown classifier"):
        ClassifierFactory.create("invalid_name")

    with pytest.raises(ValueError, match="Unknown classifier"):
        ClassifierFactory.load("invalid_name", tmp_path / "any.file")

    # Export a mock onnx to test factory load
    df = generate_synthetic_dataset(n_samples=60, random_seed=42)
    clf = TFIDFLogisticClassifier()
    clf.fit(preprocess_texts(df["text"].tolist()), df["label"].tolist())

    joblib_p = tmp_path / "test.joblib"
    onnx_p = tmp_path / "test.onnx"
    clf.save(joblib_p)
    export_to_onnx(joblib_p, onnx_p)

    loaded = ClassifierFactory.load("onnx", onnx_p)
    assert isinstance(loaded, ONNXClassifier)
    preds = loaded.predict(["paciente estável"])
    assert len(preds) == 1
