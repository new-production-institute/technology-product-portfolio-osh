"""Deterministic qualification tests for portfolio conversion."""

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIRECTORY = REPOSITORY_ROOT / "src/script"
sys.path.insert(0, str(SCRIPT_DIRECTORY))

import portfolio_conversion as conversion  # noqa: E402


DOMAINS = {
    "health": ("Health", 138),
    "food": ("Food", 50),
    "construction": ("Construction", 17),
}


def load_json(path: Path) -> dict:
    """Load a UTF-8 JSON document."""
    return json.loads(path.read_text(encoding="utf-8"))


class TransformTests(unittest.TestCase):
    """Cover normalization rules shared by the schemas."""

    def test_csv_lists_preserve_quoted_commas(self):
        value = 'Fabrication and Assembly, "Cutting, Drilling, and Fastening"'
        self.assertEqual(
            conversion.csv_string_list(value),
            ["Fabrication and Assembly", "Cutting, Drilling, and Fastening"],
        )

    def test_reference_urls_preserve_order_and_normalize_doi(self):
        value = "10.1000/example https://example.org/resource 10.1000/example"
        self.assertEqual(
            conversion.reference_urls(value),
            ["https://doi.org/10.1000/example", "https://example.org/resource"],
        )

    def test_ranges_and_na(self):
        self.assertEqual(conversion.number_or_range("10-20"), {"minimum": 10, "maximum": 20})
        self.assertEqual(conversion.integer_or_range("3/5"), {"minimum": 3, "maximum": 5})
        self.assertIsNone(conversion.integer_or_range_or_na("NA"))
        with self.assertRaisesRegex(ValueError, "minimum exceeds maximum"):
            conversion.integer_or_range("7/2")

    def test_constant_mismatch_fails(self):
        properties = {
            "category": {
                "const": "Food",
                "x-source-column": "Category",
                "x-transform": "required-string",
            }
        }
        with self.assertRaisesRegex(ValueError, "expected 'Food'"):
            conversion.build_record(4, {"Category": "Health"}, properties)


class ParsingTests(unittest.TestCase):
    """Cover malformed input and row-selection behavior."""

    def test_duplicate_headers_fail(self):
        rows = [(2, ["Name", "Name"])]
        settings = {
            "rows": {"header": 2, "dataStart": 3},
            "skipRowWhenColumnIsBlank": "Name",
        }
        with self.assertRaisesRegex(ValueError, "duplicate headers"):
            conversion.source_records(rows, settings)

    def test_data_start_and_blank_name_are_enforced(self):
        rows = [(2, ["Name"]), (3, ["Example"]), (4, ["Real"]), (5, [])]
        settings = {
            "rows": {"header": 2, "dataStart": 4},
            "skipRowWhenColumnIsBlank": "Name",
        }
        _, records = conversion.source_records(rows, settings)
        self.assertEqual(records, [(4, {"Name": "Real"})])

    def test_missing_sheet_fails(self):
        workbook = REPOSITORY_ROOT / "res/var/data/technology-product-portfolio.ods"
        with self.assertRaisesRegex(ValueError, "has no 'Missing' worksheet"):
            conversion.load_sheet(workbook, "Missing")

    def test_atomic_write_replaces_complete_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "data.json"
            conversion.write_atomic(path, b"first\n")
            conversion.write_atomic(path, b"second\n")
            self.assertEqual(path.read_bytes(), b"second\n")


class GeneratedDataTests(unittest.TestCase):
    """Qualify generated output against its checked-in contracts."""

    def test_documents_match_schema_envelopes(self):
        workbook = REPOSITORY_ROOT / "res/var/data/technology-product-portfolio.ods"
        expected_digest = hashlib.sha256(workbook.read_bytes()).hexdigest()
        for domain, (sheet, count) in DOMAINS.items():
            with self.subTest(domain=domain):
                schema = load_json(REPOSITORY_ROOT / f"spec/{domain}/{domain}.schema.json")
                document = load_json(REPOSITORY_ROOT / f"res/var/data/{domain}.json")
                self.assertEqual(set(document), {"schemaVersion", "source", "records"})
                self.assertEqual(document["schemaVersion"], "1.0.0")
                self.assertEqual(document["source"]["sheet"], sheet)
                self.assertEqual(document["source"]["sha256"], expected_digest)
                self.assertEqual(len(document["records"]), count)
                self.assert_record_shape(document, schema)

    def assert_record_shape(self, document: dict, schema: dict) -> None:
        """Check required fields and core invariants for every record."""
        properties = conversion.record_properties(schema)
        expected_fields = set(properties)
        for record in document["records"]:
            self.assertEqual(set(record), expected_fields)
            self.assertTrue(record["name"].strip())
            self.assertGreaterEqual(record["sourceRow"], schema["x-conversion"]["rows"]["dataStart"])
            for field in ("urls", "manufacturingProcesses"):
                self.assertEqual(len(record[field]), len(set(record[field])))

    def test_template_records_are_absent(self):
        for domain in ("food", "construction"):
            document = load_json(REPOSITORY_ROOT / f"res/var/data/{domain}.json")
            names = {record["name"] for record in document["records"]}
            self.assertNotIn("Example project", names)

    def test_checked_in_json_is_deterministic(self):
        for domain in DOMAINS:
            schema = load_json(REPOSITORY_ROOT / f"spec/{domain}/{domain}.schema.json")
            path = REPOSITORY_ROOT / f"res/var/data/{domain}.json"
            expected = conversion.serialize_json(load_json(path), schema["x-conversion"]["serialization"])
            self.assertEqual(path.read_bytes(), expected)


if __name__ == "__main__":
    unittest.main()
