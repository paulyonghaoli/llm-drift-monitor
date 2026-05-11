from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from monitor.utils import embed_texts, load_probe_set, save_json
from simulator.response_simulator import ResponseSimulator
from llm.openai_client import OpenAIClient


def _collect_responses(probes: List[Dict[str, Any]], client: Optional[OpenAIClient], simulator: ResponseSimulator) -> List[Dict[str, Any]]:
    if client is not None:
        return client.run_probes(probes)
    return simulator.generate_responses(probes)


def run_baseline(probe_set_path: Path, baseline_path: Path, client: Optional[OpenAIClient] = None, simulator: Optional[ResponseSimulator] = None) -> Dict[str, Any]:
    if simulator is None:
        raise ValueError("A simulator instance is required when no OpenAI client is provided.")

    probes = load_probe_set(probe_set_path)
    responses = _collect_responses(probes, client, simulator)
    texts = [entry["response"] for entry in responses]
    embeddings = embed_texts(texts)

    snapshot = {
        "snapshot_type": "baseline",
        "timestamp": responses[0].get("timestamp", ""),
        "model_id": responses[0].get("model_id", "simulated"),
        "probes": [
            {**entry, "embedding": embedding}
            for entry, embedding in zip(responses, embeddings)
        ],
    }
    save_json(snapshot, baseline_path)
    return snapshot
