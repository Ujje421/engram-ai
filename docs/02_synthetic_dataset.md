# Item 3 — Synthetic Dataset Specification

> Phase 0 design document · Engram · Graph Hacks 2026
> Track 2: Agent Memory and Coordination

---

## Design Principles

1. **Small enough to reason about manually** — every expected query result can be verified by hand
2. **Rich enough to demonstrate all capabilities** — multi-hop, temporal, contradictions, handoffs
3. **Contains planted traps** — stale facts, cross-project leaks, contradictions, poisoning attempts
4. **Tells a coherent story** — a payment platform with real-ish incident history

---

## Projects (3)

| Project ID | Name | Description |
|-----------|------|-------------|
| `proj-alpha` | **PayFlow** | Payment processing platform |
| `proj-beta` | **ShieldGuard** | Fraud detection system |
| `proj-gamma` | **DataVault** | Data analytics pipeline (minimal — exists for isolation tests) |

---

## Agents (4)

| Agent ID | Name | Role | Trust Level |
|----------|------|------|-------------|
| `agent-inv` | **InvestigatorBot** | investigator | medium |
| `agent-know` | **KnowledgeBot** | knowledge_retriever | medium |
| `agent-res` | **ResolverBot** | resolver | high |
| `agent-ver` | **VerifierBot** | verifier | high |

---

## Entities — PayFlow (proj-alpha)

### People (6)
| Entity ID | Type | Name |
|-----------|------|------|
| `person-arun` | person | Arun Mehta |
| `person-priya` | person | Priya Sharma |
| `person-vikram` | person | Vikram Patel |
| `person-neha` | person | Neha Gupta |
| `person-rohan` | person | Rohan Kumar |
| `person-sara` | person | Sara Chen |

### Services/Components (7)
| Entity ID | Type | Name |
|-----------|------|------|
| `svc-payment-api` | service | Payment API |
| `svc-auth-service` | service | Auth Service |
| `svc-notification` | service | Notification Service |
| `svc-gateway` | component | API Gateway |
| `svc-queue` | component | Message Queue |
| `svc-cache` | component | Redis Cache |
| `svc-database` | component | PostgreSQL Primary |

### Incidents (5)
| Entity ID | Type | Name | Timestamp |
|-----------|------|------|-----------|
| `inc-001` | incident | Payment timeout spike | 2026-09-15 |
| `inc-002` | incident | Auth token refresh failure | 2026-09-22 |
| `inc-003` | incident | Gateway 502 errors | 2026-10-01 |
| `inc-004` | incident | Queue message backlog | 2026-10-05 |
| `inc-005` | incident | Payment duplicate charges | 2026-10-10 |

### Documents (4)
| Entity ID | Type | Name | URI |
|-----------|------|------|-----|
| `doc-runbook-payment` | document | Payment API Runbook | docs/runbook-payment.md |
| `doc-postmortem-001` | document | Inc-001 Postmortem | docs/postmortem-001.md |
| `doc-arch-auth` | document | Auth Service Architecture | docs/arch-auth.md |
| `doc-sla-payment` | document | Payment SLA Agreement | docs/sla-payment.md |

---

## Entities — ShieldGuard (proj-beta)

### People (2)
| Entity ID | Type | Name |
|-----------|------|------|
| `person-amit` | person | Amit Desai |
| `person-lisa` | person | Lisa Wang |

### Services (3)
| Entity ID | Type | Name |
|-----------|------|------|
| `svc-fraud-engine` | service | Fraud Engine |
| `svc-risk-scorer` | service | Risk Scorer |
| `svc-fraud-alerts` | service | Fraud Alerts |

### Incidents (2)
| Entity ID | Type | Name |
|-----------|------|------|
| `inc-beta-001` | incident | False positive spike | 2026-09-28 |
| `inc-beta-002` | incident | Risk scorer latency | 2026-10-08 |

---

## Entities — DataVault (proj-gamma) — Minimal, for isolation tests

| Entity ID | Type | Name |
|-----------|------|------|
| `person-secret` | person | Classified User |
| `svc-etl` | service | ETL Pipeline |
| `doc-secret` | document | Classified Report |

---

## Structural Relationships (Edges Between Entities)

### PayFlow Dependencies
```
(svc-payment-api)-[:DEPENDS_ON]->(svc-auth-service)
(svc-payment-api)-[:DEPENDS_ON]->(svc-database)
(svc-payment-api)-[:DEPENDS_ON]->(svc-cache)
(svc-payment-api)-[:DEPENDS_ON]->(svc-queue)
(svc-notification)-[:DEPENDS_ON]->(svc-queue)
(svc-gateway)-[:DEPENDS_ON]->(svc-payment-api)
(svc-gateway)-[:DEPENDS_ON]->(svc-auth-service)
```

### Ownership
```
(person-arun)-[:OWNS]->(svc-payment-api)
(person-priya)-[:OWNS]->(svc-auth-service)
(person-vikram)-[:OWNS]->(svc-notification)
(person-neha)-[:OWNS]->(svc-gateway)
(person-rohan)-[:OWNS]->(svc-queue)
(person-sara)-[:OWNS]->(svc-cache)
```

### Incidents → Systems
```
(inc-001)-[:AFFECTS]->(svc-payment-api)
(inc-002)-[:AFFECTS]->(svc-auth-service)
(inc-003)-[:AFFECTS]->(svc-gateway)
(inc-003)-[:AFFECTS]->(svc-payment-api)     // cascade
(inc-004)-[:AFFECTS]->(svc-queue)
(inc-004)-[:AFFECTS]->(svc-notification)     // cascade
(inc-005)-[:AFFECTS]->(svc-payment-api)
(inc-005)-[:AFFECTS]->(svc-database)         // root cause
```

### Resolution History
```
(inc-001)-[:RESOLVED_BY]->(person-arun)
(inc-002)-[:RESOLVED_BY]->(person-priya)
(inc-003)-[:RESOLVED_BY]->(person-neha)
(inc-004)-[:RESOLVED_BY]->(person-rohan)
// inc-005 is UNRESOLVED — no RESOLVED_BY edge
```

### ShieldGuard Dependencies
```
(svc-fraud-engine)-[:DEPENDS_ON]->(svc-risk-scorer)
(svc-fraud-alerts)-[:DEPENDS_ON]->(svc-fraud-engine)
// Cross-project dependency (legitimate):
(svc-fraud-engine)-[:DEPENDS_ON]->(svc-payment-api)
```

---

## Sources (7)

| Source ID | Type | URI | Content Hash |
|-----------|------|-----|-------------|
| `src-log-001` | log | logs/payment-api/2026-09-15.log | hash_a1 |
| `src-ticket-001` | ticket | jira/PAY-1234 | hash_b1 |
| `src-doc-runbook` | doc | docs/runbook-payment.md | hash_c1 |
| `src-doc-postmortem` | doc | docs/postmortem-001.md | hash_d1 |
| `src-agent-output` | agent_output | agent://investigator/session-1 | hash_e1 |
| `src-log-005` | log | logs/payment-api/2026-10-10.log | hash_f1 |
| `src-poisoned` | ticket | external://untrusted-feed/claim-42 | hash_poison |

---

## Sessions (5)

| Session ID | Agent | Project | Started At | Ended At |
|-----------|-------|---------|-----------|----------|
| `sess-1` | agent-inv | proj-alpha | 2026-09-15 14:00 | 2026-09-15 14:30 |
| `sess-2` | agent-know | proj-alpha | 2026-09-15 14:15 | 2026-09-15 14:45 |
| `sess-3` | agent-res | proj-alpha | 2026-09-15 15:00 | 2026-09-15 15:20 |
| `sess-4` | agent-inv | proj-alpha | 2026-10-10 10:00 | (open) |
| `sess-5` | agent-inv | proj-beta | 2026-10-08 09:00 | 2026-10-08 09:30 |

---

## Facts — The Core Memory

### Session 1: Investigating inc-001 (Payment Timeout Spike)

| Fact ID | Kind | Predicate | Text | Status | Confidence | Subject | Session |
|---------|------|-----------|------|--------|-----------|---------|---------|
| `fact-001` | episodic | caused_by | Payment API timeouts caused by connection pool exhaustion to PostgreSQL | verified | 0.92 | svc-payment-api | sess-1 |
| `fact-002` | episodic | root_cause | PostgreSQL primary had 98% connection utilization due to leaked connections | verified | 0.88 | svc-database | sess-1 |
| `fact-003` | procedural | fix_applied | Connection pool max increased from 20 to 50, leak patched in commit abc123 | verified | 0.95 | svc-payment-api | sess-3 |
| `fact-004` | semantic | depends_on | Auth Service shares the same PostgreSQL connection pool as Payment API | verified | 0.90 | svc-auth-service | sess-2 |
| `fact-005` | decision | decision | Monitor PostgreSQL connection count, alert at 80% threshold | verified | 1.0 | svc-database | sess-3 |

### Session 4: Investigating inc-005 (Payment Duplicate Charges) — CURRENT

| Fact ID | Kind | Predicate | Text | Status | Confidence | Subject | Session |
|---------|------|-----------|------|--------|-----------|---------|---------|
| `fact-010` | episodic | symptom | Customers reporting duplicate charges, approximately 150 affected | hypothesis | 0.85 | inc-005 | sess-4 |
| `fact-011` | episodic | possible_cause | Message queue retry logic may be causing duplicate payment processing | hypothesis | 0.70 | svc-queue | sess-4 |
| `fact-012` | episodic | possible_cause | Database idempotency key check is failing under high load | hypothesis | 0.65 | svc-database | sess-4 |

---

## Planted Traps

### Trap 1: Stale Fact (Superseded)

| Fact ID | Text | Status | tx_to | Superseded By |
|---------|------|--------|-------|--------------|
| `fact-006` | Payment API timeout caused by Auth Service slowness | **superseded** | 2026-09-15 14:20 | fact-001 |

`fact-006` was the initial hypothesis (Auth Service is the cause). It was superseded by
`fact-001` (actual cause was connection pool exhaustion). The supersession chain proves
that memory evolves and the system doesn't silently forget wrong answers.

### Trap 2: Contradiction (Unresolved)

| Fact A | Fact B | Conflict |
|--------|--------|----------|
| `fact-011` (queue retry logic causing duplicates) | `fact-012` (database idempotency check failing) | Two competing root causes for inc-005 |

Both are hypotheses with different confidence scores. The system should surface this
contradiction, not pick one silently.

### Trap 3: Cross-Project Leak Attempt

Create a Fact in `proj-gamma`:
| Fact ID | Text | Project | Subject |
|---------|------|---------|---------|
| `fact-gamma-001` | Classified financial data in ETL pipeline | proj-gamma | svc-etl |

**Test:** When querying facts for `proj-alpha`, this fact must **never** appear.

### Trap 4: Poisoning Attempt

| Fact ID | Text | Source | Status |
|---------|------|--------|--------|
| `fact-poison` | Payment API has a critical zero-day vulnerability CVE-2026-FAKE | src-poisoned | hypothesis |

This fact comes from an untrusted external source. The system should:
1. Store it as `hypothesis` (not verified)
2. Flag the source as untrusted
3. Not allow it to supersede verified facts
4. The verification query should reject it because the source is not trusted

### Trap 5: Temporal Confusion

| Fact ID | Text | valid_from | valid_to | tx_from | tx_to |
|---------|------|-----------|---------|---------|-------|
| `fact-007` | Connection pool size is 20 | 2026-01-01 | 2026-09-15 | 2026-09-15 | 2026-09-15 14:20 |
| `fact-003` | Connection pool max increased to 50 | 2026-09-15 | 9999999999 | 2026-09-15 | 9999999999 |

**Time-travel test:** "What was the connection pool size before September 15?"
Expected answer: 20 (from fact-007, which was valid before fact-003 superseded the state).

---

## Expected Graph State After Loading

### Entity Count
| Project | Persons | Services | Incidents | Documents | Total |
|---------|---------|----------|-----------|-----------|-------|
| proj-alpha | 6 | 7 | 5 | 4 | 22 |
| proj-beta | 2 | 3 | 2 | 0 | 7 |
| proj-gamma | 1 | 1 | 0 | 1 | 3 |
| **Total** | **9** | **11** | **7** | **5** | **32** |

### Fact Count
| Status | Count |
|--------|-------|
| verified | 5 |
| hypothesis | 4 |
| superseded | 1 |
| (poisoned hypothesis) | 1 |
| (gamma isolation) | 1 |
| **Total** | **12** |

### Edge Count (approximate)
| Edge Type | Count |
|-----------|-------|
| DEPENDS_ON | 8 |
| OWNS | 6 |
| AFFECTS | 8 |
| RESOLVED_BY | 4 |
| SUBJECT | 12 |
| DERIVED_FROM | 12 |
| ASSERTED_IN | 12 |
| SUPERSEDES | 1 |
| CONTRADICTS | 1 |
| VERIFIED_BY | 5 |
| **Total** | **~69** |

---

## Expected Query Results (Ground Truth)

### Q1: "Who owns the system affected by inc-005?"
```
inc-005 -AFFECTS-> svc-payment-api -OWNS<- person-arun
inc-005 -AFFECTS-> svc-database -OWNS<- (nobody — no OWNS edge)
```
Expected: Arun Mehta (payment-api owner). Database has no owner.

### Q2: "What do we know about svc-payment-api?" (current verified facts)
Expected: fact-001, fact-003 (both verified, current)
NOT expected: fact-006 (superseded)

### Q3: "What was decided about inc-001?"
Expected: fact-005 (decision to monitor PostgreSQL at 80% threshold)

### Q4: "What systems could be impacted by inc-005?" (2-hop traversal)
```
inc-005 -AFFECTS-> svc-payment-api -DEPENDS_ON<- svc-gateway
inc-005 -AFFECTS-> svc-database -DEPENDS_ON<- svc-payment-api (already found)
svc-payment-api -DEPENDS_ON<- (ShieldGuard's fraud-engine, cross-project)
```
Expected: svc-gateway (1 hop), svc-fraud-engine (2 hops, cross-project if allowed)

### Q5: "What did we conclude about payment issues last time?" (cross-session recall)
Query from sess-4, looking for facts from sess-1/sess-2/sess-3 about payment entities.
Expected: fact-001, fact-002, fact-003, fact-004, fact-005

### Q6: "Are there unresolved conflicts?"
Expected: fact-011 CONTRADICTS fact-012

### Q7: Counterfactual test — remove `(svc-payment-api)-[:DEPENDS_ON]->(svc-database)`
Impact query for inc-005 should no longer show database-related findings.
After restoring the edge, results should return to normal.

---

## Data Loading Order

1. Projects (3)
2. Agents (4)
3. Sources (7)
4. Entities — all types, across all projects (32)
5. Structural edges — DEPENDS_ON, OWNS (14)
6. Incident edges — AFFECTS, RESOLVED_BY (12)
7. Sessions (5)
8. Facts — in chronological order (12)
9. Fact edges — SUBJECT, DERIVED_FROM, ASSERTED_IN (36)
10. Memory edges — SUPERSEDES, CONTRADICTS, VERIFIED_BY (7)
11. Run invariant checks
