<!-- CODEGRAPH_START -->
## CodeGraph

This project has a CodeGraph MCP server (`codegraph_*` tools) configured. CodeGraph is a tree-sitter-parsed knowledge graph of every symbol, edge, and file. Reads are sub-millisecond and return structural information grep cannot.

### When to prefer codegraph over native search

Use codegraph for **structural** questions — what calls what, what would break, where is X defined, what is X's signature. Use native grep/read only for **literal text** queries (string contents, comments, log messages) or after you already have a specific file open.

| Question | Tool |
|---|---|
| "Where is X defined?" / "Find symbol named X" | `codegraph_search` |
| "What calls function Y?" | `codegraph_callers` |
| "What does Y call?" | `codegraph_callees` |
| "What would break if I changed Z?" | `codegraph_impact` |
| "Show me Y's signature / source / docstring" | `codegraph_node` |
| "Give me focused context for a task/area" | `codegraph_context` |
| "Survey an unfamiliar module/topic" | `codegraph_explore` |
| "What files exist under path/" | `codegraph_files` |
| "Is the index healthy?" | `codegraph_status` |

### Rules of thumb

- **Trust codegraph results.** They come from a full AST parse. Do NOT re-verify them with grep — that's slower, less accurate, and wastes context.
- **Don't grep first** when looking up a symbol by name. `codegraph_search` is faster and returns kind + location + signature in one call.
- **Don't chain `codegraph_search` + `codegraph_node`** when you just want context — `codegraph_context` is one call.
- **`codegraph_explore` is the heavy hitter** for unfamiliar areas — it returns full source from all relevant files in one call, but is token-heavy. If your harness supports parallel subagents (e.g., Claude Code's Task tool), spawn one for explore-class questions to keep main session context clean.
- **Index lag**: the file watcher debounces ~500ms behind writes; don't re-query immediately after editing a file in the same turn.

### If `.codegraph/` doesn't exist

The MCP server returns "not initialized." Ask the user: *"I notice this project doesn't have CodeGraph initialized. Want me to run `codegraph init -i` to build the index?"*
<!-- CODEGRAPH_END -->


<claude-mem-context>
# Memory Context

# [DSAT_REDUX_MD] recent context, 2026-07-16 3:33pm PDT

Legend: 🎯session 🔴bugfix 🟣feature 🔄refactor ✅change 🔵discovery ⚖️decision 🚨security_alert 🔐security_note
Format: ID TIME TYPE TITLE
Fetch details: get_observations([IDs]) | Search: mem-search skill

Stats: 50 obs (25,068t read) | 737,420t work | 97% savings

### Jul 16, 2026
135 10:10a 🔵 oauth_feature Is 11 Commits Ahead of main With Zero Conflicts
138 10:17a 🔵 Git stash list and working tree state in DSAT_REDUX_MD
S23 Plan incorrect questions review feature for DSAT student app — full architecture investigation and backend design proposal (Jul 16, 10:18 AM)
139 10:30a ⚖️ Incorrect Questions Review Feature Planned for Student App Main Page
140 10:31a 🔵 Tokensave index misconfigured for DSAT_REDUX_MD worktree
141 " 🔵 Existing MissedQuestionsTab and related infrastructure in DSAT_REDUX_MD student app
142 " 🔵 MissedQuestionsTab and MissedQuestionItem data shape gaps for new incorrect questions feature
143 " 🔵 Backend /study/missed endpoint implementation and data model gaps for full question review
144 10:32a 🔵 Full ORM data model for incorrect questions feature: passage available on Question, choices via QuestionOption, section type gap
145 " 🔵 Practice test answers stored in TestSessionResults JSONB, not linked to UserProgress rows
146 10:42a 🔵 Student app route map and missing /missed-questions route
147 " 🔵 Separate submit endpoints for diagnostic vs practice test vs drill — UserProgress session tagging confirmed
S24 Incorrect questions review feature plan — API contract design for GET /study/review endpoint (Jul 16, 10:43 AM)
S25 Incorrect questions review feature plan — frontend UX and architecture design (Section 3) (Jul 16, 10:44 AM)
S26 Incorrect questions review feature plan — incorrect_questions_plan.md written and delivered for review (Jul 16, 10:45 AM)
148 10:48a 🔵 Project plan file conventions established via admin_dashboard_plan.md format
149 " ✅ incorrect_questions_plan.md created with full design spec for missed questions review feature
S27 Spec alignment of incorrect_questions_plan.md §4 with tasks file — confirmed feature not yet implemented (Jul 16, 10:50 AM)
150 10:51a 🔵 Incorrect Questions Review — Design Spec Found in DSAT_REDUX_MD
151 " 🔵 Gap Review Confirmed: `user_progress` Lacks `source_type` Column and `POST /submit` Has No Session Tagging
152 10:52a 🔵 All `submitAnswer` Call Sites Mapped — None Send `source_type`, DiagnosticTab Has a Subtle Fallback Gap
153 " 🔵 Question Model Has All Fields Needed for GET /study/review Without Additional Columns
154 10:53a 🔵 Migration Infrastructure Confirmed, DashboardPage Entry Point Absent, and Two Unlisted Call Sites Found
156 10:54a 🟣 incorrect_questions_tasks.md created with 6 phased implementation tasks
157 " ✅ incorrect_questions_plan.md updated with gap-review fixes
S29 User confirmed: add explicit Phase N headers to incorrect_questions_tasks.md to make phase structure visible (Jul 16, 11:10 AM)
S28 User asked if task file is specced into phases — confirmed yes, via IQ-B/IQ-F/IQ-QA prefix structure with dependency map, not explicit Phase N headers (Jul 16, 1:37 PM)
S30 Add explicit Phase 1–4 headers to incorrect_questions_tasks.md — completed full structural reorganization (Jul 16, 2:20 PM)
155 2:24p ✅ Added explicit Phase headers to incorrect_questions_tasks.md
S31 User asked about parallelizing tasks — analysis shows critical path is essentially serial except for one backend∥frontend worktree split (Jul 16, 2:24 PM)
158 2:46p ✅ incorrect_questions_tasks.md and plan gap-cleared with second-pass implementation detail
160 " ✅ Third-pass patch attempted on both task/plan files — failed on plan content_origin text mismatch
159 2:47p 🔵 UserProgress model confirmed missing source_type column — IQ-B01 migration not yet run
161 2:48p ✅ incorrect_questions_tasks.md updated with row_number latest-row semantics and parallel B02/B03 execution model
162 2:49p ✅ incorrect_questions_plan.md patched with row_number latest-row semantics — plan and tasks files now in sync
163 2:51p ✅ incorrect_questions_tasks.md — fourth-pass operational hardening applied (7 independent gaps closed)
164 " ✅ incorrect_questions_plan.md — correct-answer source-of-truth section rewritten to match tasks file graceful-degradation logic
165 " ✅ Fifth-pass patch applied to both spec files — CSV validation, page-reset, filter-bar, and NULL source semantics gaps closed
167 2:56p ⚖️ Implementation started on branch `missed_question` for incorrect question review feature
168 2:57p 🔵 DSAT project environment and UserProgress model state confirmed before IQ-B01 implementation
169 " 🟣 IQ-B01 implemented: `source_type` column added to UserProgress model with migration 034 and model test
170 2:58p 🔵 `uv run` fails in primary session environment — read-only filesystem blocks uv cache writes
S32 Create branch `missed_question` and begin implementing incorrect question review feature (IQ-B01 through IQ-QA01) (Jul 16, 2:58 PM)
171 3:01p 🔵 Parallel verification commands timing out — alembic current likely blocking on DB connection
173 " 🔵 Alembic current hangs and psql exits with error — dev DB unreachable from host despite Docker showing it up
172 " 🔵 Branch confirmed as `missed_question`; alembic current returned empty — migration 034 not yet applied to dev DB
174 3:06p 🔵 Dev DB state confirmed: at revision 033, no source_type column, no lock contention — migration 034 not yet run
175 3:07p 🟣 IQ-B01 model and migration verified: 7 tests pass, alembic heads shows 034, migration syntax clean
176 3:08p 🔵 Pre-migration row count confirmed; alembic not on PATH in backend container — must use full venv path
177 " 🔵 Backend container uses `.venv-jb` not `.venv` — correct alembic path is `/app/.venv-jb/bin/alembic`
178 " 🔵 `.venv-jb` binaries exist as files but are not directly executable in the container — likely shebang or symlink points to host path
179 3:09p 🟣 IQ-B01 migration 034 successfully applied to dev DB — source_type column backfilled and verified
180 " ✅ Tasks file updated: IQ-B01 marked complete, IQ-B02 claimed as in_progress
181 " 🔵 IQ-B02 pre-implementation reconnaissance complete — exact change points mapped for payload, backend, API client, hook, and tests
182 " 🔵 IQ-B02 full call-site audit complete — exact lines, current payloads, and test assertions mapped for all 5 frontend components
183 3:10p 🔵 Frontend test audit complete — TestModeTabAdaptive mocks the hook not the API; only one test has an exact payload assertion
185 " 🟣 IQ-B02 implemented: source_type persisted from all submit paths across 10 files
184 " 🔵 Complete submitAnswer call-site map finalized — 3 direct api calls, 4 hook usages, tsconfig at root
186 3:12p 🟣 IQ-B02 fully verified: 47 backend tests pass, 8-9 frontend hook tests pass, TypeScript + Vite build succeeds
187 " 🔵 Vite/rolldown build fails with `rtk proxy npm` but succeeds with `rtk npm` — Node 20.20.2 + rolldown SyntaxError in proxy mode

Access 737k tokens of past work via get_observations([IDs]) or mem-search skill.
</claude-mem-context>