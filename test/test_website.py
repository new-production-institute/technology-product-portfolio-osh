"""Dependency-free qualification tests for the static website."""

import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
PAGES = ("index.html", "health.html", "food.html", "construction.html")
TEXT_COLORS = ("#151515", "#5c625e", "#075e8c", "#b44a1c", "#a53a3a", "#2f6b49", "#8a5a13")
BACKGROUNDS = ("#ffffff", "#f6f4ee")


class PageParser(HTMLParser):
    """Collect structural facts from one HTML page."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.ids = set()
        self.duplicate_ids = set()
        self.references = []
        self.heading_levels = []
        self.label_targets = set()
        self.control_ids = set()
        self.body_attributes = {}

    def handle_starttag(self, tag, attributes):
        values = dict(attributes)
        identifier = values.get("id")
        if identifier in self.ids:
            self.duplicate_ids.add(identifier)
        if identifier:
            self.ids.add(identifier)
        if tag in {"a", "link"} and values.get("href"):
            self.references.append(values["href"])
        if tag == "script" and values.get("src"):
            self.references.append(values["src"])
        if tag in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            self.heading_levels.append(int(tag[1]))
        if tag == "label" and values.get("for"):
            self.label_targets.add(values["for"])
        if tag in {"input", "select", "textarea"} and identifier:
            self.control_ids.add(identifier)
        if tag == "body":
            self.body_attributes = values


def parse_page(path: Path) -> PageParser:
    """Parse one HTML document into audit facts."""
    parser = PageParser()
    parser.feed(path.read_text(encoding="utf-8"))
    parser.close()
    return parser


def local_target(page: Path, reference: str) -> Path | None:
    """Resolve a local reference or return None for non-file links."""
    if reference.startswith(("#", "data:", "http:", "https:", "mailto:")):
        return None
    path = unquote(urlsplit(reference).path)
    return (page.parent / path).resolve()


def relative_luminance(color: str) -> float:
    """Return WCAG relative luminance for an RGB hex color."""
    channels = [int(color[index : index + 2], 16) / 255 for index in (1, 3, 5)]
    linear = [value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4 for value in channels]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def contrast_ratio(foreground: str, background: str) -> float:
    """Return the WCAG contrast ratio for two colors."""
    lighter, darker = sorted(
        (relative_luminance(foreground), relative_luminance(background)), reverse=True
    )
    return (lighter + 0.05) / (darker + 0.05)


class WebsiteTests(unittest.TestCase):
    """Check durable files, semantics, and palette constraints."""

    def test_page_structure_and_labels(self):
        for name in PAGES:
            with self.subTest(page=name):
                path = REPOSITORY_ROOT / name
                parser = parse_page(path)
                self.assertTrue(path.read_text(encoding="utf-8").lower().startswith("<!doctype html>"))
                self.assertFalse(parser.duplicate_ids)
                self.assertEqual(parser.heading_levels.count(1), 1)
                self.assertTrue(parser.label_targets <= parser.control_ids)
                self.assertIn("main-content", parser.ids)
                for previous, current in zip(parser.heading_levels, parser.heading_levels[1:]):
                    self.assertLessEqual(current - previous, 1)

    def test_local_references_exist(self):
        repository = REPOSITORY_ROOT.resolve()
        for name in PAGES:
            page = REPOSITORY_ROOT / name
            for reference in parse_page(page).references:
                with self.subTest(page=name, reference=reference):
                    target = local_target(page, reference)
                    if target is None:
                        continue
                    self.assertTrue(target.is_relative_to(repository))
                    self.assertTrue(target.exists(), f"missing local reference: {reference}")

    def test_page_data_contracts(self):
        landing = parse_page(REPOSITORY_ROOT / "index.html")
        self.assertEqual(landing.body_attributes.get("data-page"), "landing")
        for domain in ("health", "food", "construction"):
            with self.subTest(domain=domain):
                parser = parse_page(REPOSITORY_ROOT / f"{domain}.html")
                self.assertEqual(parser.body_attributes.get("data-page"), "catalog")
                self.assertEqual(parser.body_attributes.get("data-domain"), domain)
                self.assertTrue((REPOSITORY_ROOT / f"res/var/data/{domain}.json").exists())

    def test_text_palette_meets_wcag_aa(self):
        for foreground in TEXT_COLORS:
            for background in BACKGROUNDS:
                with self.subTest(foreground=foreground, background=background):
                    self.assertGreaterEqual(contrast_ratio(foreground, background), 4.5)


if __name__ == "__main__":
    unittest.main()
