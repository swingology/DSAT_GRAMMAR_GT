# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Python Environment

Always use `uv venv` to create and manage Python virtual environments when running Python scripts in this repository. Do not use `python -m venv` or `virtualenv` directly; prefer `uv venv` for consistency.

## Official Test Source

The canonical set of official DSAT verbal practice tests is:

```
TESTS/DATA_SRC/2025-2026 Tests Answers/Practice Tests/DIVIDED/VERBAL/
```

This directory contains the split module PDFs (mod01/mod02) for Tests 1, 6–11. Use this as the authoritative source when ingesting official verbal questions.
