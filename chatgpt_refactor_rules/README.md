# ChatGPT rules refactor working set

This directory collects the documents and regenerated artifacts produced during the ChatGPT refactor review.

See the [annotation guide and JSON template](ANNOTATION_GUIDE.md) for question
families, the current annotation field inventory, and the deep-analysis format.

The [deep analysis extension v1.0.0](deep_analysis/1.0.0/RULES.md) standardizes
sentence/controller, evidence, style and distractor analysis for the
`/deep-question-analysis <UUID>` Claude skill. DA-001 records the additive
vocabulary changes; existing production keys and the frozen baseline are retained.

**Start with [STANDARD.md](STANDARD.md): the established v1.0.0 terminology and
rules baseline.** Its [versioned vocabulary records](vocabulary/v1.0.0/) preserve
College Board labels separately from existing production keys and record every
baseline addition, crosswalk, and migration boundary. Research proposals cannot
override that standard.

| Path | Contents | Status |
|---|---|---|
| [CANONCIAL_VOCABULARIES_CGPT.md](CANONCIAL_VOCABULARIES_CGPT.md) | Expanded ontology proposal, emphasizing grammar, style, traps and distractors | Proposed |
| [refactor_plan_cgpt.md](refactor_plan_cgpt.md) | Current-code audit, JSON/JSONB workflow, caching and phased-generation plan | Opt-in loader, shared quality increment, and terminology baseline recorded |
| [rules/](rules/) | 66 regenerated rule modules | Shared generation quality increment applied; full ontology proposal pending |
| [rules/manifest.json](rules/manifest.json) | Ordered generation and annotation module load sets | Shared quality and reading checklist dependencies included |
| [rules/split_report.json](rules/split_report.json) | Source-line coverage report from regeneration | Verification artifact |

The `rules/` artifacts were regenerated using `../rules_refactor/split_rules.py` and the corrected source documents in `../rules_refactor/`. They were initially written to `/tmp/dsat-rules-audit-cu5qjfl0/rules/` for verification and then moved here. They matched `../rules_refactor/rules/` byte for byte at consolidation, with no unassigned nonblank source lines.

The original `../rules_refactor/` remains intact. Its splitter and corrected monoliths predate this review and have not been duplicated here. The generated modules are a reference baseline, not a second authored source of truth. Running the original splitter regenerates its original output directory, not this snapshot.

The initial review was documentation-only. The opt-in generation loader consumes the original `../rules_refactor/rules/`; see plan §§13–14 for activation, verification, and deferred work. The current snapshot includes the shared quality increment and matches that directory. The modular loader remains opt-in; active ontology, database, and provider settings were not changed. General generation instructions also now require the stronger distractor checks and domain-appropriate prose.

Unless explicitly stated otherwise, code and source paths within the proposal documents are relative to the repository root.
