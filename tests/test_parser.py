import json

import pytest

from smart_form_parser import FormParser, SchemaError, parse
from smart_form_parser.ocr import Word

MANIFEST = [
    "BILL OF LADING: MSCU7788991",
    "Container No: MSCU 1234567",
    "Vessel: MV Northern Star",
    "Voyage: 24W",
    "Port of Loading: Mombasa",
    "Port of Discharge: Dar es Salaam",
    "Gross Weight: 18,450.5 kg",
    "Packages: 312",
    "Shipper: Highland Exports Ltd",
    "Consignee: Kigali Motors Ltd",
]


def test_parses_a_manifest_into_typed_data(engine_for):
    form = FormParser("shipping_manifest", engine=engine_for(MANIFEST)).parse(
        _blank_image()
    )
    assert form.data["container_number"] == "MSCU1234567"
    assert form.data["gross_weight"] == 18450.5
    assert form.data["package_count"] == 312
    assert form.data["consignee"] == "Kigali Motors Ltd"
    assert form.missing(("container_number",)) == []


def test_json_has_a_stable_shape_even_when_nothing_is_found(engine_for):
    form = FormParser("vehicle_registration", engine=engine_for(["blank page"])).parse(
        _blank_image()
    )
    payload = json.loads(form.to_json())
    assert payload["schema"] == "vehicle_registration"
    assert payload["data"]["vin"] is None
    assert sorted(payload["missing_required"]) == ["plate", "vin"]
    assert payload["text"] == "blank page"


def test_text_can_be_left_out_of_the_json(engine_for):
    form = FormParser("generic", engine=engine_for(["anything"])).parse(_blank_image())
    assert "text" not in json.loads(form.to_json(include_text=False))


def test_generic_schema_returns_text_and_no_fields(engine_for):
    form = FormParser("generic", engine=engine_for(["Hello", "World"])).parse(_blank_image())
    assert form.data == {}
    assert form.text == "Hello\nWorld"


def test_unknown_schema_is_rejected_with_the_available_names():
    with pytest.raises(SchemaError, match="shipping_manifest"):
        parse(_blank_image(), "not_a_schema")


def test_engine_receives_a_preprocessed_image_unless_told_otherwise():
    seen = []

    def engine(image):
        seen.append(image.mode)
        return [Word("x", 90.0, 0, 0, 10, 10)]

    image = _blank_image()
    FormParser("generic", engine=engine).parse(image)
    FormParser("generic", engine=engine, preprocess=False).parse(image)
    assert seen == ["L", "RGB"]


def _blank_image():
    from PIL import Image

    return Image.new("RGB", (900, 1200), "white")
