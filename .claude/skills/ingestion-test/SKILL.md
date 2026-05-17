---
name: ingestion-test
description: |
  Run the DSAT official-verbal ingestion pipeline test in a background subagent
  and log every failure to DEBUG_LOG.md. Use when asked to "run the ingestion
  test", "test ingestion", "verify the ingestion fix", or "run the pipeline test".
  Argument: a PDF stem (e.g. "Test_4_digital_sec01_mod01") for one module,
  "full" for the whole 18-PDF batch, or empty to default to Test_1 sec01 mod01.
---

# Ingestion Test Runner

Dispatch a background subagent that starts the API server, runs the ingestion
pipeline against one or more official verbal PDFs, and records every failure in
`DEBUG_LOG.md`. The long poll loop runs in the subagent so it never bloats the
main conversation.

## When invoked

1. Resolve the target from the skill argument:
   - empty → single PDF `Test_1_digital_sec01_mod01.pdf`
   - a `Test_*` stem → that single PDF
   - `full` → the entire batch via `backend/run_full_ingestion.sh`

2. Spawn **one** subagent with the `Agent` tool:
   - `subagent_type`: `general-purpose`
   - `run_in_background`: `true`
   - `description`: `"Run ingestion pipeline test"`
   - `prompt`: the block below, with `<TARGET>` substituted.

3. Tell the user the subagent is running in the background and that you will
   report results — including the new `DEBUG_LOG.md` entry — when it finishes.

4. When the subagent completes, relay: job status, validation-error counts by
   step, whether the `got ['']` option-label cascade is gone, and a pointer to
   the `DEBUG_LOG.md` section it appended.

## Subagent prompt

```
You are running the DSAT ingestion pipeline test, then logging the outcome.

TARGET: <TARGET>

1. Run the test with the bundled runner — a single command that handles
   prerequisites, server start/stop, submission, polling, and DB collection:

     bash /home/jb/DSAT_REDUX_MD/.claude/skills/ingestion-test/run.sh <TARGET>

   It runs up to ~30 min for one module (longer for "full"). Its stdout ends
   with a line `RESULT_JSON:{...}` carrying job_id, status, extracted/created
   counts, and prints validation-error counts by step plus representative
   errors above that line. Do NOT write your own poll loops — just run this.

2. If RESULT_JSON contains an "error" key, report it and stop (prereq failure).

3. Append findings to /home/jb/DSAT_REDUX_MD/DEBUG_LOG.md following
   /home/jb/DSAT_REDUX_MD/.claude/rules/debug-log.md EXACTLY. Read the top of
   DEBUG_LOG.md first to match formatting, then insert ONE new `##` section
   ABOVE the most recent entry:
     ## YYYY-MM-DD - Ingestion Test Run (<TARGET>)
     Report created by: Claude (ingestion-test skill subagent)
     Git branch: `<git rev-parse --abbrev-ref HEAD>`
     Git checkpoint: `<git log --oneline -1>`
     ### Findings
     <one numbered entry per distinct failure step, with Severity, the
      job_id/question affected, and the error message>
   Severity: blocking validation errors failing a whole job = High;
   per-question validating failures = High; question-number / OCR-crosscheck
   warnings = Medium. If the job reached approved/needs_review with zero
   blocking validation errors, still add the section and state the run was
   clean (no findings).

4. Log any genuine bug discovered to /home/jb/DSAT_REDUX_MD/.wolf/buglog.json
   per .wolf/OPENWOLF.md, and append a one-line entry to .wolf/memory.md.

Do NOT edit pipeline source code and do NOT commit anything — test + log only.

Report back: target, job status, extracted-vs-created question counts,
validation-error counts by step, whether the "Option labels must be exactly
{A, B, C, D}, got ['']" cascade appeared, and the DEBUG_LOG.md section you wrote.
```

## Notes

- The skill never edits pipeline code or commits — it runs the test and logs.
- The server loads code from the working tree at startup, so whatever is on disk
  (committed or not) is what gets tested.
- A single module takes 20+ minutes; the full batch takes several hours.
