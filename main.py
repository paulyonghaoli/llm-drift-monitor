import argparse
import os
from pathlib import Path

from llm.openai_client import openai_client_from_env
from monitor import alert as alert_module
from monitor import baseline as baseline_module
from monitor import drift as drift_module
from monitor import report as report_module
from monitor import snapshot as snapshot_module
from simulator.response_simulator import ResponseSimulator


def ensure_directories():
    for path in ["snapshots", "alerts", "reports"]:
        Path(path).mkdir(parents=True, exist_ok=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="LLM drift monitor CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("baseline", help="Run probes and save the baseline snapshot")
    subparsers.add_parser("snapshot", help="Run probes, save snapshot, and evaluate drift")
    subparsers.add_parser("report", help="Generate a drift report from baseline and snapshots")

    simulate_parser = subparsers.add_parser("simulate", help="Run simulator mode")
    simulate_parser.add_argument("--drift", action="store_true", help="Simulate a drifted snapshot")
    simulate_parser.add_argument("--stable", action="store_true", help="Simulate a stable snapshot")

    args = parser.parse_args()
    ensure_directories()

    probe_path = Path("probes/probe_set.json")
    baseline_path = Path("snapshots/baseline.json")
    snapshot_dir = Path("snapshots")

    if args.command == "baseline":
        client = openai_client_from_env()
        simulator = ResponseSimulator(mode="stable")
        baseline_module.run_baseline(probe_path, baseline_path, client=client, simulator=simulator)
        print(f"Baseline written to {baseline_path}")

    elif args.command == "snapshot":
        client = openai_client_from_env()
        simulator = ResponseSimulator(mode="stable")
        snapshot_path = snapshot_module.run_snapshot(probe_path, snapshot_dir, client=client, simulator=simulator)
        baseline = baseline_path if baseline_path.exists() else None
        if baseline is None:
            raise FileNotFoundError("Baseline snapshot not found. Run `python main.py baseline` first.")
        drift_result = drift_module.evaluate_snapshot(baseline_path, snapshot_path)
        if drift_result["verdict"] == "significant_drift":
            alert_path = alert_module.write_alert(drift_result, snapshot_path)
            alert_module.print_alert(drift_result, alert_path)
        else:
            alert_module.print_alert(drift_result, None)

    elif args.command == "report":
        report_path = report_module.generate_report(baseline_path, snapshot_dir, Path("reports/drift_report.md"))
        print(f"Report generated at {report_path}")

    elif args.command == "simulate":
        mode = "stable" if args.stable else "drifted" if args.drift else None
        if mode is None:
            parser.error("Please specify --stable or --drift")
        baseline_module.run_baseline(probe_path, baseline_path, client=None, simulator=ResponseSimulator(mode="stable"))
        snapshot_path = snapshot_module.run_snapshot(probe_path, snapshot_dir, client=None, simulator=ResponseSimulator(mode=mode))
        drift_result = drift_module.evaluate_snapshot(baseline_path, snapshot_path)
        if drift_result["verdict"] == "significant_drift":
            alert_path = alert_module.write_alert(drift_result, snapshot_path)
            alert_module.print_alert(drift_result, alert_path)
        else:
            alert_module.print_alert(drift_result, None)


if __name__ == "__main__":
    main()
