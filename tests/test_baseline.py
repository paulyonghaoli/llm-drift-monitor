from pathlib import Path
import tempfile

from monitor.baseline import run_baseline
from simulator.response_simulator import ResponseSimulator


def test_baseline_save_and_load_round_trip() -> None:
    project_root = Path(__file__).resolve().parents[1]
    probe_path = project_root / "probes" / "probe_set.json"
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        baseline_path = temp_path / "baseline.json"

        snapshot = run_baseline(probe_path, baseline_path, client=None, simulator=ResponseSimulator(mode="stable"))

        assert baseline_path.exists()
        assert snapshot["snapshot_type"] == "baseline"
        assert len(snapshot["probes"]) == 20
        assert all("embedding" in probe for probe in snapshot["probes"])
