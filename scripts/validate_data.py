#!/usr/bin/env python3
"""Validate the research corpus using only Python standard library."""
from __future__ import annotations

import argparse
import csv
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FEATURE_TYPES = {"village", "valley", "field", "unmatched_citation"}
EVIDENCE = {"source_verified", "secondary_quote", "hypothesis", "pending", "disputed", "rejected"}
LOCATION = {"none", "relative", "parcel_clue"}
ACCESS = {
    "pdf_pages_checked", "online_checked", "abstract_checked",
    "citation_identified", "not_obtained", "needs_official_recheck",
}
# Coordinates in parcels_research.csv are modern lookups; none is verified yet.
PARCEL_COORD_STATUS = {"private_geocoder_unverified", "official_lookup_pending_review"}
CHECKS = {
    "toponyms.csv": {
        "id_col": "toponym_id",
        "fields": ["toponym_id", "name", "feature_type", "location_precision", "evidence_status", "source_id"],
        "expected": 37,
    },
    "control_points.csv": {
        "id_col": "control_id",
        "fields": ["control_id", "label", "kind", "latitude", "longitude", "verification", "historical_scope_warning"],
        "expected": 4,
    },
    "sources.csv": {
        "id_col": "source_id",
        "fields": ["source_id", "title", "kind", "access_status"],
        "expected": None,
    },
    "claims.csv": {
        "id_col": "claim_id",
        "fields": ["claim_id", "claim", "source_ids", "evidence_status", "spatial_status", "next_check"],
        "expected": None,
    },
    "parcels_research.csv": {
        "id_col": "toponym_id",
        "fields": [
            "toponym_id", "canonical_name", "historic_parcel", "road_name_address", "latitude", "longitude",
            "coordinate_system", "source_id", "coordinate_status", "claim_id", "historical_scope_warning",
        ],
        "expected": None,
    },
}

def read_csv(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    if not path.exists():
        return [], [f"missing file: {path}"]
    with path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        if not reader.fieldnames:
            return [], [f"empty csv header: {path}"]
        if any(None in row for row in rows):
            return rows, [f"row wider than header: {path}"]
    return rows, []

def validate(data_dir: Path = ROOT / "data") -> list[str]:
    errors: list[str] = []
    loaded: dict[str, list[dict[str, str]]] = {}

    for filename, config in CHECKS.items():
        rows, issues = read_csv(data_dir / filename)
        errors.extend(issues)
        loaded[filename] = rows
        if issues:
            continue
        header = set(rows[0].keys()) if rows else set()
        missing_headers = set(config["fields"]) - header
        if missing_headers:
            errors.append(f"{filename}: missing columns {sorted(missing_headers)}")
            continue
        if config["expected"] is not None and len(rows) != config["expected"]:
            errors.append(f"{filename}: expected {config['expected']} rows, got {len(rows)}")
        seen = set()
        for idx, row in enumerate(rows, start=2):
            rid = row.get(config["id_col"], "")
            if not rid:
                errors.append(f"{filename}:{idx}: missing id")
            if rid in seen:
                errors.append(f"{filename}:{idx}: duplicate id {rid}")
            seen.add(rid)
            for col in config["fields"]:
                if not (row.get(col) or "").strip():
                    errors.append(f"{filename}:{idx}: missing {col}")

    sources = {row.get("source_id") for row in loaded["sources.csv"]}
    for i, row in enumerate(loaded["sources.csv"], 2):
        if row.get("access_status") not in ACCESS:
            errors.append(f"sources.csv:{i}: invalid access_status {row.get('access_status')}")
    names = loaded["toponyms.csv"]
    counts = Counter(row.get("feature_type") for row in names)
    if counts != Counter({"village": 4, "valley": 21, "field": 8, "unmatched_citation": 4}):
        errors.append(f"toponyms.csv: unexpected category counts {dict(counts)}")
    for i, row in enumerate(names, 2):
        rid = row.get("toponym_id", "")
        if not re.fullmatch(r"GUL-\d{3}", rid):
            errors.append(f"toponyms.csv:{i}: invalid toponym_id {rid}")
        if row.get("feature_type") not in FEATURE_TYPES:
            errors.append(f"toponyms.csv:{i}: invalid feature_type")
        if row.get("location_precision") not in LOCATION:
            errors.append(f"toponyms.csv:{i}: invalid location_precision")
        if row.get("evidence_status") not in EVIDENCE:
            errors.append(f"toponyms.csv:{i}: invalid evidence_status")
        if row.get("source_id") not in sources:
            errors.append(f"toponyms.csv:{i}: undefined source_id")
        if row.get("location_precision") == "parcel_clue" and not row.get("parcel_clue"):
            errors.append(f"toponyms.csv:{i}: parcel clue without parcel")
        if row.get("feature_type") == "unmatched_citation" and row.get("location_precision") != "none":
            errors.append(f"toponyms.csv:{i}: unmatched original has invented location")

    for i, row in enumerate(loaded["control_points.csv"], 2):
        try:
            lat, lon = float(row["latitude"]), float(row["longitude"])
            if not (33 <= lat <= 39 and 124 <= lon <= 132):
                errors.append(f"control_points.csv:{i}: coordinates outside expected Korea bounds")
        except (ValueError, KeyError, TypeError):
            errors.append(f"control_points.csv:{i}: invalid coordinates")
        if row.get("verification") != "pending_official_recheck":
            errors.append(f"control_points.csv:{i}: verification changed without method review")
        if not row.get("source_url", "").startswith("https://"):
            errors.append(f"control_points.csv:{i}: missing HTTPS source")
    for i, row in enumerate(loaded["claims.csv"], 2):
        if row.get("evidence_status") not in EVIDENCE:
            errors.append(f"claims.csv:{i}: invalid evidence_status")
        for source_id in row.get("source_ids", "").split("|"):
            if source_id not in sources:
                errors.append(f"claims.csv:{i}: unknown source ID {source_id}")

    claims = {row.get("claim_id") for row in loaded["claims.csv"]}
    toponyms = {row.get("toponym_id"): row for row in names}
    for i, row in enumerate(loaded["parcels_research.csv"], 2):
        ref = toponyms.get(row.get("toponym_id"))
        if ref is None:
            errors.append(f"parcels_research.csv:{i}: unknown toponym_id {row.get('toponym_id')}")
            continue
        if row.get("canonical_name") != ref.get("name"):
            errors.append(f"parcels_research.csv:{i}: canonical_name differs from toponyms.csv")
        if row.get("historic_parcel") != ref.get("parcel_clue"):
            errors.append(f"parcels_research.csv:{i}: historic_parcel differs from toponyms.csv parcel_clue")
        village = row.get("historic_village", "")
        if village and village != ref.get("quoted_1911_village"):
            errors.append(f"parcels_research.csv:{i}: historic_village not attested in toponyms.csv")
        if row.get("coordinate_status") not in PARCEL_COORD_STATUS:
            errors.append(f"parcels_research.csv:{i}: coordinate_status changed without method review")
        if row.get("coordinate_system") != "WGS84":
            errors.append(f"parcels_research.csv:{i}: unexpected coordinate_system")
        try:
            lat, lon = float(row["latitude"]), float(row["longitude"])
            if not (33 <= lat <= 39 and 124 <= lon <= 132):
                errors.append(f"parcels_research.csv:{i}: coordinates outside expected Korea bounds")
        except (ValueError, KeyError, TypeError):
            errors.append(f"parcels_research.csv:{i}: invalid coordinates")
        for source_id in row.get("source_id", "").split("|"):
            if source_id not in sources:
                errors.append(f"parcels_research.csv:{i}: unknown source ID {source_id}")
        for claim_id in row.get("claim_id", "").split("|"):
            if claim_id not in claims:
                errors.append(f"parcels_research.csv:{i}: unknown claim ID {claim_id}")

    return errors

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=ROOT / "data")
    args = parser.parse_args()
    errors = validate(args.data_dir)
    if errors:
        for error in errors:
            print("ERROR:", error, file=sys.stderr)
        return 1
    print("OK: 37 toponyms, 4 modern control points, parcel lookups, linked sources and claims")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
