# API Endpoints Reference

This document describes all HTTP endpoints exposed by the DSAT backend FastAPI service.

---

## Authentication

The API uses API key authentication via the `X-API-Key` header. There are two scopes:

| Scope | Env Var | Endpoints | Notes |
|---|---|---|---|
| Admin | `ADMIN_API_KEYS` | `/ingest/*`, `/generate/*`, `/admin/*`, `/questions/*` | Comma-separated list in `.env` |
| Student | `STUDENT_API_KEYS` | `/api/*` | Comma-separated list in `.env` |

For the beta period, admin and student keys may share the same pool. There are no JWTs or user sessions; API keys are sufficient for a single-admin beta.

Requests without a valid key receive `403 Forbidden`.

---

## Endpoint Groups

### Health

| Method | Path | Auth Required | Description |
|---|---|---|---|
| GET | `/` | No | Service health check. Returns status and version. |

**Response:**
```json
{
  "status": "ok",
  "version": "0.1.0"
}
```

---

### Ingestion (`/ingest/*`)

Admin scope required.

| Method | Path | Auth Required | Description |
|---|---|---|---|
| POST | `/ingest/official/pdf` | Admin | Upload an official PDF and create per-question ingestion jobs |
| POST | `/ingest/unofficial/file` | Admin | Upload a single unofficial asset (PDF, image, MD, JSON, text) |
| POST | `/ingest/unofficial/batch` | Admin | Batch upload mixed unofficial assets |
| POST | `/ingest/reannotate/{question_id}` | Admin | Re-run Pass 2 annotation on an existing question with the same or a different provider |

**Notes:**
- Uploads use multipart form data.
- Max upload size: 50MB.
- MIME types are validated against the `asset_type` enum.

---

### Generation (`/generate/*`)

Admin scope required.

| Method | Path | Auth Required | Description |
|---|---|---|---|
| POST | `/generate/questions` | Admin | Generate questions from source examples |
| POST | `/generate/questions/compare` | Admin | Generate with multiple LLMs for side-by-side comparison |
| GET | `/generate/runs/{run_id}` | Admin | Inspect generation lineage and review state |

---

### Questions (`/questions/*`)

Admin scope required.

| Method | Path | Auth Required | Description |
|---|---|---|---|
| GET | `/questions/recall` | Admin | Filter and paginate practice questions. Supports all PRD Section 12 filters (grammar_focus, difficulty, origin, etc.) |
| GET | `/questions/{question_id}` | Admin | Full question detail: content, annotation, options, lineage, overlap state |
| GET | `/questions/{question_id}/versions` | Admin | Edit history for a question |

---

### Admin (`/admin/*`)

Admin scope required.

| Method | Path | Auth Required | Description |
|---|---|---|---|
| PATCH | `/admin/questions/{question_id}` | Admin | Edit question content, answers, or explanation |
| POST | `/admin/questions/{question_id}/approve` | Admin | Approve question for practice recall (sets `practice_status = active`) |
| POST | `/admin/questions/{question_id}/reject` | Admin | Reject or retire a question (sets `practice_status = retired`) |
| POST | `/admin/questions/{question_id}/confirm-overlap` | Admin | Confirm overlap with official corpus |
| POST | `/admin/questions/{question_id}/clear-overlap` | Admin | Reject a false-positive overlap flag |
| POST | `/admin/evaluations/{evaluation_id}/score` | Admin | Store human evaluation scores for beta model comparison |

---

### Student (`/api/*`)

Student scope required. These endpoints power the practice experience.

| Method | Path | Auth Required | Description |
|---|---|---|---|
| GET | `/api/questions` | Student | Practice recall. Query params: `grammar_focus`, `difficulty`, `origin`, `limit`, `offset` |
| POST | `/api/submit` | Student | Record a student answer attempt |
| GET | `/api/stats/{user_id}` | Student | User accuracy stats including top missed focus keys and trap keys |

---

## Request / Response Payload Models

### `QuestionRecallResponse`

Used by `GET /questions/recall` and `GET /api/questions`.

| Field | Type | Required | Description |
|---|---|---|---|
| `id` | str | Yes | Question UUID |
| `content_origin` | str | Yes | `official`, `unofficial`, or `generated` |
| `current_question_text` | str | Yes | Prompt / stem text |
| `current_passage_text` | str | No | Passage text |
| `current_correct_option_label` | str | Yes | `A`, `B`, `C`, or `D` |
| `practice_status` | str | Yes | `draft`, `active`, or `retired` |
| `grammar_role_key` | str | No | V3 grammar role |
| `grammar_focus_key` | str | No | V3 grammar focus |
| `difficulty_overall` | str | No | `low`, `medium`, or `high` |
| `stimulus_mode_key` | str | No | V3 stimulus mode |
| `source_exam_code` | str | No | e.g. `PT4` |

---

### `QuestionDetailResponse`

Used by `GET /questions/{question_id}`.

| Field | Type | Required | Description |
|---|---|---|---|
| `id` | str | Yes | Question UUID |
| `content_origin` | str | Yes | `official`, `unofficial`, or `generated` |
| `current_question_text` | str | Yes | Prompt / stem text |
| `current_passage_text` | str | No | Passage text |
| `current_correct_option_label` | str | Yes | `A`, `B`, `C`, or `D` |
| `current_explanation_text` | str | No | Composed explanation |
| `practice_status` | str | Yes | `draft`, `active`, or `retired` |
| `official_overlap_status` | str | Yes | `none`, `possible`, or `confirmed` |
| `is_admin_edited` | bool | Yes | Whether the question was edited by an admin |
| `source_exam_code` | str | No | e.g. `PT4` |
| `source_module_code` | str | No | e.g. `M1` |
| `latest_annotation` | dict | No | Full annotation JSON object |
| `options` | list[dict] | Yes | List of option analysis objects |
| `lineage` | dict | No | Lineage and relation metadata |
| `created_at` | datetime | No | Creation timestamp |
| `updated_at` | datetime | No | Last update timestamp |

---

### `UserProgressCreate`

Used by `POST /api/submit`.

| Field | Type | Required | Description |
|---|---|---|---|
| `user_id` | int | Yes | Student user ID |
| `question_id` | str | Yes | Question UUID |
| `is_correct` | bool | Yes | Whether the answer was correct |
| `selected_option_label` | str | Yes | `A`, `B`, `C`, or `D` |
| `missed_grammar_focus_key` | str | No | V3 grammar focus key for the missed concept |
| `missed_syntactic_trap_key` | str | No | V3 syntactic trap key for the missed trap |

---

### `UserStats`

Used by `GET /api/stats/{user_id}`.

| Field | Type | Required | Description |
|---|---|---|---|
| `total_answered` | int | Yes | Total questions attempted |
| `total_correct` | int | Yes | Total correct answers |
| `accuracy` | float | Yes | Overall accuracy percentage |
| `top_missed_focus_keys` | list[str] | Yes | Most frequently missed grammar focus keys |
| `top_missed_trap_keys` | list[str] | Yes | Most frequently missed syntactic trap keys |

---

### `AdminEditRequest`

Used by `PATCH /admin/questions/{question_id}`.

| Field | Type | Required | Description |
|---|---|---|---|
| `question_text` | str | No | New prompt / stem text |
| `passage_text` | str | No | New passage text |
| `correct_option_label` | str | No | `A`, `B`, `C`, or `D` |
| `explanation_text` | str | No | New explanation text |
| `change_notes` | str | No | Admin notes about the edit |

---

### `EvaluationScoreRequest`

Used by `POST /admin/evaluations/{evaluation_id}/score`.

| Field | Type | Required | Description |
|---|---|---|---|
| `score_overall` | float | No | Overall score, 0.0 to 10.0 |
| `score_metadata` | float | No | Metadata score, 0.0 to 10.0 |
| `score_explanation` | float | No | Explanation score, 0.0 to 10.0 |
| `score_generation` | float | No | Generation score, 0.0 to 10.0 |
| `review_notes` | str | No | Human reviewer notes |
| `recommended_for_default` | bool | No | Whether this model should become the default |
