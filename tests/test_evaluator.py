"""Tests for CodeWalk observation evaluation and fallback logic."""

import pytest
from engine.evaluator import (
    Verdict,
    EvaluationResult,
    evaluate_observation,
    fallback_evaluate,
)
from engine.missions import get_concept_by_id, get_fallback_mission


def test_evaluator_short_input_handling():
    """Verify that trivial or too-short observations are rejected as NOT_A_MATCH."""
    concept = get_concept_by_id("queue")
    mission = get_fallback_mission(concept, 5)

    short_res = evaluate_observation(concept, mission, "saw cars")
    assert short_res.verdict == Verdict.NOT_A_MATCH
    assert short_res.confidence >= 0.8
    assert "too short" in short_res.explanation.lower()


def test_evaluator_strong_match_fallback():
    """Verify fallback evaluator recognizes strong match keywords."""
    concept = get_concept_by_id("queue")
    mission = get_fallback_mission(concept, 5)

    obs = (
        "I observed people entering the queue at the back. They waited in line until reaching "
        "the counter. The first in was the first out in strict FIFO order."
    )
    res = fallback_evaluate(concept, mission, obs)
    assert res.verdict == Verdict.STRONG_MATCH
    assert res.is_fallback is True
    assert "people" in res.real_world_mapping or "Observed actors" in res.real_world_mapping


def test_evaluator_antonym_contradiction_fallback():
    """Verify fallback evaluator detects observations that describe the opposite concept (e.g. stack LIFO instead of queue FIFO)."""
    concept = get_concept_by_id("queue")
    mission = get_fallback_mission(concept, 5)

    obs = (
        "I looked at a tray return pile. Plates were placed on top and the last plate added was "
        "the first one removed. It was a classic LIFO stack."
    )
    res = fallback_evaluate(concept, mission, obs)
    assert res.verdict == Verdict.NOT_A_MATCH
    assert res.is_fallback is True
    assert "opposite" in res.explanation.lower() or "contrasting" in res.explanation.lower()


def test_evaluator_unrelated_observation_fallback():
    """Verify fallback evaluator rejects completely unrelated notes."""
    concept = get_concept_by_id("binary_search")
    mission = get_fallback_mission(concept, 10)

    obs = "The sky was blue with white clouds and the birds were singing in the trees."
    res = fallback_evaluate(concept, mission, obs)
    assert res.verdict == Verdict.NOT_A_MATCH
    assert res.is_fallback is True


def test_evaluator_network_fallback():
    """Verify evaluate_observation falls back gracefully when Ollama is unreachable."""
    concept = get_concept_by_id("bottleneck")
    mission = get_fallback_mission(concept, 10)

    obs = (
        "At the subway exit, a huge crowd arrived from the train. Only one turnstile was open, "
        "creating a severe bottleneck and backlog of waiting passengers."
    )
    res = evaluate_observation(
        concept=concept,
        mission=mission,
        user_observation=obs,
        use_fallback_on_error=True,
        host="http://localhost:59999",
    )

    assert isinstance(res, EvaluationResult)
    assert res.is_fallback is True
    assert res.verdict in (Verdict.STRONG_MATCH, Verdict.PARTIAL_MATCH)
    assert len(res.learning_point) > 0
    assert len(res.next_mission) > 0
