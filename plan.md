LLM Behavior Observability Lab

A serious monitoring/evaluation system for detecting:

semantic drift
instruction-following drift
safety drift
format drift
retrieval-grounding drift
latency/cost drift
tool-use drift
confidence/calibration drift
model-version regression

The current repo already has a good foundation: fixed probes, baseline snapshots, later snapshots, embedding-based drift detection, keyword coverage checks, alerts, and reports. It currently compares centroid drift, per-probe drift, and keyword coverage drop, then assigns stable, mild_drift, or significant_drift.

One important issue: requirements.txt pins openai==1.9.0, but openai_client.py uses the older openai.ChatCompletion.create style, which is not the preferred v1 client pattern.

Updated plan
Phase 1 — Monitoring foundation

Add typed schemas, config file, run metadata, probe validation, richer snapshot format, and CLI flags.

Phase 2 — Stronger drift signals

Add:

semantic embedding drift
format compliance drift
keyword / concept coverage drift
length/style drift
refusal-rate drift
latency/cost drift
deterministic simulation scenarios
Phase 3 — Statistical drift detection

Add:

bootstrap confidence intervals
control-chart style thresholds
rolling baseline
category-level anomaly detection
alert severity scoring
Phase 4 — LLM-as-judge and verifier

Add optional judge checks:

answer correctness
rubric adherence
safety policy behavior
hallucination / unsupported claims
format validity
Phase 5 — Production-style observability

Add:

HTML/Markdown dashboard
alert routing adapters
scheduled runs
Prometheus/OpenTelemetry-style export
GitHub Actions regression workflow
Phase 6 — Connect to your other repos

This repo can become the monitoring layer for:

open-ended-task-agent
rag-eval-harness
hybrid-retrieval-benchmark

That gives you an integrated “LLM systems observability” portfolio.

Claude Code prompt
You are working in my repo:
paulyonghaoli/llm-drift-monitor

Long-term goal:
Transform this repo from a lightweight semantic drift demo into “LLM Behavior Observability Lab” — a serious, reproducible monitoring framework for detecting LLM behavior drift, regression, safety drift, format drift, latency/cost drift, and model-version changes.

Do NOT rewrite everything at once.
Build a stable foundation first while preserving the current CLI workflow:

python main.py baseline
python main.py snapshot
python main.py report
python main.py simulate --stable
python main.py simulate --drift

Current functionality:
- probes/probe_set.json defines fixed probes
- baseline creates snapshots/baseline.json
- snapshot creates timestamped snapshots
- drift compares baseline vs snapshot
- alert writes alert JSON for significant drift
- report generates reports/drift_report.md
- simulator supports stable/drifted responses
- optional OpenAI mode if OPENAI_API_KEY is set

==================================================
PHASE 1 TARGET — OBSERVABILITY FOUNDATION
==================================================

Main objectives:
1. Add typed schemas and validation
2. Add richer snapshot metadata
3. Add stronger drift signals
4. Fix OpenAI client compatibility
5. Add config-driven thresholds
6. Add statistical summaries
7. Add tests and CI
8. Keep offline simulation mode reliable

==================================================
PART 1 — PROJECT STRUCTURE
==================================================

Review current structure and preserve readability.

Suggested structure:

monitor/
  baseline.py
  snapshot.py
  drift.py
  alert.py
  report.py
  schemas.py
  metrics.py
  validators.py
  config.py
  stats.py

llm/
  openai_client.py
  base.py

simulator/
  response_simulator.py
  scenarios.py

scripts/
  run_monitor.py
  compare_snapshots.py

tests/

Do not force this structure if the existing one can be improved incrementally.

==================================================
PART 2 — CONFIG FILE
==================================================

Add config.yaml.

Example:

probe_set_path: probes/probe_set.json
snapshot_dir: snapshots
alert_dir: alerts
report_dir: reports

embedding:
  model_name: all-MiniLM-L6-v2

llm:
  provider: openai
  model: gpt-4o-mini
  api_key_env: OPENAI_API_KEY
  temperature: 0.0
  max_tokens: 250

thresholds:
  per_probe_semantic_drift: 0.25
  centroid_drift: 0.15
  keyword_drop: 0.2
  format_failure_rate: 0.1
  latency_increase_ratio: 1.5
  significant_drift_score: 0.25
  mild_drift_score: 0.2

alerts:
  write_json: true
  severity_levels: [info, warning, critical]

Update CLI:
python main.py baseline --config config.yaml
python main.py snapshot --config config.yaml
python main.py report --config config.yaml
python main.py simulate --stable --config config.yaml

Default config should preserve current behavior.

==================================================
PART 3 — TYPED SCHEMAS
==================================================

Create monitor/schemas.py.

Define dataclasses or Pydantic models:

Probe:
- id: str
- query: str
- category: str
- expected_keywords: list[str]
- expected_format: optional str
- rubric: optional str
- metadata: dict optional

ProbeResponse:
- id
- query
- category
- expected_keywords
- expected_format
- response
- timestamp
- model_id
- latency_ms optional
- token_usage optional
- cost_usd optional
- error optional
- embedding optional

Snapshot:
- snapshot_type: baseline | snapshot
- timestamp
- model_id
- config_hash
- probe_count
- probes: list[ProbeResponse]
- run_metadata

DriftResult:
- overall_drift
- category_drifts
- per_probe_results
- drift_score
- verdict
- severity
- thresholds

Validation rules:
- probe IDs unique
- query non-empty
- category non-empty
- expected_keywords is list
- baseline and snapshot must have matching probe IDs
- missing probes should be reported clearly, not crash with KeyError

Add tests for malformed probe sets and mismatched snapshots.

==================================================
PART 4 — FIX OPENAI CLIENT
==================================================

Update llm/openai_client.py.

Current code uses older ChatCompletion-style usage.
Use modern OpenAI v1 client style:

from openai import OpenAI
client = OpenAI(api_key=api_key)
client.chat.completions.create(...)

Requirements currently pin openai==1.9.0.
Make code compatible with openai>=1.0.

Add:
- configurable model
- api_key_env support
- latency measurement
- token usage capture when available
- graceful error capture per probe

Do not fail the whole run if one probe fails.
Return a ProbeResponse with error field.

==================================================
PART 5 — OPTIONAL DEPENDENCIES CLEANUP
==================================================

Currently requirements include OpenAI as mandatory.

Consider adding pyproject.toml with optional extras:

core:
- numpy
- python-dateutil
- sentence-transformers

llm:
- openai
- python-dotenv

dev:
- pytest
- ruff

If this is too much, keep requirements.txt but document optional OpenAI mode clearly.

Offline simulator mode must work without an OpenAI key.

==================================================
PART 6 — EMBEDDING MODEL CACHE
==================================================

Current embed_texts builds SentenceTransformer every time.
Refactor to cache/load embedding model once per process.

Create monitor/embeddings.py:
- EmbeddingModel
- embed_texts(texts)
- configurable model_name

Avoid repeated model loading between baseline/snapshot/report where possible.

Add tests using monkeypatch/mock if needed.

==================================================
PART 7 — STRONGER DRIFT SIGNALS
==================================================

Create monitor/metrics.py.

Implement drift metrics:

1. semantic_distance
- cosine distance between baseline and snapshot response embeddings

2. centroid_distance
- category-level and overall centroid distance

3. keyword_coverage_drop
- existing behavior, but move to reusable function

4. response_length_shift
- ratio or absolute difference in token/word count

5. format_compliance
- expected_format checks:
  - bullet_list
  - json
  - short_answer
  - numbered_list
  - contains_citations if useful

6. refusal_behavior_change
- detect if response changed from answering to refusing or vice versa
- simple heuristic is fine

7. error_rate
- percentage of probe responses with error field

8. latency_shift
- compare latency_ms if available

Update drift scoring to combine these signals with configurable weights.

Do not overfit weights.
Make weights transparent in config.

==================================================
PART 8 — CATEGORY-LEVEL ANALYSIS
==================================================

Improve category analysis.

For each category, compute:
- mean semantic drift
- max semantic drift
- keyword drop
- format failure rate
- refusal change rate
- count of drifted probes
- severity

This should appear in metrics JSON and report.

==================================================
PART 9 — STATISTICAL DRIFT
==================================================

Create monitor/stats.py.

Add simple bootstrap confidence intervals:
- for mean semantic drift
- for mean keyword drop
- for category means

Add:
- historical trend loader from snapshots/
- rolling mean and std for drift_score
- simple z-score anomaly flag if enough historical snapshots exist

Keep it lightweight and dependency-free.

==================================================
PART 10 — ALERT SEVERITY
==================================================

Improve alert model.

Severity:
- info: stable but measurable change
- warning: mild drift or category-specific issue
- critical: significant drift, high-risk category drift, or format failures

Alert JSON should include:
- severity
- verdict
- drift_score
- top drifted probes
- top keyword drops
- format failures
- category summary
- recommended action

Recommended actions:
- rerun snapshot
- inspect top probes
- compare model version
- check prompt/config changes
- roll back if production gate fails

==================================================
PART 11 — REPORTING
==================================================

Improve reports/drift_report.md.

Include:
- executive summary
- baseline model / snapshot model
- timestamp comparison
- overall drift score and verdict
- category drift table
- top drifted probes
- format failures
- keyword coverage drops
- latency/cost shift if available
- historical trend summary if available
- recommended next actions
- limitations

Keep report portfolio-grade.

==================================================
PART 12 — SIMULATOR SCENARIOS
==================================================

Improve simulator.

Current simulator supports stable/drifted.
Add named scenarios:

stable
semantic_drift
format_drift
keyword_drop
refusal_drift
verbosity_drift
mixed_drift

CLI:
python main.py simulate --scenario semantic_drift
python main.py simulate --scenario format_drift

Keep --stable and --drift as backward-compatible aliases.

Add tests showing each scenario triggers expected metric patterns.

==================================================
PART 13 — PROBE SET IMPROVEMENT
==================================================

Improve probes/probe_set.json if appropriate.

Add categories:
- factual_consistency
- instruction_following
- format_compliance
- safety_boundary
- summarization_style
- retrieval_grounding
- reasoning_consistency

Each probe should include:
- expected_keywords
- expected_format where relevant
- optional rubric
- optional risk_level

Do not make probes too many.
Keep default demo fast.

==================================================
PART 14 — CI / REGRESSION GATES
==================================================

Add GitHub Actions:

.github/workflows/ci.yml

Run:
- install dependencies
- pytest -v
- python main.py simulate --stable
- python main.py simulate --drift
- python main.py report

If sentence-transformers download is flaky in CI:
- add lightweight mock embedding mode for tests
- or mark integration tests separately

Add optional CLI flag:
--fail-on-drift

For CI:
python main.py simulate --drift --fail-on-drift
should exit non-zero when significant drift is detected.

==================================================
PART 15 — INTEGRATION WITH OTHER REPOS
==================================================

Create docs/INTEGRATIONS.md.

Explain how this can monitor:

1. rag-eval-harness
- detect answer behavior drift over fixed RAG eval probes
- compare baseline vs new prompt/retriever/model

2. hybrid-retrieval-benchmark
- monitor retrieval output drift if embedding model or corpus changes

3. open-ended-task-agent
- monitor agent final-answer drift
- monitor tool-use drift
- monitor termination behavior drift

Add future schema:
AgentProbeResponse:
- final_answer
- tool_calls
- termination_reason
- evidence_quality
- trace_hash

==================================================
PART 16 — RESEARCH DOCS
==================================================

Create docs/ROADMAP.md.

Position repo as:

LLM Behavior Observability Lab:
A lightweight framework for monitoring semantic, behavioral, instruction-following, safety, latency, and cost drift in LLM systems.

Roadmap:
v0: fixed probes + semantic drift
v1: typed snapshots + richer drift signals
v2: category-level monitoring + alert severity
v3: statistical trend monitoring
v4: LLM-as-judge regression gates
v5: RAG/agent drift monitoring
v6: dashboard + production observability
v7: paper-ready benchmark for LLM behavior drift

Create docs/REFERENCES.md.

Include annotated references/topics:
- model monitoring / data drift
- concept drift
- embedding drift
- LLM evaluation
- prompt regression testing
- RAG evaluation
- LLM-as-judge
- safety regression testing
- OpenTelemetry / observability
- Evidently AI / WhyLabs style ML monitoring concepts

For each:
- key idea
- what this repo borrows
- future work

==================================================
PART 17 — TESTS
==================================================

Add tests for:
- probe validation
- snapshot validation
- baseline/snapshot probe mismatch
- cosine distance
- keyword coverage
- format compliance
- response length shift
- refusal behavior change
- drift scoring
- alert severity
- simulator scenarios
- report generation
- OpenAI client error handling using mocks

==================================================
PART 18 — README UPDATE
==================================================

Update README but keep it concise.

Add:
- positioning as LLM behavior observability
- quick start
- simulator scenarios
- real LLM mode
- drift signals
- alert severity
- CI regression gate
- integration with RAG/agent systems
- roadmap link

Do not overclaim.
Say this is not a replacement for full production observability yet.

==================================================
ENGINEERING CONSTRAINTS
==================================================

- Preserve existing CLI commands.
- Offline simulator mode must work.
- No secrets.
- Do not require OpenAI for tests.
- Keep code modular.
- Add type hints.
- Avoid heavy dependencies unless optional.
- Avoid overfitting drift thresholds.
- Make outputs reproducible.
- Keep default demo fast.
- Do not claim semantic drift equals correctness drift.
- Be explicit about limitations.

==================================================
FINAL COMMANDS TO RUN
==================================================

After implementation, run:

pytest -v
python main.py simulate --stable
python main.py simulate --drift
python main.py simulate --scenario format_drift
python main.py report

If implemented:
python main.py simulate --drift --fail-on-drift

Then summarize:
- files changed
- new architecture
- drift signals added
- tests added
- sample outputs
- remaining TODOs

Most important positioning: this repo should not just detect “embedding distance changed.” It should answer:

Did the model’s behavior change?
Which behavior changed?
Is it semantic, format, refusal, safety, latency, or cost drift?
Which probes are responsible?
Should this block deployment?