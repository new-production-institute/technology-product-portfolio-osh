#!/usr/bin/env python3
"""Convert the mirrored Food worksheet to JSON."""

from pathlib import Path

from portfolio_conversion import run_conversion


SCHEMA_PATH = Path(__file__).resolve().parents[2] / "spec/food/food.schema.json"


if __name__ == "__main__":
    raise SystemExit(run_conversion("Food", SCHEMA_PATH))
