# Item 8 — Risk Register and Cut List

> Phase 0 design document · Engram · Graph Hacks 2026
> Track 2: Agent Memory and Coordination

---

## Risk Register

### R1: FalkorDB Cypher Incompatibilities (HIGH)
**What:** Critical query patterns (IS NULL, OPTIONAL MATCH, variable-length paths) may not work.
**Probability:** Medium (some are confirmed, some need testing).
**Impact:** High — core queries break.
**Mitigation:** 
- First task on Oct 15: run `verify_falkordb_features.py`
- Every query has a documented fallback (sentinel values, split queries, Python post-processing)
- Budget 3 hours for query adaptation

### R2: LLM Tool-Calling Unreliability (MEDIUM)
**What:** The LLM may not consistently call the right tools with correct parameters.
**Probability:** Medium — depends on model and prompt engineering.
**Impact:** Medium — agent workflow breaks unpredictably.
**Mitigation:**
- Use structured tool definitions (JSON schema)
- Keep tool count per agent ≤ 5
- Add retry logic with fallback to simpler prompts
- For the demo: pre-test the exact questions and tune prompts

### R3: Time Pressure — Solo Developer (HIGH)
**What:** 3 days is not enough to build everything described in these docs.
**Probability:** High.
**Impact:** Incomplete submission.
**Mitigation:**
- Strict cut list (see below)
- Focus on one end-to-end workflow, not breadth
- UI can be minimal if the graph engine is solid
- Skip deployment if local demo works

### R4: Docker/FalkorDB Setup Issues on Windows (MEDIUM)
**What:** Docker Desktop on Windows may have networking, WSL2, or memory issues.
**Probability:** Medium.
**Impact:** Can't start development.
**Mitigation:**
- Use FalkorDB Cloud (free tier) as fallback
- Pre-install Docker Desktop and pull `falkordb/falkordb:latest` before Oct 15
- Test basic container startup now (this is not coding — it's environment setup)

### R5: Demo Video Quality (MEDIUM)
**What:** Poor recording, unclear narration, or bugs during recording.
**Probability:** Medium.
**Impact:** Judges can't evaluate the project properly.
**Mitigation:**
- Practice the demo sequence 3 times
- Record narration separately (better audio quality)
- Have a backup: screen recording with captions if voice fails
- Record on Oct 17 evening, leaving Oct 18 for fixes + re-recording

### R6: Vector Index Doesn't Work (LOW-MEDIUM)
**What:** Vector similarity search fails or produces poor results.
**Probability:** Low (confirmed in docs).
**Impact:** Medium — lose semantic recall capability.
**Mitigation:**
- Fall back to full-text search + exact graph queries
- The demo can still work without vector search (graph queries are the star)

### R7: Scope Creep (HIGH)
**What:** Adding features not in the cut list, polishing UI instead of fixing bugs.
**Probability:** High (especially solo).
**Impact:** Core workflow doesn't work while extras are half-built.
**Mitigation:**
- This cut list. Review it every 4 hours during the hackathon.
- Rule: no new feature unless the existing workflow is tested and working.

### R8: Submission Mechanics (LOW)
**What:** Forget to include README, demo video, or deployment instructions.
**Probability:** Low.
**Impact:** Disqualification or low scores.
**Mitigation:**
- Submission checklist (see build plan, Oct 18)
- Prepare README template on Oct 15

---

## Cut List — Drop Order (First to Drop → Last to Drop)

When time runs out, drop features in this order. Items at the top are least critical.

### TIER 4 — Drop First (Nice-to-Have)

| # | Feature | Why It Can Be Cut |
|---|---------|-------------------|
| 1 | Production deployment | Local demo is acceptable per rules |
| 2 | Multi-project isolation demo | Keep project_id filtering in code, skip demoing it |
| 3 | Poisoning detection demo | Interesting but not a Track 2 core requirement |
| 4 | Animated graph visualization | Static evidence panel is sufficient |
| 5 | Blog post (AirPods prize) | PS5 > AirPods. Focus on the main track |

### TIER 3 — Drop If Behind (Enhancers)

| # | Feature | Impact of Cutting |
|---|---------|-------------------|
| 6 | Contradiction visualization (side-by-side) | Lose a demo moment, but contradictions can be shown in text |
| 7 | Memory timeline visualization | Lose demo part 5, but can describe in README |
| 8 | Full benchmark suite with automated scoring | Lose a talking point, but can run tests manually |
| 9 | Vector/semantic search | Graph queries alone can demo memory + coordination |
| 10 | VerifierBot as separate agent | Fold verification into ResolverBot |

### TIER 2 — Keep If Possible (Strong Demo Moments)

| # | Feature | Impact of Cutting |
|---|---------|-------------------|
| 11 | Agent activity log panel | Judges can't see coordination in real-time |
| 12 | Evidence provenance panel (click fact → see chain) | Lose explainability demo |
| 13 | Task claim and handoff | Lose coordination demo |
| 14 | Fact supersession with SUPERSEDES edge | Lose memory evolution demo |

### TIER 1 — Never Drop (Core Requirements)

| # | Feature | Why It's Essential |
|---|---------|-------------------|
| 15 | FalkorDB with synthetic data loaded | No graph = disqualification |
| 16 | At least one multi-hop Cypher query | Proves graph-driven reasoning |
| 17 | Cross-session fact persistence | Core of Track 2 |
| 18 | At least 2 agents sharing graph state | Core of Track 2 |
| 19 | Chat interface (even minimal) | Need a way to interact |
| 20 | Counterfactual test (remove edge → answer changes) | Proves FalkorDB is essential |
| 21 | Working demo video | Required for submission |
| 22 | README with architecture + setup instructions | Required for submission |
| 23 | Public repository | Required for submission |

---

## Decision Framework

At each 4-hour checkpoint during the hackathon:

1. **Is the Tier 1 feature set working end-to-end?**
   - No → Fix it. Don't touch anything else.
   - Yes → Continue.

2. **Is the current feature set tested?**
   - No → Write the test. Don't add new features.
   - Yes → Continue.

3. **How much time is left?**
   - > 24 hours → Work on Tier 2 features
   - 12-24 hours → Only Tier 2 features that are >50% done
   - 6-12 hours → Stop building features. Polish, test, record.
   - < 6 hours → README, demo video, submission only.
