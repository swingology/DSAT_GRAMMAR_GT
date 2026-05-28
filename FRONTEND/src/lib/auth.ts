/**
 * Auth seam — the only file that changes between dev and prod auth.
 *
 * DEV MODE  (Phase 1-2): set VITE_TEST_USER_TOKEN and VITE_TEST_USER_ID in .env
 *   → both getters return those values immediately, no login needed
 *
 * PROD MODE (Phase 3): remove those env vars, add Supabase.
 *   → getters read localStorage (populated by the Supabase auth flow in auth.ts)
 *   → getters become async (Promise<string>); update call sites in api/ to await them
 *
 * Nothing outside this file changes between phases.
 */

function devToken(): string | null {
  return import.meta.env.VITE_TEST_USER_TOKEN || null;
}
function devId(): string | null {
  return import.meta.env.VITE_TEST_USER_ID || null;
}

export function getUserToken(): string {
  const token = devToken() ?? localStorage.getItem("dsat_user_token");
  if (!token) throw new Error("Not authenticated — set VITE_TEST_USER_TOKEN or log in");
  return token;
}

export function getUserId(): string {
  const id = devId() ?? localStorage.getItem("dsat_user_id");
  if (!id) throw new Error("Not authenticated — set VITE_TEST_USER_ID or log in");
  return id;
}

export function isDevMode(): boolean {
  return !!devToken();
}

export function clearAuth(): void {
  localStorage.removeItem("dsat_user_token");
  localStorage.removeItem("dsat_user_id");
}
