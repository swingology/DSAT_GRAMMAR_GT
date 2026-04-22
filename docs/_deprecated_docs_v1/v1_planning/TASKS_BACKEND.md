---

## Remaining Work (Updated 2026-04-16)

### ~~Immediate: Fix Failing Test~~ ✅ Resolved

`tests/test_ontology.py::TestPromptDrift::test_pass1_stem_type_matches_ontology` — now passing (307/307).

---

### Migration 039: Token Annotation (Grammar UI)

**Status:** ✅ Complete + Hardened (Codex adversarial review 2026-04-16)

| Component | Status |
|-----------|--------|
| Migration `039_grammar_keys_token_annotations.sql` | ✅ |
| `app/pipeline/tokenize.py` | ✅ Hardened |
| `app/prompts/pass3_tokenization.py` | ✅ |
| Tests (`tests/test_tokenize.py`) | ✅ 12 tests |

**Hardening applied (Codex review findings):**
- [HIGH] Delete+insert now wrapped in `async with conn.transaction()` — stale rows survive insert failure
- [HIGH] `tokenization_status: "ready" | "pending"` added to `/practice` response so frontend knows when tokens are available
- [MEDIUM] Full token contract validated before any DB write: exactly 1 blank, unique ordered indexes, all tags in `VALID_GRAMMAR_TAGS` allowlist

---

### Practice Endpoint

**Status:** ✅ Complete

| Component | Status |
|-----------|--------|
| `GET /questions/{id}/practice` | ✅ |
| `tokenization_status` field | ✅ Added |
| Tests (`tests/test_practice_endpoint.py`) | ✅ 10 tests |

---

## Archive: Completed Phases

All backend rebuild tasks are complete except for the Pass 1 prompt fix above. The original "move to deprecated" workflow was skipped in favor of an in-place rebuild that preserved working code and fixed the search.py JOIN bug.
