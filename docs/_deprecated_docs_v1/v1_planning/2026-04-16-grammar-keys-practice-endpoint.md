# Grammar Keys + Practice Endpoint Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `grammar_keys` and `question_token_annotations` tables to Supabase, expose a `/questions/{id}/practice` endpoint, and log all schema/endpoint changes to `log_schema_<date>.md`.

**Architecture:** New migration 039 adds two tables. The FastAPI questions router gains one new endpoint that joins questions + options + grammar keys + token annotations into a single response shaped for grammar-app.html. A schema log is written during execution.

**Tech Stack:** PostgreSQL (Supabase), asyncpg, FastAPI, psql CLI for migration execution.

---

## File Map

| Action | Path |
|--------|------|
| Create | `FULL_PLAN/backend/migrations/039_grammar_keys_token_annotations.sql` |
| Modify | `FULL_PLAN/backend/app/routers/questions.py` |
| Create | `FULL_PLAN/backend/tests/test_practice_endpoint.py` |
| Create | `log_schema_2026-04-16.md` (repo root, written during execution) |

---

## Chunk 1: Migration

### Task 1: Write migration 039

**Files:**
- Create: `FULL_PLAN/backend/migrations/039_grammar_keys_token_annotations.sql`

- [ ] **Step 1: Create the migration file**

```sql
-- 039_grammar_keys_token_annotations.sql
-- Adds grammar key registry and per-question token annotations
-- for the interactive grammar-app.html UI.

BEGIN;

-- Grammar key registry: defines sentence-part categories used in the UI
CREATE TABLE IF NOT EXISTS public.grammar_keys (
    id            text PRIMARY KEY,          -- e.g. 'subordinate_clause'
    label         text NOT NULL,             -- e.g. 'Subordinate Clause'
    color         text NOT NULL,             -- hex, e.g. '#7c3aed'
    light_bg      text NOT NULL,             -- hex, e.g. '#f5f3ff'
    mid_bg        text NOT NULL,             -- hex, e.g. '#ddd6fe'
    description   text NOT NULL,
    sat_rule      text NOT NULL,
    created_at    timestamptz NOT NULL DEFAULT now()
);

-- Seed the six keys used in grammar-app.html
INSERT INTO public.grammar_keys (id, label, color, light_bg, mid_bg, description, sat_rule)
VALUES
  ('subordinate_clause',  'Subordinate Clause',  '#7c3aed', '#f5f3ff', '#ddd6fe',
   'A dependent clause that begins with a subordinating conjunction. It cannot stand alone as a sentence.',
   'A subordinate clause (''Although...'', ''Because...'', ''Since...'') must attach to a main clause. Using one alone creates a sentence fragment — a classic SAT trap.'),
  ('subject',             'Primary Subject',     '#1d4ed8', '#eff6ff', '#bfdbfe',
   'The main noun phrase that performs the action of the main verb.',
   'Subject–verb agreement: the verb must match the subject in number. Watch out for intervening phrases (like relative clauses) that can fool you into misidentifying the subject.'),
  ('main_verb',           'Main Verb',           '#15803d', '#f0fdf4', '#bbf7d0',
   'The primary action or state of the main independent clause.',
   'Verb tense must be logical and consistent. Simple past (''reflected'') is used for completed past actions. Past perfect (''had reflected'') only applies when describing an action completed before another past event.'),
  ('relative_clause',     'Relative Clause',     '#b45309', '#fffbeb', '#fde68a',
   'A clause introduced by ''which'', ''who'', or ''that'' that modifies a noun.',
   'Non-restrictive relative clauses use ''which'' and are set off by commas. They add extra info that can be removed without changing the core meaning.'),
  ('subordinating_conj',  'Sub. Conjunction',    '#b91c1c', '#fff1f2', '#fecdd3',
   'A conjunction that introduces the subordinate clause and links it to the main clause.',
   '''Although'' signals contrast — the main clause should present a result that seems unexpected given the subordinate clause.'),
  ('modifier',            'Modifier',            '#0e7490', '#ecfeff', '#a5f3fc',
   'A word or phrase that describes or qualifies another element in the sentence.',
   'Modifiers must be placed close to what they modify. A misplaced modifier changes meaning entirely.')
ON CONFLICT (id) DO NOTHING;


-- Token annotations: word-level breakdown of a question sentence
CREATE TABLE IF NOT EXISTS public.question_token_annotations (
    id           uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    question_id  uuid NOT NULL REFERENCES public.questions(id) ON DELETE CASCADE,
    token_index  int  NOT NULL,              -- 0-based position in token array
    token_text   text NOT NULL,              -- the word/punctuation string
    is_blank     boolean NOT NULL DEFAULT false,
    grammar_tags text[] NOT NULL DEFAULT '{}', -- references grammar_keys.id values
    created_at   timestamptz NOT NULL DEFAULT now(),
    UNIQUE (question_id, token_index)
);

CREATE INDEX IF NOT EXISTS idx_token_annotations_question
    ON public.question_token_annotations (question_id);

COMMIT;
```

- [ ] **Step 2: Run migration against Supabase**

```bash
DB_URL=$(grep SUPABASE_DB_URL FULL_PLAN/backend/.env | cut -d= -f2-)
psql "$DB_URL" -f FULL_PLAN/backend/migrations/039_grammar_keys_token_annotations.sql
```

Expected output:
```
BEGIN
CREATE TABLE
INSERT 0 6
CREATE TABLE
CREATE INDEX
COMMIT
```

- [ ] **Step 3: Verify tables exist**

```bash
psql "$DB_URL" -c "\dt public.grammar_keys" -c "\dt public.question_token_annotations"
```

Expected: both tables listed.

- [ ] **Step 4: Commit**

```bash
git add FULL_PLAN/backend/migrations/039_grammar_keys_token_annotations.sql
git commit -m "feat: add grammar_keys and question_token_annotations tables (migration 039)"
```

---

## Chunk 2: Practice Endpoint

### Task 2: Add `/questions/{id}/practice` endpoint

**Files:**
- Modify: `FULL_PLAN/backend/app/routers/questions.py`
- Create: `FULL_PLAN/backend/tests/test_practice_endpoint.py`

- [ ] **Step 1: Write the failing test**

Create `FULL_PLAN/backend/tests/test_practice_endpoint.py`:

```python
import uuid
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

FAKE_ID = str(uuid.uuid4())

MOCK_QUESTION = {
    "id": FAKE_ID,
    "prompt_text": "Although the committee deliberated for weeks, its final decision reflected a compromise.",
    "passage_text": None,
    "correct_option_label": "B",
    "explanation_short": "Simple past matches context.",
    "explanation_full": "Simple past matches context.",
    "stem_type_key": "sec_grammar",
}

MOCK_OPTIONS = [
    {"option_label": "A", "option_text": "had deliberated", "is_correct": False,
     "explanation": "Past perfect implies sequence not present here."},
    {"option_label": "B", "option_text": "deliberated",     "is_correct": True,
     "explanation": "Correct. Simple past matches 'reflected'."},
    {"option_label": "C", "option_text": "has deliberated", "is_correct": False,
     "explanation": "Present perfect implies connection to present."},
    {"option_label": "D", "option_text": "deliberates",     "is_correct": False,
     "explanation": "Simple present contradicts past context."},
]

MOCK_TOKENS = [
    {"token_index": 0, "token_text": "Although",     "is_blank": False, "grammar_tags": ["subordinating_conj", "subordinate_clause"]},
    {"token_index": 1, "token_text": " deliberated", "is_blank": True,  "grammar_tags": ["subordinate_clause"]},
]

MOCK_KEYS = [
    {"id": "subordinate_clause", "label": "Subordinate Clause", "color": "#7c3aed",
     "light_bg": "#f5f3ff", "mid_bg": "#ddd6fe",
     "description": "A dependent clause.", "sat_rule": "Must attach to main clause."},
]


@pytest.mark.asyncio
async def test_practice_endpoint_shape(async_client):
    """Response must include tokens, options, and grammar_keys arrays."""
    with patch("app.routers.questions.get_pool") as mock_pool:
        conn = AsyncMock()
        conn.fetchrow = AsyncMock(return_value=MOCK_QUESTION)
        conn.fetch = AsyncMock(side_effect=[MOCK_OPTIONS, MOCK_TOKENS, MOCK_KEYS])
        mock_pool.return_value.acquire.return_value.__aenter__ = AsyncMock(return_value=conn)
        mock_pool.return_value.acquire.return_value.__aexit__ = AsyncMock(return_value=False)

        resp = await async_client.get(f"/questions/{FAKE_ID}/practice")
        assert resp.status_code == 200
        body = resp.json()
        assert "tokens" in body
        assert "options" in body
        assert "grammar_keys" in body
        assert any(t["is_blank"] for t in body["tokens"])
        assert len(body["options"]) == 4
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd FULL_PLAN && uv run pytest backend/tests/test_practice_endpoint.py -v 2>&1 | tail -20
```

Expected: FAIL — endpoint doesn't exist yet.

- [ ] **Step 3: Add the endpoint to `questions.py`**

Append to `FULL_PLAN/backend/app/routers/questions.py`:

```python
@router.get("/{question_id}/practice")
async def get_question_practice(question_id: uuid.UUID):
    """
    Return full data shape for grammar-app.html interactive UI:
    tokens (word-level with grammar tags), options (A-D with explanations),
    and grammar key definitions.
    """
    pool = get_pool()
    async with pool.acquire() as conn:
        q = await conn.fetchrow(
            """
            SELECT id, prompt_text, passage_text, correct_option_label,
                   explanation_short, explanation_full, stem_type_key
            FROM public.questions WHERE id = $1
            """,
            question_id,
        )
        if not q:
            raise HTTPException(status_code=404, detail="Question not found")

        options = await conn.fetch(
            """
            SELECT option_label, option_text, is_correct, explanation
            FROM public.question_options
            WHERE question_id = $1 ORDER BY option_label
            """,
            question_id,
        )

        tokens = await conn.fetch(
            """
            SELECT token_index, token_text, is_blank, grammar_tags
            FROM public.question_token_annotations
            WHERE question_id = $1 ORDER BY token_index
            """,
            question_id,
        )

        grammar_keys = await conn.fetch(
            """
            SELECT id, label, color, light_bg, mid_bg, description, sat_rule
            FROM public.grammar_keys ORDER BY id
            """,
        )

    return {
        "id": str(q["id"]),
        "prompt_text": q["prompt_text"],
        "passage_text": q["passage_text"],
        "correct_option_label": q["correct_option_label"],
        "explanation_short": q["explanation_short"],
        "stem_type_key": q["stem_type_key"],
        "options": [
            {
                "id": r["option_label"],
                "text": r["option_text"],
                "correct": r["is_correct"],
                "explanation": r["explanation"],
            }
            for r in options
        ],
        "tokens": [
            {
                "token_index": r["token_index"],
                "text": r["token_text"],
                "is_blank": r["is_blank"],
                "tags": list(r["grammar_tags"]),
            }
            for r in tokens
        ],
        "grammar_keys": [
            {
                "id": r["id"],
                "label": r["label"],
                "color": r["color"],
                "lightBg": r["light_bg"],
                "midBg": r["mid_bg"],
                "description": r["description"],
                "rule": r["sat_rule"],
            }
            for r in grammar_keys
        ],
    }
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd FULL_PLAN && uv run pytest backend/tests/test_practice_endpoint.py -v 2>&1 | tail -10
```

Expected: PASS.

- [ ] **Step 5: Run full test suite to check for regressions**

```bash
cd FULL_PLAN && uv run pytest backend/tests/ -v 2>&1 | tail -20
```

Expected: all existing tests still pass.

- [ ] **Step 6: Commit**

```bash
git add FULL_PLAN/backend/app/routers/questions.py FULL_PLAN/backend/tests/test_practice_endpoint.py
git commit -m "feat: add /questions/{id}/practice endpoint returning tokens, options, grammar_keys"
```

---

## Chunk 3: Schema Log

### Task 3: Write schema log

**Files:**
- Create: `log_schema_2026-04-16.md` (repo root)

- [ ] **Step 1: Create the log file**

Write `log_schema_2026-04-16.md` at the repo root documenting:
- Migration 039 tables added
- Seeded grammar_keys rows
- New endpoint `/questions/{id}/practice`
- Response shape

- [ ] **Step 2: Commit**

```bash
git add log_schema_2026-04-16.md
git commit -m "docs: add schema log for grammar_keys migration and practice endpoint"
```

---

## psql prerequisite (if not yet installed)

```bash
brew install libpq
echo 'export PATH="/opt/homebrew/opt/libpq/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```
