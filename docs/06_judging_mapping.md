# Item 7 — Judging Criteria Mapping Table

> Phase 0 design document · Engram · Graph Hacks 2026
> Track 2: Agent Memory and Coordination

---

## Criterion → Feature → Demo Moment → Test

| Judging Criterion | Our Feature | Demo Moment (timestamp) | Test That Proves It |
|-------------------|-------------|------------------------|---------------------|
| **Technical Implementation: Functionality** | Full investigation pipeline works end-to-end | [0:15-0:50] Ask about duplicate charges, get multi-source answer | All benchmark tests pass (21 test cases) |
| **Technical Implementation: FalkorDB Integration** | 15 Cypher queries, vector search, full-text search, constraints | Entire demo — every answer comes from graph queries | CF-1/CF-2/CF-3: Remove edge → answer changes |
| **Technical Implementation: Code Quality** | Typed Python, FastAPI, modular agent classes, test suite | README + repository | pytest output, type hints, docstrings |
| **Innovation: Originality** | Bi-temporal fact model (valid_time + transaction_time), supersession chains, contradiction handling | [1:55-2:30] Show fact-006 superseded by fact-001, contradictions surfaced | TR-1/TR-2/TR-3 temporal tests, CH-1/CH-2/CH-3 contradiction tests |
| **Innovation: Creative FalkorDB Use** | Facts as first-class graph nodes with provenance edges, not just entity-relationship storage | [0:50-1:25] Click fact to see evidence chain: asserter → source → verifier | Explain query (Q4) returns full provenance |
| **Impact: Problem-Solving** | Engineers lose context between investigations, can't trace why decisions were made | Opening narration [0:00-0:15] + cross-session recall [0:50-1:25] | SP-1/SP-2/SP-3 persistence tests |
| **Impact: Real-World Value** | Works for any team with incidents, services, and documentation | Synthetic but realistic data — PayFlow platform with 5 incidents | MH-1/MH-2/MH-3 multi-hop tests on realistic scenarios |
| **Demo: Clarity** | 3-minute video with 5 clear sections, narration, visible graph changes | Full demo [0:00-3:00] | Practice 3x before recording |
| **Demo: Completeness** | Working UI, backend, graph, agents, tests, README | All 7 screens shown in demo | Repository contains all components |

---

## Track 2-Specific Criteria → Feature Mapping

| Track 2 Requirement | Our Implementation | Strength Level |
|---------------------|-------------------|----------------|
| **Memory persists across sessions** | Facts stored in FalkorDB with session provenance, recalled via cross_session_recall | ★★★★★ — Core feature, tested in SP-1/SP-2/SP-3 |
| **Memory evolves (updates, corrections)** | Supersession chains (SUPERSEDES edge), status machine (hypothesis→verified→superseded) | ★★★★★ — Unique differentiator, timeline visualization |
| **Agent coordination** | 4 agents with role separation, task claim/handoff, shared graph state | ★★★★☆ — Real coordination, but in single process |
| **Explainable recall** | Explain query traces: fact → source → session → agent → verification | ★★★★★ — Every recalled fact has full provenance |
| **Graph is essential** | Counterfactual test: remove edge → answer changes | ★★★★★ — Demo part 4 proves this live |

---

## Where We're Weakest (Honest Assessment)

| Area | Risk | Mitigation |
|------|------|-----------|
| **Multi-process agents** | Agents run in same process, not distributed | Document as design choice: logically separate, shares FalkorDB. Judges care about coordination protocol, not process boundaries. |
| **Scale** | 32 entities, 12 facts is small | Judges know it's a 3-day hackathon. Quality of reasoning > quantity of data. |
| **UI polish** | May not have time for advanced graph visualization | Focus on evidence panel + timeline. Use a simple force-directed graph (vis.js or react-force-graph) for the graph view. |
| **Vector search** | May not be needed if graph queries are sufficient | If vector search works: show hybrid retrieval. If not: show that graph-only retrieval is already better than vector-only. |

---

## Score Maximization Strategy

### Highest-Impact Actions (do these first)
1. ✅ Graph-dependent reasoning — the counterfactual test (CF-1/2/3)
2. ✅ Cross-session memory — recall from previous sessions (SP-1/2/3)
3. ✅ Agent coordination — visible handoff chain in the UI
4. ✅ Evidence provenance — click any fact to see its full chain

### Moderate-Impact Actions (do if time allows)
5. 🔲 Memory evolution timeline visualization
6. 🔲 Contradiction highlighting
7. 🔲 Full benchmark suite with automated scoring

### Low-Impact Actions (skip if behind schedule)
8. 🔲 Multi-project isolation demo
9. 🔲 Poisoning detection demo
10. 🔲 Production deployment (local demo is sufficient)
