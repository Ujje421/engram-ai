# Item 2 — Essential Cypher Queries

> Phase 0 design document · Engram · Graph Hacks 2026
> Track 2: Agent Memory and Coordination
>
> **Convention:** `TX_CURRENT = 9999999999` (sentinel for "still current")
> All queries use parameters prefixed with `$`. Verify each syntax marker against
> FalkorDB docs on Day 1.

---

## Query 1: Remember — Store a New Fact

**Purpose:** An agent extracts a fact from a conversation or investigation and persists it
in the graph with full provenance.

**Parameters:** `$fact_id, $project_id, $kind, $predicate, $text, $confidence, $embedding,
$valid_from, $now, $source_id, $session_id, $subject_entity_id, $object_entity_id (optional)`

```cypher
// Create the fact node
CREATE (f:Fact {
  id: $fact_id,
  project_id: $project_id,
  kind: $kind,
  predicate: $predicate,
  text: $text,
  status: 'hypothesis',
  confidence: $confidence,
  version: 1,
  valid_from: $valid_from,
  valid_to: 9999999999,
  tx_from: $now,
  tx_to: 9999999999
})

// Link to subject entity
WITH f
MATCH (subj:Entity {id: $subject_entity_id})
CREATE (f)-[:SUBJECT]->(subj)

// Link to source
WITH f
MATCH (src:Source {id: $source_id})
CREATE (f)-[:DERIVED_FROM]->(src)

// Link to session
WITH f
MATCH (sess:Session {id: $session_id})
CREATE (f)-[:ASSERTED_IN]->(sess)

RETURN f.id AS fact_id, f.status AS status
```

> **⚠ Verify:** Multi-statement WITH chaining. If FalkorDB doesn't support this pattern,
> split into separate queries within a single Python function.

---

## Query 2: Recall — Retrieve Current Facts About an Entity

**Purpose:** Given an entity, retrieve all current verified facts about it, with source provenance.

**Parameters:** `$entity_id, $project_id`

```cypher
MATCH (f:Fact)-[:SUBJECT]->(e:Entity {id: $entity_id, project_id: $project_id})
WHERE f.status = 'verified' AND f.tx_to = 9999999999
OPTIONAL MATCH (f)-[:DERIVED_FROM]->(src:Source)
RETURN f.id AS fact_id,
       f.predicate AS predicate,
       f.text AS text,
       f.confidence AS confidence,
       f.valid_from AS valid_from,
       collect(src.uri) AS sources
ORDER BY f.valid_from DESC
LIMIT 50
```

> **⚠ Verify:** `OPTIONAL MATCH` support. If unsupported, split into two queries.

---

## Query 3: Semantic Recall — Find Facts by Meaning

**Purpose:** Use vector similarity to find facts semantically related to a query, scoped to a project.

**Parameters:** `$query_embedding (float array), $project_id, $k (int)`

```cypher
CALL db.idx.vector.queryNodes('Fact', 'embedding', $k, vecf32($query_embedding))
YIELD node AS f, score
WHERE f.project_id = $project_id AND f.status IN ['hypothesis', 'verified'] AND f.tx_to = 9999999999
MATCH (f)-[:SUBJECT]->(e:Entity)
OPTIONAL MATCH (f)-[:DERIVED_FROM]->(src:Source)
RETURN f.id AS fact_id,
       f.text AS text,
       f.predicate AS predicate,
       e.name AS entity_name,
       e.type AS entity_type,
       score,
       collect(src.uri) AS sources
ORDER BY score DESC
```

> **⚠ Verify:** `WHERE` after `YIELD`, `IN` list syntax, `vecf32()` parameter passing.

---

## Query 4: Explain — Trace the Evidence Chain for a Fact

**Purpose:** Given a fact, show why the system believes it: the source, the session, the agent,
and any supersession history.

**Parameters:** `$fact_id`

```cypher
MATCH (f:Fact {id: $fact_id})
MATCH (f)-[:SUBJECT]->(subj:Entity)
MATCH (f)-[:ASSERTED_IN]->(sess:Session)-[:RUN_BY]->(agent:Agent)
OPTIONAL MATCH (f)-[:DERIVED_FROM]->(src:Source)
OPTIONAL MATCH (f)-[:VERIFIED_BY]->(verifier:Agent)
OPTIONAL MATCH (f)-[:SUPERSEDES]->(old:Fact)
RETURN f.id AS fact_id,
       f.text AS text,
       f.status AS status,
       f.confidence AS confidence,
       f.valid_from AS valid_from,
       f.tx_from AS asserted_at,
       subj.name AS subject_name,
       subj.type AS subject_type,
       agent.name AS asserted_by,
       agent.role AS agent_role,
       verifier.name AS verified_by,
       collect(src.uri) AS sources,
       old.id AS superseded_fact_id,
       old.text AS superseded_text
```

---

## Query 5: Supersede — Update a Fact with New Evidence

**Purpose:** When new information replaces old, mark the old fact as superseded and create
the new one with a SUPERSEDES edge. This is the core of memory evolution.

**Parameters:** `$old_fact_id, $new_fact_id, $new_text, $new_confidence, $new_embedding,
$now, $source_id, $session_id, $project_id, $predicate, $kind`

```cypher
// Step 1: Close the old fact
MATCH (old:Fact {id: $old_fact_id})
WHERE old.tx_to = 9999999999
SET old.tx_to = $now, old.status = 'superseded'

// Step 2: Create the new fact
WITH old
CREATE (new:Fact {
  id: $new_fact_id,
  project_id: $project_id,
  kind: $kind,
  predicate: $predicate,
  text: $new_text,
  status: 'hypothesis',
  confidence: $new_confidence,
  version: old.version + 1,
  valid_from: $now,
  valid_to: 9999999999,
  tx_from: $now,
  tx_to: 9999999999
})
CREATE (new)-[:SUPERSEDES]->(old)

// Step 3: Copy the SUBJECT edge
WITH new, old
MATCH (old)-[:SUBJECT]->(e:Entity)
CREATE (new)-[:SUBJECT]->(e)

// Step 4: Link provenance
WITH new
MATCH (src:Source {id: $source_id})
CREATE (new)-[:DERIVED_FROM]->(src)

WITH new
MATCH (sess:Session {id: $session_id})
CREATE (new)-[:ASSERTED_IN]->(sess)

RETURN new.id AS new_fact_id, new.version AS version
```

> **⚠ Verify:** `old.version + 1` arithmetic in CREATE. If not supported, compute in Python.

---

## Query 6: Contradict — Flag Conflicting Facts

**Purpose:** When the system discovers two facts with the same subject and predicate that
disagree, create a CONTRADICTS edge instead of silently choosing one.

**Parameters:** `$fact_a_id, $fact_b_id`

```cypher
MATCH (a:Fact {id: $fact_a_id}), (b:Fact {id: $fact_b_id})
WHERE a.tx_to = 9999999999 AND b.tx_to = 9999999999
CREATE (a)-[:CONTRADICTS]->(b)
RETURN a.id AS fact_a, b.id AS fact_b, a.text AS text_a, b.text AS text_b
```

---

## Query 7: Claim Task — Agent Coordination

**Purpose:** An agent claims an unclaimed task. If the task is already claimed, the query
returns nothing (failed claim). This is the coordination primitive.

**Parameters:** `$task_id, $agent_id, $expires`

```cypher
MATCH (t:Task {id: $task_id, state: 'open'})
MATCH (a:Agent {id: $agent_id})
WHERE NOT EXISTS { MATCH (t)-[:CLAIMED_BY]->() }
SET t.state = 'claimed', t.lease_expires = $expires
CREATE (t)-[:CLAIMED_BY]->(a)
RETURN t.id AS task_id, t.state AS state, a.name AS claimed_by
```

> **⚠ Verify:** `NOT EXISTS { MATCH ... }` subquery syntax. Alternative:
> ```cypher
> OPTIONAL MATCH (t)-[:CLAIMED_BY]->(existing:Agent)
> WITH t, a, existing WHERE existing IS NULL
> ```
> If both fail, check in Python before running the SET.

---

## Query 8: Handoff — Transfer Task Between Agents

**Purpose:** One agent hands a task to another, with the handoff recorded in the graph.
This is the key demo moment for Track 2 coordination.

**Parameters:** `$task_id, $from_agent_id, $to_agent_id, $new_expires`

```cypher
MATCH (t:Task {id: $task_id, state: 'claimed'})-[:CLAIMED_BY]->(from:Agent {id: $from_agent_id})
MATCH (to:Agent {id: $to_agent_id})
DELETE (t)-[:CLAIMED_BY]->(from)
CREATE (t)-[:HANDED_OFF_TO]->(from)
CREATE (t)-[:CLAIMED_BY]->(to)
SET t.lease_expires = $new_expires
RETURN t.id AS task_id, from.name AS handed_from, to.name AS handed_to
```

> **⚠ Verify:** `DELETE` on a specific relationship pattern. Alternative: use `MATCH` to find
> the edge, then `DELETE` it by variable name.

---

## Query 9: Timeline — Fact History for an Entity

**Purpose:** Show how knowledge about an entity has evolved over time. This is the
"memory evolution" demo — judges see facts being created, verified, superseded, and refuted.

**Parameters:** `$entity_id, $project_id`

```cypher
MATCH (f:Fact)-[:SUBJECT]->(e:Entity {id: $entity_id, project_id: $project_id})
MATCH (f)-[:ASSERTED_IN]->(sess:Session)-[:RUN_BY]->(agent:Agent)
OPTIONAL MATCH (f)-[:SUPERSEDES]->(old:Fact)
OPTIONAL MATCH (newer:Fact)-[:SUPERSEDES]->(f)
RETURN f.id AS fact_id,
       f.text AS text,
       f.status AS status,
       f.confidence AS confidence,
       f.tx_from AS created_at,
       f.tx_to AS retired_at,
       agent.name AS asserted_by,
       old.id AS superseded_fact,
       newer.id AS superseded_by
ORDER BY f.tx_from ASC
```

---

## Query 10: Impact Traversal — Multi-Hop Dependency Analysis

**Purpose:** Given an incident entity, traverse DEPENDS_ON and AFFECTS relationships
to find all impacted systems within N hops. This shows graph-driven reasoning.

**Parameters:** `$incident_entity_id, $max_hops (default 3)`

```cypher
MATCH (incident:Entity {id: $incident_entity_id, type: 'incident'})
MATCH path = (incident)-[:AFFECTS|DEPENDS_ON*1..3]->(impacted:Entity)
WHERE impacted.type IN ['service', 'component', 'api']
RETURN DISTINCT impacted.id AS entity_id,
       impacted.name AS name,
       impacted.type AS type,
       length(path) AS hops
ORDER BY hops ASC
```

> **⚠ Verify:** Variable-length relationship `*1..3` and multi-type `[:AFFECTS|DEPENDS_ON]`.
> If unsupported, write three fixed-depth queries and union in Python.

---

## Query 11: Cross-Session Recall — The "Killer Demo" Query

**Purpose:** "What did we conclude about X last time?" — retrieves facts from previous
sessions about the same entity, proving persistent memory across sessions.

**Parameters:** `$entity_id, $current_session_id, $project_id`

```cypher
MATCH (f:Fact)-[:SUBJECT]->(e:Entity {id: $entity_id, project_id: $project_id})
MATCH (f)-[:ASSERTED_IN]->(sess:Session)
WHERE sess.id <> $current_session_id
  AND f.status IN ['verified', 'hypothesis']
  AND f.tx_to = 9999999999
MATCH (sess)-[:RUN_BY]->(agent:Agent)
OPTIONAL MATCH (f)-[:DERIVED_FROM]->(src:Source)
RETURN f.id AS fact_id,
       f.text AS text,
       f.status AS status,
       f.confidence AS confidence,
       f.kind AS kind,
       sess.started_at AS session_date,
       agent.name AS agent_name,
       collect(src.uri) AS sources
ORDER BY sess.started_at DESC
LIMIT 20
```

---

## Query 12: Verify Fact — Promote Hypothesis to Verified

**Purpose:** A verifier agent confirms a hypothesis with supporting evidence. Critical for
the "trustworthy memory" narrative.

**Parameters:** `$fact_id, $verifier_agent_id`

```cypher
MATCH (f:Fact {id: $fact_id, status: 'hypothesis'})
MATCH (f)-[:ASSERTED_IN]->(sess:Session)-[:RUN_BY]->(author:Agent)
WHERE author.id <> $verifier_agent_id
MATCH (verifier:Agent {id: $verifier_agent_id})
SET f.status = 'verified'
CREATE (f)-[:VERIFIED_BY]->(verifier)
RETURN f.id AS fact_id, f.status AS status, verifier.name AS verified_by
```

---

## Query 13: Find Contradictions — Surface Unresolved Conflicts

**Purpose:** Show the judges that the system doesn't silently overwrite — it flags conflicts.

**Parameters:** `$project_id`

```cypher
MATCH (a:Fact)-[:CONTRADICTS]->(b:Fact)
WHERE a.project_id = $project_id
  AND a.tx_to = 9999999999
  AND b.tx_to = 9999999999
MATCH (a)-[:SUBJECT]->(e:Entity)
RETURN a.id AS fact_a_id,
       a.text AS fact_a_text,
       b.id AS fact_b_id,
       b.text AS fact_b_text,
       e.name AS entity_name,
       a.confidence AS confidence_a,
       b.confidence AS confidence_b
```

---

## Query 14: Project Isolation Check — Security Invariant

**Purpose:** Verify that facts from one project cannot leak into another. Used in the
evaluation suite.

**Parameters:** `$project_id`

```cypher
MATCH (f:Fact {project_id: $project_id})-[:SUBJECT]->(e:Entity)
WHERE e.project_id <> $project_id
RETURN f.id AS leaked_fact, e.id AS wrong_entity, e.project_id AS actual_project
```

Expected result: **zero rows** if isolation holds.

---

## Query 15: Investigation Summary — Group Findings

**Purpose:** For a given investigation, retrieve all discovered facts, the entities involved,
and the actions taken. This is the demo's "evidence panel."

**Parameters:** `$investigation_id`

```cypher
MATCH (inv:Investigation {id: $investigation_id})
MATCH (inv)-[:ABOUT]->(target:Entity)
OPTIONAL MATCH (inv)-[:FOUND]->(f:Fact)-[:SUBJECT]->(e:Entity)
OPTIONAL MATCH (f)-[:DERIVED_FROM]->(src:Source)
RETURN inv.title AS investigation,
       inv.status AS status,
       target.name AS target_entity,
       collect(DISTINCT {
         fact_id: f.id,
         text: f.text,
         status: f.status,
         confidence: f.confidence,
         entity: e.name,
         sources: collect(src.uri)
       }) AS findings
```

> **⚠ Verify:** Nested `collect()` inside map literal. If unsupported, split into two queries.

---

## Syntax Items to Verify on Day 1 (Checklist)

| # | Feature | Query | Fallback |
|---|---------|-------|----------|
| 1 | `IS NULL` predicate | Q2, Q3, Q5 | Sentinel value (already planned) |
| 2 | `OPTIONAL MATCH` | Q2, Q4, Q9, Q15 | Split into separate queries |
| 3 | Variable-length paths `*1..N` | Q10 | Fixed-depth queries |
| 4 | Multi-type relationships `[:A\|B]` | Q10 | Separate queries per type |
| 5 | `NOT EXISTS { MATCH ... }` | Q7 | OPTIONAL MATCH + WHERE IS NULL |
| 6 | `DELETE` specific relationship | Q8 | MATCH edge, DELETE variable |
| 7 | Map literal in RETURN | Q15 | Return flat columns |
| 8 | `IN` list in WHERE | Q3, Q10, Q11 | Multiple OR conditions |
| 9 | Arithmetic in CREATE | Q5 | Compute in Python |
| 10 | `collect()` with DISTINCT | Q15 | Post-process in Python |
| 11 | `ORDER BY` after OPTIONAL MATCH | Q2, Q9 | Move ORDER BY to final RETURN |
| 12 | `vecf32()` parameter passing | Q3 | Test with hardcoded vector |
