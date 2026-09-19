# DSAT annotation guide and JSON template

This guide describes the existing annotation fields and the deep-analysis
extension used by `/deep-question-analysis <question UUID>`. The JSON below is
a **review-artifact template**, not a new database/API payload. Empty arrays and
nulls are placeholders to fill from evidence, not a completed annotation.

Authorities: [core standard](STANDARD.md), [active vocabulary](../vocabulary/master.json),
[College Board crosswalk](vocabulary/v1.0.0/crosswalk.json), and
[deep analysis 1.0.0](deep_analysis/1.0.0/RULES.md). DA-001 in the extension records
the new local vocabulary. No existing database annotations are rewritten.

## 1. What “family” means

There are three separate groupings: the assessed question family, the skill
family within it, and the annotation family describing an aspect of the item.
An Inferences question remains a reading question even when its analysis maps
every grammatical clause. Incidental grammar does not change its assessed skill.

| Production question family | College Board domain | Scope |
|---|---|---|
| `information_and_ideas` | Information and Ideas | Central Ideas and Details; Command of Evidence; Inferences |
| `craft_and_structure` | Craft and Structure | Words in Context; Text Structure and Purpose; Cross-Text Connections |
| `expression_of_ideas` | Expression of Ideas | Rhetorical Synthesis; Transitions |
| `conventions_grammar` | Standard English Conventions | Boundaries; Form, Structure, and Sense |

The seven current reading skill-family keys are `central_ideas_and_details`,
`command_of_evidence_textual`, `command_of_evidence_quantitative`, `inferences`,
`words_in_context`, `text_structure_and_purpose`, and `cross_text_connections`.
Textual and Quantitative are internal subdivisions of Command of Evidence.
Use `READING_FOCUS_BY_SKILL_FAMILY` to select a focus under the correct parent.

Grammar role keys group the current internal rules: `sentence_boundary`,
`agreement`, `verb_form`, `modifier`, `punctuation`, `parallel_structure`,
`pronoun`, and `expression_of_ideas`. These are internal organizational terms;
they do not correspond one-for-one to the official domains. Grammar focus keys
must belong to their role in `GRAMMAR_FOCUS_BY_ROLE`. For synthesis and
transitions, consult the explicit crosswalk and existing rule route rather than
forcing them into a reading-only skill-family field.

## 2. Annotation families

| Annotation family | What it answers | Main contents |
|---|---|---|
| Source/provenance | Which exact item and version is this? | UUID, year/test/section/module/number, original text, key, version, annotation, assets, retrieval and analysis versions |
| Assessed classification | What is being tested? | Question family, grammar role/focus or reading skill/focus, secondary focuses, rationale |
| Evidence/reasoning | Why does the answer follow? | Evidence scope/location, premises, qualification, inference bridge, answer mechanism, solver pattern |
| Sentence/clause anatomy | How is the language built? | Sentences, clause form/function, verbs, subjects, heads, complements, modifiers, punctuation |
| Controllers/dependencies | Which element governs or refers to which? | Agreement controller, antecedent, understood subject, attachment, coordination, scope |
| Disruptors/traps | What invites a mistaken interpretation? | Observable disrupting span, affected dependency, question-level trap, hypothesized error |
| Option anatomy | Why is each choice attractive and right/wrong? | Canonical distractor/plausibility/failure keys, partial truth, violated constraint, defeating evidence |
| Style/discourse | How does the passage communicate? | Register, attribution, hedging, information flow, architecture, cohesion, parallelism |
| Difficulty/quality | What makes it demanding or defective? | Stored and estimated difficulty, competing options, shortcuts, ambiguity, uniqueness |
| Confidence/review | What is established and what needs review? | Status, uncertainty, annotation gaps, proposed corrections, validation and generation lessons |

## 3. Existing annotation field inventory

These fields are declared in [the annotation model](../backend/app/models/annotation.py).
Persisted annotations can also contain legacy/additional JSON keys. Preserve the
complete original snapshot rather than dropping keys absent from this inventory.

| Group | Fields | Interpretation |
|---|---|---|
| Classification | `question_family_key`, `grammar_role_key`, `grammar_focus_key`, `secondary_grammar_focus_keys`, `skill_family_key`, `reading_focus_key`, `secondary_reading_focus_keys` | Controlled labels and parent relationships; reading grammar role/focus are null |
| Legacy/descriptive classification | `skill_family`, `subskill`, `transition_subtype_key`, `disambiguation_rule_applied`, `classification_rationale` | Preserve source labels; canonical keyed fields govern current classification |
| Traps | `reasoning_trap_key`, `syntactic_trap_key` | Question-level reasoning or syntax mechanism; distinct from wrong-choice type |
| Content/style | `topic_broad`, `topic_fine`, `register` (Python attribute `register_label`), `tone`, `passage_architecture_key` | Subject matter, prose register, stance and passage organization |
| Reasoning | `evidence_scope_key`, `evidence_location_key`, `answer_mechanism_key`, `solver_pattern_key`, `reading_scope`, `reasoning_demand` | Evidence extent/location, warrant and solving procedure |
| Difficulty | `difficulty_overall`, `difficulty_reading`, `difficulty_grammar`, `difficulty_inference`, `difficulty_vocab`, `distractor_strength` | Existing qualitative ratings; overall keys are `low`, `medium`, `high` |
| Explanation | `explanation_short`, `explanation_full`, `evidence_span_text` | Model limits: 300 and 2,000 characters for short/full explanation; detailed report lives separately |
| Review | `annotation_confidence`, `needs_human_review`, `review_notes` | Confidence 0–1, review flag and reason; confidence is not empirical accuracy |
| Optional quality | `distractor_distance`, `distractor_competition_score`, `plausible_wrong_count`, `answer_separation_strength`, `official_similarity_score`, `structural_similarity_score`, `empirical_difficulty_estimate` | Optional diagnostics; scores require a stated method, empirical estimates require data |

The database annotation row also stores provider/model, prompt/rules versions,
timestamps, `annotation_jsonb`, `explanation_jsonb`, `confidence_jsonb`,
`generation_profile_jsonb`, `passage_spans`, `span_annotated_at`, and
`span_model_name`. These are separate containers/metadata, not all members of the
Pydantic annotation object.

Option rows contain text/identity/version, `is_correct`, `option_role`,
`distractor_type_key`, `semantic_relation_key`, `plausibility_source_key`,
`option_error_focus_key`, `why_plausible`, `why_wrong`, `student_failure_mode_key`,
and optional fit/quality diagnostics. Export preserves every actual column.
Do not assume every stored value has a dedicated vocabulary category or validator.

Existing `passage_spans` holds `tokens`, `label`, `anatomy_present`,
`concepts_present`, and a source field. Token objects contain `text`, `anatomy`,
`concept_tags`, `is_blank`. Their text must concatenate to the exact source.
Deep analysis adds explicit cross-span relations and evidence; it does not
replace these historical tokens.

## 4. Deep-analysis JSON template

Save alongside the Markdown report when structured output is requested. The
skill always saves the unmodified fetch as `.source.json`; this template is an
additional analysis object, never a substitute for that source snapshot.
All `null` example classification fields require evidence-based completion.

```json
{
  "analysis_standard": "deep_analysis/1.0.0",
  "core_standard": "1.0.0",
  "vocabulary_sha256": null,
  "question_id": null,
  "source": {
    "snapshot_file": null,
    "retrieved_at": null,
    "question_version_id": null,
    "annotation_id": null,
    "year": null,
    "test_number": null,
    "section": null,
    "module": null,
    "question_number": null,
    "content_origin": null,
    "text_version_conflicts": []
  },
  "classification": {
    "question_family_key": null,
    "skill_family_key": null,
    "reading_focus_key": null,
    "secondary_reading_focus_keys": [],
    "grammar_role_key": null,
    "grammar_focus_key": null,
    "secondary_grammar_focus_keys": [],
    "reasoning_trap_key": null,
    "syntactic_trap_key": null,
    "answer_mechanism_key": null,
    "solver_pattern_key": null,
    "rationale": null
  },
  "spans": [],
  "sentences": [],
  "clauses": [],
  "relations": [],
  "evidence_map": [],
  "disruptors": [],
  "options": [
    {"label": "A", "analysis": null},
    {"label": "B", "analysis": null},
    {"label": "C", "analysis": null},
    {"label": "D", "analysis": null}
  ],
  "style_observations": [],
  "difficulty": {
    "stored": null,
    "requested": null,
    "analyst_estimate": null,
    "rationale": null,
    "empirical_measurements": null
  },
  "quality_checks": [],
  "annotation_gaps": [],
  "generation_constraints": [],
  "review": {
    "status": "unknown",
    "needs_human_review": true,
    "findings": [],
    "analyst": null,
    "model": null,
    "analyzed_at": null
  }
}
```

## 5. Objects inside the template

Each table row describes one array element. Fields named `*_key` retain their
existing vocabulary where available; fields marked `da.*` use the extension's
closed lists. Do not put the string `unknown` into a production enum field.

| Array | Element fields | Notes |
|---|---|---|
| `spans` | `id`, `source_field`, `quote`, `occurrence`, optional `start`, `end` | Exact source text; occurrence is 1-based; optional offsets are Unicode code points, 0-based/end-exclusive |
| `sentences` | `id`, `span_id`, `clause_ids`, `discourse_role`, `notes` | Cover every passage sentence and option; describe stem/blank requirements |
| `clauses` | `id`, `span_id`, `form`, `function`, `finite_verb_span_ids`, `subject_span_id`, `head_span_id`, `tense_aspect_voice`, `notes`, `status` | Form and function use separate `da.*` categories; null where inapplicable |
| `relations` | `type`, `from_span_id`, `to_span_id`, `explanation`, `status` | `type` uses `da.relation`; direction is controller/modifier/etc. to governed element; coordination symmetric |
| `evidence_map` | `span_ids`, `role`, `premise`, `inference_bridge`, `limitation`, `status` | Role uses `da.evidence_role`; distinguish text from inference |
| `disruptors` | `type`, `span_ids`, `affected_relation`, `canonical_trap_key`, `explanation`, `status` | Type uses `da.disruptor`; canonical trap must match its production category |
| `style_observations` | `feature`, `span_ids`, `description`, `measurement`, `status` | Feature uses `da.style_feature`; quantitative measurement can be null |
| `quality_checks` | `check`, `option_labels`, `result`, `evidence`, `explanation` | Check uses `da.quality_check`; result pass/fail/unknown |
| `annotation_gaps` | `field`, `stored_value`, `proposed_value`, `span_ids`, `reason`, `status` | Proposals do not overwrite stored values |
| `generation_constraints` | `constraint`, `supporting_span_ids`, `reason` | Reusable lessons grounded in this question |

Every option's `analysis` object uses this shape:

```json
{
  "exact_text": null,
  "stored_is_correct": null,
  "verdict": null,
  "distractor_type_key": null,
  "option_error_focus_key": null,
  "plausibility_source_key": null,
  "student_failure_mode_key": null,
  "tempting_partial_truth": null,
  "violated_constraint": null,
  "evidence_span_ids": [],
  "why_plausible": null,
  "why_wrong_or_right": null,
  "student_failure_hypothesis": null,
  "hypothesis_status": "unknown",
  "completed_sentence": null,
  "strongest_competing_interpretation": null,
  "status": "unknown"
}
```

`verdict` uses `da.option_verdict`. Correct answers need a positive justification;
wrong-answer-specific fields can be null with an explanation. For completion
items, assess grammar and logic after insertion, not just in the isolated choice.

## 6. Small worked relationship example

For the illustrative sentence “The collection of maps is valuable.”, the head
`collection` governs agreement with `is`; the plural `maps` does not. This is an
anatomy example only, not a sourced DSAT item or a complete question annotation.

```json
{
  "spans": [
    {"id": "s1", "source_field": "example", "quote": "collection", "occurrence": 1},
    {"id": "s2", "source_field": "example", "quote": "maps", "occurrence": 1},
    {"id": "s3", "source_field": "example", "quote": "is", "occurrence": 1}
  ],
  "relations": [
    {"type": "agreement_controller_of", "from_span_id": "s1", "to_span_id": "s3",
     "explanation": "The singular subject head controls finite-verb agreement.", "status": "observed"}
  ],
  "disruptors": [
    {"type": "competing_noun", "span_ids": ["s2"], "affected_relation": "s1 to s3",
     "canonical_trap_key": null,
     "explanation": "The intervening plural noun could invite attraction; learner behavior is not observed.",
     "status": "inferred"}
  ]
}
```

## 7. Completion checks and use

Run `/deep-question-analysis <UUID>` in Claude Code. The skill fetches the
question and writes its source snapshot and a Markdown analysis under
`GENERATIONS/`. Request a structured analysis JSON too when needed for tooling.

Before marking an analysis complete: preserve all source fields; reconcile
versions and keys; analyze all four options; check span references and exact
quotes; validate enum category/parent; distinguish observed/inferred/unknown/
not-applicable/review states; review all quality checks; and establish one
defensible answer. Missing or ambiguous evidence remains visible. The template
is a documented contract, not an installed JSON Schema validator or DB migration.
