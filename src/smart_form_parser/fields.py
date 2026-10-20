"""Turning loose OCR words into the labelled values a form is meant to carry."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence, Tuple

from .ocr import Word
from .schema import Field, FormSchema

VALUE_SEPARATORS = " \t:;=.-–—_|"
"""Punctuation that sits between a printed label and its value."""

BELOW_REACH = 2.5
"""How many label heights below a label a value may still belong to it."""


@dataclass(frozen=True)
class Line:
    """Words that share a row on the page, left to right."""

    words: Tuple[Word, ...]

    @property
    def text(self) -> str:
        return " ".join(word.text for word in self.words)

    @property
    def left(self) -> int:
        return min(word.left for word in self.words)

    @property
    def right(self) -> int:
        return max(word.right for word in self.words)

    @property
    def top(self) -> int:
        return min(word.top for word in self.words)

    @property
    def bottom(self) -> int:
        return max(word.bottom for word in self.words)

    @property
    def confidence(self) -> float:
        return sum(word.confidence for word in self.words) / len(self.words)


@dataclass(frozen=True)
class FieldValue:
    """A value read off the form, with how sure the OCR engine was about it."""

    value: Any
    confidence: float
    text: str

    @property
    def found(self) -> bool:
        return self.value is not None


EMPTY = FieldValue(None, 0.0, "")


def group_lines(words: Sequence[Word], tolerance: float = 0.6) -> List[Line]:
    """Cluster ``words`` into rows, using each word's height as the row tolerance."""
    lines: List[List[Word]] = []
    for word in sorted(words, key=lambda item: (item.middle, item.left)):
        if lines and abs(word.middle - lines[-1][-1].middle) <= tolerance * word.height:
            lines[-1].append(word)
        else:
            lines.append([word])
    return [Line(tuple(sorted(row, key=lambda item: item.left))) for row in lines]


def extract(lines: Sequence[Line], schema: FormSchema) -> Dict[str, FieldValue]:
    """Read every field in ``schema`` off ``lines``, keyed by field name."""
    scans = [_scan(line) for line in lines]
    return {field.name: _extract_field(field, scans) for field in schema.fields}


class _Scan:
    """A line plus the alphanumeric-only copy used to locate labels in it."""

    __slots__ = ("line", "text", "search", "offsets")

    def __init__(self, line: Line) -> None:
        self.line = line
        self.text = line.text
        self.search = re.sub(r"[^a-z0-9]", " ", self.text.lower())
        self.offsets = []
        position = 0
        for word in line.words:
            self.offsets.append(position)
            position += len(word.text) + 1


def _scan(line: Line) -> _Scan:
    return _Scan(line)


def _label_expression(label: str) -> re.Pattern:
    tokens = re.findall(r"[a-z0-9]+", label.lower())
    return re.compile(r"(?<![a-z0-9])" + r"\s+".join(tokens) + r"(?![a-z0-9])")


def _extract_field(field: Field, scans: Sequence[_Scan]) -> FieldValue:
    """Try each of the field's labels, most specific first, and take the first hit."""
    for label in sorted(field.labels, key=lambda text: -len(text.split())):
        expression = _label_expression(label)
        for index, scan in enumerate(scans):
            match = expression.search(scan.search)
            if match is None:
                continue
            text, confidence = _value_near(match.end(), index, scans)
            value = _coerce(field, text)
            if value is not None:
                return FieldValue(value, confidence, text)
    return EMPTY


def _value_near(offset: int, index: int, scans: Sequence[_Scan]) -> Tuple[str, float]:
    """Take what follows the label on its own line, else the line beneath it."""
    scan = scans[index]
    tail = scan.text[offset:].strip(VALUE_SEPARATORS)
    if tail:
        trailing = [
            word
            for word, start in zip(scan.line.words, scan.offsets)
            if start + len(word.text) > offset
        ]
        confidence = sum(w.confidence for w in trailing) / len(trailing) if trailing else 0.0
        return tail, confidence
    below = _line_below(index, scans)
    return (below.text, below.confidence) if below else ("", 0.0)


def _line_below(index: int, scans: Sequence[_Scan]) -> Optional[Line]:
    label = scans[index].line
    reach = label.bottom + BELOW_REACH * (label.bottom - label.top)
    for scan in scans[index + 1 :]:
        candidate = scan.line
        if candidate.top > reach:
            break
        if candidate.left <= label.right and candidate.right >= label.left:
            return candidate
    return None


def _coerce(field: Field, text: str) -> Any:
    """Match ``text`` against the field's kind and convert it to a Python value."""
    if not text:
        return None
    pattern = field.pattern
    if pattern is None:
        return text
    match = pattern.search(text)
    if match is None:
        return None
    matched = match.group().strip()
    if field.kind == "integer":
        return int(re.sub(r"[^\d-]", "", matched))
    if field.kind == "number":
        return float(_decimal_text(matched))
    if field.kind in ("vin", "container"):
        return re.sub(r"\s+", "", matched).upper()
    return matched


def _decimal_text(matched: str) -> str:
    """Normalize '1 250,75' and '1,250.75' into something ``float`` accepts."""
    cleaned = re.sub(r"\s", "", matched)
    if "." in cleaned:
        return cleaned.replace(",", "")
    if re.search(r",\d{1,2}$", cleaned):
        return cleaned.replace(",", ".")
    return cleaned.replace(",", "")
