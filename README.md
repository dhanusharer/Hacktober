# CodeWalk

> **"Find Computer Science in the Real World."**  
> Built for the **Hacktoberfest 2026 Week 1 "Touch Grass" Challenge**.

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![Model](https://img.shields.io/badge/model-Gemma%202%202B-green.svg)](https://ollama.com/library/gemma2:2b)
[![Inference](https://img.shields.io/badge/inference-100%25%20Local%20(Ollama)-darkgreen.svg)](https://ollama.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## What is CodeWalk?

**CodeWalk** is an open-source, local-first companion app that challenges developers and computer science students to step away from their monitors, walk outside, and discover foundational computer science principles in the physical world.

Rather than solving abstract algorithmic problems on a screen, CodeWalk gives you a short, physical observation mission (5 to 15 minutes). You put your phone away, observe real-world systems in public spaces (e.g., checkout lines, traffic lights, trash sorting bins, ascending house numbers), return to the app, and document what you saw.

A **locally hosted Google Gemma model** then objectively evaluates your observation, maps the real-world actors to computer science theoretical equivalents, explains the underlying software systems principle, and generates your next mission.

---

## Why I Built It

As software engineers, we spend thousands of hours staring at IDEs, abstract syntax trees, and virtualized services, frequently forgetting that the principles governing our code originated from physical observations of reality:

> *"Computer science is no more about computers than astronomy is about telescopes."*  
> — **Edsger W. Dijkstra**

For the **Hacktoberfest 2026 Week 1 "Touch Grass" challenge**, the goal was simple: create a project that genuinely compels people to disconnect, step outside into their physical environment, and experience the tactile reality of computation.

---

## How It Works

```
 Choose Concept & Duration
 (DSA, Systems, AI/ML, Data)
            │
            ▼
 Gemma Generates Physical Mission
            │
            ▼
  "PUT YOUR PHONE AWAY"
  (Step outside & observe)
            │
            ▼
 Return & Submit Observation Notes
            │
            ▼
 Gemma Evaluates & Maps to CS Theory
 (Strong Match / Partial / Not a Match)
            │
            ▼
 Next Real-World Mission Generated
```

1. **Select Concept & Time:** Pick a topic (e.g., *Queue*, *Bottleneck*, *Anomaly Detection*, *Binary Search*) and your available outdoor time (5, 10, or 15 minutes).
2. **Receive Mission:** Gemma generates a safe, specific physical mission detailing where to look and what questions to consider.
3. **Touch Grass:** The app reminds you to put your phone away and step outside.
4. **Submit Notes:** Return to the app and describe what you observed.
5. **Receive Evaluation:** Gemma evaluates your observation, highlights real-world to CS mappings, delivers a learning point, and suggests your next mission.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   Streamlit UI (app.py)                     │
│  [Screen 1: Choose]  -> [Screen 2: Put Phone Away]          │
│  [Screen 3: Input]   -> [Screen 4: Evaluation] -> [Summary] │
└──────────────────────────────┬──────────────────────────────┘
                               │
                ┌──────────────┴──────────────┐
                ▼                             ▼
   ┌─────────────────────────┐   ┌─────────────────────────┐
   │ Mission Engine          │   │ Evaluator Engine        │
   │ (engine/missions.py)    │   │ (engine/evaluator.py)   │
   └────────────┬────────────┘   └────────────┬────────────┘
                │                             │
                ├─────────────────────────────┤
                ▼                             ▼
   ┌─────────────────────────────────────────────────────────┐
   │ Deterministic Safety Layer & Heuristic Fallback Catalog │
   │ (data/concepts.json, 12 Safety Rules, Regex Filter)     │
   └────────────────────────────┬────────────────────────────┘
                                │
                                ▼
   ┌─────────────────────────────────────────────────────────┐
   │ Local Gemma Client Wrapper (engine/gemma.py)            │
   │ Pydantic Structured Output Validation                   │
   └────────────────────────────┬────────────────────────────┘
                                │ HTTP (Localhost only)
                                ▼
   ┌─────────────────────────────────────────────────────────┐
   │ Local Ollama Service (http://localhost:11434)           │
   │ Google Gemma 2 2B (GGUF Q4_0)                           │
   └─────────────────────────────────────────────────────────┘
```

---

## Why Gemma?

We selected **Google Gemma 2 2B** as the core model for CodeWalk because:

1. **Lightweight Footprint:** At ~1.6 GB in quantized 4-bit precision (`gemma2:2b`), it runs reliably and smoothly on standard consumer laptops with modest CPU/RAM, requiring no dedicated GPU.
2. **Instruction Following:** Gemma 2 demonstrates superior instruction-following for structured JSON extraction compared to earlier small models.
3. **Speed:** Token generation completes in seconds, allowing the app to respond promptly without awkward delays.
4. **Reliability:** Combined with Ollama's `format: "json"` constraint, Gemma consistently produces validated Pydantic structures.

---

## Why Open AI / Open-Weight AI Matters

CodeWalk deliberately avoids closed cloud LLM APIs (OpenAI, Claude, proprietary endpoints). Here is why open-weight AI is vital:

- **Local & Private:** Your personal notes, daily routes, and physical observations are processed 100% locally on your machine. No telemetry or observation text is ever transmitted over the network to external servers.
- **Zero Cloud Dependence:** The application does not require paid subscriptions, API keys, rate limit tiers, or an active internet connection once the model weights are downloaded.
- **Developer Ownership:** Open-weight models empower developers to inspect, audit, fine-tune, and control the exact model version without fear of sudden cloud deprecations or pricing shifts.

---

## Local Setup

### Prerequisites
- **Python 3.10+** (tested on Python 3.11 and 3.12)
- **Ollama** installed ([https://ollama.com](https://ollama.com))

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/CodeWalk.git
cd CodeWalk
```

### 2. Create a Virtual Environment
```bash
# On Windows
python -m venv venv
.\venv\Scripts\activate

# On macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Pull the Gemma Model
Ensure the Ollama server is running, then pull the lightweight Gemma 2 2B model:
```bash
ollama pull gemma2:2b
```

---

## Running the App

Start the Streamlit application:
```bash
streamlit run app.py
```
Open your browser to `http://localhost:8501`.

---

## Example Mission

**Target Concept:** `Queue` (Category: `DSA`)  
**Duration:** `10 minutes`  
**Generated by Gemma 2B:**

```json
{
  "title": "The First-Come, First-Served Line",
  "mission": "Walk to a nearby coffee shop or transit stop. Stand at a respectful distance, put your phone away, and observe how people arrive and leave for 10 minutes.",
  "observation_questions": [
    "Where do new people enter the line, and where do they exit after service?",
    "Is the order of arrival strictly preserved (FIFO), or does anyone jump ahead?",
    "What happens if the service counter slows down while more people arrive?"
  ],
  "concept": "Queue",
  "estimated_minutes": 10,
  "safety_note": "Observe from a natural public vantage point without blocking pathways or approaching strangers."
}
```

---

## Example Evaluation

**User Submitted Observation:**
> *"I watched the coffee shop counter. People arrived and joined the back of the line. The cashier took one order at a time and served the person at the front. When a customer ordered five complex drinks, the line behind them grew rapidly because the barista was overloaded."*

**Gemma Evaluation Output:**
```json
{
  "concept": "Queue",
  "verdict": "STRONG_MATCH",
  "confidence": 0.95,
  "explanation": "You accurately identified the FIFO (First-In, First-Out) queuing discipline, arrival at the tail, and departure from the head. You also correctly recognized how single-point processing delays create backpressure.",
  "real_world_mapping": {
    "customers waiting": "Queue items / Buffer elements",
    "cashier / barista": "Consumer / Processing thread",
    "complex multi-drink order": "High-latency task causing head-of-line blocking"
  },
  "learning_point": "In operating systems and network queues, head-of-line blocking occurs when a slow task at the front of a FIFO queue prevents subsequent ready tasks from executing.",
  "next_mission": "Observe a multi-lane grocery checkout or traffic merge to see how multi-queue or load-balancing scheduling operates."
}
```

---

## Safety

Physical safety is paramount when sending users into public environments. CodeWalk incorporates **deterministic multi-tier safety validation**:

1. **12 Strict Mission Design Rules:** Embedded into all prompt instructions, strictly forbidding dangerous activities.
2. **Deterministic Regex Safety Filter (`engine/missions.py`):** Model outputs are deterministically audited before being shown to the user. Outputs containing dangerous keywords (e.g. approaching strangers, climbing roofs/poles, entering private property, touching high-voltage electrical boxes, standing in traffic) are immediately rejected.
3. **Curated Fallback Catalog:** If any generation violates safety rules, is malformed, or if Ollama is unreachable, CodeWalk seamlessly falls back to pre-vetted, 100% safe missions.

---

## Project Structure

```
CodeWalk/
│
├── app.py                     # Streamlit 5-screen interactive user interface
├── requirements.txt           # Minimal dependencies (streamlit, pydantic, requests, pytest)
├── README.md                  # Comprehensive documentation & guide
├── LICENSE                    # MIT open-source license
├── .gitignore                 # Excludes venv, caches, and temp files
│
├── engine/
│   ├── __init__.py
│   ├── gemma.py               # Local Ollama client with structured JSON parsing
│   ├── missions.py            # Mission generator, concept loader, safety filter
│   └── evaluator.py           # Observation evaluator with CS mapping
│
├── data/
│   └── concepts.json          # Curated catalog (DSA, Systems, AI/ML, Data)
│
├── prompts/
│   ├── mission.txt            # Mission generation prompt template
│   └── evaluator.txt          # Evaluator prompt template
│
├── tests/
│   ├── conftest.py            # Pytest configuration
│   ├── test_missions.py       # Mission engine & safety tests
│   ├── test_evaluator.py      # Evaluator engine & fallback tests
│   └── test_scenarios.py      # Scenarios A, B, C, D integration tests
│
└── demo/
    └── walkthrough.md         # Step-by-step submission walkthrough & test proof
```

---

## Demo

A complete end-to-end walkthrough demonstrating all 5 screens, sample inputs, and verified outputs is located in [demo/walkthrough.md](demo/walkthrough.md).

To run the automated test suite locally:
```bash
pytest -v
```

---

## Limitations

- **Text-Based Observations:** CodeWalk relies on user-written text observations rather than on-device computer vision.
- **Hardware Variation:** Generation speed on local laptops depends on CPU threads and memory bandwidth (typically 5 to 20 seconds for Gemma 2B on modern laptops).
- **Subjectivity in Nuanced Notes:** For borderline observations, small language models can occasionally misclassify nuance; CodeWalk counters this by providing fallback keyword heuristics.

---

## Future Improvements

- **Audio-Guided Missions:** Text-to-speech option allowing users to listen to mission instructions on headphones while walking.
- **Printable Field Cards:** Exportable printable pocket sheets for educators and coding bootcamps.
- **Offline PWA:** Offline-first caching for mobile browsers.

---

## License

This project is licensed under the [MIT License](LICENSE).
