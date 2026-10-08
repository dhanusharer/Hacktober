"""Mission generation, validation, and safety engine for CodeWalk."""

from __future__ import annotations

import json
import logging
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field

from engine.gemma import generate_structured_response

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent
CONCEPTS_PATH = BASE_DIR / "data" / "concepts.json"
PROMPT_TEMPLATE_PATH = BASE_DIR / "prompts" / "mission.txt"


class Concept(BaseModel):
    """Represents a curated CS concept."""
    id: str
    name: str
    category: str
    short_explanation: str
    safe_observation_contexts: List[str] = Field(default_factory=list)


class Mission(BaseModel):
    """Structured mission issued to the user."""
    title: str
    mission: str
    observation_questions: List[str]
    concept: str
    estimated_minutes: int
    safety_note: str
    is_fallback: bool = False


# Deterministic Safety Rules
UNSAFE_PATTERNS = [
    # Interacting with / harassing strangers
    r"\b(?:ask|talk to|approach|interview|harass|confront)\s+(?:strangers|passersby|pedestrians|customers|people)\b",
    r"\b(?:photograph|take pictures? of|record|film)\s+(?:faces|strangers|people|passersby)\b",
    # Private property & trespassing
    r"\b(?:trespass|private property|restricted area|staff only|employees? only|break into|hop (?:a )?fence)\b",
    # Physical hazards & climbing
    r"\b(?:climb|jump off|scale)\s+(?:roof|fence|wall|tree|pole|building|ledge|bridge)\b",
    r"\b(?:touch|open|tamper with)\s+(?:electrical|wires?|power line|high voltage|transformer|fuse|panel)\b",
    # Traffic hazards
    r"\b(?:stand in (?:the )?(?:road|traffic|street|highway)|cross (?:a )?highway|jaywalk)\b",
    # Privacy / credential collection
    r"\b(?:steal|collect|record)\s+(?:passwords?|credit card|personal info|pins?|screens)\b",
]

# Curated deterministic fallback missions for all 10 concepts
FALLBACK_MISSIONS: Dict[str, Dict[str, Any]] = {
    "queue": {
        "title": "The First-Come, First-Served Line",
        "mission": "Walk to a nearby coffee shop counter, bus stop, or checkout line. Stand at a respectful distance, put your phone away, and observe the line quietly for {duration} minutes.",
        "observation_questions": [
            "Where do new people enter the line, and where do they exit after service?",
            "Is the order of arrival strictly preserved (FIFO), or does anyone jump ahead?",
            "What happens if the service counter slows down while more people arrive?"
        ],
        "safety_note": "Observe from a natural public vantage point without blocking pathways or approaching strangers."
    },
    "stack": {
        "title": "The Return Tray LIFO Stack",
        "mission": "Find a tray return station in a cafeteria, a stack of plates/baskets at a food hall, or a pile of brochures/books on a display table. Put your phone away and observe how items are added and removed for {duration} minutes.",
        "observation_questions": [
            "Which tray or item is taken first: the one placed first or the one placed last?",
            "What would happen if you attempted to pull an item from the very bottom of the pile?",
            "How does this LIFO (Last-In, First-Out) behavior mirror an undo stack or browser back button?"
        ],
        "safety_note": "Observe passively without handling food service items or disturbing displays."
    },
    "linear_search": {
        "title": "The Unsorted Bookshelf Scan",
        "mission": "Find a public bookshelf, bulletin board of flyers, or store snack rack. Choose one specific target item in your mind and simulate searching for it sequentially. Put your phone away and observe the physical search pattern for {duration} minutes.",
        "observation_questions": [
            "Did your eyes inspect each item in order from left to right, one by one?",
            "How does the time to find an item change if the target is at the beginning versus the very end?",
            "What would be the worst-case scenario (O(N)) if the item isn't on the shelf at all?"
        ],
        "safety_note": "Stand in public pedestrian flow without blocking aisle access."
    },
    "binary_search": {
        "title": "The Sorted Street Number Probe",
        "mission": "Find a hallway with numbered doors, a printed directory/dictionary, or a street with clearly ascending building numbers. Observe how someone would find a specific number by jumping halfway. Put your phone away and trace the middle split for {duration} minutes.",
        "observation_questions": [
            "Is the environment strictly sorted in ascending or descending order?",
            "If you look at the middle number and it is too high, which half do you eliminate?",
            "Why is this logarithmic O(log N) approach vastly faster than checking every single door?"
        ],
        "safety_note": "Remain on public sidewalks or open lobbies; do not enter private residences."
    },
    "bottleneck": {
        "title": "The Sidewalk Funnel & Turnstile",
        "mission": "Find a spot where a wide open space narrows into a single exit door, turnstile, escalator, or crosswalk. Put your phone away, step to the side, and watch the pedestrian flow for {duration} minutes.",
        "observation_questions": [
            "What is the arrival rate of people entering the wide area versus the exit rate through the choke point?",
            "Does a queue form immediately behind the narrowest point when arrival rate exceeds capacity?",
            "How would a systems engineer increase total throughput without widening the physical exit?"
        ],
        "safety_note": "Stand well clear of the pedestrian funnel so you do not contribute to the congestion."
    },
    "scheduling": {
        "title": "The Crosswalk Signal Dispatcher",
        "mission": "Find a four-way intersection with pedestrian walk signals. Put your phone away, sit or stand on a public bench, and observe how the intersection allocates green time to competing directions for {duration} minutes.",
        "observation_questions": [
            "Does the traffic signal use a fixed round-robin schedule, or does it adapt dynamically when a pedestrian presses a call button?",
            "How does the controller balance starvation prevention (giving everyone a turn) with maximum throughput?",
            "What priority rules are enforced (e.g. emergency vehicles vs pedestrians vs cross-traffic)?"
        ],
        "safety_note": "Stay completely on the sidewalk behind the curb; do not step into the street."
    },
    "classification": {
        "title": "The Three-Stream Waste Classifier",
        "mission": "Find a public waste station with separated bins (e.g., compost, recycling, landfill). Put your phone away and observe how people categorize items before disposal for {duration} minutes.",
        "observation_questions": [
            "What features (material, cleanliness, shape) determine which class/bin an item belongs to?",
            "Did you observe any misclassification (false positives or false negatives)?",
            "What label ambiguity occurs with complex items (like coffee cups with wax linings)?"
        ],
        "safety_note": "Observe from several feet away; do not touch trash or peer into bins."
    },
    "anomaly_detection": {
        "title": "The Outlier in the Crowd",
        "mission": "Find a quiet public square, park, or sidewalk. Observe the baseline pattern of activity for 2 minutes to define 'normal', then spend {duration} minutes spotting true anomalies or outliers.",
        "observation_questions": [
            "What defined the 'normal distribution' of the environment (speed of walking, noise level, clothing)?",
            "What unexpected event or object stood out as a statistical outlier?",
            "Was the outlier benign noise, or did it trigger a reaction from the surrounding system?"
        ],
        "safety_note": "Never stare aggressively at individuals; observe ambient environmental patterns."
    },
    "sampling": {
        "title": "The Transit Color Sample",
        "mission": "Find a public vantage point overlooking passing traffic or pedestrians. Define a sample rule (e.g., count the color of every 3rd car, or note the bag type of 10 consecutive people). Put your phone away and collect your mental sample for {duration} minutes.",
        "observation_questions": [
            "How representative do you think your small sample size is of the entire day's population?",
            "What selection bias might exist due to the specific time of day or location chosen?",
            "How would increasing the sample size reduce variance in your estimation?"
        ],
        "safety_note": "Stay safely on the pedestrian walkway; do not stand close to road shoulders."
    },
    "duplicate_data": {
        "title": "The Redundant Notice Board",
        "mission": "Find a public community bulletin board, kiosk, or storefront window covered in posters or announcements. Put your phone away and scan the items for {duration} minutes to identify exact or near-duplicate messages.",
        "observation_questions": [
            "Are there duplicate copies of the exact same event flyer posted in multiple places?",
            "How does redundant data waste limited screen/board real estate?",
            "If you were writing a deduplication algorithm for this board, what unique key (e.g. event title + date) would you hash?"
        ],
        "safety_note": "Stand comfortably back from the board and allow others normal access."
    }
}


def load_concepts() -> List[Concept]:
    """Load concepts from data/concepts.json."""
    if not CONCEPTS_PATH.exists():
        raise FileNotFoundError(f"Concepts catalogue missing at: {CONCEPTS_PATH}")
    with open(CONCEPTS_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    return [Concept.model_validate(item) for item in data]


def get_concept_by_id(concept_id: str) -> Optional[Concept]:
    """Find a concept by its unique id."""
    concepts = load_concepts()
    for c in concepts:
        if c.id == concept_id:
            return c
    return None


def get_concepts_by_category(category: str) -> List[Concept]:
    """Filter concepts by category (e.g. DSA, Systems, AI/ML, Data)."""
    return [c for c in load_concepts() if c.category.lower() == category.lower()]


def is_mission_safe(mission: Mission) -> Tuple[bool, Optional[str]]:
    """Deterministically check a mission against safety constraints."""
    full_text = f"{mission.title} {mission.mission} {' '.join(mission.observation_questions)} {mission.safety_note}".lower()

    for pattern in UNSAFE_PATTERNS:
        match = re.search(pattern, full_text, flags=re.IGNORECASE)
        if match:
            return False, f"Deterministic safety rule triggered: '{match.group(0)}'"

    return True, None


def get_fallback_mission(concept: Concept, duration: int = 10) -> Mission:
    """Return a guaranteed safe, pre-crafted mission for the concept."""
    template = FALLBACK_MISSIONS.get(concept.id)
    if not template:
        # Generic safe fallback if concept ID is not mapped
        return Mission(
            title=f"Observing {concept.name} in Action",
            mission=(
                f"Find a safe public space where {concept.name.lower()} naturally occurs "
                f"(e.g., {concept.safe_observation_contexts[0] if concept.safe_observation_contexts else 'a public lobby'}). "
                f"Observe silently for {duration} minutes with your phone put away."
            ),
            observation_questions=[
                f"How does the physical setup reflect the core mechanism of {concept.name}?",
                "What inputs, transformations, or outputs are visible?",
                "What constraints or edge cases could cause this real-world system to fail?"
            ],
            concept=concept.name,
            estimated_minutes=duration,
            safety_note="Remain in open public areas and observe passively from a safe distance.",
            is_fallback=True,
        )

    mission_text = template["mission"].replace("{duration}", str(duration))
    return Mission(
        title=template["title"],
        mission=mission_text,
        observation_questions=template["observation_questions"],
        concept=concept.name,
        estimated_minutes=duration,
        safety_note=template["safety_note"],
        is_fallback=True,
    )


def generate_mission(
    concept: Concept,
    duration: int = 10,
    environment: Optional[str] = None,
    use_fallback_on_error: bool = True,
    model: Optional[str] = None,
    host: Optional[str] = None,
) -> Mission:
    """Generate a physical CS observation mission using local Gemma.

    Applies deterministic safety validation and falls back cleanly on error.
    """
    if not PROMPT_TEMPLATE_PATH.exists():
        if use_fallback_on_error:
            logger.warning("Prompt template missing, using fallback mission.")
            return get_fallback_mission(concept, duration)
        raise FileNotFoundError(f"Mission prompt template missing at: {PROMPT_TEMPLATE_PATH}")

    with open(PROMPT_TEMPLATE_PATH, "r", encoding="utf-8") as f:
        template = f.read()

    safe_contexts_str = ", ".join(concept.safe_observation_contexts)
    env_str = environment.strip() if environment else "Everyday public open space or street"

    prompt = template.format(
        concept_name=concept.name,
        category=concept.category,
        concept_explanation=concept.short_explanation,
        safe_contexts=safe_contexts_str,
        duration=duration,
        environment=env_str,
    )

    try:
        mission = generate_structured_response(
            prompt=prompt,
            response_model=Mission,
            model=model,
            host=host,
            temperature=0.4,
        )

        # Enforce that duration and concept match
        mission.estimated_minutes = duration
        mission.concept = concept.name
        mission.is_fallback = False

        # Deterministic Safety Verification
        safe, reason = is_mission_safe(mission)
        if not safe:
            logger.warning("Generated mission failed deterministic safety check (%s). Falling back.", reason)
            return get_fallback_mission(concept, duration)

        return mission

    except Exception as exc:
        logger.warning("Gemma mission generation failed (%s). Utilizing safe fallback.", exc)
        if use_fallback_on_error:
            return get_fallback_mission(concept, duration)
        raise
