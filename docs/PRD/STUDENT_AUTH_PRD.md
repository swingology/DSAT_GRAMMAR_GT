# DSAT Student Auth — PRD

**Version:** 1.0  
**Date:** 2026-05-27  
**Depends on:** `STUDENT_FRONTEND_PRD.md` Phase 2 verified  
**Scope:** Replace the test-user stub in `src/lib/auth.ts` with real authentication. No other frontend files change.

---

## Overview

The student practice frontend is built with a deliberate auth seam: `src/lib/auth.ts` exports `getUserToken()` and `getUserId()`. In Phases 1–2 these return hardcoded env vars. This PRD covers replacing that stub with Supabase-backed authentication — OAuth and email/password — while leaving every question, submission, and stats component completely untouched.

---

## Auth Strategies

Both strategies are supported simultaneously. Which one a user picks is their choice at the login screen.

### Option A — Supabase OAuth
- Providers: **Google**, **GitHub** (enabled in Supabase dashboard, no backend code required)
- Flow: browser redirect → Supabase handles identity → redirect back with session
- Zero credential storage on our side

### Option B — Supabase Email/Password
- Standard `signUp` / `signInWithPassword` flow via Supabase JS client
- Password reset via Supabase's built-in email flow (no custom implementation needed)

---

## Backend Auth Integration

The existing `student_auth.py` router provides the bridge between a Supabase identity and a DSAT `user_token` UUID:

| Endpoint | Purpose |
|----------|---------|
| `POST /auth/signup` | Creates a new `User` row; returns `user_token` + `user_id` |
| `POST /auth/login` | Fetches existing `User` by Supabase identity; returns `user_token` + `user_id` |
| `POST /auth/refresh` | Refreshes the backend JWT if used |
| `GET /auth/me` | Returns current user profile |

**The flow on first login:**
1. Supabase issues a session (JWT with `sub` = Supabase user ID)
2. Frontend calls `POST /auth/login` with the Supabase JWT in the `Authorization` header
3. Backend looks up or creates the `User` row keyed to that Supabase identity
4. Backend returns `{ user_token: "<uuid>", user_id: <int> }`
5. Frontend stores both in `localStorage` under `dsat_user_token` / `dsat_user_id`
6. `auth.ts` reads from `localStorage` for all subsequent API calls

**No backend code changes required.** The `student_auth.py` endpoints already exist.

---

## What Changes in the Frontend

| File | Change |
|------|--------|
| `src/lib/auth.ts` | Replace stub with Supabase session + localStorage lookup |
| `src/lib/supabase.ts` | New file — Supabase client singleton |
| `src/pages/LoginPage.tsx` | New file — login UI |
| `src/components/ProtectedRoute.tsx` | New file — redirect unauthenticated users |
| `src/App.tsx` | Add `/login` route + wrap protected routes |
| `.env` | Add `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY`; remove test user vars |

**Zero changes to:** `QuestionCard`, `SessionSetup`, `SessionComplete`, `StatsPanel`, `api/questions.ts`, `api/stats.ts`, `types/index.ts`.

---

## Login Screen

Single page at `/login`:

- App name / logo
- "Continue with Google" button
- "Continue with GitHub" button
- Divider: "or"
- Email input + Password input
- "Sign in" button
- "Don't have an account? Sign up" toggle (reuses the same form, calls `signUp`)
- Error message area (wrong password, email already exists, etc.)

No password-strength UI, no email verification UI — Supabase handles these via its dashboard config and email templates.

---

## Session Lifecycle

| Event | Action |
|-------|--------|
| Login success | Store `dsat_user_token` + `dsat_user_id` in `localStorage` |
| App load | Check `supabase.auth.getSession()` — if no session, redirect to `/login` |
| Token expiry | Supabase auto-refreshes; no frontend handling needed |
| Logout | `supabase.auth.signOut()` + clear `localStorage` + redirect to `/login` |

---

## What is NOT in Scope

- Admin authentication (separate system, API-key based)
- Email verification flow UI (Supabase handles via email; user clicks link)
- Password reset UI (Supabase handles via email; user clicks link)
- Multi-factor authentication
- Any backend changes

---

## Success Criteria

- [ ] Unauthenticated users cannot reach `/` or `/stats` — redirected to `/login`
- [ ] Google OAuth login completes and user lands on `/`
- [ ] GitHub OAuth login completes and user lands on `/`
- [ ] Email/password signup creates a new user; subsequent login retrieves same `user_token`
- [ ] Stats are user-specific: two different logged-in users see their own stats
- [ ] Logout clears session; navigating to `/` sends user back to `/login`
- [ ] All Phase 1 and Phase 2 behavior is unchanged for authenticated users
- [ ] Test user env vars (`VITE_TEST_USER_TOKEN`, `VITE_TEST_USER_ID`) are removed
