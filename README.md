# smart-form-parser

Read a printed form from an image and get structured JSON back.

Logistics providers, shipping lines and car dealerships still receive a lot of
paper: vehicle inspection sheets, registration documents, shipping manifests.
Someone then retypes them into a system by hand. `smart-form-parser` takes the
photo or scan and returns the fields, so that step can be automated.

```python
from smart_form_parser import parse

form = parse("inspection.jpg", "vehicle_inspection")

form.data          # {"vin": "1HGCM82633A004352", "make": "Toyota", "odometer": 142370, ...}
form.confidence    # {"vin": 94.2, "make": 96.0, ...}
print(form.to_json())
```

The JSON shape is stable whether or not a field was found, so a pipeline can
rely on the keys being there:

```json
{
  "schema": "vehicle_inspection",
  "data": { "vin": "1HGCM82633A004352", "make": "Toyota", "inspector": null },
  "confidence": { "vin": 94.2, "make": 96.0, "inspector": 0.0 },
  "missing_required": [],
  "text": "VIN: 1HGCM82633A004352\nMake: Toyota\n..."
}
```

## Install

```bash
pip install smart-form-parser
```

OCR is done by [Tesseract](https://tesseract-ocr.github.io/tessdoc/Installation.html),
which is a separate system binary and **not** installed by pip:

```bash
sudo apt install tesseract-ocr     # Debian / Ubuntu / Kali
brew install tesseract             # macOS
```

On Windows, install the UB Mannheim build and make sure `tesseract.exe` is on
your `PATH`.

## Command line

```bash
smart-form-parser manifest.jpg --schema shipping_manifest
smart-form-parser inspection.png -s vehicle_inspection -o result.json --no-text
smart-form-parser --list-schemas
```

## Built-in schemas

| Schema | Fields |
| --- | --- |
| `vehicle_inspection` | vin, plate, make, model, year, odometer, inspection_date, inspector, result |
| `vehicle_registration` | vin, plate, owner_name, address, make, model, year, expiry_date |
| `shipping_manifest` | container_number, bill_of_lading, vessel, voyage, port_of_loading, port_of_discharge, gross_weight, package_count, shipper, consignee |
| `generic` | no fields; returns the page text only |

Values are typed and normalized by their field kind: `vin` and `container`
numbers are validated and upper-cased, `integer` and `number` come back as
numbers (`"1 250,75"` and `"1,250.75"` both parse to `1250.75`), and anything
that does not fit its kind is reported as `null` rather than guessed at.

## Your own forms

A schema is a name and a list of fields. Each field lists the labels that may
be printed next to it:

```python
from smart_form_parser import Field, FormParser, FormSchema

delivery_note = FormSchema("delivery_note", (
    Field("order_number", ("order", "order no", "order number"), required=True),
    Field("delivered_on", ("delivered", "delivery date"), kind="date"),
    Field("pieces", ("pieces", "quantity", "qty"), kind="integer"),
))

form = FormParser(delivery_note).parse("note.jpg")
```

Field kinds are `text`, `integer`, `number`, `date`, `vin`, `plate` and
`container`. Pass `register_schema(delivery_note)` if you would rather refer to
it by name later, including from the command line.

## How it works

1. **Load** the image and respect its EXIF rotation.
2. **Prepare** it for OCR: grayscale, upscale to at least 1600px wide,
   normalize contrast, sharpen, then binarize on an Otsu threshold.
3. **Recognize** words with Tesseract, keeping each word's box and confidence
   and dropping anything below `min_confidence`.
4. **Group** words into lines by vertical position.
5. **Extract** each field by finding its label, then taking the text after it
   on the same line, or the line directly beneath it.
6. **Coerce** the result to the field's kind, or report `null`.

Steps 3 and 5 are replaceable. `FormParser(engine=...)` accepts any callable
that takes a Pillow image and returns `Word` objects, so a different OCR
backend or a hosted vision model can be dropped in without touching the rest.

## Accuracy notes

Results depend on scan quality far more than on anything in this library. Flat,
well-lit, 300 DPI scans of forms whose labels and values sit on the same line
work well. Heavy skew, handwriting and dense tables are the weak spots: this
library does not deskew, and it reads printed text rather than handwriting.
Always check `confidence` and `missing_required` before trusting a value in an
automated pipeline.

## Development

```bash
git clone git@github.com:twarimitswe/image-parser.git
cd image-parser
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest
```

The test suite injects a fake OCR engine, so most of it runs without Tesseract
installed; the end-to-end test skips itself when the binary is missing.

## License

MIT -- see [LICENSE](LICENSE).
