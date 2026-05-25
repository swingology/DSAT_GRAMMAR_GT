# V3 Research Report — External Validation & Enhancement Recommendations

**Date**: 2026-04-29
**Purpose**: External research synthesis identifying gaps in V2 rules and recommending targeted enhancements for V3

---

## 1. Methodology

Conducted 15 targeted web searches across College Board official specifications, test prep expert analyses, and DSAT-specific strategy guides. Sources include:

- College Board Assessment Framework for the Digital SAT Suite v3.01 (August 2024)
- College Board 2025-26 SAT School Day Student Guide
- The Test Advantage, PrepScholar, UWorld, Princeton Review, Khan Academy
- ChatSAT Benchmark Study (AI-generated vs. official questions, May 2025)
- InGenius Prep analysis of AI SAT diagnostics (February 2026)
- Bluebook test frequency analyses (Tests 4-10)

---

## 2. College Board Official Content Domain Blueprint

The Digital SAT Reading and Writing section has four content domains in every module, always in this order:

| Domain | Weight | Questions |
|--------|--------|-----------|
| Craft and Structure | ~28% | 13-15 |
| Information and Ideas | ~26% | 12-14 |
| Standard English Conventions | ~26% | 11-15 |
| Expression of Ideas | ~20% | 8-12 |

SEC has exactly two testing points: **Boundaries** (sentence completeness, punctuation between/within sentences) and **Form, Structure, and Sense** (agreement, verb form, modifier placement, possessives/plurals).

Expression of Ideas has exactly two testing points: **Rhetorical Synthesis** (notes integration) and **Transitions** (logical connector selection).

Reference: `satsuite.collegeboard.org/media/pdf/assessment-framework-for-digital-sat-suite.pdf`

---

## 3. Gap Analysis & Recommended Enhancements

### 3.1 Expression of Ideas Distractor Heuristics (CRITICAL — P0)

**Finding**: V2 Section 18 provides detailed distractor tables for 18+ SEC grammar focus families but has only a minimal 3-row table for Transition Logic and NO tables for Rhetorical Synthesis, Redundancy/Concision, Precision Word Choice, Register/Style Consistency, Emphasis/Meaning Shifts, or Data Interpretation Claims.

**Impact**: Expression of Ideas is ~20% of all DSAT questions. Without heuristic tables, generated EOI distractors lack the structured competition of SEC distractors.

**Recommended**: Add full distractor heuristic tables for all 7 EOI focus keys.

#### Rhetorical Synthesis Patterns Discovered

Five goal types govern all Rhetorical Synthesis questions:

| Goal Type | Signal Structure |
|-----------|-----------------|
| Contrast/Difference | Must mention both subjects; "whereas," "unlike," "while" |
| Similarity | Must mention both subjects; "both," "similarly," "also" |
| Summarize/Introduce | Broad coverage of multiple bullets; reject narrow options |
| Specific Detail | Must include keyword from prompt (time, person, place) |
| Generalization | Synthesize across bullets without minutiae |

Four deadly traps identified:

1. **Correct Info, Wrong Goal** — accurately reflects notes but fails the stated rhetorical goal
2. **Goal Achievement with Distortion** — uses absolute language ("always," "never") unsupported by notes
3. **Outside Knowledge** — introduces facts not in the bullet points
4. **Reversed Causation** — misrepresents cause-effect direction

The "Smart Student" Trap (December 2025 SAT advisory): high scorers pick the most eloquent-sounding answer rather than the one that literally fulfills the prompt. These are data retrieval tasks, not reading comprehension.

#### Transition Word Taxonomy

Complete 3-category 10-subcategory taxonomy derived from Bluebook frequency analysis:

**I. CONTINUE (Additive)**
- Addition: *also, besides, furthermore, in addition, moreover*
- Similarity: *likewise, similarly, by the same token*
- Example: *for example, for instance, specifically, in particular*
- Clarification: *in other words, that is, namely*
- Emphasis: *in fact, indeed, notably*
- Sequence: *afterward, eventually, previously, subsequently, then, ultimately*

**II. CONTRAST (Adversative)**
- Direct Opposition: *however, nevertheless, nonetheless, conversely, yet, but*
- Concession: *admittedly, granted, that said, still, even so*
- Difference: *by comparison, in contrast, alternatively*

**III. CAUSE-AND-EFFECT (Causal)**
- Result: *therefore, thus, consequently, hence, accordingly, as a result*

Bluebook frequency ranking (Tests 4-10): However (10x), Therefore (8x), Conversely (8x), Nevertheless (7x), Accordingly (6x), Thus (6x), Consequently (5x).

Hard vs. Soft distinction: adverbs (*however*, *therefore*) are "hard" transitions (require comma after); FANBOYS and subordinators are "soft" (don't require comma after when starting a clause).

#### Redundancy/Concision Patterns

Three mechanisms identified:
1. **Definition-repetition**: adjective + its own definition ("inaudible and could not be heard")
2. **Wordy phrases**: *due to the fact that→because, at this point in time→now, has the ability to→can*
3. **"Being" rule**: *being* is almost always wordy on the SAT

Key rule: shortest answer that preserves meaning is correct (provided no grammar flaw).

---

### 3.2 Boundaries Decision Tree & Anti-Trap Rules (HIGH — P1)

**Finding**: V2 has disambiguation rules but lacks the structured decision framework used across all major prep sources.

Clear decision framework:

| What's Before/After Blank | Correct Punctuation |
|---------------------------|---------------------|
| IC + IC | `.` or `;` or `, FANBOYS` |
| IC + list/explanation | `:` or `—` |
| IC—extra info—IC | paired `, ... ,` or paired `— ... —` |
| DC + IC | `,` |
| IC + DC | no punctuation (usually) |

Critical anti-traps:
- If period and semicolon both appear with no other difference, BOTH are wrong
- Colon after verb is always wrong (e.g., "The species were: hawks, falcons")
- Colon after preposition is always wrong
- "Including," "such as," "like" NEVER followed by colon
- 0 or 2 punctuation marks between subject and verb — NEVER 1
- Never mix dash with comma for paired non-essential elements

---

### 3.3 Form/Structure/Sense Edge Cases (HIGH — P1)

**Finding**: V2 covers main patterns but missing explicit handling of specific edge cases that make high-difficulty items authentic.

**Collective Nouns**: SAT treats all collectives as singular (team, committee, jury, company, audience, staff, faculty, class, government, band, family). Exception only when individuals act separately (rarely tested).

**Inverted Sentences**: 3 patterns:
1. Prepositional fronting: "On my forehead reside five pimples" → subject after verb
2. There-is/are: "There are three reasons" → subject follows verb
3. Linking verb inversion: "Less fun are its consequences"

**Tricky Singular Subjects**:
- *each, every, everyone, everybody* → always singular
- Gerunds as subjects → always singular
- Titles of works → always singular (even if plural-looking)
- *the number of* → singular; *a number of* → plural

**Or/Nor Proximity Rule**: verb agrees with closest subject

**Possessive/Contraction Confusion**: *its/it's, whose/who's, their/they're/there* — SAT consistently tests this

**Pronoun Agreement**: SAT has not historically accepted singular "they" (requires "he or she"); need to verify current Bluebook stance

---

### 3.4 Missing Passage Construction Rules (MEDIUM — P2)

**Finding**: Section 17 covers ~30 focus keys with explicit templates but ~14 approved keys rely on ambiguous "use closest family above" fallback.

Missing templates: `voice_active_passive`, `negation`, `noun_countability`, `determiners_articles`, `affirmative_agreement`, `elliptical_constructions`, `quotation_punctuation`, `logical_predication`, `conjunction_usage`, `possessive_contraction`, `precision_word_choice`, `register_style_consistency`, `emphasis_meaning_shifts`, `data_interpretation_claims`.

---

### 3.5 Authenticity Anti-Patterns (MEDIUM — P2)

**Finding**: Research on AI vs. official SAT question quality reveals systematic patterns that distinguish authentic questions.

Key findings from the ChatSAT Benchmark Study (May 2025):
- AI matched difficulty distribution but 31% needed revisions
- AI questions had overly discriminating distractor profiles (1.69 vs 1.26 for official)
- Common failures: diverging from standardized prompt language, missing disciplinary literacy

From InGenius Prep (Feb 2026): AI questions "mimicked SAT style without accurately targeting the reasoning, analysis, and problem-solving skills emphasized by College Board."

Anti-pattern checklist:
1. All four options should produce coherent, meaningful sentences — difference must be structural, not semantic
2. Distractors must represent common student misconceptions (not random errors)
3. Question phrasing must be standardized (no diverging from official prompt language)
4. Grammar must be tested in prose context, not as isolated rule application
5. Topic distribution should match College Board content domains (Literature, History/Social Studies, Humanities, Science)
6. No option should be visibly longer, safer, or more polished than the rest
7. Answer must not rely on "which sounds right" — rule must be deterministically applicable
8. Precision score 2 options (grammatically valid but suboptimal) must be rare and intentional

---

### 3.6 2025-2026 DSAT Trends (LOW — P3)

- Poetry passages more frequent (theme, tone, figurative language)
- Table-based questions standard (2-3 per module)
- Module 1/Module 2 difficulty gap widening (M1 slightly easier, M2 significantly harder)
- Passage length trending to 110-120 words for logical completion items
- Scientific/economic reasoning passages increasingly common
- Punctuation and sentence structure questions getting more intricate

---

## 4. V3 Enhancement Summary

| # | Enhancement | Priority | Status in V3 |
|---|-------------|----------|--------------|
| 1 | Expression of Ideas distractor heuristics (§18.1-18.7) | P0 | Implemented |
| 2 | Boundaries decision tree + anti-traps (§25) | P1 | Implemented |
| 3 | Form/Structure/Sense edge case appendix (§26) | P1 | Implemented |
| 4 | Filled passage construction rules (§17) | P2 | Implemented |
| 5 | Authenticity anti-patterns (§27) | P2 | Implemented |
| 6 | 2025-2026 DSAT trends noted (§28) | P3 | Implemented |

---

## 5. Sources

- [College Board Assessment Framework for Digital SAT Suite v3.01](https://satsuite.collegeboard.org/media/pdf/assessment-framework-for-digital-sat-suite.pdf)
- [College Board Digital SAT Test Spec Overview](https://satsuite.collegeboard.org/media/pdf/digital-sat-test-spec-overview.pdf)
- [The Test Advantage — DSAT Grammar Rules Cheat Sheet 2026](https://thetestadvantage.com/blog/sat-grammar-rules-cheat-sheet-2026-all-15-rules)
- [The Test Advantage — Digital SAT Punctuation Rules 2026](https://thetestadvantage.com/blog/digital-sat-punctuation-rules-2026-commas-semicolons-colons)
- [The Test Advantage — DSAT Rhetorical Synthesis Guide (June 2025)](https://thetestadvantage.com/blog/how-to-solve-digital-sat-notes-questions-june-2025-guide)
- [The Test Advantage — Complete SAT Transition Words Guide](https://thetestadvantage.com/blog/sat-transition-words-guide-categories-examples-for-higher-scores)
- [PrepScholar — Subject-Verb Agreement on the SAT](http://blog.prepscholar.com/subject-verb-agreement-on-sat-writing-strategies-and-practice)
- [PrepScholar — Transition Questions on SAT Writing](https://blog.prepscholar.com/transition-questions-on-sat-writing)
- [PrepScholar — Wordiness and Redundancy on SAT](https://blog.prepscholar.com/wordiness-and-redundancy-in-sat-writing)
- [UWorld — Subject Verb Agreement SAT Guide](https://collegeprep.uworld.com/blog/subject-verb-agreement-on-sat-writing/)
- [UWorld — Pronoun Agreement SAT Guide](https://collegeprep.uworld.com/blog/pronoun-agreement-sat-writing-tips-practice/)
- [Princeton Review — Hardest SAT English Questions](https://www.princetonreview.com/sat-study/hardest-sat-english-questions)
- [ChatSAT Benchmark Study — AI vs. Official SAT Questions (May 2025)](https://pursu.io/guide/does-chatgpt-generated-practice-match-official-sat-difficulty-a-benchmark-study)
- [InGenius Prep — AI-Generated SAT Practice: What Works & What Doesn't (Feb 2026)](https://ingeniusprep.com/blog/ai-generated-sat-practice-tests-what-works-and-what-does-not/)
- [IVY Lounge Test Prep — Complete Transition Word List (2026)](https://www.ivyloungetestprep.com/blog/the-most-complete-transition-word-guide)
- [NUM8ERS — DSAT Boundaries Guide](https://num8ers.com/boundaries/)
