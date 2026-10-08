"""Tests for CodeWalk concept loading, mission generation, and safety filters."""

import pytest
from engine.missions import (
    Concept,
    Mission,
    load_concepts,
    get_concept_by_id,
    get_concepts_by_category,
    is_mission_safe,
    get_fallback_mission,
    generate_mission,
)


def test_concept_loading():
    """Verify that all 10 core concepts are loaded with valid structure."""
    concepts = load_concepts()
    assert len(concepts) == 10

    categories = {c.category for c in concepts}
    assert categories == {"DSA", "Systems", "AI/ML", "Data"}

    concept_ids = {c.id for c in concepts}
    expected_ids = {
        "queue", "stack", "linear_search", "binary_search",
        "bottleneck", "scheduling",
        "classification", "anomaly_detection",
        "sampling", "duplicate_data"
    }
    assert concept_ids == expected_ids

    for c in concepts:
        assert isinstance(c, Concept)
        assert len(c.name) > 0
        assert len(c.short_explanation) > 10
        assert len(c.safe_observation_contexts) >= 2


def test_get_concept_by_id():
    """Verify concept lookup by ID works correctly."""
    queue = get_concept_by_id("queue")
    assert queue is not None
    assert queue.name == "Queue"
    assert queue.category == "DSA"

    non_existent = get_concept_by_id("quantum_entanglement")
    assert non_existent is None


def test_get_concepts_by_category():
    """Verify filtering concepts by category."""
    dsa_concepts = get_concepts_by_category("DSA")
    assert len(dsa_concepts) == 4
    for c in dsa_concepts:
        assert c.category == "DSA"

    systems_concepts = get_concepts_by_category("Systems")
    assert len(systems_concepts) == 2


def test_fallback_missions_all_concepts():
    """Verify that every concept has a valid, safe fallback mission."""
    concepts = load_concepts()
    for c in concepts:
        mission = get_fallback_mission(c, duration=10)
        assert isinstance(mission, Mission)
        assert mission.concept == c.name
        assert mission.estimated_minutes == 10
        assert len(mission.title) > 0
        assert len(mission.mission) > 20
        assert len(mission.observation_questions) == 3
        assert mission.is_fallback is True

        # Fallback missions MUST pass the deterministic safety check
        is_safe, reason = is_mission_safe(mission)
        assert is_safe, f"Fallback for {c.id} triggered safety violation: {reason}"


def test_unsafe_mission_detection():
    """Verify that deterministic safety filter catches dangerous activities."""
    dangerous_cases = [
        # Approaching strangers
        Mission(
            title="Interview Crowds",
            mission="Approach strangers at the bus stop and interview them about their transit habits.",
            observation_questions=["What did they say?", "Did they answer?", "Where do they go?"],
            concept="Queue",
            estimated_minutes=10,
            safety_note="Be polite.",
        ),
        # Climbing hazard
        Mission(
            title="Birdseye View",
            mission="Climb roof of the building or climb a pole to observe the intersection.",
            observation_questions=["Can you see cars?", "Is it high?", "What is moving?"],
            concept="Bottleneck",
            estimated_minutes=5,
            safety_note="Watch your step.",
        ),
        # Electrical hazard
        Mission(
            title="Inspect Circuits",
            mission="Touch electrical wires or open the high voltage fuse box to trace signals.",
            observation_questions=["Is it humming?", "What color are the wires?", "Is it warm?"],
            concept="Systems",
            estimated_minutes=10,
            safety_note="Wear gloves.",
        ),
        # Trespassing
        Mission(
            title="Restricted Access",
            mission="Trespass onto private property and enter employee only areas to inspect logistics.",
            observation_questions=["What is back there?", "Where are packages?", "Are doors locked?"],
            concept="Stack",
            estimated_minutes=15,
            safety_note="Quickly sneak in.",
        ),
    ]

    for dm in dangerous_cases:
        is_safe, reason = is_mission_safe(dm)
        assert not is_safe, f"Failed to catch unsafe mission: {dm.title}"
        assert reason is not None


def test_mission_fallback_on_unreachable_ollama():
    """Verify that generate_mission gracefully falls back when Ollama is unreachable."""
    queue = get_concept_by_id("queue")
    assert queue is not None

    # Point to an unreachable port
    mission = generate_mission(
        concept=queue,
        duration=10,
        use_fallback_on_error=True,
        host="http://localhost:59999",
    )

    assert isinstance(mission, Mission)
    assert mission.concept == "Queue"
    assert mission.is_fallback is True
    assert len(mission.observation_questions) >= 3
