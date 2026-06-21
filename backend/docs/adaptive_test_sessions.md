# Adaptive Test Sessions API

These endpoints implement Phase 4 of the student tracking backend: a two-module adaptive test where module 2 difficulty is determined by module 1 performance.

## Overview

The DSAT is structured as two sequential modules. The real exam routes students to a harder or easier module 2 based on how they performed in module 1. These endpoints replicate that routing logic.

**Flow:**

```
Student completes module 1
        ↓
POST /api/test-session/module-1-complete
        ↓
 accuracy ≥ 70%? → "higher" difficulty
 accuracy < 70%? → "lower" difficulty
        ↓
GET /api/test-session/{id}/module-2-blueprint
        ↓
Student answers module 2 questions
```

---

## Routing Algorithm

The routing threshold is **70% accuracy**:

| Module 1 accuracy | Module 2 difficulty |
|---|---|
| ≥ 70% | `"higher"` — questions weighted toward the student's weakest focus areas |
| < 70% | `"lower"` — balanced active question set |

Both difficulty paths avoid questions the student answered in the last 3 days. The `"higher"` path additionally queries the student's weakest grammar focus keys from `UserProgress` and prioritises questions tagged with those keys.

---

## Authentication

All endpoints require the `X-API-Key: student-test-key` header.

---

## Endpoints

### `POST /api/test-session/module-1-complete`

Record module 1 results and receive the module 2 routing decision.

**Request body:**

```json
{
  "user_token": "string (required) — identifies the student",
  "module_1_accuracy": 0.74,
  "module_1_duration_seconds": 1847,
  "focus_breakdown": {
    "verb_tense_consistency": { "attempts": 4, "correct": 3 },
    "subject_verb_agreement": { "attempts": 3, "correct": 1 }
  },
  "test_mode": "practice"
}
```

| Field | Type | Required | Notes |
|---|---|---|---|
| `user_token` | string | ✓ | Student's auth token |
| `module_1_accuracy` | float 0–1 | ✓ | Correct answers / total questions |
| `module_1_duration_seconds` | int | — | Time taken; recorded but not used in routing |
| `focus_breakdown` | object | — | Per-focus-key attempt/correct counts; stored in `module_1_results` JSONB |
| `test_mode` | string | — | `"practice"` (default) or `"official"` |

**Response `200`:**

```json
{
  "test_session_id": "550e8400-e29b-41d4-a716-446655440000",
  "module_2_difficulty": "higher",
  "routing_rationale": "Accuracy 74% ≥ 70% threshold — routing to higher difficulty",
  "module_1_accuracy": 0.74
}
```

**Save `test_session_id`** — it's required for the blueprint endpoint.

**Errors:**
- `401/403` — missing or invalid API key
- `404` — `user_token` not found
- `422` — missing `module_1_accuracy`

---

### `GET /api/test-session/{test_session_id}/module-2-blueprint`

Fetch the question set for module 2 using the routed difficulty.

**Path parameter:** `test_session_id` — UUID returned by `module-1-complete`

**Query parameters:**

| Param | Type | Default | Notes |
|---|---|---|---|
| `user_token` | string | required | Must match the user who created the session |
| `limit` | int | `27` | Number of questions to return (5–40) |

**Response `200`:**

```json
{
  "test_session_id": "550e8400-e29b-41d4-a716-446655440000",
  "module_2_difficulty": "higher",
  "routing_rationale": "Accuracy 74% ≥ 70% threshold — routing to higher difficulty",
  "question_count": 27,
  "questions": [
    {
      "id": "question-uuid",
      "current_question_text": "The committee [BLANK] its decision.",
      "current_passage_text": null,
      "options": [
        { "label": "A", "text": "announce" },
        { "label": "B", "text": "announces" },
        { "label": "C", "text": "announced" },
        { "label": "D", "text": "is announcing" }
      ],
      "domain": "grammar",
      "grammar_focus_key": "subject_verb_agreement",
      "reading_focus_key": null
    }
  ]
}
```

**Question selection logic:**

- Only `practice_status = "active"` questions are included
- Questions answered within the last 3 days are excluded to prevent immediate repetition
- **"higher" path**: the student's 5 lowest-accuracy grammar focus keys are identified from `UserProgress`; questions tagged with those keys are surfaced first
- **"lower" path**: questions are drawn in random order from the active pool

**Errors:**
- `401/403` — missing or invalid API key
- `404` — session not found, or session belongs to a different user
- `422` — `test_session_id` is not a valid UUID

---

### `GET /api/test-session/history`

Return the student's past adaptive test sessions, most recent first.

**Query parameters:**

| Param | Type | Default | Notes |
|---|---|---|---|
| `user_token` | string | required | |
| `limit` | int | `10` | Max sessions to return (1–50) |

**Response `200`:**

```json
{
  "user_id": 42,
  "sessions": [
    {
      "test_session_id": "550e8400-e29b-41d4-a716-446655440000",
      "module_1_accuracy": 0.74,
      "module_2_difficulty": "higher",
      "estimated_score": null,
      "test_mode": "practice",
      "created_at": "2026-06-21T19:30:00+00:00",
      "completed_at": null
    }
  ]
}
```

`estimated_score` and `completed_at` are `null` until the backend records a module 2 completion (not yet implemented — see [Future work](#future-work) below).

**Errors:**
- `401/403` — missing or invalid API key
- `404` — `user_token` not found

---

## Database

**Table: `test_session_results`**

| Column | Type | Notes |
|---|---|---|
| `id` | UUID PK | Auto-generated |
| `user_id` | integer FK → users | |
| `module_1_results` | JSONB | `focus_breakdown` from the request |
| `module_1_accuracy` | float | Stored rounded to 4 decimal places |
| `module_1_duration_seconds` | integer | Optional |
| `module_2_difficulty` | varchar(20) | `"higher"` or `"lower"` |
| `routing_rationale` | text | Human-readable explanation |
| `module_2_results` | JSONB | Null until module 2 is recorded |
| `estimated_score` | integer | Null until computed (200–800 scale) |
| `test_mode` | varchar(20) | `"practice"` or `"official"` |
| `created_at` | timestamptz | Set on insert |
| `completed_at` | timestamptz | Null until module 2 is finished |

---

## Frontend Integration

`TestModeTab` uses these endpoints for its adaptive flow:

```
TestModeTab state machine:
  idle → running (module 1) → routing (POST module-1-complete)
       → module2 (GET module-2-blueprint) → done
```

The `userToken` prop is injected at render time. The routing screen shows the difficulty decision and lets the student choose to review module 1 or proceed to module 2.

---

## Future Work

- **Module 2 completion endpoint** — `POST /api/test-session/{id}/module-2-complete` to record module 2 results and set `completed_at`
- **Score estimation** — compute a 200–800 estimated score from combined module 1 + 2 accuracy
- **Reading domain routing** — currently only grammar focus keys are used in the `"higher"` blueprint selection; reading focus keys should be included
- **Official mode** — `test_mode: "official"` sessions could drive a stricter question pool (official questions only)
