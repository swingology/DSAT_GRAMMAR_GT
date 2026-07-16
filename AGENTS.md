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

# [DSAT_REDUX_MD] recent context, 2026-07-16 1:24am PDT

Legend: 🎯session 🔴bugfix 🟣feature 🔄refactor ✅change 🔵discovery ⚖️decision 🚨security_alert 🔐security_note
Format: ID TIME TYPE TITLE
Fetch details: get_observations([IDs]) | Search: mem-search skill

Stats: 50 obs (16,416t read) | 242,490t work | 93% savings

### Jul 13, 2026
S9 Investigate and test the "add user" action through the DSAT_REDUX_MD admin dashboard, which had a reported issue (Jul 13, 1:02 PM)
80 1:20p 🟣 Admin App Phase 3 Production Build Passes — 882KB Bundle, No Errors
81 " 🔵 Dev Stack Not Running — Backend and Both Apps Need to Be Started for Phase 4 QA
82 1:22p 🔵 Dev Stack Uses Podman Compose — Backend on Port 8002, Frontend on 5174 (Not 8000/5173)
83 " 🔵 Dev Stack Port Mapping Confirmed — Internal 8000/5173/5432 Map to External 8002/5174/5437
84 " 🔵 Port 5174 Serves Student App — Admin App Not in Compose Stack
85 1:23p 🔵 Admin App vite.config.ts Proxies to localhost:8000 — Needs VITE_BACKEND_ORIGIN=http://localhost:8002 for Dev Stack
86 " 🔵 Admin API Key for Dev Stack is "admin-test-key" — Not Set in Admin App .env
87 " 🔵 Backend Auth QA Shows 500 on /users with Admin API Key — Possible DB Issue in Dev Stack
88 " 🔵 Backend 500 on /users Caused by Missing DB Schema — "relation users does not exist"
89 1:24p 🔴 Dev Stack DB Migrations Run — 33 Migrations Applied, Schema Now Ready
90 " 🔵 Backend Fully Operational After Migration + Restart — Admin Seed Created, /users Returns 200
91 " 🟣 Admin App .env Created for Phase 4 QA — Three Required Vars Set
92 1:25p 🔵 Backend JWT Lifecycle QA Passes With One Exception — Old Refresh Token Reuse Returns 200 Instead of 401
93 " 🔵 Refresh Token Rotation Confirmed Working — Previous Test Was False Positive Due to Race Condition
94 " 🔵 POST /api/auth/login Requires Email Not Username — Login Schema Takes {email, password}
95 " 🔵 Refresh Token Rotation Definitively Confirmed — Old Token 401, New Token 200
### Jul 15, 2026
96 9:29a 🔵 Admin Dashboard User-Add Investigation: Buglog Review
97 " 🔵 Admin App Project Structure and User Management API
98 " 🔵 Bug-777/778: Backend /users and /admin Routes Missing /api Prefix
99 " 🔵 Dev Stack Running: Backend on :8002, Admin Frontend on :5174
100 9:37a 🔵 DSAT_REDUX_MD Admin Dashboard Infrastructure State
101 9:38a 🔵 POST /users Endpoint: Auth and Schema for Admin User Creation
102 " 🔵 admin_required Auth: Dual-Mode — Legacy API Key or Bearer JWT with admin Role
103 " 🔵 Backend POST /users Works Directly — Admin App Port 5173 Returns 502
104 " 🔵 Root Cause: Port 5173 Vite Instance Has No Env Vars — Port 5175 Is the Correctly Configured Instance
S12 Session wrap-up: add-user admin dashboard investigation completed; user asked "is the server running?" as final check (Jul 15, 9:39 AM)
105 9:41a 🔴 Killed Stale Admin App Vite Instance on Port 5173
106 " 🔵 APP/ADMIN_APP/.env Missing VITE_BACKEND_ORIGIN — Must Be Set as Shell Env at Launch
107 " 🔴 Persisted VITE_BACKEND_ORIGIN to APP/ADMIN_APP/.env to Prevent 502 Recurrence
108 9:42a 🔴 Add-User Flow Verified End-to-End via Admin Dashboard Proxy on Port 5175
109 9:46a ✅ Bug-784 Logged in Project Buglog — Admin Dashboard Add-User 502 via Stale Vite Process
110 9:47a ✅ Bug-784 Documented in DEBUG_LOG.md and .wolf/memory.md
S10 Investigate and fix the "add user through admin dashboard" failing action — root cause was a stale Vite process on port 5173 with no VITE_BACKEND_ORIGIN set (Jul 15, 9:47 AM)
S11 User asked "is the server running?" — a quick status check following the completed add-user bug fix session (Jul 15, 9:47 AM)
S13 User asked "is the server running?" — confirmed full dev stack is healthy across all services (Jul 15, 9:48 AM)
S14 Google OAuth admin login investigation — confirmed working for jbyun76@gmail.com; identified multi-account picker confusion and potential frontend session issue (Jul 15, 10:02 AM)
111 10:03a 🔵 Google OAuth Only in student_auth.py — Admin Auth Uses admin_seed_email Config
112 10:04a 🔵 Google OAuth Login is Pre-Registration Only — Never Creates Accounts
113 " 🔵 Current User DB State — Admin Account Confirmed, 8 Total Users
114 " 🔵 Google OAuth Endpoint Mounted at /api/auth/google — Admin App src/ Not at Expected Path
115 10:07a 🔵 Admin App Google OAuth Flow: GIS Popup → credential → POST /auth/google → JWT
116 " 🔵 Admin LoginPage.tsx: GIS Button Renders Only When VITE_GOOGLE_CLIENT_ID Is Set
117 " 🔵 Admin App :5175 Has All Three VITE_ Vars Correctly Injected — Google Login Is Ready
118 10:08a 🔵 Backend Logs Confirm Google OAuth Working — Admin Login Succeeded, Two Unregistered Emails Rejected
119 " 🔵 chrisbyun@gmail.com 401 Was Correct — User CB17 Added to DB After Failed Login Attempt
S15 Google OAuth admin login investigation — confirmed jbyun76@gmail.com works as admin; user confirmed CB17/chrisbyun stays as student; no DB changes needed (Jul 15, 10:08 AM)
S16 Google OAuth "Access blocked / Authorization error" — identified as Google Cloud Console OAuth consent screen in Testing mode blocking non-listed accounts (Jul 15, 10:10 AM)
S17 Create jeenbyun@gmail.com admin user and fix Google OAuth "access blocked" issue (Jul 15, 10:11 AM)
120 10:12a 🔵 PATCH /users/{user_id} Supports Role Changes — Path to Promote chrisbyun@gmail.com to Admin
121 10:17a 🔵 Admin App Vite Process Launch Details
122 " ✅ Admin Vite App Restarted to Pick Up New .env
123 " 🔵 502 Persists After Admin App Restart — Proxy Still Broken
124 " 🔵 New Vite Process (PID 1045436) Also Missing VITE_BACKEND_ORIGIN
125 10:18a 🔴 vite.config.ts Fixed to Use loadEnv for Proxy Target
126 10:20a 🔴 Admin App Proxy 502 Bug Fully Resolved
127 " 🔵 VITE_GOOGLE_CLIENT_ID Confirmed in Restarted Admin App Bundle
128 " ✅ bug-785 Logged in .wolf/buglog.json and memory.md
129 10:21a 🔵 cerebrum.md Do-Not-Repeat Section Contains Vite-Adjacent Warning
S18 Restart admin app cleanly and fix persistent 502 proxy bug (vite.config.ts loadEnv fix) (Jul 15, 10:21 AM)

Access 242k tokens of past work via get_observations([IDs]) or mem-search skill.
</claude-mem-context>