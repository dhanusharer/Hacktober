"""Observation Evaluator for CodeWalk.

Evaluates user real-world observations against the target CS concept using
local Gemma, with deterministic fallback for reliability.
"""

from __future__ import annotations

import logging
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field

from engine.gemma import generate_structured_response
from engine.missions import Concept, Mission

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent
EVALUATOR_PROMPT_PATH = BASE_DIR / "prompts" / "evaluator.txt"


class Verdict(str, Enum):
    """Evaluation verdict categories."""
    STRONG_MATCH = "STRONG_MATCH"
    PARTIAL_MATCH = "PARTIAL_MATCH"
    NOT_A_MATCH = "NOT_A_MATCH"


class EvaluationResult(BaseModel):
    """Structured evaluation returned to the user."""
    concept: str
    verdict: Verdict
    confidence: float = Field(ge=0.0, le=1.0)
    explanation: str
    real_world_mapping: Dict[str, str] = Field(default_factory=dict)
    learning_point: str
    next_mission: str
    is_fallback: bool = False


# Keyword indicators for heuristic fallback evaluation
CONCEPT_KEYWORDS: Dict[str, Dict[str, list[str]]] = {
    "queue": {
        "core": ["line", "queue", "fifo", "first-in", "first in", "first come", "first-come", "first-served", "wait", "counter", "turn", "head", "tail", "behind", "back", "front", "enqueue", "dequeue"],
        "antonyms": ["stack", "lifo", "undo", "last in", "bottom"],
    },
    "stack": {
        "core": ["stack", "pile", "lifo", "last-in", "last in", "top", "tray", "plate", "pushed", "popped"],
        "antonyms": ["fifo", "queue", "line"],
    },
    "linear_search": {
        "core": ["one by one", "sequential", "search", "scan", "item by item", "unsorted", "in order", "checked every"],
        "antonyms": ["half", "binary", "divide", "sorted", "middle"],
    },
    "binary_search": {
        "core": ["half", "middle", "sorted", "binary", "divide", "split", "logarithmic", "too high", "too low"],
        "antonyms": ["one by one", "sequential", "linear"],
    },
    "bottleneck": {
        "core": ["bottleneck", "narrow", "slow", "choke", "funnel", "congestion", "throughput", "backlog", "delay", "jam"],
        "antonyms": ["smooth", "unlimited", "fast"],
    },
    "scheduling": {
        "core": ["schedule", "round-robin", "priority", "cycle", "timer", "crosswalk", "dispatch", "turn", "allocated", "signal"],
        "antonyms": [],
    },
    "classification": {
        "core": ["classify", "sort", "category", "classes", "bin", "recycle", "compost", "landfill", "type", "feature", "label"],
        "antonyms": [],
    },
    "anomaly_detection": {
        "core": ["anomaly", "outlier", "unusual", "unexpected", "rare", "different", "abnormal", "strange", "deviant"],
        "antonyms": ["normal", "identical", "uniform"],
    },
    "sampling": {
        "core": ["sample", "subset", "count", "estimate", "percentage", "every 3rd", "every 5th", "population", "bias", "representative"],
        "antonyms": ["all", "entire", "census"],
    },
    "duplicate_data": {
        "core": ["duplicate", "copy", "identical", "redundant", "same", "repeated", "clones", "deduplicate"],
        "antonyms": ["unique", "distinct"],
    },
}


def fallback_evaluate(
    concept: Concept,
    mission: Mission,
    user_observation: str,
) -> EvaluationResult:
    """Deterministic fallback evaluator used when Gemma is unavailable."""
    clean_obs = user_observation.strip().lower()

    if len(clean_obs) < 15:
        return EvaluationResult(
            concept=concept.name,
            verdict=Verdict.NOT_A_MATCH,
            confidence=0.9,
            explanation=(
                f"Your observation was too brief to demonstrate the mechanics of {concept.name}. "
                "Take a few minutes to describe what physical actors, steps, or patterns you witnessed."
            ),
            real_world_mapping={"Input notes": "Insufficient detail"},
            learning_point=(
                f"In computer science, validating algorithms requires observable, verifiable inputs and outputs."
            ),
            next_mission=f"Revisit a spot where {concept.name.lower()} is happening and note at least two distinct actions.",
            is_fallback=True,
        )

    import re
    keywords = CONCEPT_KEYWORDS.get(concept.id, {"core": [concept.name.lower()], "antonyms": []})
    
    def matches_keyword(word: str, text: str) -> bool:
        return bool(re.search(r"\b" + re.escape(word) + r"\b", text, flags=re.IGNORECASE))

    core_hits = sum(1 for kw in keywords["core"] if matches_keyword(kw, clean_obs))
    antonym_hits = sum(1 for kw in keywords.get("antonyms", []) if matches_keyword(kw, clean_obs))

    if antonym_hits > 0 and core_hits == 0:
        return EvaluationResult(
            concept=concept.name,
            verdict=Verdict.NOT_A_MATCH,
            confidence=0.85,
            explanation=(
                f"Your observation describes characteristics opposite to {concept.name}. "
                f"For example, you observed behaviors typical of opposing or contrasting structures."
            ),
            real_world_mapping={"Observed pattern": "Contrasting structure"},
            learning_point=concept.short_explanation,
            next_mission=f"Try observing a clear, unambiguous example such as {concept.safe_observation_contexts[0] if concept.safe_observation_contexts else 'a public queue'}.",
            is_fallback=True,
        )

    if core_hits >= 2:
        return EvaluationResult(
            concept=concept.name,
            verdict=Verdict.STRONG_MATCH,
            confidence=0.85,
            explanation=(
                f"Great observation! You noted core elements directly illustrating {concept.name}, "
                f"such as order and process flow."
            ),
            real_world_mapping={
                "Observed actors": f"Items undergoing {concept.name.lower()} processing",
                "Observed environment": f"Operating environment for {concept.category}",
            },
            learning_point=(
                f"{concept.name} is foundational in {concept.category}: {concept.short_explanation}"
            ),
            next_mission=f"Next, explore how {concept.name} behaves under peak overload conditions.",
            is_fallback=True,
        )
    elif core_hits == 1:
        return EvaluationResult(
            concept=concept.name,
            verdict=Verdict.PARTIAL_MATCH,
            confidence=0.7,
            explanation=(
                f"Your observation touched on some aspects of {concept.name}, but did not fully describe "
                f"how elements are processed or ordered from start to finish."
            ),
            real_world_mapping={"Observed element": f"Related to {concept.name.lower()}"},
            learning_point=concept.short_explanation,
            next_mission=f"Observe the exact transition moment when an element enters or leaves the system.",
            is_fallback=True,
        )
    else:
        return EvaluationResult(
            concept=concept.name,
            verdict=Verdict.NOT_A_MATCH,
            confidence=0.75,
            explanation=(
                f"Your notes do not clearly describe the behavior of {concept.name}. "
                f"Remember that {concept.name} specifically deals with: {concept.short_explanation}"
            ),
            real_world_mapping={"Observed description": "General observation"},
            learning_point=concept.short_explanation,
            next_mission=f"Find a designated example of {concept.name.lower()} such as: {concept.safe_observation_contexts[0] if concept.safe_observation_contexts else 'a public setting'}.",
            is_fallback=True,
        )


def evaluate_observation(
    concept: Concept,
    mission: Mission,
    user_observation: str,
    use_fallback_on_error: bool = True,
    model: Optional[str] = None,
    host: Optional[str] = None,
) -> EvaluationResult:
    """Evaluate a user observation using local Gemma with deterministic fallback."""
    obs_clean = user_observation.strip()

    # Pre-validation: reject completely empty or trivial spam observations
    if len(obs_clean) < 10:
        return EvaluationResult(
            concept=concept.name,
            verdict=Verdict.NOT_A_MATCH,
            confidence=0.95,
            explanation=(
                f"Your observation is too short to evaluate. Please provide a descriptive account "
                f"of what you physically saw and how it behaved."
            ),
            real_world_mapping={"Input": "Too brief or empty"},
            learning_point=f"Validating real-world behavior requires describing actual inputs and outputs.",
            next_mission=f"Observe {concept.name.lower()} in a public setting and write down at least 2 full sentences.",
            is_fallback=True,
        )

    if not EVALUATOR_PROMPT_PATH.exists():
        if use_fallback_on_error:
            logger.warning("Evaluator prompt template missing, using fallback.")
            return fallback_evaluate(concept, mission, user_observation)
        raise FileNotFoundError(f"Evaluator prompt missing at: {EVALUATOR_PROMPT_PATH}")

    with open(EVALUATOR_PROMPT_PATH, "r", encoding="utf-8") as f:
        template = f.read()

    prompt = template.format(
        concept_name=concept.name,
        category=concept.category,
        concept_explanation=concept.short_explanation,
        mission_title=mission.title,
        mission_text=mission.mission,
        user_observation=user_observation.strip(),
    )

    try:
        result = generate_structured_response(
            prompt=prompt,
            response_model=EvaluationResult,
            model=model,
            host=host,
            temperature=0.3,
        )
        result.concept = concept.name
        result.is_fallback = False
        return result
    except Exception as exc:
        logger.warning("Gemma evaluation failed (%s). Using fallback evaluator.", exc)
        if use_fallback_on_error:
            return fallback_evaluate(concept, mission, user_observation)
        raise
