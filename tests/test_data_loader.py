"""Tests for the dataset loader and synthetic data generation."""

import pandas as pd

from triage.data.loader import LABEL_MAP, LABEL_NAMES, generate_synthetic_dataset


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
