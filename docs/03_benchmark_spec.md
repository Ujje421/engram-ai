# Item 4 — Benchmark Specification with Ground Truth

> Phase 0 design document · Engram · Graph Hacks 2026
> Track 2: Agent Memory and Coordination

---

## Three Baselines

| Baseline | Description | Purpose |
|----------|------------|---------|
| **B0: No Memory** | Agent uses only the current user message + LLM. No graph, no retrieval. | Floor — shows what a raw chatbot produces |
| **B1: Vector RAG** | Agent retrieves top-k chunks from a vector store, feeds them as context to LLM. No graph. | Standard RAG — shows what similarity-only retrieval produces |
| **B2: Engram** | Agent uses FalkorDB graph queries + vector search + persistent memory + multi-agent coordination. | Our system — shows graph-powered advantage |

---

## Benchmark Categories (8)

### Category 1: Multi-Hop Recall

| Test ID | Question | Expected Answer | Required Hops |
|---------|----------|----------------|---------------|
| MH-1 | "Who owns the system affected by inc-005?" | Arun Mehta (Payment API), database has no owner | 2: incident → system → owner |
| MH-2 | "Which services could be affected if the message queue goes down?" | Notification Service, Payment API (via dependency chain) | 1-2 |
| MH-3 | "Who fixed issues related to systems that Payment API depends on?" | Priya (Auth), Rohan (Queue), Sara (Cache) — via DEPENDS_ON + RESOLVED_BY | 2-3 |

**Metric: Recall@K**
- Extract entity names from the agent's answer
- Compare against ground truth entity set
- `Recall = |correct_entities ∩ returned_entities| / |correct_entities|`
- Compute at K=5 and K=10

**Expected scores:**
| Test | B0 | B1 | B2 |
|------|----|----|-----|
| MH-1 | 0.0 (can't traverse) | 0.5 (may find Arun in docs) | 1.0 |
| MH-2 | 0.0 | 0.3 | 1.0 |
| MH-3 | 0.0 | 0.3 | 0.8+ |

---

### Category 2: Temporal Reasoning

| Test ID | Question | Expected Answer |
|---------|----------|----------------|
| TR-1 | "What was the database connection pool size before September 15?" | 20 (from fact-007) |
| TR-2 | "What changed about the payment API after the September incident?" | Pool increased to 50 (fact-003 superseded fact-007) |
| TR-3 | "Show me the timeline of what we know about svc-database" | Chronological: fact-007 → superseded → fact-002, fact-005 |

**Metric: Temporal Accuracy**
- Binary: did the answer reference the correct temporal version of the fact?
- `Accuracy = correct_temporal_answers / total_temporal_questions`

---

### Category 3: Contradiction Handling

| Test ID | Scenario | Expected Behavior |
|---------|----------|-------------------|
| CH-1 | "What's causing the duplicate charges?" | Surface BOTH fact-011 and fact-012 as competing hypotheses with confidence scores |
| CH-2 | "Should we trust the claim about CVE-2026-FAKE?" | Flag as unverified hypothesis from untrusted source |
| CH-3 | Ask the system to verify fact-poison | Should refuse — source is untrusted |

**Metric: Contradiction Detection Rate**
- `CDR = contradictions_surfaced / contradictions_in_ground_truth`
- B0 and B1 will always be 0 (no contradiction tracking)

---

### Category 4: Cross-Agent Handoff

| Test ID | Scenario | Expected Behavior |
|---------|----------|-------------------|
| AH-1 | InvestigatorBot discovers symptoms → KnowledgeBot retrieves related history → ResolverBot proposes fix | Each agent can read the previous agent's findings from FalkorDB |
| AH-2 | InvestigatorBot claims a task → hands off to ResolverBot | Task CLAIMED_BY changes, HANDED_OFF_TO edge created |
| AH-3 | Two agents try to claim the same task simultaneously | Only one succeeds; the other gets empty result |

**Metric: Handoff Completeness**
- Binary per test: did the receiving agent successfully use the previous agent's findings?
- `Completeness = successful_handoffs / attempted_handoffs`

---

### Category 5: Cross-Session Persistence

| Test ID | Scenario | Expected Behavior |
|---------|----------|-------------------|
| SP-1 | Session 1: investigate inc-001. Session 2: "What did we learn about payment issues?" | Retrieve fact-001, fact-002, fact-003 from previous session |
| SP-2 | Session 1: store a hypothesis. Session 2: verify it. Session 3: retrieve verified fact. | Status progression persists: hypothesis → verified |
| SP-3 | Session 1: store fact A. Session 2: supersede with fact B. Session 3: ask about entity. | Return fact B, not fact A. Show supersession in timeline. |

**Metric: Persistence Accuracy**
- `PA = correctly_recalled_facts / expected_recalled_facts`
- B0 = 0 (no persistence). B1 may get partial via vector store persistence.

---

### Category 6: Isolation

| Test ID | Scenario | Expected Behavior |
|---------|----------|-------------------|
| ISO-1 | Query proj-alpha facts, check for proj-gamma leakage | Zero proj-gamma facts returned |
| ISO-2 | Agent in proj-beta tries to read proj-gamma's classified document | Access denied or empty result |
| ISO-3 | Cross-project dependency (fraud-engine → payment-api) | Entity visible, but proj-gamma facts are not |

**Metric: Leakage Rate**
- `LR = leaked_facts / total_facts_in_other_projects`
- Must be 0.0 for pass

---

### Category 7: Insufficient Evidence

| Test ID | Question | Expected Behavior |
|---------|----------|-------------------|
| IE-1 | "Who owns svc-database?" | "No ownership record found" (no OWNS edge exists) |
| IE-2 | "What's the root cause of inc-005?" | "Two hypotheses exist, neither verified yet" |
| IE-3 | "Has the fraud engine ever had an outage?" | "No incident records found for this service" |

**Metric: Abstention Rate**
- `AR = correct_abstentions / abstention_opportunities`
- B0 will likely hallucinate an answer. B1 may hallucinate. B2 should abstain correctly.

---

### Category 8: Counterfactual / Graph Dependency

| Test ID | Modification | Expected Change |
|---------|-------------|-----------------|
| CF-1 | Remove `(svc-payment-api)-[:DEPENDS_ON]->(svc-database)` | Impact analysis for inc-005 no longer shows database path |
| CF-2 | Remove `(inc-001)-[:RESOLVED_BY]->(person-arun)` | "Who fixed the payment timeout?" returns no result |
| CF-3 | Remove all facts from sess-1 | Cross-session recall returns no findings for that period |

**Metric: Graph Sensitivity**
- `GS = 1 if answer_changed_correctly_after_edit, 0 otherwise`
- This is the "remove FalkorDB and does the app break?" test
- B0 and B1 will show GS = 0 (no change, because they don't use the graph)

---

## Composite Scoring

| Metric | Weight | B0 Expected | B1 Expected | B2 Target |
|--------|--------|-------------|-------------|-----------|
| Multi-Hop Recall@5 | 20% | 0.0 | 0.3 | 0.9+ |
| Temporal Accuracy | 10% | 0.0 | 0.2 | 0.9+ |
| Contradiction Detection | 10% | 0.0 | 0.0 | 1.0 |
| Handoff Completeness | 15% | 0.0 | 0.0 | 1.0 |
| Persistence Accuracy | 20% | 0.0 | 0.3 | 1.0 |
| Leakage Rate (inverted) | 5% | N/A | N/A | 0.0 |
| Abstention Rate | 10% | 0.0 | 0.2 | 0.8+ |
| Graph Sensitivity | 10% | 0.0 | 0.0 | 1.0 |

> **Note:** These expected scores are design-time estimates, not measured values.
> Do not claim these in the submission until tests are run.

---

## How to Run the Benchmark

```
python -m pytest tests/test_benchmark.py -v --tb=short
```

Each test:
1. Loads the synthetic dataset
2. Runs the question through the agent pipeline
3. Extracts entities/facts from the response
4. Compares against ground truth
5. Computes the metric
6. Outputs pass/fail + score

The evaluation module should output a markdown table showing all results.
