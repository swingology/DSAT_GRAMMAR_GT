# Grammar Rules v7 → v8 Sub-Pattern Expansion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce `rules_agent_dsat_grammar_ingestion_generation_v8.md` by adding PT-cited sub-patterns (max 3 per focus key) to every focus key in B.3, sourced from web research cross-validated against `analysis/calibration/official_classifications.json`.

**Architecture:** Three-tier evidence policy. Tier A (≥5 PT examples): full 3 PT-cited sub-patterns. Tier B (1–4 PT examples): mix of PT + web-cited sub-patterns, minimum 1 PT-cited. Tier C (0 PT examples): web-cited only, marked `[NO PT EVIDENCE]` in source line. Anti-rigidity preamble added to B.3 explicitly authorizing items that match no listed sub-pattern.

**Tech Stack:** Python 3 (one-off extraction scripts), markdown editing, `analysis/calibration/official_classifications.json` (542 calibration-eligible PT questions), WebSearch + WebFetch for canonical sub-pattern naming, B.3 of v7 as the structural template.

---

## Constraints and Conventions

| Constraint | Value | Source |
|---|---|---|
| Sub-patterns per focus key | Hard cap: 3 | User decision |
| Citation format | `(PT{exam} M{module} Q{number}: "short quote")` | User selected |
| Sub-pattern source bar | Web source name + tier-appropriate PT cross-check | User decision |
| File strategy | New file `rules_agent_dsat_grammar_ingestion_generation_v8.md`, v7 stays frozen | Matches v3→v6→v7 convention in the file's history |
| Calibration JSON | `analysis/calibration/official_classifications.json` | 542 questions, rules_agent_v7.0-classified |
| Anti-rigidity clause | New preamble paragraph at top of B.3 | User concern about template lock-in |
| In-scope sub-pattern types | Trap variant, distractor variant, register variant, punctuation sub-rule | Mirrors existing v7 B.3 sub-pattern shapes |
| Out-of-scope | New `grammar_focus_key` values, new `syntactic_trap_key` values | Per v7 §A.1.3 — amendments only via C.5 |

### Web source allowlist

| Source | Use for |
|---|---|
| College Board (collegeboard.org, Bluebook docs) | Authoritative sub-pattern naming |
| Khan Academy SAT R&W course | Skill family taxonomy, sub-pattern names |
| The Critical Reader (Erica Meltzer) | Trap mechanism descriptions |
| PrepScholar | Sub-pattern frequency and examples |
| Albert.io | Distractor pattern catalogs |
| Test Innovators | DSAT-specific item structure |
| Manhattan Review, PrepMaven, UWorld, TestPrepKart | Cross-reference only; do not cite as primary |

---

## File Structure

```
docs/superpowers/plans/
  └── 2026-05-23-grammar-rules-v7-to-v8-subpatterns.md   (this plan)

scripts/v8/                                              (new — extraction utilities)
  ├── extract_focus_examples.py                          (queries calibration JSON)
  ├── compute_tier_table.py                              (tiers focus keys by PT count)
  └── validate_v8_citations.py                           (checks citation format)

analysis/v8/                                             (new — intermediate artifacts)
  ├── tier_table.json                                    (focus_key → tier + PT count)
  ├── focus_evidence/                                    (per-focus-key example dumps)
  │   ├── subject_verb_agreement.json
  │   ├── transition_logic.json
  │   └── ... (one file per focus_key)
  └── subpattern_drafts/                                 (per-focus-key sub-pattern drafts)
      ├── subject_verb_agreement.md
      └── ... (one file per focus_key)

rules_agent_dsat_grammar_ingestion_generation_v8.md      (final output)

RULES_ANATOMY.md                                         (modify — bump v7 reference to v8)
```

---

## Task 1: Set up extraction tooling

**Files:**
- Create: `scripts/v8/extract_focus_examples.py`
- Create: `scripts/v8/compute_tier_table.py`
- Create: `scripts/v8/validate_v8_citations.py`

- [ ] **Step 1: Create the extractor script**

Create `scripts/v8/extract_focus_examples.py`:

```python
"""Extract official-classification examples per grammar_focus_key.

Reads analysis/calibration/official_classifications.json and writes one JSON
file per focus_key into analysis/v8/focus_evidence/. Each per-focus file
contains the full question records that v7 classified to that focus, sorted
by source_exam_code then source_question_number.
"""
import json
import sys
from collections import defaultdict
from pathlib import Path

CALIBRATION = Path("analysis/calibration/official_classifications.json")
OUT_DIR = Path("analysis/v8/focus_evidence")


def main() -> int:
    data = json.loads(CALIBRATION.read_text())
    by_focus: dict[str, list] = defaultdict(list)
    for q in data["questions"]:
        focus = (q.get("classification") or {}).get("grammar_focus_key")
        if focus:
            by_focus[focus].append(q)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for focus, items in by_focus.items():
        items.sort(
            key=lambda q: (
                str(q.get("source_exam_code") or ""),
                str(q.get("source_module_code") or ""),
                q.get("source_question_number") or 0,
            )
        )
        (OUT_DIR / f"{focus}.json").write_text(json.dumps(items, indent=2))

    print(f"Wrote {len(by_focus)} focus files to {OUT_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: Create the tier-table script**

Create `scripts/v8/compute_tier_table.py`:

```python
"""Tier each grammar_focus_key by PT evidence count.

Tier A: >= 5 PT examples (full 3 PT-cited sub-patterns achievable)
Tier B: 1-4 PT examples (mix PT + web, minimum 1 PT)
Tier C: 0 PT examples (web-cited only, NO PT EVIDENCE marker)

Reads from analysis/v8/focus_evidence/, also accepts an additional list of
v7-defined focus keys with 0 calibration coverage (Tier C).
"""
import json
from pathlib import Path

EVIDENCE = Path("analysis/v8/focus_evidence")
OUT = Path("analysis/v8/tier_table.json")

# Full list of v7 production focus keys (D.2.1-D.2.8). Tier C if missing
# from evidence dir.
V7_FOCUS_KEYS = [
    # D.2.1 sentence boundary
    "sentence_fragment", "comma_splice", "run_on_sentence", "sentence_boundary",
    # D.2.2 agreement
    "subject_verb_agreement", "pronoun_antecedent_agreement",
    "noun_countability", "determiners_articles", "affirmative_agreement",
    # D.2.3 pronoun
    "pronoun_case", "pronoun_clarity",
    # D.2.4 verb form
    "verb_tense_consistency", "verb_form", "voice_active_passive", "negation",
    # D.2.5 modifier
    "modifier_placement", "comparative_structures", "illogical_comparison",
    "adjective_adverb_distinction", "logical_predication", "relative_pronouns",
    # D.2.6 punctuation
    "punctuation_comma", "colon_dash_use", "semicolon_use",
    "conjunctive_adverb_usage", "apostrophe_use", "possessive_contraction",
    "appositive_punctuation", "hyphen_usage", "quotation_punctuation",
    "unnecessary_internal_punctuation", "end_punctuation_question_statement",
    # D.2.7 parallel
    "parallel_structure", "elliptical_constructions", "conjunction_usage",
    # D.2.8 expression of ideas
    "redundancy_concision", "precision_word_choice",
    "register_style_consistency", "logical_relationships",
    "emphasis_meaning_shifts", "data_interpretation_claims", "transition_logic",
    "commonly_confused_words", "preposition_idiom",
]


def main() -> int:
    table = {}
    for key in V7_FOCUS_KEYS:
        ev_file = EVIDENCE / f"{key}.json"
        if ev_file.exists():
            count = len(json.loads(ev_file.read_text()))
        else:
            count = 0
        if count >= 5:
            tier = "A"
        elif count >= 1:
            tier = "B"
        else:
            tier = "C"
        table[key] = {"pt_examples": count, "tier": tier}

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(table, indent=2, sort_keys=True))

    by_tier: dict[str, int] = {"A": 0, "B": 0, "C": 0}
    for v in table.values():
        by_tier[v["tier"]] += 1
    print(f"Tier A (>=5 PT examples): {by_tier['A']} focus keys")
    print(f"Tier B (1-4 PT examples): {by_tier['B']} focus keys")
    print(f"Tier C (0 PT examples):   {by_tier['C']} focus keys")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
```

- [ ] **Step 3: Create the citation validator**

Create `scripts/v8/validate_v8_citations.py`:

```python
"""Validate sub-pattern citation format in v8 markdown.

Citation format spec:
  (PT{exam} M{module} Q{number}: "short quote")
  e.g. (PT7 M2 Q14: "a toxin that is deadly to nematodes that comes...")

Also accepts:
  [NO PT EVIDENCE — source: <web source name>]

Counts sub-patterns per focus key and fails if any focus key has > 3.
"""
import re
import sys
from collections import defaultdict
from pathlib import Path

V8 = Path("rules_agent_dsat_grammar_ingestion_generation_v8.md")

CITATION_RE = re.compile(r'\(PT(\d{1,2}) M(\d) Q(\d{1,2}): "[^"]+"\)')
NO_EVIDENCE_RE = re.compile(r"\[NO PT EVIDENCE — source: [^\]]+\]")
SUBPATTERN_RE = re.compile(r"^\*\*Sub-pattern — ([^*]+)\*\*", re.MULTILINE)
FOCUS_HEADER_RE = re.compile(r"^### `([a-z_]+)`\s*$", re.MULTILINE)


def main() -> int:
    text = V8.read_text()

    errors: list[str] = []
    sections = FOCUS_HEADER_RE.split(text)
    # sections[0] is preamble; subsequent pairs are (focus_key, body)
    counts: dict[str, int] = defaultdict(int)
    for i in range(1, len(sections), 2):
        focus = sections[i]
        body = sections[i + 1] if i + 1 < len(sections) else ""
        subpatterns = SUBPATTERN_RE.findall(body)
        counts[focus] = len(subpatterns)
        if len(subpatterns) > 3:
            errors.append(f"{focus}: {len(subpatterns)} sub-patterns (cap is 3)")
        # Every sub-pattern line region must contain at least one citation
        # or NO PT EVIDENCE marker
        sp_regions = re.split(SUBPATTERN_RE, body)
        for region in sp_regions[1:]:
            if not CITATION_RE.search(region) and not NO_EVIDENCE_RE.search(region):
                errors.append(
                    f"{focus}: sub-pattern missing citation or NO PT EVIDENCE marker"
                )

    print(f"Scanned {sum(counts.values())} sub-patterns across {len(counts)} focus keys")
    if errors:
        for e in errors:
            print(f"  ERROR: {e}")
        return 1
    print("All sub-patterns have valid citations or NO PT EVIDENCE markers.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run the extractor**

Run: `uv run python scripts/v8/extract_focus_examples.py`
Expected: `Wrote 36 focus files to analysis/v8/focus_evidence`

- [ ] **Step 5: Run the tier table**

Run: `uv run python scripts/v8/compute_tier_table.py`
Expected: prints Tier A/B/C counts, writes `analysis/v8/tier_table.json`

- [ ] **Step 6: Commit**

```bash
git add scripts/v8/ analysis/v8/tier_table.json analysis/v8/focus_evidence/
git commit -m "chore(v8): add sub-pattern extraction tooling and evidence tier table"
```

---

## Task 2: Bootstrap v8 from v7

**Files:**
- Create: `rules_agent_dsat_grammar_ingestion_generation_v8.md` (copy of v7)

- [ ] **Step 1: Copy v7 to v8**

Run:
```bash
cp rules_agent_dsat_grammar_ingestion_generation_v7.md \
   rules_agent_dsat_grammar_ingestion_generation_v8.md
```

- [ ] **Step 2: Update v8 header**

Edit `rules_agent_dsat_grammar_ingestion_generation_v8.md` line 1:

Replace:
```markdown
# rules_agent_dsat_grammar_ingestion_generetion_v7.md
```

With:
```markdown
# rules_agent_dsat_grammar_ingestion_generation_v8.md
```

(Also fixes the v7 typo "generetion" → "generation".)

- [ ] **Step 3: Replace the v7-changes block with a v8-changes block**

Edit lines 11–34 of v8. Replace the entire `**v7 changes from v6:**` block with:

```markdown
**v8 changes from v7:**

- B.3 expanded with PT-cited sub-patterns for every grammar_focus_key (max 3 per key, hard cap)
- Each sub-pattern carries a citation in format `(PT{exam} M{module} Q{number}: "short quote")` or a `[NO PT EVIDENCE — source: <web>]` marker
- Evidence tiers documented per focus key in §B.3.0 (Tier A ≥5 PT examples, B 1–4, C 0)
- Anti-rigidity preamble added at §B.3.0: sub-patterns are attested variants, not exhaustive templates. Generators MAY produce items matching no listed sub-pattern.
- `model_version` updated to `rules_agent_v8.0`
- No changes to taxonomy keys (D.1–D.9) — all additions are documentary, not classificatory
- v7 grammar_focus_key, grammar_role_key, syntactic_trap_key, and all distractor-mechanism keys carry over unchanged

**v7 source:** `rules_agent_dsat_grammar_ingestion_generation_v7.md`
```

- [ ] **Step 4: Update model_version references**

Edit v8, find every occurrence of `"rules_agent_v7.0"` and replace with `"rules_agent_v8.0"`. There are at least 3 occurrences (B.12 Example A, B.12 Example B, and the schema in A.3).

Run (verification):
```bash
grep -c "rules_agent_v8.0" rules_agent_dsat_grammar_ingestion_generation_v8.md
```
Expected: `3` (or whatever total v7 had)

Run (no leftover v7 refs):
```bash
grep -n "rules_agent_v7.0" rules_agent_dsat_grammar_ingestion_generation_v8.md
```
Expected: no output

- [ ] **Step 5: Commit**

```bash
git add rules_agent_dsat_grammar_ingestion_generation_v8.md
git commit -m "chore(v8): copy v7 to v8 and update version header"
```

---

## Task 3: Add §B.3.0 preamble and tier table

**Files:**
- Modify: `rules_agent_dsat_grammar_ingestion_generation_v8.md` (insert before §B.3)

- [ ] **Step 1: Locate the insertion point**

Find the line `## B.3 Passage Construction Rules by Grammar Focus` in v8.
Insert a new `## B.3.0` section IMMEDIATELY BEFORE that line.

- [ ] **Step 2: Insert the preamble**

Insert this block before §B.3:

```markdown
## B.3.0 Sub-Pattern Policy and Evidence Tiers

### B.3.0.1 What sub-patterns are

Sub-patterns are *attested trap variants* observed in official DSAT practice
tests or documented in verified prep sources (College Board, Khan Academy,
The Critical Reader, PrepScholar, Albert.io, Test Innovators). They are
documentary, not classificatory: every sub-pattern resolves to the parent
`grammar_focus_key` and an existing `syntactic_trap_key` from D.5. Sub-patterns
do not create new keys.

### B.3.0.2 Sub-patterns are not rails

Sub-patterns are examples of variation, not an exhaustive menu. **Generators
MAY produce items that match no listed sub-pattern** as long as the canonical
construction for the focus key is honored, distractors target distinct failure
modes, and B.13 validation passes. Annotators MAY classify items that match no
listed sub-pattern; the sub-pattern field is descriptive, not required.

### B.3.0.3 Citation format

Every sub-pattern carries either:

1. A PT citation: `(PT{exam} M{module} Q{number}: "short quote")`
   Example: `(PT7 M2 Q14: "a toxin that is deadly to nematodes that comes in contact with it")`
2. A web-source marker: `[NO PT EVIDENCE — source: <name>]` when no calibration-set example exists.

### B.3.0.4 Hard cap

Maximum 3 sub-patterns per grammar_focus_key. Adding a fourth requires
demoting one. Use the v7→v8 generation log to track demotions.

### B.3.0.5 Evidence tiers

Each focus key is assigned a tier in §B.3.0.6 based on PT example count in
`analysis/calibration/official_classifications.json` as of the v8 cut.

| Tier | PT examples | Sub-pattern policy |
|---|---|---|
| A | ≥5 | All 3 sub-patterns PT-cited |
| B | 1–4 | At least 1 PT-cited; remainder may be web-only |
| C | 0 | All web-only with `[NO PT EVIDENCE]` markers |

Tier C sub-patterns should be re-promoted to Tier B/A as new PT examples are
classified. Re-tiering does not require a version bump; it can be done as a
patch.

### B.3.0.6 Tier table

[INSERT GENERATED TABLE FROM analysis/v8/tier_table.json HERE — see Task 3 Step 4]

---
```

- [ ] **Step 3: Generate the tier table markdown**

Run:
```bash
uv run python -c "
import json
table = json.load(open('analysis/v8/tier_table.json'))
rows = sorted(table.items(), key=lambda kv: (kv[1]['tier'], -kv[1]['pt_examples'], kv[0]))
print('| Focus key | Tier | PT examples |')
print('|---|---|---|')
for key, info in rows:
    print(f'| \`{key}\` | {info[\"tier\"]} | {info[\"pt_examples\"]} |')
"
```

- [ ] **Step 4: Replace the placeholder with the generated table**

In v8, replace `[INSERT GENERATED TABLE FROM analysis/v8/tier_table.json HERE — see Task 3 Step 4]` with the output of the previous step (the full markdown table).

- [ ] **Step 5: Commit**

```bash
git add rules_agent_dsat_grammar_ingestion_generation_v8.md
git commit -m "feat(v8): add B.3.0 sub-pattern policy preamble and tier table"
```

---

## Task 4: Draft sub-patterns for Tier A focus keys

> **Note to executor:** Tier A is the largest workload but the most evidence-dense. Process focus keys one at a time. For each focus key, follow Task 4's sub-steps in full before moving on.

**Per-key workflow (repeat for every Tier A focus key listed in `analysis/v8/tier_table.json`):**

- [ ] **Step 1: Read the focus key's PT examples**

Run:
```bash
uv run python -c "
import json
data = json.load(open('analysis/v8/focus_evidence/<FOCUS_KEY>.json'))
for q in data:
    print(f\"PT{q['source_exam_code']} M{q['source_module_code']} Q{q['source_question_number']}\")
    print(f\"  trap: {q['classification'].get('syntactic_trap_key')}\")
    passage = (q.get('passage_text') or '')[:160].replace(chr(10), ' ')
    print(f\"  passage: {passage}\")
    print(f\"  rationale: {(q['classification'].get('classification_rationale') or '')[:200]}\")
    print()
"
```

Replace `<FOCUS_KEY>` with the actual focus key (e.g., `subject_verb_agreement`).

- [ ] **Step 2: Group examples by trap mechanism**

Read the output of Step 1. Group the questions into clusters where the same trap mechanism is at work. Common groupings:
- Same `syntactic_trap_key`
- Same structural pattern in the passage (e.g., all inversions, all relative-clause stackings)
- Same distractor failure mode

You should arrive at 2–5 candidate clusters. The 3 most distinct clusters become the 3 sub-patterns.

- [ ] **Step 3: Web-research canonical sub-pattern naming**

For each cluster, search the web allowlist (College Board, Khan Academy, The Critical Reader, PrepScholar, Albert.io, Test Innovators) for the canonical name of the trap mechanism.

Use one WebSearch query per cluster, formatted: `"<trap mechanism description>" SAT grammar "<focus_key noun>"` (e.g., `"nearest noun attraction" SAT subject-verb agreement`).

If the web sources name the sub-pattern, use that name (lowercase snake_case for the slug, Title Case for the heading). If they do not, derive a name from the trap mechanism description (e.g., "Stacked relative clauses").

- [ ] **Step 4: Draft the sub-pattern entry**

Use this template for each sub-pattern. Write to `analysis/v8/subpattern_drafts/<focus_key>.md`:

```markdown
**Sub-pattern — <Title Case name>**

(PT{exam} M{module} Q{number}: "{shortest distinctive quote from passage_text, ≤90 chars}")

<2-3 sentence description of the trap mechanism, written in the v7 B.3 voice
— what to construct, what makes it tricky, where the blank goes.>

Distractors: <one-sentence summary of how distractors exploit this sub-pattern>.

Classify with `syntactic_trap_key: "<existing v7 key from D.5>"` and
`student_failure_mode_key: "<existing v7 key from D.7>"`.
```

Pick the PT example with the cleanest passage text (avoid OCR garbage, missing characters, or passages that test multiple things at once). The quote should be the part of the passage that contains the actual trap.

- [ ] **Step 5: Validate the draft**

Check the draft against this checklist:
- Exactly 3 sub-patterns (no more, no fewer)
- Each sub-pattern has a PT citation in the exact format `(PT{n} M{n} Q{n}: "...")`
- Each sub-pattern references an existing `syntactic_trap_key` from D.5 (do NOT invent new ones)
- Each sub-pattern references an existing `student_failure_mode_key` from D.7
- Quotes are ≤90 characters and contain the actual trap
- Sub-pattern names are distinct from any existing v7 sub-pattern in B.3

- [ ] **Step 6: Append to v8**

Open `rules_agent_dsat_grammar_ingestion_generation_v8.md`. Find the section `### \`<focus_key>\`` in §B.3. If v7 already has a `**Secondary trap patterns:**` block, replace it with the new 3-sub-pattern block. If v7 does not, add the new block immediately after the canonical construction description for that focus key.

The exact insertion point: AFTER the last paragraph describing the canonical construction, BEFORE any other heading or focus-key section.

- [ ] **Step 7: Commit (per focus key — frequent commits)**

```bash
git add rules_agent_dsat_grammar_ingestion_generation_v8.md \
        analysis/v8/subpattern_drafts/<focus_key>.md
git commit -m "feat(v8): add sub-patterns for <focus_key> (Tier A)"
```

---

## Task 5: Draft sub-patterns for Tier B focus keys

> Tier B has 1–4 PT examples. Goal: at least 1 PT-cited sub-pattern per key, fill remainder from web sources.

**Per-key workflow (repeat for every Tier B focus key):**

- [ ] **Step 1: Read PT examples**

Same command as Task 4 Step 1.

- [ ] **Step 2: Use every PT example as a sub-pattern (up to 3)**

Because Tier B has 1–4 examples, you cannot afford to discard any. Each PT example becomes a sub-pattern as long as the trap mechanisms differ. If two PT examples share the same trap mechanism, merge them and cite the cleaner one.

- [ ] **Step 3: Fill remaining sub-pattern slots from web sources**

If Tier B has 1 PT example, you need 2 web-only sub-patterns. If 2, you need 1. If 3+, you may have enough.

For each web-only sub-pattern, search the web allowlist for documented variants of this focus key's trap mechanism that do NOT appear in the PT examples you already have. Use this format:

```markdown
**Sub-pattern — <Title Case name>**

[NO PT EVIDENCE — source: <web source name>, <year if available>]

<2-3 sentence description of the trap mechanism.>

Distractors: <one-sentence summary>.

Classify with `syntactic_trap_key: "<existing v7 key from D.5>"` and
`student_failure_mode_key: "<existing v7 key from D.7>"`.
```

- [ ] **Step 4: Validate the draft**

Same checklist as Task 4 Step 5, plus:
- At least 1 sub-pattern is PT-cited (not all 3 web-only)
- Web sources cited are from the allowlist (B.3.0 web allowlist table)

- [ ] **Step 5: Append to v8 and commit**

Same as Task 4 Steps 6–7, commit message `feat(v8): add sub-patterns for <focus_key> (Tier B)`.

---

## Task 6: Draft sub-patterns for Tier C focus keys

> Tier C has 0 PT examples. All sub-patterns are web-only. Apply extra scrutiny because these are not cross-validated against official tests.

**Per-key workflow (repeat for every Tier C focus key):**

- [ ] **Step 1: Determine whether the focus key warrants v8 inclusion**

For each Tier C focus key, check:
- Is it marked `dsat_confidence: low` in D.2? If yes, consider skipping sub-patterns entirely and leaving v7's canonical construction as-is. Note in the commit message: `<focus_key> skipped — dsat_confidence: low and no PT evidence`.
- Is it a recently promoted key from v7 (e.g., `commonly_confused_words`, `preposition_idiom`, `adjective_adverb_distinction`, `illogical_comparison`)? These are valid SAT-pattern keys without calibration coverage yet — add web-only sub-patterns.
- Is the key documented in 2+ web allowlist sources as a real DSAT pattern? If yes, add sub-patterns. If no, skip and log to `analysis/v8/skipped_focus_keys.md` with reason.

- [ ] **Step 2: Web-research sub-patterns**

Use WebSearch with 2 queries per focus key to identify the most-attested sub-patterns. Cross-reference at least 2 sources from the allowlist before drafting.

- [ ] **Step 3: Draft 1–3 sub-patterns (cap at 3 still applies)**

Use the web-only template from Task 5 Step 3. Every sub-pattern carries `[NO PT EVIDENCE — source: ...]`.

- [ ] **Step 4: Append to v8 and commit**

Commit message: `feat(v8): add sub-patterns for <focus_key> (Tier C, web-only)`.

---

## Task 7: Run citation validator

**Files:**
- Run: `scripts/v8/validate_v8_citations.py`

- [ ] **Step 1: Run the validator**

Run: `uv run python scripts/v8/validate_v8_citations.py`

Expected output:
```
Scanned NNN sub-patterns across NN focus keys
All sub-patterns have valid citations or NO PT EVIDENCE markers.
```

- [ ] **Step 2: Fix any errors reported**

If the validator reports errors, fix them in v8 directly. Common errors:
- Sub-pattern with no citation → add PT citation or `[NO PT EVIDENCE]` marker
- More than 3 sub-patterns per focus key → demote the weakest one (move to a `Demoted sub-patterns` section at the bottom of v8 or delete)
- Malformed citation → reformat to `(PT{n} M{n} Q{n}: "...")`

Re-run the validator until it passes.

- [ ] **Step 3: Commit any fixes**

```bash
git add rules_agent_dsat_grammar_ingestion_generation_v8.md
git commit -m "fix(v8): citation format and sub-pattern cap corrections"
```

---

## Task 8: Update companion documents

**Files:**
- Modify: `RULES_ANATOMY.md`
- Modify: `rules_agent_dsat_review_v1.md` (companion-rules reference at top)
- Modify: `.wolf/anatomy.md` (add v8 file entry)

- [ ] **Step 1: Update RULES_ANATOMY.md version table**

Edit `RULES_ANATOMY.md`. In the Version Tracking section, update the grammar row:

Replace:
```markdown
| `rules_agent_dsat_grammar_ingestion_generation_v7.md` | v7.0 | Production; do not edit — create v8 for changes |
```

With:
```markdown
| `rules_agent_dsat_grammar_ingestion_generation_v8.md` | v8.0 | Production; v7 frozen as audit trail |
| `rules_agent_dsat_grammar_ingestion_generation_v7.md` | v7.0 (frozen) | Superseded by v8 — kept for audit |
```

- [ ] **Step 2: Update review_v1 companion reference**

Edit `rules_agent_dsat_review_v1.md`. Find the line:
```markdown
- Grammar v7 (`rules_agent_dsat_grammar_ingestion_generation_v7.md`) is loaded **always** as the prose style canon for all DSAT writing.
```

Replace with:
```markdown
- Grammar v8 (`rules_agent_dsat_grammar_ingestion_generation_v8.md`) is loaded **always** as the prose style canon for all DSAT writing.
```

- [ ] **Step 3: Append v8 to anatomy.md**

Add to `.wolf/anatomy.md` under the `## ./` section, immediately after the v7 entry:

```markdown
- `rules_agent_dsat_grammar_ingestion_generation_v8.md` — v8 production rules with PT-cited sub-patterns (~40000 tok est.)
```

- [ ] **Step 4: Commit**

```bash
git add RULES_ANATOMY.md rules_agent_dsat_review_v1.md .wolf/anatomy.md
git commit -m "docs(v8): update companion references to point at v8"
```

---

## Task 9: Add changelog entry and memory log

**Files:**
- Modify: `CHANGELOG.md`
- Modify: `.wolf/memory.md`

- [ ] **Step 1: Add CHANGELOG entry**

Prepend a new entry at the top of `CHANGELOG.md`:

```markdown
## 2026-05-23 — Grammar Rules v8 sub-pattern expansion

- Created `rules_agent_dsat_grammar_ingestion_generation_v8.md` from v7
- Added §B.3.0 sub-pattern policy preamble: hard cap 3 per focus key, PT citation format, three-tier evidence policy, explicit anti-rigidity clause
- Added PT-cited sub-patterns for all v7 production focus keys across D.2.1–D.2.8
- Tier A (≥5 PT examples): full 3 PT-cited sub-patterns per key
- Tier B (1–4 PT examples): minimum 1 PT-cited, web-only allowed for remainder
- Tier C (0 PT examples): web-only with `[NO PT EVIDENCE]` markers
- Updated `RULES_ANATOMY.md` and `rules_agent_dsat_review_v1.md` to reference v8
- Added `scripts/v8/` extraction and validation tooling
- v7 frozen as audit trail; no changes to taxonomy keys (D.1–D.9)
```

- [ ] **Step 2: Add memory entry**

Append to `.wolf/memory.md`:

```
| HH:MM | Completed v7→v8 sub-pattern expansion; v8 file + tooling + companion doc updates | rules_agent_dsat_grammar_ingestion_generation_v8.md, scripts/v8/, RULES_ANATOMY.md, rules_agent_dsat_review_v1.md, .wolf/anatomy.md, CHANGELOG.md | success | ~12k |
```

Replace `HH:MM` with the actual completion time.

- [ ] **Step 3: Commit**

```bash
git add CHANGELOG.md .wolf/memory.md
git commit -m "docs(v8): changelog and memory log for v8 release"
```

---

## Self-Review Checklist (run by executor before declaring complete)

Run these checks against the final v8 file:

- [ ] `grep -c "^### \`" rules_agent_dsat_grammar_ingestion_generation_v8.md` returns the same count as v7 (no focus keys lost)
- [ ] `uv run python scripts/v8/validate_v8_citations.py` passes
- [ ] `grep -n "v7\.0" rules_agent_dsat_grammar_ingestion_generation_v8.md` returns no `rules_agent_v7.0` references (only v7-changelog references in the v8-changes block)
- [ ] B.3.0 preamble is present and immediately precedes B.3
- [ ] At least one focus key from each tier (A, B, C) has been hand-spot-checked for correctness
- [ ] CHANGELOG entry is dated correctly
- [ ] All commits are present in `git log --oneline rules_edit ^main`

## Spec Coverage Check

| User requirement | Where addressed |
|---|---|
| New v8 file (not in-place) | Task 2 |
| All focus keys covered | Tasks 4 (Tier A) + 5 (Tier B) + 6 (Tier C) |
| Hard cap of 3 sub-patterns per key | B.3.0.4 preamble + validator Task 7 + Task 4–6 templates |
| Citation + short quote format | B.3.0.3 preamble + Task 4 Step 4 + validator Task 7 |
| Web + PT cross-validation | Tier policy in B.3.0.5 + Task 4 (Tier A: PT-cited) + Task 5 (Tier B: PT+web) + Task 6 (Tier C: web-only marked) |
| Anti-rigidity preamble | B.3.0.2 (Task 3 Step 2) |
| v7 frozen as audit trail | Task 2 (new file) + Task 8 Step 1 (version table) |
| Concern about overlap | Hard cap of 3 + disambiguation D.3 references in Task 4 Step 5 + sub-pattern name distinctness check in validation |
