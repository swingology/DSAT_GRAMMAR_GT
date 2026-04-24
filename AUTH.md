# Auth & Database Setup Guide

This document provides step-by-step instructions for setting up Supabase, Supabase Auth, OAuth, and database migrations using the Supabase CLI. All instructions reflect the latest official Supabase documentation as of April 2026.

---

## Table of Contents

1. [Setting Up Supabase](#1-setting-up-supabase)
2. [Setting Up Supabase Auth](#2-setting-up-supabase-auth)
3. [Setting Up Supabase OAuth](#3-setting-up-supabase-oauth)
4. [Setting Up Migrations with Supabase CLI](#4-setting-up-migrations-with-supabase-cli)

---

## 1. Setting Up Supabase

### Prerequisites

- Docker installed and running locally.
- Node.js 20+ if using `npx` or `bunx`.
- A Supabase account (free tier is sufficient).
- Git (recommended for version-controlling the `supabase/` directory).

### Install the Supabase CLI

**macOS (Homebrew):**
```bash
brew install supabase/tap/supabase
```

**Windows (Scoop):**
```powershell
scoop bucket add supabase https://github.com/supabase/scoop-bucket.git
scoop install supabase
```

**Linux:** Download `.apk`, `.deb`, or `.rpm` from the [GitHub releases page](https://github.com/supabase/cli/releases).

**Via npx/bunx (requires Node.js 20+):**
```bash
npx supabase --help
```

> **Critical:** Installing the CLI globally via `npm install -g supabase` is **not supported** and will cause issues.

### Initialize a Local Project

Navigate to your application root and run:
```bash
supabase init
```

This scaffolds a `supabase/` directory containing `config.toml` and other local configuration. Commit this directory to version control.

### Start the Local Stack

```bash
supabase start
```

The first run downloads Docker images, which may take several minutes. Once running, the CLI outputs local credentials:
- **Studio Dashboard:** http://127.0.0.1:54323
- **API URL:** http://127.0.0.1:54321
- **Database:** `postgresql://postgres:postgres@127.0.0.1:54322/postgres`

### Create a Remote Project

1. Go to [supabase.com/dashboard](https://supabase.com/dashboard).
2. Click **New Project**, choose your organization, name the project, and select a region.
3. Save the database password securely.
4. Copy the **Project ID** from the dashboard URL: `https://supabase.com/dashboard/project/<project-id>`.

### Link Local to Remote

```bash
supabase login
supabase link --project-ref <project-id>
```

If the remote project already has schema, pull it locally:
```bash
supabase db pull
```

### Configuration Example

The `supabase/config.toml` file controls local behavior:
```toml
[api]
port = 54321
schemas = ["public", "storage", "graphql_public"]

[db]
port = 54322
major_version = 15

[studio]
port = 54323
```

For CI/CD pipelines, use the official GitHub Action:
```yaml
- uses: supabase/setup-cli@v1
  with:
    version: latest
```

### Common Pitfalls

| Issue | Solution |
|---|---|
| `npm install -g supabase` fails | Use Homebrew, Scoop, or `npx` instead. Global npm installation is unsupported. |
| Docker not running | Start Docker Desktop or your container engine before `supabase start`. |
| Edge Functions cannot connect to local DB | Use `host.docker.internal` instead of `localhost` from within Edge Functions. |
| `--no-backup` flag deletes containers | Avoid `--no-backup` unless you intend to lose local data. |
| Older Node.js versions fail | Use Node.js 20 or later for `npx` execution. |

### Official Documentation

- [Supabase CLI Getting Started](https://supabase.com/docs/guides/cli/getting-started)
- [Local Development](https://supabase.com/docs/guides/cli/local-development)
- [Managing Environments](https://supabase.com/docs/guides/cli/managing-environments)
- [CLI Reference](https://supabase.com/docs/reference/cli)

---

## 2. Setting Up Supabase Auth

### Prerequisites

- A hosted or local Supabase project.
- A custom SMTP provider account (required for production).
- Access to the Supabase Dashboard or Management API.

### Email/Password Authentication

Email authentication is enabled by default on new projects. Hosted projects require email confirmation before sign-in; local projects do not.

**Sign up a user:**
```javascript
const { data, error } = await supabase.auth.signUp({
  email: 'user@example.com',
  password: 'secure-password',
  options: {
    emailRedirectTo: 'https://example.com/welcome'
  }
})
```

**Sign in:**
```javascript
const { data, error } = await supabase.auth.signInWithPassword({
  email: 'user@example.com',
  password: 'secure-password'
})
```

**Password reset flow:**
```javascript
// 1. Request reset
await supabase.auth.resetPasswordForEmail('user@example.com', {
  redirectTo: 'https://example.com/auth/callback'
})

// 2. In callback route, exchange token and update password
await supabase.auth.verifyOtp({ token_hash, type: 'recovery' })
await supabase.auth.updateUser({ password: 'new-secure-password' })
```

### Configure Custom SMTP (Production Required)

Supabase provides a built-in SMTP server for development only. For production, configure a custom provider.

Supported providers: Resend, AWS SES, Postmark, Twilio SendGrid, ZeptoMail, Brevo.

**Via Management API:**
```bash
export SUPABASE_ACCESS_TOKEN="your-access-token"
export PROJECT_REF="your-project-ref"

curl -X PATCH "https://api.supabase.com/v1/projects/$PROJECT_REF/config/auth" \
  -H "Authorization: Bearer $SUPABASE_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "external_email_enabled": true,
    "smtp_host": "smtp.example.com",
    "smtp_port": 587,
    "smtp_user": "your-smtp-user",
    "smtp_pass": "your-smtp-password",
    "smtp_sender_name": "Your App Name",
    "smtp_admin_email": "no-reply@example.com"
  }'
```

Or configure via **Dashboard → Authentication → Emails**.

> **Note:** After enabling custom SMTP, an initial low rate limit of 30 messages/hour is imposed. Adjust this in **Rate Limits** configuration.

### Customize Email Templates

Supabase uses Go Templates. Available templates include:

| Authentication | Security Notifications |
|---|---|
| Confirm Sign Up | Password Changed |
| Invite User | Email Address Changed |
| Magic Link | Phone Number Changed |
| Change Email Address | Identity Linked / Unlinked |
| Reset Password | MFA Enrolled / Unenrolled |
| Reauthentication (OTP) | |

Key template variables:
- `{{ .ConfirmationURL }}` — Verification link
- `{{ .Token }}` — 6-digit OTP
- `{{ .TokenHash }}` — Hashed token for custom links
- `{{ .SiteURL }}` — Your application's site URL
- `{{ .RedirectTo }}` — Custom redirect destination
- `{{ .Data }}` — User metadata from `auth.users.user_metadata`
- `{{ .Email }}`, `{{ .NewEmail }}`, `{{ .OldEmail }}`
- `{{ .Phone }}`, `{{ .OldPhone }}`
- `{{ .Provider }}`, `{{ .FactorType }}`

For local development, configure templates in `supabase/config.toml`:
```toml
[auth.email.template.confirmation]
subject = "Confirm Your Signup"
content_path = "./supabase/templates/confirmation.html"

[auth.email.template.recovery]
subject = "Reset Your Password"
content_path = "./supabase/templates/recovery.html"
```

### Local Email Testing

The Supabase CLI automatically captures outgoing emails using Mailpit. Run:
```bash
supabase status
```
Then visit the Mailpit URL to inspect captured emails.

### Common Pitfalls

| Issue | Solution |
|---|---|
| Emails not arriving in production | The default SMTP only sends to pre-authorized addresses. Configure custom SMTP before going live. |
| Rate limit errors after SMTP setup | Increase the email rate limit from the default 30/hour in **Authentication → Rate Limits**. |
| Bot sign-up abuse | Enable CAPTCHA protection (hcaptcha or turnstile) in **Authentication → Providers**. |
| Emails landing in spam | Set up DKIM, DMARC, and SPF records. Use a custom domain for auth emails. |
| Password reset link fails | Ensure the `redirectTo` URL is added to **Authentication → URL Configuration** allow list. |
| Short session lifespans causing excess email | Increase session duration where possible to reduce reauthentication emails. |

### Official Documentation

- [Password-based Auth](https://supabase.com/docs/guides/auth/auth-email)
- [Send Emails with Custom SMTP](https://supabase.com/docs/guides/auth/auth-smtp)
- [Email Templates](https://supabase.com/docs/guides/auth/auth-email-templates)
- [Customizing Email Templates (Local)](https://supabase.com/docs/guides/local-development/customizing-email-templates)

---

## 3. Setting Up Supabase OAuth

### Prerequisites

- A hosted Supabase project.
- Accounts with the OAuth providers you intend to use (Google Cloud Console, GitHub Developer Settings).
- Your application's callback route implemented server-side for PKCE exchange.

### Configure Redirect URLs

Before implementing OAuth, add your application's URLs to Supabase's allow list.

Go to **Authentication → URL Configuration**:
- Set **Site URL** to your production URL (e.g., `https://example.com`).
- Add redirect URLs:
  - `http://localhost:3000/**` (local development)
  - `https://*.vercel.app/**` (Vercel preview deployments)
  - `https://example.com/auth/callback` (production callback route)

Wildcard rules:
- `*` matches any sequence of non-separator characters.
- `**` matches any sequence of characters (useful for nested paths and preview deployments).

> **Recommendation:** In production, set the exact redirect URL path rather than relying on wildcards.

### Google OAuth Setup

In [Google Cloud Console](https://console.cloud.google.com/):
1. Create/select a project.
2. Navigate to **APIs & Services → OAuth consent screen** and configure it.
3. Go to **APIs & Services → Credentials → Create Credentials → OAuth client ID**.
4. Choose **Web application**.
5. Under **Authorized redirect URIs**, add:
   - Production: `https://<project-ref>.supabase.co/auth/v1/callback`
   - Local CLI: `http://127.0.0.1:54321/auth/v1/callback`
6. Save the **Client ID** and **Client Secret**.

Required scopes:
- `openid` (add manually)
- `.../auth/userinfo.email` (added by default)
- `.../auth/userinfo.profile` (added by default)

In Supabase Dashboard:
1. Go to **Authentication → Providers → Google**.
2. Enable Google.
3. Enter the Client ID and Client Secret.
4. Save.

> **Note:** If you maintain multiple platform clients, concatenate all client IDs with a comma, ensuring the web client ID is first.

### GitHub OAuth Setup

In GitHub **Settings → Developer settings → OAuth Apps → New OAuth App**:
1. Fill in:
   - **Application name**: Your app name
   - **Homepage URL**: `https://example.com`
   - **Authorization callback URL**: `https://<project-ref>.supabase.co/auth/v1/callback`
2. For local testing, also add: `http://localhost:54321/auth/v1/callback`
3. Ensure **Enable Device Flow** remains disabled.
4. Save the **Client ID** and generate a **Client Secret**.

In Supabase Dashboard:
1. Go to **Authentication → Providers → GitHub**.
2. Enable GitHub.
3. Enter the Client ID and Client Secret.
4. Save.

### Web Application Implementation (PKCE Flow)

Modern web applications should use the PKCE flow with a dedicated server-side callback route.

**Initiate sign-in:**
```javascript
const { data, error } = await supabase.auth.signInWithOAuth({
  provider: 'google', // or 'github'
  options: {
    redirectTo: `${window.location.origin}/auth/callback`,
  },
})
```

**Server-side callback handler (Next.js App Router example):**
```typescript
import { NextResponse } from 'next/server'
import { createClient } from '@/utils/supabase/server'

export async function GET(request: Request) {
  const { searchParams, origin } = new URL(request.url)
  const code = searchParams.get('code')
  const next = searchParams.get('next') ?? '/'

  if (code) {
    const supabase = await createClient()
    const { error } = await supabase.auth.exchangeCodeForSession(code)

    if (!error) {
      const forwardedHost = request.headers.get('x-forwarded-host')
      const isLocalEnv = process.env.NODE_ENV === 'development'

      if (isLocalEnv) {
        return NextResponse.redirect(`${origin}${next}`)
      } else if (forwardedHost) {
        return NextResponse.redirect(`https://${forwardedHost}${next}`)
      } else {
        return NextResponse.redirect(`${origin}${next}`)
      }
    }
  }

  return NextResponse.redirect(`${origin}/auth/auth-code-error`)
}
```

### Self-Hosted Configuration

For self-hosted Supabase with Docker, configure OAuth in `.env`:
```sh
GOOGLE_ENABLED=true
GOOGLE_CLIENT_ID=your-client-id
GOOGLE_SECRET=your-client-secret

GITHUB_ENABLED=true
GITHUB_CLIENT_ID=your-github-client-id
GITHUB_SECRET=your-github-client-secret

SITE_URL=https://example.com
API_EXTERNAL_URL=https://example.com
```

Then map these to the `auth` service in `docker-compose.yml`:
```yaml
auth:
  environment:
    GOTRUE_EXTERNAL_GOOGLE_ENABLED: ${GOOGLE_ENABLED}
    GOTRUE_EXTERNAL_GOOGLE_CLIENT_ID: ${GOOGLE_CLIENT_ID}
    GOTRUE_EXTERNAL_GOOGLE_SECRET: ${GOOGLE_SECRET}
    GOTRUE_EXTERNAL_GOOGLE_REDIRECT_URI: ${API_EXTERNAL_URL}/auth/v1/callback
    GOTRUE_EXTERNAL_GITHUB_ENABLED: ${GITHUB_ENABLED}
    GOTRUE_EXTERNAL_GITHUB_CLIENT_ID: ${GITHUB_CLIENT_ID}
    GOTRUE_EXTERNAL_GITHUB_SECRET: ${GITHUB_SECRET}
    GOTRUE_EXTERNAL_GITHUB_REDIRECT_URI: ${API_EXTERNAL_URL}/auth/v1/callback
```

Restart the auth service:
```bash
docker compose up -d --force-recreate --no-deps auth
```

### Common Pitfalls

| Issue | Solution |
|---|---|
| "Provider not enabled" error | Verify credentials are entered in the dashboard and the provider is toggled on. For self-hosted, check `GOTRUE_EXTERNAL_*_ENABLED` env vars. |
| Redirect URL mismatch | Ensure the exact callback URL is in the OAuth provider settings and in Supabase's **URL Configuration** allow list. |
| Local development redirect fails | Add `http://localhost:54321/auth/v1/callback` to the provider's authorized redirect URIs. |
| Nonce check failure (Google mobile) | Enable "Skip nonce check" in the Supabase dashboard or set `GOTRUE_EXTERNAL_SKIP_NONCE_CHECK: 'true'` temporarily. |
| Load balancer/Vercel host issues | Check the `x-forwarded-host` header in your callback handler to construct the correct redirect URL. |

### Official Documentation

- [Login with Google](https://supabase.com/docs/guides/auth/social-login/auth-google)
- [Login with GitHub](https://supabase.com/docs/guides/auth/social-login/auth-github)
- [Redirect URLs](https://supabase.com/docs/guides/auth/redirect-urls)
- [Configure Social Login Providers (Self-Hosting)](https://supabase.com/docs/guides/self-hosting/self-hosted-oauth)

---

## 4. Setting Up Migrations with Supabase CLI

### Prerequisites

- Supabase CLI installed and a project initialized (`supabase init`).
- Local stack running (`supabase start`) or a linked remote project.
- Basic familiarity with PostgreSQL DDL.

### Create a New Migration

```bash
supabase migration new create_employees_table
```

This generates a file in `supabase/migrations/` with a timestamp prefix:
```
supabase/migrations/20240115120000_create_employees_table.sql
```

Write your schema changes inside this file:
```sql
create table public.employees (
  id uuid default gen_random_uuid() primary key,
  name text not null,
  created_at timestamptz default now()
);
```

### Run Migrations Locally

```bash
supabase db reset
```

This command:
1. Recreates the local Postgres container.
2. Applies all migrations in `supabase/migrations/` in timestamp order.
3. Seeds data from `supabase/seed.sql` (unless `--no-seed` is passed).

Flags:
- `--no-seed` — Skip running the seed script.
- `--version <timestamp>` — Reset up to a specific migration.
- `--linked` — Reset a remote linked project with local migrations.
- `--local` — Reset the local database (default).

### Auto-Generate Migrations from Studio Changes

If you prefer designing schemas in the Studio UI, capture changes as SQL:
```bash
supabase db diff --schema public -f add_new_columns
```

This creates a migration file containing the diff between your current local database state and the Studio modifications.

### Link to Remote and Push

```bash
# Link project
supabase link --project-ref <project-id>

# Pull any existing remote schema (optional, for existing projects)
supabase db pull

# Preview changes before applying
supabase db push --dry-run

# Apply migrations to remote
supabase db push
```

`supabase db push` behavior:
- Creates a migration history table `supabase_migrations.schema_migrations` on first run.
- Skips migrations already applied (tracked by timestamp).
- Use `--include-seed` to also push seed data.
- Use `--include-roles` to push custom roles from `supabase/roles.sql`.
- For self-hosted databases, pass `--db-url <connection-string>`.

### Squash Migrations (Optional)

To combine multiple migrations into one:
```bash
supabase migration squash
```

> **Warning:** Squashing omits DML (INSERT/UPDATE/DELETE) statements. You must re-add any data manipulations manually.

### Repair Migration History (Advanced)

If the remote migration history becomes out of sync with local files, repair it without executing SQL:
```bash
supabase migration repair <timestamp> --status applied
```

### Seeding Data

Configure in `supabase/config.toml`:
```toml
[db.seed]
enabled = true
sql_paths = ['./seed.sql']        # single file
# OR
sql_paths = ['./seeds/*.sql']     # multiple files via glob
```

The default seed file is `supabase/seed.sql`:
```sql
insert into public.employees (name)
values
  ('Erlich Bachman'),
  ('Richard Hendricks'),
  ('Monica Hall');
```

Seeds run automatically after migrations during `supabase start` and `supabase db reset`. The CLI processes `sql_paths` in declaration order, sorting glob results lexicographically.

### Complete Local Development Workflow

```bash
# 1. Initialize
supabase init

# 2. Create migration
supabase migration new add_users_table
# Edit: supabase/migrations/20240115120000_add_users_table.sql

# 3. Test locally
supabase db reset

# 4. Link and synchronize
supabase link --project-ref abcdefghijklmnopqrst
supabase db pull

# 5. Deploy
supabase db push
```

### Common Pitfalls

| Issue | Solution |
|---|---|
| Migration fails locally | Check `supabase start` is running. Review migration SQL for syntax errors. |
| `db push` fails with auth/storage schema errors | Use `--schema public` or target specific schemas. If the migrations directory is empty, run `db pull` first. |
| Seed data not appearing | Ensure `[db.seed] enabled = true` in `config.toml`. Avoid schema statements in seed files; use only DML (INSERT). |
| Remote migration history out of sync | Use `supabase migration repair` to mark migrations as applied or pending without re-running SQL. |
| Pushing to wrong environment | Always use `--dry-run` before `db push` to preview which migrations will be applied. |

### Official Documentation

- [Local Development with Schema Migrations](https://supabase.com/docs/guides/cli/local-development)
- [Seeding Your Database](https://supabase.com/docs/guides/local-development/seeding-your-database)
- [Managing Environments](https://supabase.com/docs/guides/cli/managing-environments)
- [CLI Reference: supabase db push](https://supabase.com/docs/reference/cli/supabase-db-push)
- [CLI Reference: supabase db reset](https://supabase.com/docs/reference/cli/v1/supabase-db-reset)

---

## Key Takeaways

- **CLI Installation:** Use Homebrew, Scoop, or `npx` — never `npm install -g supabase`. Docker is mandatory for local development.
- **Auth Email Deliverability:** The built-in SMTP is for development only. Production workloads require a custom SMTP provider (Resend, AWS SES, etc.) with DKIM/SPF/DMARC records and a dedicated auth domain.
- **OAuth Security:** Always implement the PKCE flow with a server-side callback route. Precisely match redirect URIs in both the provider settings and Supabase's URL Configuration allow list.
- **Migration Discipline:** Treat schema as code via timestamped SQL migrations. Use `supabase db diff` to capture Studio UI changes, `supabase db reset` to test locally, and `supabase db push --dry-run` to preview remote changes before applying them.
- **Seed Best Practices:** Keep seed files focused on data insertions only. Configure multiple seed files via `config.toml` glob patterns for reproducible environments across local, staging, and production.
