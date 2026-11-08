"""Regression tests for source-aware Ulsan toponymy research."""
from __future__ import annotations

import csv
import shutil
import sys
import tempfile
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

    def _validate_with_parcel_edit(self, column, value):
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp)
            for path in (ROOT / "data").glob("*.csv"):
                shutil.copy(path, data_dir / path.name)
            target = data_dir / "parcels_research.csv"
            with target.open(encoding="utf-8", newline="") as file:
                reader = csv.DictReader(file)
                fieldnames = reader.fieldnames
                rows = list(reader)
            rows[0][column] = value
            with target.open("w", encoding="utf-8", newline="") as file:
                writer = csv.DictWriter(file, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
                writer.writeheader()
                writer.writerows(rows)
            return validate(data_dir)

    def test_parcel_village_must_be_attested(self):
        errors = self._validate_with_parcel_edit("historic_village", "栢川洞/굴화리")
        self.assertTrue(any("historic_village not attested" in error for error in errors))

    def test_parcel_coordinates_cannot_be_marked_verified(self):
        errors = self._validate_with_parcel_edit("coordinate_status", "verified")
        self.assertTrue(any("coordinate_status changed" in error for error in errors))

    def test_parcel_lookups_are_unverified_modern_proxies(self):
        with (ROOT / "data" / "parcels_research.csv").open(encoding="utf-8", newline="") as file:
            rows = list(csv.DictReader(file))
        self.assertEqual({"GUL-010", "GUL-011", "GUL-014", "GUL-015"}, {row["toponym_id"] for row in rows})
        self.assertTrue(all(row["coordinate_status"] == "private_geocoder_unverified" for row in rows))

    def test_dossier_claims_stay_unconfirmed(self):
        with (ROOT / "data" / "claims.csv").open(encoding="utf-8", newline="") as file:
            rows = {row["claim_id"]: row for row in csv.DictReader(file)}
        self.assertEqual("hypothesis", rows["CL-009"]["evidence_status"])
        self.assertEqual("hypothesis", rows["CL-010"]["evidence_status"])
        for claim_id in ("CL-013", "CL-015", "CL-020", "CL-021"):
            self.assertEqual("pending", rows[claim_id]["evidence_status"])
        self.assertEqual("disputed", rows["CL-022"]["evidence_status"])

    def test_1911_holding_record_correction(self):
        with (ROOT / "data" / "claims.csv").open(encoding="utf-8", newline="") as file:
            claims = {row["claim_id"]: row for row in csv.DictReader(file)}
        with (ROOT / "data" / "sources.csv").open(encoding="utf-8", newline="") as file:
            sources = {row["source_id"]: row for row in csv.DictReader(file)}
        # The dossier call number 古2150-1-32 did not match the NLK catalogue.
        self.assertEqual("rejected", claims["CL-018"]["evidence_status"])
        self.assertIn("古貴2703-1", claims["CL-023"]["claim"])
        # Catalogue checked, but the Ulsan pages themselves are still unread.
        self.assertEqual("catalog_verified", sources["SRC-008"]["access_status"])
        self.assertIn("미열람", sources["SRC-008"]["note"])


if __name__ == "__main__":
    unittest.main()
