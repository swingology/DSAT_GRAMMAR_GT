# 2024 Practice Test 1 Verbal Answer Audit

## Status

This is a provisional answer audit, not an official answer key. No official 2024
Practice Test 1 answer key was available. The conclusions below are based on:

- all 81 current database questions across Module 1, Module 2A, and Module 2B;
- the source PDFs `Test01_ENG_Sec01_Mod01.pdf`,
  `Test01_ENG_Sec01_Mod02A.pdf`, and `Test01_ENG_Sec01_Mod02B.pdf`;
- exact normalized question matches against already audited 2024 PT4-PT10 and
  2025 PT4-PT11 records;
- source-page review of unmatched questions, graphs, tables, grammar, and answer
  choices; and
- explanation-to-answer consistency checks.

Forty-eight questions had exact full-content matches in already audited tests.
The remaining 33 were reviewed independently. Complete option-set matching was
used only as a discovery aid because generic grammar choices can occur in more
than one question.

## Summary

- Questions audited: **81**
- Keep current DB answer: **76**
- Proposed answer changes: **5**
- Module 2B proposed changes: **0**
- Database modified: **No**

### Proposed corrections

| Module | Question | DB answer | Audited answer | Reason |
|---|---:|:---:|:---:|---|
| 1 | 11 | A | **D** | The graph shows general uncertainty substantially below trade-policy uncertainty in 2005 but substantially above it in 2010. This also matches an audited duplicate. |
| 1 | 13 | C | **A** | The countries are similar in 1900 but sharply different by 1950. The source-PDF answer is A, "1900 with the employment by sector in 1950." The DB choices are corrupted and must be repaired with the answer. |
| 1 | 17 | A | **D** | "Essays" ends the first sentence. "Praising her ..." begins a new sentence and correctly modifies writer Robert Antoni. |
| 1 | 21 | D | **C** | "However" is supplementary at the end of the first independent clause: `antiquity, however;` correctly uses a comma before it and a semicolon between clauses. This also matches audited duplicates. |
| 2A | 22 | C | **D** | The blank is a direct question, so it requires subject-auxiliary inversion and a question mark: `could the blueberries thrive?` This also matches audited duplicates. |

### Module 1 proposed key

`A C C B C D D D B C D C A D B B D A C D C D A D C B A`

### Module 2A proposed key

`C D B D A A C D B C C B B A A D A A A C B D A C A A D`

### Module 2B proposed key

`B A B C D B D B D B A A D D D B D D C A B A A B D C A`

## Module 1

| Q | DB | Audited | Verdict | Rationale |
|---:|:---:|:---:|---|---|
| 1 | A | A | Keep | The example shows that biodiversity loss from invasive species can be avoided, so "preventable" is the most precise word. |
| 2 | C | C | Keep | "By no means unimportant" means that recognizing Bosch's influence is important. |
| 3 | C | C | Keep | The second sentence identifies uncertainty about Betelgeuse's internal state, the problem Nance and colleagues attempted but failed to solve. |
| 4 | B | B | Keep | The third sentence states a general evolutionary principle that the mimosa and *B. terrenus* example then illustrates. |
| 5 | C | C | Keep | Focarelli and Panetta distinguish adverse short-term effects from long-term consumer benefits, so they would encourage studying long-term effects. |
| 6 | D | D | Keep | Elinor serves as her mother's counselor and governs her own feelings despite being nineteen, demonstrating unusual maturity. |
| 7 | D | D | Keep | Mrs. Ochiltree's frank comments cause acquaintances to avoid her, implying that the comments offend them. |
| 8 | D | D | Keep | The speaker goes to bed exhausted but remains awake thinking about the friend. |
| 9 | B | B | Keep | B shows reductions in both hard-to-digest compounds and antinutrients after fermentation. |
| 10 | C | C | Keep | The 28% versus 90% ablation rates directly illustrate that faster-moving dust has a higher ablation rate. |
| 11 | A | D | **Change** | In 2005 general uncertainty is far below trade uncertainty; in 2010 it is far above trade uncertainty. Only D accurately states both comparisons. |
| 12 | C | C | Keep | Alaska marmots have shorter torpor bouts and longer arousal episodes than Arctic ground squirrels, supporting C. |
| 13 | C | A | **Change** | The two countries are similar in 1900 and strongly diverge by 1950. Source choice A states that comparison. See the data-integrity note below. |
| 14 | D | D | Keep | The proposed method selectively targets the invasive plant without harming other organisms. |
| 15 | B | B | Keep | The restrictive clause identifying which center is meant should not be preceded by a comma. |
| 16 | B | B | Keep | The antecedent is the plural phrase "two memorable woodcuts," so the plural pronoun and verb are required. |
| 17 | A | D | **Change** | A period completes the list ending in "essays." The participial phrase beginning "Praising" then correctly modifies Robert Antoni. |
| 18 | A | A | Keep | The sentence needs the finite main verb "helped"; A supplies it. |
| 19 | C | C | Keep | The title *Gingerbread* is a restrictive identifier and takes no separating punctuation. |
| 20 | D | D | Keep | The singular pronoun "it" refers to "a traditional violin." |
| 21 | D | C | **Change** | The first independent clause ends with the supplementary "however" and must be separated from the next independent clause by a semicolon. |
| 22 | D | D | Keep | The passage contrasts radio listeners' and television viewers' perceptions, so the contrast transition is required. |
| 23 | A | A | Keep | "Still" contrasts Sher-Gil's success in Paris with her desire to return to India. |
| 24 | D | D | Keep | The next sentence specifies Sauer's broader argument, so "Specifically" is logical. |
| 25 | C | C | Keep | "Consequently" correctly marks the result of the obstacle described before the blank. |
| 26 | B | B | Keep | B combines the study method, date, and conclusion in a way that satisfies the stated writing goal. |
| 27 | A | A | Keep | A directly contrasts the Anglo-French origin of one word with the Greek origin of the other. |

### Module 1 Q13 data-integrity issue — RESOLVED 2026-07-30

The source PDF choices are:

- **A.** 1900 with the employment by sector in 1950.
- **B.** 1800 with the employment by sector in 2012.
- **C.** 1900 with the employment by sector in 2012.
- **D.** 1800 with the employment by sector in 1900.

~~The DB instead stores only `1800`, `1900`, `1950`, and `2012`. Changing only the
answer label would leave this question invalid; the four option texts and related
JSONB must be replaced from the source page before any DB propagation.~~

**Fixed (2026-07-30, bug-819).** All four option texts and `choices_jsonb` were
replaced from the source page, and the correct answer is now label `A`. Note that
the "DB answer C → audited answer A" framing in the summary table above was
incoherent as originally written: with bare years stored, DB label `C` (`1950`)
did not denote PDF choice `C` (`1900 ... 2012`), so relabeling asserted nothing.
The repair was a content re-ingest, not a relabel. Also corrected: the stem read
"complete the text?" but the PDF reads "complete the statement?", and the four
distractor rationales described single years rather than year pairs.

Verified after repair: `question_options`, `question_versions.choices_jsonb`, and
the denormalized `questions` columns all agree, and a drift scan across all 81 PT1
questions returned 0 inconsistencies.

## Module 2A

| Q | DB | Audited | Verdict | Rationale |
|---:|:---:|:---:|---|---|
| 1 | C | C | Keep | "Interpret" means determine or explain meaning, fitting the discussion of difficult poems. |
| 2 | D | D | Keep | "Substantial" precisely matches the stated idea of considerable variation in venom potency. |
| 3 | B | B | Keep | Ochoa lacks certainty and offers a conjecture, so "speculates" is correct. |
| 4 | D | D | Keep | The collaboration serves as an example of the model and therefore "exemplifies" it. |
| 5 | A | A | Keep | Hiccups are uncontrollable contractions, so they occur "involuntarily." |
| 6 | A | A | Keep | Flowering at the same time as the host is "synchronization." |
| 7 | C | C | Keep | "Extensive" accurately characterizes the many varied contributions described. |
| 8 | D | D | Keep | The crops form a complex, interdependent, or "intricate," network. |
| 9 | B | B | Keep | Dorian's flushed cheeks and joyful expression show delight at the portrait. |
| 10 | C | C | Keep | C explicitly describes walking where nature leads and supplies countryside imagery. |
| 11 | C | C | Keep | C shows Mrs. Spring Fragrance giving household-care instructions, directly illustrating her concern. |
| 12 | B | B | Keep | Hedda explicitly says that she wants the power to shape another person's destiny. |
| 13 | B | B | Keep | If the settlement dates to the fourteenth century but the artifacts are older, the artifacts must have arrived from elsewhere. |
| 14 | A | A | Keep | Orangutans' upright movement in trees supports a tree-dwelling origin for bipedalism. |
| 15 | A | A | Keep | Failure to control task dexterity could create apparent cognitive differences that do not actually exist. |
| 16 | D | D | Keep | The text says manufacturing and distribution costs changed more than authoring, editing, and design costs. |
| 17 | A | A | Keep | The plural antecedent "customers" requires the plural pronoun "they." |
| 18 | A | A | Keep | The relative clause needs the finite verb "provided." |
| 19 | A | A | Keep | A comma plus "but" correctly joins the contrasting independent clauses. |
| 20 | C | C | Keep | "Their" is the possessive form agreeing with Watson and Crick. |
| 21 | B | B | Keep | The modal "would" governs the base verb "create." |
| 22 | C | D | **Change** | This is a direct question, not an embedded question: "could the blueberries thrive?" correctly uses inversion and a question mark. |
| 23 | A | A | Keep | The singular gerund phrase "landing on one of the good spaces" requires "allows." |
| 24 | C | C | Keep | "Finally" marks the successful end of fifteen years of repeated attempts. |
| 25 | A | A | Keep | "For instance" introduces larch trees as an example of non-evergreen conifers. |
| 26 | A | A | Keep | "In addition" adds a second example of Coleridge-Taylor emphasizing his ancestry. |
| 27 | D | D | Keep | D makes the requested generalization about using statistical methods to study Beatles authorship. |

## Module 2B

| Q | DB | Audited | Verdict | Rationale |
|---:|:---:|:---:|---|---|
| 1 | B | B | Keep | The fungus reciprocates the tree's carbon by helping it absorb nitrogen. |
| 2 | A | A | Keep | "Recognizable" matches the idea of something easy to observe. |
| 3 | B | B | Keep | Pico honors nature in tribal belief but dislikes wilderness personally, showing ambivalence. |
| 4 | C | C | Keep | The examples show varied diets and abilities, contradicting the claim that early mammals lacked diversity. |
| 5 | D | D | Keep | Jamie Okuma's work challenges the idea that fine art and fashion rarely "intersect." |
| 6 | B | B | Keep | A claim that fails to account for recent discoveries is "tenuous." |
| 7 | D | D | Keep | "Peripheral" accurately describes a place far from the capital. |
| 8 | B | B | Keep | The underlined conflict between prior research and later election losses is resolved by the discussion of strategic timing. |
| 9 | D | D | Keep | The Lord Chancellor describes unity, but the narrator immediately observes disagreement. |
| 10 | B | B | Keep | The Alboran decline coincides with a strong local oxygenation decline, while the Mauritanian decline occurs with little local change. |
| 11 | A | A | Keep | A directly shows Chambi documenting multiple levels of Peruvian society. |
| 12 | A | A | Keep | A describes a collective failing because its members could not share credit and responsibility. |
| 13 | D | D | Keep | Fewer sharks permit more cownose rays, which then consume more oysters; D states the hypothesized chain. |
| 14 | D | D | Keep | Recently originating folklore supports continuing cultural interaction rather than ancient derivation. |
| 15 | D | D | Keep | Structural coloration lets tanagers mimic a costly carotenoid signal, making the signal potentially dishonest. |
| 16 | B | B | Keep | Solitary tortoises' preference for face-like stimuli weakens a specifically social-adaptation explanation. |
| 17 | D | D | Keep | "Aluminum oxide" restrictively identifies the chemical and takes no comma. |
| 18 | D | D | Keep | The singular subject "triangle" requires "is." |
| 19 | C | C | Keep | A restrictive title immediately before a proper name takes no comma. |
| 20 | A | A | Keep | A colon correctly introduces the explanation that follows. |
| 21 | B | B | Keep | The singular subject "shape" requires "is." |
| 22 | A | A | Keep | The colon introduces the explanation of how Hopper's career extended beyond equations. |
| 23 | A | A | Keep | "Specifically" introduces the detailed mechanism behind the general aurora statement. |
| 24 | B | B | Keep | "Additionally" adds another reason for the justices' resistance. |
| 25 | D | D | Keep | "Thus" marks the second sentence as a consequence of the first. |
| 26 | C | C | Keep | C emphasizes both the duration and purpose of the work preserving Gullah culture. |
| 27 | A | A | Keep | A directly states the research aim and gives the requested context. |

## Recommended DB work after external review

Do not propagate this provisional key until it has been independently checked.
If the five corrections are confirmed, update answer and explanation fields in
`questions`, latest `question_versions`, latest `question_options`,
`choices_jsonb`, `annotation_jsonb`, and `explanation_jsonb`. Module 1 Q13 also
requires replacing all four option texts from the PDF before synchronizing its
answer metadata.
