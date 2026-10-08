"""CodeWalk: Find Computer Science in the Real World.

Hacktoberfest 2026 Week 1 "Touch Grass" Challenge Submission.
Powered by Local Google Gemma (via Ollama).
"""

from __future__ import annotations

import streamlit as st
from engine.gemma import check_ollama_status, DEFAULT_GEMMA_MODEL
from engine.missions import (
    Concept,
    Mission,
    load_concepts,
    get_concept_by_id,
    get_concepts_by_category,
    generate_mission,
)
from engine.evaluator import (
    Verdict,
    EvaluationResult,
    evaluate_observation,
)

# Page configuration
st.set_page_config(
    page_title="CodeWalk — Find CS in the Real World",
    page_icon="🌱",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# Custom CSS for polished, distraction-free outdoor styling
st.markdown(
    """
    <style>
    .main-header {
        font-size: 2.4rem;
        font-weight: 800;
        letter-spacing: -0.03em;
        margin-bottom: 0.1rem;
        color: #1b4332;
    }
    .tagline {
        font-size: 1.15rem;
        color: #40916c;
        margin-bottom: 1.5rem;
        font-weight: 500;
    }
    .mission-card {
        background-color: #f4f9f4;
        border: 2px solid #b7e4c7;
        border-radius: 12px;
        padding: 24px;
        margin: 20px 0;
    }
    .phone-away-banner {
        background-color: #1b4332;
        color: #d8f3dc;
        border-radius: 10px;
        padding: 20px;
        text-align: center;
        font-size: 1.25rem;
        font-weight: 700;
        letter-spacing: 0.05em;
        margin: 24px 0;
        box-shadow: 0 4px 12px rgba(27, 67, 50, 0.15);
    }
    .verdict-strong {
        background-color: #d8f3dc;
        color: #1b4332;
        border: 1px solid #74c69d;
        padding: 8px 16px;
        border-radius: 20px;
        font-weight: 700;
        display: inline-block;
    }
    .verdict-partial {
        background-color: #fefae0;
        color: #bc6c25;
        border: 1px solid #dda15e;
        padding: 8px 16px;
        border-radius: 20px;
        font-weight: 700;
        display: inline-block;
    }
    .verdict-nomatch {
        background-color: #fceade;
        color: #9d0208;
        border: 1px solid #f48c06;
        padding: 8px 16px;
        border-radius: 20px;
        font-weight: 700;
        display: inline-block;
    }
    .metric-badge {
        font-size: 0.85rem;
        background-color: #e9ecef;
        padding: 4px 10px;
        border-radius: 12px;
        font-weight: 600;
        color: #495057;
        margin-right: 8px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Initialize Session State
if "step" not in st.session_state:
    st.session_state.step = "choose_mission"  # choose_mission | display_mission | record_observation | view_evaluation | completed

if "current_concept" not in st.session_state:
    st.session_state.current_concept = None

if "current_mission" not in st.session_state:
    st.session_state.current_mission = None

if "current_evaluation" not in st.session_state:
    st.session_state.current_evaluation = None

if "user_observation_text" not in st.session_state:
    st.session_state.user_observation_text = ""

if "explored_concepts" not in st.session_state:
    st.session_state.explored_concepts = []

if "total_outdoor_minutes" not in st.session_state:
    st.session_state.total_outdoor_minutes = 0


# Sidebar System Status
with st.sidebar:
    st.subheader("⚙️ System Status")
    status = check_ollama_status()
    if status["connected"]:
        st.success(f"Ollama: Connected ({status['host']})")
        if status["model_available"]:
            st.info(f"Model: {DEFAULT_GEMMA_MODEL} (Local Ready)")
        else:
            st.warning(f"Target model '{DEFAULT_GEMMA_MODEL}' not found. Using safe fallbacks.")
    else:
        st.warning("Ollama offline. Running with verified local fallback engine.")

    st.markdown("---")
    st.markdown("**Hacktoberfest 2026**")
    st.markdown("Week 1: *Touch Grass Challenge*")
    st.caption("100% Local Inference — No cloud AI API keys required.")


# ==============================================================================
# SCREEN 1: CHOOSE MISSION
# ==============================================================================
if st.session_state.step == "choose_mission":
    st.markdown("<div class='main-header'>🌱 CODEWALK</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='tagline'>\"Find Computer Science in the Real World.\"</div>",
        unsafe_allow_html=True,
    )

    st.markdown(
        "Step outside. Observe physical systems in action. Connect reality back to computational theory."
    )

    # Category Selection
    category_tabs = ["DSA", "Systems", "AI/ML", "Data"]
    selected_category = st.radio(
        "**1. Select a Computer Science Category:**",
        category_tabs,
        horizontal=True,
    )

    # Concepts in Category
    concepts = get_concepts_by_category(selected_category)
    concept_names = [c.name for c in concepts]
    selected_concept_name = st.selectbox(
        "**2. Choose a Target Concept:**",
        concept_names,
    )

    selected_concept = next(c for c in concepts if c.name == selected_concept_name)

    # Concept Details Preview
    with st.expander("📖 Concept Breakdown & Real-World Hints", expanded=True):
        st.write(f"**Explanation:** {selected_concept.short_explanation}")
        st.write("**Where to look:**")
        for ctx in selected_concept.safe_observation_contexts:
            st.markdown(f"- {ctx}")

    # Duration selection
    col1, col2 = st.columns([1, 1])
    with col1:
        duration = st.select_slider(
            "**3. Target Outdoor Duration:**",
            options=[5, 10, 15],
            value=10,
            format_func=lambda m: f"{m} minutes",
        )

    with col2:
        env_notes = st.text_input(
            "**4. Your Current Location (Optional):**",
            placeholder="e.g. coffee shop, bus stop, library, sidewalk",
        )

    st.markdown("<br>", unsafe_allow_html=True)

    if st.button("🚀 START MISSION", type="primary", use_container_width=True):
        with st.spinner("Gemma is crafting your outdoor mission..."):
            mission = generate_mission(
                concept=selected_concept,
                duration=duration,
                environment=env_notes.strip() if env_notes else None,
                use_fallback_on_error=True,
            )
            st.session_state.current_concept = selected_concept
            st.session_state.current_mission = mission
            st.session_state.step = "display_mission"
            st.rerun()


# ==============================================================================
# SCREEN 2: DISPLAY MISSION
# ==============================================================================
elif st.session_state.step == "display_mission":
    mission: Mission = st.session_state.current_mission
    concept: Concept = st.session_state.current_concept

    st.markdown("<div class='main-header'>🎯 YOUR MISSION</div>", unsafe_allow_html=True)
    st.markdown(
        f"<span class='metric-badge'>Concept: {mission.concept}</span>"
        f"<span class='metric-badge'>Duration: {mission.estimated_minutes} min</span>"
        + ("<span class='metric-badge'>Local Offline Fallback</span>" if mission.is_fallback else "<span class='metric-badge'>Gemma 2B</span>"),
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div class='mission-card'>
            <h3 style='margin-top: 0; color: #1b4332;'>{mission.title}</h3>
            <p style='font-size: 1.15rem; line-height: 1.6;'>{mission.mission}</p>
            <hr style='border: 0; border-top: 1px solid #b7e4c7; margin: 16px 0;'>
            <strong>Think about these questions while observing:</strong>
            <ul style='margin-top: 8px;'>
                {"".join(f"<li>{q}</li>" for q in mission.observation_questions)}
            </ul>
            <p style='margin-top: 12px; font-size: 0.9rem; color: #52796f;'>
                🛡️ <em>Safety note: {mission.safety_note}</em>
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Core Instruction
    st.markdown(
        """
        <div class='phone-away-banner'>
            📴 PUT YOUR PHONE AWAY.<br>
            COME BACK WHEN YOU'RE DONE.
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_btn1, col_btn2 = st.columns([1, 1])
    with col_btn1:
        if st.button("⬅️ Choose Another Concept", use_container_width=True):
            st.session_state.step = "choose_mission"
            st.rerun()

    with col_btn2:
        if st.button("🚶 I'M BACK — RECORD OBSERVATION", type="primary", use_container_width=True):
            st.session_state.step = "record_observation"
            st.rerun()


# ==============================================================================
# SCREEN 3: RECORD OBSERVATION
# ==============================================================================
elif st.session_state.step == "record_observation":
    mission: Mission = st.session_state.current_mission
    concept: Concept = st.session_state.current_concept

    st.markdown("<div class='main-header'>📝 WHAT DID YOU NOTICE?</div>", unsafe_allow_html=True)
    st.markdown(
        f"You just observed **{concept.name}** for **{mission.estimated_minutes} minutes**.",
        unsafe_allow_html=True,
    )

    st.info(
        "Write what you physically saw. What items or people entered? What processing happened? "
        "Where did delays or state transitions occur?"
    )

    obs_text = st.text_area(
        "Your Physical Observations:",
        value=st.session_state.user_observation_text,
        placeholder="e.g. I stood by the coffee counter. Customers formed a single line at the cash register. "
                    "Each person ordered one at a time in the exact sequence they arrived...",
        height=180,
    )

    st.session_state.user_observation_text = obs_text

    col_sub1, col_sub2 = st.columns([1, 2])
    with col_sub1:
        if st.button("⬅️ Review Mission"):
            st.session_state.step = "display_mission"
            st.rerun()

    with col_sub2:
        if st.button("🔍 ANALYZE MY OBSERVATION", type="primary", use_container_width=True):
            if not obs_text.strip():
                st.warning("Please enter your observation before analyzing.")
            else:
                with st.spinner("Gemma is evaluating your observation against computer science theory..."):
                    result = evaluate_observation(
                        concept=concept,
                        mission=mission,
                        user_observation=obs_text,
                        use_fallback_on_error=True,
                    )
                    st.session_state.current_evaluation = result

                    # Record exploration
                    if concept.name not in st.session_state.explored_concepts:
                        st.session_state.explored_concepts.append(concept.name)
                    st.session_state.total_outdoor_minutes += mission.estimated_minutes

                    st.session_state.step = "view_evaluation"
                    st.rerun()


# ==============================================================================
# SCREEN 4: VIEW EVALUATION
# ==============================================================================
elif st.session_state.step == "view_evaluation":
    eval_res: EvaluationResult = st.session_state.current_evaluation
    concept: Concept = st.session_state.current_concept
    mission: Mission = st.session_state.current_mission

    st.markdown("<div class='main-header'>📊 EVALUATION RESULTS</div>", unsafe_allow_html=True)

    # Verdict Badge
    if eval_res.verdict == Verdict.STRONG_MATCH:
        badge_html = "<span class='verdict-strong'>✅ STRONG MATCH</span>"
    elif eval_res.verdict == Verdict.PARTIAL_MATCH:
        badge_html = "<span class='verdict-partial'>⚠️ PARTIAL MATCH</span>"
    else:
        badge_html = "<span class='verdict-nomatch'>❌ NOT A MATCH</span>"

    st.markdown(
        f"{badge_html} &nbsp;&nbsp; "
        f"<span class='metric-badge'>Confidence: {int(eval_res.confidence * 100)}%</span>"
        f"<span class='metric-badge'>Target: {eval_res.concept}</span>"
        + ("<span class='metric-badge'>Offline Fallback</span>" if eval_res.is_fallback else "<span class='metric-badge'>Gemma 2B</span>"),
        unsafe_allow_html=True,
    )

    st.markdown("### Analysis & Feedback")
    st.write(eval_res.explanation)

    # Real World Mapping Table
    if eval_res.real_world_mapping:
        st.markdown("### 🗺️ Real-World to CS Mapping")
        mapping_data = [
            {"Physical Observation": k, "Computer Science Equivalent": v}
            for k, v in eval_res.real_world_mapping.items()
        ]
        st.table(mapping_data)

    # Learning Point Card
    st.markdown(
        f"""
        <div style='background-color: #edf2fb; border-left: 5px solid #2b2d42; padding: 16px; border-radius: 8px; margin: 20px 0;'>
            <strong style='color: #2b2d42;'>💡 Computer Science Learning Point:</strong><br>
            <p style='margin-top: 6px; margin-bottom: 0; color: #1d3557;'>{eval_res.learning_point}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Next Mission Suggestion
    st.markdown("### ⏭️ Suggested Next Mission")
    st.info(f"**Next Step:** {eval_res.next_mission}")

    st.markdown("<br>", unsafe_allow_html=True)
    col_c1, col_c2 = st.columns([1, 1])
    with col_c1:
        if st.button("🔄 Try Another Concept", use_container_width=True):
            st.session_state.user_observation_text = ""
            st.session_state.step = "choose_mission"
            st.rerun()

    with col_c2:
        if st.button("🎉 FINISH & TOUCH GRASS SUMMARY", type="primary", use_container_width=True):
            st.session_state.step = "completed"
            st.rerun()


# ==============================================================================
# SCREEN 5: TOUCH GRASS COMPLETION
# ==============================================================================
elif st.session_state.step == "completed":
    st.markdown("<div class='main-header'>🌱 YOU TOUCHED GRASS!</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='tagline'>Congratulations on closing the laptop and exploring real-world computing.</div>",
        unsafe_allow_html=True,
    )

    st.balloons()

    st.markdown(
        f"""
        <div class='mission-card'>
            <h3 style='margin-top: 0; color: #1b4332;'>Session Accomplishments</h3>
            <p><strong>Total outdoor observation time:</strong> {st.session_state.total_outdoor_minutes} minutes</p>
            <p><strong>Concepts explored:</strong></p>
            <ul>
                {"".join(f"<li><strong>{c}</strong></li>" for c in st.session_state.explored_concepts) if st.session_state.explored_concepts else "<li>Queue</li>"}
            </ul>
            <hr style='border: 0; border-top: 1px solid #b7e4c7; margin: 16px 0;'>
            <p style='margin-bottom: 0;'>
                <em>"Computer science is no more about computers than astronomy is about telescopes."</em><br>
                — Edsger W. Dijkstra
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button("🚀 Start a New CodeWalk", type="primary", use_container_width=True):
        st.session_state.user_observation_text = ""
        st.session_state.step = "choose_mission"
        st.rerun()
