# Google OAuth Login — Task List

**PRD:** `.scratch/oauth-login/PRD.md` (branch `oauth_feature`, commit `ffe255e`)
**Supersedes:** `STUDENT_AUTH_TASKS.md` (old Supabase-based plan — do not follow it; we go direct to Google, no Supabase)

**Architecture in one line:** GIS popup flow → `POST /api/auth/google` verifies the Google ID token → issues the *existing* JWT access/refresh pair. Pre-registered emails only. Legacy API keys and `user_token` params keep working in parallel.

---

## Phase 0 · Google Cloud setup — ✅ COMPLETE (2026-07-07)

- [x] O-00a · Create OAuth client (Web application) under jbyun76@gmail.com
  - Client ID: `721127096332-4b5fgqs0dfn8g414gnehrnbrb85q22r4.apps.googleusercontent.com` (public — safe to commit)
  - Client secret: **not used anywhere** — never copy it into the repo or env files
- [x] O-00b · Register authorized JavaScript origins (no redirect URIs — popup flow needs none):
  - `http://localhost:5173` (student app)
  - `http://localhost:5174` (admin app)
  - `http://localhost`
  - `https://jb-2410.tail0cecc1.ts.net:8443`
- [x] O-00c · **Verify origins accepted by Google** — done via headless Chrome on the server
  (playwright-core + `/usr/bin/google-chrome-stable`):
  - `http://localhost:5173` → ✅ button renders, no origin error
  - `https://jb-2410.tail0cecc1.ts.net:8443` → ✅ button renders, no origin error
  - `http://127.0.0.1:5173` negative control → ❌ rejected (proves test validity)
  - Client ID confirmed live against Google's token endpoint
- [ ] O-00d · Consent screen: confirm publishing status is **In production** (if left in
  Testing mode, every student Gmail must also be added as a Test user or sign-in fails)

**Known env quirk (not blocking):** the Windows laptop's Chrome cannot resolve `*.ts.net`
(secure-DNS bypasses MagicDNS). Test GSI origins with server-side headless Chrome, not the
laptop browser. Fix later via Chrome secure-DNS setting or a Windows hosts-file entry.

---

## Phase 1 · Backend — ✅ COMPLETE (2026-07-13)

- [x] O-01 · Mount the existing auth router — registered in `backend/app/main.py`.
  **Verified:** `GET /api/auth/me` → `401` (was `404`); all 6 `/api/auth/*` routes mounted.
- [x] O-02 · `google_oauth_client_id` setting added to `backend/app/config.py` (env-overridable)
- [x] O-03 · `google-auth[requests]` added to `backend/pyproject.toml` — **the `[requests]`
  extra is required**: `google.auth.transport.requests` raises ImportError without it
- [x] O-04 · `POST /api/auth/google` in `student_auth.py` — verifies via `app/google_oauth.py`,
  looks up User by verified email, generic 401 on unknown email, 403 on inactive, rotates refresh
- [x] O-05 · `user_token` added to `StudentMeResponse`
- [x] O-06 · `admin_required` upgraded: legacy `X-API-Key` **or** admin Bearer JWT.
  **Kept its `str` return type** — 6 call sites persist it to the audit trail
  (`rejected_by_admin_token`, `admin_token=`), so JWT auth returns `"jwt:<email>"`.
  A valid non-admin JWT 403s rather than falling through to the key check.
- [x] O-07 · Idempotent admin seed in the `main.py` lifespan — creates or promotes
  `admin_seed_email` to active admin; never crashes startup if the DB is down
- [x] O-08 · Backend tests — `backend/tests/test_google_auth.py`, 17 passing. Also covers the
  O-07 seed (create / promote / idempotent), which otherwise fails silently by design.
  (run: `cd backend && ./.venv-jb/bin/python -m pytest` — venv is at `backend/.venv-jb`)

**Extra hardening beyond the PRD:** the verifier pins the issuer and rejects
`email_verified: false` — without that check, an unverified Google account could claim a
registered student's address.

**Suite status:** 1084 passed. The 6 failures (`test_config`, `test_student_retrieval`,
`test_vocab_sync`) are pre-existing — confirmed identical on a clean tree, unrelated to OAuth.

## Phase 2 · Student app (5173) — ✅ COMPLETE (2026-07-13)

- [x] O-09 · `VITE_GOOGLE_CLIENT_ID` in `.env.example`; GIS script loaded on demand by
  `src/auth/useGoogleScript.ts` (single shared loader, no `index.html` `<script>` tag)
- [x] O-10 · `src/auth/AuthContext.tsx` + `src/auth/authStore.ts`. The store is a **plain
  module, not a hook** — `api/client.ts` must read tokens outside React. Silent refresh on
  401 with a single retry; concurrent 401s share one in-flight refresh; a dead refresh
  clears the store, which the context observes via `subscribe()` and drops to the login page.
- [x] O-11 · `src/pages/LoginPage.tsx` — the only unauthenticated route
- [x] O-12 · `src/auth/RequireAuth.tsx` wraps every existing route in `App.tsx`
- [x] O-13 · `client.ts` sends the real JWT as `Authorization: Bearer` (it previously sent
  the `user_token` there, which the backend never read). `user_token` now comes from
  `/api/auth/me` via `getUserToken()`.
- [x] O-14 · `src/components/UserMenu.tsx` in the dashboard header — calls `/api/auth/logout`,
  clears local state, and `queryClient.clear()`s the cache

**The load-bearing detail in O-13:** `user_token` was read into **module-scope consts in 8
files**, i.e. evaluated at import time, before a login can exist. Swapping the right-hand
side would have kept the bug — every read had to move to render/fetch time
(`getUserToken()` at the call site). The legacy `VITE_TEST_USER_TOKEN` → `localStorage`
fallback is preserved inside `getUserToken()`, so scripts and existing tests still work.

**Login needs two calls, not one:** `POST /api/auth/google` returns only
`{access_token, refresh_token, expires_in}` — no `user_token`. Only `GET /api/auth/me`
carries it, and every legacy endpoint needs it. Skipping `/me` breaks the whole app.

**Session bootstrap:** on mount the context re-validates a stored session against `/me`
(status `bootstrapping`), so a page refresh doesn't bounce a signed-in student to `/login`.

**Tests:** `src/auth/__tests__/auth.test.tsx`, 8 passing — Bearer header, refresh-and-retry,
dead-refresh clears session without looping, guard redirect, session restore on load.

**Suite status:** 162 passed / 16 failed. All 16 failures are **pre-existing** — verified
identical on a clean tree (`grammar-page`, `GrammarPractice`, `PracticeCard`,
`PracticeTestCard`, `PracticeTestPage`, `keyColors`). None touch auth.

**Fixed en route (was blocking any test run):** `vitest.config.ts` now sets `pool: 'forks'`.
Vite dep re-optimization segfaults the default worker-thread pool on this Linux box, so a
cold cache — e.g. adding `src/auth/` — took the entire run down with `Segmentation fault`
before a single test executed. Same class as the `optimizeDeps.bundler: 'esbuild'` pin
already in `vite.config.ts`.

## Phase 3 · Admin app (5174) — ✅ COMPLETE (2026-07-13)

- [x] O-15 · Same login pattern as student app (shared shape, port the AuthContext)
- [x] O-16 · Post-login role check: non-admin Google accounts see "not an admin" + sign-out only
- [x] O-17 · `client.ts`: switch from hardcoded `ADMIN_TOKEN` to Bearer tokens
  (API key stays valid backend-side for scripts)

**Ported from the student app:** `src/auth/{authStore.ts,useGoogleScript.ts,AuthContext.tsx,RequireAdmin.tsx,google.d.ts}`
+ `src/pages/LoginPage.tsx`. `authStore` is a plain module (not a hook) so `client.ts` can read
tokens outside React; `AuthContext` subscribes to it and mirrors into React state. `App.tsx`
wraps every admin route in `RequireAdmin` under `AuthProvider`, with `/login` as the only
unauthenticated route.

**Role gate (O-16):** the backend issues JWTs to *any* registered user, so the role check is a
frontend concern. `RequireAdmin` shows a spinner while `bootstrapping` (no login flash on
reload), redirects to `/login` when `anonymous`, and renders an explicit "Not an admin account"
screen with sign-out as the only exit for a signed-in non-admin — instead of a dashboard where
every `/admin` call would 403.

**Bearer auth (O-17):** `client.ts` sends `Authorization: Bearer <jwt>` on every call, with
silent refresh on 401 (one in-flight refresh, no recursion — `refreshTokens` uses bare `fetch`),
and `clearSession()` on a dead refresh so `AuthContext` bounces to login. Legacy
`VITE_ADMIN_TOKEN` still sent as `X-API-Key` so scripts keep working; both headers are safe
because `admin_required` checks Bearer first.

**Verification (re-run this session, not just prior observations):**
- `tsc -p tsconfig.app.json` → 0; `tsc -b` → 0 (after clearing a stale `node_modules/.tmp`
  incremental cache that segfaulted the `-b` orchestrator — not a code issue)
- `vite build` → ✓ 882.98 kB bundle, built in 572ms
- `eslint src` → 11 errors, all pre-existing `no-explicit-any` in legacy `adminApi` /
  `DataManagement` / `UserManagement`. **Zero new errors.** (Fixed one new
  `no-useless-assignment` in `client.ts`'s error-detail parser — removed a redundant
  `detail = ''` in the `catch` that duplicated the init.)

## Phase 4 · Live QA

- [x] O-18 · Full pass on dev stack: sign-in, guarded routes, silent refresh, logout,
  unknown-email rejection, admin role rejection — both apps (hermetic e2e
  `e2e/oauth-live.mjs`, 9/9 green, 2026-07-13)
- [ ] O-19 · QA from a tailnet device via `https://jb-2410.tail0cecc1.ts.net:8443`

  **Server-side plumbing verified 2026-07-13 (no tailscale change needed):**
  `tailscale serve` already maps `:8443 → localhost:5174`, and **5174 is the student
  app** (`<title>Student App Redux</title>`), not the admin app. The earlier note here
  was wrong — 5174 had been mislabeled "admin". Confirmed over the live tailnet URL:
  - `GET https://…:8443/login` → student login page renders, `window.google.accounts.id`
    present, **no GIS origin error** (origin `https://…:8443` was registered in O-00b)
  - `GET https://…:8443/api/auth/me` → `401` (Vite `/api` proxy reaches the backend,
    same status as a direct `localhost:8002` hit)
  - `:8444 → localhost:5175` is a second admin-app instance; the student-facing port is
    `:8443`.

  **Remaining (manual, requires a real tailnet device + a registered Google account):**
  on a phone/laptop on the tailnet, open `https://jb-2410.tail0cecc1.ts.net:8443`,
  sign in with a Google account whose email is in the `users` table, and confirm the
  dashboard loads + Sign-out works. Only the seeded admin (`jbyun76@gmail.com`) is
  guaranteed present; a real **student** email must be inserted first (e.g.
  `psql … -c "insert into users(email,role,is_active) values('<student@gmail>', 'student', true)"`)
  or the sign-in will hit the generic "No DSAT account" 401.
