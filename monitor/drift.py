from __future__ import annotations

import math
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np
from monitor.utils import load_json


def _cosine_distance(a: List[float], b: List[float]) -> float:
    array_a = np.array(a, dtype=np.float64)
    array_b = np.array(b, dtype=np.float64)
    denom = np.linalg.norm(array_a) * np.linalg.norm(array_b)
    if denom == 0:
        return 0.0
    similarity = np.dot(array_a, array_b) / denom
    return float(max(0.0, 1.0 - similarity))


def _mean_embedding(entries: List[Dict[str, Any]]) -> List[float]:
    embeddings = np.array([entry["embedding"] for entry in entries], dtype=np.float64)
    mean_vec = np.mean(embeddings, axis=0)
    return mean_vec.tolist()


def _keyword_coverage(text: str, keywords: List[str]) -> float:
    if not keywords:
        return 1.0
    normalized = text.lower()
    found = sum(1 for keyword in keywords if keyword.lower() in normalized)
    return found / len(keywords)


def compare_snapshots(baseline: Dict[str, Any], snapshot: Dict[str, Any], drift_threshold: float = 0.25, keyword_drop_threshold: float = 0.2) -> Dict[str, Any]:
    baseline_probes = {entry["id"]: entry for entry in baseline["probes"]}
    snapshot_probes = {entry["id"]: entry for entry in snapshot["probes"]}
    categories = defaultdict(list)
    per_probe = []
    keyword_issues = []

    for probe_id, base_entry in baseline_probes.items():
        snap_entry = snapshot_probes[probe_id]
        distance = _cosine_distance(base_entry["embedding"], snap_entry["embedding"])
        category = base_entry["category"]
        categories[category].append((base_entry, snap_entry, distance))

        base_coverage = _keyword_coverage(base_entry["response"], base_entry.get("expected_keywords", []))
        snapshot_coverage = _keyword_coverage(snap_entry["response"], base_entry.get("expected_keywords", []))
        coverage_drop = max(0.0, base_coverage - snapshot_coverage)
        keyword_issues.append({
            "id": probe_id,
            "query": base_entry["query"],
            "coverage_drop": coverage_drop,
            "base_coverage": base_coverage,
            "snapshot_coverage": snapshot_coverage,
        })
        per_probe.append({
            "id": probe_id,
            "query": base_entry["query"],
            "category": category,
            "distance": distance,
            "coverage_drop": coverage_drop,
            "base_response": base_entry["response"],
            "snapshot_response": snap_entry["response"],
        })

    category_drifts = {}
    for category, rows in categories.items():
        baseline_embeddings = [row[0]["embedding"] for row in rows]
        snapshot_embeddings = [row[1]["embedding"] for row in rows]
        category_drifts[category] = _cosine_distance(
            np.mean(np.array(baseline_embeddings, dtype=np.float64), axis=0).tolist(),
            np.mean(np.array(snapshot_embeddings, dtype=np.float64), axis=0).tolist(),
        )

    overall_baseline = _mean_embedding(baseline["probes"])
    overall_snapshot = _mean_embedding(snapshot["probes"])
    overall_drift = _cosine_distance(overall_baseline, overall_snapshot)

    drifted_probes = [entry for entry in per_probe if entry["distance"] > drift_threshold]
    coverage_drops = [entry for entry in keyword_issues if entry["coverage_drop"] > keyword_drop_threshold]
    probe_score = len(drifted_probes) / max(len(per_probe), 1)
    keyword_score = sum(entry["coverage_drop"] for entry in keyword_issues) / max(len(keyword_issues), 1)

    drift_score = float(min(1.0, 0.1 * overall_drift + 0.6 * probe_score + 0.35 * keyword_score))
    if drift_score < 0.2:
        verdict = "stable"
    elif drift_score < 0.25:
        verdict = "mild_drift"
    else:
        verdict = "significant_drift"

    top_drifted = sorted(per_probe, key=lambda entry: entry["distance"], reverse=True)[:3]

    return {
        "baseline_path": baseline.get("snapshot_type", "baseline"),
        "snapshot_path": snapshot.get("snapshot_type", "snapshot"),
        "overall_drift": overall_drift,
        "category_drifts": category_drifts,
        "probe_count": len(per_probe),
        "drifted_probes": drifted_probes,
        "coverage_drops": coverage_drops,
        "top_drifted": top_drifted,
        "drift_score": drift_score,
        "verdict": verdict,
        "thresholds": {
            "per_probe": drift_threshold,
            "keyword_drop": keyword_drop_threshold,
        },
    }


def evaluate_snapshot(baseline_path: Path, snapshot_path: Path) -> Dict[str, Any]:
    baseline = load_json(baseline_path)
    snapshot = load_json(snapshot_path)
    return compare_snapshots(baseline, snapshot)
