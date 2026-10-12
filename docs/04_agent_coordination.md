# Item 5 — Agent Roles and Coordination Protocol

> Phase 0 design document · Engram · Graph Hacks 2026
> Track 2: Agent Memory and Coordination

---

## Agent Architecture: Orchestrator + Specialists

```
User Question
     │
     ▼
┌──────────────────────────┐
│     OrchestratorAgent    │  (Python function, not a separate LLM call)
│                          │
│  1. Parse intent         │
│  2. Create Investigation │
│  3. Dispatch to agents   │
│  4. Merge results        │
│  5. Format response      │
└──────────┬───────────────┘
           │
     ┌─────┼─────────┬──────────────┐
     ▼     ▼         ▼              ▼
 Investigator   Knowledge    Resolver     Verifier
   Agent          Agent       Agent        Agent
```

---

## Agent Definitions

### InvestigatorBot (`agent-inv`)
**Role:** Analyze the question, identify relevant entities, run impact traversals.

**Tools available:**
- `graph_find_entity(name_or_description)` — semantic search for entities
- `graph_impact_traversal(entity_id, max_hops)` — multi-hop dependency analysis
- `graph_get_incidents(entity_id)` — find incidents affecting an entity
- `remember(fact_text, subject_entity_id, kind, confidence)` — store a new fact

**Writes to graph:** Yes (new hypothesis facts, investigation findings)
**Trust level:** Medium

---

### KnowledgeBot (`agent-know`)
**Role:** Retrieve historical context — past facts, decisions, documents, previous sessions.

**Tools available:**
- `recall(entity_id)` — get current facts about an entity
- `semantic_recall(query_text, project_id)` — vector search across facts
- `timeline(entity_id)` — fact history for an entity
- `cross_session_recall(entity_id, current_session_id)` — what was learned before
- `find_contradictions(project_id)` — surface unresolved conflicts
- `explain(fact_id)` — trace evidence chain for a fact

**Writes to graph:** No (read-only)
**Trust level:** Medium

---

### ResolverBot (`agent-res`)
**Role:** Synthesize findings into a recommendation or action plan.

**Tools available:**
- `recall(entity_id)` — read findings
- `remember(fact_text, subject_entity_id, kind='decision', confidence)` — store decisions
- `claim_task(task_id)` — claim a task
- `handoff(task_id, to_agent_id)` — hand off to another agent

**Writes to graph:** Yes (decisions, task state changes)
**Trust level:** High

---

### VerifierBot (`agent-ver`)
**Role:** Check whether hypotheses are supported by evidence. Promote or refute.

**Tools available:**
- `explain(fact_id)` — see the evidence chain
- `verify(fact_id)` — promote hypothesis to verified
- `contradict(fact_a_id, fact_b_id)` — flag conflict
- `recall(entity_id)` — check existing facts

**Writes to graph:** Yes (status changes only)
**Trust level:** High

---

## Coordination Protocol — Sequence Diagram (Text)

### Scenario: "The payment service is failing. What could be the cause?"

```
User ──message──▶ Orchestrator
                    │
                    │ 1. Create Session (sess-new)
                    │ 2. Create Investigation (inv-new) about "payment"
                    │ 3. Create Task: "investigate payment failure"
                    │
                    ├──dispatch──▶ InvestigatorBot
                    │               │
                    │               │ a. graph_find_entity("payment service")
                    │               │    → svc-payment-api
                    │               │
                    │               │ b. graph_impact_traversal(svc-payment-api, 3)
                    │               │    → svc-auth-service, svc-database, svc-cache,
                    │               │      svc-queue, svc-gateway
                    │               │
                    │               │ c. graph_get_incidents(svc-payment-api)
                    │               │    → inc-001, inc-003, inc-005
                    │               │
                    │               │ d. remember("Payment API has active incident inc-005
                    │               │              with 150 duplicate charges", 
                    │               │              svc-payment-api, "episodic", 0.85)
                    │               │
                    │               │ e. Claim task, then handoff to KnowledgeBot
                    │               │
                    │  ◀──findings──┤
                    │
                    ├──dispatch──▶ KnowledgeBot
                    │               │
                    │               │ a. cross_session_recall(svc-payment-api, sess-new)
                    │               │    → fact-001, fact-003 (from previous sessions)
                    │               │
                    │               │ b. recall(svc-database)
                    │               │    → fact-002, fact-005
                    │               │
                    │               │ c. find_contradictions(proj-alpha)
                    │               │    → fact-011 CONTRADICTS fact-012
                    │               │
                    │               │ d. explain(fact-001)
                    │               │    → Evidence: postmortem, log, verified by ResolverBot
                    │               │
                    │  ◀──context───┤
                    │
                    ├──dispatch──▶ ResolverBot
                    │               │
                    │               │ a. Synthesize: "Based on previous incidents,
                    │               │    the most likely cause is the database connection.
                    │               │    Two hypotheses exist for inc-005:
                    │               │    queue retry (70% confidence) vs
                    │               │    idempotency check (65% confidence).
                    │               │    Recommended: check queue retry logic first."
                    │               │
                    │               │ b. remember("Recommendation: investigate queue
                    │               │    retry logic for duplicate charges",
                    │               │    inc-005, "decision", 0.75)
                    │               │
                    │  ◀──recommendation──┤
                    │
                    ├──dispatch──▶ VerifierBot
                    │               │
                    │               │ a. explain(fact-010) — check if symptom is supported
                    │               │    → Source: logs/payment-api/2026-10-10.log ✓
                    │               │
                    │               │ b. verify(fact-010) — promote to verified
                    │               │
                    │  ◀──verification──┤
                    │
                    │ 4. Merge all findings
                    │ 5. Format response with evidence
                    │
Orchestrator ──response──▶ User
```

---

## Task Lifecycle

```
OPEN ──claim──▶ CLAIMED ──complete──▶ DONE
                   │
                   ├──handoff──▶ CLAIMED (by different agent)
                   │
                   └──timeout──▶ OPEN (lease expired)
```

### Claim Rules
1. Only `OPEN` tasks can be claimed
2. A task can have at most one `CLAIMED_BY` edge at a time
3. Claims have a `lease_expires` timestamp
4. If `lease_expires < now`, the task reverts to OPEN (checked by orchestrator)
5. Handoff creates a `HANDED_OFF_TO` edge (preserves history) and moves `CLAIMED_BY`

### Conflict Resolution
- If two agents try to claim simultaneously: FalkorDB's single-threaded execution
  ensures one wins, the other gets empty result
- If findings conflict: create `CONTRADICTS` edge, don't silently overwrite
- If a later fact contradicts a verified fact: create `CONTRADICTS`, notify orchestrator

---

## Implementation Note

For the hackathon, the "multi-agent" system is implemented as:
```python
class OrchestratorAgent:
    def process(self, user_message: str) -> Response:
        # 1. Create session + investigation
        # 2. Run InvestigatorBot (Python function with its own LLM call + tools)
        # 3. Run KnowledgeBot (Python function with its own LLM call + tools)  
        # 4. Run ResolverBot (Python function with its own LLM call + tools)
        # 5. Run VerifierBot (Python function with its own LLM call + tools)
        # 6. Merge and return

class InvestigatorBot:
    def run(self, context: InvestigationContext) -> Findings:
        # LLM call with tools: graph_find_entity, graph_impact_traversal, etc.
        
class KnowledgeBot:
    def run(self, context: InvestigationContext) -> KnowledgeContext:
        # LLM call with tools: recall, semantic_recall, timeline, etc.
```

Each agent is a Python class with:
- A system prompt defining its role and available tools
- A set of FalkorDB-backed tool functions
- A session context shared via the Investigation node in the graph

This is **logically** multi-agent while being a single FastAPI process.
The coordination is real (shared graph state, task handoffs, role separation).
The agents genuinely read each other's persisted findings from FalkorDB.
