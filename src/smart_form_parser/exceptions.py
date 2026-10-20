"""Exception types raised by smart_form_parser."""


class SmartFormParserError(Exception):
    """Base class for every error this package raises."""


class ImageLoadError(SmartFormParserError):
    """The image could not be opened or decoded."""


class OCREngineError(SmartFormParserError):
    """The OCR engine is missing or failed while reading the image."""


class SchemaError(SmartFormParserError):
    """A form schema is unknown or malformed."""
