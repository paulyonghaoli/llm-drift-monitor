from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from monitor.utils import embed_texts, load_probe_set, save_json
from simulator.response_simulator import ResponseSimulator
from llm.openai_client import OpenAIClient


def _collect_responses(probes: List[Dict[str, Any]], client: Optional[OpenAIClient], simulator: ResponseSimulator) -> List[Dict[str, Any]]:
    if client is not None:
        return client.run_probes(probes)
    return simulator.generate_responses(probes)


def run_snapshot(probe_set_path: Path, snapshot_dir: Path, client: Optional[OpenAIClient] = None, simulator: Optional[ResponseSimulator] = None) -> Path:
    if simulator is None:
        raise ValueError("A simulator instance is required when no OpenAI client is provided.")

    probes = load_probe_set(probe_set_path)
    responses = _collect_responses(probes, client, simulator)
    texts = [entry["response"] for entry in responses]
    embeddings = embed_texts(texts)

    snapshot = {
        "snapshot_type": "snapshot",
        "timestamp": responses[0].get("timestamp", ""),
        "model_id": responses[0].get("model_id", "simulated"),
        "probes": [
            {**entry, "embedding": embedding}
            for entry, embedding in zip(responses, embeddings)
        ],
    }
    snapshot_path = snapshot_dir / f"snapshot_{snapshot['timestamp'].replace(':', '-')}.json"
    save_json(snapshot, snapshot_path)
    return snapshot_path
