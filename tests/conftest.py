"""Helpers that let the tests run without a Tesseract install."""

from __future__ import annotations

from typing import List, Sequence

import pytest

from smart_form_parser.ocr import Word

LINE_HEIGHT = 30
CHAR_WIDTH = 12


def row_words(rows: Sequence[str], confidence: float = 95.0) -> List[Word]:
    """Lay out ``rows`` of text as words on a page, one row per line."""
    words = []
    for index, row in enumerate(rows):
        left = 10
        for token in row.split():
            width = CHAR_WIDTH * len(token)
            words.append(Word(token, confidence, left, index * LINE_HEIGHT * 2, width, LINE_HEIGHT))
            left += width + CHAR_WIDTH
    return words


@pytest.fixture
def engine_for():
    """Build a fake OCR engine that always returns the given rows."""

    def build(rows: Sequence[str], confidence: float = 95.0):
        return lambda image: row_words(rows, confidence)

    return build
