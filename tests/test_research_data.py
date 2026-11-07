"""Regression tests for source-aware Ulsan toponymy research."""
from __future__ import annotations

import csv
import sys
import unittest
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from validate_data import validate  # noqa: E402
from export_geojson import export_points  # noqa: E402


class ResearchDataTest(unittest.TestCase):
    def test_validate_all(self):
        self.assertEqual([], validate(ROOT / "data"))

    def test_canonical_toponym_counts(self):
        with (ROOT / "data" / "toponyms.csv").open(encoding="utf-8", newline="") as file:
            rows = list(csv.DictReader(file))
        self.assertEqual(37, len(rows))
        self.assertEqual(
            Counter({"village": 4, "valley": 21, "field": 8, "unmatched_citation": 4}),
            Counter(row["feature_type"] for row in rows),
        )

    def test_corrected_transcriptions(self):
        with (ROOT / "data" / "toponyms.csv").open(encoding="utf-8", newline="") as file:
            rows = {row["toponym_id"]: row for row in csv.DictReader(file)}
        self.assertEqual(rows["GUL-006"]["name"], "굴안골")
        self.assertEqual(rows["GUL-012"]["name"], "분닭골")
        self.assertEqual(rows["GUL-013"]["name"], "불쌍골")
        self.assertEqual(rows["GUL-031"]["quoted_1911_hanja"], "將板坪 / 長灘坪")
        self.assertEqual(rows["GUL-034"]["quoted_1911_hanja"], "鳥川谷")
        self.assertEqual(rows["GUL-032"]["name"], "행고들")

    def test_geojson_has_modern_points_only(self):
        collection = export_points(ROOT / "data")
        self.assertEqual("FeatureCollection", collection["type"])
        self.assertEqual(4, len(collection["features"]))
        self.assertTrue(all(
            not feature["properties"]["historical_location_confirmed"]
            for feature in collection["features"]
        ))
        for feature in collection["features"]:
            lon, lat = feature["geometry"]["coordinates"]
            self.assertGreater(lon, lat)  # East longitude vs North latitude in Korea.

if __name__ == "__main__":
    unittest.main()
