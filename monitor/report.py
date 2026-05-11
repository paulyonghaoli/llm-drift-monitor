from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from monitor.drift import evaluate_snapshot
from monitor.utils import load_json


def _ascii_table(category_drifts: Dict[str, float]) -> str:
    rows = ["Category | Drift", "--- | ---"]
    for category, drift in sorted(category_drifts.items()):
        rows.append(f"{category} | {drift:.3f}")
    return "\n".join(rows)


def _select_top_drifted(per_snapshot: Dict[str, Any]) -> str:
    rows = ["Probe ID | Distance | Coverage Drop | Query"]
    rows.append("--- | --- | --- | ---")
    for entry in per_snapshot["top_drifted"]:
        rows.append(f"{entry['id']} | {entry['distance']:.3f} | {entry['coverage_drop']:.2f} | {entry['query']}")
    return "\n".join(rows)


def generate_report(baseline_path: Path, snapshot_dir: Path, report_path: Path) -> Path:
    baseline = load_json(baseline_path)
    snapshots = sorted(snapshot_dir.glob("snapshot_*.json"))
    if not snapshots:
        raise FileNotFoundError("No snapshots found to generate a report.")

    sections: List[str] = ["# Drift Report", "", "## Summary"]
    sections.append(f"Baseline: {baseline_path.name}")
    sections.append(f"Snapshots analyzed: {len(snapshots)}")
    sections.append("")

    for snapshot_path in snapshots:
        snapshot_result = evaluate_snapshot(baseline_path, snapshot_path)
        sections.append(f"## Snapshot {snapshot_path.name}")
        sections.append(f"- Verdict: {snapshot_result['verdict']}" )
        sections.append(f"- Drift score: {snapshot_result['drift_score']:.3f}")
        sections.append(f"- Overall centroid drift: {snapshot_result['overall_drift']:.3f}")
        sections.append("")
        sections.append("### Category drift")
        sections.append(_ascii_table(snapshot_result["category_drifts"]))
        sections.append("")
        sections.append("### Most drifted probes")
        sections.append(_select_top_drifted(snapshot_result))
        sections.append("")

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(sections), encoding="utf-8")
    return report_path
