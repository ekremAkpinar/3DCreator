from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .config import ROOT

TAXONOMY_PATH = ROOT / "knowledge" / "model_families.json"


def load_taxonomy() -> dict[str, Any]:
    with TAXONOMY_PATH.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict) or not isinstance(payload.get("families"), dict):
        raise RuntimeError(f"Ungueltige Modell-Taxonomie: {TAXONOMY_PATH}")
    return payload


def classify_model(name: str, prompt: str) -> dict[str, Any]:
    taxonomy = load_taxonomy()
    text = f"{name} {prompt}".lower()
    normalized = re.sub(r"\s+", " ", text)

    scores: list[tuple[str, int, list[str]]] = []
    for family_id, family in taxonomy["families"].items():
        matched: list[str] = []
        for keyword in family.get("keywords", []):
            keyword_norm = str(keyword).lower().strip()
            if keyword_norm and keyword_norm in normalized:
                matched.append(keyword_norm)
        score = sum(max(1, len(k.split())) for k in matched)
        scores.append((family_id, score, matched))

    scores.sort(key=lambda item: item[1], reverse=True)
    best_family, best_score, matched = scores[0] if scores else ("decoration", 0, [])

    if best_score == 0:
        best_family = "decoration"
        confidence = 0.25
    else:
        second_score = scores[1][1] if len(scores) > 1 else 0
        margin = max(0, best_score - second_score)
        confidence = min(0.98, 0.55 + best_score * 0.08 + margin * 0.04)

    family = taxonomy["families"].get(best_family, {})
    return {
        "family": best_family,
        "label": family.get("label_de", best_family),
        "confidence": round(confidence, 3),
        "matched_keywords": matched,
        "preferred_pipeline": family.get("preferred_pipeline", "hybrid"),
        "priorities": family.get("priorities", []),
        "taxonomy_version": taxonomy.get("schema_version", 1),
    }
