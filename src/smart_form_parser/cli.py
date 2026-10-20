"""Command line entry point: ``smart-form-parser image.jpg -s vehicle_inspection``."""

from __future__ import annotations

import argparse
import sys
from typing import List, Optional

from . import __version__
from .exceptions import SmartFormParserError
from .parser import FormParser
from .schema import schema_names


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="smart-form-parser",
        description="Read a printed form from an image and print structured JSON.",
    )
    parser.add_argument("image", nargs="?", help="path to the form image")
    parser.add_argument(
        "-s", "--schema", default="generic", help=f"one of: {', '.join(schema_names())}"
    )
    parser.add_argument("-l", "--language", default="eng", help="Tesseract language code")
    parser.add_argument("-o", "--output", help="write the JSON here instead of stdout")
    parser.add_argument(
        "-c",
        "--min-confidence",
        type=float,
        default=40.0,
        help="drop words the OCR engine scores below this (0-100)",
    )
    parser.add_argument("--no-text", action="store_true", help="omit the full page text")
    parser.add_argument("--raw", action="store_true", help="skip image preprocessing")
    parser.add_argument("--list-schemas", action="store_true", help="list schemas and exit")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    arguments = build_parser().parse_args(argv)
    if arguments.list_schemas:
        print("\n".join(schema_names()))
        return 0
    if not arguments.image:
        print("error: an image path is required", file=sys.stderr)
        return 2

    try:
        form = FormParser(
            arguments.schema,
            language=arguments.language,
            min_confidence=arguments.min_confidence,
            preprocess=not arguments.raw,
        ).parse(arguments.image)
    except SmartFormParserError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1

    report = form.to_json(include_text=not arguments.no_text)
    if arguments.output:
        with open(arguments.output, "w", encoding="utf-8") as handle:
            handle.write(report + "\n")
    else:
        print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
