# API Endpoints

Base URL: `http://localhost:8000`

All endpoints except `GET /` require the `X-API-Key` header.

---

## Health

### `GET /`
No auth required.

**Response:**
```json
{"status": "ok", "version": "0.1.0"}
```

---

## Ingestion (`/ingest/*`)
Admin scope required.

### `POST /ingest/official/pdf`
Upload an official PDF. Creates a `QuestionJob` and spawns a background pipeline.

**Form data:**
| Field | Type | Required | Default |
|---|---|---|---|
| `file` | UploadFile | Yes | — |
| `source_exam_code` | str | No | `""` |
| `source_module_code` | str | No | `""` |
| `provider_name` | str | No | `anthropic` |
| `model_name` | str | No | `claude-sonnet-4-6` |

**Response:** `JobResponse`
```json
{"id": "...", "job_type": "ingest", "status": "parsing", "created_at": "..."}
```

**Notes:**
- Max file size: 50MB
- MIME types validated against allowed set

---

### `POST /ingest/unofficial/file`
Upload a single unofficial asset (PDF, image, markdown, JSON, text).

**Form data:**
| Field | Type | Required | Default |
|---|---|---|---|
| `file` | UploadFile | Yes | — |
| `provider_name` | str | No | `anthropic` |
| `model_name` | str | No | `claude-sonnet-4-6` |

**Response:** `JobResponse`

---

### `POST /ingest/unofficial/batch`
Batch upload multiple unofficial assets.

**Form data:**
| Field | Type | Required |
|---|---|---|
| `files` | list[UploadFile] | Yes |
| `provider_name` | str | No |
| `model_name` | str | No |

**Response:** `list[JobResponse]`

---

### `POST /ingest/reannotate/{question_id}`
Re-run Pass 2 annotation on an existing question.

**Path params:**
| Field | Type |
|---|---|
| `question_id` | UUID string |

**Query params:**
| Field | Type | Default |
|---|---|---|
| `provider_name` | str | `anthropic` |
| `model_name` | str | `claude-sonnet-4-6` |

**Response:** `JobResponse`

---

## Generation (`/generate/*`)
Admin scope required.

### `POST /generate/questions`
Generate questions from a specification.

**Body:** `GenerationRequest`
```json
{
  "target_grammar_role_key": "agreement",
  "target_grammar_focus_key": "subject_verb_agreement",
  "target_syntactic_trap_key": "nearest_noun_attraction",
  "difficulty_overall": "medium",
  "source_question_ids": ["uuid-1", "uuid-2"]
}
```

**Response:** `JobResponse`

---

### `POST /generate/questions/compare`
Generate with multiple LLMs for side-by-side comparison.

**Body:** `GenerationCompareRequest`
```json
{
  "target_grammar_role_key": "agreement",
  "target_grammar_focus_key": "subject_verb_agreement",
  "providers": ["anthropic", "openai"]
}
```

**Response:** `list[JobResponse]`

---

### `GET /generate/runs/{run_id}`
Inspect a generation job or comparison group.

**Response:** Job status or comparison group summary.

---

## Questions (`/questions/*`)
Admin scope required.

### `GET /questions/recall`
Filter and paginate practice questions.

**Query params:**
| Param | Type | Default |
|---|---|---|
| `grammar_focus` | str | None |
| `difficulty` | str | None |
| `origin` | str | None |
| `limit` | int | 20 |
| `offset` | int | 0 |

**Response:** `list[QuestionRecallResponse]`

---

### `GET /questions/{question_id}`
Full question detail including annotation, options, and lineage.

**Response:** `QuestionDetailResponse`

---

### `GET /questions/{question_id}/versions`
Edit history for a question.

**Response:** `list[dict]` with `version_number`, `change_source`, `change_notes`, etc.

---

## Admin (`/admin/*`)
Admin scope required.

### `PATCH /admin/questions/{question_id}`
Edit question content. Creates a new `QuestionVersion` snapshot.

**Body:** `AdminEditRequest`
```json
{
  "question_text": "...",
  "passage_text": "...",
  "correct_option_label": "A",
  "explanation_text": "...",
  "change_notes": "Fixed typo"
}
```

**Response:** `{"id": "...", "version": 2, "changes": [...]}`

---

### `POST /admin/questions/{question_id}/approve`
Set `practice_status = active`.

### `POST /admin/questions/{question_id}/reject`
Set `practice_status = retired`.

### `POST /admin/questions/{question_id}/confirm-overlap`
Set `official_overlap_status = confirmed`.

### `POST /admin/questions/{question_id}/clear-overlap`
Set `official_overlap_status = none`.

---

### `POST /admin/evaluations/{evaluation_id}/score`
Store human evaluation scores for beta model comparison.

**Body:** `EvaluationScoreRequest`
```json
{
  "score_overall": 8.5,
  "score_metadata": 9.0,
  "score_explanation": 8.0,
  "score_generation": 7.5,
  "review_notes": "...",
  "recommended_for_default": true
}
```

---

## Student (`/api/*`)
Student scope required.

### `GET /api/questions`
Practice recall. Same filters as `/questions/recall`.

**Response:** `list[QuestionRecallResponse]`

---

### `POST /api/submit`
Record a student answer attempt.

**Body:** `UserProgressCreate`
```json
{
  "user_id": 1,
  "question_id": "...",
  "is_correct": false,
  "selected_option_label": "B",
  "missed_grammar_focus_key": "subject_verb_agreement",
  "missed_syntactic_trap_key": "nearest_noun_attraction"
}
```

**Response:** `{"id": 123, "is_correct": false}`

---

### `GET /api/stats/{user_id}`
User accuracy stats including top missed focus keys and trap keys.

**Response:** `UserStats`
```json
{
  "total_answered": 42,
  "total_correct": 35,
  "accuracy": 0.833,
  "top_missed_focus_keys": ["subject_verb_agreement", "modifier_placement"],
  "top_missed_trap_keys": ["nearest_noun_attraction"]
}
```
