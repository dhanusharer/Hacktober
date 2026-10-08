# CodeWalk — Interactive Demo & Submission Walkthrough

**Challenge:** Hacktoberfest 2026 Week 1 "Touch Grass" Challenge  
**Core Model:** Google Gemma 2 2B (Local via Ollama)  
**Technology:** Python, Streamlit, Pydantic, Ollama, Pytest  

---

## 1. Application Walkthrough

### Screen 1: Choose Mission
The user opens CodeWalk at `http://localhost:8501`.

```
============================================================
🌱 CODEWALK
"Find Computer Science in the Real World."
============================================================

1. Select a Computer Science Category:
   (o) DSA    ( ) Systems    ( ) AI/ML    ( ) Data

2. Choose a Target Concept:
   [ Queue                      v ]

   📖 Concept Breakdown:
   A First-In, First-Out (FIFO) linear data structure where elements 
   are added at the back (enqueue) and removed from the front (dequeue).

   Where to look:
   - Coffee shop order counter or bakery pickup line
   - Bus stop or transit ticket booth
   - Cars at a stop sign or drive-through lane

3. Target Outdoor Duration:
   5 min ───●─── 10 min ────── 15 min

4. Your Current Location (Optional):
   [ Near a coffee shop on campus ]

[ 🚀 START MISSION ]
```

---

### Screen 2: Mission Display & "Put Phone Away"
Gemma crafts a specific physical mission for the user.

```
============================================================
🎯 YOUR MISSION
[Concept: Queue] [Duration: 10 min] [Gemma 2B]
============================================================

Title: The Coffee Line FIFO Queue
Mission: Observe the coffee line at a local cafe for 10 minutes.
Notice how customers join the line, what happens as they get served,
and how they leave.

Think about these questions while observing:
- What happens first when a customer joins the line?
- What happens next in the process?
- How do customers leave the line after being served?

🛡️ Safety note: Stay in safe public areas and observe from a respectful distance.

┌──────────────────────────────────────────────────────────┐
│             📴 PUT YOUR PHONE AWAY.                      │
│             COME BACK WHEN YOU'RE DONE.                  │
└──────────────────────────────────────────────────────────┘

[ 🚶 I'M BACK — RECORD OBSERVATION ]
```

---

### Screen 3: User Observation Submission
The user returns from the real world and types what they noticed.

```
============================================================
📝 WHAT DID YOU NOTICE?
============================================================
You just observed Queue for 10 minutes.

Your Physical Observations:
┌──────────────────────────────────────────────────────────┐
│ I observed the order line at the campus bakery.          │
│ Customers arrived and joined the back of the line.       │
│ The cashier took orders one by one in the exact order    │
│ people arrived (first-in, first-out).                    │
│ When a customer had a custom order that took longer,     │
│ the line backed up behind them, showing the register was │
│ the throughput bottleneck.                               │
└──────────────────────────────────────────────────────────┘

[ 🔍 ANALYZE MY OBSERVATION ]
```

---

### Screen 4: Real-World to CS Evaluation
Gemma evaluates the submission, maps physical components to CS theory, and provides a learning point and next mission.

```
============================================================
📊 EVALUATION RESULTS
[✅ STRONG MATCH]  [Confidence: 95%]  [Target: Queue]
============================================================

Analysis & Feedback:
You accurately identified the FIFO (First-In, First-Out) queuing
discipline, arrival at the tail, and departure from the head. You also
correctly recognized how single-point processing delays create backpressure.

🗺️ Real-World to CS Mapping:
┌───────────────────────────────┬──────────────────────────────┐
│ Physical Observation          │ Computer Science Equivalent  │
├───────────────────────────────┼──────────────────────────────┤
│ Customers waiting in line     │ Queue items / Buffer elements│
│ Cashier register              │ Processing unit / Consumer   │
│ Multi-drink order delay       │ Head-of-line blocking        │
└───────────────────────────────┴──────────────────────────────┘

💡 Computer Science Learning Point:
In operating systems and network queues, head-of-line blocking occurs
when a slow task at the front of a FIFO queue prevents subsequent ready
tasks from executing.

⏭️ Suggested Next Mission:
Observe a four-way crosswalk or traffic light to see how scheduling
algorithms alternate between competing queues.

[ 🎉 FINISH & TOUCH GRASS SUMMARY ]
```

---

### Screen 5: Touch Grass Completion Summary
Celebration of stepping away from the screen and connecting CS to physical reality.

```
============================================================
🌱 YOU TOUCHED GRASS!
Congratulations on closing the laptop and exploring real-world computing.
============================================================

Session Accomplishments:
- Total outdoor observation time: 10 minutes
- Concepts explored: Queue

"Computer science is no more about computers than astronomy is
about telescopes."
— Edsger W. Dijkstra

[ 🚀 Start a New CodeWalk ]
```

---

## 2. Test Verification Matrix

All four required verification scenarios are verified automatically:

| Scenario | Concept | User Observation | Expected Verdict | Verified Result |
|---|---|---|---|---|
| **TEST A** | `Queue` | Detailed FIFO arrival and counter departure | `STRONG_MATCH` | ✅ PASS |
| **TEST B** | `Queue` | Vague: "People standing around waiting" | `PARTIAL_MATCH` or `NOT_A_MATCH` | ✅ PASS |
| **TEST C** | `Queue` | Unrelated: "Trees and birds in the park" | `NOT_A_MATCH` | ✅ PASS |
| **TEST D** | `Queue` | Gemma offline (network failure simulation) | Safe fallback | ✅ PASS (Zero crash) |
