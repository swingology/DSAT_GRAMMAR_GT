# Visual Stimulus Assets — Marker Backfill and Delivery Plan

**Status:** Proposed design, 2026-07-16.

**Decision:** Charts, graphs, tables, and figures are delivered to students through one
image-first asset contract. Marker-extracted Markdown, HTML, and structured data are retained as
secondary derivatives, but they do not replace the faithful source image in the first release.

---

## 1. Goal

Faithfully extract visual stimuli from source-question PDFs, link them to the correct persisted
question version, store them durably, and render them consistently in diagnostics, practice tests,
drills, and review screens.

The backfill must operate only on relevant PDF pages. It must not regenerate question text,
choices, answers, annotations, or question IDs.

## 2. Why image-first

Marker can often decipher charts and translate tables into Markdown or HTML. That output is useful,
but rebuilding the visual introduces an additional correctness surface: values, axes, legends,
units, blank cells, merged cells, emphasis, ordering, and footnotes can be altered even when the
result looks plausible.

The first release therefore uses the extracted image as the canonical student-visible artifact:

- one backend relationship and response shape for every visual type;
- one shared frontend renderer across every question flow;
- source fidelity without chart-specific rendering code;
- no risk that a reconstructed chart changes the question;
- simpler review, because the reviewer compares the crop directly with the PDF page;
- Marker Markdown/HTML remains available for alt text, search, validation, and future accessible
  table rendering.

Simple tables may be rendered as HTML in a later release after a verification gate is proven. The
faithful image remains stored as the fallback and audit source even then.

## 3. Current seams to reuse

The repository already has most of the required storage and provenance vocabulary:

- `backend/app/parsers/pdf_parser.py` renders PDF pages.
- `backend/app/storage/crop_detector.py` crops normalized regions and stores PNGs.
- `backend/app/storage/object_store.py` provides storage keys and local object persistence.
- `backend/config/storage_layout.yaml` defines page-render, page-crop, and stimulus buckets.
- `QuestionSourceSpan` records PDF page and region provenance.
- `QuestionStimulusAsset` links structured visual data to a question.

The missing end-to-end behavior is:

1. a reliable targeted backfill using Marker;
2. an explicit student-renderable image path on each stimulus asset;
3. version-aware question-to-asset linking;
4. student API serialization;
5. a shared frontend visual renderer;
6. publication and review gates for questions that require visuals.

## 4. Target pipeline

```text
Visually tagged questions without approved assets
    -> group by source PDF
    -> determine unique relevant pages
    -> extract/render only those pages
    -> run a long-lived local Marker worker
    -> collect Figure/Picture/Table blocks and bounding polygons
    -> associate each block with a question
    -> create a faithful image crop with deterministic code
    -> store crop plus Marker derivatives
    -> review ambiguous links/crops
    -> expose approved assets through student APIs
    -> render through one shared frontend component
```

Marker locates and interprets visual blocks. Marker or the PDF renderer supplies the source pixels,
but ordinary deterministic image code performs the final crop. No generative model creates or
redraws the canonical image.

## 5. Phase 1 — Inventory and source manifest

Create a read-only inventory command that selects questions whose `stimulus_mode_key` indicates a
chart, graph, table, figure, quantitative display, or mixed visual stimulus and which do not have an
approved linked visual asset.

The inventory groups questions by:

- source asset or source PDF;
- source test, section, and module;
- source question number;
- known source page number, when available;
- expected visual type derived from `stimulus_mode_key`.

Produce a rerunnable JSON manifest:

```json
{
  "source_pdf": "Test10_ENG_Sec01_Mod01.pdf",
  "source_asset_id": "uuid",
  "pages": [
    {
      "pdf_page": 14,
      "question_ids": ["uuid"],
      "source_question_numbers": [10],
      "expected_asset_types": ["chart"]
    }
  ]
}
```

When old records do not contain page provenance, page discovery is a preprocessing step: scan the
PDF text or Marker page output for the source question number and distinctive question stem. Cache
the resolved page in the manifest so later runs do not repeat discovery.

Acceptance:

- every visually tagged question is classified as `ready`, `already_complete`, `missing_pdf`,
  `page_unresolved`, or `needs_manual_mapping`;
- duplicate pages are processed once per source PDF;
- no database mutation occurs during inventory generation.

## 6. Phase 2 — Targeted PDF preprocessing

For each unique page in the manifest:

1. retain the original PDF as the immutable source;
2. render the page at a configured high resolution, initially 250–300 DPI;
3. normalize page rotation before detection;
4. save the rendered page through the existing object store;
5. record pixel dimensions and the PDF-to-image scale;
6. optionally create a single-page PDF when Marker behaves better on PDF input than PNG input.

Do not launch Marker separately for each page. Load Marker models once in a bounded worker and feed
all selected pages for a source batch through that worker. Prefer Marker page-range processing on
the original PDF when it preserves stable page identifiers.

The worker must have explicit CPU/GPU concurrency and memory limits. It is an offline ingestion
worker, never part of a student request.

## 7. Phase 3 — Marker extraction adapter

Add a Marker adapter behind a project-owned interface rather than spreading Marker-specific types
through the ingestion pipeline.

Run Marker from the isolated uv project at `tools/marker_worker/`. Do not add `marker-pdf` to the
FastAPI backend environment: Marker pins older Pillow, Anthropic, and OpenAI dependencies and needs
its own CUDA-compatible PyTorch build. The worker currently pins Marker 1.10.2 and PyTorch 2.11.0
from the CUDA 12.8 wheel index.

The adapter accepts a selected PDF/page and returns normalized project data:

```json
{
  "page_number": 14,
  "page_width": 1800,
  "page_height": 2400,
  "blocks": [
    {
      "provider_block_id": "...",
      "block_type": "chart",
      "polygon": [[x, y], [x, y], [x, y], [x, y]],
      "image_bytes": "optional",
      "markdown": "optional",
      "html": "optional",
      "structured_data": "optional"
    }
  ]
}
```

Normalize Marker block types into the project vocabulary: `chart`, `graph`, `table`, or `figure`.
Preserve the raw Marker JSON as an immutable extraction artifact for debugging and future parser
upgrades.

Pin the Marker package/model version and store it with each extraction. A later Marker upgrade must
not silently change already approved crops.

## 8. Phase 4 — Question-to-visual association

Associate a Marker visual block with a question using ordered evidence:

1. an explicit question number in or near the visual block;
2. containment within a detected question region;
3. vertical reading order and spatial proximity;
4. distinctive stem text found on the same page;
5. expected visual type from the manifest.

Persist an association score and evidence. Do not auto-publish low-confidence associations.

Proposed states:

- `auto_linked`: strong unambiguous match;
- `needs_review`: multiple candidate questions or visual blocks;
- `manually_linked`: reviewer selected the relationship;
- `rejected`: block is decorative, irrelevant, or incorrectly detected.

Multiple visuals may link to one question. The schema and API must use an ordered array rather than
assuming exactly one asset.

## 9. Phase 5 — Faithful crop production

Use Marker-provided extracted image bytes when testing confirms they preserve the complete visual.
Otherwise crop the high-resolution rendered page using Marker’s polygon.

Crop rules:

- convert the polygon to pixel coordinates using the recorded page dimensions;
- add a small configurable margin, initially 1–2% of page dimensions;
- clamp the crop to page boundaries;
- preserve labels, title, axes, legends, units, source notes, and table footnotes;
- encode losslessly as PNG initially;
- record width, height, MIME type, byte size, and SHA-256 checksum;
- reject degenerate, tiny, blank, or mostly uniform crops;
- never use a generated or redrawn image as the canonical artifact.

Use the checksum and question/version relationship as the idempotency key so a rerun does not create
duplicate assets.

## 10. Phase 6 — Storage and database contract

Store binary images in the existing object-storage layer. Store their durable relationship and
metadata in Postgres. Do not store expiring URLs or base64 payloads in question rows.

Extend `QuestionStimulusAsset` or replace its ambiguous path fields with an explicit contract:

```text
id
question_id
question_version_id
question_job_id
raw_asset_id
source_span_id
stimulus_type
image_storage_path
manifest_storage_path
mime_type
width
height
checksum
title
alt_text
marker_markdown
structured_data_jsonb
render_hints_jsonb
display_order
placement
association_status
review_status
extractor_name
extractor_version
created_at
reviewed_at
```

`image_storage_path` is the canonical student-renderable artifact. Marker Markdown/HTML and
structured data are derivatives. `question_version_id` prevents an edited question from silently
retaining a stale chart.

Create a source span for each visual with source page, polygon/bounding box, rendered page path,
raw asset, and Marker artifact path. This preserves the full audit path from student image back to
the PDF.

## 11. Phase 7 — Admin Dashboard initiation, review, and publication gate

Use the existing **Data Management -> Browse by Test -> Question Detail** workflow as the primary
manual entry point. Do not create a separate visual-ingestion application.

Add a **Visual stimulus** panel to the question detail view:

```text
Visual required:  Yes / No

Expected type:
  Chart/graph | Table | Figure/diagram | Multiple visuals

Source page: [page number]  [Find automatically]

[Save requirement] [Extract with Marker]
```

Saving the requirement and starting extraction are separate actions. An admin must be able to mark
a question for later processing without synchronously starting Marker.

Keep classification and workflow state separate:

- `stimulus_mode_key` describes the question taxonomy and may prepopulate the expected type;
- `visual_required` explicitly says that the question is incomplete without a visual;
- `visual_type` records the admin's canonical expectation (`chart`, `graph`, `table`, `figure`,
  or `mixed`);
- `visual_status` tracks `unmarked`, `marked`, `queued`, `processing`, `needs_review`, `approved`,
  `failed`, or `not_required`;
- `QuestionStimulusAsset` represents each extracted artifact and its own association/review state.

Do not treat `practice_status='needs_review'` as the visual workflow state. General question review
and missing-visual review are different concerns. Likewise, do not infer visual readiness directly
from legacy `stimulus_mode_key` values such as `graph_data`, `graph_and_text`, or `graph_or_table`.

Proposed admin API operations:

```text
PATCH /admin/questions/{question_id}/visual-requirement
POST  /admin/questions/{question_id}/visual-extractions
GET   /admin/questions/{question_id}/visual-extractions/latest
GET   /admin/questions/{question_id}/stimulus-assets
PATCH /admin/stimulus-assets/{asset_id}
POST  /admin/stimulus-assets/{asset_id}/approve
POST  /admin/stimulus-assets/{asset_id}/reject
```

Starting an extraction creates a queued offline job containing the question ID, question version,
source PDF asset, optional page hint, and expected visual type. The HTTP request returns the job ID
immediately; Marker never runs inside the admin request.

The question detail panel then displays the job lifecycle and eventual candidate:

```text
Status: needs review

Source page with polygon        Proposed faithful crop
[page preview]                  [crop preview]

Marker derivatives
- detected type
- title
- Markdown/HTML
- structured data

[Adjust crop] [Relink] [Change type] [Approve] [Reject]
```

Provide a **Browse by Test** bulk action after the single-question path is proven:

1. select several questions;
2. mark them as visual-dependent;
3. choose or confirm expected types and page hints;
4. queue extraction for the unique selected PDF pages;
5. review candidates individually before publication.

Bulk marking must not bulk-approve assets. It may deduplicate page work, but every ambiguous
question-to-visual association remains individually reviewable.

Add an admin review surface that shows:

- question stem and source number;
- full rendered source page;
- proposed crop;
- bounding polygon overlay;
- Marker type, Markdown, and structured extraction;
- association confidence and evidence;
- approve, adjust crop, relink, or reject actions.

A visually dependent question cannot become or remain student-eligible unless every required visual
has an approved asset. Selection queries should exclude questions whose stimulus mode requires a
visual but whose visual readiness check fails.

Approval checks:

- image object exists and checksum matches;
- crop is readable at tablet width;
- no title, legend, axis, unit, note, or relevant cell is clipped;
- question association is correct;
- display order and placement are set;
- alt text or a descriptive derivative exists;
- no answer key or unrelated neighboring question appears in the crop.

## 12. Phase 8 — Student API delivery

Add one shared `StimulusAssetResponse` model and include `stimulus_assets` in every question payload
used by:

- general practice and drills;
- blueprint diagnostics;
- adaptive practice tests;
- missed-question review;
- spaced-repetition or future question surfaces.

Proposed response:

```json
{
  "id": "asset-uuid",
  "type": "chart",
  "title": "Housing Starts in the US",
  "display_order": 0,
  "placement": "before_passage",
  "image_url": "/api/stimulus-assets/asset-uuid/content",
  "mime_type": "image/png",
  "width": 1600,
  "height": 900,
  "alt_text": "...",
  "structured_data": null
}
```

Expose a stable authenticated content endpoint. In local development it reads the local object; in
hosted environments it may redirect to a short-lived signed object-storage URL. Never expose a
filesystem path or internal `local-s3://` URI to the browser.

Bulk-load assets for all questions in a session to avoid an N+1 database query.

## 13. Phase 9 — Shared frontend insertion

Build one `QuestionStimulus` component used everywhere a student sees a question.

Responsibilities:

- order assets by `display_order`;
- place them according to `placement`;
- preserve aspect ratio;
- fit tablet/mobile width without horizontal page overflow;
- allow zoom or full-screen inspection without modifying the image;
- use alt text;
- show a controlled error state when the image cannot load;
- avoid layout shift by using the stored width and height;
- never render internal storage paths directly.

Diagnostics and practice tests must consume the same component and response type. Do not implement
separate chart logic in each runner.

The first release renders every approved visual as an image, including tables. A later verified
table-rendering component may prefer structured HTML while retaining an explicit "view original"
image fallback.

## 14. Phase 10 — Backfill execution

Run the backfill in source-PDF batches:

1. generate and review the inventory manifest;
2. process unique selected pages through the warm Marker worker;
3. persist candidate crops and derivatives;
4. auto-link only high-confidence candidates;
5. manually review ambiguous candidates;
6. approve assets;
7. verify the affected questions in both diagnostic and practice-test runners;
8. emit a batch report before moving to the next PDF.

Each batch report includes:

- questions considered;
- unique pages processed;
- visuals detected;
- auto-linked, manually linked, rejected, and unresolved counts;
- missing source PDFs or unresolved pages;
- crop validation failures;
- questions now student-ready;
- questions still excluded.

The command must support dry-run, resume, and safe rerun behavior.

## 15. Verification strategy

### Backend automated coverage

- Marker output normalization for figure, chart, graph, and table blocks;
- coordinate conversion, margin, clamping, and crop checksum;
- duplicate/rerun idempotency;
- association scoring and ambiguity behavior;
- version-aware asset linking;
- visual-readiness selection gate;
- API response excludes unapproved assets;
- content endpoint authorization and missing-object behavior;
- session payload uses a bulk asset query;
- no answer key is exposed through visual metadata.

### Frontend automated coverage

- diagnostic and practice runners render the same shared component;
- multiple ordered assets render correctly;
- responsive sizing and stored aspect ratio;
- alt text and load-error behavior;
- questions without assets retain their current text layout;
- internal storage paths never appear in image `src` values.

### Manual visual QA set

Include representative cases:

- raster chart;
- vector chart;
- graph with small axis labels;
- boxed spreadsheet-style table;
- table with merged cells or footnotes;
- page with multiple questions;
- page with multiple visuals;
- visual immediately above or below a page break;
- crop near a page edge;
- tablet and mobile rendering.

## 16. Marker Markdown and reconstruction policy

Marker Markdown/HTML is persisted because it is valuable for:

- accessibility descriptions;
- indexing and question search;
- checking that visible numeric values were captured;
- generating structured table data;
- future HTML table rendering;
- reviewer assistance;
- detecting extraction regressions across Marker versions.

It is not the canonical visual in the first release. A reconstruction feature requires its own
acceptance gate proving cell/value parity with the faithful crop. Charts and graphs remain images
unless a future feature explicitly requires interactive rendering and introduces equivalent visual
and numeric validation.

## 17. Non-goals

- Rewriting or regenerating existing questions.
- Replacing the original PDFs.
- Drawing charts with a generative model.
- Making Marker part of a live student HTTP request.
- Publishing unreviewed ambiguous crops.
- Removing stored faithful images after creating Markdown or HTML derivatives.
- Building interactive charts in the first release.

## 18. Recommended implementation order

1. Build a one-PDF spike covering inventory through persisted candidate crops.
2. Confirm Marker image fidelity and question association on representative pages.
3. Finalize the database migration and stable content endpoint.
4. Add the shared student API asset contract.
5. Add the shared frontend component to diagnostics and practice tests.
6. Add publication gating and the minimal review workflow.
7. Run the remaining PDF backfill in resumable batches.
8. Evaluate verified HTML tables only after image delivery is complete and stable.

The spike is successful only when the same persisted crop appears correctly in one diagnostic and
one practice test without any per-runner visual special case.
