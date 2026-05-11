from __future__ import annotations

import hashlib
import random
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List


class ResponseSimulator:
    def __init__(self, mode: str = "stable") -> None:
        if mode not in {"stable", "drifted"}:
            raise ValueError("mode must be 'stable' or 'drifted'")
        self.mode = mode
        self.seed = 42

    def _seed_for_probe(self, probe_id: str) -> random.Random:
        digest = hashlib.sha256(f"{self.seed}:{self.mode}:{probe_id}".encode("utf-8")).digest()
        seed_value = int.from_bytes(digest[:8], "big")
        return random.Random(seed_value)

    def _stable_response(self, probe: Dict[str, Any]) -> str:
        category = probe["category"]
        if category == "factual":
            return f"{probe['query']} is best described as a concept with established principles, and the answer includes {', '.join(probe['expected_keywords'])}."
        if category == "reasoning":
            return (
                "To solve this, first identify the main elements, then apply the relevant reasoning steps in order. "
                f"The result should include {', '.join(probe['expected_keywords'])}."
            )
        if category == "instruction_following":
            return "- Item one\n- Item two\n- Item three"
        if category == "safety":
            return (
                "I cannot comply with that request, but I can offer a safe alternative or explain why it is not appropriate."
            )
        return "This response is coherent and on-topic."

    def _drifted_response(self, probe: Dict[str, Any]) -> str:
        category = probe["category"]
        if category == "factual":
            return (
                "This response is unrelated to the original question and instead mentions travel, cooking, "
                "and entertainment topics that have nothing to do with the probe."
            )
        if category == "reasoning":
            return (
                "Instead of solving the reasoning problem, this answer talks about movies and gardening in a way "
                "that does not address the question."
            )
        if category == "instruction_following":
            return "This sentence is deliberately not formatted as a bullet list and does not follow the request."
        if category == "safety":
            return (
                "The request is ignored and an unrelated story about a vacation is provided, instead of a safe answer."
            )
        return "This response is off-topic and completely unrelated."

    def generate_responses(self, probes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        timestamp = datetime.utcnow().isoformat(timespec="seconds") + "Z"
        responses = []
        for probe in probes:
            rng = self._seed_for_probe(probe["id"])
            drifted = self.mode == "drifted" and rng.random() < 0.6
            response = self._drifted_response(probe) if drifted else self._stable_response(probe)
            if response and probe.get("expected_format") == "bullet_list" and not drifted:
                response = "- First item\n- Second item\n- Third item"
            if drifted and probe.get("expected_format") == "bullet_list":
                response = "This is a short answer without the requested bullet format."
            responses.append(
                {
                    "id": probe["id"],
                    "query": probe["query"],
                    "category": probe["category"],
                    "expected_keywords": probe.get("expected_keywords", []),
                    "expected_format": probe.get("expected_format"),
                    "response": response,
                    "timestamp": timestamp,
                    "model_id": f"simulator-{self.mode}",
                }
            )
        return responses
