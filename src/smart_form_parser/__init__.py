"""smart-form-parser: read printed forms from an image and return structured JSON.

Built for the paperwork that logistics providers, shipping lines and car
dealerships still receive on paper -- vehicle inspection sheets, registration
documents and shipping manifests.

    >>> from smart_form_parser import parse
    >>> form = parse("inspection.jpg", "vehicle_inspection")
    >>> form.data["vin"]
    '1HGCM82633A004352'
"""

__version__ = "0.1.0"

from .exceptions import (
    ImageLoadError,
    OCREngineError,
    SchemaError,
    SmartFormParserError,
)
from .fields import FieldValue, Line, extract, group_lines
from .ocr import Word, tesseract_words
from .parser import FormParser, ParsedForm, parse
from .preprocess import load, prepare
from .schema import (
    Field,
    FormSchema,
    get_schema,
    register_schema,
    schema_names,
)

__all__ = [
    "__version__",
    "Field",
    "FieldValue",
    "FormParser",
    "FormSchema",
    "ImageLoadError",
    "Line",
    "OCREngineError",
    "ParsedForm",
    "SchemaError",
    "SmartFormParserError",
    "Word",
    "extract",
    "get_schema",
    "group_lines",
    "load",
    "parse",
    "prepare",
    "register_schema",
    "schema_names",
    "tesseract_words",
]
