# OpenWolf

@.wolf/OPENWOLF.md

This project uses OpenWolf for context management. Read and follow .wolf/OPENWOLF.md every session. Check .wolf/cerebrum.md before generating code. Check .wolf/anatomy.md before reading files.


# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Python Environment

Always use `uv venv` to create and manage Python virtual environments when running Python scripts in this repository. Do not use `python -m venv` or `virtualenv` directly; prefer `uv venv` for consistency.

## Official Test Source

The canonical set of official DSAT verbal practice tests is:

```
TESTS/DATA_SRC/2025-2026 Tests Answers/VERBAL/
```

This directory contains the split module PDFs (`Test_N_digital_sec01_mod01.pdf` / `mod02.pdf`) for Tests 1, 4–11. Use this as the authoritative source when ingesting official verbal questions.

The config setting `official_test_verbal_dir` in `backend/app/config.py` points to this directory and should be used as the default path in all code that references official test PDFs.

## Agent skills

### Issue tracker

Issues live as local markdown files under `.scratch/<feature>/`. See `docs/agents/issue-tracker.md`.

### Triage labels

Default label strings: `needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`. See `docs/agents/triage-labels.md`.

### Domain docs

Single-context repo: one `CONTEXT.md` + `docs/adr/` at the repo root. See `docs/agents/domain.md`.

## graphify

This project has a knowledge graph at graphify-out/ with god nodes, community structure, and cross-file relationships.

Rules:
- For codebase questions, first run `graphify query "<question>"` when graphify-out/graph.json exists. Use `graphify path "<A>" "<B>"` for relationships and `graphify explain "<concept>"` for focused concepts. These return a scoped subgraph, usually much smaller than GRAPH_REPORT.md or raw grep output.
- If graphify-out/wiki/index.md exists, use it for broad navigation instead of raw source browsing.
- Read graphify-out/GRAPH_REPORT.md only for broad architecture review or when query/path/explain do not surface enough context.
- After modifying code, run `graphify update .` to keep the graph current (AST-only, no API cost).
