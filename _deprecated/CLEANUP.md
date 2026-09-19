# Repo Cleanup Audit

Generated 2026-08-22. Audit only — nothing deleted or moved. Evidence = grep for inbound references across `backend/`, `APP/`, `docker-compose.yml`, `start.sh`/`stop.sh`, `.wolf/anatomy.md`, plus checkbox/CHANGELOG cross-checks for task docs.

## Already staged for deletion (uncommitted)

Prior session traced these dead and `git rm`'d them from disk; just not committed yet.

- `FRONTEND/` (43 files) — superseded by `APP/STUDENT_APP_REDUX/`; docker-compose only builds `./APP/STUDENT_APP_REDUX`. Confirmed dead.
- `dev_server.py` — standalone SPA dev server, superseded by the Docker/Vite dev stack. Confirmed dead.
- `db` — empty placeholder blob, never had content.
- `ingestion` — empty placeholder blob, never had content.
- `backend/test_ocr_live.py` — superseded by the Claude skill runner (`run_ocr_benchmark.py` + skills).

**Action:** these are safe to `git add -u && git commit`.

## Safe to delete — confirmed orphaned

- `node_modules/` (root, 0 packages inside, no root `package.json` exists) — dead directory shell, nothing references it.
- `__pycache__/dev_server.cpython-313.pyc` (root) — bytecode for the already-dead `dev_server.py`.
- `UPFOR_DELETE.md` — 0 bytes, empty stub. This report (`CLEANUP.md`) fulfills its intent; the stub itself is now redundant.
- `grammar-top.jpeg`, `mixed-practice.png`, `practice-card-expanded.png` (root images, ~400KB total) — zero references anywhere in `.md`/`.tsx`/`.ts`. Look like design-conversation screenshots, not app assets.
- `qwen3_test01_q01.md`, `notes.md` (229 bytes), `opencode.jsonc` — zero inbound references outside their own listing in `.wolf/anatomy.md`/logs.
- `docs/research_v1/grammar_research.md` — byte-identical to `docs/research/grammar_research.md` (confirmed via `diff`). Keep one, drop the other.
- `.stimulus-worker.log`, `.admin-dashboard.log`, `.admin-dashboard.pid` (root) — runtime log/pid artifacts, not source. Not currently gitignored — add to `.gitignore` rather than one-time delete (they'll regenerate).

## Archive candidates — completed work, not deleted

Move to `docs/archive/` (already exists and already holds prior completed docs) rather than delete — historical record.

- `TASK_OAUTH.md` — OAuth login shipped and merged to main 2026-07-16 (confirmed working with real Google sign-in 2026-07-17 per project memory). Phase 0 explicitly marked `✅ COMPLETE`.
- `TASKS_GENERATION.md` — 81/81 checkboxes done, 0 open.
- `annotate_refactor_task.md` — 30/31 done, effectively shipped.
- `TASKS_OCR.md` — 20/24 done; mostly shipped, 4 open items — hold until those 4 are checked, or split.
- `2024_PT1_audit.md` through `2024_PT4_audit.md`, `2025_PT1_ANSWERS.md` — per memory, all PT1 answer-change findings verified/applied (bug-819 etc.); these are audit trail docs whose findings have been actioned. Good `docs/archive/` fits.
- `admin_dashboard_issues.md` — Gap 1 (Critical) fixed per memory; check remaining gaps 2-3 before archiving fully (see Needs human judgment).
- The 4-doc old admin-dashboard package (`ADMIN_DASHBOARD_DESIGN.md`, `ADMIN_DASHBOARD_README.md`, `ADMIN_DASHBOARD_TASKS.md`, `ADMIN_DASHBOARD_WIREFRAMES.md`) and `STUDENT_AUTH_TASKS.md` — **already moved** to `_deprecated/` by a prior session (confirmed on disk). No action needed; `.wolf/anatomy.md` is just stale here (still lists them under `./`). Worth a `anatomy.md` rescan.

## Needs human judgment

- **`rules_backup/`, `rules2_backup/`** — hold `v7` grammar / `v2` reading rule docs. Root-level `rules_agent_dsat_grammar_ingestion_generation_v8.md` and `rules_agent_dsat_reading_v3.md` are the confirmed-live versions (referenced directly in `backend/app/prompts/generate_prompt.py`, `review_prompt.py`, `annotate_prompt.py`, `backend/app/config.py`). These backups are older, superseded versions — candidates for `_deprecated/` (which already holds v1-v6 grammar / v1 reading), but confirm nothing still branches on v7/v2 before moving.
- **`rules_modularize/`, `rules_refactor/`** — both are unwired sandbox/experiment directories (a modular-decomposition draft and a "corrected rules docs" sandbox added 2026-08-02 per recent commit `8190a6d`). Neither is imported by `backend/app/prompts/*`. Not clearly dead (recent, deliberate work) but not live either — ask whether this work is still active or ready to fold in/archive.
- **`admin_dashboard_tasks.md`** — 0/87 checkboxes marked done in this file specifically, but `admin_dashboard_plan.md` (the designated "living plan" per memory) shows recent unfinished dashboard-grid work (drag/resize/iPad phase). Likely still an active plan, not stale — don't archive without confirming with the living plan owner.
- **`archive/`, `archive_generated/`, `generated_test/`** (88K / 856K / 484K) — names suggest these are already intentional archives of generated-question test runs (`claude/`, `kimi/`, `gpt5_5/` subdirs). Not referenced by backend code, but likely kept on purpose as generation-quality samples. Confirm before touching.
- **`analysis/`** (16MB) — mixes `analysis/v8/subpattern_drafts/` (in-progress grammar rule drafting, tiered by PT-example coverage — looks active) with `analysis/calibration/` (empty) and `analysis/ingestion/`. Don't bulk-archive; the v8 subpattern drafts look live.
- **`.worktrees/concept-quick-pick/`, `.worktrees/stimulus-type-picker/`** and 4 stale `.claude/worktrees/agent-*` dirs (all pinned at commit `373390b`, same hash, likely from one abandoned multi-agent run) — these are git worktrees, not repo-tracked files, but they're consuming disk and cluttering `.wolf/anatomy.md`'s index (contributes ~15 of the 1244 tracked-file entries). Worth `git worktree remove` on the 4 agent-* ones if that work is abandoned — check `git log` on each branch first.
- **`e2e/oauth-live.mjs`** — the one file in `e2e/`. OAuth shipped, but this may still be a useful live-auth smoke test; not referenced by any script/CI config found. Confirm if still run manually before archiving.
- **`tools/marker_worker/`** — has its own `.venv`/`uv.lock`; not referenced from `backend/` or `docker-compose.yml`. Possibly a standalone utility invoked manually. Confirm usage before touching.

## Not touching — confirmed still live

- `local_object_store/` (5.6GB) — actively mounted in `docker-compose.yml` (`OBJECT_STORAGE_LOCAL_ROOT`) and referenced in `backend/app/config.py`. This is the runtime asset store (OCR artifacts, page renders, stimulus assets), not clutter.
- `litellm/config.yaml` — mounted by the `litellm` compose service (`--profile llm`).
- `scripts/` — actively used utility scripts (backup, vocab checks, reannotation, v8 tooling).
- `vocabulary/`, `docs/`, `TESTS/`, `MATH/` — live taxonomy/docs/test-source/math-ontology directories, all referenced from backend config or CLAUDE.md.
- Root `rules_agent_dsat_grammar_ingestion_generation_v8.md`, `rules_agent_dsat_reading_v3.md`, `rules_agent_dsat_review_v1.md` — confirmed live via direct references in 4 backend prompt/config files.
- `APP/STUDENT_APP_REDUX/`, `APP/ADMIN_APP/` — the two canonical frontends, both built by `docker-compose.yml`.
- `backend/` — live FastAPI app (this audit did not recurse deep inside it per scope; use `codegraph`/`tokensave` for a code-level dead-code sweep there if wanted).
- `__deprecated_code/` and `_deprecated/` — already correctly gitignored/quarantined by a prior session; nothing to do.

## Caveat

`.wolf/anatomy.md` (1244-file index) is stale in places — it still lists at least 4 root `.md` files that were already moved to `_deprecated/` in a prior session. Worth re-running the OpenWolf anatomy scan so the index matches disk before relying on it again.
