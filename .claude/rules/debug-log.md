# DEBUG_LOG.md Rule

Whenever you discover, fix, or are told about a problem (bug, error, regression,
data issue, test failure, security gap), log it to `DEBUG_LOG.md`.

## When to log

- Any bug found during code review or testing
- Any error encountered while running commands
- Any fix applied to a broken or incorrect behavior
- Any security or data-integrity gap identified

## Entry format

Add a new `##` section at the top of the findings list (most-recent-first):

```
## YYYY-MM-DD - <Short Audit Title>
Report created by: <Model name, e.g. Claude Sonnet 4.6>
Git branch: `<branch name>`
Git checkpoint: `<short hash>` — <commit message>

### Findings

1. **<Severity>:** <description of problem>
   - <detail / affected files>
   - **Fixed:** <what was changed to resolve it>  ← add only after fixing
```

## Severity levels

- **Critical** — data loss, auth bypass, or production breakage
- **High** — incorrect behavior affecting core functionality
- **Medium** — edge-case bugs or gaps with limited blast radius
- **Low** — cosmetic issues, minor inconsistencies

## Strikethrough rule

When a finding is resolved, wrap the original text in `~~strikethrough~~` and
add a `**Fixed:**` note inline. Do NOT delete the original finding — the audit
trail must show what was found and how it was resolved.

## Getting the branch and hash

Run these when creating an entry:
```
git rev-parse --abbrev-ref HEAD   # branch name
git log --oneline -1              # short hash + commit message
```
