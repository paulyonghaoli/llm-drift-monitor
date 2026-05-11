# llm-drift-monitor

A lightweight Python monitoring system that detects semantic drift in LLM outputs over time.

## Problem statement
Monitoring an LLM in production means verifying that repeated probe queries return consistent behavior. Silent drift can happen after a model version change, prompt injection, or other subtle regression where outputs shift even though the service is still available.

This project simulates that workflow with a fixed probe set, embedding-based drift detection, and alerts when responses diverge from a baseline.

## Architecture

```
probes/probe_set.json -> monitor/baseline.py -> snapshots/baseline.json
                                \-> monitor/snapshot.py -> snapshots/snapshot_<timestamp>.json
monitor/drift.py compares baseline and snapshots
monitor/alert.py writes alerts/alert_<timestamp>.json when drift is significant
monitor/report.py generates reports/drift_report.md
simulator/response_simulator.py provides stable/drifted responses without an API key
llm/openai_client.py optionally wraps OpenAI if OPENAI_API_KEY is set
```

## Requirements

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

## Usage

Run a baseline snapshot:

```bash
python main.py baseline
```

Run a later snapshot and evaluate drift:

```bash
python main.py snapshot
```

Generate a report from baseline and all snapshots:

```bash
python main.py report
```

Run simulation mode without an OpenAI API key:

```bash
python main.py simulate --stable
python main.py simulate --drift
```

## Real LLM mode

If `OPENAI_API_KEY` is defined, `main.py` will use `llm/openai_client.py` to collect responses from OpenAI. Otherwise, it falls back to the deterministic simulator.

Create a `.env` file in the repository root with your key:

```bash
cat > .env <<'EOF'
OPENAI_API_KEY=your_openai_api_key_here
EOF
```

This repo now loads `OPENAI_API_KEY` from `.env` automatically.

## Drift signals

- **Semantic centroid drift**: cosine distance between the mean embeddings of baseline and snapshot responses.
- **Per-probe drift**: distance between each baseline response embedding and its later response embedding.
- **Keyword coverage drop**: whether expected probe keywords are missing or reduced in the new response.

## Verdicts

- `stable`
- `mild_drift`
- `significant_drift`

## Tests

Run tests:

```bash
pytest
```
