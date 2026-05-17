# FastAPI Endpoints

## Health
| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Database health check and API version (public). |

## Users
| Method | Path | Description |
|--------|------|-------------|
| POST | `/users` | Admin creates a new user. |
| GET | `/users` | Admin lists users with pagination (`limit`, `offset`). |
| GET | `/users/{user_id}` | Admin gets a single user by ID. |
| DELETE | `/users/{user_id}` | Admin deletes a user. |

## Questions
| Method | Path | Description |
|--------|------|-------------|
| GET | `/questions/recall` | Admin filters active questions by grammar_focus, difficulty, or origin (paginated). |
| GET | `/questions/{question_id}` | Admin gets full question detail including annotation, options, and lineage. |
| GET | `/questions/{question_id}/versions` | Admin gets version history for a question. |

## Student
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/questions` | Student-facing recall of active practice questions (paginated, filterable). |
| POST | `/api/submit` | Student submits an answer for a question. |
| GET | `/api/stats/{user_id}` | Gets user stats: accuracy, missed grammar/trap keys. |
| POST | `/api/users` | Public self-registration for a new student user. |
| GET | `/api/users` | Admin lists all student users (paginated). |
| GET | `/api/users/{user_id}` | Gets a specific user by ID. |
| DELETE | `/api/users/{user_id}` | Admin deletes a user and their progress records. |

## Admin
| Method | Path | Description |
|--------|------|-------------|
| GET | `/admin/questions` | Admin question list, filterable by practice_status and content_origin (paginated). |
| PATCH | `/admin/questions/{question_id}` | Edits question fields and creates a new version with change_source="admin_edit". |
| POST | `/admin/questions/{question_id}/approve` | Approves a question: sets practice_status to "active" (blocks official questions with unresolved overlaps). |
| POST | `/admin/questions/{question_id}/reject` | Rejects a question: sets practice_status to "retired" and deletes linked annotations/evaluations/relations. |
| DELETE | `/admin/questions/{question_id}` | Hard-deletes a question and all linked data (keeps job records as audit trail). |
| POST | `/admin/questions/{question_id}/confirm-overlap` | Confirms official overlap: sets status to "confirmed" and links canonical official question. |
| POST | `/admin/questions/{question_id}/clear-overlap` | Clears overlap status: resets to "none". |
| POST | `/admin/evaluations/{evaluation_id}/score` | Updates evaluation scores and review notes for an LLM evaluation. |
| POST | `/admin/evaluations` | Creates a new LLM evaluation record linked to a job and question. |
| GET | `/admin/relations` | Lists question relations, optionally filtered by from_question_id or relation_type. |
| POST | `/admin/relations` | Creates a new question relation (validates both questions exist, checks for duplicates). |
| DELETE | `/admin/relations/{relation_id}` | Deletes a question relation. |

## Ingest
| Method | Path | Description |
|--------|------|-------------|
| POST | `/ingest/official/pdf` | Upload official SAT PDF; runs extract → annotate → validate → persist pipeline asynchronously. |
| POST | `/ingest/unofficial/file` | Upload unofficial file (PDF/text/markdown/JSON); runs pipeline asynchronously (images rejected). |
| POST | `/ingest/text` | Submit raw text for ingestion with content_origin and optional source metadata. |
| POST | `/ingest/unofficial/batch` | Batch upload multiple unofficial files; runs pipeline on each. |
| POST | `/ingest/reannotate/{question_id}` | Re-runs the annotation pipeline on an existing question (skips extraction). |
| GET | `/ingest/jobs/{job_id}` | Polls ingest/reannotate job status: returns status, question_id, and validation errors. |

## Generate
| Method | Path | Description |
|--------|------|-------------|
| POST | `/generate/questions` | Generates a new question from a GenerationRequest spec; runs generate → annotate → validate → persist asynchronously. |
| POST | `/generate/questions/compare` | Compares generation across multiple providers; creates one job per provider with a shared comparison_group_id. |
| GET | `/generate/runs/{run_id}` | Looks up a generation run by job ID or comparison group ID. |

## Dashboard
| Method | Path | Description |
|--------|------|-------------|
| GET | `/dashboard` | Returns the main dashboard HTML page (public). |
| GET | `/dashboard/jobs` | HTMX fragment: renders the 30 most recent ingest/generate jobs as an HTML table. |
| GET | `/dashboard/review` | Returns the review queue HTML page (public). |
| GET | `/dashboard/review-items` | HTMX fragment: renders review queue items (questions with needs_review status). |
