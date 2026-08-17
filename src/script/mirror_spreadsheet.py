#!/usr/bin/env python3
"""Mirror the portfolio's public Google spreadsheet as an ODS workbook."""

from __future__ import annotations

import argparse
import io
import os
import sys
import tempfile
import xml.etree.ElementTree as ElementTree
import zipfile
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen


SPREADSHEET_ID = "1QYfOAk3SBu_R4Y-irApLiYlAljDATvf5rRMBtY1dJFA"
REQUIRED_SHEETS = ("Health", "Food", "Construction")
REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_DIR = REPOSITORY_ROOT / "res" / "var" / "data"
OUTPUT_FILENAME = "technology-product-portfolio.ods"
ODS_MIMETYPE = b"application/vnd.oasis.opendocument.spreadsheet"
TABLE_NAMESPACE = "urn:oasis:names:tc:opendocument:xmlns:table:1.0"


def export_url(spreadsheet_id: str) -> str:
    """Return the ODS export URL for the spreadsheet."""
    query = urlencode({"format": "ods"})
    return f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/export?{query}"


def download_ods(spreadsheet_id: str, timeout: float) -> bytes:
    """Download the spreadsheet as ODS bytes."""
    request = Request(
        export_url(spreadsheet_id),
        headers={"User-Agent": "technology-product-portfolio-mirror/1.0"},
    )
    with urlopen(request, timeout=timeout) as response:
        data = response.read()
    if not data:
        raise ValueError("spreadsheet returned an empty response")
    return data


def validate_ods(data: bytes) -> list[str]:
    """Validate the ODS archive and return its worksheet names."""
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        corrupt_member = archive.testzip()
        if corrupt_member:
            raise ValueError(f"ODS archive contains a corrupt file: {corrupt_member}")
        try:
            mimetype = archive.read("mimetype")
            content = archive.read("content.xml")
        except KeyError as error:
            raise ValueError(f"ODS archive is missing {error.args[0]}") from error
        if mimetype != ODS_MIMETYPE:
            raise ValueError("download is not an ODS spreadsheet")

    root = ElementTree.fromstring(content)
    name_attribute = f"{{{TABLE_NAMESPACE}}}name"
    table_element = f".//{{{TABLE_NAMESPACE}}}table"
    sheet_names = [table.attrib[name_attribute] for table in root.findall(table_element)]
    missing = set(REQUIRED_SHEETS) - set(sheet_names)
    if missing:
        raise ValueError(f"ODS export is missing sheets: {', '.join(sorted(missing))}")
    return sheet_names


def write_atomic(path: Path, data: bytes) -> None:
    """Replace a file atomically with downloaded bytes."""
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


def mirror_spreadsheet(spreadsheet_id: str, output_dir: Path, timeout: float) -> str:
    """Download, validate, and write the configured spreadsheet."""
    data = download_ods(spreadsheet_id, timeout)
    sheet_names = validate_ods(data)
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / OUTPUT_FILENAME
    write_atomic(path, data)
    return f"{len(sheet_names)} sheets ({', '.join(sheet_names)}) -> {path}"


def parse_args() -> argparse.Namespace:
    """Parse command-line options."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spreadsheet-id", default=SPREADSHEET_ID)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--timeout", type=float, default=30.0)
    return parser.parse_args()


def main() -> int:
    """Run the spreadsheet mirror."""
    arguments = parse_args()
    if arguments.timeout <= 0:
        print("error: --timeout must be greater than zero", file=sys.stderr)
        return 2
    try:
        summary = mirror_spreadsheet(
            arguments.spreadsheet_id, arguments.output_dir, arguments.timeout
        )
    except (OSError, ElementTree.ParseError, ValueError, zipfile.BadZipFile) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    print(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
