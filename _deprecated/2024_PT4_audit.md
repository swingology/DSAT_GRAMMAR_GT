# 2024 Practice Test 4 Verbal Answer Audit

## Status

This is a provisional answer audit, not an official answer key. No official 2024
Practice Test 4 answer key is present in the local answer-key directory, which
contains only Tests 5 through 10. The conclusions below are based on:

- all 81 PT4 database records and all 81 source-PDF question slots;
- the source PDFs `Test04_ENG_Sec01_Mod01.pdf`,
  `Test04_ENG_Sec01_Mod02A.pdf`, and `Test04_ENG_Sec01_Mod02B.pdf`;
- exact normalized question matches against already audited 2024 PT5-PT10 and
  2025 PT4-PT11 records;
- direct source-page review of unmatched questions, graphs, grammar, and answer
  choices; and
- explanation, option-count, duplicate-choice, and source-slot consistency
  checks.

The DB has 81 PT4 records but only 80 unique source slots: Module 1 Q13 is
duplicated and Module 1 Q14 is absent. Twelve of the 80 stored source slots had
exact full-content matches in already audited tests. The remaining 68 stored
slots were reviewed independently, and missing Q14 was solved from its source
page.

**Applied to the live DB on 2026-07-30.** The approved corrections and integrity
repairs in this report have been propagated through `questions`, active
`question_versions`, active `question_options`, `choices_jsonb`,
`annotation_jsonb`, `explanation_jsonb`, and the Q10 stimulus graph JSON. The
duplicate Q13 row was retained for audit history but retired and linked to the
active canonical row.

## Summary

- Source questions audited: **81**
- PT4 DB records after repair: **82 total; 81 active and 1 retired duplicate**
- Active unique source slots: **81**
- Pre-change answers retained on existing unique slots: **78**
- Answer changes applied to existing rows: **2**
- Missing question inserted: **Module 1 Q14, answer D**
- Duplicate record reconciled: **Module 1 Q13**
- Blank explanations repaired: **Module 1 Q15 and Q17**
- Misaligned explanation repaired: **Module 2A Q11**
- Source-text repairs applied: **Module 2A Q26 stem and Module 2B Q13 choice D**
- Database modified: **Yes, 2026-07-30**

### Applied answer corrections

| Module | Question | DB answer | Audited answer | Reason |
|---|---:|:---:|:---:|---|
| 1 | 17 | A | **C** | The blank separates two independent clauses: the initiative represented an investment; it prioritized improvements. Choice C supplies the required semicolon. |
| 2A | 10 | C | **A** | The graph places Washington between 600 and 800 organic farms. Wisconsin is around 1,300, but Iowa is around 700, so C is false. |

### Inserted question

Module 1 Q14 was absent from the DB and has now been inserted. Its sentence begins with the introductory
participial phrase `Known for ... pools,` and then names the subject: `Calida
Garcia Rawles was the logical choice ...`. No punctuation belongs between the
surname `Rawles` and the verb `was`, so source choice D is correct.

### Resolved data-integrity findings

1. **Module 1 Q13 was duplicated.** The same sauropod question appears as DB IDs
   `d6cc4659-46ec-53c6-b8b8-5f318650e84e` and
   `8e9c81a9-d41a-40f0-92a9-f6384eba9b86`. Both use answer B. The latter is now
   retired and linked to the former as its canonical official question.
2. **Module 1 Q15 and Q17 had empty explanations.** Both now have full
   official-answer-key-style explanations, and Q17 is corrected to C.
3. **Module 2A Q11's explanation was misaligned.** Answer C is correct because
   the quotation shows John working from early morning through afternoon, not
   merely because it demonstrates a physical trait. Its explanation and option
   rationales now address the actual claim.
4. **Module 2A Q26 repeated the question prompt.** The duplicate prompt has been
   removed from both the current question and active version.
5. **Module 2B Q13 choice D was truncated.** The restored source choice is: `The method
   for determining the composition of rocky planets is discovered to be less
   effective when used to analyze other kinds of planets.` Its explanation and
   distractor rationale now address the complete choice.
6. Every canonical stored slot has four distinct current option texts. No other
   option-count or duplicate-choice failure was found.

### Module 1 proposed key

`B B A B A D A A D B C B B D D B C A D D D C D A C D C`

### Module 2A proposed key

`D D A A B C C A C A C A D A D C B A A D C D B D D A B`

### Module 2B proposed key

`B B C C D A A A B C C D C B D A D D C A A C B C D A D`

## Module 1

| Q | DB | Audited | Verdict | Rationale |
|---:|:---:|:---:|---|---|
| 1 | B | B | Keep | The critics' concerns did not impede Whatley's advocacy, so `hinder` is precise. |
| 2 | B | B | Keep | The artisans generally follow inherited methods but sometimes depart from them, so `adhere to` fits. |
| 3 | A | A | Keep | `Haphazard` means lacking order or plan, matching the chaotic movement across time. |
| 4 | B | B | Keep | The protozoans' flexible strategies show behavior more sophisticated than merely `rudimentary` behavior. |
| 5 | A | A | Keep | `Surmised` means inferred or supposed, matching the historians' assumption later disproved by data. |
| 6 | D | D | Keep | In context, a machine that `answers` requirements fulfills or meets them. |
| 7 | A | A | Keep | Earth's helicopter cannot fly because Mars's much thinner atmosphere provides insufficient resistance. |
| 8 | A | A | Keep | Despite technological changes, jalis remain valued as preservers of their communities' histories. |
| 9 | D | D | Keep | Buck is indifferent to others and accepts Thornton's partners only because of their relationship to Thornton. |
| 10 | B | B | Keep | B directly conveys Du Bois's immediate, unexpected recognition of songs from a region unknown to him. |
| 11 | C | C | Keep | The graph shows that women constitute at least half of non-root-vegetable farmers in both north and south Ondo. |
| 12 | B | B | Keep | Treating Zelda only as Fitzgerald's inspiration omits her own novels and stories and misrepresents her literary contribution. |
| 13 | B | B | Keep | The absence of carbon-dioxide spikes at key stages of gigantism undermines the proposed dependence on increased carbon dioxide. |
| 14 | Missing | D | **Insert** | `Calida Garcia Rawles` is the complete subject name and must connect directly to `was`, with no punctuation after `Rawles`. |
| 15 | D | D | Keep | `Temple walls` completes one sentence; `With the help ...` correctly begins the next. |
| 16 | B | B | Keep | The properties belong to multiple snow grains, requiring the plural possessive `grains' physical properties`. |
| 17 | A | C | **Change** | `The initiative represented ...` and `it prioritized ...` are independent clauses, so choice C's semicolon is correct. |
| 18 | A | A | Keep | In the inverted construction, the singular subject `Josephine St. Pierre Ruffin` requires `was`. |
| 19 | D | D | Keep | Matching dashes correctly enclose the appositive identifying cephalopods as ocean dwellers. |
| 20 | D | D | Keep | The main clause needs the finite verb `will be`; the other choices are nonfinite. |
| 21 | D | D | Keep | `In fact` emphasizes that McFerrin finds research as engaging as visiting a location. |
| 22 | C | C | Keep | C introduces the familiar author's novel by naming it and describing its two central characters and settings. |
| 23 | D | D | Keep | D presents both the study's evidence about growth lines and its conclusion that the bones were juvenile. |
| 24 | A | A | Keep | A introduces Selvon and the novel while supplying its date, reputation, characters, and migration setting. |
| 25 | C | C | Keep | C states the requested similarity: both ridley species occur in the Atlantic Ocean. |
| 26 | D | D | Keep | D summarizes the study's central result that stronger winds reduced landing success. |
| 27 | C | C | Keep | C introduces the novel, its author, date, acclaim, genre, setting, and Gurnah's Nobel Prize. |

## Module 2A

| Q | DB | Audited | Verdict | Rationale |
|---:|:---:|:---:|---|---|
| 1 | D | D | Keep | Analysts expecting continued growth would have `predicted` future revenue. |
| 2 | D | D | Keep | Smooth, uniformly green leaves contrast with insect damage and describe a `healthy` plant. |
| 3 | A | A | Keep | The recognition of the work as groundbreaking means researchers `acknowledged` it. |
| 4 | A | A | Keep | Officials devise policies and administer services to `implement`, or carry out, the laws. |
| 5 | B | B | Keep | Jeyifous produced a new series of layered portraits, so `created` is precise. |
| 6 | C | C | Keep | Witnessing kindness promotes further helpful behavior, so individual acts can `foster` prosocial behavior. |
| 7 | C | C | Keep | The underlined sentence details how cuckoos place eggs in other birds' nests while those birds are away. |
| 8 | A | A | Keep | The owner thinks the picture does not belong yet is secretly proud of it, revealing conflicted feelings. |
| 9 | C | C | Keep | Text 2 argues that digital art still requires artistic fundamentals and skill with sophisticated tools. |
| 10 | C | A | **Change** | Washington's bar is between 600 and 800; Iowa's is well below 1,200, making A the only accurate completion. |
| 11 | C | C | Keep | Working from early morning until afternoon, with a body accustomed to the labor, directly illustrates John's dedication. |
| 12 | A | A | Keep | Personifying the moon as writing legends presents nature as an active participant. |
| 13 | D | D | Keep | Every species has substantially more juveniles in vegetation patches than the 15 percent expected randomly. |
| 14 | A | A | Keep | A explicitly argues that literature supplies a people's desire and strength for life and is necessary to its well-being. |
| 15 | D | D | Keep | Harvesting more than needed logically allowed the Sumerians to store surplus crops. |
| 16 | C | C | Keep | Rewards produce dopamine, fan-cell activity needs dopamine, and fan cells enable new associative memories. |
| 17 | B | B | Keep | The sentence needs the finite present-tense verb `claim`; the other forms cannot serve as the main verb. |
| 18 | A | A | Keep | No punctuation belongs between the preposition `of` and its objects. |
| 19 | A | A | Keep | `Explains` is the finite singular verb required for the subject `A recent study`. |
| 20 | D | D | Keep | `Was studying` describes the ongoing past action interrupted by the discovery. |
| 21 | C | C | Keep | The plural noun `stories` requires no apostrophe because the phrase is not possessive. |
| 22 | D | D | Keep | A comma before `while` correctly links the main statement to the contrasting subordinate clause. |
| 23 | B | B | Keep | The plural subject `barnacles` requires the plural reflexive pronoun `themselves`. |
| 24 | D | D | Keep | `As a result` marks spiders' ability to cling as the consequence of temporary atomic bonds. |
| 25 | D | D | Keep | `However` contrasts the longstanding Mauna Loa belief with evidence that Puhahonu is larger. |
| 26 | A | A | Keep | The calm caused by the stew supports the resulting theory about the name `unwinding`, so `Therefore` fits. |
| 27 | B | B | Keep | B both defines `flauna` as plant-animal hybrids and gives the requested parrot example. |

## Module 2B

| Q | DB | Audited | Verdict | Rationale |
|---:|:---:|:---:|---|---|
| 1 | B | B | Keep | `Innocuous` means harmless and refers back to harmless vibration and warming. |
| 2 | B | B | Keep | The contrast with many high-altitude studies requires `paucity of`, meaning scarcity. |
| 3 | C | C | Keep | A monarch must `buttress`, or support, the legitimacy of the right to the throne. |
| 4 | C | C | Keep | Helpful acts encourage additional helpful acts throughout the group, thereby fostering prosocial behavior. |
| 5 | D | D | Keep | The sentence explains the differing readiness of individual trees to yield sap, which the women test. |
| 6 | A | A | Keep | Jane works calmly while repeatedly imagining leaving, contrasting outward calm with inward restlessness. |
| 7 | A | A | Keep | The text states a general claim about Mitchell's cover art and then supports it with one album example. |
| 8 | A | A | Keep | The underlined sentence reports the relationship the analysis found between sunshine and forecast error. |
| 9 | B | B | Keep | Text 2 says EGR's human function remains unclear, making Text 1's optimism premature. |
| 10 | C | C | Keep | Because recorded counts are minimums, the actual acting and directing totals could exceed 66 and 58. |
| 11 | C | C | Keep | Polar mosasaur fossils coupled with few nonendothermic-reptile fossils support a cold-water advantage from endothermy. |
| 12 | D | D | Keep | The average number of department leaders reporting directly to CEOs rises across all three periods. |
| 13 | C | C | Keep | Planets containing more iron than their host stars directly contradict the equal-or-smaller-quantity claim. |
| 14 | B | B | Keep | B places African artists alongside prominent artists from other countries in a global postwar exhibition. |
| 15 | D | D | Keep | Without controlling election winners, researchers cannot easily identify otherwise similar non-office-holders. |
| 16 | A | A | Keep | Predominantly pre-invasion material containing Spanish-era references points to some post-invasion additions. |
| 17 | D | D | Keep | A semicolon separates the independent clauses, and a comma follows the conjunctive adverb `rather`. |
| 18 | D | D | Keep | `Was studying` correctly describes the ongoing past activity when Buratti made the discovery. |
| 19 | C | C | Keep | A comma introduces the supplementary participial phrase `having left New York Harbor ...`. |
| 20 | A | A | Keep | The singular book title takes the singular verb phrase `has enhanced`. |
| 21 | A | A | Keep | A period ends the sentence about studying tombs; `Built into ...` begins a new sentence modifying the chambers. |
| 22 | C | C | Keep | `Critic Stina Chyn` is the subject and `claims` its verb, so neither takes an intervening comma. |
| 23 | B | B | Keep | Semicolons separate the three list items because the first item contains an internal comma. |
| 24 | C | C | Keep | `However` contrasts Hammurabi's many achievements with what he is mainly remembered for today. |
| 25 | D | D | Keep | `Similarly` links two parallel examples of Dove setting personal stories against broad historical movements. |
| 26 | A | A | Keep | `Nevertheless` contrasts Larlarb's usual custom fitting with the standard-size factory production. |
| 27 | D | D | Keep | D makes the generalization that comet orbits change and supports it with 81P/Wild's former and current orbit. |

## Applied DB work

All seven repair steps above were applied transactionally on 2026-07-30. Exact
post-commit read-back confirmed:

1. Each module has 27 active rows and 27 unique question numbers.
2. Module 1 Q17 is C and Module 2A Q10 is A in `questions`, the active version,
   the active annotation, and the single correct option row.
3. Module 1 Q14 has four source-faithful choices and answer D in every storage
   layer.
4. Every touched row has four options in `question_options`, `choices_jsonb`,
   and `annotation_jsonb`, with zero label, text, or correctness drift.
5. Corrected explanations agree exactly across the current question, active
   version, and `explanation_jsonb`.
6. No existing student attempts referenced either corrected-answer row.
