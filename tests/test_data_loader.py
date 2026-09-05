"""Tests for the dataset loader and synthetic data generation."""

import json
from pathlib import Path

import pandas as pd
import pytest

from triage.data.loader import (
    LABEL_MAP,
    LABEL_NAMES,
    _load_csv,
    _resolve_kaggle_credentials,
    generate_synthetic_dataset,
    load_dataset,
)


def test_label_map_and_names_are_consistent() -> None:
    """LABEL_MAP and LABEL_NAMES should be inverses of each other."""
    for name, idx in LABEL_MAP.items():
        assert LABEL_NAMES[idx] == name


def test_generate_synthetic_dataset_returns_dataframe() -> None:
    """generate_synthetic_dataset() should return a DataFrame."""
    df = generate_synthetic_dataset(n_samples=90, random_seed=0)
    assert isinstance(df, pd.DataFrame)


def test_synthetic_dataset_has_required_columns() -> None:
    """Generated dataset should have 'text' and 'label' columns."""
    df = generate_synthetic_dataset(n_samples=90)
    assert "text" in df.columns
    assert "label" in df.columns


def test_synthetic_dataset_size() -> None:
    """Generated dataset should have approximately n_samples rows."""
    df = generate_synthetic_dataset(n_samples=90)
    # Will be exactly 90 (30 per class with 3 classes)
    assert len(df) == 90


def test_synthetic_dataset_labels_are_valid() -> None:
    """All labels in synthetic dataset should be in {0, 1, 2}."""
    df = generate_synthetic_dataset(n_samples=90)
    valid_labels = set(LABEL_MAP.values())
    assert set(df["label"].unique()).issubset(valid_labels)


def test_synthetic_dataset_is_balanced() -> None:
    """Synthetic dataset should be roughly balanced across 3 classes."""
    df = generate_synthetic_dataset(n_samples=90)
    counts = df["label"].value_counts()
    assert len(counts) == 3
    assert all(c == 30 for c in counts.values)


def test_synthetic_dataset_reproducibility() -> None:
    """Same seed should produce same dataset."""
    df1 = generate_synthetic_dataset(n_samples=90, random_seed=42)
    df2 = generate_synthetic_dataset(n_samples=90, random_seed=42)
    pd.testing.assert_frame_equal(df1, df2)


def test_synthetic_dataset_text_is_non_empty() -> None:
    """All text entries should be non-empty strings."""
    df = generate_synthetic_dataset(n_samples=90)
    assert df["text"].apply(lambda x: isinstance(x, str) and len(x) > 0).all()


def test_load_csv_standard_format(tmp_path: Path) -> None:
    """_load_csv correctly reads a CSV with 'text' and 'label' columns."""
    csv_file = tmp_path / "test.csv"
    data = pd.DataFrame(
        {
            "text": ["dor no peito aguda", "consulta de rotina", "febre moderada"],
            "label": [2, 0, 1],
        }
    )
    data.to_csv(csv_file, index=False)

    df = _load_csv(csv_file)
    assert len(df) == 3
    assert list(df["label"]) == [2, 0, 1]
    assert list(df["text"]) == list(data["text"])


def test_load_csv_kaggle_format(tmp_path: Path) -> None:
    """_load_csv correctly maps Kaggle 5-class columns to 3-class triage format."""
    csv_file = tmp_path / "kaggle.csv"
    # Kaggle format: abstract, condition_label
    # 1=Neoplasms->2, 2=Digestive->1, 3=Nervous->2, 4=Cardiovascular->2, 5=General->0
    data = pd.DataFrame(
        {
            "abstract": ["laudo 1", "laudo 2", "laudo 3", "laudo 4", "laudo 5"],
            "condition_label": [1, 2, 3, 4, 5],
        }
    )
    data.to_csv(csv_file, index=False)

    df = _load_csv(csv_file)
    assert "text" in df.columns
    assert "label" in df.columns
    assert list(df["label"]) == [2, 1, 2, 2, 0]


def test_load_dataset_from_disk(tmp_path: Path) -> None:
    """load_dataset prefers reading medical_abstracts.csv from data_dir if present."""
    csv_file = tmp_path / "medical_abstracts.csv"
    data = pd.DataFrame({"text": ["exame normal"], "label": [0]})
    data.to_csv(csv_file, index=False)

    df = load_dataset(tmp_path)
    assert len(df) == 1
    assert df["text"].iloc[0] == "exame normal"


def test_load_dataset_fallback_to_synthetic(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """When no dataset is on disk and Kaggle is not set, falls back to synthetic."""
    # Ensure no Kaggle credentials
    monkeypatch.delenv("KAGGLE_API_TOKEN", raising=False)
    monkeypatch.delenv("KAGGLE_USERNAME", raising=False)
    monkeypatch.delenv("KAGGLE_KEY", raising=False)
    monkeypatch.setattr(Path, "home", lambda: tmp_path / "empty_home")

    df = load_dataset(tmp_path, random_seed=42)
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 3000
    assert set(df["label"].unique()) == {0, 1, 2}


def test_resolve_kaggle_credentials_token(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """_resolve_kaggle_credentials detects KAGGLE_API_TOKEN and writes kaggle.json."""
    fake_home = tmp_path / "home_token"
    fake_home.mkdir()
    monkeypatch.setattr(Path, "home", lambda: fake_home)
    monkeypatch.setenv("KAGGLE_API_TOKEN", "KGAT_test_secret_token_123")
    monkeypatch.delenv("KAGGLE_USERNAME", raising=False)
    monkeypatch.delenv("KAGGLE_KEY", raising=False)

    assert _resolve_kaggle_credentials() is True

    kaggle_json = fake_home / ".kaggle" / "kaggle.json"
    assert kaggle_json.exists()
    content = json.loads(kaggle_json.read_text())
    assert content == {"token": "KGAT_test_secret_token_123"}


def test_resolve_kaggle_credentials_legacy(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """_resolve_kaggle_credentials detects KAGGLE_USERNAME and KAGGLE_KEY env vars."""
    fake_home = tmp_path / "home_legacy"
    fake_home.mkdir()
    monkeypatch.setattr(Path, "home", lambda: fake_home)
    monkeypatch.delenv("KAGGLE_API_TOKEN", raising=False)
    monkeypatch.setenv("KAGGLE_USERNAME", "test_user")
    monkeypatch.setenv("KAGGLE_KEY", "test_key")

    assert _resolve_kaggle_credentials() is True


def test_resolve_kaggle_credentials_existing_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """_resolve_kaggle_credentials detects existing ~/.kaggle/kaggle.json."""
    fake_home = tmp_path / "home_file"
    kaggle_dir = fake_home / ".kaggle"
    kaggle_dir.mkdir(parents=True)
    (kaggle_dir / "kaggle.json").write_text('{"token": "xyz"}')

    monkeypatch.setattr(Path, "home", lambda: fake_home)
    monkeypatch.delenv("KAGGLE_API_TOKEN", raising=False)
    monkeypatch.delenv("KAGGLE_USERNAME", raising=False)
    monkeypatch.delenv("KAGGLE_KEY", raising=False)

    assert _resolve_kaggle_credentials() is True


def test_resolve_kaggle_credentials_none(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """_resolve_kaggle_credentials returns False when no credentials exist."""
    fake_home = tmp_path / "home_none"
    fake_home.mkdir()
    monkeypatch.setattr(Path, "home", lambda: fake_home)
    monkeypatch.delenv("KAGGLE_API_TOKEN", raising=False)
    monkeypatch.delenv("KAGGLE_USERNAME", raising=False)
    monkeypatch.delenv("KAGGLE_KEY", raising=False)

    assert _resolve_kaggle_credentials() is False
