# Item 9 — Hour-by-Hour Build Plan (Solo Developer)

> Phase 0 design document · Engram · Graph Hacks 2026
> Track 2: Agent Memory and Coordination
>
> Total: 96 hours (Oct 15 00:01 – Oct 18 23:59 IST)
> Realistic working hours: ~14h/day × 4 days = 56 hours
> Buffer: 10 hours (for bugs, scope issues, rest)
> Net productive hours: ~46 hours

---

## Pre-Hackathon (Oct 12-14) — PAPER ONLY

> ✅ Already done: Schema critique, Cypher queries, synthetic dataset, benchmark,
> agent protocol, demo script, judging mapping, risk register, this build plan.

### Remaining Pre-Hack Tasks
- [ ] Pre-pull Docker images: `docker pull falkordb/falkordb:latest`
- [ ] Verify Docker Desktop works on your Windows machine
- [ ] Install/update: Python 3.11+, Node.js 20+, npm, Git
- [ ] Create empty GitHub repo: `engram-ai` (private until submission)
- [ ] Prepare `.env.example` with placeholder keys
- [ ] Choose LLM provider and get API key (Gemini, OpenAI, or Groq — pick one that supports tool calling reliably)
- [ ] Read FalkorDB Python client docs end-to-end
- [ ] Practice the demo narration once (timing only, no product needed)

---

## Day 1: October 15 (Foundation)

### Hour 0-1 (00:00-01:00) — Project Bootstrap
```
- [ ] Init Git repo with this docs/ folder
- [ ] Create project structure:
      engram-ai/
      ├── backend/
      │   ├── api/
      │   ├── agents/
      │   ├── graph/
      │   ├── memory/
      │   └── main.py
      ├── frontend/
      ├── data/
      ├── tests/
      ├── docker-compose.yml
      ├── requirements.txt
      ├── .env.example
      └── README.md
- [ ] docker-compose.yml with FalkorDB + backend services
- [ ] Start FalkorDB, confirm it's running
```

### Hour 1-3 (01:00-03:00) — FalkorDB Feature Verification ⚡ CRITICAL
```
- [ ] Write verify_falkordb_features.py
- [ ] Test each syntax item from the checklist:
      □ IS NULL / sentinel approach
      □ OPTIONAL MATCH
      □ Variable-length paths *1..3
      □ Multi-type relationships [:A|B]
      □ NOT EXISTS subquery
      □ DELETE specific relationship
      □ Map literals in RETURN
      □ IN list in WHERE
      □ Arithmetic in CREATE
      □ vecf32() parameter passing
      □ Full-text index + query
      □ Vector index + query
- [ ] Document what works, what needs fallback
- [ ] Update query templates based on results
```

### Hour 3-5 (03:00-05:00) — Graph Client + Schema
```
- [ ] backend/graph/client.py — FalkorDB connection wrapper (async)
- [ ] backend/graph/schema.py — create indexes, constraints
- [ ] backend/graph/queries.py — implement Q1-Q15 (use verified syntax)
- [ ] Test each query function with hardcoded parameters
```

### Hour 5-7 (05:00-07:00) — Synthetic Data Loader
```
- [ ] data/seed.py — loads all entities, relationships, facts from dataset spec
- [ ] data/synthetic/ — JSON files with entity/fact definitions
- [ ] Run seed, verify with manual Cypher queries in FalkorDB Browser
- [ ] Run invariant checks (all 8)
```

### 💤 REST (07:00-10:00)

### Hour 7-9 (10:00-12:00) — FastAPI Foundation
```
- [ ] backend/main.py — FastAPI app with CORS, health check
- [ ] backend/api/chat.py — POST /api/chat endpoint (placeholder)
- [ ] backend/api/graph.py — GET /api/entities, /api/facts, /api/investigation
- [ ] Connect FastAPI to FalkorDB graph client
- [ ] Test endpoints with curl/httpie
```

### Hour 9-11 (12:00-14:00) — Core Memory Operations
```
- [ ] backend/memory/remember.py — store new fact (Q1)
- [ ] backend/memory/recall.py — retrieve facts (Q2, Q3)
- [ ] backend/memory/explain.py — trace evidence (Q4)
- [ ] backend/memory/supersede.py — update fact (Q5)
- [ ] backend/memory/contradict.py — flag conflict (Q6)
- [ ] Unit tests for each memory operation
```

### Hour 11-14 (14:00-17:00) — Tests + Day 1 Checkpoint
```
- [ ] tests/test_graph_queries.py — test all 15 queries against synthetic data
- [ ] tests/test_memory.py — test remember/recall/supersede/contradict
- [ ] Fix any failures
- [ ] GIT COMMIT + PUSH
```

### Day 1 Exit Criteria ✅
- FalkorDB running with synthetic data
- All 15 queries working (verified syntax)
- Memory operations tested
- FastAPI serving basic endpoints
- No frontend yet — that's intentional

---

## Day 2: October 16 (Intelligence)

### Hour 14-16 (07:00-09:00) — Agent Framework
```
- [ ] backend/agents/base.py — BaseAgent class with tool registration
- [ ] backend/agents/tools.py — FalkorDB tool functions:
      □ graph_find_entity
      □ graph_impact_traversal
      □ graph_get_incidents
      □ recall
      □ semantic_recall
      □ timeline
      □ cross_session_recall
      □ explain
      □ remember
      □ verify_fact
      □ claim_task
      □ handoff_task
      □ find_contradictions
```

### Hour 16-19 (09:00-12:00) — Individual Agents
```
- [ ] backend/agents/investigator.py — InvestigatorBot
      □ System prompt
      □ Tool bindings: find_entity, impact_traversal, get_incidents, remember
      □ Test: ask about inc-005, verify it finds the right entities

- [ ] backend/agents/knowledge.py — KnowledgeBot
      □ System prompt
      □ Tool bindings: recall, semantic_recall, timeline, cross_session_recall, explain
      □ Test: ask for history of svc-payment-api, verify cross-session facts

- [ ] backend/agents/resolver.py — ResolverBot
      □ System prompt
      □ Tool bindings: recall, remember (decisions), claim_task
      □ Test: synthesize recommendation from findings
```

### Hour 19-21 (12:00-14:00) — Orchestrator + Coordination
```
- [ ] backend/agents/orchestrator.py — OrchestratorAgent
      □ Create session + investigation
      □ Dispatch to agents in sequence
      □ Merge results
      □ Task handoff between agents
- [ ] Test full pipeline: question → investigator → knowledge → resolver → response
```

### Hour 21-23 (14:00-16:00) — Session Management + Persistence
```
- [ ] backend/memory/session.py — create/close sessions
- [ ] backend/memory/investigation.py — create/update investigations
- [ ] Test: run investigation in session 1, close it, open session 2, recall findings
- [ ] GIT COMMIT + PUSH
```

### Hour 23-25 (16:00-18:00) — Integration Test
```
- [ ] tests/test_investigation.py — full pipeline test
      □ Ask about payment failure → get multi-agent response
      □ Start new session → ask "what did we learn?" → get cross-session recall
      □ Check facts in graph have correct status and provenance
- [ ] Fix issues
- [ ] GIT COMMIT + PUSH
```

### Day 2 Exit Criteria ✅
- All 4 agents working with FalkorDB tools
- Orchestrator dispatches and merges correctly
- Cross-session memory works (the killer feature)
- Agent coordination visible in logs
- Still no frontend — that's next

---

## Day 3: October 17 (Product)

### Hour 25-27 (07:00-09:00) — Frontend Bootstrap
```
- [ ] npx create-vite frontend -- --template react-ts
- [ ] Install: axios, react-markdown, (vis.js or react-force-graph for graph viz)
- [ ] Basic layout: sidebar + chat + panels
- [ ] Connect to backend API
```

### Hour 27-30 (09:00-12:00) — Core UI Components
```
- [ ] Chat interface — message input, response display, streaming
- [ ] Agent activity panel — show which agent is working, what tools were called
- [ ] Evidence panel — click a fact to see provenance (source, asserter, verifier)
- [ ] Test: type a question, see response with evidence
```

### Hour 30-32 (12:00-14:00) — Memory + Graph UI
```
- [ ] Memory timeline — show fact evolution for an entity
- [ ] Simple graph visualization — show entities + edges for investigation results
- [ ] "New Session" button — demonstrates cross-session memory
```

### Hour 32-34 (14:00-16:00) — Counterfactual Demo Feature
```
- [ ] Admin panel or debug button: "Remove edge" / "Restore edge"
      (calls backend endpoint that runs the DELETE/CREATE Cypher)
- [ ] Test the full counterfactual flow:
      □ Ask question → get result with database in path
      □ Remove edge → re-ask → database not in path
      □ Restore edge → re-ask → database back in path
```

### Hour 34-37 (16:00-19:00) — Polish + Bug Fixes
```
- [ ] Fix responsive layout issues
- [ ] Add loading states and error handling
- [ ] Test full demo flow 3 times
- [ ] GIT COMMIT + PUSH
```

### Hour 37-39 (19:00-21:00) — Benchmark Suite
```
- [ ] tests/test_benchmark.py — implement automated evaluation
- [ ] Run full benchmark, record results
- [ ] If results are bad: debug and fix the weakest queries/agents
- [ ] GIT COMMIT + PUSH
```

### Day 3 Exit Criteria ✅
- Working UI with chat, evidence, and agent activity
- Counterfactual demo works
- Full demo flow tested 3 times
- Benchmark results recorded (even if partial)

---

## Day 4: October 18 (Submission)

### Hour 39-41 (07:00-09:00) — README
```
- [ ] Write comprehensive README.md:
      □ Problem statement and why graph reasoning matters
      □ Architecture diagram (Mermaid or image)
      □ Graph data model (node/edge table)
      □ Key Cypher queries (top 5)
      □ How memory persistence works
      □ How agent coordination works
      □ Setup instructions (Docker, env vars, seed data, run)
      □ Demo description
      □ Evaluation results
      □ Track: Agent Memory and Coordination
      □ AI tools disclosure
      □ License: MIT
```

### Hour 41-43 (09:00-11:00) — Clean Environment Test
```
- [ ] Clone repo to a fresh directory
- [ ] Follow README setup instructions exactly
- [ ] docker-compose up → seed data → run backend → run frontend
- [ ] Run the demo flow once
- [ ] Fix any issues in setup instructions
- [ ] GIT COMMIT + PUSH
```

### Hour 43-45 (11:00-13:00) — Record Demo Video 🎬
```
- [ ] Set up screen recording (OBS or similar)
- [ ] Record the demo (follow demo script doc 05)
- [ ] Record narration separately (clear, calm)
- [ ] Combine video + audio
- [ ] Watch the recording — re-record if any section is unclear
- [ ] Target: 2.5-3 minutes
```

### Hour 45-47 (13:00-15:00) — Final Fixes
```
- [ ] Last bug fixes based on demo recording
- [ ] Update README if anything changed
- [ ] Run test suite one final time
- [ ] GIT COMMIT + PUSH
```

### Hour 47-48 (15:00-16:00) — Buffer Time
```
Use for:
- Re-recording demo if first attempt had issues
- Fixing critical bugs discovered during testing
- Deployment attempt (if time and if it adds value)
```

### Hour 48-49 (16:00-17:00) — Submission ⚡
```
- [ ] Make repository public
- [ ] Upload demo video (YouTube unlisted or direct upload)
- [ ] SUBMISSION CHECKLIST:
      □ Public GitHub repository URL
      □ README with setup instructions
      □ Demo video link
      □ Deployment URL (or "run locally" with instructions)
      □ Track selected: Agent Memory and Coordination
      □ Team name: Team Shiva
      □ AI tools disclosure
- [ ] Submit before 23:59 IST (target: 17:00 IST for safety margin)
- [ ] Verify submission was received
```

---

## Checkpoint Schedule

| Time | Check |
|------|-------|
| Oct 15, 17:00 | Day 1 exit criteria met? |
| Oct 16, 12:00 | Agents working with graph? |
| Oct 16, 18:00 | Day 2 exit criteria met? |
| Oct 17, 12:00 | UI connected and showing responses? |
| Oct 17, 19:00 | Day 3 exit criteria met? Full demo works? |
| Oct 18, 11:00 | Demo recorded? README done? |
| Oct 18, 15:00 | Clean environment test passed? |
| Oct 18, 17:00 | SUBMITTED? |

At each checkpoint, ask:
1. Can I demo the Tier 1 features right now?
2. What's blocking? Fix that, nothing else.
3. How much time remains? Apply the cut list.

---

## Emergency Plan

If by Oct 17 18:00 the agents don't work:
1. Strip the project to: FalkorDB + FastAPI + minimal chat
2. Hardcode the investigation flow (no LLM tool calling)
3. Show: graph query → fact storage → cross-session recall → counterfactual test
4. Record demo of the hardcoded flow
5. This still demonstrates Track 2 requirements with less sophistication

If by Oct 18 12:00 the demo video isn't recorded:
1. Use screen capture with typed narration (subtitles)
2. Keep it under 3 minutes
3. Focus on the 3 most impressive moments

If Docker/FalkorDB never works:
1. Use FalkorDB Cloud free tier
2. Update docker-compose to connect to cloud instance
3. Continue as planned
