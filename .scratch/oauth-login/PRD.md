# PRD: Google OAuth Login for Student and Admin Apps

Status: ready-for-agent
Created: 2026-07-07
Branch: `oauth_feature`

## Problem Statement

Neither the student app nor the admin app has a real login. The student app ships a
static API key baked into its build and identifies the student with a `user_token`
value pulled from env vars or localStorage; the admin app ships a hardcoded admin API
key. Anyone who obtains a URL (localhost or the Tailscale hostname) gets full access
with no identity, no accountability, and no way to revoke a single person. Students
cannot sign in as themselves, and the tutor cannot tell who generated which practice
data without manually managing opaque tokens.

## Solution

Add "Sign in with Google" to both apps. A login page in each app uses the Google
Identity Services (GIS) popup flow to obtain a Google ID token, which the backend
verifies and exchanges for the JWT access/refresh tokens the backend already knows how
to issue. Access is restricted to **pre-registered emails only**: the tutor creates a
student's account (with their Gmail address) in the admin User Management page first;
an unknown Google account is politely rejected. The admin app additionally requires
the signed-in user to have the `admin` role.

The legacy auth (static `X-API-Key` headers and `user_token` params) keeps working in
parallel. Nothing existing breaks; the login becomes the front door for humans while
scripts and tests continue using keys until a future cleanup.

## Google OAuth Client Setup (one-time, manual)

These steps happen in the Google Cloud console and cannot be automated. Budget ~15
minutes. The person doing this signs in with the Google account that will own the
OAuth client (the tutor's account).

1. **Create / select a project.** Go to <https://console.cloud.google.com/>, open the
   project picker (top bar), and create a new project, e.g. `dsat-tutoring`. No
   billing account is required for OAuth.

2. **Configure the consent screen (branding).** Navigate to **APIs & Services →
   OAuth consent screen** (newer consoles label this **Google Auth Platform →
   Branding**).
   - **User type:** External (Internal is only available on Workspace accounts).
   - **App name:** e.g. `DSAT Practice`. **Support email:** the tutor's Gmail.
   - **Scopes:** none need to be added manually — Sign in with Google uses only the
     non-sensitive `openid`, `email`, and `profile` scopes.
   - **Publishing status:** push the app to **In production** (button on the consent
     screen page). With only non-sensitive scopes this does NOT trigger Google's
     verification review. If instead the app is left in **Testing** mode, every
     student's Gmail must ALSO be added under **Test users** (limit 100) or their
     sign-in fails with `access_denied` — production mode avoids maintaining that
     second list.

3. **Create the OAuth client ID.** Navigate to **APIs & Services → Credentials →
   Create Credentials → OAuth client ID**.
   - **Application type:** Web application. **Name:** e.g. `dsat-web`.
   - **Authorized JavaScript origins** — add every origin the apps are served from,
     scheme + host + port exactly:
     - `http://localhost:5173` (student app dev server)
     - `http://localhost:5174` (admin app dev server)
     - `https://<node>.<tailnet>.ts.net:8443` (student app via `tailscale serve`)
     - any other Tailscale origin the admin app will be served from
   - **Authorized redirect URIs:** leave empty. The GIS popup flow never redirects;
     it only checks JavaScript origins.
   - Click Create and copy the **Client ID** (ends in `.apps.googleusercontent.com`).
     The client *secret* is not used anywhere in this design — the backend verifies
     ID-token signatures against Google's published public keys, so the secret should
     not be copied into the repo or env files at all.

4. **Distribute the client ID** (it is public, not a secret): set it in the backend
   settings (new `google_oauth_client_id` setting, env-overridable) and in both
   frontend builds as a Vite env var so the GIS script can initialize.

5. **Verify the Tailscale origin immediately.** Before any code is written on top of
   it, load a trivial page with the GIS script from the `https://….ts.net:8443`
   origin and confirm the Google button renders and the popup opens. `*.ts.net`
   certificates are real Let's Encrypt certificates, so this is expected to work; if
   the console or popup rejects the origin, the fallback is Google-login on localhost
   plus revisiting how the Tailscale entry point is served — and it is much cheaper
   to learn that on day one.

## User Stories

1. As a student, I want to sign in with my Google account, so that I don't have to remember another password.
2. As a student, I want the app to remember me across visits, so that I don't sign in every time I practice.
3. As a student, I want my practice history, diagnostics, and progress tied to my own identity, so that my dashboard reflects my work and nobody else's.
4. As a student, I want a clear "no account registered for this email" message when I sign in with the wrong Google account, so that I know to contact my tutor instead of assuming the app is broken.
5. As a student, I want to sign out, so that I can safely use a shared or family computer.
6. As a student, I want my session to renew silently in the background while I'm working, so that a practice test is never interrupted by a login screen mid-question.
7. As a student, I want to be sent back to where I was after re-authenticating, so that an expired session costs me nothing.
8. As a tutor (admin), I want to sign in to the admin app with my Google account, so that admin access is tied to my identity instead of a shared key string.
9. As a tutor, I want the admin app to reject Google accounts that aren't admins, so that a student who finds the admin URL sees nothing.
10. As a tutor, I want to pre-register a student by entering their Gmail address in User Management, so that only students I invited can create sessions and data.
11. As a tutor, I want to deactivate a student's account and have their sign-in and existing sessions stop working, so that offboarding is one switch.
12. As a tutor, I want my own admin account seeded automatically on deploy, so that I am never locked out of the system that manages accounts.
13. As a tutor, I want existing scripts, cron jobs, and tests that use API keys to keep working unchanged, so that adding login doesn't break the pipeline tooling.
14. As a student, I want the login page to be the only page I can see while signed out, so that no data or UI leaks before authentication.
15. As a tutor, I want sign-in failures (unknown email, disabled account) to be logged server-side, so that I can see who attempted access.
16. As a developer, I want the Google verification isolated behind a small interface, so that tests can exercise every auth outcome without contacting Google.
17. As a developer, I want the two frontends to share the same auth pattern (context, storage, guard), so that a fix in one app is trivially portable to the other.

## Implementation Decisions

- **Login method:** Google Identity Services **popup** flow (ID token in the browser),
  not the server-side authorization-code flow. No redirect URIs, no client secret, no
  server-held Google tokens. Decided during brainstorming because the app only needs
  identity, never Google API access on the user's behalf.
- **Token architecture unchanged:** the existing JWT layer (access + rotating refresh
  tokens, `role` claim, `/api/auth/*` endpoints) stays the single session mechanism.
  Google is only a new way to *obtain* those tokens.
- **New backend endpoint** `POST /api/auth/google`: accepts the GIS `credential` (ID
  token), verifies signature/audience/expiry against Google's public keys (via the
  `google-auth` package), extracts the verified email, and looks up the user.
  Unknown email → rejection with a friendly, non-enumerating message; inactive user →
  rejected; success → the exact same token response shape as password login, with
  refresh-token rotation.
- **Access policy — pre-registered emails only.** No auto-provisioning, no allowlist
  config. Account creation remains an admin action in User Management. (Decided
  explicitly over "anyone auto-creates" and "config allowlist".)
- **Google identity ↔ User matching is by verified email.** No new columns required;
  the Google `sub` claim is not stored in v1.
- **Admin guard upgraded in place:** the single shared admin dependency learns to
  accept *either* the legacy admin API key *or* a Bearer JWT whose user has the
  `admin` role. Because every admin endpoint uses that one dependency, all ~41
  endpoints gain JWT support with no per-endpoint edits.
- **Legacy auth runs in parallel** (explicit user decision): static student/admin API
  keys and `user_token` params remain valid. Removal is a separate future effort.
- **`/api/auth/me` gains the user's `user_token`** so a logged-in student app can
  populate the legacy `user_token` parameters that the ~25 student endpoints still
  take, instead of reading it from env vars.
- **Frontend auth pattern (both apps):** an auth context that owns tokens + profile
  (persisted in localStorage), a login page as the only unauthenticated route, a
  route guard around everything else, automatic refresh on 401 with a single retry,
  and logout that calls the backend logout then clears local state. The admin app
  adds a role check after login: non-admins are shown "not an admin" and given only
  a sign-out action.
- **Admin seed:** an idempotent startup/seed step ensures `jbyun76@gmail.com` exists
  as an active `admin` user (email configurable in settings).
- **Config additions:** `google_oauth_client_id` in backend settings; a Vite env var
  carrying the same client ID in each frontend.

## Testing Decisions

- Tests assert **external behavior only**: what an HTTP caller observes (status
  codes, token responses, rejection messages), never internals like hashing details
  or which library verified the ID token.
- **Google verification is faked at its seam** — tests inject/monkeypatch the
  verifier interface, never call Google, and never require network.
- **Backend `POST /api/auth/google`** is the primary tested module: valid token for a
  registered active user (returns working access+refresh pair), unknown email,
  inactive user, invalid/expired/wrong-audience credential, and refresh rotation
  behavior matching password login.
- **Upgraded admin dependency** is the second tested module: legacy admin key still
  passes, admin JWT passes, student JWT gets 403, absent credentials get 401 — run
  against a representative admin endpoint.
- **Prior art:** the existing backend pytest suite (run with the project's venv
  python, not `uv run`, per project convention). Follow its async-client fixtures.
- Frontend auth flows are verified by **live QA** through the dev stack (both apps:
  sign-in, guarded routes, refresh, logout, admin role rejection) rather than unit
  tests, matching current frontend test coverage in this repo.

## Out of Scope

- Removing legacy API keys or `user_token` parameters (parallel operation is the
  explicit decision; cleanup is a future PRD).
- Email/password login UI (backend endpoints exist and remain, but no page is built).
- Self-serve signup of any kind, password reset flows, or email sending.
- Other identity providers (Apple, GitHub, etc.).
- Storing Google profile data (avatar, name) or the Google `sub` claim.
- Server-side authorization-code OAuth flow and offline access to Google APIs.
- Multi-tutor/permission tiers beyond the existing `student`/`admin` roles.

## Further Notes

- The OAuth client ID is intentionally public; only ID-token *verification* keys
  (fetched from Google) are involved server-side. There is no secret to leak.
- Sign-in rejections should use one generic message for "unknown email" to avoid
  account enumeration, while the server log records the attempted email for the
  tutor's benefit.
- If Google's console refuses the `ts.net` origin (step 5 of setup), that is a
  blocking discovery for Tailscale-served logins and must be surfaced before frontend
  work proceeds.
- The dev-stack ports (5173/5174/8000) are assumed by the origin list; if ports
  change, the Google console origin list must be updated to match.
