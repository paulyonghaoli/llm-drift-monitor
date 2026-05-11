from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional


def _short_snippet(text: str, limit: int = 120) -> str:
    snippet = text.replace("\n", " ").strip()
    if len(snippet) <= limit:
        return snippet
    return snippet[: limit - 3].rstrip() + "..."


def write_alert(drift_result: Dict[str, Any], snapshot_path: Path) -> Path:
    timestamp = snapshot_path.stem.replace("snapshot_", "")
    alert = {
        "snapshot": snapshot_path.name,
        "drift_score": drift_result["drift_score"],
        "verdict": drift_result["verdict"],
        "overall_drift": drift_result["overall_drift"],
        "category_drifts": drift_result["category_drifts"],
        "affected_probes": [
            {
                "id": entry["id"],
                "query": entry["query"],
                "distance": entry["distance"],
                "coverage_drop": entry["coverage_drop"],
                "base_response": _short_snippet(entry["base_response"], limit=200),
                "snapshot_response": _short_snippet(entry["snapshot_response"], limit=200),
            }
            for entry in drift_result["top_drifted"]
        ],
    }
    alert_dir = Path("alerts")
    alert_dir.mkdir(parents=True, exist_ok=True)
    alert_path = alert_dir / f"alert_{timestamp}.json"
    with alert_path.open("w", encoding="utf-8") as handle:
        json.dump(alert, handle, indent=2, ensure_ascii=False)
    return alert_path


def print_alert(drift_result: Dict[str, Any], alert_path: Optional[Path]) -> None:
    print("\n=== Drift Monitor Result ===")
    print(f"Verdict: {drift_result['verdict']}")
    print(f"Drift score: {drift_result['drift_score']:.3f}")
    print(f"Overall centroid drift: {drift_result['overall_drift']:.3f}")
    print("Category drift:")
    for category, value in drift_result["category_drifts"].items():
        print(f"  - {category}: {value:.3f}")
    if alert_path is not None:
        print(f"Significant drift detected. Alert written to {alert_path}")
    else:
        print("No alert generated; drift remains below the significance threshold.")
