# Ingestion Architecture - Canonical Current-State Ground Truth

> **Status:** Canonical architecture reference for the currently implemented
> ingestion system.
>
> **Verified:** 2026-06-08 against commit `fe1b64c` plus the working-tree
> ingestion changes present on that date.
>
> **Authority rule:** When this document and code disagree, code is authoritative.
> Update this document in the same change that alters ingestion architecture.
>
> **Scope rule:** This document describes current behavior only. Proposed
> architecture and refactor work belongs in `BACKEND_REFACTOR.md`,
> `TASKS_INGESTION_REFACTOR.md`, or another explicitly non-canonical plan.

## How Agents Must Use This Document

Read this document before changing:

- ingestion HTTP routes or accepted input formats;
- OCR strategy selection, page processing, or fallback order;
- extraction, normalization, annotation, validation, or persistence ordering;
- job statuses, terminal behavior, timeout handling, or recovery;
- `pass1_json`, `pass2_json`, or validation-error shapes;
- database rows or object-store artifacts written by ingestion.

After an architecture-changing edit:

1. Re-read the affected code path.
2. Update every affected diagram and contract table here.
3. Keep planned or desired behavior out of this document.
4. Run the ingestion tests and a documentation diff check.

## Architecture Summary

The ingestion system is an in-process asynchronous pipeline owned primarily by
`backend/app/routers/ingest.py`.

An authenticated request performs synchronous intake work, creates durable
database rows, commits them, schedules a background task, and immediately
returns a job ID. The background task acquires source text, optionally runs OCR,
extracts question structure, annotates questions concurrently, validates and
persists questions serially, and writes a terminal job status.

PostgreSQL is authoritative for job and question state. Object storage contains
supporting source, OCR, layout, crop, and diagnostic artifacts. YAML exports are
non-authoritative convenience snapshots.

```mermaid
flowchart LR
    Admin[Admin or Agent Client]
    API[FastAPI Ingest Router]
    Task[In-Process Background Task]
    Pipeline[Ingestion Pipeline in ingest.py]
    Providers[LLM and OCR Providers]
    DB[(PostgreSQL)]
    Objects[(Object Storage)]
    YAML[(Archive YAML)]

    Admin -->|admin-authenticated request| API
    API -->|create asset and job| DB
    API -->|store upload and page renders| Objects
    API -->|schedule after commit| Task
    API -->|return job ID immediately| Admin
    Task --> Pipeline
    Pipeline <--> Providers
    Pipeline -->|statuses, questions, metadata, links| DB
    Pipeline -->|OCR text, layouts, diagnostics, crops| Objects
    Pipeline -->|non-fatal export| YAML
```

## Current Ownership Map

| Concern | Current owner | Notes |
|---|---|---|
| HTTP intake and pipeline coordination | `backend/app/routers/ingest.py` | This file owns most ingestion behavior. |
| Job concurrency cap | `backend/app/job_limits.py` | Bounds active background jobs. |
| Job transition model | `backend/app/pipeline/orchestrator.py` | Defined, but direct status assignments remain common. |
| PDF text and page rendering | `backend/app/parsers/pdf_parser.py` | Uses PyMuPDF. |
| DeepSeek OCR client | `backend/app/parsers/ocr.py` | Local HTTP OCR adapter. |
| LLM providers | `backend/app/llm/` | Cached provider instances; closed at app shutdown. |
| Extraction and annotation prompts | `backend/app/prompts/` | Pass 1 extraction and Pass 2 annotation. |
| Validation | `backend/app/pipeline/validator.py` | Structural and ontology validation. |
| Overlap detection | `backend/app/pipeline/overlap.py` | Runs for unofficial/generated content. |
| Layout detection and crops | `backend/app/storage/crop_detector.py` | Non-blocking enrichment. |
| Object storage | `backend/app/storage/object_store.py` | Current active implementation is local filesystem. |
| Durable relational state | `backend/app/models/db.py` | SQLAlchemy models backed by PostgreSQL. |

## 1. Public Ingestion Surface

```mermaid
flowchart TD
    Client[Admin Client]

    Official[POST /ingest/official/pdf]
    Unofficial[POST /ingest/unofficial/file]
    Batch[POST /ingest/unofficial/batch]
    Text[POST /ingest/text]
    Reannotate[POST /ingest/reannotate/question_id]
    Benchmark[POST /ingest/benchmark/ocr]
    BenchmarkPoll[GET /ingest/benchmark/ocr/group_id]
    JobPoll[GET /ingest/jobs/job_id]
    GC[POST /ingest/gc/images]

    Intake[Validate and Prepare Intake]
    PersistIntake[Commit Asset and Job Rows]
    Schedule[Schedule Background Task]
    MainPipeline[_run_pipeline_with_session]
    ReannotationPipeline[_run_reannotate_pipeline_with_session]

    Client --> Official
    Client --> Unofficial
    Client --> Batch
    Client --> Text
    Client --> Reannotate
    Client --> Benchmark
    Client --> BenchmarkPoll
    Client --> JobPoll
    Client --> GC

    Official --> Intake
    Unofficial --> Intake
    Text --> Intake
    Batch -->|calls unofficial-file route once per file| Unofficial
    Intake --> PersistIntake --> Schedule --> MainPipeline
    Reannotate --> PersistIntake --> ReannotationPipeline
    Benchmark -->|one job per selected strategy| PersistIntake
    PersistIntake -->|benchmark jobs| MainPipeline
```

### Entry-Point Contracts

| Entry point | Synchronous intake | Background behavior | Durable response evidence |
|---|---|---|---|
| `POST /ingest/official/pdf` | Requires official source identity, validates PDF, checks duplicate checksum against prior jobs, stores raw PDF and all page renders, creates `QuestionAsset` and `QuestionJob`. Duplicate checksums are rejected when a prior job is active or already complete; failed or partial terminal prior jobs may be retried. | Runs normal ingestion pipeline. | Asset row plus ingest job in `parsing`. |
| `POST /ingest/unofficial/file` | Validates file, rejects duplicate checksum, stores raw file, parses supported format, creates asset and job. | Runs normal ingestion pipeline. | Asset row plus ingest job in `parsing`. |
| `POST /ingest/unofficial/batch` | Iterates files and calls `ingest_unofficial_file()` directly for each one. | Each accepted file schedules its own pipeline. | One response/job per accepted file. |
| `POST /ingest/text` | Validates origin and text length, creates a job without an asset row. | Runs normal ingestion pipeline. | Ingest job in `parsing`. |
| `POST /ingest/reannotate/{question_id}` | Loads current question/version, synthesizes one-question `pass1_json`, creates reannotate job. | Runs separate reannotation pipeline; skips extraction. | Reannotate job in `annotating`. |
| `POST /ingest/benchmark/ocr` | Stores one source asset and creates one ingest job per selected OCR strategy under a comparison group. | Runs normal ingestion pipeline for each strategy. | Comparison group ID and job IDs. |
| `GET /ingest/jobs/{job_id}` | Reads one persisted job. | None. | Status, first question ID, validation errors, OCR and LLM metadata. |

### Intake Sequence

```mermaid
sequenceDiagram
    participant Client
    participant Route as Ingest Route
    participant Parser as PDF or Image Parser
    participant Obj as Object Store
    participant DB as PostgreSQL
    participant Limit as Job Semaphore
    participant Pipeline as Background Pipeline

    Client->>Route: authenticated ingest request
    Route->>Route: validate MIME, size, metadata, checksum
    Route->>Obj: store raw source when file-based
    opt PDF or image input
        Route->>Parser: parse source
        Parser-->>Route: raw text, page text, page renders
        Route->>Obj: store full-page renders
    end
    Route->>DB: add QuestionAsset when file-based
    Route->>DB: add QuestionJob with seeded pass1_json
    Route->>DB: commit
    Route-->>Limit: schedule task through run_with_job_limit
    Route-->>Client: return job ID and initial status
    Limit->>Pipeline: run with fresh async DB session
```

## 2. Seeded Job Data

Before the background pipeline starts, `QuestionJob.pass1_json` acts as an
internal, untyped handoff envelope.

Common seed keys:

| Key | Meaning |
|---|---|
| `raw_text` | Embedded PDF text, decoded file text, JSON text, or pasted text. File paths may store only the first 100,000 characters. |
| `_truncated` | Indicates the intake text exceeded the stored preview length. |
| `_page_images` | Stored page-render descriptors used by OCR/layout processing. |
| `_page_texts` | Per-page embedded text used to detect mixed PDFs. |
| `_ocr_strategy` | Requested OCR strategy or `null`. |
| `source_metadata` | Form-submitted source identity and page count. |

The pipeline later replaces or extends this envelope with extracted question
data, provider metadata, OCR metadata, diagnostic paths, and created question
IDs.

## 3. Source Acquisition and OCR Decision Flow

```mermaid
flowchart TD
    Start[Pipeline loads seeded pass1_json]
    HasText{raw_text is non-empty?}
    PageText{_page_texts contains blank pages?}
    PartialImages{matching page renders found?}
    Bypass[Set _ocr_strategy=bypassed]
    Preserve[Preserve full embedded text and OCR blank pages only]
    HasImages{page image entries available?}
    FailNoText[Fail job: no_raw_text]
    Resolve[Resolve requested or configured OCR strategy]
    Chain[Build fallback chain]
    Try[Try each strategy until success]
    TwoStep{Strategy mode}
    GLM[GLM pagewise vision OCR]
    DeepSeek[DeepSeek pagewise OCR]
    VlmPdf[VLM pagewise OCR for PDF]
    VlmFused[VLM fused OCR plus extraction for non-PDF]
    Merge[Append OCR text to preserved embedded text for mixed PDF]
    Pass1[Continue to Pass 1 text extraction]
    SkipPass1[Set _vision_fused_ sentinel and skip Pass 1]
    FailOCR[Fail job after fallback exhaustion]

    Start --> HasText
    HasText -->|yes| PageText
    PageText -->|no blank pages| Bypass --> Pass1
    PageText -->|blank pages exist| PartialImages
    PartialImages -->|yes| Preserve --> Resolve
    PartialImages -->|no| Bypass
    HasText -->|no| HasImages
    HasImages -->|no| FailNoText
    HasImages -->|yes| Resolve
    Resolve --> Chain --> Try --> TwoStep
    TwoStep -->|glm| GLM --> Merge
    TwoStep -->|deepseek| DeepSeek --> Merge
    TwoStep -->|ollama, anthropic, openai and PDF| VlmPdf --> Merge
    TwoStep -->|ollama, anthropic, openai and non-PDF| VlmFused --> SkipPass1
    Merge --> Pass1
    Try -->|all fail| FailOCR
```

### OCR Strategy Contract

| Strategy | Adapter | PDF behavior | Non-PDF image behavior | On success |
|---|---|---|---|---|
| `glm` | Temporary `OllamaProvider` using `glm_ocr_model` | One vision request per page, bounded concurrency, sequential retry for blank pages. | Same pagewise helper over available image entries. | Produces raw OCR text; Pass 1 still runs. |
| `deepseek` | Cached `DeepSeekOCRClient` | One OCR request per page, bounded concurrency, sequential retry for blank pages. | Same helper over available image entries. | Produces raw OCR text; Pass 1 still runs. |
| `ollama` | Cached LLM provider | Pagewise OCR, then text Pass 1. | Fused vision extraction with up to three JSON-parse attempts. | PDF produces raw text; non-PDF may populate extraction directly. |
| `anthropic` | Cached LLM provider | Pagewise OCR, then text Pass 1. | Fused vision extraction. | Same mode distinction as Ollama. |
| `openai` | Cached LLM provider | Pagewise OCR, then text Pass 1. | Fused vision extraction. | Same mode distinction as Ollama. |

### OCR Fallback Order

The resolved strategy is attempted first. When `ocr_fallback` is enabled, the
remaining configured strategies follow in this preference order:

```text
glm -> deepseek -> anthropic -> openai -> ollama
```

The chain is configuration-dependent. A strategy is omitted when its required
model, key, or endpoint is unavailable.

### OCR Side Effects

Successful OCR can write:

- `pass1_json.raw_text`;
- `pass1_json._ocr_meta`;
- one `ocr_text` object-store artifact;
- per-page latency, character count, and token usage;
- later, one `ocr_diagnostics` artifact.

OCR failure is blocking. Layout detection failure is not.

## 4. Main Pipeline Flow

```mermaid
flowchart TD
    Start[_run_pipeline job and DB session]
    Acquire[Acquire usable text or fused extraction]
    P1{Fused extraction already populated?}
    Extract[Pass 1 text extraction with JSON retry]
    Normalize[Normalize, split passages, clean labels, deduplicate]
    Metadata[Apply form metadata and shared extracted metadata]
    QNum[Official number checks and OCR cross-check]
    Layout[Optional non-blocking layout detection and diagnostics]
    Prewarm[Pre-warm annotation cache once per detected domain]
    Annotate[Concurrent bounded Pass 2 annotation]
    Serial[Serial per-question validate and persist loop]
    Finalize[Assemble pass2_json, errors, created IDs, final status]
    Commit[Commit terminal state]

    Start --> Acquire --> P1
    P1 -->|no| Extract --> Normalize
    P1 -->|yes| Normalize
    Normalize --> Metadata --> QNum --> Layout --> Prewarm --> Annotate --> Serial --> Finalize --> Commit
```

### Complete Pipeline Sequence

```mermaid
sequenceDiagram
    participant Runner as Session Runner
    participant Pipe as _run_pipeline
    participant OCR as OCR or Vision Provider
    participant Extract as Extraction LLM
    participant Layout as Layout Detector
    participant Annotate as Annotation LLM
    participant Overlap as Overlap Detector
    participant Persist as _persist_single_question
    participant DB as PostgreSQL
    participant Obj as Object Store

    Runner->>Pipe: run with pipeline timeout
    Pipe->>DB: load and mutate QuestionJob

    alt raw text absent or mixed PDF
        Pipe->>OCR: try ordered OCR chain
        OCR-->>Pipe: OCR text or fused extraction
        Pipe->>Obj: store OCR text
        Pipe->>DB: persist OCR metadata/status checkpoints
    end

    opt Pass 1 not already completed by fused vision
        Pipe->>Extract: text extraction call
        Extract-->>Pipe: structured question JSON
    end

    Pipe->>Pipe: normalize and deduplicate questions
    Pipe->>Pipe: official number validation and OCR cross-check

    opt layout enabled and page renders exist
        Pipe->>Layout: detect question/table/chart/figure regions
        Layout-->>Pipe: page-indexed regions or empty result
        Pipe->>Obj: store layout JSON and OCR diagnostics
    end

    Pipe->>Annotate: pre-warm static rules per domain
    Pipe->>DB: status=annotating and commit

    par bounded concurrent annotation calls
        Pipe->>Annotate: annotate question N
        Annotate-->>Pipe: annotation JSON and usage metadata
    end

    loop each question in original order
        Pipe->>Pipe: capture amendment proposal if present
        opt unofficial or generated
            Pipe->>DB: status=overlap_checking and commit
            Pipe->>Overlap: find official overlap candidates
            Overlap-->>Pipe: overlap records
        end
        Pipe->>Pipe: merge extraction and annotation, then validate
        opt no blocking validation errors
            Pipe->>Persist: persist question inside DB savepoint
            Persist->>Obj: optional crop and stimulus annotation artifacts
            Persist->>DB: question, version, annotation, options, spans, stimuli, relations
            Pipe->>DB: add question_job_questions link
            Pipe->>Obj: non-fatal YAML export
        end
    end

    Pipe->>DB: persist pass2_json, validation records, first question ID, created IDs, terminal status
    Pipe->>DB: final commit
```

## 5. Normalization, Validation, and Annotation

### Pass 1 Extraction

Pass 1 converts usable raw text into one question object or a `questions` array.
It retries JSON/structural failures up to three attempts with backoff. Parsed
JSON that contains no non-empty `question_text` is treated as a retryable
failure. For official jobs with known subject/module counts, parsed extractions
that return too few questions are also retried before annotation; retry prompts
include the missing printed question numbers inferred from the expected module
range. If the final attempt is still short, the pipeline continues with the
partial extraction and the module-completeness safety net routes the job to
`needs_review`.

Pass 1 stores:

- the extracted root payload;
- source metadata;
- raw text;
- preserved page-image and OCR-artifact descriptors;
- `_llm_meta`;
- preserved `_ocr_meta`, when present.

### Normalization

`_normalize_extracted_questions()`:

- supports single-question and multi-question response shapes;
- merges shared source metadata into each question;
- cleans answer labels and options;
- splits passage text accidentally embedded in question text;
- attempts passage recovery from raw text;
- removes empty and duplicate questions;
- returns normalization issues instead of silently dropping them.

### Official Number Validation

For official ingestion only:

- question numbers are checked for null/non-integer values;
- subject/module expected ranges are checked;
- duplicates and gaps are reported;
- numbers are cross-checked against OCR/raw text when available.
- final extracted and created question counts are checked against the expected
  official module count when subject/module metadata is known.

Any pre-persist warning currently sets `defer_activation=True` for the entire
job, causing persisted questions to remain drafts and the job to end in
`needs_review`.

### Pass 2 Annotation

```mermaid
flowchart LR
    Questions[Normalized questions]
    Sort[Sort indices by detected domain]
    Warm[Serial cache pre-warm per distinct domain]
    Gather[asyncio.gather with annotation semaphore]
    Parse[Parse, normalize, enforce domain nullability]
    Index[Map result back to original question index]
    Serial[Serial validation and persistence]

    Questions --> Sort --> Warm --> Gather --> Parse --> Index --> Serial
```

Annotation calls are concurrent but bounded by
`settings.annotation_max_concurrent`. Validation and persistence remain serial.

## 6. Per-Question Processing and Persistence

```mermaid
flowchart TD
    Item[Question plus annotation result]
    AnnotationOK{Annotation succeeded?}
    RecordError[Record annotation error and skip]
    Amendment[Capture optional amendment proposal]
    Origin{Unofficial or generated?}
    Overlap[Detect overlaps]
    Validate[Validate merged extraction and annotation]
    Blocking{Blocking validation error?}
    RecordValidation[Record validation errors and skip]
    Savepoint[Open nested DB savepoint]
    Identity[Resolve deterministic official identity or UUID4]
    Existing{Official question already exists?}
    PersistRows[Add question, version, annotation, options]
    Enrich[Crop/layout/stimulus enrichment and source spans]
    Relations[Persist overlap relations]
    Link[Add question_job_questions link]
    Export[Non-fatal YAML export]
    PersistFailure[Record persistence error and continue]

    Item --> AnnotationOK
    AnnotationOK -->|no| RecordError
    AnnotationOK -->|yes| Amendment --> Origin
    Origin -->|yes| Overlap --> Validate
    Origin -->|no| Validate
    Validate --> Blocking
    Blocking -->|yes| RecordValidation
    Blocking -->|no| Savepoint --> Identity --> Existing
    Existing -->|yes| Link
    Existing -->|no| PersistRows --> Enrich --> Relations --> Link --> Export
    Savepoint -->|exception| PersistFailure
```

### Persistence Contract

| Behavior | Current implementation |
|---|---|
| Transaction isolation | Each question is persisted inside `db.begin_nested()` so one question can fail without rolling back successful siblings. |
| Official identity | Complete, non-suspect official identity produces deterministic UUID5. Existing official identity returns the existing question ID. |
| Primary job question | `question_jobs.question_id` points to the first successfully linked question. |
| Complete job links | `question_job_questions` links the job to every successfully produced or reused question ID. |
| Activation | Official questions are usually drafts unless testing auto-activation is enabled. Any job-level warning defers activation. Unofficial questions default active. |
| External I/O | Layout crops, stimulus annotation, object-store writes, and YAML export currently occur within or adjacent to persistence processing. |
| Export failure | Logged and non-fatal. |

## 7. Durable Database Model

```mermaid
erDiagram
    QUESTION_ASSETS ||--o{ QUESTION_JOBS : raw_asset_id
    QUESTION_JOBS ||--o{ QUESTION_JOB_QUESTIONS : produces
    QUESTIONS ||--o{ QUESTION_JOB_QUESTIONS : linked_from_job
    QUESTION_JOBS }o--o| QUESTIONS : primary_question_id
    QUESTIONS ||--o{ QUESTION_VERSIONS : versions
    QUESTIONS ||--o{ QUESTION_ANNOTATIONS : annotations
    QUESTION_VERSIONS ||--o{ QUESTION_ANNOTATIONS : annotated_version
    QUESTIONS ||--o{ QUESTION_OPTIONS : options
    QUESTION_VERSIONS ||--o{ QUESTION_OPTIONS : versioned_options
    QUESTIONS ||--o{ QUESTION_SOURCE_SPANS : source_provenance
    QUESTION_JOBS ||--o{ QUESTION_SOURCE_SPANS : created_by_job
    QUESTION_ASSETS ||--o{ QUESTION_SOURCE_SPANS : source_asset
    QUESTIONS ||--o{ QUESTION_STIMULUS_ASSETS : stimuli
    QUESTION_SOURCE_SPANS ||--o{ QUESTION_STIMULUS_ASSETS : derived_from_span
    QUESTIONS ||--o{ QUESTION_RELATIONS : from_question
    QUESTIONS ||--o{ QUESTION_RELATIONS : to_question
```

### Database Authority

| Table | Ingestion responsibility |
|---|---|
| `question_jobs` | Pipeline state, intermediate JSON, validation records, provider/model attribution, first question ID. |
| `question_assets` | Uploaded source identity, checksum, MIME type, source metadata, raw object-storage path. |
| `question_job_questions` | Complete set of questions produced or reused by one job. |
| `questions` | Current question state and source identity. |
| `question_versions` | Versioned content snapshot. |
| `question_annotations` | Pass 2 annotation, explanations, confidence, generation profile, rules attribution. |
| `question_options` | Version-scoped options and option-level analysis. |
| `question_source_spans` | Page/crop/OCR/layout provenance. |
| `question_stimulus_assets` | Stored visual/structured stimulus artifacts. |
| `question_relations` | Overlap and lineage relationships. |

## 8. Object-Store and Export Artifacts

```mermaid
flowchart LR
    Source[Uploaded Source]
    Raw[raw_source_pdf or raw_source_file]
    Render[rendered_page]
    OCR[ocr_text]
    Layout[ocr_layout]
    Diag[ocr_diagnostics]
    QCrop[question_crop]
    StimCrop[table_crop, chart_crop, figure_crop]
    StimData[table_asset, chart_asset, figure_asset]
    YAML[archive YAML]

    Source --> Raw
    Source --> Render
    Render --> OCR
    Render --> Layout
    Layout --> QCrop
    Layout --> StimCrop
    StimCrop --> StimData
    OCR --> Diag
    Raw -. authoritative path in question_assets .-> DB[(PostgreSQL)]
    Render -. referenced by source spans and pass1_json .-> DB
    OCR -. referenced by OCR metadata and source spans .-> DB
    Layout -. referenced by source spans .-> DB
    QCrop -. referenced by source spans .-> DB
    StimData -. referenced by stimulus assets .-> DB
    DB --> YAML
```

PostgreSQL is authoritative for whether a question was persisted. Object-store
artifacts support provenance and debugging. YAML export is not authoritative and
does not control job success.

## 9. Persisted Job Status Behavior

### Defined State Model

```mermaid
stateDiagram-v2
    [*] --> pending
    pending --> parsing
    pending --> extracting
    parsing --> extracting
    extracting --> annotating
    annotating --> overlap_checking: unofficial or generated
    annotating --> validating: official
    overlap_checking --> validating
    validating --> approved
    validating --> needs_review
    pending --> failed
    parsing --> failed
    extracting --> failed
    annotating --> failed
    overlap_checking --> failed
    validating --> failed
    approved --> [*]
    needs_review --> [*]
    failed --> [*]
```

### Current Implementation Reality

- Intake-created ingest jobs begin at `parsing`.
- The pipeline directly assigns and commits statuses at several checkpoints.
- `JobOrchestrator` is instantiated and used for some OCR/extraction transitions
  and error construction, but it does not currently own all persisted status
  changes.
- During multi-question unofficial processing, `overlap_checking` and
  `validating` may be committed repeatedly.
- Terminal status is:
  - `approved` when at least one question succeeds, no review condition applies,
    and known official module counts are complete;
  - `needs_review` when at least one question succeeds and official activation or
    warnings require review, including an incomplete official module count;
  - `failed` when no question succeeds or a blocking pipeline stage fails.

### Recovery and Timeout Paths

```mermaid
flowchart TD
    Run[Background pipeline]
    Timeout{Exceeds pipeline_timeout_s?}
    Fresh[Open fresh DB session]
    MarkTimeout[Mark non-terminal job failed with pipeline_timeout error]
    Restart[Application startup]
    StartupScan[Mark all in-progress jobs failed with startup_recovery error]
    Sweep[Periodic stuck-job sweeper]
    Old{updated_at older than timeout cutoff?}
    MarkSweep[Mark failed with sweeper error]

    Run --> Timeout
    Timeout -->|yes| Fresh --> MarkTimeout
    Restart --> StartupScan
    Sweep --> Old
    Old -->|yes| MarkSweep
```

## 10. Failure and Partial-Success Semantics

```mermaid
flowchart TD
    Job[Ingestion Job]
    OCRFail{All OCR strategies fail?}
    P1Fail{Pass 1 retry exhausted?}
    Questions[Normalized questions]
    Each[Process each question]
    AnnFail{Annotation failed?}
    ValFail{Blocking validation?}
    PersistFail{Savepoint persistence failed?}
    Success[Record created or reused question ID]
    Count{Any successful question IDs?}
    Review{Any warnings/errors or official review hold?}
    Approved[approved]
    NeedsReview[needs_review]
    Failed[failed]

    Job --> OCRFail
    OCRFail -->|yes| Failed
    OCRFail -->|no| P1Fail
    P1Fail -->|yes| Failed
    P1Fail -->|no| Questions --> Each
    Each --> AnnFail
    AnnFail -->|yes| Each
    AnnFail -->|no| ValFail
    ValFail -->|yes| Each
    ValFail -->|no| PersistFail
    PersistFail -->|yes| Each
    PersistFail -->|no| Success --> Each
    Each --> Count
    Count -->|no| Failed
    Count -->|yes| Review
    Review -->|yes| NeedsReview
    Review -->|no| Approved
```

### Blocking Versus Non-Blocking Behavior

| Event | Blocking? | Persisted result |
|---|---|---|
| No OCR provider or all OCR fallbacks fail | Yes, entire job | Job becomes `failed`; OCR error stored. |
| No usable raw text | Yes, entire job | Job becomes `failed`. |
| Pass 1 retry exhaustion | Yes, entire job | Job becomes `failed`; extraction error stored. |
| Normalization drop | No for sibling questions | Issue is stored; surviving questions continue. |
| Official number, OCR cross-check, or module-completeness warning | No for persistence, yes for activation | Questions continue as drafts; job becomes `needs_review`. |
| Layout detection or diagnostics write failure | No | Logged; pipeline continues. |
| One annotation failure | No for sibling questions | Issue stored; failed question skipped. |
| One blocking validation result | No for sibling questions | Issue stored; failed question skipped. |
| One savepoint persistence failure | No for sibling questions | Issue stored; successful siblings remain. |
| YAML export failure | No | Logged only; DB persistence remains authoritative. |
| Pipeline timeout | Yes | Fresh session marks non-terminal job `failed`. |

## 11. Reannotation Flow

Reannotation is a separate pipeline. It does not call `_run_pipeline()`.

```mermaid
flowchart TD
    Request[POST /ingest/reannotate/question_id]
    Load[Load current Question and latest QuestionVersion]
    Synthesize[Synthesize one-question pass1_json]
    Job[Create reannotate QuestionJob]
    Annotate[Pass 2 annotation only]
    Validate[Validate merged current content and new annotation]
    Blocking{Blocking errors?}
    Review[needs_review]
    Version[Create new QuestionVersion and QuestionAnnotation]
    Options[Clone current-version options with new annotation fields]
    Update[Update Question latest IDs and explanation]
    Approved[approved]

    Request --> Load --> Synthesize --> Job --> Annotate --> Validate --> Blocking
    Blocking -->|yes| Review
    Blocking -->|no| Version --> Options --> Update --> Approved
```

## 12. OCR Benchmark Flow

The OCR benchmark endpoint uses the production ingestion pipeline rather than a
separate benchmark-only extractor.

```mermaid
flowchart LR
    Upload[One benchmark upload]
    Asset[One QuestionAsset]
    Select[Resolve requested or available strategies]
    Jobs[Create one ingest job per strategy]
    Run[Run normal ingestion pipeline for each job]
    Group[comparison_group_id]
    Poll[GET benchmark group]
    Compare[Compare status, OCR metadata, extracted count, created count, errors]

    Upload --> Asset --> Select --> Jobs --> Run
    Jobs --> Group --> Poll --> Compare
```

## 13. Known Current Inconsistencies

These are current-code facts, not target architecture:

1. `backend/app/routers/ingest.py` owns intake, OCR, coordination, enrichment,
   persistence, and finalization in one large module.
2. `JobOrchestrator` defines a transition interface, but direct persisted status
   assignments bypass it in much of the pipeline.
3. `pass1_json` and `pass2_json` are untyped internal protocols with private
   underscore-prefixed keys and the `_vision_fused_` sentinel.
4. `ingest_unofficial_batch()` calls the single-file HTTP route function directly.
5. File intake stores only a 100,000-character raw-text preview in the seeded
   job envelope.
6. External enrichment and export work is interleaved with persistence processing.
7. Layout detection is broad and non-blocking; missing layout output can leave
   visual stimuli without crops.
8. Background tasks are in-process. Startup recovery marks interrupted jobs
   failed rather than resuming them.

Track proposed fixes outside this document. Remove an inconsistency from this
list only after the code changes.

## 14. Architecture Update Checklist

When ingestion architecture changes, update:

- [ ] public entry-point diagram and contract table;
- [ ] seeded `pass1_json` contract;
- [ ] OCR/source-acquisition decision diagram and fallback order;
- [ ] complete pipeline sequence and stage ordering;
- [ ] concurrency statements for annotation and OCR;
- [ ] per-question processing and transaction semantics;
- [ ] database entity and object-artifact diagrams;
- [ ] status, recovery, timeout, and terminal rules;
- [ ] blocking/non-blocking failure table;
- [ ] known current inconsistencies;
- [ ] verified date and commit/worktree note.

Then run:

```bash
git diff --check -- docs/backend/INGESTION_ARCHITECTURE.md
cd backend
uv run pytest tests/test_ingest_router.py tests/test_pipeline.py tests/test_backend_regressions.py -q
```
