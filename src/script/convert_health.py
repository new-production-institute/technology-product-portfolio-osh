#!/usr/bin/env python3
"""Convert the mirrored Health worksheet to a schema-shaped JavaScript module."""

from __future__ import annotations

import csv
import hashlib
import json
import os
import re
import sys
import tempfile
import xml.etree.ElementTree as ElementTree
import zipfile
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = REPOSITORY_ROOT / "spec" / "health" / "health.schema.json"
TABLE_NAMESPACE = "urn:oasis:names:tc:opendocument:xmlns:table:1.0"
TEXT_NAMESPACE = "urn:oasis:names:tc:opendocument:xmlns:text:1.0"
OFFICE_NAMESPACE = "urn:oasis:names:tc:opendocument:xmlns:office:1.0"
TABLE = f"{{{TABLE_NAMESPACE}}}table"
TABLE_ROW = f"{{{TABLE_NAMESPACE}}}table-row"
TABLE_CELL = f"{{{TABLE_NAMESPACE}}}table-cell"
COVERED_CELL = f"{{{TABLE_NAMESPACE}}}covered-table-cell"
TABLE_NAME = f"{{{TABLE_NAMESPACE}}}name"
COLUMN_REPEAT = f"{{{TABLE_NAMESPACE}}}number-columns-repeated"
ROW_REPEAT = f"{{{TABLE_NAMESPACE}}}number-rows-repeated"
TEXT_PARAGRAPH = f".//{{{TEXT_NAMESPACE}}}p"
TEXT_SPACE = f"{{{TEXT_NAMESPACE}}}s"
TEXT_TAB = f"{{{TEXT_NAMESPACE}}}tab"
TEXT_LINE_BREAK = f"{{{TEXT_NAMESPACE}}}line-break"
TEXT_SPACE_COUNT = f"{{{TEXT_NAMESPACE}}}c"
OFFICE_VALUE = f"{{{OFFICE_NAMESPACE}}}value"
URL_PATTERN = re.compile(r"https?://[^\s]+")
DOI_PATTERN = re.compile(r"(?<![/\w])10\.\d{4,9}/[^\s]+")
NUMBER_PATTERN = r"(?:0|[1-9]\d*)(?:\.\d+)?"
NUMBER_RANGE_PATTERN = re.compile(rf"^({NUMBER_PATTERN})\s*-\s*({NUMBER_PATTERN})$")
TRL_PATTERN = re.compile(r"^([1-9])(?:\s*/\s*([1-9]))?$")


def load_schema(path: Path) -> dict:
    """Load the conversion schema."""
    with path.open(encoding="utf-8") as schema_file:
        return json.load(schema_file)


def repository_path(value: str) -> Path:
    """Resolve a schema path relative to the repository."""
    path = Path(value)
    return path if path.is_absolute() else REPOSITORY_ROOT / path


def load_sheet(path: Path, sheet_name: str) -> ElementTree.Element:
    """Load one worksheet element from an ODS archive."""
    with zipfile.ZipFile(path) as archive:
        corrupt_member = archive.testzip()
        if corrupt_member:
            raise ValueError(f"ODS archive contains a corrupt file: {corrupt_member}")
        try:
            content = archive.read("content.xml")
        except KeyError as error:
            raise ValueError("ODS archive is missing content.xml") from error
    root = ElementTree.fromstring(content)
    for table in root.iter(TABLE):
        if table.get(TABLE_NAME) == sheet_name:
            return table
    raise ValueError(f"ODS archive has no {sheet_name!r} worksheet")


def element_text(element: ElementTree.Element) -> str:
    """Extract ODF text while honoring explicit whitespace elements."""
    parts = [element.text or ""]
    for child in element:
        if child.tag == TEXT_SPACE:
            parts.append(" " * int(child.get(TEXT_SPACE_COUNT, "1")))
        elif child.tag == TEXT_TAB:
            parts.append("\t")
        elif child.tag == TEXT_LINE_BREAK:
            parts.append("\n")
        else:
            parts.append(element_text(child))
        parts.append(child.tail or "")
    return "".join(parts)


def cell_text(cell: ElementTree.Element, separator: str) -> str:
    """Extract visible text from one ODS cell."""
    paragraphs = cell.findall(TEXT_PARAGRAPH)
    text = separator.join(element_text(paragraph) for paragraph in paragraphs)
    return (text if paragraphs else cell.get(OFFICE_VALUE, "")).strip()


def row_values(row: ElementTree.Element, separator: str) -> list[str]:
    """Expand one ODS row while bounding repeated empty columns."""
    values = []
    for cell in row:
        if cell.tag not in {TABLE_CELL, COVERED_CELL}:
            continue
        repeat = int(cell.get(COLUMN_REPEAT, "1"))
        value = "" if cell.tag == COVERED_CELL else cell_text(cell, separator)
        values.extend([value] * min(repeat, 1024 - len(values)))
        if len(values) == 1024:
            break
    while values and not values[-1]:
        values.pop()
    return values


def nonempty_rows(table: ElementTree.Element, separator: str) -> list[tuple[int, list[str]]]:
    """Return logical row numbers and values without expanding empty row runs."""
    result = []
    logical_row = 1
    for row in table.findall(TABLE_ROW):
        repeat = int(row.get(ROW_REPEAT, "1"))
        values = row_values(row, separator)
        if values:
            result.extend((logical_row + offset, values) for offset in range(repeat))
        logical_row += repeat
    return result


def source_records(rows: list, conversion: dict) -> tuple[list[str], list[tuple[int, dict]]]:
    """Map logical ODS rows to dictionaries keyed by normalized headers."""
    header_number = conversion["rows"]["header"]
    headers = next((values for number, values in rows if number == header_number), None)
    if not headers or len(headers) != len(set(headers)):
        raise ValueError("Health worksheet has missing or duplicate headers")
    headers = list(headers)
    unnamed = conversion.get("unnamedColumns", {}).items()
    for column, name in sorted(unnamed, key=lambda item: int(item[0])):
        if int(column) != len(headers) + 1:
            raise ValueError(f"unnamed source column {column} is not contiguous")
        headers.append(name)
    records = []
    for row_number, values in rows:
        if row_number < conversion["rows"]["dataStart"]:
            continue
        if any(values[len(headers) :]):
            raise ValueError(f"row {row_number} contains data beyond the header columns")
        padded = values + [""] * (len(headers) - len(values))
        source = dict(zip(headers, padded))
        if source[conversion["skipRowWhenColumnIsBlank"]]:
            records.append((row_number, source))
    return headers, records


def validate_mapping(headers: list[str], schema: dict) -> dict:
    """Validate schema columns, properties, and transform identifiers."""
    definition = schema["$defs"]["healthRecord"]
    properties = definition["properties"]
    required = set(definition["required"])
    if required != set(properties):
        raise ValueError("Health schema properties and required fields differ")
    mapped = {
        rules["x-source-column"]
        for rules in properties.values()
        if "x-source-column" in rules
    }
    if mapped != set(headers):
        difference = ", ".join(sorted(mapped ^ set(headers)))
        raise ValueError(f"Health schema and worksheet columns differ: {difference}")
    configured = schema["x-conversion"]["transforms"]
    unknown = {rules["x-transform"] for rules in properties.values()} - set(configured)
    if unknown:
        raise ValueError(f"Health schema has undefined transforms: {', '.join(unknown)}")
    return properties


def nullable_string(value: str) -> str | None:
    """Normalize an optional string."""
    normalized = value.strip()
    return normalized or None


def required_string(value: str) -> str:
    """Normalize a required string."""
    normalized = value.strip()
    if not normalized:
        raise ValueError("required string is empty")
    return normalized


def csv_string_list(value: str) -> list[str]:
    """Parse one CSV-encoded list and remove duplicate items."""
    if not value:
        return []
    items = (item.strip() for item in next(csv.reader([value], strict=True)))
    return list(dict.fromkeys(item for item in items if item))


def reference_urls(value: str) -> list[str]:
    """Extract HTTP URLs and normalize bare DOIs while preserving order."""
    matches = [(match.start(), match.group()) for match in URL_PATTERN.finditer(value)]
    matches.extend(
        (match.start(), f"https://doi.org/{match.group()}")
        for match in DOI_PATTERN.finditer(value)
    )
    ordered = (url for _, url in sorted(matches))
    return list(dict.fromkeys(ordered))


def json_number(value: str) -> int | float:
    """Parse a non-negative plain JSON number."""
    if not re.fullmatch(NUMBER_PATTERN, value):
        raise ValueError(f"invalid number {value!r}")
    return float(value) if "." in value else int(value)


def number_or_range(value: str) -> int | float | dict | None:
    """Parse an optional number or inclusive hyphen-separated range."""
    if not value:
        return None
    match = NUMBER_RANGE_PATTERN.fullmatch(value)
    if not match:
        return json_number(value)
    minimum, maximum = (json_number(part) for part in match.groups())
    if minimum > maximum:
        raise ValueError("number range minimum exceeds maximum")
    return {"minimum": minimum, "maximum": maximum}


def integer_or_range(value: str) -> int | dict | None:
    """Parse an optional TRL integer or inclusive slash-separated range."""
    if not value:
        return None
    match = TRL_PATTERN.fullmatch(value)
    if not match:
        raise ValueError(f"invalid TRL {value!r}")
    minimum = int(match.group(1))
    if not match.group(2):
        return minimum
    maximum = int(match.group(2))
    if minimum > maximum:
        raise ValueError("TRL range minimum exceeds maximum")
    return {"minimum": minimum, "maximum": maximum}


def source_row_number(value: int) -> int:
    """Return a validated one-based source row number."""
    if value < 1:
        raise ValueError("source row number must be positive")
    return value


TRANSFORMS = {
    "source-row-number": source_row_number,
    "required-string": required_string,
    "nullable-string": nullable_string,
    "csv-string-list": csv_string_list,
    "http-url-and-doi-list": reference_urls,
    "number-or-hyphen-range": number_or_range,
    "integer-or-slash-range": integer_or_range,
}


def build_record(row_number: int, source: dict, properties: dict) -> dict:
    """Transform one source row according to schema annotations."""
    record = {}
    for name, rules in properties.items():
        transform_name = rules["x-transform"]
        if transform_name not in TRANSFORMS:
            raise ValueError(f"converter does not implement {transform_name!r}")
        raw_value = source.get(rules.get("x-source-column"), row_number)
        try:
            record[name] = TRANSFORMS[transform_name](raw_value)
        except (TypeError, ValueError, csv.Error) as error:
            raise ValueError(f"row {row_number}, field {name}: {error}") from error
    return record


def sha256_file(path: Path) -> str:
    """Return the SHA-256 digest of a file."""
    digest = hashlib.sha256()
    with path.open("rb") as source_file:
        for chunk in iter(lambda: source_file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_document(schema: dict, input_path: Path, records: list[dict]) -> dict:
    """Build the schema-shaped export document."""
    root_properties = schema["properties"]
    source_properties = root_properties["source"]["properties"]
    return {
        "schemaVersion": root_properties["schemaVersion"]["const"],
        "source": {
            "workbook": source_properties["workbook"]["const"],
            "sheet": source_properties["sheet"]["const"],
            "sha256": sha256_file(input_path),
        },
        "records": records,
    }


def serialize_module(document: dict, settings: dict) -> bytes:
    """Serialize the document as the configured JavaScript module."""
    if settings.get("format") != "javascript-es-module":
        raise ValueError("unsupported output format")
    if settings.get("export") != "default":
        raise ValueError("unsupported JavaScript export style")
    indent = settings.get("jsonIndent", 2)
    payload = json.dumps(document, ensure_ascii=False, indent=indent)
    content = "// Generated by src/script/convert_health.py.\nexport default "
    return f"{content}{payload};\n".encode("utf-8")


def write_atomic(path: Path, data: bytes) -> None:
    """Replace a file atomically with generated bytes."""
    descriptor, temporary_name = tempfile.mkstemp(
        dir=path.parent, prefix=f".{path.name}.", suffix=".tmp"
    )
    try:
        with os.fdopen(descriptor, "wb") as temporary_file:
            temporary_file.write(data)
            temporary_file.flush()
            os.fsync(temporary_file.fileno())
        os.replace(temporary_name, path)
    except BaseException:
        Path(temporary_name).unlink(missing_ok=True)
        raise


def convert_health(schema_path: Path) -> tuple[Path, int]:
    """Convert the Health worksheet using its schema annotations."""
    schema = load_schema(schema_path)
    conversion = schema["x-conversion"]
    input_path = repository_path(conversion["input"])
    output_path = repository_path(conversion["output"])
    table = load_sheet(input_path, conversion["sheet"])
    separator = conversion["cellText"]["paragraphSeparator"]
    rows = nonempty_rows(table, separator)
    headers, sources = source_records(rows, conversion)
    properties = validate_mapping(headers, schema)
    records = [build_record(number, source, properties) for number, source in sources]
    document = build_document(schema, input_path, records)
    data = serialize_module(document, conversion["serialization"])
    output_path.parent.mkdir(parents=True, exist_ok=True)
    write_atomic(output_path, data)
    return output_path, len(records)


def main() -> int:
    """Run the Health worksheet conversion."""
    try:
        output_path, record_count = convert_health(SCHEMA_PATH)
    except (OSError, KeyError, ValueError, ElementTree.ParseError, zipfile.BadZipFile) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    print(f"Health: {record_count} records -> {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
