# Research Notes: Digital SAT Grammar — Gap Analysis

**Task**: Final pass on the Digital SAT verbal section grammar rules. Evaluate the existing `grammar_focus_key` list for missing Standard English Conventions topics the SAT actually tests.

**Existing grammar_focus_keys under review**:
`subject_verb_agreement`, `parallel_structure`, `pronoun_antecedent_agreement`, `comma_splice`, `run_on_sentence`, `apostrophe_possession`, `modifier_placement`, `transition_words`, `verb_tense_consistency`

---

## What I Found

### The Current Taxonomy vs. The Full Taxonomy

The project's current `grammar_focus_key` controlled vocabulary (as of v2.4) is actually much larger than the nine keys listed in the task prompt — the master taxonomy file at `taxonomy/DSAT_Verbal_Master_Taxonomy_v2.md` Section 7.4 already enumerates 24 keys. This gap analysis therefore has two layers: (1) what's missing from the nine-key "short list" the user mentioned, and (2) whether anything is missing from the full 24-key list in the database schema.

The 24 keys currently in the DB are:
`subject_verb_agreement`, `pronoun_antecedent_agreement`, `pronoun_case`, `modifier_placement`, `parallel_structure`, `verb_tense_consistency`, `verb_form`, `comma_splice`, `sentence_fragment`, `semicolon_use`, `apostrophe_use`, `punctuation_comma`, `sentence_boundary`, `voice_active_passive`, `logical_predication`, `conjunction_usage`, `comparative_structures`, `noun_countability`, `affirmative_agreement`, `elliptical_constructions`, `negation`, `relative_pronouns`, `possessive_contraction`, `hyphen_usage`

This is a strong set. The analysis below addresses what the SAT tests and where gaps still exist.

---

### College Board's Official Structure for SEC Questions

The Digital SAT organizes Standard English Conventions into two top-level skill buckets:

**Boundaries** — purely about selecting the right punctuation mark to correctly delimit clauses, phrases, and sentence units. Tests: periods, commas, semicolons, colons, dashes, and when *no* punctuation is correct. Source: Test Innovators guide, Khan Academy Form/Structure/Sense overview.

**Form, Structure, and Sense** — grammar and usage, independent of punctuation mechanics. College Board's official sub-skills here are: subject-verb agreement, verb forms (finite/nonfinite, tense, mood), pronoun-antecedent agreement, subject-modifier placement, and plural/possessive forms of nouns. Source: College Board Reading and Writing Specifications page, Test Ninjas Form/Structure/Sense breakdown.

Practically every third-party analysis of released Digital SAT tests (PrepScholar, Test Ninjas, Test Innovators, The Critical Reader, The Test Advantage) converges on the same approximately 15 rule categories.

---

### The Nine-Key Short List: What's Missing vs. the Full SAT Scope

Against just the nine keys listed in the task prompt, the following rule areas are real SAT test points that are absent:

**Sentence fragment** — The SAT tests incomplete sentences (dependent clause or phrase punctuated as a full sentence) at medium frequency, separate from comma splices and run-ons. The full taxonomy has `sentence_fragment` as its own key; the short list omits it.

**Semicolon, colon, and dash usage** — Boundary punctuation questions are among the highest-frequency question types on the test (Test Innovators, Test Ninjas both confirm punctuation is over a quarter of all SEC questions). The short list has no key for semicolons, colons, or dashes. The full taxonomy has `semicolon_use` and `punctuation_comma`; colon and dash are bundled into `sentence_boundary` or `punctuation_comma`, which may be under-specified (see gaps section below).

**Pronoun case** — Who vs. whom, I vs. me, subjective vs. objective in compound structures. This is a distinct test point from pronoun-antecedent agreement. The full taxonomy has `pronoun_case`; the short list conflates this with `pronoun_antecedent_agreement`.

**Verb form (finite/nonfinite)** — This is explicitly called out as a College Board test point. The SAT presents sentences where the choice is between a finite verb form and a nonfinite form (infinitive, gerund, participle). A real released question asks students to choose between "to reach" and a conjugated verb form. College Board internally labels this "nonfinite base forms." The full taxonomy has `verb_form` covering this ground, but the short list has only `verb_tense_consistency`, which is different.

**Modifier placement / dangling modifiers** — The short list has `modifier_placement`, so this one is covered.

**Plural vs. possessive nouns** — The SAT specifically tests whether a noun should be plural, singular possessive, or plural possessive (beyond just apostrophe mechanics). Multiple sources confirm this is a distinct test point (Alps Academy, PrepScholar possessives guide, Test Ninjas). The full taxonomy has `apostrophe_use` and `possessive_contraction`; the short list only has `apostrophe_possession`, which partially covers this.

**Relative pronouns / restrictive vs. non-restrictive clauses** — Which vs. that, who vs. whom in relative clause contexts, and the presence or absence of commas around essential vs. non-essential modifiers. The full taxonomy has `relative_pronouns`; the short list omits this entirely.

**Nonessential element punctuation** — Setting off parenthetical information consistently with a matched pair (two commas, two dashes, or two parentheses — you cannot mix types). This is a high-frequency boundary question type that doesn't map cleanly to any key in the short list. The full taxonomy handles it imperfectly; it's partially covered by `punctuation_comma` and `sentence_boundary`.

---

## Gaps and Issues in the Full 24-Key Taxonomy

Against the broader 24-key list (which is what actually lives in the DB), the following observations apply:

**Colon/dash as punctuation-after-independent-clause** — Currently these appear to be rolled into `sentence_boundary` or `punctuation_comma`, but colon and dash questions are common enough and mechanically distinct enough that a `colon_dash_use` key (or separate `colon_use` and `dash_use` keys) would add precision. A colon question always tests whether an independent clause precedes the colon; a dash question tests either the colon-equivalent use or matched nonessential pairs. Both are meaningfully different from a comma question or semicolon question. Every major test prep source treats these as distinct rule types. Frequency: Test Innovators and PrepScholar both confirm colon/dash questions appear regularly in Boundaries.

**Nonessential element consistency** — The rule "you cannot mix a dash on one side with a comma on the other" is a real SAT trap that doesn't fit cleanly into any existing key. It's not purely `punctuation_comma`, not purely a `sentence_boundary` issue, and not `semicolon_use`. It might warrant a dedicated key like `nonessential_element_punctuation` or at minimum should be explicitly called out in the `punctuation_comma` mapping notes.

**Finite vs. nonfinite verb forms** — The existing `verb_form` key covers this, but the mapping description reads "Indicative vs subjunctive, active vs passive, infinitive vs gerund" which is a reasonable scope. What it should also explicitly include: choosing a nonfinite infinitive ("to + verb") when the sentence already has a finite main verb, vs. a second finite verb that would create a fragment or run-on. College Board has released actual questions on this; Khan Academy has a dedicated lesson ("FSS Verb Forms") for it. The existing key handles it but the description could be tightened.

**Question marks for direct vs. indirect questions** — Test Ninjas explicitly lists this as one of their 18 rules ("Use question marks for direct questions only, not indirect ones"). Example: "She asked where he was going." (no question mark) vs. "Where is he going?" (question mark). This is not currently in the 24-key taxonomy. It's a low-frequency rule but it's testable, and it belongs under `sentence_boundary` or as a standalone `terminal_punctuation` key. Worth adding.

**Word choice / diction within SEC** — Occasionally the SAT presents a grammar question where the distractor pattern includes a real word used in the wrong syntactic slot rather than an inflectional error. Test Ninjas and Test Advantage list "Word Choice" as a distinct rule. This is arguably in a gray zone between SEC and Expression of Ideas, but in pure SEC questions the distractor can be "a word that is grammatically correct but semantically wrong in this syntactic position." The taxonomy currently handles this in the distractor section (Section 4, `semantic_imprecision`) but has no `grammar_focus_key` for it. Most practitioners treat this as out-of-scope for SEC and inside EOI (vocabulary/diction), which seems right. Not recommending a new key here, just flagging the borderline.

**"As vs. like" and preposition idioms** — Currently handled under `conjunction_usage` ("as vs. like" note in Rule 2.10.3) and the general `comparative_structures` key. The existing coverage is adequate; these rules appear at low frequency on the Digital SAT. No new key needed.

**Double negatives and negation patterns** — The existing `negation` key is well-specified. Worth noting that Double Negative questions are very rare on the Digital SAT (appears mainly in older paper SAT prep materials); the "hardly/scarcely/no sooner" inversion patterns listed in the taxonomy are more ACT-flavored. On the Digital SAT, the more common negation trap is incorrect "neither...nor" parallelism, which is already covered under `parallel_structure`. The `negation` key should probably be deprioritized in generation since it doesn't appear frequently in released Digital SAT material.

**Affirmative agreement / tag questions** — The `affirmative_agreement` key (so/neither inversion, tag questions) is similarly ACT-adjacent. I found no evidence from released Digital SAT test analysis that tag questions or so/neither inversions appear in Digital SAT SEC questions. This key should be marked low-confidence for Digital SAT specifically.

---

## Recommended Additions

Two genuine gaps worth adding as new keys:

**`colon_dash_use`** (or split into `colon_use` + `dash_use`) — Colon and dash as punctuation-after-independent-clause are high-frequency Boundaries question types. They have distinct rules from commas and semicolons (colon: must follow complete independent clause, introduces explanation/list; dash: introduces explanation like colon, OR marks nonessential pair). Every major prep source treats these as a distinct category. Proposed mapping: `grammar_role_key` = `punctuation`.

**`nonessential_element_punctuation`** — The rule about using matched pairs (both commas, both dashes, both parentheses — no mixing) is a real and frequently tested Digital SAT Boundaries rule. It overlaps with `punctuation_comma` but the matching-pair constraint is its own distinct trap. Alternatively, this could be folded explicitly into `punctuation_comma`'s mapping description rather than made a new key. Either way, it needs to be explicitly represented.

**`terminal_punctuation`** (low priority) — Direct vs. indirect question mark. Real rule, very low frequency on Digital SAT. Could be added as a minor key under `sentence_boundary`. Not critical.

---

## Validation of Existing Keys Against Real SAT Frequency

| Key | SAT Frequency | Notes |
|---|---|---|
| `subject_verb_agreement` | Very High | Core test point; accurate |
| `pronoun_antecedent_agreement` | Medium | Well covered |
| `pronoun_case` | Medium | Real test point; who/whom, I/me |
| `modifier_placement` | Medium | Dangling modifier questions confirmed |
| `parallel_structure` | Medium-High | Lists and correlative conjunctions |
| `verb_tense_consistency` | High | Confirmed very high frequency |
| `verb_form` | Medium | Finite/nonfinite confirmed by CB |
| `comma_splice` | High | Very high frequency |
| `sentence_fragment` | Medium | Real test point |
| `semicolon_use` | High | Confirmed high frequency |
| `apostrophe_use` | High | Confirmed high frequency |
| `punctuation_comma` | Very High | Non-restrictive clauses, intros, appositives |
| `sentence_boundary` | Medium | Catch-all structural boundary |
| `relative_pronouns` | High | Which/that, who/whom confirmed |
| `possessive_contraction` | Medium | Its/it's, their/they're confirmed |
| `hyphen_usage` | Low-Medium | Less common but real |
| `voice_active_passive` | Low | Real but rare on Digital SAT |
| `logical_predication` | Low | "Reason is because" rare on DSAT |
| `conjunction_usage` | Medium | FANBOYS + conjunctive adverbs |
| `comparative_structures` | Medium | Faulty comparison, as...as patterns |
| `noun_countability` | Low-Medium | Fewer/less, amount/number |
| `affirmative_agreement` | Very Low | Likely ACT-adjacent, not Digital SAT |
| `elliptical_constructions` | Low | Appears in harder questions |
| `negation` | Very Low | Primarily ACT; rare on DSAT |

---

## Summary

The 24-key taxonomy is substantially complete and well-grounded. The nine-key short list mentioned in the task is missing about half the real test points. The two most significant missing items from the full 24-key taxonomy are: **colon/dash usage** (high-frequency Boundary question type with distinct mechanics) and **nonessential element punctuation consistency** (matched-pair rule for commas, dashes, and parentheses). Two existing keys — `affirmative_agreement` and `negation` — appear to be low-confidence inclusions for Digital SAT specifically and should be flagged as ACT-adjacent. The `verb_form` key is well-placed to handle finite/nonfinite verb questions, which College Board explicitly tests.

---

*Sources consulted*:
- [Test Innovators: Digital SAT Grammar and Punctuation Guide](https://testinnovators.com/blog/standard-english-conventions-guide-digital-sat/)
- [Test Ninjas: 18 SAT Grammar Rules](https://test-ninjas.com/sat-grammar-rules)
- [Test Ninjas: Form, Structure, and Sense](https://test-ninjas.com/sat-form-structure-and-sense)
- [PrepScholar: Complete Guide to SAT Grammar Rules](https://blog.prepscholar.com/the-complete-guide-to-sat-grammar-rules)
- [The Critical Reader: Complete SAT Grammar Rules](https://thecriticalreader.com/complete-sat-grammar-rules/)
- [ELA Free: Finite vs Non-Finite Verbs Explained for Digital SAT](https://www.elafree.com/2026/01/finite-vs-non-finite-verbs-digital-sat-grammar-guide.html)
- [College Board: Reading and Writing Specifications](https://satsuite.collegeboard.org/k12-educators/about/alignment/reading)
- [The Test Advantage: SAT Grammar Rules Cheat Sheet 2026](https://thetestadvantage.com/blog-details/530)
- [Alps Academy: Plural and Possessive Nouns on SAT](https://www.alps.academy/sat-plural-and-possessive-nouns/)
