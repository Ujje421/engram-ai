# 🧬 Engram — Graph-Native Memory & Coordination for AI Agents

<div align="center">

**The Cognitive Substrate for AI Agents · Persistent · Verifiable · Relational**

*Named after the neurological engram — the physical unit of cognitive memory trace encoded within neural networks. Engram grounds volatile agent cognition into an evidence-backed, bi-temporal knowledge graph powered by FalkorDB.*

[![Track](https://img.shields.io/badge/Track%202-Agent%20Memory%20%26%20Coordination-blueviolet?style=for-the-badge)]()
[![FalkorDB](https://img.shields.io/badge/Powered%20by-FalkorDB-FF8101?style=for-the-badge&logo=data:image/svg+xml;base64,PHN2Zz48L3N2Zz4=)]()
[![Graph Hacks](https://img.shields.io/badge/Graph%20Hacks-2026-00C853?style=for-the-badge)]()
[![License](https://img.shields.io/badge/License-MIT-blue?style=for-the-badge)]()

</div>

---

## The Problem

AI agents today suffer from **digital amnesia**. Every conversation is a blank slate.

Ask an agent to investigate a production incident on Monday, and by Tuesday it has
forgotten what it found. It can't tell you *why* it reached a conclusion. And when
multiple agents work together, they can't share what they've learned.

**What's missing isn't intelligence — it's memory.**

Not a chat log. Not a vector store of raw document chunks. A structured, evidence-backed,
versionable memory substrate that agents can **write to, read from, verify, and explain**.

---

## What Engram Does

Engram gives AI agents a **persistent knowledge graph** in FalkorDB where every
piece of learned information is a first-class citizen with provenance, lifecycle, and
relationships.

```
┌─────────────────────────────────────────────────────────────────┐
│                        What makes it different                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Traditional Chat Memory    vs    Engram Graph Memory           │
│  ─────────────────────────        ────────────────────           │
│  "User asked about X"            Fact: X caused Y                │
│  (lost after session)            Status: verified                │
│  (no source tracking)            Source: incident-log-42         │
│  (no verification)               Asserted by: InvestigatorBot   │
│  (silently overwrites)           Verified by: VerifierBot        │
│  (can't explain why)             Supersedes: old-hypothesis-7    │
│  (agents can't share)            Available to all project agents │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Core Capabilities

| Capability | Description |
|-----------|-------------|
| **🔗 Remember** | Store facts with subject, source, session, and confidence |
| **🔍 Recall** | Retrieve current verified facts about any entity — across sessions |
| **📖 Explain** | Trace any fact back to: who asserted it, from what source, who verified it, and what it replaced |
| **🔄 Evolve** | Supersede old facts with new evidence — the old fact is kept, not deleted |
| **⚡ Contradict** | Flag conflicting facts instead of silently picking one |
| **🤝 Coordinate** | Multiple agents claim tasks, hand off work, and share findings through FalkorDB |
| **🧪 Verify** | A separate verifier agent confirms hypotheses against source evidence |
| **🕐 Time-Travel** | Ask "what did we believe at time T?" — bi-temporal fact tracking |

---

## Architecture

```
┌───────────────────────────────────────────────────────────┐
│                   React + Vite Frontend                    │
│    💬 Chat  │  📋 Evidence Panel  │  🔗 Graph View        │
│             │  🤖 Agent Activity  │  📊 Memory Timeline   │
└──────────────────────┬────────────────────────────────────┘
                       │  REST API
┌──────────────────────┴────────────────────────────────────┐
│                    FastAPI Backend                          │
│                                                            │
│   Orchestrator ─→ InvestigatorBot ─→ KnowledgeBot         │
│                ─→ ResolverBot     ─→ VerifierBot           │
│                                                            │
│   ┌────────────────────────────────────────┐               │
│   │        Graph Memory Engine             │               │
│   │  remember · recall · explain           │               │
│   │  supersede · contradict · verify       │               │
│   │  claim_task · handoff · timeline       │               │
│   └──────────────────┬─────────────────────┘               │
└──────────────────────┼─────────────────────────────────────┘
                       │  Cypher Queries
┌──────────────────────┴─────────────────────────────────────┐
│                FalkorDB (Graph Database)                    │
│                                                             │
│   Entities · Facts · Sessions · Sources · Tasks             │
│   Vector Index · Full-Text Index · Range Indexes            │
│   Bi-temporal tracking · Evidence chains · Supersession     │
└─────────────────────────────────────────────────────────────┘
```

---

## Graph Data Model

### The Core Idea: Facts Are Nodes

In most systems, knowledge is stored as key-value pairs or embedded in text.
In Engram, every learned fact is a **graph node** with typed edges to its
subject, source, session, and related facts.

```cypher
(fact:Fact {
  text: "Payment API timeouts caused by connection pool exhaustion",
  status: "verified",
  confidence: 0.92,
  kind: "episodic",
  valid_from: 1726387200,    -- when it became true in the world
  tx_from: 1726387500        -- when the system learned it
})-[:SUBJECT]->(entity:Entity {name: "Payment API", type: "service"})
 -[:DERIVED_FROM]->(source:Source {uri: "logs/payment-api/2026-09-15.log"})
 -[:ASSERTED_IN]->(session:Session)-[:RUN_BY]->(agent:Agent {name: "InvestigatorBot"})
 -[:VERIFIED_BY]->(verifier:Agent {name: "VerifierBot"})
 -[:SUPERSEDES]->(old_fact:Fact {text: "Auth Service slowness causing timeouts", status: "superseded"})
```

### Node Types

| Node | Purpose | Key Properties |
|------|---------|---------------|
| **Entity** | Things in the world (services, people, incidents, documents) | id, project_id, type, name, embedding |
| **Fact** | What the system believes about an entity | text, status, confidence, kind, bi-temporal timestamps |
| **Session** | A conversation or investigation session | id, agent_id, started_at, ended_at |
| **Agent** | An AI agent that can read/write the graph | id, name, role, trust_level |
| **Source** | Evidence backing a fact (logs, docs, tickets) | type, uri, content_hash |
| **Task** | Work items for agent coordination | title, state, lease_expires |
| **Investigation** | Groups related findings into a thread | title, status, created_at |
| **Message** | Conversation audit trail | role, content, timestamp |
| **Action** | Tool calls and their results | tool_name, parameters, result, status |

### Fact Lifecycle

```
                  ┌──────────────────┐
                  │                  │
  New evidence ──▶│   hypothesis     │◀── LLM-extracted claim
                  │                  │
                  └────────┬─────────┘
                           │
                    verified by a
                    different agent
                           │
                  ┌────────▼─────────┐
                  │                  │
                  │    verified      │◀── Source-backed + agent-confirmed
                  │                  │
                  └───┬─────────┬────┘
                      │         │
              new evidence   contradicting
              arrives        evidence found
                      │         │
           ┌──────────▼──┐  ┌──▼──────────┐
           │ superseded  │  │  refuted    │
           │ (old kept)  │  │ (flagged)   │
           └─────────────┘  └─────────────┘
```

### Key Relationships

```
(Fact)-[:SUBJECT]->(:Entity)         What the fact is about
(Fact)-[:DERIVED_FROM]->(:Source)    Where the evidence came from
(Fact)-[:ASSERTED_IN]->(:Session)   When and by whom it was asserted
(Fact)-[:SUPERSEDES]->(:Fact)        New evidence replaces old
(Fact)-[:CONTRADICTS]->(:Fact)       Conflicting claims flagged
(Fact)-[:VERIFIED_BY]->(:Agent)      Who confirmed the claim
(Entity)-[:DEPENDS_ON]->(:Entity)   Service dependencies
(Entity)-[:AFFECTS]->(:Entity)       Incident impact chains
(Task)-[:CLAIMED_BY]->(:Agent)       Agent coordination
(Task)-[:HANDED_OFF_TO]->(:Agent)    Work handoff trail
```

---

## Multi-Agent Coordination

Four agents collaborate through FalkorDB's shared graph state:

| Agent | Role | Reads From Graph | Writes To Graph |
|-------|------|-----------------|-----------------|
| **InvestigatorBot** | Identify entities, traverse dependencies, find incidents | Entity, dependency edges | New hypothesis facts |
| **KnowledgeBot** | Retrieve history, past decisions, cross-session context | Facts, sessions, sources | Nothing (read-only) |
| **ResolverBot** | Synthesize findings into recommendations | Investigation findings | Decision facts, task claims |
| **VerifierBot** | Confirm hypotheses against evidence | Fact provenance chains | Status promotions (hypothesis → verified) |

### Coordination Flow

```
User: "Payment service has duplicate charges. What's happening?"
                    │
    ┌───────────────┴───────────────┐
    │          Orchestrator          │
    │   Creates session + investigation
    └───────┬───────┬───────┬───────┘
            │       │       │
    ┌───────▼──┐ ┌──▼────┐ ┌▼──────────┐
    │Investigator│ │Knowledge│ │Resolver   │
    │           │ │        │ │           │
    │Find inc-005│ │Recall   │ │Synthesize │
    │Traverse   │ │prior    │ │recommend- │
    │dependencies│ │sessions │ │ation     │
    │Store hypo- │ │Surface  │ │Store     │
    │theses     │ │conflicts│ │decision  │
    └───────┬──┘ └──┬────┘ └┬──────────┘
            │       │       │
    ┌───────▼───────▼───────▼───────┐
    │          VerifierBot           │
    │  Confirm symptoms (✓)         │
    │  Reject untrusted claims (✗)  │
    │  Promote verified facts       │
    └───────────────┬───────────────┘
                    │
            Final response with
            evidence + provenance
```

---

## Key Cypher Queries

### Cross-Session Memory Recall
```cypher
-- "What did we learn about the Payment API in previous sessions?"
MATCH (f:Fact)-[:SUBJECT]->(e:Entity {id: $entity_id, project_id: $project_id})
MATCH (f)-[:ASSERTED_IN]->(sess:Session)
WHERE sess.id <> $current_session_id
  AND f.status IN ['verified', 'hypothesis']
  AND f.tx_to = 9999999999
MATCH (sess)-[:RUN_BY]->(agent:Agent)
RETURN f.text, f.status, f.confidence, agent.name, sess.started_at
ORDER BY sess.started_at DESC
```

### Fact Evidence Chain (Explainability)
```cypher
-- Trace exactly why the system believes something
MATCH (f:Fact {id: $fact_id})
MATCH (f)-[:SUBJECT]->(subj:Entity)
MATCH (f)-[:ASSERTED_IN]->(sess:Session)-[:RUN_BY]->(agent:Agent)
OPTIONAL MATCH (f)-[:DERIVED_FROM]->(src:Source)
OPTIONAL MATCH (f)-[:VERIFIED_BY]->(verifier:Agent)
OPTIONAL MATCH (f)-[:SUPERSEDES]->(old:Fact)
RETURN f.text, subj.name, agent.name AS asserted_by,
       verifier.name AS verified_by, collect(src.uri) AS sources,
       old.text AS replaced_claim
```

### Multi-Hop Impact Analysis
```cypher
-- Which systems are affected if this service goes down?
MATCH (incident:Entity {id: $incident_id, type: 'incident'})
MATCH path = (incident)-[:AFFECTS|DEPENDS_ON*1..3]->(impacted:Entity)
WHERE impacted.type IN ['service', 'component', 'api']
RETURN DISTINCT impacted.name, impacted.type, length(path) AS hops
ORDER BY hops ASC
```

### Memory Evolution (Supersession Chain)
```cypher
-- How has our understanding of this entity changed?
MATCH (f:Fact)-[:SUBJECT]->(e:Entity {id: $entity_id})
OPTIONAL MATCH (f)-[:SUPERSEDES]->(old:Fact)
OPTIONAL MATCH (newer:Fact)-[:SUPERSEDES]->(f)
RETURN f.text, f.status, f.confidence, f.tx_from,
       old.text AS superseded_claim, newer.text AS superseded_by
ORDER BY f.tx_from ASC
```

---

## Setup & Run

### Prerequisites
- Docker & Docker Compose
- Python 3.11+
- Node.js 20+
- LLM API key (Gemini or OpenAI)

### Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/ujje421/engram-ai.git
cd engram-ai

# 2. Configure environment
cp .env.example .env
# Edit .env with your LLM API key

# 3. Start FalkorDB
docker-compose up -d

# 4. Install backend dependencies
cd backend
pip install -r requirements.txt

# 5. Seed the graph with synthetic data
python -m data.seed

# 6. Start the backend
uvicorn main:app --reload --port 8000

# 7. Start the frontend (new terminal)
cd ../frontend
npm install
npm run dev
```

### Verify Setup
```bash
# Run the test suite
cd backend
python -m pytest tests/ -v

# Check FalkorDB is populated
python -m graph.verify
```

---

## Evaluation

We evaluate Engram against three baselines across 8 test categories:

| Category | What We Measure | Tests |
|----------|----------------|-------|
| Multi-Hop Reasoning | Correct entities found across 2-3 relationship hops | 3 |
| Temporal Reasoning | Correct fact version for a given point in time | 3 |
| Contradiction Handling | Conflicting facts surfaced, not silently resolved | 3 |
| Agent Handoff | Receiving agent uses previous agent's findings | 3 |
| Cross-Session Persistence | Facts from session N available in session N+1 | 3 |
| Isolation | No cross-project fact leakage | 3 |
| Insufficient Evidence | System abstains when evidence is missing | 3 |
| Graph Dependency | Removing a graph edge changes the agent's conclusion | 3 |

### The "Remove Test"

The strongest proof that FalkorDB is essential:

1. Ask: "What systems are impacted by inc-005?"
2. Remove the `DEPENDS_ON` edge between Payment API and PostgreSQL
3. Re-ask the same question
4. The answer changes — PostgreSQL is no longer in the blast radius
5. Restore the edge — the answer returns to normal

If the answer doesn't change, the graph is decorative. In Engram, **it changes**.

---

## Project Structure

```
engram-ai/
├── frontend/                  # React + Vite
│   ├── src/
│   │   ├── components/        # Chat, EvidencePanel, AgentLog, GraphView
│   │   ├── pages/             # Main investigation interface
│   │   └── api/               # Backend API client
│   └── package.json
├── backend/
│   ├── api/                   # FastAPI route handlers
│   │   ├── chat.py            # POST /api/chat
│   │   └── graph.py           # GET /api/entities, /api/facts
│   ├── agents/                # Multi-agent system
│   │   ├── orchestrator.py    # Dispatches to specialist agents
│   │   ├── investigator.py    # InvestigatorBot
│   │   ├── knowledge.py       # KnowledgeBot
│   │   ├── resolver.py        # ResolverBot
│   │   └── verifier.py        # VerifierBot
│   ├── graph/                 # FalkorDB integration
│   │   ├── client.py          # Connection management
│   │   ├── schema.py          # Indexes, constraints
│   │   └── queries.py         # All 15 Cypher query templates
│   ├── memory/                # Memory operations
│   │   ├── remember.py        # Store facts
│   │   ├── recall.py          # Retrieve facts
│   │   ├── explain.py         # Trace evidence chains
│   │   ├── supersede.py       # Update with new evidence
│   │   └── contradict.py      # Flag conflicts
│   ├── main.py                # FastAPI app entry point
│   └── requirements.txt
├── data/
│   ├── seed.py                # Load synthetic dataset into FalkorDB
│   └── synthetic/             # JSON entity/fact definitions
├── tests/
│   ├── test_graph_queries.py  # Query correctness
│   ├── test_memory.py         # Memory operations
│   ├── test_investigation.py  # End-to-end pipeline
│   └── test_benchmark.py      # Full evaluation suite
├── docs/                      # Design documents
├── docker-compose.yml         # FalkorDB + services
├── .env.example
├── README.md
└── LICENSE
```

---

## Tech Stack

| Component | Technology | Why |
|-----------|-----------|-----|
| Graph Database | **FalkorDB** | Required. Native vector + full-text + Cypher. Redis-based performance. |
| Backend | **FastAPI** (Python) | Async, typed, fast development. Native Pydantic validation. |
| Frontend | **React + Vite** | Fast builds, TypeScript, component ecosystem. |
| LLM | **Gemini / OpenAI** | Tool calling for agent actions. |
| Graph Client | **falkordb-py** | Official async Python client. |

---

## Track & Team

- **Track:** Agent Memory and Coordination
- **Team:** Team Shiva
- **Hackathon:** Graph Hacks 2026 (FalkorDB × WeMakeDevs)

---

## AI Tools Disclosure

As required by hackathon rules, the following AI coding assistants were used
during development:

- **Google Antigravity (Gemini)** — code generation.
All code was reviewed, understood, and tested by the developer.

---

## License

MIT License — see [LICENSE](./LICENSE) for details.
