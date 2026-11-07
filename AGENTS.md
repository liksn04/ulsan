# Research agent instructions

This repository is a **historical toponymy research corpus**, not a game-map or tourist database.

1. Answer in Korean unless requested otherwise. Never present reconstruction hypotheses as confirmed archaeological/administrative boundaries.
2. Always consult `docs/02-sources-and-evidence.md` and `docs/03-toponymy-and-errata.md` before introducing or changing a historical claim.
3. Do not silently "fix" a transcribed historical name: preserve diplomatic transcription, normalized reading, page, source ID, and the reason for the change.
4. The 2018 toponym compendium quotes the 1911 `조선지지자료`; do not claim direct access to 1911 unless that source is actually obtained.
5. Treat modern POI/control-point coordinates as *modern reference points*, never the center/boundary of 1911 villages. No made-up coordinates.
6. Keep the 37 existing `toponym_id` keys stable; use a new ID for a newly established record, not a reused ID.
7. Maintain source URLs, provenance, confidence, and open questions. Cite public source URLs with precise page references when known.
8. Add assertions to `data/claims.csv` for new historical conclusions and test schema validations before committing.
9. Do not upload copyrighted archival maps/PDFs or personal interview recordings without rights/consent.
10. Run `python scripts/validate_data.py` and `python -m unittest discover -s tests -v` after data/code edits.

Next task priority: acquire and transcribe original 1911 source; identify and georeference original cadastral maps; verify the `물탕골` parcel linkage.
