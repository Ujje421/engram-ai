# Item 6 — Demo Script (~3 Minutes)

> Phase 0 design document · Engram · Graph Hacks 2026
> Track 2: Agent Memory and Coordination

---

## Pre-Demo Setup
- FalkorDB running via Docker
- Synthetic dataset loaded (32 entities, 12 facts, 69 edges)
- Frontend open in browser (React + Vite)
- Backend running (FastAPI)
- Terminal visible for showing Cypher queries (optional split screen)

---

## [0:00 – 0:15] Opening — The Problem

**Narration:**
"AI agents are getting better at answering questions, but they forget everything
between sessions. They can't trace why they made a decision. And they can't
coordinate with other agents on a shared investigation.

Engram fixes this. It gives AI agents a persistent, graph-backed memory
that remembers verified facts, traces evidence, and lets multiple agents
collaborate through shared state in FalkorDB."

**Screen:** Title slide or landing page of Engram.

---

## [0:15 – 0:50] Demo Part 1 — Investigate an Active Incident

**Narration:**
"Let's say our payment service is experiencing duplicate charges.
I'll ask the system to investigate."

**Action:** Type in chat:
> "The payment service is reporting duplicate charges. What could be causing this,
> and has anything similar happened before?"

**Screen shows:**
1. **Agent activity panel** — InvestigatorBot identifies `svc-payment-api`,
   finds `inc-005`, runs impact traversal
2. **Evidence panel** — KnowledgeBot retrieves facts from previous Session 1:
   - "Payment API timeouts caused by connection pool exhaustion" (verified, Sept 15)
   - "Connection pool max increased from 20 to 50" (verified, Sept 15)
3. **Contradictions surfaced** — Two competing hypotheses:
   - Queue retry logic (70% confidence)
   - Idempotency check (65% confidence)
4. **Graph visualization** — Shows the path: inc-005 → svc-payment-api → svc-database,
   with dependency edges highlighted

**Narration:**
"The system found the active incident, traversed dependencies to identify
impacted systems, retrieved learnings from a *previous* investigation session,
and surfaced two competing hypotheses — without silently picking one."

---

## [0:50 – 1:25] Demo Part 2 — Cross-Session Memory

**Narration:**
"Now watch what happens when I start a new session and ask about the same topic."

**Action:** Click "New Session" button. Type:
> "What did we learn about payment issues from previous investigations?"

**Screen shows:**
1. **Recalled facts** from Session 1 (fact-001, fact-002, fact-003, fact-004, fact-005)
   with timestamps, confidence scores, and verification status
2. **Evidence chain** — click on fact-001 to see:
   - Asserted by: InvestigatorBot
   - Source: logs/payment-api/2026-09-15.log, jira/PAY-1234
   - Verified by: VerifierBot
   - Superseded: fact-006 (initial wrong hypothesis about Auth Service)

**Narration:**
"Every fact has provenance — who asserted it, from what source, who verified it,
and what it replaced. This is memory you can trust and audit."

---

## [1:25 – 1:55] Demo Part 3 — Agent Coordination

**Narration:**
"Let me show the coordination between agents."

**Screen shows:** Agent activity log or timeline:
```
[InvestigatorBot] Claimed task: "Investigate duplicate charges"
[InvestigatorBot] Found: inc-005, svc-payment-api, svc-database
[InvestigatorBot] Stored hypothesis: "Queue retry may cause duplicates" (0.70)
[InvestigatorBot] → Handed off to KnowledgeBot

[KnowledgeBot] Retrieved 5 facts from previous sessions
[KnowledgeBot] Found contradiction: fact-011 vs fact-012
[KnowledgeBot] → Handed off to ResolverBot

[ResolverBot] Synthesized recommendation: "Check queue retry first"
[ResolverBot] Stored decision in graph
[ResolverBot] → Handed off to VerifierBot

[VerifierBot] Verified fact-010 (symptom confirmed by logs)
[VerifierBot] Refused to verify fact-poison (untrusted source)
```

**Narration:**
"Four agents, each with a specific role, sharing state through FalkorDB.
The verifier caught an untrusted fact from an external source and refused
to promote it. Everything is traceable."

---

## [1:55 – 2:30] Demo Part 4 — Graph Dependency Proof

**Narration:**
"The most important test: does the graph actually matter?
Let me remove a relationship and show what changes."

**Action:** Open a terminal or admin panel. Run:
```cypher
MATCH (a:Entity {id: 'svc-payment-api'})-[r:DEPENDS_ON]->(b:Entity {id: 'svc-database'})
DELETE r
```

**Action:** Re-ask the same question:
> "What systems are impacted by inc-005?"

**Screen shows:**
- **Before:** svc-payment-api, svc-database, svc-gateway, svc-cache, svc-queue
- **After:** svc-payment-api, svc-gateway, svc-cache, svc-queue (database missing)

**Narration:**
"When I removed the dependency edge between Payment API and the database,
the impact analysis changed. The database is no longer in the blast radius.
This proves FalkorDB isn't decorative — it drives the agent's reasoning."

**Action:** Restore the edge:
```cypher
MATCH (a:Entity {id: 'svc-payment-api'}), (b:Entity {id: 'svc-database'})
CREATE (a)-[:DEPENDS_ON]->(b)
```

---

## [2:30 – 2:50] Demo Part 5 — Memory Evolution Timeline

**Narration:**
"Finally, let me show how memory evolves."

**Action:** Type:
> "Show me the timeline of what we know about the Payment API"

**Screen shows:** A timeline visualization:
```
Sept 15 14:05  [hypothesis] "Auth Service slowness causing timeouts"
                    ↓ SUPERSEDED
Sept 15 14:20  [verified]   "Connection pool exhaustion is root cause"
Sept 15 15:00  [verified]   "Pool increased to 50, leak patched"
Oct 10  10:05  [hypothesis] "Queue retry causing duplicate charges"
Oct 10  10:07  [hypothesis] "Idempotency check failing"
                    ↕ CONTRADICTS
```

**Narration:**
"You can see the initial wrong hypothesis was superseded — not deleted.
The current hypotheses are flagged as contradictory. The system never
silently overwrites or forgets."

---

## [2:50 – 3:00] Closing

**Narration:**
"Engram gives AI agents memory they can trust — persistent, versioned,
evidence-backed, and graph-driven. Built on FalkorDB, which makes the
connected reasoning possible.

Track 2: Agent Memory and Coordination. Thank you."

---

## Screens Needed

| # | Screen | Components |
|---|--------|------------|
| 1 | Chat interface | Message input, response display, typing indicator |
| 2 | Agent activity panel | Agent name, action, timestamp, status badges |
| 3 | Evidence panel | Fact cards with provenance, confidence, source links |
| 4 | Graph visualization | Entity nodes, relationship edges, highlighted paths |
| 5 | Memory timeline | Chronological fact display with status, supersession arrows |
| 6 | Contradiction view | Side-by-side competing facts with confidence comparison |
| 7 | Admin/debug panel | Cypher query display, raw graph modification (for demo part 4) |

---

## Recording Tips
- Record at 1920×1080
- Use a calm, clear voiceover (record separately, overlay)
- Show the graph changing in real-time when edges are deleted
- Highlight the Cypher queries being executed (small overlay or side panel)
- Keep transitions smooth — no blank loading screens longer than 2 seconds
- Practice the full sequence 3 times before recording
