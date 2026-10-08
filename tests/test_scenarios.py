"""End-to-end scenario verification tests for CodeWalk (Scenarios A, B, C, D)."""

import pytest
from engine.missions import get_concept_by_id, generate_mission, get_fallback_mission
from engine.evaluator import evaluate_observation, Verdict


def test_scenario_a_queue_correct_observation():
    """TEST A: Queue + correct FIFO observation -> STRONG_MATCH."""
    concept = get_concept_by_id("queue")
    assert concept is not None

    mission = generate_mission(concept, duration=5, use_fallback_on_error=True)
    assert mission is not None

    observation = (
        "I observed the order line at the local bakery. Customers arrived and queued at the end "
        "of the line (enqueue). The cashier served them one by one in exact order of arrival (dequeue / FIFO). "
        "When an order took longer, the queue backed up, demonstrating the service counter was the bottleneck."
    )

    eval_result = evaluate_observation(concept, mission, observation, use_fallback_on_error=True)
    assert eval_result is not None
    assert eval_result.verdict == Verdict.STRONG_MATCH
    assert eval_result.confidence >= 0.7
    assert len(eval_result.real_world_mapping) > 0
    assert len(eval_result.learning_point) > 0
    assert len(eval_result.next_mission) > 0


def test_scenario_b_queue_weak_observation():
    """TEST B: Queue + weak/vague observation -> PARTIAL_MATCH or NOT_A_MATCH with constructive critique."""
    concept = get_concept_by_id("queue")
    assert concept is not None

    mission = get_fallback_mission(concept, 5)

    observation = "I saw some people standing around near a shop counter waiting."

    eval_result = evaluate_observation(concept, mission, observation, use_fallback_on_error=True)
    assert eval_result is not None
    # Must not falsely give STRONG_MATCH to a weak observation
    assert eval_result.verdict in (Verdict.PARTIAL_MATCH, Verdict.NOT_A_MATCH)
    assert len(eval_result.explanation) > 0


def test_scenario_c_queue_unrelated_observation():
    """TEST C: Queue + unrelated observation -> NOT_A_MATCH."""
    concept = get_concept_by_id("queue")
    assert concept is not None

    mission = get_fallback_mission(concept, 5)

    observation = (
        "I looked at trees in the park. The wind was blowing the green leaves and two dogs "
        "were playing fetch in the grass."
    )

    eval_result = evaluate_observation(concept, mission, observation, use_fallback_on_error=True)
    assert eval_result is not None
    assert eval_result.verdict == Verdict.NOT_A_MATCH
    assert len(eval_result.explanation) > 0


def test_scenario_d_gemma_temporarily_unavailable():
    """TEST D: Gemma/Ollama temporarily unavailable -> application does not crash and provides valid fallback."""
    concept = get_concept_by_id("queue")
    assert concept is not None

    # Force invalid host to simulate service outage
    fake_host = "http://localhost:59999"

    # Mission generation fallback
    mission = generate_mission(
        concept=concept,
        duration=10,
        use_fallback_on_error=True,
        host=fake_host,
    )
    assert mission is not None
    assert mission.is_fallback is True
    assert mission.estimated_minutes == 10
    assert len(mission.observation_questions) == 3

    # Evaluation fallback
    observation = (
        "People joined the back of the queue and left from the front in first-come first-served order."
    )
    eval_result = evaluate_observation(
        concept=concept,
        mission=mission,
        user_observation=observation,
        use_fallback_on_error=True,
        host=fake_host,
    )
    assert eval_result is not None
    assert eval_result.is_fallback is True
    assert eval_result.verdict == Verdict.STRONG_MATCH
