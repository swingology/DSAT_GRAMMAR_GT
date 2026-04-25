# AI MCP Agentic Integration Plan — DSAT Grammar Backend

An MCP server wrapping the DSAT Grammar backend enables any MCP-compatible client (Claude Code, Claude Desktop, OpenClaw, custom UIs) to read/write question data, trigger pipelines, and pull student stats — without custom API integrations.

---

## 1. Benefits

### Agentic Test Management

- An LLM can browse the question bank, find weak areas by grammar focus, and dynamically assemble practice sets — not just by `grammar_focus_key` but by understanding *why* a student is missing certain traps.
- Monitor user progress via `user_progress` and `llm_evaluations`, then autonomously kick off generation of new questions targeting the specific syntactic traps a student keeps failing.
- Navigate the overlap detection and relation tables — trace "this student keeps missing subject_verb_agreement when a prepositional phrase intervenes" and pull exactly those questions.

### Smarter Teaching Through the Interface

The backend returns questions and records right/wrong. With MCP, an LLM client can:

- After a wrong answer, pull the annotation's `why_wrong` and `trap_mechanism` and generate a personalized mini-lesson in real time.
- Track which distractors a student picks and adapt subsequent question selection.
- Act as a tutor that knows the full V3 taxonomy and can explain *why* B is plausible but wrong.

### Generation Efficiency Gains

- Pull existing questions, identify coverage gaps in the corpus, generate only what's missing.
- Before generating, check overlap against official questions so you don't waste tokens on near-duplicates.
- Run generation comparison jobs and automatically score results via `llm_evaluations` — closing the loop without a human in the middle.

### UI Decoupling (OpenClaw, etc.)

- An agentic UI wouldn't need a bespoke frontend. The agent reads the question bank via MCP tools, presents questions in whatever UI the client supports, records answers, and adjusts. The backend becomes a pure data + pipeline engine.
- A "teaching UI" comes for free — the agent handles presentation, the backend handles correctness and pedagogy.

---

## 2. MCP Tools to Expose

| Tool | Purpose |
|------|---------|
| `recall_questions(focus, difficulty, limit)` | Pull practice questions filtered by grammar focus, difficulty, origin |
| `submit_answer(user_id, question_id, answer)` | Record attempt + return instant feedback with explanation |
| `get_user_weaknesses(user_id)` | Aggregate stats → top missed grammar foci and syntactic traps |
| `generate_question(focus, difficulty)` | Spawn generation pipeline, return job ID to poll |
| `annotate_question(question_data)` | Run single-pass annotation on extracted question data |
| `get_question_detail(id)` | Full question + annotation + options + version history |
| `get_related_questions(question_id)` | Traverse relation graph (overlaps, derived_from) for similar questions |
| `get_user_stats(user_id)` | Accuracy, total answered, streak data |
| `list_users()` | Active users for admin/oversight |

---

## 3. The Feedback Loop

The biggest win: **the feedback loop closes autonomously**.

```
Student misses question
    → agent sees it in stats
    → agent looks up annotation for why_wrong + trap_mechanism
    → agent generates personalized explanation
    → agent generates a new question targeting that specific gap
    → student practices it
    → agent checks if they improved
    → repeat
```

This loop currently requires manual steps. With MCP, it runs continuously per student.

---

## 4. Architecture

```
MCP Client (Claude Desktop / OpenClaw / custom UI)
    │
    ├── MCP Protocol (tools + resources)
    │
    ▼
MCP Server (Python, using fastmcp or similar)
    │
    ├── app.database (asyncpg via SQLAlchemy)
    ├── app.models.db (ORM: Question, UserProgress, etc.)
    ├── app.pipeline (trigger generation jobs)
    └── app.llm (run annotations, generate explanations)
```

The MCP server reuses the existing `app` package directly — no HTTP layer needed. It's a direct Python import, zero serialization overhead.

---

## 5. Implementation Notes

- **Resources**: Expose questions as MCP resources with URIs like `dsat://questions/{id}`, `dsat://users/{id}/stats`
- **Prompts**: Optionally expose a "tutor prompt template" that sets up the LLM with the V3 taxonomy for generating explanations
- **Authentication**: Reuse the existing API key auth or upgrade to Supabase Auth for student-scoped tokens
- **Sampling**: The MCP server can request LLM completions (generate explanations, create new questions) through the MCP sampling protocol, avoiding a second API key management layer

---

## 6. Architectural Approaches — Compare & Contrast

### Approach A: FastAPI-Only (traditional web app)

```
Browser (React) ──REST──▶ FastAPI ──▶ Supabase
                              │
                         [writes stats,
                          serves questions,
                          runs pipelines]
```

The agent does not exist at runtime. The website handles everything — question serving, answer submission, stats computation. The LLM is only used for ingestion/generation pipelines, never for student interaction.

**Who writes stats?** FastAPI (exclusive writer)
**Who reads stats?** FastAPI endpoints
**Consistency:** Perfect (single writer)
**Teaching quality:** None (returns right/wrong only)
**Works without agent:** Yes — the app is fully functional
**Latency per answer:** ~100ms
**Complexity:** Low

### Approach B: Agent-Centric (MCP is primary interface)

```
Browser/OpenClaw ──MCP──▶ MCP Server ──▶ FastAPI DB layer
     │                                     (read/write)
  [agent mediates
   everything]
```

The agent sits in the client and calls MCP tools for everything — getting questions, recording answers, computing stats. FastAPI becomes a pure data layer. The agent is the business logic.

**Who writes stats?** MCP agent (via tool calls)
**Who reads stats?** MCP agent
**Consistency:** Risk of drift if website and agent both write
**Teaching quality:** High — full LLM context on every interaction
**Works without agent:** No — agent is the critical path
**Latency per answer:** ~2-10s (every interaction goes through LLM)
**Complexity:** High — agent must be connected for the app to function

### Approach C: Hybrid (recommended)

```
Browser (React) ──REST──▶ FastAPI ──▶ Supabase
     │                     │
     │               [writes stats,
     │                serves questions,
     │                returns results]
     │
     │
  [agent reads stats,      ▲
   generates insights,     │
   creates practice sets]  │
     │                     │
     └──── MCP ────────────┘
```

The website handles all writes. The agent handles reads + analysis. When a student submits an answer: the browser POSTs to `/api/submit` → FastAPI writes `user_progress` and returns right/wrong → the agent independently reads the updated stats via MCP and generates coaching.

**Who writes stats?** FastAPI (always — single writer)
**Who reads stats?** Both — REST for UI, MCP for agent (read-only)
**Consistency:** Perfect — FastAPI is the sole writer
**Teaching quality:** High — agent analyzes asynchronously with full LLM context
**Works without agent:** Yes — core Q&A flow is independent
**Latency per answer:** ~100ms (REST) + async agent analysis (non-blocking)
**Complexity:** Medium — agent is a sidecar, not the critical path

### Where the Agent Lives

| Approach | Agent location | Notes |
|----------|---------------|-------|
| A: FastAPI-only | None | No agent |
| B: Agent-Centric | Desktop (Claude Desktop / OpenClaw) | Must be running for app to function |
| C: Hybrid (recommended) | Browser side-panel / OpenClaw / overlay | Agent is optional — adds value when present |

### Summary Table

| Dimension | A: FastAPI-only | B: Agent-Centric | C: Hybrid |
|-----------|----------------|-----------------|-----------|
| Who writes stats? | FastAPI | MCP agent | FastAPI (always) |
| Who reads stats? | FastAPI endpoints | MCP agent | REST for UI, MCP for agent |
| Consistency | Perfect | Risk of drift | Perfect |
| Teaching quality | None (right/wrong) | High (full LLM) | High (async analysis) |
| Works without agent | Yes | No | Yes |
| Latency per answer | ~100ms | ~2-10s | ~100ms + async agent |
| Complexity | Low | High | Medium |

### Recommendation: Hybrid (C)

- **Stats are always written by FastAPI.** The `/api/submit` endpoint records the answer. This keeps data consistent regardless of whether the agent is connected.
- **The agent reads stats via MCP** and generates insights, but never writes directly to `user_progress` or `questions` tables. It is a read-only analyst.
- The agent sits in the **browser as a side-panel** (via OpenClaw or embedded MCP client). It watches progress and offers coaching, but the core Q&A flow works perfectly without it.

This way the traditional website works independently, and the agent adds value on top without risking data integrity. The MCP server is read-heavy (stats, questions) with only one write operation: `generate_question` (creates a `QuestionJob`, not user data).
