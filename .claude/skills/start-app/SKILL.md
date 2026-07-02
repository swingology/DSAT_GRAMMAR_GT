---
name: start-app
description: Delegate starting the local app/dev stack to a Haiku subagent instead of running it in the main context. Use when the user asks to start, run, launch, or boot the app, the stack, the dev server, the backend, or the frontend — including phrases like "run the stack", "start the app", "/dev-stack", "spin it up", or "bring it up".
---

# start-app

When the user asks to start/run/launch the app or stack, **do not run docker/podman
commands by hand** — delegate to the canonical `.claude/skills/dev-stack/run.sh` script
and dispatch it via a subagent on the **Haiku** model. This keeps the build/log noise
out of the main conversation context, and guarantees the volume-creation, engine
detection (podman-first), and healthcheck fixes in that script are actually used
instead of re-derived ad hoc each time.

## Workflow

1. Use the **Agent** tool with:
   - `subagent_type: "general-purpose"`
   - `model: "haiku"`
   - `description: "Start dev stack"`
   - `prompt:` the block below (verbatim)
2. Relay the subagent's final report (the service/URL/status table) to the user.
3. If the subagent reports a container unhealthy or a build failure, surface its log
   excerpt and ask the user how to proceed — do not silently retry.

## Subagent prompt (pass verbatim)

```
Start the DSAT local dev stack and report its status. Do NOT edit any files.

1. Run: bash /home/jb/DSAT_REDUX_MD/.claude/skills/dev-stack/run.sh start
   (allow up to 10 min; it builds images, auto-creates the DB volume if missing,
   uses podman if available (falls back to docker), and prints a Frontend/Backend
   API/Database URL summary with the actual host ports when done — read those
   printed URLs rather than assuming fixed port numbers, they can differ from
   docker-compose.yml's current defaults if it's edited later.)
2. If any service didn't come up healthy, run:
   bash /home/jb/DSAT_REDUX_MD/.claude/skills/dev-stack/run.sh status
   and for any unhealthy/non-responding service, get logs with
   `podman compose logs <service> --tail 30` (or `docker compose logs` if podman
   isn't installed) from /home/jb/DSAT_REDUX_MD.
3. Report a compact markdown table: Service | URL | Status, using the ports the
   script actually printed. Include a log excerpt for anything unhealthy.
4. If step 1 itself fails outright (non-zero exit, no summary printed), report the
   full error output and stop — do not attempt manual workarounds.
```

## Notes

- Invoking this skill is the user's standing authorization to spawn the subagent.
- Stop/status/logs (`/dev-stack stop|status|logs`) are quick and do NOT need delegation —
  run those directly (they call the same `run.sh`). This skill is only for **starting**
  the app.
- `run.sh` prefers `podman` explicitly (checked via `command -v`, not a shell alias) so
  it behaves the same whether invoked interactively or from a non-interactive subagent.
