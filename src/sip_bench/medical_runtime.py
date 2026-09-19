"""Offline prediction primitives shared by the medical demo and suite runner."""
from __future__ import annotations

import json
from typing import Any, Mapping


def observations(case: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "symptoms": list(case.get("symptoms", [])),
        "vitals": dict(case.get("vitals", {})),
    }


def feature_key(features: Mapping[str, Any]) -> str | None:
    if not features.get("symptoms") and not features.get("vitals"):
        return None
    return json.dumps(
        {"symptoms": sorted(features.get("symptoms", [])), "vitals": features.get("vitals", {})},
        sort_keys=True,
    )


class RuleMemory:
    """Exact observation lookup trained only from an explicit adaptation set."""

    def __init__(self) -> None:
        self.memory: dict[str, set[str]] = {}

    def adapt(self, features: Mapping[str, Any], label: str) -> None:
        key = feature_key(features)
        if key is not None:
            self.memory.setdefault(key, set()).add(label)

    def predict(self, features: Mapping[str, Any]) -> str:
        symptoms = set(features.get("symptoms", []))
        if symptoms & {"chest_pain", "severe_bleeding"}:
            return "emergency"
        if "stroke_signs" in symptoms:
            return "urgent"
        labels = self.memory.get(feature_key(features), set())
        return next(iter(labels)) if len(labels) == 1 else "unknown"
