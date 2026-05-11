from pathlib import Path
import tempfile

from monitor.drift import evaluate_snapshot
from monitor.baseline import run_baseline
from monitor.snapshot import run_snapshot
from simulator.response_simulator import ResponseSimulator


def test_simulated_stable_snapshot_is_stable() -> None:
    project_root = Path(__file__).resolve().parents[1]
    probe_path = project_root / "probes" / "probe_set.json"
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        baseline_path = temp_path / "baseline.json"
        snapshot_dir = temp_path / "snapshots"
        snapshot_dir.mkdir()

        run_baseline(probe_path, baseline_path, client=None, simulator=ResponseSimulator(mode="stable"))
        snapshot_path = run_snapshot(probe_path, snapshot_dir, client=None, simulator=ResponseSimulator(mode="stable"))
        result = evaluate_snapshot(baseline_path, snapshot_path)

        assert result["verdict"] == "stable"
        assert result["drift_score"] < 0.2


def test_simulated_drifted_snapshot_is_significant() -> None:
    project_root = Path(__file__).resolve().parents[1]
    probe_path = project_root / "probes" / "probe_set.json"
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        baseline_path = temp_path / "baseline.json"
        snapshot_dir = temp_path / "snapshots"
        snapshot_dir.mkdir()

        run_baseline(probe_path, baseline_path, client=None, simulator=ResponseSimulator(mode="stable"))
        snapshot_path = run_snapshot(probe_path, snapshot_dir, client=None, simulator=ResponseSimulator(mode="drifted"))
        result = evaluate_snapshot(baseline_path, snapshot_path)

        assert result["verdict"] == "significant_drift"
        assert result["drift_score"] >= 0.4
