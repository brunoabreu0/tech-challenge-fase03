"""Tests for the text preprocessor module."""

import pytest

from triage.data.preprocessor import clean_text, preprocess_texts


@pytest.mark.parametrize(
    "input_text,expected",
    [
        ("  Hello World  ", "hello world"),
        ("Paciente com DOR TORÁCICA", "paciente com dor torácica"),
        ("Texto com 123 números!", "texto com números"),
        ("http://example.com visita", "visita"),
        ("  Multiple   spaces   here  ", "multiple spaces here"),
        ("", ""),
    ],
)
def test_clean_text(input_text: str, expected: str) -> None:
    """clean_text should normalise text correctly."""
    result = clean_text(input_text)
    assert result == expected


def test_clean_text_handles_none_gracefully() -> None:
    """clean_text should return empty string for non-string input."""
    assert clean_text(None) == ""  # type: ignore[arg-type]


def test_preprocess_texts_returns_list() -> None:
    """preprocess_texts should return a list of same length."""
    texts = ["Hello World", "Second text", "Third!"]
    result = preprocess_texts(texts)
    assert isinstance(result, list)
    assert len(result) == 3


def test_preprocess_texts_applies_clean_text() -> None:
    """preprocess_texts should apply clean_text to each element."""
    texts = ["HELLO WORLD", "test 123"]
    result = preprocess_texts(texts)
    assert result[0] == "hello world"
    assert result[1] == "test"
