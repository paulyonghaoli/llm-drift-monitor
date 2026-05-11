from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover
    load_dotenv = None

try:
    import openai
except ImportError:  # pragma: no cover
    openai = None

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if load_dotenv is not None:
    load_dotenv(PROJECT_ROOT / ".env")


class OpenAIClient:
    def __init__(self, api_key: str, model: str = "gpt-3.5-turbo") -> None:
        if openai is None:
            raise RuntimeError("The openai package is required for real LLM mode.")
        self.model = model
        openai.api_key = api_key

    def run_probe(self, probe: Dict[str, Any]) -> Dict[str, Any]:
        prompt = probe["query"]
        if probe.get("expected_format") == "bullet_list":
            prompt += "\nRespond with a bullet list."

        response = openai.ChatCompletion.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a helpful question-answering assistant."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.0,
            max_tokens=250,
        )
        text = response.choices[0].message.content.strip()
        return {
            "id": probe["id"],
            "query": probe["query"],
            "category": probe["category"],
            "expected_keywords": probe.get("expected_keywords", []),
            "expected_format": probe.get("expected_format"),
            "response": text,
            "timestamp": response.created if hasattr(response, "created") else "",
            "model_id": self.model,
        }

    def run_probes(self, probes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return [self.run_probe(probe) for probe in probes]


def openai_client_from_env() -> Optional[OpenAIClient]:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    return OpenAIClient(api_key=api_key)
