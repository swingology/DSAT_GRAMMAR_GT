# DSAT Student Auth — Task List

**Prerequisite:** `STUDENT_FRONTEND_TASKS.md` Phase 2 verification checklist must be fully passing before starting any task here.

**Rule:** These tasks touch exactly 6 files. If you find yourself editing a question, stats, or API module, stop — you're in the wrong file.

---

## A-00 · Register `student_auth` router in backend (one-time backend change)

The `student_auth` router exists at `backend/app/routers/student_auth.py` but is **not mounted** in `backend/app/main.py`. Add it before any auth task:

```python
# backend/app/main.py
from backend.app.routers import student_auth          # add this import
# ...
app.include_router(student_auth.router)               # add after existing routers
```

**Verify:** `GET http://localhost:8000/api/auth/me` should return `401` (not `404`).

---

## A-01 · Supabase project setup (manual, outside code)

- Create a Supabase project at supabase.com (or use existing)
- Enable Google OAuth provider: Authentication → Providers → Google → add Client ID + Secret
- Enable GitHub OAuth provider: Authentication → Providers → GitHub → add Client ID + Secret
- Add redirect URL to both OAuth apps: `http://localhost:5173`
- Copy `Project URL` and `anon public key` from Project Settings → API

---

## A-02 · Add env vars and install Supabase client

Add to `frontend/.env`:
```
VITE_SUPABASE_URL=<your-project-url>
VITE_SUPABASE_ANON_KEY=<your-anon-key>
```

Install the client:
```bash
cd frontend && npm install @supabase/supabase-js
```

Do NOT remove `VITE_TEST_USER_TOKEN` / `VITE_TEST_USER_ID` yet — they are removed in A-06.

---

## A-03 · Create `src/lib/supabase.ts`

```ts
import { createClient } from '@supabase/supabase-js';

export const supabase = createClient(
  import.meta.env.VITE_SUPABASE_URL,
  import.meta.env.VITE_SUPABASE_ANON_KEY,
);
```

This is the single Supabase client instance. Import from here everywhere — do not call `createClient` in any other file.

---

## A-04 · Build `<LoginPage>` (`src/pages/LoginPage.tsx`)

Route: `/login`

```tsx
// Structure only — implement with Tailwind classes
export function LoginPage() {
  // state: email, password, mode ('signin' | 'signup'), error

  async function handleOAuth(provider: 'google' | 'github') {
    await supabase.auth.signInWithOAuth({ provider, options: { redirectTo: 'http://localhost:5173' } });
  }

  async function handleCredentials() {
    const fn = mode === 'signup' ? supabase.auth.signUp : supabase.auth.signInWithPassword;
    const { data, error } = await fn({ email, password });
    if (error) { setError(error.message); return; }
    // exchange Supabase session for backend user_token
    await exchangeToken(data.session);
    navigate('/');
  }

  // render: OAuth buttons, divider, email+password form, error area, mode toggle
}
```

`exchangeToken(session)` is a local helper inside this file:
```ts
async function exchangeToken(session: Session) {
  const res = await fetch(`${import.meta.env.VITE_API_BASE_URL}/api/auth/login`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${session.access_token}`,
    },
  });
  if (!res.ok) throw new Error('Backend token exchange failed');
  const { user_token, user_id } = await res.json();
  localStorage.setItem('dsat_user_token', user_token);
  localStorage.setItem('dsat_user_id', String(user_id));
}
```

**Note:** Confirm the exact request shape `POST /api/auth/login` expects by reading `backend/app/routers/student_auth.py` before implementing. It may expect the Supabase JWT in the body rather than the `Authorization` header.

---

## A-05 · Build `<ProtectedRoute>` (`src/components/ProtectedRoute.tsx`)

```tsx
import { useEffect, useState } from 'react';
import { Navigate, Outlet } from 'react-router-dom';
import { supabase } from '../lib/supabase';

export function ProtectedRoute() {
  const [checking, setChecking] = useState(true);
  const [authed, setAuthed] = useState(false);

  useEffect(() => {
    supabase.auth.getSession().then(({ data: { session } }) => {
      setAuthed(!!session && !!localStorage.getItem('dsat_user_token'));
      setChecking(false);
    });
  }, []);

  if (checking) return null; // brief flash before redirect
  return authed ? <Outlet /> : <Navigate to="/login" replace />;
}
```

---

## A-06 · Update `src/lib/auth.ts` (the only change to existing logic)

Replace the entire stub with:

```ts
import { supabase } from './supabase';

export async function getUserToken(): Promise<string> {
  const { data: { session } } = await supabase.auth.getSession();
  if (!session) throw new Error('Not authenticated');
  const token = localStorage.getItem('dsat_user_token');
  if (!token) throw new Error('No user token — complete login');
  return token;
}

export async function getUserId(): Promise<string> {
  const id = localStorage.getItem('dsat_user_id');
  if (!id) throw new Error('No user id');
  return id;
}
```

**After this change:** `getUserToken()` and `getUserId()` return `Promise<string>` instead of `string`. Update all call sites in `api/questions.ts` and `api/stats.ts` to `await getUserToken()` / `await getUserId()`.

---

## A-07 · Update `src/App.tsx` — add routes and ProtectedRoute wrapper

```tsx
<Routes>
  <Route path="/login" element={<LoginPage />} />
  <Route element={<ProtectedRoute />}>
    <Route path="/" element={<PracticePage />} />
    <Route path="/stats" element={<StatsPage />} />
  </Route>
</Routes>
```

Add "Log out" to the nav bar:
```ts
async function handleLogout() {
  await supabase.auth.signOut();
  localStorage.removeItem('dsat_user_token');
  localStorage.removeItem('dsat_user_id');
  navigate('/login');
}
```

---

## A-08 · Handle OAuth callback

Supabase OAuth redirects back to `http://localhost:5173` with tokens in the URL hash. The Supabase client auto-parses these on `createClient`. Add a one-time effect to `App.tsx` or a dedicated `/auth/callback` route to exchange the token immediately after redirect:

```ts
useEffect(() => {
  supabase.auth.onAuthStateChange(async (event, session) => {
    if (event === 'SIGNED_IN' && session) {
      const stored = localStorage.getItem('dsat_user_token');
      if (!stored) {
        // First OAuth login — exchange for backend token
        await exchangeToken(session); // same helper from LoginPage
        navigate('/');
      }
    }
  });
}, []);
```

Move `exchangeToken` to `src/lib/auth.ts` so it can be shared between `LoginPage` and this listener.

---

## A-09 · Remove test user env vars

Only after A-08 is verified working:

- Remove from `frontend/.env`:
  ```
  VITE_TEST_USER_TOKEN=...
  VITE_TEST_USER_ID=...
  ```
- Confirm app still starts and login flow works

---

## A-10 · Auth verification checklist (all must pass)

- [ ] Navigating to `/` without being logged in redirects to `/login`
- [ ] Navigating to `/stats` without being logged in redirects to `/login`
- [ ] "Continue with Google" → OAuth flow completes → lands on `/` with no console errors
- [ ] "Continue with GitHub" → OAuth flow completes → lands on `/` with no console errors
- [ ] Email signup creates a new user; `POST /auth/signup` returns `user_token`
- [ ] Email login on existing user returns the same `user_token` as the signup call
- [ ] Practice drill works identically to pre-auth (Phase 1 smoke test steps still pass)
- [ ] Stats correctly reflect the logged-in user's submissions (not another user's)
- [ ] Log two different users in (different browsers/incognito), each sees only their own stats
- [ ] Log out → `localStorage` cleared → `/login` shown → cannot reach `/` without logging in again
- [ ] `VITE_TEST_USER_TOKEN` env var is absent; app still works

---

## Implementation Order

```
A-00 (register student_auth router in main.py)
  → A-01 (manual Supabase setup)
  → A-02 (install + env)
  → A-03 (supabase.ts)
  → A-04 (LoginPage)
  → A-05 (ProtectedRoute)
  → A-06 (auth.ts replacement + update call sites)
  → A-07 (App.tsx routing)
  → A-08 (OAuth callback handler)
  → A-09 (remove test env vars)
  → A-10 (verification checklist)
```
