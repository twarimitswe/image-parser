"""End-to-end check against a real Tesseract install; skipped when it is missing."""

from __future__ import annotations

import shutil

import pytest
from PIL import Image, ImageDraw

from smart_form_parser import FormParser

pytest.importorskip("pytesseract")
pytestmark = pytest.mark.skipif(
    shutil.which("tesseract") is None, reason="the tesseract binary is not installed"
)

ROWS = [
    "VEHICLE INSPECTION REPORT",
    "VIN: 1HGCM82633A004352",
    "Make: Toyota",
    "Model: Hilux",
    "Year: 2019",
    "Odometer: 142370",
    "Inspection Date: 14/10/2026",
    "Result: PASS",
]


@pytest.fixture
def inspection_sheet(tmp_path):
    image = Image.new("RGB", (1700, 700), "white")
    canvas = ImageDraw.Draw(image)
    for index, row in enumerate(ROWS):
        canvas.text((60, 50 + index * 75), row, fill="black", font_size=44)
    path = tmp_path / "inspection.png"
    image.save(path)
    return path


def test_reads_a_rendered_inspection_sheet(inspection_sheet):
    form = FormParser("vehicle_inspection").parse(inspection_sheet)
    assert form.data["vin"] == "1HGCM82633A004352"
    assert form.data["make"] == "Toyota"
    assert form.data["year"] == 2019
    assert form.data["odometer"] == 142370
    assert form.missing(("vin", "inspection_date")) == []
