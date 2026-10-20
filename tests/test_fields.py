from smart_form_parser.fields import extract, group_lines
from smart_form_parser.schema import Field, FormSchema, get_schema

from conftest import row_words


def extract_rows(rows, schema):
    return extract(group_lines(row_words(rows)), schema)


def test_group_lines_keeps_rows_separate_and_ordered():
    lines = group_lines(row_words(["Make Toyota", "Model Hilux"]))
    assert [line.text for line in lines] == ["Make Toyota", "Model Hilux"]


def test_reads_labelled_values_on_the_same_line():
    fields = extract_rows(
        ["VIN: 1HGCM82633A004352", "Make: Toyota", "Odometer: 142,370 km"],
        get_schema("vehicle_inspection"),
    )
    assert fields["vin"].value == "1HGCM82633A004352"
    assert fields["make"].value == "Toyota"
    assert fields["odometer"].value == 142370


def test_falls_back_to_the_value_printed_below_the_label():
    fields = extract_rows(["Consignee", "Kigali Motors Ltd"], get_schema("shipping_manifest"))
    assert fields["consignee"].value == "Kigali Motors Ltd"


def test_prefers_the_most_specific_label():
    fields = extract_rows(
        ["Date: 01/01/2020", "Inspection Date: 14/10/2026"],
        get_schema("vehicle_inspection"),
    )
    assert fields["inspection_date"].value == "14/10/2026"


def test_rejects_a_value_that_does_not_fit_the_field_kind():
    fields = extract_rows(["VIN: not-a-vin"], get_schema("vehicle_inspection"))
    assert fields["vin"].value is None
    assert fields["vin"].found is False


def test_missing_fields_still_appear_with_an_empty_value():
    fields = extract_rows(["Make: Toyota"], get_schema("vehicle_inspection"))
    assert set(fields) == {field.name for field in get_schema("vehicle_inspection").fields}
    assert fields["inspector"].value is None


def test_normalizes_container_numbers_and_european_decimals():
    fields = extract_rows(
        ["Container No: mscu 1234567", "Gross Weight: 1 250,75 kg"],
        get_schema("shipping_manifest"),
    )
    assert fields["container_number"].value == "MSCU1234567"
    assert fields["gross_weight"].value == 1250.75


def test_confidence_comes_from_the_words_that_carried_the_value():
    schema = FormSchema("tiny", (Field("make", ("make",)),))
    fields = extract(group_lines(row_words(["Make: Toyota"], confidence=63.0)), schema)
    assert fields["make"].confidence == 63.0
