# Pipeline

## Ingestion Pipeline

Defined in `app/routers/ingest.py` with background task execution.

### Steps

1. **Upload & Store**
   - File uploaded via multipart form
   - Saved to local archive via `save_asset()`
   - SHA-256 checksum computed for deduplication
   - `QuestionAsset` row created

2. **Parse**
   - PDFs: `pymupdf` extracts text per page + embedded images as base64
   - Text/Markdown: decoded as UTF-8
   - JSON: pretty-printed
   - Images: stored as-is for multimodal processing

3. **Extract (Pass 1)**
   - `build_extract_prompt(raw_text)` constructs system + user prompts
   - LLM outputs structured JSON:
     ```json
     {
       "question_text": "...",
       "passage_text": "...",
       "options": [{"label": "A", "text": "..."}, ...],
       "correct_option_label": "A",
       "source_exam_code": "PT4",
       "stimulus_mode_key": "sentence_only",
       "stem_type_key": "choose_best_grammar_revision"
     }
     ```
   - `extract_json_from_text()` parses JSON from LLM response

4. **Annotate (Pass 2)**
   - `build_annotate_prompt(extract_json)` constructs prompt with V3 rules context
   - LLM outputs full annotation including classification, option analysis, reasoning, generation profile, and confidence
   - Rules file is loaded dynamically and truncated to 8000 chars if too long

5. **Validate**
   - `validate_question(merged_data, content_origin)` runs PRD §15 rules:
     - Blocking: missing `question_text`, wrong number of options, invalid correct label
     - Review: missing explanation
     - Official: requires `source_exam_code`, `source_module_code`, `source_question_number`
     - Generated: requires lineage

6. **Finalize**
   - If any blocking errors: status → `needs_review`
   - Otherwise: status → `approved`

### Background Tasks

Each ingestion endpoint returns a `JobResponse` immediately, then spawns an `asyncio.create_task()` that runs the pipeline in a fresh async session. This keeps the HTTP response fast while allowing long LLM calls to complete off-request.

---

## Generation Pipeline

Defined in `app/routers/generate.py`.

### Steps

1. **Request Validation**
   - `GenerationRequest` specifies `target_grammar_role_key`, `target_grammar_focus_key`, optional `source_question_ids`

2. **Generate**
   - `build_generate_prompt()` constructs system + user prompts
   - LLM outputs a complete question with all V3 fields
   - Temperature: 0.7 for generation

3. **Annotate**
   - Same Pass 2 annotation as ingestion

4. **Validate & Create**
   - Validation rules applied with `content_origin="generated"`
   - `Question` row created automatically on success
   - Job linked to new question via `question_id`

### Multi-Provider Comparison

`POST /generate/questions/compare` accepts a list of provider names. Each provider gets its own `QuestionJob` with a shared `comparison_group_id`. All jobs run in parallel as background tasks.

---

## Reannotation

`POST /ingest/reannotate/{question_id}` fetches the latest job for a question, copies its `pass1_json`, and runs only the Pass 2 annotation step. Used to:
- Re-annotate with a different model
- Re-annotate after rules version updates
- Fix failed annotation jobs
