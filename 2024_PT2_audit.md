# 2024 Practice Test 2 Verbal Answer Audit

## Status

This is a provisional answer audit, not an official answer key. No official 2024
Practice Test 2 answer key was available in the local answer-key directory. The
conclusions below are based on:

- all 81 canonical database questions across Module 1, Module 2A, and Module 2B;
- the source PDFs `Test02_ENG_Sec01_Mod01.pdf`,
  `Test02_ENG_Sec01_Mod02A.pdf`, and `Test02_ENG_Sec01_Mod02B.pdf`;
- exact normalized question matches against already audited 2024 PT4-PT10 and
  2025 PT4-PT11 records;
- direct source-page review of unmatched questions, graphs, grammar, and answer
  choices; and
- explanation, option-count, and duplicate-choice consistency checks.

Fifty-five questions had exact full-content matches in already audited tests.
The remaining 26 were reviewed independently. Complete option-set matching was
used only as a discovery aid because generic grammar choices can occur in more
than one question.

The canonical PT2 rows use inconsistent exam codes (`SAT`, `2`, and `02`). This
audit selects the 81 rows by their full `Test02_ENG_Sec01_Mod*` source names. It
excludes 17 separate legacy rows stored as `source_test_name = 'Test02'`.

## Summary

- Questions audited: **81**
- Keep current DB answer: **77**
- Proposed answer changes: **4**
- Additional content or explanation repairs: **3**
- Database modified: **Yes — applied 2026-07-31 after independent review**

> **APPLIED 2026-07-31.** All findings below were independently verified against
> the rendered source PDFs before propagation. One correction was made to this
> audit in the process: Module 1 Q19's answer is **C**, not the B originally
> proposed here (see that section). All four answer changes, the Q19 option-text
> restoration, the Q7 passage replacement, and the Q19 explanation rewrite are
> now live in `dsat_dev`, along with rewritten per-option distractor rationales
> on all six questions. A drift scan across all 81 PT2 rows returns zero
> inconsistencies. Repair script: `scripts/repair_pt2_audit.py`.

### Proposed answer corrections

| Module | Question | DB answer | Audited answer | Reason |
|---|---:|:---:|:---:|---|
| 1 | 17 | B | **D** | The sentence has two coordinated objects of `because of`: the waterways and the fact that water conditions vary. No punctuation belongs inside that structure. |
| 1 | 19 | A | **C** | The sentence is a three-item series in which each product carries its own date. Source choice C uses a comma after `Basic` and a semicolon after `2009`, pairing `Chickasaw Basic` with 2009 and `Chickasaw TV` with 2010. |
| 2A | 11 | C | **D** | The graph shows lower iron and zinc levels in kanamycin-exposed plants than in controls. This also matches audited duplicates. |
| 2B | 21 | B | **A** | `However` contrasts this sentence with the preceding statement and belongs at the end of the first clause: `single-handedly, however;`. This also matches an audited duplicate. |

### Additional integrity findings

| Module | Question | Finding |
|---|---:|---|
| 1 | 19 | Three of the four DB option texts are corrupt. All four are stored ending `online television network;` with a semicolon, so A and B are exact duplicates, and C and D both differ from the source, which ends them with a comma. Only source choice A legitimately ends in a semicolon. Because C is the correct answer, the correct option's own text is among the corrupt ones, so the full option set must be restored from the source PDF. |
| 2B | 7 | The DB passage is copied from Q6 and discusses the Wigner crystal. The source Q7 passage concerns the *Terropterus xiushanensis* fossil and must replace it. Answer D remains correct. |
| 2B | 19 | The DB explanation discusses unrelated old quilts. The answer B is correct, but the explanation and associated rationale JSONB must be replaced. |

### Module 1 proposed key

`A C B C A B A D D A A B B A C B D A C D A B C C C D C`

### Module 2A proposed key

`B B D D A B C D C A D B B A B B C C D C A B A A B A D`

### Module 2B proposed key

`A B D C B A D D B C C C B C C C B B B D A B D A C A D`

## Module 1

| Q | DB | Audited | Verdict | Rationale |
|---:|:---:|:---:|---|---|
| 1 | A | A | Keep | The context indicates extensive adoption, so "widespread" is the most precise word. |
| 2 | C | C | Keep | "Comprises" means "consists of," correctly indicating that the cast contains the characters. |
| 3 | B | B | Keep | The discovery may persuade researchers to admit that women held leadership roles, so "concede" is correct. |
| 4 | C | C | Keep | In context, "endure" means tolerate or put up with. |
| 5 | A | A | Keep | The poem reflects on renewal and repetition coexisting in human life. |
| 6 | B | B | Keep | The waves repeatedly rush forward despite being repulsed, characterizing them as relentless and enduring. |
| 7 | A | A | Keep | The text describes the unusual delivery of a letter and then Rinaldo's overwhelming joy upon reading it. |
| 8 | D | D | Keep | The passage traces Mary's increasing pleasure in gardening. |
| 9 | D | D | Keep | The impractical apartment design is nevertheless presented as potentially improving residents' well-being. |
| 10 | A | A | Keep | The poem praises Dunbar's perception of both people and nature. |
| 11 | A | A | Keep | A directly conveys the writer's deep understanding of the reader's inner self. |
| 12 | B | B | Keep | Vietnamese and Spanish have very different speech rates but almost identical information rates. |
| 13 | B | B | Keep | Spider numbers also decline substantially without lizards, weakening the claim that lizards caused the entire decline. |
| 14 | A | A | Keep | Familiarity with organizational structures explains why civilian government work appeals to veterans. |
| 15 | C | C | Keep | The researchers' names restrictively identify which researchers are meant and take no commas. |
| 16 | B | B | Keep | A semicolon correctly separates the two independent clauses. |
| 17 | B | D | **Change** | "Millions of miles of waterways" and "the fact that ..." are coordinated objects of `because of`; D correctly inserts no punctuation. |
| 18 | A | A | Keep | The introductory phrase logically modifies "many critics," the people assessing the films. |
| 19 | A | C | **Change** | C is the only choice that keeps each product with its own date: `Chickasaw Basic, in 2009; an online television network, Chickasaw TV, in 2010; and a Rosetta Stone language course in Chickasaw, in 2015`. The DB text of C must also be repaired. |
| 20 | D | D | Keep | A colon correctly introduces the two sweet-potato varieties. |
| 21 | A | A | Keep | "Hence" marks the inability to confirm the theory as a consequence of evidence being erased. |
| 22 | B | B | Keep | B directly compares the two tunnel lengths using the relevant figures. |
| 23 | C | C | Keep | C uses the close movement of two stars to explain why the Pleiades now appears to contain six stars. |
| 24 | C | C | Keep | C states the fossil's significance as evidence of an early stage in pinniped evolution. |
| 25 | C | C | Keep | C contrasts the portraits by both medium and date, as requested. |
| 26 | D | D | Keep | D states the mistaken island classification and explains the name derived from the novel. |
| 27 | C | C | Keep | C emphasizes the paintings' shared large scale and provides both dimensions. |

### Module 1 Q19 source choices

- **A.** `Basic; in 2009, an online television network;`
- **B.** `Basic; in 2009, an online television network,`
- **C.** `Basic, in 2009; an online television network,`
- **D.** `Basic, in 2009, an online television network,`

The DB stores all four options ending in a semicolon (`... online television
network;`). That makes A and B exact duplicates and also corrupts C and D, whose
source text ends in a comma. Changing only the answer label would leave the
question invalid.

The passage reads:

> ... helped produce the world's first Indigenous-language instructional app,
> Chickasaw \_\_\_\_\_ Chickasaw TV, in 2010; and a Rosetta Stone language course
> in Chickasaw, in 2015.

The blank sits inside a three-item series of products, and the semicolon already
present before `and a Rosetta Stone` fixes the series' top-level separator as a
semicolon. Each item pairs a product with the year it appeared:

1. `Chickasaw Basic, in 2009`
2. `an online television network, Chickasaw TV, in 2010`
3. `a Rosetta Stone language course in Chickasaw, in 2015`

Choice **C** (`Basic, in 2009; an online television network,`) is the only option
that produces this reading: the comma after `Basic` attaches 2009 to the app, the
semicolon after `2009` closes the first item, and the trailing comma makes
`Chickasaw TV` an appositive renaming `an online television network`.

Choice B (`Basic; in 2009, an online television network,`) instead closes the
first item immediately after `Basic`, leaving the app undated and attaching 2009
to the television network — which contradicts the passage, since Chickasaw TV is
dated 2010 in the text that follows the blank.

## Module 2A

| Q | DB | Audited | Verdict | Rationale |
|---:|:---:|:---:|---|---|
| 1 | B | B | Keep | "Important" fits the description of a figure with significant accomplishments. |
| 2 | B | B | Keep | Cole's two interests culminate in his book, so "enthusiasm for" is precise. |
| 3 | D | D | Keep | "Overcome" means successfully address the transmission problem. |
| 4 | D | D | Keep | "Replenishes" means fills again, matching repopulation after the decline. |
| 5 | A | A | Keep | "Reflect" means show or represent, which fits the discussion of the Moon's surface record. |
| 6 | B | B | Keep | Similarity to modern climbing apes indicates adaptation to movement in trees. |
| 7 | C | C | Keep | "Abrupt" precisely matches the sudden appearance and rapid diversification. |
| 8 | D | D | Keep | Text 2 agrees with the Polynesian-origin claim but says the newer evidence supports it more strongly. |
| 9 | C | C | Keep | The text explicitly says Mother creates stories and poems for her children. |
| 10 | A | A | Keep | Participants found far fewer iridescent wings, directly supporting the camouflage claim. |
| 11 | C | D | **Change** | Both iron and zinc are lower in exposed plants than in controls, directly supporting altered metal uptake. |
| 12 | B | B | Keep | B directly contrasts the New York dawn with the speaker's desire to be on the island. |
| 13 | B | B | Keep | B connects Braschi's cross-genre practice to work produced in other artistic forms. |
| 14 | A | A | Keep | Since EBF activates Or31, identifying similar molecules is the logical next step. |
| 15 | B | B | Keep | The responses imply that volunteering benefits society more broadly than many youths realize. |
| 16 | B | B | Keep | The general scientific description requires the simple present "reach." |
| 17 | C | C | Keep | The singular subject "writing" requires "has been." |
| 18 | C | C | Keep | "Forcing" correctly expresses the result of the preceding clause. |
| 19 | D | D | Keep | The infinitive "to tell" expresses purpose. |
| 20 | C | C | Keep | The singular antecedent "a document" requires "outlines." |
| 21 | A | A | Keep | The possessive form of the plural noun "people" is "people's." |
| 22 | B | B | Keep | The past perfect "had doubled" places the doubling before the later past reference point. |
| 23 | A | A | Keep | "Suggested" maintains the passage's past-tense narrative. |
| 24 | A | A | Keep | The sentence shifts from historical practice to present practice, requiring the present-time transition. |
| 25 | B | B | Keep | The second sentence gives an example of the general statement. |
| 26 | A | A | Keep | "Afterward" shows that the CEO's response followed the failure. |
| 27 | D | D | Keep | "In addition" introduces another requirement of the amendment. |

## Module 2B

| Q | DB | Audited | Verdict | Rationale |
|---:|:---:|:---:|---|---|
| 1 | A | A | Keep | The blank requires a word meaning supporter or advocate, so "proponent" is correct. |
| 2 | B | B | Keep | "Inventive" accurately characterizes the creativity described. |
| 3 | D | D | Keep | Society imposes or "prescribes" rigid expectations. |
| 4 | C | C | Keep | "Disparate" means fundamentally different, matching the stated contrast. |
| 5 | B | B | Keep | Graeber and Wengrow reject a linear progression through fixed social stages. |
| 6 | A | A | Keep | The first visual confirmation is the strongest evidence yet for the Wigner crystal. |
| 7 | D | D | Keep | The source says all prior evidence came from Laurussia, while the new fossil came from Gondwana. D identifies its significance. The DB passage is wrong. |
| 8 | D | D | Keep | The picturesque rejected overt artifice but was still judged according to artistic principles. |
| 9 | B | B | Keep | The powder box shows the girl attending to her appearance, illustrating vanity. |
| 10 | C | C | Keep | Similar methods yield similar bite-force estimates, whereas different methods yield divergent estimates. |
| 11 | C | C | Keep | C supplies a negative relationship between otter characteristics and eelgrass health, contrary to the expectation. |
| 12 | C | C | Keep | C shows roots creating new paths even when easier cracks exist, supporting an active process. |
| 13 | B | B | Keep | Farming practices appearing after 1280 support migration from Mesa Verde to the Rio Grande Valley. |
| 14 | C | C | Keep | Confidentiality could prevent observers from assessing whether compensation is equitable. |
| 15 | C | C | Keep | The evidence supports arrival without people, implying that human activity was unnecessary. |
| 16 | C | C | Keep | C correctly forms the singular possessive `playa's` and plural possessive `rocks'`. |
| 17 | B | B | Keep | A semicolon separates the clauses, and a comma sets off the appositive identifying the second film. |
| 18 | B | B | Keep | "The bioswales" logically performs the action in the introductory modifier. |
| 19 | B | B | Keep | B forms a valid supplementary absolute phrase: `quilts, the stitching barely visible`. The DB explanation is unrelated. |
| 20 | D | D | Keep | D compares silica glass's atomic arrangement with alumina glass's atomic arrangement without a dangling comparison. |
| 21 | B | A | **Change** | `However` contrasts the second sentence with the preceding one and belongs at the end of the first clause: `single-handedly, however;`. |
| 22 | B | B | Keep | "Previously" correctly places the event before the later event described. |
| 23 | D | D | Keep | "Increasingly" indicates the growing trend required by the context. |
| 24 | A | A | Keep | "Alternatively" introduces the alternative possibility. |
| 25 | C | C | Keep | C states both the decline in apple varieties and its industrial-agriculture cause. |
| 26 | A | A | Keep | A introduces the book, author, and subject without repeating background the audience already knows. |
| 27 | D | D | Keep | D explains that bromelain improves protein absorption, which increases growth. |

### Module 2B Q7 source passage

The source passage explains that all previously known mixopterid fossils came
from species on Laurussia, whereas Wang's team found *Terropterus
xiushanensis* on Gondwana. The DB instead repeats the Wigner-crystal passage
from Q6. Q7's answer choices and answer D are correct, but its passage and any
passage-dependent annotation data must be replaced.

## DB work — completed 2026-07-31

All items below were applied via `scripts/repair_pt2_audit.py` in a single
transaction after independent verification against the source PDFs.

1. ~~Apply the four answer changes and rewrite their explanations.~~ **Done.**
   M1 Q17 B→D, M1 Q19 A→**C** (not B as originally proposed), M2A Q11 C→D,
   M2B Q21 B→A. New explanations written for all six touched questions.
2. ~~Restore all four Module 1 Q19 choices from the source PDF.~~ **Done.** All
   four now distinct: A ends in a semicolon, B/C/D end in a comma.
3. ~~Replace Module 2B Q7's passage and passage-dependent annotations.~~
   **Done.** The Terropterus xiushanensis passage replaced the duplicated
   Wigner-crystal text; all four option rationales rewritten against it.
4. ~~Replace Module 2B Q19's explanation and distractor rationales.~~ **Done.**
   The unrelated 1800s-quilt appositive rationale is gone; the absolute-phrase
   explanation replaces it.
5. ~~Synchronize `questions`, latest `question_versions`, latest
   `question_options`, `choices_jsonb`, and `annotation_jsonb`.~~ **Done.**
   Verified by a drift scan over all 81 PT2 rows: zero mismatches between
   `question_options.option_text`, `choices_jsonb`, and
   `annotation_jsonb.options[]`, and `is_correct` agrees with
   `correct_option_label` across all three surfaces.

### Notes on the applied repair

- All four rationales were rewritten on each flipped question, not just the two
  whose `is_correct` changed. The originals encoded a wrong theory of each
  question (e.g. M2A Q11's assumed the hypothesis predicted a zinc *increase*;
  M1 Q19's assumed the series break fell after `Basic`).
- Edits were made to the latest version row in place rather than by minting new
  version rows. These questions had zero `user_progress` attempts, so no student
  answer data was invalidated. Same approach as the PT1 Q13 repair (bug-819).
- One stale rationale was deleted rather than reworded: M2B Q21's choice A
  claimed "the semicolon should come before the conjunctive adverb, not after,"
  which is not a real rule.
- Pre-existing, unrelated: M1 Q20 and M2B Q16 store annotation options under
  `text`/`label` keys instead of `option_text`/`option_label`. Content is
  correct; only the key shape differs. Not touched by this repair.
