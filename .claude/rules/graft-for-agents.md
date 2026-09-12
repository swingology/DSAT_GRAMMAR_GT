# Graft for spawned agents/subagents

This repo's graft reminders (`[graft] starting points...`) are injected by
`SessionStart`/`UserPromptSubmit` hooks in `.claude/settings.json`. Those
hooks fire for the main interactive session only — a subagent spawned via
the `Agent` tool does NOT automatically receive them.

**When spawning any Agent/Task for this repo**, put graft usage directly in
the task prompt — don't assume the subagent will reach for it on its own:

- "Use `graft ask \"<task>\" --source` to locate the relevant code before
  grepping or reading files."
- For refactors/renames: "Run `graft callers <symbol> --depth all` first to
  map every connected file."
- For unfamiliar areas: "Use `graft skeleton <file>` instead of reading a
  file whole when you just need its API."

This applies to every subagent type (general-purpose, Explore, Plan,
studio-coach-orchestrated agents, etc.) and to `Workflow`-spawned agents —
none of them inherit the hook-injected reminder.
