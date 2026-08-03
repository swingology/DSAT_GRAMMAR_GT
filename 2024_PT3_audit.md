# 2024 Practice Test 3 Verbal Answer Audit

## Status

This is a provisional answer audit, not an official answer key. No official 2024
Practice Test 3 answer key was available in the local answer-key directory. The
conclusions below are based on:

- all 80 canonical PT3 database rows and all 81 source-PDF question slots;
- the source PDFs `Test03_ENG_Sec01_Mod01.pdf`,
  `Test03_ENG_Sec01_Mod02A.pdf`, and `Test03_ENG_Sec01_Mod02B.pdf`;
- exact normalized question matches against already audited 2024 PT4-PT10 and
  2025 PT4-PT11 records;
- direct source-page review of unmatched questions, graphs, grammar, and answer
  choices; and
- explanation, option-count, and duplicate-choice consistency checks.

Fifty-four of the 80 stored questions had exact full-content matches in already
audited tests. The remaining 26 stored questions were reviewed independently.
The missing source question was reviewed from its PDF page and cross-checked
against an audited duplicate.

## Summary

- Source questions audited: **81**
- Canonical DB questions present: **80** → **81 after repair**
- Keep current DB answer: **78**
- Proposed answer changes to existing rows: **2**
- Missing question to insert: **Module 2B Q4, answer A**
- Additional option-text repair: **Module 2B Q19 choice C**
- Database modified: **Yes — applied 2026-07-31 after independent review**

> **APPLIED 2026-07-31.** Every substantive claim in this audit was independently
> verified against the rendered source PDFs and confirmed correct — no finding
> required correction. All three changes are live in `dsat_dev`: Q13 C→B, Q19
> A→C (with choice C's option text restored), and Q4 inserted with answer A.
> New explanations and per-option distractor rationales were written for all
> three. Module 2B's stored key now matches this audit's proposed key exactly.
> Repair script: `scripts/repair_pt3_audit.py`.
>
> Two items this audit does not mention, neither affecting its conclusions:
> Module 1 is stored under the legacy `source_test_name = 'Bluebook Practice
> Test 3'`, not `Test03_ENG_Sec01_Mod01`; and the stored explanations for Q13
> and Q19 both argued for the wrong answer (Q19's stated the correct rule and
> then chose the option violating it). Both are detailed in `DEBUG_LOG.md`.

### Proposed answer corrections

| Module | Question | DB answer | Audited answer | Reason |
|---|---:|:---:|:---:|---|
| 2B | 13 | C | **B** | The lowest-performing spray-coated layer has higher efficiency than the highest-performing spin-coated layer. This also matches audited duplicates. |
| 2B | 19 | A | **C** | `However` is parenthetical and requires commas on both sides: `nickname, however, feeling that ...`. Source choice C is correct. |

### Missing question

Module 2B Q4 is absent from the DB. The source question states that director
Sterlin Harjo rejects television's tendency to place Native characters only in
the distant past. Choice A, **repudiates**, means rejects and is correct. This is
also confirmed by an audited PT8 duplicate.

### Additional integrity finding

Module 2B Q19 choices B and C are duplicated in the DB. Source choice C is
`nickname, however,` with a comma after `however`; the DB incorrectly stores a
semicolon there. The choice text must be repaired with the answer.

### Module 1 proposed key

`B D C B A D A A A D A B A C A D D D C C B D C A D D C`

### Module 2A proposed key

`B B C B D A D A A C C C B D A D A B B A D D D A C B D`

### Module 2B proposed key

`D D C A C A D D A A A C B C A C B C C A A B B A D B B`

## Module 1

| Q | DB | Audited | Verdict | Rationale |
|---:|:---:|:---:|---|---|
| 1 | B | B | Keep | The baskets use sweetgrass and palmetto palm, so "handmade from" is precise. |
| 2 | D | D | Keep | "Dormant" means temporarily inactive, fitting genes that are present but have no effect. |
| 3 | C | C | Keep | "Confined to" means limited to, matching the claim that the influence extended beyond Spain. |
| 4 | B | B | Keep | "Impenetrable" describes a field that was extremely difficult to enter. |
| 5 | A | A | Keep | In context, "assumed" means acquired or took on greater precision. |
| 6 | D | D | Keep | The speaker answers a charge and then announces an intention to establish comradeship. |
| 7 | A | A | Keep | The text explicitly says ecologists are concerned because Pando's growth is declining. |
| 8 | A | A | Keep | The researchers measured surprise through the animals' ear and head movements. |
| 9 | A | A | Keep | The unusual and influential book is presented as an important contribution to food writing. |
| 10 | D | D | Keep | D shows Alexandra gaining comfort and security from contemplating nature's order. |
| 11 | A | A | Keep | A cupid does not conclusively identify Venus because cupids could be linked to fishing more generally. |
| 12 | B | B | Keep | Addressing conflicting views would help judges consider and rebut objections. |
| 13 | A | A | Keep | The specialized historical knowledge required by the history plays makes them less accessible than the tragedies. |
| 14 | C | C | Keep | The comma belongs inside the closing quotation mark before the sentence continues. |
| 15 | A | A | Keep | The introductory phrase must modify researcher Robert Losey, the person who uncovered the fragments. |
| 16 | D | D | Keep | A comma closes the introductory appositive describing Mary Ping. |
| 17 | D | D | Keep | The singular antecedent "Nerf football" requires "is a smaller, foam version." |
| 18 | D | D | Keep | The comma introduces the participial phrase describing Potter's mycology work. |
| 19 | C | C | Keep | "Julian's 1935 synthesis" is the achievement logically modified by the introductory phrase. |
| 20 | C | C | Keep | A period separates the completed VisiCalc sentence from the next independent sentence. |
| 21 | B | B | Keep | "Next" introduces the following step in the experiment. |
| 22 | D | D | Keep | "Second" continues the explicit sequence begun with "First." |
| 23 | C | C | Keep | "Thus" marks the Ceres finding as a consequence of the spectroscopic-fingerprint principle. |
| 24 | A | A | Keep | A emphasizes both the discovery's role in decoding the genetic code and its broader health significance. |
| 25 | D | D | Keep | D directly contrasts the two materials' emissivity values. |
| 26 | D | D | Keep | D explains that the Hart-Celler Act abolished a quota system favoring northern Europe. |
| 27 | C | C | Keep | C states the format's advantage: audiences could control their experience. |

## Module 2A

| Q | DB | Audited | Verdict | Rationale |
|---:|:---:|:---:|---|---|
| 1 | B | B | Keep | Lawrence's attention to neighborhood details makes "observant" precise. |
| 2 | B | B | Keep | Physicists examine particles, so "inspecting" is the appropriate verb. |
| 3 | C | C | Keep | Years of work across a vast region are accurately described as "persistent." |
| 4 | B | B | Keep | The contrast shows the old chemical process was "inadequate." |
| 5 | D | D | Keep | Jemisin refuses to follow, or "conform to," genre conventions. |
| 6 | A | A | Keep | Historians dismissed the letters because they could not validate their authenticity. |
| 7 | D | D | Keep | The poem encourages the son to go forward and embrace life's opportunities. |
| 8 | A | A | Keep | The passage's primary purpose is to explain von Ahn's invention of reCAPTCHA. |
| 9 | A | A | Keep | Text 2 accepts that the skulls looked birdlike, making the initial interpretation understandable. |
| 10 | C | C | Keep | The flower comparison shows that the mind needs proper nourishment to thrive. |
| 11 | C | C | Keep | Red maple alone is native to North America and does not exceed 60 feet. |
| 12 | C | C | Keep | C shows the notes were requested to market the edition to readers who already owned the poem. |
| 13 | B | B | Keep | Amal interprets the girl's flower gathering as joyful and carefree. |
| 14 | D | D | Keep | All listed planets exceed 0.25 Jupiter masses, and all but TOI-1478 b orbit in under ten days. |
| 15 | A | A | Keep | At every orientation, high-information voters have a higher voting probability. |
| 16 | D | D | Keep | Persisting fluency and cultural pride into adulthood support future language transmission. |
| 17 | A | A | Keep | Gibson uses traditional Native beadwork and dressmaking in an original artwork. |
| 18 | B | B | Keep | "Have used" is the finite verb required to complete the clause. |
| 19 | B | B | Keep | A comma plus "but" joins the two independent clauses. |
| 20 | A | A | Keep | "Enter" is the finite main verb required by the sentence. |
| 21 | D | D | Keep | "Is" agrees with the present-time cue "Today." |
| 22 | D | D | Keep | The essential `whenever` clause follows "is added" without punctuation. |
| 23 | D | D | Keep | The general biological fact requires the simple present "survives." |
| 24 | A | A | Keep | "Meanwhile" indicates that Obinze's and Ifemelu's actions occur concurrently. |
| 25 | C | C | Keep | "Similarly" connects comparable actions in Los Angeles and San Francisco. |
| 26 | B | B | Keep | B states the requested advantage: infilling is less invasive than power grinding. |
| 27 | D | D | Keep | D identifies the artwork's key visual feature and supplies enough context for an unfamiliar audience. |

## Module 2B

| Q | DB | Audited | Verdict | Rationale |
|---:|:---:|:---:|---|---|
| 1 | D | D | Keep | "Invalidate" means disprove; the delays extend rather than disprove the projection. |
| 2 | D | D | Keep | Negating "latent" establishes that the spleen actively supports diving. |
| 3 | C | C | Keep | Employment, housing, and climate exert stronger influence, so taxes are "overshadowed by" them. |
| 4 | Missing | A | **Insert** | Harjo rejects television's historical confinement of Native characters; "repudiates" means rejects. |
| 5 | C | C | Keep | Different waste components decay at different rates, so MSW cannot be treated as "undifferentiated." |
| 6 | A | A | Keep | Tom assures the group that the play will be harmless and private. |
| 7 | D | D | Keep | John's desire to follow the twigs toward the sea reveals longing for a larger life. |
| 8 | D | D | Keep | The underlined scene illustrates Lily's sensitivity to surroundings that match her mood. |
| 9 | A | A | Keep | Text 2 challenges the assumed intensity of direct phytoplankton competition. |
| 10 | A | A | Keep | At every depth, beach-collected tools outnumber tools made from seafloor shells. |
| 11 | A | A | Keep | The awe condition leads participants to help collect more pens, demonstrating altruism. |
| 12 | C | C | Keep | Voters become more polarized than nonvoters, contradicting the claim that voting does not alter attitudes. |
| 13 | C | B | **Change** | Even the lowest-performing spray-coated layer exceeds the highest-performing spin-coated layer, directly supporting B. |
| 14 | C | C | Keep | Lear's words and gesture explicitly express regret for having acted foolishly. |
| 15 | A | A | Keep | Nonmycorrhizal broccoli gains some mass with fungi, contrary to the predicted lack of benefit. |
| 16 | C | C | Keep | Replacing ELF3 removes temperature-sensitive flowering, identifying ELF3 as causal. |
| 17 | B | B | Keep | Modest productivity gains combined with tax incentives support tax benefits as the stronger adoption motive. |
| 18 | C | C | Keep | A matching dash closes the parenthetical appositive before the sentence continues. |
| 19 | A | C | **Change** | `However` is parenthetical and requires commas on both sides. Source choice C is correct and its DB text must be repaired. |
| 20 | A | A | Keep | A colon introduces the explanation of how the number varied. |
| 21 | A | A | Keep | "To forge" expresses the chemists' purpose. |
| 22 | B | B | Keep | A colon introduces the explanation of what the structures called arcs are. |
| 23 | B | B | Keep | "By contrast" introduces the opposing condition described next. |
| 24 | A | A | Keep | A accurately says the Sun is hotter than most, but not all, nearby stars. |
| 25 | D | D | Keep | D explains the collection, translation, and paper-sharing process used to preserve knowledge. |
| 26 | B | B | Keep | B states both the research question and the computer-simulation methodology. |
| 27 | B | B | Keep | B emphasizes the shared characteristic that neither path requires diving. |

### Module 2B Q19 source choices

- **A.** `nickname, however`
- **B.** `nickname, however;`
- **C.** `nickname, however,`
- **D.** `nickname; however,`

The DB currently stores the semicolon version for both B and C. Changing only
the answer label would leave the question invalid.

## DB work — completed 2026-07-31

Applied via `scripts/repair_pt3_audit.py` in a single transaction (26 statements)
after independent verification against the source PDFs.

1. ~~Insert Module 2B Q4 from the source PDF with answer A and a source-grounded
   explanation.~~ **Done.** Inserted with the passage, all four choices, answer A,
   a full annotation, and per-option rationales. Its UUID was derived with the
   ingestion pipeline's own deterministic UUID5 scheme
   (`ingest.py::_official_question_uuid`), so re-ingesting this module updates the
   row rather than creating a duplicate.
2. ~~Change Module 2B Q13 from C to B and replace its explanation and
   rationales.~~ **Done.**
3. ~~Restore Module 2B Q19 choice C, change its answer from A to C, and replace
   its explanation and rationales.~~ **Done.** Choice C now reads
   `nickname, however,`; it had been stored as `nickname, however;`, duplicating B.
4. ~~Synchronize `questions`, latest `question_versions`, latest
   `question_options`, `choices_jsonb`, `annotation_jsonb`, and
   `explanation_jsonb`.~~ **Done.** Verified by a drift scan over all 81 PT3 rows.

### Notes on the applied repair

- All four rationales were rewritten on each changed question, not just the pair
  whose `is_correct` swapped, because the originals encoded a wrong reading. Q19's
  stored explanation had stated the correct rule ("a comma before and after the
  parenthetical adverb") and then selected choice A, which has no comma after
  `however`.
- Existing rows were edited in place rather than by minting new version rows.
  These questions had zero `user_progress` attempts, so no student answer data was
  invalidated. Same approach as the PT1 (bug-819) and PT2 (bug-821) repairs.
- **Pre-existing condition found during this work:** 408 of 1489 rows
  database-wide have a `latest_annotation_id` whose `question_version_id` points
  at a superseded version — PT3 M2B Q13 is one. Any script that locates a
  question's annotation by `question_version_id` silently updates nothing on those
  rows. Annotations must be reached via `questions.latest_annotation_id`.
- **Pre-existing, not repaired:** five PT3 questions have annotations missing
  option detail — M1 Q10's annotation has no `options` array at all, and M2A Q1,
  Q3, Q4, and Q6 carry `option_label`/`is_correct` but no `option_text`. Stored
  answers on all five are correct; only the annotation shape is incomplete.
