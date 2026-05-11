from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

import numpy as np
from sentence_transformers import SentenceTransformer

MODEL_NAME = "all-MiniLM-L6-v2"


def load_probe_set(path: Path) -> List[Dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def save_json(data: Any, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2, ensure_ascii=False)


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def build_embedding_model() -> SentenceTransformer:
    return SentenceTransformer(MODEL_NAME)


def embed_texts(texts: List[str]) -> List[List[float]]:
    model = build_embedding_model()
    embeddings = model.encode(texts, convert_to_numpy=True)
    return [emb.tolist() for emb in embeddings]


def normalize_vector(vector: List[float]) -> List[float]:
    array = np.array(vector, dtype=np.float64)
    norm = np.linalg.norm(array)
    return array / norm if norm > 0 else array
