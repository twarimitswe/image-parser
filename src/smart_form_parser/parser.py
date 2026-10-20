"""The parser that takes a form image and hands back structured data."""

from __future__ import annotations

import json
from dataclasses import dataclass, field as dataclass_field
from functools import partial
from typing import Any, Callable, Dict, List, Sequence, Union

from PIL import Image

from .fields import EMPTY, FieldValue, Line, extract, group_lines
from .ocr import Word, tesseract_words
from .preprocess import ImageSource, load, prepare
from .schema import FormSchema, get_schema

Engine = Callable[[Image.Image], Sequence[Word]]


@dataclass(frozen=True)
class ParsedForm:
    """Everything read off one form image."""

    schema: str
    fields: Dict[str, FieldValue] = dataclass_field(default_factory=dict)
    lines: List[Line] = dataclass_field(default_factory=list)

    @property
    def text(self) -> str:
        """The full page text, one line per row of the form."""
        return "\n".join(line.text for line in self.lines)

    @property
    def data(self) -> Dict[str, Any]:
        """Just the values, which is what a downstream pipeline consumes."""
        return {name: value.value for name, value in self.fields.items()}

    @property
    def confidence(self) -> Dict[str, float]:
        return {name: round(value.confidence, 1) for name, value in self.fields.items()}

    def missing(self, required: Sequence[str]) -> List[str]:
        """Which of ``required`` fields came back empty."""
        return [name for name in required if not self.fields.get(name, EMPTY).found]

    def to_dict(self, *, include_text: bool = True) -> Dict[str, Any]:
        """A JSON-ready dict with a stable shape, whether or not fields were found."""
        payload: Dict[str, Any] = {
            "schema": self.schema,
            "data": self.data,
            "confidence": self.confidence,
            "missing_required": self.missing(get_schema(self.schema).required_names),
        }
        if include_text:
            payload["text"] = self.text
        return payload

    def to_json(self, *, include_text: bool = True, indent: int = 2) -> str:
        """The structured JSON this package exists to produce."""
        return json.dumps(self.to_dict(include_text=include_text), indent=indent, ensure_ascii=False)


class FormParser:
    """Reads one kind of form, reusing the same settings across many images."""

    def __init__(
        self,
        schema: Union[str, FormSchema] = "generic",
        *,
        language: str = "eng",
        min_confidence: float = 40.0,
        engine: Engine = None,
        preprocess: bool = True,
    ) -> None:
        self.schema = get_schema(schema)
        self.preprocess = preprocess
        self.engine = engine or partial(
            tesseract_words, language=language, min_confidence=min_confidence
        )

    def parse(self, source: ImageSource) -> ParsedForm:
        """Parse ``source`` -- a path, bytes or a Pillow image -- into a ``ParsedForm``."""
        image = load(source)
        words = self.engine(prepare(image) if self.preprocess else image)
        lines = group_lines(words)
        return ParsedForm(self.schema.name, extract(lines, self.schema), lines)


def parse(source: ImageSource, schema: Union[str, FormSchema] = "generic", **options: Any) -> ParsedForm:
    """Parse a single image without keeping a parser around."""
    return FormParser(schema, **options).parse(source)
