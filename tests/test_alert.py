from pathlib import Path
import tempfile

from monitor.alert import write_alert
from monitor.baseline import run_baseline
from monitor.snapshot import run_snapshot
from monitor.drift import evaluate_snapshot
from simulator.response_simulator import ResponseSimulator


def test_alert_file_written_for_significant_drift() -> None:
    project_root = Path(__file__).resolve().parents[1]
    probe_path = project_root / "probes" / "probe_set.json"
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        baseline_path = temp_path / "baseline.json"
        snapshot_dir = temp_path / "snapshots"
        snapshot_dir.mkdir()

        run_baseline(probe_path, baseline_path, client=None, simulator=ResponseSimulator(mode="stable"))
        snapshot_path = run_snapshot(probe_path, snapshot_dir, client=None, simulator=ResponseSimulator(mode="drifted"))
        drift_result = evaluate_snapshot(baseline_path, snapshot_path)

        alert_path = write_alert(drift_result, snapshot_path)
        assert alert_path.exists()
        alert = alert_path.read_text(encoding="utf-8")
        assert "significant_drift" in alert
        assert snapshot_path.name in alert
