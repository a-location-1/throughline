import json
from pathlib import Path


def test_manifest_entries_have_sources_and_expected_paths():
    root = Path(__file__).parents[1] / "fixtures"
    manifest = json.loads((root / "manifest.json").read_text())
    assert manifest["cases"]
    for case in manifest["cases"]:
        assert (root / case["source"]).exists()
        assert (root / case["expected"]).exists()
