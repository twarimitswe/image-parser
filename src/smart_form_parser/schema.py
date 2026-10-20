"""Field kinds, form schemas and the registry that looks them up by name."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, Optional, Tuple

from .exceptions import SchemaError

VALUE_PATTERNS: Dict[str, Optional[str]] = {
    "text": None,
    "integer": r"-?\d[\d,\s]*",
    "number": r"-?\d[\d,\s]*(?:[.,]\d+)?",
    "date": r"\d{1,4}[/.\-]\d{1,2}[/.\-]\d{1,4}",
    "vin": r"[A-HJ-NPR-Z0-9]{17}",
    "plate": r"[A-Z0-9][A-Z0-9\- ]{2,10}[A-Z0-9]",
    "container": r"[A-Z]{4}\s?\d{7}",
}
"""The shape each field kind expects inside the text next to its label."""


@dataclass(frozen=True)
class Field:
    """One value to pull off the form, named by the labels printed beside it."""

    name: str
    labels: Tuple[str, ...]
    kind: str = "text"
    required: bool = False

    def __post_init__(self) -> None:
        if self.kind not in VALUE_PATTERNS:
            raise SchemaError(f"field '{self.name}' has unknown kind '{self.kind}'")
        if not self.labels:
            raise SchemaError(f"field '{self.name}' needs at least one label")

    @property
    def pattern(self) -> Optional[re.Pattern]:
        """The compiled matcher for this field's kind, or ``None`` for free text."""
        expression = VALUE_PATTERNS[self.kind]
        return re.compile(expression, re.IGNORECASE) if expression else None


@dataclass(frozen=True)
class FormSchema:
    """The set of fields expected on one kind of form."""

    name: str
    fields: Tuple[Field, ...] = ()

    @property
    def required_names(self) -> Tuple[str, ...]:
        return tuple(field.name for field in self.fields if field.required)


def _schema(name: str, *fields: Field) -> FormSchema:
    return FormSchema(name, fields)


GENERIC = _schema("generic")

VEHICLE_INSPECTION = _schema(
    "vehicle_inspection",
    Field("vin", ("vin", "vehicle identification number", "chassis number"), "vin", True),
    Field("plate", ("plate", "licence plate", "license plate", "registration plate"), "plate"),
    Field("make", ("make", "manufacturer")),
    Field("model", ("model",)),
    Field("year", ("year", "model year", "year of manufacture"), "integer"),
    Field("odometer", ("odometer", "mileage", "kilometres", "kilometers"), "integer"),
    Field("inspection_date", ("inspection date", "date of inspection", "date"), "date", True),
    Field("inspector", ("inspector", "inspected by", "technician")),
    Field("result", ("result", "outcome", "status", "pass fail")),
)

VEHICLE_REGISTRATION = _schema(
    "vehicle_registration",
    Field("vin", ("vin", "vehicle identification number", "chassis number"), "vin", True),
    Field("plate", ("plate", "registration number", "licence plate", "license plate"), "plate", True),
    Field("owner_name", ("owner", "owner name", "registered owner", "holder")),
    Field("address", ("address", "residence", "street")),
    Field("make", ("make", "manufacturer")),
    Field("model", ("model",)),
    Field("year", ("year", "model year", "first registration year"), "integer"),
    Field("expiry_date", ("expiry", "expiry date", "valid until", "expires"), "date"),
)

SHIPPING_MANIFEST = _schema(
    "shipping_manifest",
    Field("container_number", ("container", "container number", "container no"), "container", True),
    Field("bill_of_lading", ("bill of lading", "b l number", "bol", "bl no")),
    Field("vessel", ("vessel", "ship", "vessel name")),
    Field("voyage", ("voyage", "voyage number", "voyage no")),
    Field("port_of_loading", ("port of loading", "pol", "loading port")),
    Field("port_of_discharge", ("port of discharge", "pod", "discharge port")),
    Field("gross_weight", ("gross weight", "weight", "kgs", "gross kg"), "number"),
    Field("package_count", ("packages", "package count", "no of packages", "pieces"), "integer"),
    Field("shipper", ("shipper", "exporter", "consignor")),
    Field("consignee", ("consignee", "importer", "receiver")),
)

_REGISTRY: Dict[str, FormSchema] = {
    schema.name: schema
    for schema in (GENERIC, VEHICLE_INSPECTION, VEHICLE_REGISTRATION, SHIPPING_MANIFEST)
}


def get_schema(schema: "str | FormSchema") -> FormSchema:
    """Look up a schema by name, or pass a ``FormSchema`` straight through."""
    if isinstance(schema, FormSchema):
        return schema
    try:
        return _REGISTRY[schema]
    except KeyError:
        raise SchemaError(
            f"unknown schema '{schema}'; available: {', '.join(sorted(_REGISTRY))}"
        ) from None


def register_schema(schema: FormSchema) -> FormSchema:
    """Add a custom schema so it can be used by name."""
    _REGISTRY[schema.name] = schema
    return schema


def schema_names() -> Tuple[str, ...]:
    """Every schema name currently registered."""
    return tuple(sorted(_REGISTRY))
