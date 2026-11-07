#!/usr/bin/env python3
"""Export ONLY modern control points to GeoJSON (never historical village centers)."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from validate_data import ROOT, validate

def export_points(data_dir: Path = ROOT / "data") -> dict:
    problems = validate(data_dir)
    if problems:
        raise ValueError("Invalid research dataset: " + "; ".join(problems))
    features = []
    with (data_dir / "control_points.csv").open(encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            features.append({
                "type": "Feature",
                "id": row["control_id"],
                "geometry": {"type": "Point", "coordinates": [float(row["longitude"]), float(row["latitude"])]},
                "properties": {
                    "label": row["label"],
                    "kind": row["kind"],
                    "address_or_description": row["address_or_description"],
                    "verification": row["verification"],
                    "source_url": row["source_url"],
                    "warning": row["historical_scope_warning"],
                    "historical_location_confirmed": False,
                },
            })
    return {
        "type": "FeatureCollection",
        "name": "Modern control points (NOT historic village locations)",
        "features": features,
    }

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=ROOT / "data")
    parser.add_argument("--output", type=Path, default=ROOT / "outputs" / "control_points.geojson")
    args = parser.parse_args()
    geojson = export_points(args.data_dir)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(geojson, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Exported {len(geojson['features'])} modern points to {args.output}")

if __name__ == "__main__":
    main()
