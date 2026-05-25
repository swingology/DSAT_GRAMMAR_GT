# missing_rules_v8.md

## Purpose

This document identifies grammar rules, sub-patterns, distractor mechanics, and
traps that are **absent or underrepresented in v8** of the DSAT grammar rules
file (`rules_agent_dsat_grammar_ingestion_generation_v8.md`). It is the result
of a cross-reference audit against College Board official taxonomy, released
practice tests PT1–PT11, and the following external sources:

- [College Board Skills Insight for the Digital SAT Suite (official PDF)](https://satsuite.collegeboard.org/media/pdf/skills-insight-digital-sat-suite.pdf)
- [The Critical Reader — Erica Meltzer (complete SAT grammar rules)](https://thecriticalreader.com/complete-sat-grammar-rules/)
- [PrepScholar — Complete Guide to SAT Grammar Rules](https://blog.prepscholar.com/the-complete-guide-to-sat-grammar-rules)
- [Test Innovators — A Guide to Digital SAT Grammar and Punctuation](https://testinnovators.com/blog/standard-english-conventions-guide-digital-sat/)
- [Pursu / ChatSAT — SAT Subject-Verb Agreement Fast-Fix](https://pursu.io/guide/sat-subject-verb-agreement-fast-fix-2025-11-digital-sat-traps)
- [Pursu / ChatSAT — SAT Grammar Cheat Sheet: 23 Patterns](https://pursu.io/guide/sat-grammar-cheat-sheet-2025-the-23-patterns-that-appear-85-of-the-time)
- [The College Panda — Subject-Verb Agreement on the SAT](https://thecollegepanda.com/sat-writing-subject-verb-agreement/)
- [Albert.io — Rhetorical Synthesis SAT Review](https://www.albert.io/blog/rhetorical-synthesis-sat-reading-and-writing-review/)
- [PrepScholar — Illogical Comparisons on SAT Writing](https://blog.prepscholar.com/illogical-comparisons-the-weirdest-topic-on-sat-writing)
- [PrepScholar — Faulty Modifiers on SAT Writing](https://blog.prepscholar.com/faulty-modifiers-on-sat-writing-grammar-rule-prep)
- [PrepScholar — Wordiness and Redundancy in SAT Writing](https://blog.prepscholar.com/wordiness-and-redundancy-in-sat-writing)
- [Admit Studio — Verb Mood: Subjunctive / Imperative](https://admitstudio.com/undergraduate-articles/sat-writing-verb-mood-subjunctive-imperative/)
- [Magoosh — SAT Grammar Rules (50+)](https://magoosh.com/sat/sat-grammar-rules/)
- [The Test Advantage — SAT Grammar Rules Cheat Sheet 2026](https://thetestadvantage.com/blog/sat-grammar-rules-cheat-sheet-2026-all-15-rules)
- [The Test Advantage — Digital SAT Punctuation Rules 2026](https://thetestadvantage.com/blog/digital-sat-punctuation-rules-2026-commas-semicolons-colons)
- [Test Innovators — Digital SAT Transitions](https://testinnovators.com/blog/digital-sat-reading-writing-transitions/)
- [The Opus Way — Expression of Ideas Detailed Syllabus](https://sat.theopusway.com/digital-sat-reading-writing-preparation/expression-of-ideas-detailed-syllabus)
- Khan Academy SAT Grammar prep materials
- Official College Board DSAT practice tests (PT1–PT11)

---

## How to Read This Document

**Gap severity levels:**

- **CRITICAL** — Rule is completely absent from v8. The agent cannot correctly
  generate or annotate a DSAT item that tests this pattern.
- **MAJOR** — Rule is pending (D.2.9) or mentioned without sub-patterns. The
  agent has no executable procedure for generating or annotating it.
- **MODERATE** — Rule exists but the B.3 hard cap (3 sub-patterns max) excluded
  one or more well-attested PT patterns. Items exist in official PTs that fall
  outside the documented sub-patterns.
- **MINOR** — Rule is covered implicitly but the explicit formulation is absent
  or buried. A dedicated statement would prevent annotator drift.

---

## Part 1 — CRITICAL Gaps (Rules Not Documented Anywhere in v8)

---

### GAP-001 | `subject_verb_agreement` — Inverted Sentence Order

**Severity:** CRITICAL
**Parent key:** `subject_verb_agreement`
**Trap key:** `garden_path`
**Frequency:** Well-documented across all SAT prep sources; appears in official PTs

**Rule:**
In inverted constructions, the true grammatical subject follows the verb.
The verb must agree with the post-verbal subject, not with any noun that
appears before the verb.

Three common DSAT inversion patterns:

1. **Existential `there`:** "There is/are..." — the subject is the noun after
   the verb. "There is one exhibit" vs. "There are three exhibits."

2. **Existential `here`:** "Here is/are..." — same pattern.

3. **Fronted prepositional phrase:** "Among the artifacts ___ three bronze
   figurines." The subject ("three bronze figurines") follows the verb slot.
   The fronted prepositional phrase is not the subject.

**Distractors:**
- Singular verb matching a singular noun in the fronted phrase (the classic
  nearest-noun attraction applied to an inverted structure)
- Wrong tense combined with wrong number
- Plural verb when the post-verbal subject is singular

**Why it matters:**
Students (and agents) trained on "find the subject before the verb" fail
completely on inverted constructions. The pattern is cross-documented in every
major prep source as a high-value trap.

**Sources:**
[The College Panda — Subject-Verb Agreement](https://thecollegepanda.com/sat-writing-subject-verb-agreement/),
[Pursu — SVA Fast-Fix](https://pursu.io/guide/sat-subject-verb-agreement-fast-fix-2025-11-digital-sat-traps),
[Magoosh — SAT Grammar Rules](https://magoosh.com/sat/sat-grammar-rules/)

---

### GAP-002 | `subject_verb_agreement` — Indefinite Pronoun Subjects

**Severity:** CRITICAL
**Parent key:** `subject_verb_agreement`
**Trap key:** `nearest_noun_attraction`
**Frequency:** Standard DSAT pattern; absent from B.3 SVA sub-patterns

**Rule:**
The following indefinite pronouns are grammatically singular and require
singular verbs regardless of any following prepositional phrase:

*each, everyone, anyone, someone, no one, everybody, anybody, somebody,
nobody, everything, anything, something, nothing, either, neither, whoever,
whatever, whichever*

The canonical trap: "Each of the students ___ ready." The prepositional
object "the students" is plural, but the subject "each" is singular.

**Distractors:**
- Plural verb agreeing with the plural noun inside the prepositional phrase
  ("Each of the students are" — lured by "students")
- Present perfect where simple present is required
- Progressive form where simple present is required

**Key additional note:**
`either` and `neither` as subjects (without the correlative partner "or/nor")
are singular: "Neither of the solutions ___ correct."

**Sources:**
[PrepScholar — Complete Guide to SAT Grammar](https://blog.prepscholar.com/the-complete-guide-to-sat-grammar-rules),
[The Critical Reader](https://thecriticalreader.com/complete-sat-grammar-rules/),
[Magoosh — SAT Grammar Rules](https://magoosh.com/sat/sat-grammar-rules/)

---

### GAP-003 | `subject_verb_agreement` — Compound Subjects with `or`/`nor`

**Severity:** CRITICAL
**Parent key:** `subject_verb_agreement`
**Trap key:** `long_distance_dependency`
**Frequency:** Documented in all major prep sources

**Rule:**
When two subjects are joined by `or` or `nor` (and in correlative pairs:
`either…or`, `neither…nor`), the verb agrees with the **subject closest to
the verb** (the proximity rule).

Patterns:
- "Either the manager or the employees ___ responsible." → plural verb
  (closest subject = "the employees")
- "Either the employees or the manager ___ responsible." → singular verb
  (closest subject = "the manager")
- "Neither the results nor the method ___ convincing." → singular verb

**Distractors:**
- Verb agreeing with the first subject rather than the second
- Plural verb treating the compound as equivalent to an "and" compound
- Singular verb regardless of proximity

**Contrast with `and` compounds:**
Two subjects joined by `and` always take a plural verb regardless of
proximity.

**Sources:**
[PrepScholar — Complete Guide to SAT Grammar](https://blog.prepscholar.com/the-complete-guide-to-sat-grammar-rules),
[Magoosh — SAT Grammar Rules](https://magoosh.com/sat/sat-grammar-rules/),
[The Critical Reader](https://thecriticalreader.com/complete-sat-grammar-rules/)

---

### GAP-004 | `verb_form` — Gerund vs. Infinitive Idiomatic Selection

**Severity:** CRITICAL
**Parent key:** `verb_form`
**Trap key:** `none`
**Frequency:** Documented as a tested pattern; no B.3 sub-pattern in v8

**Rule:**
Certain verbs are followed only by gerunds (`-ing`), others only by
infinitives (`to + base`), and some by either with a meaning change.

**Gerund-only verbs (common on the DSAT):**
`enjoy`, `avoid`, `finish`, `consider`, `suggest`, `recommend`, `deny`,
`admit`, `practice`, `risk`, `postpone`, `keep`, `discuss`
→ "enjoyed *swimming*" not "enjoyed *to swim*"

**Infinitive-only verbs (common on the DSAT):**
`decide`, `choose`, `plan`, `hope`, `want`, `agree`, `offer`, `promise`,
`refuse`, `expect`, `need`, `seem`
→ "decided *to leave*" not "decided *leaving*"

**Verbs that take either with meaning change:**
- `stop doing` (cease the action) vs. `stop to do` (pause in order to do)
- `remember doing` (recall past action) vs. `remember to do` (not forget)
- `try doing` (experiment) vs. `try to do` (attempt)

**Distractors:**
- Gerund where an infinitive is required (and vice versa)
- Bare infinitive (no `to`) where the full infinitive is required
- Past tense form where a non-finite complement is required

**Note for annotators:**
When the tested convention is which non-finite complement form to use after
a specific governing verb, classify as `verb_form`. Do not classify as
`conjunction_usage` or `parallel_structure` unless a structural comparison
is present.

**Sources:**
[The Critical Reader](https://thecriticalreader.com/complete-sat-grammar-rules/),
[PrepScholar — Complete Guide to SAT Grammar](https://blog.prepscholar.com/the-complete-guide-to-sat-grammar-rules),
[Magoosh — SAT Grammar Rules](https://magoosh.com/sat/sat-grammar-rules/)

---

### GAP-005 | Absolute Phrases / Nominative Absolutes

**Severity:** CRITICAL
**Parent key:** Proposed: `modifier_placement` or new key `absolute_phrase`
**Trap key:** `modifier_attachment_ambiguity`
**Frequency:** Occasionally tested; absent entirely from v8 taxonomy

**Rule:**
An absolute phrase (nominative absolute) consists of a noun plus a
participial phrase that modifies the entire main clause, not any specific
noun in it. It is grammatically separate from the subject and requires a
comma boundary.

Structure: `[Noun] + [participial phrase], [main clause].`

Examples:
- "The experiment completed, the team published their findings."
- "Her voice trembling slightly, the professor continued her lecture."
- "Weather permitting, we will proceed with the outdoor session."

**Punctuation rule:**
The absolute phrase is always set off from the main clause by a comma when
it precedes, and by a comma when it follows. It cannot be joined to the
main clause with a subordinating conjunction or relative pronoun.

**Trap mechanics:**
- Students misread the absolute phrase as a dangling modifier (looking for
  a matching subject in the main clause)
- Students add a relative pronoun ("which" or "that"), turning the absolute
  into a relative clause that may create a fragment or splice
- Students remove the comma or replace it with a coordinating conjunction

**Distractors:**
- The nominal head of the absolute in the main-clause subject slot (converts
  the absolute to a conjunction-less clause, producing a splice)
- An `-ing` participle without the nominal head (converts it to a standard
  dangling modifier)
- A relative pronoun before the participle ("the results having been,
  which…")

**Why it matters:**
Absolute phrases are structurally distinct from dangling modifiers and
participial phrases. An annotator or generator that does not know this
pattern will either misclassify the item or generate items where the
"correct" answer is actually a well-formed absolute (and thus incorrectly
label it as a modifier error).

**Sources:**
[The Critical Reader](https://thecriticalreader.com/complete-sat-grammar-rules/),
[PrepScholar — Complete Guide to SAT Grammar](https://blog.prepscholar.com/the-complete-guide-to-sat-grammar-rules)

---

## Part 2 — MAJOR Gaps (Pending in D.2.9 or Mentioned Without Sub-Patterns)

---

### GAP-006 | `subjunctive_mood` — Sub-Patterns Not Documented

**Severity:** MAJOR
**Status in v8:** Listed in D.2.9 as "pending review"; no sub-patterns in B.3
**Parent key:** `verb_form` (as sub-pattern per v8 decision)
**Frequency:** ~1 per official book per The Critical Reader; may appear on
live test more often than in official PTs

**Rule:**
The subjunctive mood uses the base form of the verb (or `were` for `be`) in
specific syntactic environments.

**Three DSAT-tested environments:**

**Environment 1 — Hypothetical or contrary-to-fact conditionals:**
`if + [subject] + were/had`
"If I *were* in charge…" (not "was")
"If the experiment *had* succeeded…"
Trap: "was" in place of "were" — sounds natural in informal English

**Environment 2 — Indirect demands, recommendations, suggestions:**
Verb of mandating/recommending + `that` + subject + **base form**
(not third-person singular, not past, not infinitive)
- "The committee *recommended* that the funding *be* approved." (not "is")
- "The law *requires* that each citizen *vote*." (not "votes")
- "The doctor *suggested* that he *exercise* daily." (not "exercises")
Trigger verbs: `recommend`, `suggest`, `require`, `demand`, `insist`,
`propose`, `ask`, `urge`, `request`, `mandate`

**Environment 3 — Adjective clauses of necessity or importance:**
`It is [adjective] that [subject] [base form]`
- "It is essential *that the data be preserved*." (not "is preserved")
- "It is important *that each student submit*." (not "submits")
Trigger adjectives: `essential`, `important`, `critical`, `necessary`,
`imperative`, `vital`

**Distractors for all three environments:**
- Third-person singular indicative (adds `-s`): most common distractor
- Past tense form
- Infinitive with `to`
- Present perfect

**Sources:**
[Admit Studio — Verb Mood: Subjunctive / Imperative](https://admitstudio.com/undergraduate-articles/sat-writing-verb-mood-subjunctive-imperative/),
[The Critical Reader](https://thecriticalreader.com/complete-sat-grammar-rules/),
[Magoosh — SAT Grammar Rules](https://magoosh.com/sat/sat-grammar-rules/)

---

### GAP-007 | `pronoun_antecedent_agreement` — Singular `they`/`their` for Gender-Neutral Singular

**Severity:** MAJOR
**Parent key:** `pronoun_antecedent_agreement`
**Frequency:** Not in B.3 sub-patterns; documented in College Board materials

**Rule:**
When the antecedent is a singular noun that does not specify gender, or is
a singular indefinite pronoun (`everyone`, `each person`, `anyone`), the
DSAT accepts `they`/`their`/`them` as the singular pronoun. This is the
preferred form over `he or she`/`his or her`.

Context: "When a student *submits* their assignment late, *they* must accept
the penalty." Both `their` and `they` refer to the singular antecedent
"a student."

**Trap mechanics:**
- Students substitute `he or she` or `his or her` (older formal convention,
  now considered cumbersome and non-preferred on DSAT)
- Students switch to plural subject ("students") to avoid the pronoun
  agreement issue, which may change the sentence's meaning
- Students use `it` for a gender-neutral person (always wrong for persons)

**Distractors:**
- `he or she` / `his or her` — grammatically acceptable but not the
  preferred DSAT form when a singular `they` is available
- Plural noun restructuring that removes the pronoun agreement requirement
- `it`/`its` — cannot refer to people

**Sources:**
[College Board Skills Insight for the Digital SAT Suite](https://satsuite.collegeboard.org/media/pdf/skills-insight-digital-sat-suite.pdf),
[PrepScholar — Complete Guide to SAT Grammar](https://blog.prepscholar.com/the-complete-guide-to-sat-grammar-rules)

---

## Part 3 — MODERATE Gaps (B.3 Hard Cap Excluded Well-Attested Sub-Patterns)

---

### GAP-008 | `subject_verb_agreement` — Stacked Relative Clauses (4th Sub-Pattern)

**Severity:** MODERATE
**Status in v8:** Documented in `TRAPS_EXAMPLES.md` but excluded from B.3
by the 3-sub-pattern hard cap
**PT evidence:** PT5 M2 Q21

**Pattern:**
Two relative clauses are nested inside each other. The second relative
pronoun refers to the plural noun two clauses back, not to the singular noun
immediately before it.

Template: "a toxin that is deadly to nematodes that *___* in contact with it"
The second `that` refers to `nematodes` (plural), not `toxin` (singular).
Required verb: plural.

**Trap:**
Students anchor to `toxin` (the grammatical head of the entire noun phrase)
or to the singular noun immediately before the second relative pronoun.
The correct antecedent is the plural noun embedded inside the first relative
clause.

**Distractors:**
- Singular verb agreeing with `toxin` (the distant head noun)
- Singular verb agreeing with any intervening singular noun
- Present perfect where simple present is required

**Why this matters for generation:**
This sub-pattern is not generatable from the three documented B.3 SVA
sub-patterns. An agent generating SVA items exclusively from v8's B.3 section
will never produce stacked-relative-clause items.

**Sources:**
[Pursu — SVA Fast-Fix](https://pursu.io/guide/sat-subject-verb-agreement-fast-fix-2025-11-digital-sat-traps),
[The College Panda — Subject-Verb Agreement](https://thecollegepanda.com/sat-writing-subject-verb-agreement/)

---

### GAP-009 | `verb_tense_consistency` — Tense Shift from Past to Present (`Today`/`Now`)

**Severity:** MODERATE
**Status in v8:** The `literary_present` variant is documented; the
`Today`/`Now` shift sub-pattern does NOT appear as a named B.3 sub-pattern
**PT evidence:** PT1 M2 Q23

**Pattern:**
A passage opens with past-tense biographical or historical narrative, then
introduces an explicit present-time adverbial (`Today`, `Currently`,
`In the present day`, `Now`, `At present`). The blank must be simple present
because the adverbial locks the action to the current state.

"After spending years developing her technique in the 1990s, Rodriguez became
one of the leading voices in her field. Today, her work *___* regarded as
foundational."

Required: simple present (`is`)
Traps: simple past (`was` — pulled by the biographical narrative tense),
present perfect (`has been` — mixes timeframes)

**Failure mode:** `tense_proximity_pull` — students match the tense of the
immediately surrounding sentences rather than the local adverbial cue.

**Sources:**
PT1 M2 Q23,
[Test Innovators — Digital SAT Grammar Guide](https://testinnovators.com/blog/standard-english-conventions-guide-digital-sat/)

---

## Part 4 — MINOR Gaps (Implicit Coverage; Explicit Statement Absent)

---

### GAP-010 | Matching Delimiter Rule (Comma-Comma, Dash-Dash, Paren-Paren)

**Severity:** MINOR
**Status in v8:** Embedded in the nonrestrictive appositive sub-pattern
(§B.3 `appositive_punctuation`, sub-pattern 3) but not stated as a
standalone generalized rule
**Affected keys:** `appositive_punctuation`, `punctuation_comma`,
`colon_dash_use`, `unnecessary_internal_punctuation`

**Rule:**
When a parenthetical element is set off inside a sentence, the opening
delimiter must be matched by the same type of closing delimiter:

- Opening comma → closing comma
- Opening dash → closing dash
- Opening parenthesis → closing parenthesis

No mixing is permitted: a comma-opened parenthetical cannot close with a
dash; a dash-opened parenthetical cannot close with a comma.

**Trap mechanics:**
- Asymmetric punctuation: one side of a paired element uses a comma, the
  other uses a dash
- Students scan each delimiter in isolation and find it locally acceptable,
  missing that the two sides must match
- Distractors routinely exploit this by offering a comma + dash combination
  where paired commas are correct

**Explicit statement needed:**
v8's current documentation says "paired commas or, when the surrounding
sentence already uses em dashes for another set-off element, paired dashes
that match the existing register." This is correct but is buried in a single
sub-pattern note. A top-level rule statement would prevent annotators and
generators from missing this on items where no appositive is involved.

**Sources:**
[The Critical Reader](https://thecriticalreader.com/complete-sat-grammar-rules/),
[The Test Advantage — Digital SAT Punctuation Rules 2026](https://thetestadvantage.com/blog/digital-sat-punctuation-rules-2026-commas-semicolons-colons)

---

### GAP-011 | `punctuation_comma` — No Comma Before/After a Preposition (Meltzer Rule)

**Severity:** MINOR
**Status in v8:** Covered implicitly under `unnecessary_internal_punctuation`
(§D.2.6: "between preposition and its noun complement") but never stated as
a standalone preposition-specific rule
**Affected keys:** `punctuation_comma`, `unnecessary_internal_punctuation`

**Rule:**
No comma may appear immediately before or after a preposition.
The prepositions most frequently tested: `of`, `by`, `to`, `at`, `for`,
`from`, `with`, `in`, `on`, `that`.

"The results *of*[,] the experiment were striking." → comma before `of` = wrong
"She was responsible *for*[,] the oversight." → comma after `for` = wrong

**Why a dedicated statement matters:**
Students routinely insert commas around prepositions when the prepositional
phrase is long or when the phrase creates a natural rhythmic pause. The
`unnecessary_internal_punctuation` rule is framed around syntactic units
(subject–verb, verb–object, etc.), not around the preposition itself.
A student who knows "no comma between subject and verb" may still miss "no
comma before `of`" because they conceptualize the issue differently.

**Sources:**
[The Critical Reader](https://thecriticalreader.com/complete-sat-grammar-rules/),
[Magoosh — SAT Grammar Rules](https://magoosh.com/sat/sat-grammar-rules/)

---

### GAP-012 | `punctuation_comma` — No Comma Before Restrictive `that`

**Severity:** MINOR
**Status in v8:** Covered implicitly under `relative_pronouns` and
`unnecessary_internal_punctuation` but not stated as a rule in its own right

**Rule:**
No comma precedes `that` when it introduces a restrictive (essential)
relative clause.

"The company *that* specializes in renewable energy *___* the contract."
→ No comma before `that`. The relative clause is restrictive: it specifies
which company.

**Trap mechanics:**
- Students add a comma before `that` by analogy with nonrestrictive `which`
  clauses (which do require a comma)
- Students confuse the comma-before-`that` construction with the
  comma-before-`which` rule

**The absolute rule:**
On the DSAT, `comma + that` for a relative clause is never correct.
`that` = restrictive → no comma, ever.
`which` (nonrestrictive) = comma required.

**Sources:**
[The Critical Reader](https://thecriticalreader.com/complete-sat-grammar-rules/),
[Test Innovators — Digital SAT Grammar Guide](https://testinnovators.com/blog/standard-english-conventions-guide-digital-sat/)

---

### GAP-013 | `commonly_confused_words` — Missing Pairs

**Severity:** MINOR
**Status in v8:** `commonly_confused_words` is in production (D.2.8) but
no B.3 sub-pattern exists for it. The key's definition covers "non-homophone
semantic confusion pairs."

**Missing pairs not explicitly listed anywhere in v8:**

| Pair | Rule |
|---|---|
| `lie` / `lay` | `lie` = intransitive (no object); `lay` = transitive (takes object) |
| `imply` / `infer` | speaker/writer *implies*; listener/reader *infers* |
| `comprise` / `compose` | the whole *comprises* the parts; the parts *compose* the whole |
| `farther` / `further` | `farther` = physical distance; `further` = figurative/degree |
| `assure` / `ensure` / `insure` | *assure* a person; *ensure* a result; *insure* against risk |
| `who` / `that` | persons are typically introduced by `who`, not `that` |
| `between` / `among` | `between` for 2 items; `among` for 3 or more |
| `number` / `amount` | `number` for countable; `amount` for uncountable |

**Note:** `fewer`/`less` and `number`/`amount` are partially covered under
`noun_countability`, but the commonly-confused-words framing is distinct
(the test is semantic knowledge, not grammar).

**Why this gap matters:**
If no B.3 sub-pattern exists, a generation agent has no template to follow
for commonly-confused-words items. Items cannot be generated for this
focus key.

**Sources:**
[PrepScholar — Complete Guide to SAT Grammar](https://blog.prepscholar.com/the-complete-guide-to-sat-grammar-rules),
[The Critical Reader](https://thecriticalreader.com/complete-sat-grammar-rules/),
[Magoosh — SAT Grammar Rules](https://magoosh.com/sat/sat-grammar-rules/)

---

## Part 5 — Distractor Mechanics Coverage Gaps

The following focus keys have B.4 distractor heuristic entries but are
missing specific distractor types documented in external sources.

---

### GAP-014 | `subject_verb_agreement` B.4 — Missing Distractor: Collective Noun Trap

**Status in v8:** `noun_countability` B.3 documents collective nouns under
the `Collective or "-s-Ending" Noun Takes a Singular Verb` sub-pattern,
but the B.4 distractor entry for `subject_verb_agreement` (§B.4, line 3625)
does not mention this pattern as a distractor source.

**Missing distractor type:**
Plural verb supplied as distractor because the collective noun subject
("the team," "the committee," "the jury") implies multiple members.
Students conflate semantic plurality with grammatical plurality.

---

### GAP-015 | `modifier_placement` B.4 — Missing Distractor: Passive-Voice Main Clause

**Status in v8:** The B.4 entry for `modifier_placement` does not mention
the passive-voice variant of a dangling modifier.

**Missing distractor type:**
When an opening participial phrase describes an active agent, distractors
offer passive-voice main clauses that put an abstract noun or result in the
subject slot ("Having studied the specimen, the results were published").
The passive sounds formal and academic, making it strongly seductive. The
correct answer must use an active-voice subject that can logically perform
the participial action.

**Sources:**
[PrepScholar — Faulty Modifiers](https://blog.prepscholar.com/faulty-modifiers-on-sat-writing-grammar-rule-prep),
[The Critical Reader](https://thecriticalreader.com/complete-sat-grammar-rules/)

---

## Part 6 — Transition Subtype Documentation Gaps

v8's transition subtype taxonomy (§B.5.2) is exhaustive. However, the
following distinctions are not cross-referenced to the distractor heuristics
section (§B.4 `transition_logic`) and are therefore not enforced during
generation.

---

### GAP-016 | `transition_logic` — `restatement_clarification` vs. `example` Distinction Not in B.4

**Severity:** MINOR

**The distinction:**
- `restatement_clarification` (`in other words`, `that is`, `i.e.`):
  The second sentence rephrases the first sentence's content — no new
  information is added.
- `example` (`for example`, `for instance`, `to illustrate`):
  The second sentence introduces a **new, concrete instance** of the first
  sentence's general claim.

Both transitions "continue" the prior idea without contrast or causation,
so they are easily confused. The distractor for a correct `example` item
is often `in other words`, and vice versa.

**Missing from B.4:** The `transition_logic` B.4 entry does not specify that
distractors for `example` items should include `restatement_clarification`
options, and vice versa.

**Sources:**
[Test Innovators — Digital SAT Transitions](https://testinnovators.com/blog/digital-sat-reading-writing-transitions/),
[Blog.DSAT16 — Digital SAT Transitions Guide](https://blog.dsat16.com/post/digital-sat-transitions-guide)

---

### GAP-017 | `transition_logic` — `purpose_action` vs. `result_consequence` Distinction Not in B.4

**Severity:** MINOR

**The distinction:**
- `result_consequence` (`therefore`, `thus`, `as a result`): The second
  statement is an **outcome that follows** from the first — it already
  happened.
- `purpose_action` (`to that end`, `to this end`, `for this purpose`):
  The second statement is an **intended action** taken in order to achieve
  the first statement's goal — it is directed forward, not backward.

Both occur after a goal or problem statement, making them contextually
interchangeable to a careless reader.

**Missing from B.4:** No distractor entry distinguishes these two subtypes
for generation purposes.

**Sources:**
[Test Innovators — Digital SAT Transitions](https://testinnovators.com/blog/digital-sat-reading-writing-transitions/),
[Albert.io — Rhetorical Synthesis](https://www.albert.io/blog/rhetorical-synthesis-sat-reading-and-writing-review/)

---

## Summary Table

| ID | Gap | Key(s) Affected | Severity |
|---|---|---|---|
| GAP-001 | SVA — Inverted sentence order (there/here is/are) | `subject_verb_agreement` | CRITICAL |
| GAP-002 | SVA — Indefinite pronoun subjects | `subject_verb_agreement` | CRITICAL |
| GAP-003 | SVA — Compound subjects with or/nor (proximity rule) | `subject_verb_agreement` | CRITICAL |
| GAP-004 | Verb form — Gerund vs. infinitive idiomatic selection | `verb_form` | CRITICAL |
| GAP-005 | Absolute phrases / Nominative absolutes | (new key or `modifier_placement`) | CRITICAL |
| GAP-006 | Subjunctive mood — Sub-patterns not documented | `verb_form` (pending D.2.9) | MAJOR |
| GAP-007 | Pronoun-antecedent — Singular `they`/`their` (gender-neutral) | `pronoun_antecedent_agreement` | MAJOR |
| GAP-008 | SVA — Stacked relative clauses (B.3 hard cap excluded) | `subject_verb_agreement` | MODERATE |
| GAP-009 | Verb tense — `Today`/`Now` shift sub-pattern not in B.3 | `verb_tense_consistency` | MODERATE |
| GAP-010 | Matching delimiter rule not stated as standalone | `appositive_punctuation` | MINOR |
| GAP-011 | No comma before/after preposition (Meltzer rule) | `punctuation_comma` | MINOR |
| GAP-012 | No comma before restrictive `that` | `punctuation_comma`, `relative_pronouns` | MINOR |
| GAP-013 | `commonly_confused_words` — Missing pairs, no B.3 sub-pattern | `commonly_confused_words` | MINOR |
| GAP-014 | B.4 SVA missing collective noun distractor type | `subject_verb_agreement` | MINOR |
| GAP-015 | B.4 modifier_placement missing passive-voice distractor | `modifier_placement` | MINOR |
| GAP-016 | B.4 transition: restatement vs. example not distinguished | `transition_logic` | MINOR |
| GAP-017 | B.4 transition: purpose_action vs. result_consequence not distinguished | `transition_logic` | MINOR |

---

## Excluded from This Report

The following were considered but determined to be **already covered in v8**:

- Collective noun / -s-ending singular nouns SVA → covered under
  `noun_countability` B.3 sub-pattern 3 ("Collective or '-s-Ending' Noun")
- Litotes / double negation → covered under `negation` B.3 sub-pattern 1
- Negation scope over quantifier (`not all` ≠ `none`) → covered under
  `negation` B.3 sub-pattern 2
- `who` vs. `whom` → covered under `pronoun_case` B.3 sub-pattern 3
- Pronoun case in elliptical clause after `than`/`as` → covered under
  `elliptical_constructions` B.3 sub-pattern 1
- Correlative conjunction parallelism → covered under `parallel_structure` B.3
- Double conjunction error → covered under `conjunction_usage` B.3
- Irregular plural possessives (`children's`) → covered under `apostrophe_use` B.3
- Colon = dash interchangeability → covered in `colon_dash_use` B.3
- Semicolon super-comma in complex lists → covered in `semicolon_use` B.3
- Indirect question / declarative word order → covered in
  `end_punctuation_question_statement` B.3
- Non-finite verb demotion as comma-splice repair → covered in
  `comma_splice` B.3 sub-pattern 3
