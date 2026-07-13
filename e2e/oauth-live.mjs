// Hermetic OAuth end-to-end harness for Phase 4 (O-18).
//
// Uses the SYSTEM Playwright (no per-app install) to drive both the student
// (:5174) and admin (:5173) apps in a real Chromium browser. Google Identity
// Services is stubbed at the page seam (window.google.accounts.id is installed
// before the app boots), and every /api/auth/* call is intercepted at the
// browser network layer (page.route), so no real Google token and no backend
// are required. Each O-18 checklist item maps to one scenario below.
//
// Run:  node e2e/oauth-live.mjs
import { createRequire } from 'node:module'
import fs from 'node:fs'

// --- resolve system playwright -------------------------------------------------
const PW_CANDIDATES = [
  '/home/jb/.npm/_npx/9833c18b2d85bc59/node_modules/playwright',
  '/home/jb/node_modules/.pnpm/playwright@1.61.0/node_modules/playwright',
  '/home/jb/.claude/skills/gstack/node_modules/playwright',
  '/home/jb/nimbalyst/node_modules/playwright',
]
const PW_DIR = PW_CANDIDATES.find((p) => fs.existsSync(p + '/package.json'))
if (!PW_DIR) {
  console.error('FATAL: system playwright not found in any candidate path.')
  process.exit(2)
}
const require = createRequire(import.meta.url)
const { chromium } = require(PW_DIR)

const STUDENT = 'http://localhost:5174'
const ADMIN = 'http://localhost:5173'
const WAIT_MS = 15000

const STUDENT_PROFILE = {
  id: 1, email: 'student@example.com', username: 'student-user', role: 'student',
  user_token: 'stu-uuid-123', is_active: true,
}
const ADMIN_PROFILE = {
  id: 2, email: 'admin@example.com', role: 'admin',
  user_token: 'adm-uuid-456', is_active: true,
}
const TOKENS = { access_token: 'access-e2e-aaa', refresh_token: 'refresh-e2e-bbb' }
const REFRESHED = { access_token: 'access-e2e-ccc', refresh_token: 'refresh-e2e-ddd' }

// Fake GIS installed before the app boots. useGoogleScript sees
// window.google.accounts.id and resolves "ready" immediately; renderButton
// injects a real clickable button so Playwright can drive the callback.
const GIS_STUB = `
;(function () {
  const id = {
    _cb: null,
    initialize(opts) { this._cb = opts && opts.callback ? opts.callback : null; },
    renderButton(el) {
      if (!el) return;
      el.innerHTML = '';
      const b = document.createElement('button');
      b.type = 'button';
      b.id = 'e2e-gis-button';
      b.textContent = 'Sign in with Google';
      b.style.cssText = 'padding:10px 24px;cursor:pointer;border:1px solid #888;border-radius:9999px;font-size:14px;';
      b.addEventListener('click', () => { if (this._cb) this._cb({ credential: 'e2e-fake-credential' }); });
      el.appendChild(b);
    },
    prompt() {}, disableAutoSelect() {}, cancel() {}, storeCredential() {},
  };
  window.google = window.google || {};
  window.google.accounts = window.google.accounts || {};
  window.google.accounts.id = id;
})();
`

// Seed localStorage for the silent-refresh scenario: an expired access token
// plus a still-valid refresh token and a stored profile, so the app tries to
// revalidate /auth/me on mount and hits the 401→refresh→retry path.
function seedScript(seed) {
  return `
;(function () {
  localStorage.setItem('auth.access_token', ${JSON.stringify(seed.access)});
  localStorage.setItem('auth.refresh_token', ${JSON.stringify(seed.refresh)});
  localStorage.setItem('auth.profile', ${JSON.stringify(JSON.stringify(seed.profile))});
})();
`
}

// Per-scenario auth response config, read by the route handler closures.
function newCfg(over) {
  return {
    googleStatus: 200, googleBody: TOKENS,
    meStatus: 200, meProfile: STUDENT_PROFILE,
    meFirstStatus: null, // if set, first /auth/me returns this (then meStatus)
    refreshStatus: 200, refreshBody: REFRESHED,
    logoutStatus: 200,
    meCount: 0,
    ...over,
  }
}

// Intercept every /api/** call hermetically. Auth endpoints read cfg; any other
// /api GET/POST gets a generic 200 so the post-login dashboards don't crash.
function installRoutes(page, cfg) {
  return page.route('**/api/**', async (route) => {
    const req = route.request()
    const url = new URL(req.url())
    const path = url.pathname
    const method = req.method()
    // Pass source modules through to the dev server. The `**/api/**` glob also
    // matches dev-served paths like /src/api/client.ts (and .vite/deps/…);
    // fulfilling those with JSON breaks the app's module graph with a MIME
    // mismatch and nothing boots. API calls (e.g. /api/auth/me) have no file
    // extension, so anything with an extension is a real static asset/module.
    if (/\.[a-z0-9]+$/i.test(path)) return route.continue()
    const j = (status, body) =>
      route.fulfill({ status, contentType: 'application/json', body: JSON.stringify(body) })

    if (path === '/api/auth/google' && method === 'POST') {
      if (cfg.googleStatus === 200) return j(200, cfg.googleBody)
      return j(cfg.googleStatus, cfg.googleBody) // e.g. 401 {detail}
    }
    if (path === '/api/auth/me' && method === 'GET') {
      cfg.meCount += 1
      if (cfg.meFirstStatus !== null && cfg.meCount === 1) {
        return j(cfg.meFirstStatus, cfg.meBody || { detail: 'expired' })
      }
      return j(cfg.meStatus, cfg.meProfile)
    }
    if (path === '/api/auth/refresh' && method === 'POST') {
      if (cfg.refreshStatus === 200) return j(200, cfg.refreshBody)
      return j(cfg.refreshStatus, cfg.refreshBody || { detail: 'invalid' })
    }
    if (path === '/api/auth/logout' && method === 'POST') {
      return j(cfg.logoutStatus, {})
    }
    // TrapSusceptibilityDashboard reads data.total_questions_attempted and
    // data.most_susceptible_traps.length without a null guard, so the generic
    // `[]` catch-all throws a TypeError and unmounts the whole dashboard tree
    // (no error boundary) — taking UserMenu's "Sign out" down with it. Return
    // its empty-state shape so the dashboard stays mounted.
    if (path === '/api/student/trap-susceptibility' && method === 'GET') {
      return j(200, { total_questions_attempted: 0, most_susceptible_traps: [] })
    }
    // Generic catch-all for non-auth /api/* (dashboard data, etc.)
    return j(200, method === 'GET' ? [] : {})
  })
}

async function visible(page, selector, ms = WAIT_MS) {
  await page.waitForSelector(selector, { state: 'visible', timeout: ms })
}
// Substring text wait. Playwright's `text="…"` (quoted) is an EXACT match, which
// fails when the target is a fragment of a longer string (e.g. the backend's
// "No DSAT account is registered for that Google email." rejection, or a
// "Sign out" button that also holds an SVG icon). Use getByText(exact:false).
async function visibleText(page, text, ms = WAIT_MS) {
  await page.getByText(text, { exact: false }).first().waitFor({ state: 'visible', timeout: ms })
}
async function hasText(page, text) {
  return (await page.getByText(text, { exact: false }).count()) > 0
}
function assert(cond, msg) {
  if (!cond) throw new Error(msg)
}

// ---------------------------------------------------------------- scenarios -----
async function guardedRedirect(base, appLabel, ctxFactory) {
  const browser = ctxFactory
  const ctx = await browser.newContext()
  await ctx.addInitScript(GIS_STUB)
  const page = await ctx.newPage()
  await installRoutes(page, newCfg({}))
  await page.goto(base + '/', { waitUntil: 'domcontentloaded' })
  await visible(page, '#e2e-gis-button')
  assert(page.url().includes('/login'), `expected /login redirect, got ${page.url()}`)
  assert(await hasText(page, appLabel), `expected "${appLabel}" heading on login page`)
  await ctx.close()
}

// Identity shown after sign-in differs per app: admin Layout renders the email
// inline; student UserMenu renders the username (email is only a title attr).
// Assert whichever marker the profile carries.
function identityMarker(profile) {
  return profile.username || profile.email
}

async function signInSuccess(base, profile, ctxFactory) {
  const browser = ctxFactory
  const ctx = await browser.newContext()
  await ctx.addInitScript(GIS_STUB)
  const page = await ctx.newPage()
  await installRoutes(page, newCfg({ meProfile: profile }))
  await page.goto(base + '/', { waitUntil: 'domcontentloaded' })
  await visible(page, '#e2e-gis-button')
  await page.locator('#e2e-gis-button').click()
  await visibleText(page, 'Sign out')
  assert(!page.url().includes('/login'), `expected to leave /login, got ${page.url()}`)
  assert(await hasText(page, identityMarker(profile)), `expected identity "${identityMarker(profile)}" in UI`)
  await ctx.close()
}

async function unknownEmailRejected(base, ctxFactory) {
  const browser = ctxFactory
  const ctx = await browser.newContext()
  await ctx.addInitScript(GIS_STUB)
  const page = await ctx.newPage()
  await installRoutes(page, newCfg({
    googleStatus: 401,
    googleBody: { detail: 'No DSAT account is registered for that Google email.' },
  }))
  await page.goto(base + '/login', { waitUntil: 'domcontentloaded' })
  await visible(page, '#e2e-gis-button')
  await page.locator('#e2e-gis-button').click()
  await visibleText(page, 'No DSAT account')
  assert(page.url().includes('/login'), `expected to stay on /login, got ${page.url()}`)
  await ctx.close()
}

async function silentRefresh(base, profile, ctxFactory) {
  const browser = ctxFactory
  const ctx = await browser.newContext()
  await ctx.addInitScript(GIS_STUB)
  await ctx.addInitScript(seedScript({
    access: 'expired-access-token', refresh: 'valid-refresh-token', profile,
  }))
  const page = await ctx.newPage()
  await installRoutes(page, newCfg({
    meProfile: profile,
    meFirstStatus: 401, meBody: { detail: 'expired' },
    refreshStatus: 200, refreshBody: REFRESHED,
  }))
  await page.goto(base + '/', { waitUntil: 'domcontentloaded' })
  await visibleText(page, 'Sign out')
  assert(!page.url().includes('/login'), `expected silent refresh to land off /login, got ${page.url()}`)
  await ctx.close()
}

async function logoutFlow(base, profile, ctxFactory) {
  const browser = ctxFactory
  const ctx = await browser.newContext()
  await ctx.addInitScript(GIS_STUB)
  const page = await ctx.newPage()
  await installRoutes(page, newCfg({ meProfile: profile }))
  await page.goto(base + '/', { waitUntil: 'domcontentloaded' })
  await visible(page, '#e2e-gis-button')
  await page.locator('#e2e-gis-button').click()
  await visibleText(page, 'Sign out')
  await page.getByText('Sign out', { exact: false }).first().click()
  await visible(page, '#e2e-gis-button')
  assert(page.url().includes('/login'), `expected logout to return to /login, got ${page.url()}`)
  await ctx.close()
}

async function adminRoleRejected(ctxFactory) {
  const browser = ctxFactory
  const ctx = await browser.newContext()
  await ctx.addInitScript(GIS_STUB)
  const page = await ctx.newPage()
  await installRoutes(page, newCfg({ meProfile: STUDENT_PROFILE })) // student role on admin app
  await page.goto(ADMIN + '/', { waitUntil: 'domcontentloaded' })
  await visible(page, '#e2e-gis-button')
  await page.locator('#e2e-gis-button').click()
  await visibleText(page, 'Not an admin account')
  assert(await hasText(page, STUDENT_PROFILE.email), 'expected rejected non-admin email on screen')
  await ctx.close()
}

// ------------------------------------------------------------------- runner -----
const SCENARIOS = [
  ['student: guarded route → /login', (b) => guardedRedirect(STUDENT, 'DSAT Practice', b)],
  ['student: sign-in → dashboard', (b) => signInSuccess(STUDENT, STUDENT_PROFILE, b)],
  ['student: unknown-email rejected', (b) => unknownEmailRejected(STUDENT, b)],
  ['student: silent refresh on 401', (b) => silentRefresh(STUDENT, STUDENT_PROFILE, b)],
  ['student: logout → /login', (b) => logoutFlow(STUDENT, STUDENT_PROFILE, b)],
  ['admin: guarded route → /login', (b) => guardedRedirect(ADMIN, 'DSAT Admin', b)],
  ['admin: admin sign-in → dashboard', (b) => signInSuccess(ADMIN, ADMIN_PROFILE, b)],
  ['admin: non-admin → "Not an admin account"', (b) => adminRoleRejected(b)],
  ['admin: unknown-email rejected', (b) => unknownEmailRejected(ADMIN, b)],
]

;(async () => {
  const browser = await chromium.launch({ headless: true })
  const results = []
  for (const [name, fn] of SCENARIOS) {
    const t0 = Date.now ? null : null // Date is fine in plain node script (not a workflow)
    try {
      await fn(browser)
      results.push({ name, pass: true })
      console.log(`  ✅ ${name}`)
    } catch (e) {
      results.push({ name, pass: false, err: e.message })
      console.log(`  ❌ ${name}  — ${e.message}`)
    }
  }
  await browser.close()
  const passed = results.filter((r) => r.pass).length
  const total = results.length
  console.log(`\nPhase 4 (O-18) hermetic e2e: ${passed}/${total} passed`)
  process.exit(passed === total ? 0 : 1)
})().catch((e) => {
  console.error('HARNESS CRASHED:', e)
  process.exit(2)
})