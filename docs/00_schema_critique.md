# Item 1 — Schema Critique

> Phase 0 design document · Engram · Graph Hacks 2026
> Track 2: Agent Memory and Coordination

---

## 1. FalkorDB-Specific Constraints That Break the Current Design

### 1.1 No `IS NULL` in WHERE (Verify Day 1)
The schema relies on `f.tx_to IS NULL` to find current facts. FalkorDB's openCypher subset
**may not support `IS NULL`** predicates. If it doesn't:

**Fix:** Use a sentinel value instead.
```
tx_to = 9999999999  (or 0, or -1)
```
All queries change from `WHERE f.tx_to IS NULL` to `WHERE f.tx_to = 9999999999`.
This must be the **first thing tested** on Oct 15 when FalkorDB is running.

### 1.2 No Native Schema Enforcement via Cypher DDL
FalkorDB constraints use the Redis-level command `GRAPH.CONSTRAINT CREATE`, not Cypher DDL.
- `UNIQUE` constraints require a range index to already exist on the property.
- `MANDATORY` constraints exist but are also Redis-level commands.
- Constraints are enforced **asynchronously** — they return `PENDING` and enforce gradually.

**Impact:** You cannot rely on `CREATE CONSTRAINT ... IS UNIQUE` in Cypher migration scripts.
All schema enforcement must be done via Redis commands or the `falkordb-py` client's
lower-level `execute_command` method.

### 1.3 No `CASE WHEN` in All Positions (Verify)
Some openCypher `CASE` expressions may not work in all clauses.
Any query using `CASE` in `SET` or `RETURN` needs testing.

### 1.4 Array Properties Are Supported — But No Array Indexing
`Entity.aliases[]` is fine as a stored property, but you **cannot create an index** on it
or use it efficiently in `WHERE e.aliases CONTAINS $x` unless you do a full scan.

**Fix:** For lookup by alias, create a separate `(:Alias {name})-[:ALIAS_OF]->(:Entity)` pattern,
or accept full scan on alias lookups (acceptable at hackathon scale).

### 1.5 Vector Indexes Work — But With Specific Syntax
```cypher
CREATE VECTOR INDEX FOR (f:Fact) ON (f.embedding)
OPTIONS {dimension: 1536, similarityFunction: 'cosine'}
```
Query:
```cypher
CALL db.idx.vector.queryNodes('Fact', 'embedding', 5, vecf32($query_vec))
YIELD node, score
```
This is confirmed working. Embeddings must be stored as float arrays, and the query vector
must use `vecf32()` cast.

### 1.6 Full-Text Index — Procedure-Based
```cypher
CALL db.idx.fulltext.createNodeIndex('Fact', 'text')
```
Query:
```cypher
CALL db.idx.fulltext.queryNodes('Fact', 'search term')
YIELD node, score
```
This works. No additional plugins needed.

---

## 2. Structural Weaknesses in the Schema

### 2.1 The Fact Node Is Overloaded
The `Fact` node carries: kind, predicate, text, status, confidence, version, embedding,
valid_from, valid_to, tx_from, tx_to. That's 11+ properties.

**Risk:** Every query that touches Facts pulls all these properties through the query engine.

**Keep it.** At hackathon scale (hundreds to low thousands of nodes), this is fine.
In production you'd split Fact from FactMeta, but splitting now doubles your query complexity
for zero demo benefit.

### 2.2 Missing: Conversation / Message Tracking
The schema has `Session` but no conversation history. For Track 2 (Memory & Coordination),
judges want to see:
- What the user asked
- What the agent decided
- What was remembered
- What was recalled later

**Fix:** Add a `Message` node:
```
Message {id, session_id, role: user|agent|system, content, timestamp, tool_calls_json}
```
Edges:
```
(Message)-[:IN_SESSION]->(Session)
(Message)-[:PRODUCED]->(Fact)       -- agent extracted this fact from this message
(Message)-[:RECALLED]->(Fact)       -- agent used this fact to answer this message
```
This gives you an **audit trail** that directly maps to the Explainability criterion.

### 2.3 Missing: AgentAction / ToolCall Node
For multi-agent coordination, judges want to see agents **doing things**, not just
producing text. The schema needs to capture what tools were called and what happened.

**Fix:** Add an `Action` node:
```
Action {id, agent_id, session_id, tool_name, parameters_json, result_json, 
        status: success|failed|pending, timestamp}
```
Edges:
```
(Action)-[:PERFORMED_BY]->(Agent)
(Action)-[:IN_SESSION]->(Session)
(Action)-[:PRODUCED]->(Fact)
(Action)-[:TARGETED]->(Entity)
```

### 2.4 The `Tenant` Node Adds Complexity Without Demo Value
For a solo-developer hackathon project with synthetic data, multi-tenancy is overhead.
Every query needs `WHERE e.tenant_id = $tenant_id`, every relationship needs tenant guards.

**Decision:** Keep `tenant_id` as a property on `Entity` and `Fact` for future-proofing,
but don't build tenant isolation into the demo. The "isolation" test can instead demonstrate
**project-level** isolation (which is simpler and still scores on the Isolation criterion).

**Drop** the `Tenant` node. Keep `project_id` as the isolation boundary.

### 2.5 The `Source` Node Content Hash Is Smart — Keep It
Content-addressed provenance means the same document ingested twice produces the same
Source node. This prevents duplicate evidence chains. Good design.

### 2.6 Missing: Explicit `Investigation` Node
The demo scenario is "investigate an incident." Without an Investigation node, there's no
way to group related facts, messages, and actions into a coherent investigation thread.

**Fix:** Add:
```
Investigation {id, project_id, title, status: open|resolved|stale, created_at, resolved_at}
```
Edges:
```
(Investigation)-[:ABOUT]->(Entity)     -- the incident or system being investigated
(Investigation)-[:IN_SESSION]->(Session)
(Investigation)-[:FOUND]->(Fact)       -- facts discovered during this investigation
(Investigation)-[:DECIDED]->(Decision) -- renamed from generic Fact
```

### 2.7 `Task` Node Optimistic Concurrency — Simplify
The `version` field for optimistic locking on tasks is a good pattern, but FalkorDB
doesn't have `CASE WHEN ... THEN SET` transactional guarantees in a single query.

**Fix:** Use a simpler claim pattern:
```cypher
MATCH (t:Task {id: $task_id, state: 'open'})
WHERE NOT EXISTS((t)-[:CLAIMED_BY]->())
SET t.state = 'claimed', t.lease_expires = $expires
CREATE (t)-[:CLAIMED_BY]->(a:Agent {id: $agent_id})
RETURN t
```
If the query returns 0 rows, the claim failed. This is simpler and works within
FalkorDB's single-query atomicity.

> **Note:** Verify that FalkorDB provides query-level atomicity (each `GRAPH.QUERY` is
> atomic). This is expected since it runs on Redis, which is single-threaded.

---

## 3. Status Machine — Issues and Fixes

### 3.1 The Status Transitions Are Sound
```
quarantined -> hypothesis -> verified -> superseded
hypothesis | verified -> refuted
```
This is good. It prevents unverified claims from being treated as facts.

### 3.2 But the "Author Cannot Verify Own Fact" Rule Needs an Agent Architecture Decision
With a solo developer, you may only have 2-3 agents. If the Investigation Agent produces
a fact and the only other agent is the Knowledge Agent, can the Knowledge Agent verify it?

**Decision:** Yes, as long as the verifier has a different `role` than the asserter.
The rule should be: `fact.asserted_by_agent_id != verifier_agent_id`. Not role-based, ID-based.

### 3.3 `quarantined` Is Extra Ceremony for a Hackathon
Every new fact going through quarantine adds a step that the demo has to explain.

**Simplify for demo:** New facts from the LLM start as `hypothesis`. Facts extracted from
a Source (document, log, ticket) start as `verified` if the source is trusted.
Drop `quarantined` from the demo. Mention it in the README as a production enhancement.

**Revised status machine:**
```
hypothesis -> verified -> superseded
hypothesis | verified -> refuted
```

---

## 4. Invariants — Revised

| # | Invariant | Test Method |
|---|-----------|-------------|
| 1 | Every `Fact` has at least one `SUBJECT` edge | Cypher assertion query |
| 2 | Every `Fact` has at least one `ASSERTED_IN` edge | Cypher assertion query |
| 3 | Every `Fact` has at least one `DERIVED_FROM` edge | Cypher assertion query |
| 4 | No cross-project Entity references (except explicit sharing) | Query for edges crossing project_id boundaries |
| 5 | At most one current `verified` Fact per (subject_entity_id, predicate) | Aggregation query with HAVING count > 1 |
| 6 | The asserting agent is not the verifying agent | Check `ASSERTED_IN->Session->RUN_BY` vs `VERIFIED_BY` |
| 7 | A Task has at most one active `CLAIMED_BY` edge | Count query |
| 8 | All `Fact` nodes with `tx_to = 9999999999` are "current" | Convention, not a constraint |

---

## 5. Index Strategy (Verified Against FalkorDB Capabilities)

### Range Indexes (for exact-match and property lookups)
```cypher
CREATE INDEX FOR (e:Entity) ON (e.id)
CREATE INDEX FOR (e:Entity) ON (e.project_id)
CREATE INDEX FOR (f:Fact) ON (f.id)
CREATE INDEX FOR (f:Fact) ON (f.status)
CREATE INDEX FOR (f:Fact) ON (f.project_id)
CREATE INDEX FOR (s:Session) ON (s.id)
CREATE INDEX FOR (a:Agent) ON (a.id)
CREATE INDEX FOR (t:Task) ON (t.id)
CREATE INDEX FOR (t:Task) ON (t.state)
CREATE INDEX FOR (src:Source) ON (src.id)
CREATE INDEX FOR (inv:Investigation) ON (inv.id)
CREATE INDEX FOR (m:Message) ON (m.id)
CREATE INDEX FOR (act:Action) ON (act.id)
```

### Vector Indexes
```cypher
CREATE VECTOR INDEX FOR (f:Fact) ON (f.embedding)
OPTIONS {dimension: 1536, similarityFunction: 'cosine'}

CREATE VECTOR INDEX FOR (e:Entity) ON (e.embedding)
OPTIONS {dimension: 1536, similarityFunction: 'cosine'}
```

### Full-Text Indexes
```cypher
CALL db.idx.fulltext.createNodeIndex('Fact', 'text')
CALL db.idx.fulltext.createNodeIndex('Entity', 'name')
```

---

## 6. Revised Node Summary

| Node | Key Properties | New/Changed? |
|------|---------------|-------------|
| **Entity** | id, project_id, type, name, aliases[], embedding | Dropped tenant_id, kept project_id |
| **Fact** | id, project_id, kind, predicate, text, status, confidence, version, embedding, valid_from, valid_to, tx_from, tx_to | tx_to uses sentinel 9999999999 |
| **Session** | id, agent_id, project_id, started_at, ended_at | Unchanged |
| **Agent** | id, name, role, trust_level | Unchanged |
| **Source** | id, type, uri, content_hash | Unchanged |
| **Task** | id, title, state, lease_expires | Simplified — removed version |
| **Message** | id, session_id, role, content, timestamp, tool_calls_json | **NEW** |
| **Action** | id, agent_id, session_id, tool_name, parameters_json, result_json, status, timestamp | **NEW** |
| **Investigation** | id, project_id, title, status, created_at, resolved_at | **NEW** |

Dropped: `Tenant`, `Decision` (folded into `Fact` with `kind = 'decision'`)

---

## 7. Edge Summary (Revised)

| Edge | From -> To | Purpose |
|------|-----------|---------|
| SUBJECT | Fact -> Entity | What the fact is about |
| OBJECT | Fact -> Entity | Second entity in the predicate |
| DERIVED_FROM | Fact -> Source | Provenance |
| ASSERTED_IN | Fact -> Session | When/who wrote it |
| SUPERSEDES | Fact -> Fact | New replaces old |
| CONTRADICTS | Fact -> Fact | Unresolved conflict |
| VERIFIED_BY | Fact -> Agent | Who confirmed it |
| IN_PROJECT | Entity -> Project | Namespace boundary |
| DEPENDS_ON | Entity -> Entity | Structural dependency |
| OWNS | Entity -> Entity | Ownership |
| AFFECTS | Entity -> Entity | Impact relationship |
| RESOLVED_BY | Entity -> Entity | Who fixed what |
| RUN_BY | Session -> Agent | Agent that ran the session |
| CLAIMED_BY | Task -> Agent | Task ownership |
| HANDED_OFF_TO | Task -> Agent | Coordination handoff |
| ABOUT | Task/Investigation -> Entity | What it concerns |
| IN_SESSION | Message/Action -> Session | Session membership |
| PRODUCED | Message/Action -> Fact | What was extracted |
| RECALLED | Message -> Fact | What was used to answer |
| PERFORMED_BY | Action -> Agent | Who did it |
| TARGETED | Action -> Entity | What was acted on |
| FOUND | Investigation -> Fact | Discovery during investigation |

---

## 8. Risk: What Could Go Wrong on Day 1

| Risk | Impact | Mitigation |
|------|--------|-----------|
| `IS NULL` not supported | All "current fact" queries break | Test first, use sentinel value |
| Variable-length path `*1..5` not supported | Supersession chain query fails | Test, fall back to fixed-depth MATCH |
| Vector index creation fails | No semantic search | Fall back to full-text only |
| `MERGE` with ON CREATE / ON MATCH not supported | Upsert logic breaks | Test, use conditional MATCH + CREATE |
| Query plan doesn't use indexes | Performance issues | Use `GRAPH.EXPLAIN` to verify index hits |
| `OPTIONAL MATCH` not supported | Evidence queries break | Test; restructure as two separate queries |

> **Action:** Create a `verify_falkordb_features.py` script as the **very first task** on Oct 15.
> It runs each query pattern against a minimal test graph and reports what works.

---

## 9. Summary of Changes to the Baseline Schema

1. **Dropped** `Tenant` node — use `project_id` for isolation
2. **Dropped** `Decision` node — folded into `Fact` with `kind = 'decision'`
3. **Dropped** `quarantined` status — start at `hypothesis` or `verified`
4. **Dropped** Task `version` field — use query-level atomicity for claims
5. **Added** `Message` node — audit trail for conversations
6. **Added** `Action` node — tool calls and their results
7. **Added** `Investigation` node — groups findings into coherent threads
8. **Changed** `tx_to` from nullable to sentinel value `9999999999`
9. **Changed** constraint creation from Cypher DDL to Redis-level commands
10. **Changed** author-cannot-verify rule from role-based to agent-ID-based
