"""OCR adapters. Tesseract is the default; any callable returning words can replace it."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

from PIL import Image

from .exceptions import OCREngineError


@dataclass(frozen=True)
class Word:
    """One recognized word and where it sits on the page."""

    text: str
    confidence: float
    left: int
    top: int
    width: int
    height: int

    @property
    def right(self) -> int:
        return self.left + self.width

    @property
    def bottom(self) -> int:
        return self.top + self.height

    @property
    def middle(self) -> float:
        return self.top + self.height / 2


def tesseract_words(
    image: Image.Image, *, language: str = "eng", min_confidence: float = 40.0
) -> List[Word]:
    """Read ``image`` with Tesseract and return the words it is confident about."""
    try:
        import pytesseract
    except ImportError as exc:  # pragma: no cover - depends on the install
        raise OCREngineError(
            "pytesseract is not installed; run 'pip install smart-form-parser[ocr]'"
        ) from exc
    try:
        data = pytesseract.image_to_data(
            image, lang=language, output_type=pytesseract.Output.DICT
        )
    except pytesseract.TesseractNotFoundError as exc:
        raise OCREngineError(
            "the tesseract binary was not found; install it from "
            "https://tesseract-ocr.github.io/tessdoc/Installation.html"
        ) from exc
    except pytesseract.TesseractError as exc:
        raise OCREngineError(f"tesseract failed: {exc}") from exc

    words = []
    for text, confidence, left, top, width, height in zip(
        data["text"], data["conf"], data["left"], data["top"], data["width"], data["height"]
    ):
        text = text.strip()
        confidence = float(confidence)
        if text and confidence >= min_confidence:
            words.append(Word(text, confidence, int(left), int(top), int(width), int(height)))
    return words
