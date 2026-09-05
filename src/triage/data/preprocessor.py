"""Text preprocessing utilities for medical reports."""

import re
import string


def clean_text(text: str) -> str:
    """Clean and normalise a medical report text string.

    Steps applied:
    1. Lowercase
    2. Remove URLs
    3. Remove punctuation and digits
    4. Collapse extra whitespace

    Args:
        text: Raw medical report text.

    Returns:
        Cleaned, normalised text string.
    """
    if not isinstance(text, str):
        return ""

    # Lowercase
    text = text.lower()

    # Remove URLs
    text = re.sub(r"http\S+|www\.\S+", " ", text)

    # Remove punctuation and digits
    text = text.translate(str.maketrans("", "", string.punctuation + string.digits))

    # Collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()

    return text


def preprocess_texts(texts: list[str]) -> list[str]:
    """Apply clean_text to a list of texts.

    Args:
        texts: List of raw text strings.

    Returns:
        List of cleaned text strings.
    """
    return [clean_text(t) for t in texts]
