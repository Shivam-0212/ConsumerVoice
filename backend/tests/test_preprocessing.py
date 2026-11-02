"""Unit tests for Data Preprocessing and Audit service."""

import pytest
from backend.app.services.data_preprocessing import clean_text_basic, normalize_summary, parse_rating


def test_clean_text_basic():
    raw_html = "<p>Superb   quality!!!</p>"
    cleaned = clean_text_basic(raw_html)
    assert cleaned == "Superb quality!!!"
    assert clean_text_basic(None) == ""


def test_normalize_summary_preserves_negations():
    text = "Not good at all, completely useless!"
    norm = normalize_summary(text)
    assert "not" in norm
    assert "good" in norm
    assert "useless" in norm


def test_parse_rating_valid_and_malformed():
    assert parse_rating("5") == 5.0
    assert parse_rating("3.0") == 3.0
    assert parse_rating("1") == 1.0

    # Malformed non-numeric values
    assert parse_rating("Pigeon Favourite Electric Kettle") is None
    assert parse_rating("Bajaj DX 2 L/W Dry Iron") is None
    assert parse_rating("invalid_rate") is None
    assert parse_rating(None) is None
