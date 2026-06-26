---
name: start-app
description: Delegate starting the local app/dev stack to a Haiku subagent instead of running it in the main context. Use when the user asks to start, run, launch, or boot the app, the stack, the dev server, the backend, or the frontend — including phrases like "run the stack", "start the app", "/dev-stack", "spin it up", or "bring it up".
---

# start-app

When the user asks to start/run/launch the app or stack, **do not run docker yourself**.
Dispatch a subagent on the **Haiku** model to do it and report back. This keeps the
build/log noise out of the main conversation context.

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

1. cd /home/jb/DSAT_REDUX_MD
2. Run: docker compose up -d --build   (allow up to 10 min; the Dockerfiles may rebuild)
3. Run: docker compose ps --format 'table {{.Name}}\t{{.Service}}\t{{.Status}}\t{{.Ports}}'
   The host ports are defined in docker-compose.yml and are NOT the documented
   defaults — read the actual host->container mappings from `ps` (containers listen
   on 8000 backend / 5173 frontend / 5432 db internally; host ports differ).
4. Health-check using the HOST ports from step 3:
   - backend: curl the mapped host port at /docs, retry up to 15x/3s (it runs
     migrations on startup). Expect HTTP 200. Note: there is no /health endpoint.
   - frontend: curl the mapped host port at /. Expect HTTP 200.
5. Report a compact markdown table: Service | URL | Status. For any container that
   is not "healthy" or any non-200 probe, include `docker compose logs <service>
   --tail 20`.
6. If `docker compose up` itself fails, report the error and stop.
```

## Notes

- Invoking this skill is the user's standing authorization to spawn the subagent.
- Stop/status/logs (`/dev-stack stop|status|logs`) are quick and do NOT need delegation —
  run those directly. This skill is only for **starting** the app.
