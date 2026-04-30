# College Board PT4 Answer-Question Analysis

Date: 2026-04-29

## Sources Matched

Local source PDFs:

- `TESTS/DATA_SRC/2025-2026 Tests Answers/ANSWERS/sat-practice-test-4-answers-digital.pdf`
- `TESTS/DATA_SRC/2025-2026 Tests Answers/Practice Tests/sat-practice-test-4-digital.pdf`
- `TESTS/DATA_SRC/2025-2026 Tests Answers/ANSWERS/sat-practice-test-5-answers-digital.pdf`
- `TESTS/DATA_SRC/2025-2026 Tests Answers/Practice Tests/sat-practice-test-5-digital.pdf`
- `TESTS/DATA_SRC/2025-2026 Tests Answers/ANSWERS/sat-practice-test-6-answers-digital.pdf`
- `TESTS/DATA_SRC/2025-2026 Tests Answers/Practice Tests/sat-practice-test-6-digital.pdf`
- `TESTS/DATA_SRC/2025-2026 Tests Answers/ANSWERS/sat-practice-test-7-answers-digital.pdf`
- `TESTS/DATA_SRC/2025-2026 Tests Answers/Practice Tests/sat-practice-test-7-digital.pdf`
- `TESTS/DATA_SRC/2025-2026 Tests Answers/ANSWERS/sat-practice-test-8-answers-digital.pdf`
- `TESTS/DATA_SRC/2025-2026 Tests Answers/Practice Tests/sat-practice-test-8-digital.pdf`
- `TESTS/DATA_SRC/2025-2026 Tests Answers/ANSWERS/sat-practice-test-9-answers-digital.pdf`
- `TESTS/DATA_SRC/2025-2026 Tests Answers/Practice Tests/sat-practice-test-9-digital.pdf`
- `TESTS/DATA_SRC/2025-2026 Tests Answers/ANSWERS/sat-practice-test-10-answers-digital.pdf`
- `TESTS/DATA_SRC/2025-2026 Tests Answers/Practice Tests/sat-practice-test-10-digital.pdf`
- `TESTS/DATA_SRC/2025-2026 Tests Answers/ANSWERS/sat-practice-test-11-answers-digital.pdf`
- `TESTS/DATA_SRC/2025-2026 Tests Answers/Practice Tests/sat-practice-test-11-digital.pdf`

Method:

- Extracted both PDFs with `pdftotext -layout`.
- Matched Reading and Writing items by module number and question number.
- Used the answer-explanation PDF as the authority for correct answers and College Board reasoning.
- Compared observed explanation patterns with:
  - `rules_v2/rules_core_generation.md`
  - `rules_v2/rules_dsat_reading_module.md`
  - `rules_v2/rules_dsat_grammar_module.md`
  - `rules_v2/future_plans.md`
  - `rules_agent_dsat_reading_v1.md`

Important format note: these PDFs are the nondigital linear accommodation version. Each Reading and Writing module has 33 questions. The current `rules_v2/future_plans.md` module blueprint defaults to 27-question digital modules unless stats specify otherwise, so PT4, PT5, PT6, PT7, PT8, PT9, PT10, and PT11 should be treated as paper-accommodation stats sources, not as the default adaptive app module length.

## Executive Findings

The current rules cover most College Board reasoning patterns well. The strongest coverage is in evidence anchoring, controlled skill keys, distractor plausibility, grammar-domain separation, transition logic, quantitative evidence, cross-text comparison, and the requirement to explain why each wrong answer fails.

The main gaps are generation calibration gaps rather than taxonomy failures:

- Add a 33-question paper-accommodation blueprint or explicit source-format flag.
- Add explicit Words in Context handling for polarity and negation context, such as "by no means" and "not atypical."
- Add an experimental-design/control-group passage architecture for support, weaken, inference, and data items.
- Add a grammar punctuation rule for no punctuation inside a required syntactic unit, such as between a preposition and its complement or between a verb and its object.
- Expand Expression of Ideas / notes synthesis into finer audience-purpose patterns: audience familiar vs unfamiliar, emphasize similarity/difference, explain advantage, explain mechanism, present a theory, introduce a work, identify real author or pseudonym, classify a category, emphasize a sample, identify a profession/title/setting/year/duration/distance, present a study overview or methodology, present aim of a study, provide a historical overview, compare lengths/quantities/sizes/meters, identify statistical-authorship studies, emphasize duration and purpose, and avoid irrelevant background.

## What College Board Explanations Emphasize

Across the PT4 explanations, College Board consistently uses the same reasoning template:

1. Name why the correct answer satisfies the exact task in the stem.
2. Define the key word, convention, relationship, or evidence target.
3. Point to the specific context, data, sentence role, claim, or grammar boundary that makes the answer required.
4. Explain each wrong answer by a single clear failure: unsupported, contradicted, irrelevant to the claim, wrong comparison, wrong rhetorical action, wrong transition relation, or violation of a convention.

The explanations are especially focused on exactness. Wrong answers are often close in topic but fail because they do not address the specific claim, do not preserve the same variable, describe the wrong relationship, use the wrong scope, or add information the text does not support.

## Observed Module Distribution

### Reading and Writing Module 1

| Q | Ans | Observed CB focus | Rules coverage |
|---:|:---:|---|---|
| 1 | B | Words in Context: context-supported verb choice | Covered |
| 2 | A | Words in Context: context-supported meaning | Covered |
| 3 | A | Words in Context: comparison clue | Covered |
| 4 | C | Words in Context: negated/polarity context | Partially covered; add WIC polarity trap |
| 5 | A | Text Structure/Purpose: literary main purpose | Covered |
| 6 | B | Text Structure/Purpose: overall structure of poem | Covered |
| 7 | D | Text Structure/Purpose: criticism then ambition | Covered |
| 8 | B | Text Structure/Purpose: sentence function | Covered |
| 9 | B | Cross-Text: Text 2 response disputes Text 1 | Covered; confirms disagreement-oriented response rule |
| 10 | D | Central Ideas: literary main idea | Covered |
| 11 | C | Central Details: directly supported analogy | Covered |
| 12 | D | Central Ideas: literary main idea | Covered |
| 13 | A | Quantitative Evidence: graph completion | Covered |
| 14 | B | Textual Evidence: supports hypothesis | Covered |
| 15 | C | Quantitative Evidence: table example/comparison | Covered |
| 16 | A | Textual Evidence: quotation illustrates claim | Covered |
| 17 | A | Quantitative Evidence: surprising table result | Covered; could better encode expectation-violation data pattern |
| 18 | A | Inference: logically completes conclusion | Covered |
| 19 | A | SEC: plural/possessive nouns | Covered |
| 20 | D | SEC: verb tense for general fact | Covered |
| 21 | D | SEC: sentence boundary with period | Covered |
| 22 | D | SEC: subject-verb agreement | Covered |
| 23 | B | SEC: semicolon joining main clauses | Covered |
| 24 | C | SEC: subject-modifier placement | Covered |
| 25 | B | SEC: complex series punctuation | Covered |
| 26 | A | SEC: conjunctive adverb punctuation | Covered |
| 27 | C | Transition: final event in sequence | Covered |
| 28 | D | Transition: contrast/refutation | Covered |
| 29 | A | Transition: addition | Covered |
| 30 | A | Transition: result/consequence | Covered |
| 31 | D | Notes synthesis: emphasize difference | Broadly covered; needs finer synthesis subtypes |
| 32 | D | Notes synthesis: describe work to unfamiliar audience | Broadly covered; needs audience subtype |
| 33 | C | Notes synthesis: present research to unfamiliar audience | Broadly covered; needs audience/research subtype |

### Reading and Writing Module 2

| Q | Ans | Observed CB focus | Rules coverage |
|---:|:---:|---|---|
| 1 | D | Words in Context: prediction/future meaning | Covered |
| 2 | D | Words in Context: overcome an obstacle | Covered |
| 3 | B | Words in Context: inspecting/examining | Covered |
| 4 | B | Words in Context: comparable/similar | Covered |
| 5 | B | Words in Context: negated atypicality | Partially covered; add WIC polarity trap |
| 6 | B | Words in Context: created/produced | Covered |
| 7 | A | Words in Context: phrase meaning, proponent of | Covered, but phrase-level WIC should be explicit |
| 8 | C | Words in Context: buttress/defend | Covered |
| 9 | C | Text Structure/Purpose: underlined sentence function | Covered |
| 10 | A | Supporting Detail: study method | Covered |
| 11 | A | Textual Evidence: weakens hypothesis through experimental outcome | Covered; add experimental-design architecture |
| 12 | B | Textual Evidence: quotation illustrates two-part claim | Covered |
| 13 | D | Quantitative Evidence: graph supports claim | Covered |
| 14 | C | Textual Evidence: supports hypothesis | Covered |
| 15 | C | Textual Evidence: quotation illustrates claim | Covered |
| 16 | A | Inference: logical completion from comparison | Covered |
| 17 | B | Inference: conclusion from genetic evidence | Covered |
| 18 | D | Inference: conclusion about control group design | Covered; add control-group architecture |
| 19 | C | SEC: plural nouns | Covered |
| 20 | A | SEC: no punctuation between preposition and complement | Partially covered; add explicit syntactic-unit punctuation rule |
| 21 | B | SEC: integrated relative clause | Covered |
| 22 | D | SEC: supplementary element punctuation | Covered |
| 23 | D | SEC: sentence boundary with period | Covered |
| 24 | A | SEC: finite/nonfinite verb form | Covered |
| 25 | B | SEC: subject-modifier placement | Covered |
| 26 | B | SEC: colon introducing explanation | Covered |
| 27 | A | Transition: chronology | Covered |
| 28 | A | Transition: alternative | Covered |
| 29 | C | Notes synthesis: explain advantage | Broadly covered; needs finer synthesis subtype |
| 30 | C | Notes synthesis: present theory to unfamiliar audience | Broadly covered; needs audience/theory subtype |
| 31 | A | Notes synthesis: emphasize relative heat | Broadly covered; needs emphasis subtype |
| 32 | A | Notes synthesis: introduce book to familiar audience | Broadly covered; needs audience subtype |
| 33 | B | Notes synthesis: emphasize similarity | Broadly covered; needs comparison subtype |

## Observed Module Distribution: PT5

PT5 uses the same 33-question nondigital-linear source format:

- PT5 Module 1: Q1-Q19 reading, Q20-Q26 SEC, Q27-Q30 transitions, Q31-Q33 notes synthesis
- PT5 Module 2: Q1-Q17 reading, Q18-Q25 SEC, Q26-Q29 transitions, Q30-Q33 notes synthesis

PT5 supports the later finding from PT10 that Reading/Craft/Information can extend through Q19 in Module 1 and that SEC can begin as early as Q18 in Module 2.

### PT5 Reading and Writing Module 1

| Q | Ans | Observed CB focus | Rules coverage |
|---:|:---:|---|---|
| 1 | A | Words in Context: trace/evidence left behind | Covered |
| 2 | B | Words in Context: fragile sculpture feature | Covered |
| 3 | B | Words in Context: impending solar flare | Covered |
| 4 | D | Words in Context: exploited magnetic-field tendency | Covered |
| 5 | B | Words in Context: ameliorate unrepresentative samples | Covered |
| 6 | D | Text Structure/Purpose: narrator explains why she might make team | Covered |
| 7 | B | Text Structure/Purpose: Spanish-language newspapers thrived in Texas/El Paso | Covered |
| 8 | C | Text Structure/Purpose: underlined sentence explains why Atacama is research site | Covered |
| 9 | B | Text Structure/Purpose: underlined concession about unlikely ridership transfer | Covered |
| 10 | B | Text Structure/Purpose: unresolved question, hypothesis, study design | Covered |
| 11 | D | Supporting Detail: scientists surprised by same marsquake location | Covered |
| 12 | A | Supporting Detail: Maya zero symbol | Covered |
| 13 | D | Textual Evidence: quotation illustrates banker's distress | Covered |
| 14 | B | Quantitative Evidence: extinct date creates habitat concern | Covered |
| 15 | C | Textual Evidence: quotation illustrates mixed feelings | Covered |
| 16 | B | Quantitative Evidence: graph supports coral-current conclusion | Covered |
| 17 | A | Inference: crater location supports Younger Dryas impact hypothesis | Covered |
| 18 | B | Inference: appendix repeatedly emerged and persisted in mammal lineages | Covered |
| 19 | A | Inference: Aztec ethics evaluates actions by societal role/community effect | Covered |
| 20 | C | SEC: singular event antecedent uses singular pronoun "this" | Covered; add event-reference pronoun pattern |
| 21 | A | SEC: finite verb required in main clause | Covered; add finite-main-clause pattern |
| 22 | D | SEC: subject-verb agreement with gerund subject | Covered |
| 23 | B | SEC: plural nouns | Covered |
| 24 | D | SEC: subject-verb agreement | Covered |
| 25 | B | SEC: no punctuation between title/role and proper name | Partially covered; supports title-name no-punctuation rule |
| 26 | B | SEC: punctuation between two supplementary elements | Covered |
| 27 | D | Transition: as a result | Covered |
| 28 | D | Transition: though marks concession | Covered |
| 29 | B | Transition: conversely marks contrast/opposite tendency | Covered; add converse subtype |
| 30 | D | Transition: hence consequence | Covered |
| 31 | A | Notes synthesis: identify real author behind pseudonym | Broadly covered; needs authorship/pseudonym subtype |
| 32 | C | Notes synthesis: explain mechanism for energy storage | Broadly covered; needs mechanism-explanation subtype |
| 33 | D | Notes synthesis: identify classification category | Broadly covered; needs category subtype |

### PT5 Reading and Writing Module 2

| Q | Ans | Observed CB focus | Rules coverage |
|---:|:---:|---|---|
| 1 | C | Words in Context: reaching across/stretching toward | Covered |
| 2 | D | Words in Context: obtain detailed fossil information | Covered |
| 3 | A | Words in Context: reduced brain-region communication | Covered |
| 4 | A | Words in Context: tenuous historical memory | Covered |
| 5 | C | Words in Context: defend interpretation despite limited evidence | Covered |
| 6 | C | Text Structure/Purpose: Harris's varying but self-favorable account | Covered |
| 7 | B | Text Structure/Purpose: underlined contrast motivates new explanation | Covered |
| 8 | A | Cross-Text: Text 2 challenges Text 1 argument about graphic novels | Covered |
| 9 | A | Central Detail: Lutie observes street activity at sunset | Covered |
| 10 | D | Supporting Detail: critics skeptical of biodiversity practicality | Covered |
| 11 | A | Central Ideas: fabula/syuzhet explained through film example | Covered |
| 12 | D | Quantitative Evidence: graph supports 2019 highest medicine/health submissions | Covered |
| 13 | D | Textual Evidence: quotation supports ecological-risk claim | Covered |
| 14 | D | Quantitative Evidence: moderate vs extreme climate-change compensation | Covered |
| 15 | D | Textual Evidence: quotation illustrates ambivalence toward poetry | Covered |
| 16 | B | Quantitative Evidence: table supports precipitation-event conclusion | Covered |
| 17 | A | Inference: Upland South dialect feature connected to Scottish settlement | Covered |
| 18 | A | SEC: finite verb required in main clause | Covered |
| 19 | B | SEC: no punctuation between subject and verb | Partially covered; supports internal-unit punctuation rule |
| 20 | A | SEC: pronoun-antecedent agreement | Covered |
| 21 | C | SEC: commas around supplementary appositive | Covered |
| 22 | B | SEC: comma before supplementary element after main clause | Covered |
| 23 | A | SEC: restrictive appositive no punctuation | Covered; supports restrictive appositive generation |
| 24 | C | SEC: subject-verb agreement | Covered |
| 25 | C | SEC: present participle supplementary phrase with paired commas | Covered |
| 26 | B | Transition: next step in process | Covered |
| 27 | C | Transition: later in chronology | Covered |
| 28 | D | Transition: for this reason result | Covered |
| 29 | D | Transition: accordingly result/consequence | Covered |
| 30 | A | Notes synthesis: identify publication year | Broadly covered; needs year/date subtype |
| 31 | D | Notes synthesis: emphasize mass/size relative to Sun | Broadly covered; needs measurement-emphasis subtype |
| 32 | D | Notes synthesis: contrast lever types | Broadly covered; needs structural-comparison subtype |
| 33 | A | Notes synthesis: emphasize similarity between wave types | Broadly covered; needs similarity subtype |

## Observed Module Distribution: PT6

PT6 confirms the same broad nondigital-linear architecture as PT4:

- Q1-Q18: Reading/Craft/Information
- Q19-Q25 or Q26: Standard English Conventions
- Q26-Q30 or Q27-Q29: transitions
- Final 3-4 questions: notes synthesis

The exact boundary can shift by module. PT6 Module 1 has SEC through Q25 and transitions Q26-Q30; PT6 Module 2 has SEC through Q26 and transitions Q27-Q29.

### PT6 Reading and Writing Module 1

| Q | Ans | Observed CB focus | Rules coverage |
|---:|:---:|---|---|
| 1 | D | Words in Context: phrase meaning/comparison | Covered; phrase-level WIC should be explicit |
| 2 | B | Words in Context: contrast signal and political explicitness | Covered |
| 3 | B | Words in Context: remedying a research imbalance | Covered |
| 4 | D | Words in Context: underlined word, archaic/literary usage | Covered; supports keeping underlined WIC ingestion |
| 5 | D | Words in Context: negated inconsequentiality | Partially covered; add WIC polarity trap |
| 6 | A | Text Structure/Purpose: underlined sentence elaborates transition | Covered |
| 7 | B | Text Structure/Purpose: main purpose from apparent contrast | Covered |
| 8 | B | Text Structure/Purpose: underlined literary portion explains vulnerability | Covered |
| 9 | D | Cross-Text: Text 2 concedes then qualifies/revises Text 1 | Covered; confirms qualified-disagreement response rule |
| 10 | D | Central Ideas: research method and finding | Covered |
| 11 | A | Quantitative Evidence: two-variable trend in table | Covered |
| 12 | A | Textual Evidence: quotation supports causal explanation | Covered |
| 13 | A | Textual Evidence: supports claim about diverse media | Covered |
| 14 | C | Quantitative Evidence: graph supports conclusion with timing constraint | Covered; highlights wrong-time data trap |
| 15 | B | Quantitative Evidence: graph completion using binned distribution | Covered; add binned-data pattern |
| 16 | D | Textual Evidence: supports molecular hypothesis | Covered |
| 17 | D | Inference: new evidence overturns prior speculation | Covered |
| 18 | B | Inference: applies theory to age-group purchase likelihood | Covered |
| 19 | A | SEC: nonfinite past participle as supplementary element | Covered |
| 20 | C | SEC: no punctuation between verb and object | Partially covered; add internal-unit punctuation rule |
| 21 | D | SEC: subject-verb agreement | Covered |
| 22 | D | SEC: end punctuation for indirect question | Covered, but add direct/indirect question contrast |
| 23 | D | SEC: subject-verb agreement | Covered |
| 24 | C | SEC: sentence boundary with modifying noun phrase after period | Covered |
| 25 | B | SEC: sentence boundary with because-clause sentence | Covered |
| 26 | D | Transition: alternative/substitution | Covered |
| 27 | D | Transition: present-time contrast with historical setup | Covered |
| 28 | C | Transition: on-the-other-hand contrast | Covered |
| 29 | C | Transition: addition | Covered |
| 30 | B | Transition: logical consequence/expected outcome | Covered; add "then" as inferential result |
| 31 | A | Notes synthesis: emphasize named person's achievement | Broadly covered; needs achievement subtype |
| 32 | B | Notes synthesis: emphasize similarity | Broadly covered; needs comparison subtype |
| 33 | C | Notes synthesis: make a generalization | Broadly covered; needs generalization subtype |

### PT6 Reading and Writing Module 2

| Q | Ans | Observed CB focus | Rules coverage |
|---:|:---:|---|---|
| 1 | C | Words in Context: display/location contrast | Covered |
| 2 | D | Words in Context: inspired by direct experience | Covered |
| 3 | C | Words in Context: skeptic position opposite deliberate finding | Covered; add opposition-to-claim WIC pattern |
| 4 | B | Words in Context: "manifest in" as apparent from evidence | Covered; phrase-level WIC should be explicit |
| 5 | B | Words in Context: tentative memorability contrast | Covered |
| 6 | C | Text Structure/Purpose: literary main purpose, determination | Covered |
| 7 | D | Text Structure/Purpose: experiment casts doubt on hypothesis | Covered; add experiment-overturns-hypothesis architecture |
| 8 | C | Text Structure/Purpose: underlined concession/limitation | Covered |
| 9 | C | Text Structure/Purpose: underlined conventional approach obscures diversity | Covered |
| 10 | C | Central Ideas: unexpected economic relationship and explanation | Covered |
| 11 | C | Supporting Detail/Inference: unchanged composition rules out alternative cause | Covered; add control-of-alternative-explanation pattern |
| 12 | C | Inference: conditional biosignature conclusion with exception | Covered |
| 13 | C | Quantitative Evidence: highest across all months in line graph | Covered |
| 14 | D | Textual Evidence: quotation illustrates contradictory feelings | Covered |
| 15 | D | Quantitative Evidence: table comparison across all measures | Covered |
| 16 | B | Textual Evidence: supports indirect-effect hypothesis | Covered; add mediation/indirect-effect architecture |
| 17 | A | Inference: limited logging may support conservation | Covered |
| 18 | D | Inference: cannot isolate effect of one creative condition | Covered |
| 19 | C | SEC: question mark for coordinated direct questions | Covered; add direct-question punctuation detail |
| 20 | A | SEC: subject-modifier placement | Covered |
| 21 | A | SEC: subject-modifier placement | Covered |
| 22 | C | SEC: semicolon joining main clauses | Covered |
| 23 | B | SEC: complex series punctuation | Covered |
| 24 | A | SEC: however plus colon introducing list | Covered |
| 25 | D | SEC: colon between main clauses when second explains first | Covered |
| 26 | B | SEC: subject-verb agreement | Covered |
| 27 | D | Transition: final step in process | Covered |
| 28 | A | Transition: "in turn" result/consequence | Covered; add causal-chain transition subtype |
| 29 | B | Transition: "in fact" emphasis/support | Covered; add emphasis transition subtype |
| 30 | C | Notes synthesis: emphasize similarity | Broadly covered; needs comparison subtype |
| 31 | D | Notes synthesis: contrast numbers of categories | Broadly covered; needs quantitative contrast subtype |
| 32 | B | Notes synthesis: emphasize a specific sample | Broadly covered; needs sample-emphasis subtype |
| 33 | C | Notes synthesis: indicate classification category | Broadly covered; needs category-identification subtype |

## Observed Module Distribution: PT7

PT7 confirms the same 33-question nondigital-linear source format but shows that late-module boundaries vary:

- PT7 Module 1: Q1-Q18 reading, Q19-Q26 SEC, Q27 transition, Q28-Q33 notes synthesis
- PT7 Module 2: Q1-Q18 reading, Q19-Q26 SEC, Q27-Q31 transitions, Q32-Q33 notes synthesis

This reinforces that paper-accommodation generation should use stats-driven position bands rather than a fixed "four transitions plus three notes" ending.

### PT7 Reading and Writing Module 1

| Q | Ans | Observed CB focus | Rules coverage |
|---:|:---:|---|---|
| 1 | A | Words in Context: scientific theory confirmed by observation | Covered |
| 2 | D | Words in Context: underlined common word in literary context | Covered |
| 3 | B | Words in Context: remedying lack of services | Covered |
| 4 | B | Words in Context: corroborate real-world conclusions | Covered |
| 5 | A | Words in Context: demarcated from comparison class | Covered |
| 6 | A | Text Structure/Purpose: underlined portion shows comfort beyond warmth | Covered |
| 7 | A | Text Structure/Purpose: parenthetical definition clarifies term | Covered; add parenthetical-definition function pattern |
| 8 | C | Text Structure/Purpose: poetic image grounds metaphorical thought | Covered |
| 9 | A | Text Structure/Purpose: warning against displacement predictions | Covered |
| 10 | A | Inference: site likely used only for reproduction | Covered |
| 11 | D | Supporting Detail/Inference: ordinary subject, important historical moment | Covered |
| 12 | D | Supporting Detail: exact percentage from interview data | Covered; add exact-value lookup pattern |
| 13 | A | Textual Evidence: quotation supports claim about preserving constitutions | Covered |
| 14 | B | Textual Evidence: supports conclusion about lighting changing time references | Covered |
| 15 | A | Quantitative Evidence: graph supports proposal about ULE factors | Covered |
| 16 | B | Quantitative Evidence: graph supports limited-capital explanation over time | Covered |
| 17 | C | Inference: researcher's reasoning about narwhal tusks | Covered |
| 18 | D | Quantitative Evidence/Inferences: lower creep rate from treatment supports durability | Covered |
| 19 | A | SEC: subject-verb agreement with singular subject | Covered |
| 20 | D | SEC: determiner agreement | Covered |
| 21 | D | SEC: past-tense consistency | Covered |
| 22 | C | SEC: comma plus coordinating conjunction joins main clauses | Covered |
| 23 | C | SEC: nonfinite past participle in supplementary element | Covered |
| 24 | A | SEC: sentence boundary with period | Covered |
| 25 | D | SEC: subject-modifier placement | Covered |
| 26 | D | SEC: comma before supplementary element | Covered |
| 27 | A | Transition: additional function | Covered |
| 28 | D | Notes synthesis: identify type of scientist | Broadly covered; needs profession/type subtype |
| 29 | A | Notes synthesis: indicate setting of a story | Broadly covered; needs setting subtype |
| 30 | C | Notes synthesis: contrast two styles | Broadly covered; needs comparison subtype |
| 31 | B | Notes synthesis: contrast two songs | Broadly covered; needs comparison subtype |
| 32 | C | Notes synthesis: use quotation to challenge explanation | Broadly covered; needs quote-challenge subtype |
| 33 | D | Notes synthesis: present overview of study findings | Broadly covered; needs study-overview subtype |

### PT7 Reading and Writing Module 2

| Q | Ans | Observed CB focus | Rules coverage |
|---:|:---:|---|---|
| 1 | C | Words in Context: popularize technology | Covered |
| 2 | D | Words in Context: influenced by surroundings | Covered |
| 3 | C | Words in Context: successful conservation goal | Covered |
| 4 | D | Words in Context: oddity based on duration | Covered |
| 5 | B | Words in Context: esteem/high regard | Covered |
| 6 | A | Text Structure/Purpose: ocean-floor theory setup | Covered |
| 7 | B | Text Structure/Purpose: historical reason for advertiser reluctance | Covered |
| 8 | B | Text Structure/Purpose: sentence supports scale/novelty of tapestry | Covered |
| 9 | D | Cross-Text: Text 2 responds to researchers in Text 1 | Covered |
| 10 | B | Supporting Detail: useful feature of rubber tree | Covered |
| 11 | B | Central Ideas: nature-based conservation approaches | Covered |
| 12 | D | Quantitative Evidence: table supports shaded-shelter claim | Covered |
| 13 | C | Quantitative Evidence: exact area value from table | Covered; add exact-value lookup pattern |
| 14 | C | Textual Evidence: quotation illustrates delicate-but-durable sculptures | Covered |
| 15 | D | Textual Evidence: finding supports tectonic transition conclusion | Covered |
| 16 | D | Inference: language-family origin and similarities | Covered |
| 17 | B | Inference: Mars sediment source from water-deposition evidence | Covered |
| 18 | B | Quantitative Evidence/Inferences: coin metal percentages change over time | Covered |
| 19 | D | SEC: to-infinitive subordinate clause | Covered |
| 20 | D | SEC: past-tense consistency | Covered |
| 21 | C | SEC: no punctuation between subject and verb | Partially covered; strengthens internal-unit punctuation gap |
| 22 | C | SEC: pronoun-antecedent agreement | Covered |
| 23 | C | SEC: complex series punctuation | Covered |
| 24 | A | SEC: supplementary "though" punctuation | Covered |
| 25 | B | SEC: semicolon plus supplementary adverb "though" | Covered |
| 26 | D | SEC: semicolon joining main clauses | Covered |
| 27 | B | Transition: result/consequence | Covered |
| 28 | D | Transition: specific elaboration | Covered |
| 29 | A | Transition: particular elaboration | Covered |
| 30 | D | Transition: goal-to-action relationship | Covered; add purpose/action transition subtype |
| 31 | C | Transition: more-often difference between old and new routes | Covered; add frequency/difference subtype |
| 32 | A | Notes synthesis: identify title of award-winning novel | Broadly covered; needs title subtype |
| 33 | C | Notes synthesis: identify completion year | Broadly covered; needs year/date subtype |

## Observed Module Distribution: PT8

PT8 uses the 33-question nondigital-linear source format:

- PT8 Module 1: Q1-Q18 reading, Q19-Q26 SEC, Q27-Q29 transitions, Q30-Q33 notes synthesis
- PT8 Module 2: Q1-Q18 reading, Q19-Q26 SEC, Q27-Q31 transitions, Q32-Q33 notes synthesis

PT8 reinforces that the number of transition items can vary significantly by module, from three in Module 1 to five in Module 2.

### PT8 Reading and Writing Module 1

| Q | Ans | Observed CB focus | Rules coverage |
|---:|:---:|---|---|
| 1 | B | Words in Context: important historical figure | Covered |
| 2 | D | Words in Context: substantial effect | Covered |
| 3 | A | Words in Context: tranquil/calm environment | Covered |
| 4 | C | Words in Context: collaboration between writers | Covered |
| 5 | C | Words in Context: extensive contributions | Covered |
| 6 | C | Text Structure/Purpose: present recent archaeological discovery | Covered |
| 7 | D | Text Structure/Purpose: depict setting while awaiting visitor | Covered |
| 8 | A | Text Structure/Purpose: letter delivery then joy | Covered |
| 9 | A | Text Structure/Purpose: labor-bargaining example | Covered |
| 10 | D | Supporting Detail: fossil discovery expanded geographic evidence | Covered |
| 11 | B | Quantitative Evidence: table percent availability by release period | Covered |
| 12 | C | Quantitative Evidence: exact depth range from table | Covered |
| 13 | A | Quantitative Evidence: highest housing starts month | Covered |
| 14 | A | Textual Evidence: supports ethnographic-value claim | Covered |
| 15 | D | Textual Evidence: supports predator-prey cascading hypothesis | Covered |
| 16 | C | Textual Evidence: supports plant dependence on rock dissolution | Covered |
| 17 | A | Inference: receptor-targeting could reduce need for new repellents | Covered |
| 18 | D | Inference: tanager feather color not always honest signal | Covered |
| 19 | C | SEC: subject-verb agreement | Covered |
| 20 | B | SEC: modal "would" plus nonfinite plain-form verb | Covered; add modal-plain-form pattern |
| 21 | B | SEC: coordinated restrictive appositive no punctuation | Covered; add coordinated appositive variant |
| 22 | A | SEC: comma plus colon around supplementary "though" | Covered |
| 23 | D | SEC: subject-verb agreement | Covered |
| 24 | C | SEC: however plus semicolon | Covered |
| 25 | C | SEC: nonfinite participle inside supplementary element | Covered |
| 26 | D | SEC: subject-modifier placement | Covered |
| 27 | A | Transition: still signals contrast with expectation | Covered |
| 28 | B | Transition: specifically elaborates general influence claim | Covered |
| 29 | C | Transition: indeed gives emphasis/support | Covered |
| 30 | A | Notes synthesis: emphasize distance covered | Broadly covered; needs distance subtype |
| 31 | C | Notes synthesis: emphasize aim of research study | Broadly covered; needs aim-of-study subtype |
| 32 | A | Notes synthesis: emphasize aim of research study | Broadly covered; needs aim-of-study subtype |
| 33 | D | Notes synthesis: generalize statistical authorship study | Broadly covered; needs statistical-study subtype |

### PT8 Reading and Writing Module 2

| Q | Ans | Observed CB focus | Rules coverage |
|---:|:---:|---|---|
| 1 | B | Words in Context: attractive colors | Covered |
| 2 | A | Words in Context: preventable biodiversity loss | Covered |
| 3 | B | Words in Context: inadequate mechanical recycling | Covered |
| 4 | D | Words in Context: intricate crop relations | Covered |
| 5 | D | Words in Context: latent/functionless accessory spleen | Covered |
| 6 | A | Text Structure/Purpose: von Ahn work led to reCAPTCHA | Covered |
| 7 | C | Text Structure/Purpose: personified nighttime description | Covered |
| 8 | A | Text Structure/Purpose: play staged for private amusement | Covered |
| 9 | A | Cross-Text: Text 2 challenges conventional wisdom in Text 1 | Covered |
| 10 | D | Supporting Detail: narrator and Mario played license-plate games | Covered |
| 11 | B | Supporting Detail: Wagner achieved volume with more musicians | Covered |
| 12 | C | Supporting Detail: difrasismo has formal and ritual functions | Covered |
| 13 | D | Central Ideas: invisible-hand metaphor interpretation is uncertain | Covered |
| 14 | B | Quantitative Evidence: different rates, similar information conveyed | Covered |
| 15 | C | Quantitative Evidence: method affects dinosaur bite-force estimates | Covered |
| 16 | A | Textual Evidence: supports awe and altruism claim | Covered |
| 17 | C | Inference: sweet potato evidence supports pre-European contact | Covered |
| 18 | D | Inference: sea star body plan suggests mostly head-like body | Covered |
| 19 | A | SEC: finite verb required in main clause | Covered |
| 20 | B | SEC: past perfect for earlier completed membership doubling | Covered |
| 21 | C | SEC: period between sentences | Covered |
| 22 | A | SEC: finite main-clause verb | Covered |
| 23 | C | SEC: paired dashes around supplementary element | Covered |
| 24 | A | SEC: colon introduces description | Covered |
| 25 | B | SEC: complex series punctuation | Covered |
| 26 | A | SEC: though plus semicolon between main clauses | Covered |
| 27 | A | Transition: in fact emphasis/support | Covered |
| 28 | A | Transition: currently marks present continuation | Covered; add present-continuation subtype |
| 29 | C | Transition: by contrast | Covered |
| 30 | B | Transition: on the contrary refutes assumption | Covered; add refutation subtype |
| 31 | D | Transition: as such logical consequence | Covered; add as-such consequence subtype |
| 32 | B | Notes synthesis: explain advantage of infilling | Broadly covered; needs technique-advantage subtype |
| 33 | D | Notes synthesis: misconception in place naming | Broadly covered; needs misconception-cause subtype |

## Observed Module Distribution: PT9

PT9 again uses the 33-question nondigital-linear source format:

- PT9 Module 1: Q1-Q18 reading, Q19-Q26 SEC, Q27-Q30 transitions, Q31-Q33 notes synthesis
- PT9 Module 2: Q1-Q18 reading, Q19-Q26 SEC, Q27-Q28 transitions, Q29-Q33 notes synthesis

This strengthens the recommendation to use paper-format stats snapshots for position-band generation rather than a single hard-coded ending pattern.

### PT9 Reading and Writing Module 1

| Q | Ans | Observed CB focus | Rules coverage |
|---:|:---:|---|---|
| 1 | A | Words in Context: underlined word in historical prose | Covered |
| 2 | D | Words in Context: consistent/steady over time | Covered |
| 3 | C | Words in Context: interpret opaque poems | Covered |
| 4 | C | Words in Context: confined to as restricted to | Covered |
| 5 | B | Words in Context: impenetrable field barrier | Covered |
| 6 | C | Text Structure/Purpose: underlined sentence establishes contrast | Covered |
| 7 | A | Text Structure/Purpose: adaptation method detail | Covered |
| 8 | A | Text Structure/Purpose: underlined portion qualifies weak effects as still worth pursuing | Covered |
| 9 | C | Cross-Text: Text 2 researchers respond to Text 1 finding | Covered |
| 10 | A | Supporting Detail: directly stated reason for concern | Covered |
| 11 | D | Quantitative/Detail: exact table value by ID | Covered; add exact-value lookup variant |
| 12 | C | Quantitative Evidence: table completion under constraints | Covered |
| 13 | D | Quantitative Evidence: graph supports hypothesis about metal uptake | Covered |
| 14 | C | Quantitative Evidence: table comparison across species and sleep states | Covered |
| 15 | A | Quantitative Evidence: graph supports conclusion about hive structure | Covered |
| 16 | D | Textual Evidence: finding supports strategic sales claim | Covered |
| 17 | B | Inference: judicial citation argument about philosophers | Covered |
| 18 | A | Inference: veterans overrepresented in civilian government jobs | Covered |
| 19 | A | SEC: finite verb required in relative clause | Covered; add finite-relative-clause generation pattern |
| 20 | A | SEC: subject-verb agreement | Covered |
| 21 | B | SEC: pronoun-antecedent agreement | Covered |
| 22 | C | SEC: supplementary adverb between main clause and supplementary phrase | Covered |
| 23 | C | SEC: no punctuation between title and proper noun/name | Partially covered; add title-name no-punctuation case |
| 24 | C | SEC: colon introduces elaborating main clause | Covered |
| 25 | A | SEC: nonfinite present participle restrictive phrase | Covered; add restrictive participial phrase pattern |
| 26 | B | SEC: subject-verb agreement | Covered |
| 27 | A | Transition: meanwhile signals simultaneous actions | Covered; add simultaneity subtype |
| 28 | B | Transition: additionally adds a second concern | Covered |
| 29 | D | Transition: thus signals consequence | Covered |
| 30 | B | Transition: by contrast | Covered |
| 31 | B | Notes synthesis: explain advantage of microprobes | Broadly covered; needs advantage subtype |
| 32 | A | Notes synthesis: emphasize significance of discovery | Broadly covered; needs significance subtype |
| 33 | C | Notes synthesis: introduce poetry collection | Broadly covered; needs title/publication subtype |

### PT9 Reading and Writing Module 2

| Q | Ans | Observed CB focus | Rules coverage |
|---:|:---:|---|---|
| 1 | B | Words in Context: completing/finishing task | Covered |
| 2 | C | Words in Context: provide prey | Covered |
| 3 | B | Words in Context: enthusiasm for two art forms | Covered |
| 4 | B | Words in Context: handmade from materials | Covered |
| 5 | C | Words in Context: persistent public-health work | Covered |
| 6 | D | Text Structure/Purpose: oral histories advantage and example | Covered |
| 7 | D | Text Structure/Purpose: poem encourages child toward future | Covered |
| 8 | D | Text Structure/Purpose: setting reflects character's mood | Covered |
| 9 | A | Text Structure/Purpose: category used to introduce speculation | Covered |
| 10 | A | Supporting Detail: Gloria Richardson's leadership | Covered |
| 11 | D | Supporting Detail: Elinor's maturity | Covered |
| 12 | A | Central Ideas: influential cookbook and contemporary impact | Covered |
| 13 | D | Supporting Detail: acquaintances avoid frank comments | Covered |
| 14 | C | Textual Evidence: quotation illustrates concern for home | Covered |
| 15 | C | Textual Evidence: weakens eelgrass genetic-diversity hypothesis | Covered |
| 16 | D | Textual Evidence: supports folklore-origin argument | Covered |
| 17 | B | Inference: face attraction linked to species traits | Covered |
| 18 | D | Inference: aptamer specificity for pathogen testing | Covered |
| 19 | C | SEC: possessive determiner agreement | Covered |
| 20 | D | SEC: to-infinitive explains reason | Covered |
| 21 | C | SEC: plural verb agrees with plural subject | Covered |
| 22 | C | SEC: no punctuation between subject and verb | Partially covered; strengthens internal-unit punctuation gap |
| 23 | B | SEC: semicolon plus introductory phrase comma | Covered |
| 24 | D | SEC: restrictive appositive no punctuation | Partially covered; add restrictive appositive punctuation case |
| 25 | C | SEC: nonfinite past participle supplementary element | Covered |
| 26 | C | SEC: though plus semicolon between main clauses | Covered |
| 27 | C | Transition: similarly links comparable activities | Covered; add similarity subtype |
| 28 | A | Transition: specifically elaborates mechanism | Covered |
| 29 | B | Notes synthesis: compare lengths of rail tunnels | Broadly covered; needs length-comparison subtype |
| 30 | C | Notes synthesis: emphasize fossil significance | Broadly covered; needs significance subtype |
| 31 | D | Notes synthesis: contrast quantitative emissivity values | Broadly covered; needs quantitative-contrast subtype |
| 32 | C | Notes synthesis: explain advantage of format | Broadly covered; needs format-advantage subtype |
| 33 | B | Notes synthesis: present study and methodology | Broadly covered; needs methodology subtype |

## Observed Module Distribution: PT10

PT10 again uses the 33-question nondigital-linear source format, but its domain boundary differs from prior tests:

- PT10 Module 1: Q1-Q19 reading, Q20-Q27 SEC, Q28-Q30 transitions, Q31-Q33 notes synthesis
- PT10 Module 2: Q1-Q17 reading, Q18-Q25 SEC, Q26-Q30 transitions, Q31-Q33 notes synthesis

This is the strongest evidence so far that the paper-accommodation scheduler should not hard-code "Q1-Q18 reading, Q19-Q26 SEC." It should use a stats snapshot with tolerances by module and route.

### PT10 Reading and Writing Module 1

| Q | Ans | Observed CB focus | Rules coverage |
|---:|:---:|---|---|
| 1 | A | Words in Context: source of information | Covered |
| 2 | B | Words in Context: observant artist | Covered |
| 3 | B | Words in Context: speculates without firm evidence | Covered |
| 4 | A | Words in Context: synchronization/same-time flowering | Covered |
| 5 | C | Words in Context: exhaustive account blocked by destroyed evidence | Covered |
| 6 | B | Text Structure/Purpose: development of a dance form | Covered |
| 7 | D | Text Structure/Purpose: obstacle then method/solution | Covered |
| 8 | D | Text Structure/Purpose: imaginative action reveals desire | Covered |
| 9 | C | Text Structure/Purpose: problem/uncertainty after known belief | Covered |
| 10 | C | Cross-Text: Text 2 challenges Text 1 conclusion | Covered |
| 11 | C | Supporting Detail: narrator's mixed feelings | Covered |
| 12 | B | Supporting Detail: Dorian's reaction to portrait | Covered |
| 13 | A | Central Detail: artist transforms punching bags | Covered |
| 14 | A | Textual Evidence: quotation illustrates emotional connection to nature | Covered |
| 15 | A | Textual Evidence: supports claim about editor's goal | Covered |
| 16 | A | Textual Evidence: chemical bone evidence supports settlement-distance conclusion | Covered |
| 17 | C | Quantitative Evidence: graph completes gene/pathogen conclusion | Covered |
| 18 | D | Inference: engineered DNA could target weed without harming nearby plants | Covered |
| 19 | C | Inference/experimental mechanism: ELF3 replacement and flowering at high temperature | Covered; add mechanism-test architecture |
| 20 | B | SEC: comma plus coordinating conjunction joins main clauses | Covered |
| 21 | A | SEC: comma plus coordinating conjunction joins independent clauses | Covered |
| 22 | C | SEC: nonfinite present participle supplementary phrase | Covered |
| 23 | C | SEC: comma between subordinate and main clause | Covered |
| 24 | C | SEC: literary present tense | Covered; add literary-present tense pattern |
| 25 | C | SEC: colon introduces explanation | Covered |
| 26 | C | SEC: possessive determiner agreement | Covered |
| 27 | A | SEC: subject-verb agreement with "each one" head noun | Covered |
| 28 | B | Transition: for example | Covered |
| 29 | B | Transition: previously gives chronological perspective | Covered |
| 30 | B | Transition: hence logical conclusion | Covered |
| 31 | B | Notes synthesis: present study and conclusions | Broadly covered; needs study-conclusion subtype |
| 32 | C | Notes synthesis: emphasize difference between portraits | Broadly covered; needs comparison subtype |
| 33 | C | Notes synthesis: emphasize both duration and purpose of work | Broadly covered; needs duration-purpose subtype |

### PT10 Reading and Writing Module 2

| Q | Ans | Observed CB focus | Rules coverage |
|---:|:---:|---|---|
| 1 | A | Words in Context: widespread script adoption | Covered |
| 2 | A | Words in Context: involuntary diaphragm contractions | Covered |
| 3 | D | Words in Context: peripheral location | Covered |
| 4 | A | Words in Context: implications for nonrecipients | Covered |
| 5 | A | Words in Context: sanguine/optimistic | Covered |
| 6 | D | Text Structure/Purpose: character's long-desired trip | Covered |
| 7 | B | Text Structure/Purpose: character wants visitor to leave | Covered |
| 8 | B | Text Structure/Purpose: waves as relentless/enduring force | Covered |
| 9 | D | Central Ideas: disorienting apartment building designed to affect residents | Covered |
| 10 | D | Supporting Detail: Lord Chancellor asks what crowd wants | Covered |
| 11 | D | Quantitative Evidence: highest biomass in graph | Covered |
| 12 | A | Quantitative Evidence: table supports Neanderthal shell-harvesting conclusion | Covered |
| 13 | B | Quantitative Evidence: graph supports solar-cell coating conclusion | Covered |
| 14 | A | Quantitative Evidence: table completes employment-sector comparison | Covered |
| 15 | D | Textual Evidence: finding supports inconsistency with linguistic niche hypothesis | Covered |
| 16 | A | Inference: tomb evidence suggests Queen Merneith may have been pharaoh | Covered |
| 17 | A | Inference: study design cannot distinguish simpler vs harder task outcomes | Covered |
| 18 | A | SEC: pronoun-antecedent agreement | Covered |
| 19 | D | SEC: question mark for direct question | Covered |
| 20 | B | SEC: present-tense consistency in process description | Covered |
| 21 | D | SEC: present tense with "today" | Covered |
| 22 | C | SEC: subject-verb agreement | Covered |
| 23 | A | SEC: colon introduces series of goals | Covered |
| 24 | D | SEC: subject-verb agreement | Covered |
| 25 | A | SEC: colon introduces explanation | Covered |
| 26 | A | Transition: for instance | Covered |
| 27 | B | Transition: next step in experiment | Covered |
| 28 | D | Transition: specifically elaborates argument | Covered |
| 29 | A | Transition: fittingly signals appropriateness | Covered; add appropriateness subtype |
| 30 | D | Transition: increasingly marks change over time | Covered; add trend/change subtype |
| 31 | D | Notes synthesis: both-books thematic similarity | Broadly covered; needs both-similarity subtype |
| 32 | A | Notes synthesis: while contrasts word origins | Broadly covered; needs contrast-origins subtype |
| 33 | C | Notes synthesis: emphasize similarity in large sizes | Broadly covered; needs size-similarity subtype |

## Observed Module Distribution: PT11

PT11 is a 2025 nondigital-linear source and preserves the 33-question module format:

- PT11 Module 1: Q1-Q18 reading, Q19-Q25 SEC, Q26-Q29 transitions, Q30-Q33 notes synthesis
- PT11 Module 2: Q1-Q18 reading, Q19-Q26 SEC, Q27-Q30 transitions, Q31-Q33 notes synthesis

PT11 confirms the paper-format variation already observed: the SEC block can contain seven or eight items, and notes synthesis can begin as early as Q30.

### PT11 Reading and Writing Module 1

| Q | Ans | Observed CB focus | Rules coverage |
|---:|:---:|---|---|
| 1 | A | Words in Context: comprehend dense poetry | Covered |
| 2 | C | Words in Context: interconnected irrigation system | Covered |
| 3 | D | Words in Context: suppress public access to novel | Covered |
| 4 | D | Words in Context: contradicted long-held view | Covered |
| 5 | A | Words in Context: unassuming appearance vs complex work | Covered |
| 6 | B | Text Structure/Purpose: sentence extends footsteps-as-message idea | Covered |
| 7 | B | Text Structure/Purpose: relationship strengthened by flexibility | Covered |
| 8 | D | Text Structure/Purpose: comparable waking visual tracking supports conclusion | Covered |
| 9 | D | Cross-Text: Text 2 critics qualify Text 1 explanation for backlash | Covered |
| 10 | C | Inference: entrepreneurship training may increase young-adult startups | Covered |
| 11 | B | Central Ideas: notable first observation of seal spitting | Covered |
| 12 | D | Supporting Detail: Schmidt's dramatic reaction to art comment | Covered |
| 13 | A | Supporting Detail: distinguished appearance despite mediocre achievements | Covered |
| 14 | D | Central Ideas: spike-wave study differs from traveling-wave research | Covered |
| 15 | B | Quantitative Evidence: highest energy-density fuel in graph | Covered |
| 16 | A | Textual Evidence: quotation illustrates carpa-theater influence | Covered |
| 17 | D | Inference: poor lighting deters new cyclists, not experienced cyclists | Covered |
| 18 | D | Inference: bumblebee evidence may not generalize to all wild bees | Covered; add overgeneralization-from-studied-subgroup pattern |
| 19 | D | SEC: period for declarative sentence ending in indirect question | Covered |
| 20 | D | SEC: past perfect for action completed before later date | Covered |
| 21 | A | SEC: current present tense with "currently" | Covered |
| 22 | B | SEC: commas around supplementary element | Covered |
| 23 | B | SEC: subject-modifier placement after multiple modifiers | Covered |
| 24 | A | SEC: subject-verb agreement | Covered |
| 25 | D | SEC: comma-plus-dash around interrupting supplementary element | Covered |
| 26 | D | Transition: as a result | Covered |
| 27 | D | Transition: consequently | Covered |
| 28 | A | Transition: by contrast | Covered |
| 29 | A | Transition: though signals exception | Covered; add exception subtype |
| 30 | C | Notes synthesis: indicate duration of musical piece | Broadly covered; needs duration subtype |
| 31 | A | Notes synthesis: historical overview of expedition | Broadly covered; needs historical-overview subtype |
| 32 | D | Notes synthesis: contrast poetic meters | Broadly covered; needs meter-contrast subtype |
| 33 | B | Notes synthesis: place document in context of changing beliefs | Broadly covered; needs context-of-change subtype |

### PT11 Reading and Writing Module 2

| Q | Ans | Observed CB focus | Rules coverage |
|---:|:---:|---|---|
| 1 | C | Words in Context: effective farming method | Covered |
| 2 | C | Words in Context: relying on astronauts | Covered |
| 3 | C | Words in Context: neglect overlooked factor | Covered |
| 4 | D | Words in Context: integral contribution | Covered |
| 5 | B | Words in Context: manifest/perceptible light | Covered |
| 6 | B | Text Structure/Purpose: parenthetical definition of microfilm | Covered |
| 7 | B | Text Structure/Purpose: eradication, consequences, reintroduction | Covered |
| 8 | A | Text Structure/Purpose: finding then broader challenge to uniqueness | Covered |
| 9 | B | Text Structure/Purpose: explain energy technology operation | Covered |
| 10 | C | Central Ideas: Asawa's art education and community focus | Covered |
| 11 | B | Quantitative Evidence: largest city population in graph | Covered |
| 12 | D | Quantitative Evidence: graph supports children draw mammals more often | Covered |
| 13 | C | Quantitative Evidence: veteran representation declined in both houses | Covered |
| 14 | B | Textual Evidence: quotation illustrates personal-experience stories | Covered |
| 15 | C | Textual Evidence: supports claim that olms regularly surface for food | Covered |
| 16 | C | Textual Evidence: supports dynamic/ephemeral ikaah representation claim | Covered |
| 17 | A | Inference: climbers exaggerated edelweiss difficulty for status | Covered |
| 18 | A | Inference: Titan models require assumed methane values | Covered |
| 19 | B | SEC: period for declarative sentence ending in relative-clause indirect question | Covered |
| 20 | B | SEC: to-infinitive expressing how software facilitates map creation | Covered |
| 21 | B | SEC: no punctuation between verb and complement | Partially covered; strengthens internal-unit punctuation gap |
| 22 | B | SEC: paired dashes around supplementary element | Covered |
| 23 | B | SEC: commas around "for instance" supplementary element | Covered |
| 24 | B | SEC: subject-modifier placement | Covered |
| 25 | A | SEC: subject-modifier placement | Covered |
| 26 | B | SEC: present participle supplementary element | Covered |
| 27 | D | Transition: finally in process sequence | Covered |
| 28 | B | Transition: instead contradicts initial hypothesis | Covered |
| 29 | C | Transition: indeed adds emphasis/support | Covered |
| 30 | B | Transition: ultimately signals final realization | Covered; add final-realization subtype |
| 31 | C | Notes synthesis: present study methods | Broadly covered; needs methods subtype |
| 32 | A | Notes synthesis: emphasize similarity in ages | Broadly covered; needs age-similarity subtype |
| 33 | A | Notes synthesis: compare two hypotheses by scope | Broadly covered; needs scope-comparison subtype |

## Coverage Audit Against Current Rules

| College Board pattern | Current coverage | Assessment |
|---|---|---|
| Correct answer must be required by text, not merely plausible | `rules_core_generation.md` evidence-before-invention; reading inference and evidence rules | Strong |
| Wrong answers are tempting for one reason and wrong for one reason | Core distractor engineering and option fields | Strong |
| Words in Context uses local and distributed context clues | Reading WIC rules and three-level wrong-answer distinction | Strong, with polarity gap |
| WIC phrase-level choices, not only single words | Stem wording allows "word or phrase" | Covered, but should be made explicit in generation |
| WIC negation/polarity traps | Grammar has `negation`; reading WIC lacks explicit polarity trap | Gap |
| Underlined WIC in literary or older prose | `underlined_word_meaning` exists; generation defaults to blanks | Covered for ingestion; use sparingly in generation |
| Main purpose and structure use rhetorical action and sequence | Text Structure/Purpose rules | Strong |
| Sentence-function questions ask what a sentence or underlined portion does in the whole text | Sentence-function evidence-span rules | Strong; explicitly mention underlined portions, not only sentences |
| Purpose/function items may identify concessions, limitations, conventional approaches, or detail elaboration | Text Structure/Purpose and `author_stance`/`structural_pattern` | Strong, but add named rhetorical-move examples |
| Parenthetical definitions can be tested as sentence/phrase function | `sentence_function` and rhetorical classification | Covered; add generation pattern |
| Cross-text response item is disagreement-oriented | Reading critical cross-text rule | Strong; PT4 confirms it |
| Cross-text response may concede a point but reject the proposed action | `confirmation_with_qualification` | Strong; PT6 confirms this as official |
| Quantitative items require exact data and correct comparison | Quantitative CoE rules require table/graph data and evidence values | Strong |
| Quantitative items may ask for exact table lookup, not just synthesis | `supporting_detail` or `data_completes_example` depending stem | Covered, but generation should include exact-value variants |
| Quantitative wrong answers may be true data with wrong relation | `data_context_mismatch`, `data_comparison`, distractor rules | Strong |
| Quantitative items may use binned distributions or timing constraints | General graph/table handling | Partial; add binned-data and wrong-time traps |
| Quantitative support can involve constraints, thresholds, or row selection by ID | General quantitative rules | Partial; add constrained-lookup pattern |
| Evidence items may test experimental mechanism by manipulating one component | `science_hypothesis_method_result` and CoE/Inferences | Partial; add mechanism-test architecture |
| Evidence from a studied subgroup may not generalize to a broader group | `scope_extension`, `overreach` | Covered; add studied-subgroup overgeneralization generation pattern |
| Support/weaken hypothesis questions require matching exact variables | CoE textual support/weakener rules | Strong |
| Experimental/control-group logic | General support, weaken, inference, and `science_hypothesis_method_result` architecture | Partial; add explicit architecture |
| Indirect-effect or mediation hypotheses | General CoE textual support | Partial; add mediation architecture |
| Alternative-cause control logic | General inference/evidence rules | Partial; add ruled-out-alternative pattern |
| Quote-illustration questions | `evidence_illustrates_claim`, `choose_best_illustration` | Strong |
| Literary quote questions may require satisfying two claim elements | `partial_match` trap | Covered |
| Inference explanations reject overreach and unsupported alternatives | Inference rules | Strong |
| Grammar explanations name the exact convention | Grammar module explanation requirements | Strong |
| Sentence boundary, semicolon, colon, comma splice, run-on | Grammar role/focus keys and examples | Strong |
| Modifier placement/dangling modifier | Grammar modifier rules | Strong |
| Relative clauses, finite/nonfinite verbs, tense | Grammar module | Strong |
| Direct vs indirect question punctuation | `punctuation_comma` / sentence punctuation broad handling | Partial; add explicit question-punctuation rule |
| No punctuation between syntactically bound elements | General punctuation only | Gap; PT4 and PT6 both show this |
| No punctuation between title/role noun and proper name | General punctuation/appositive handling | Partial; add title-name no-punctuation pattern |
| Restrictive appositive no punctuation | `appositive_punctuation` | Covered, but generation should include restrictive appositive cases |
| Finite verb required in relative clause | `verb_form`, `relative_pronouns` | Covered; add explicit finite-relative-clause pattern |
| Finite verb required in main clause | `verb_form` | Covered; add finite-main-clause generation pattern |
| Modal auxiliary requires plain-form verb | `verb_form` | Covered; add modal-plain-form generation pattern |
| Singular pronoun referring to an event or whole clause | `pronoun_antecedent_agreement` / pronoun clarity | Covered; add event-reference pronoun pattern |
| Literary present tense for discussing novels | `verb_tense_consistency` | Covered; add literary-present generation note |
| Determiner agreement | `determiners_articles` | Covered |
| Pronoun-antecedent agreement | `pronoun_antecedent_agreement` | Covered |
| Transitions classify logical relationship explicitly | `transition_logic`, transition distractor rules | Strong |
| Transition emphasis relation: "in fact" | `transition_logic` | Covered, but add emphasis subtype |
| Transition causal-chain relation: "in turn" | `transition_logic` | Covered, but add causal-chain subtype |
| Transition purpose/action relation: "to that end" | `transition_logic` | Covered, but add purpose-action subtype |
| Transition specificity/elaboration: "specifically" and "in particular" | `transition_logic` | Covered, but add specificity subtype |
| Transition simultaneity: "meanwhile" | `transition_logic` | Covered, but add simultaneity subtype |
| Transition similarity: "similarly" | `transition_logic` | Covered, but add similarity subtype |
| Transition appropriateness: "fittingly" | `transition_logic` | Covered, but add appropriateness subtype |
| Transition trend/change over time: "increasingly" | `transition_logic` | Covered, but add change-over-time subtype |
| Transition exception: "though" | `transition_logic` | Covered, but add exception subtype |
| Transition final realization: "ultimately" | `transition_logic` | Covered, but add final-realization subtype |
| Transition converse/opposite tendency: "conversely" | `transition_logic` | Covered, but add converse subtype |
| Transition present continuation: "currently" | `transition_logic` | Covered, but add present-continuation subtype |
| Transition refutation: "on the contrary" | `transition_logic` | Covered, but add refutation subtype |
| Transition logical consequence: "as such" | `transition_logic` | Covered, but add consequence subtype |
| Notes synthesis filters by rhetorical goal and audience | Broad Expression of Ideas handling | Partial; needs official-style subtype controls |
| Official paper-accommodation module distribution | `future_plans.md` has stats-driven plan but defaults to 27 | Partial; add 33-question format handling |

## Official Explanation Templates to Mirror

### Reading and Craft

College Board repeatedly explains reading items as:

```text
Choice [X] is best because it [does the stem task]. The text indicates [specific evidence].
This supports [exact interpretation].

Choice [Y] is incorrect because [single failure]. The text does not indicate/suggest [wrong claim].
```

Generation implication: `explanation_full` should name the stem task, identify the exact evidence span, and explain each distractor with one clean failure. This matches the current rules, but generated explanations should be checked for the same directness.

### Words in Context

College Board usually:

- Defines the correct word in context.
- Cites the phrase or sentence that determines the meaning.
- Defines each wrong word briefly.
- Explains why each wrong word creates an unsupported or illogical reading.

Generation implication: WIC distractors should be real words or phrases that are grammatically usable but fail by denotation, connotation, precision, register, or polarity.

### Grammar

College Board usually:

- Starts with "The convention being tested is..."
- Names the correct rule.
- Identifies the local words or clauses that control the rule.
- Labels wrong choices by the error they create.

Generation implication: grammar explanations should preserve the convention-first style already required in `rules_dsat_grammar_module.md`.

### Transitions

College Board explains transitions by naming the logical relationship:

- sequence/final event
- contrast/refutation
- addition
- result/consequence
- chronology
- alternative
- present-time shift after a historical setup
- emphasis/support
- causal chain
- specific or particular elaboration
- goal-to-action fulfillment
- frequency/difference emphasis
- simultaneity
- similarity
- appropriateness
- change over time or trend
- exception
- final realization
- converse or opposite tendency
- present continuation
- direct refutation
- logical consequence

Wrong answers are explained as signaling the wrong relationship.

Generation implication: transition items should store the intended relation and each distractor's relation. The current `transition_logic` rules cover this well.

### Notes Synthesis

College Board explanations focus on the requested rhetorical goal and audience. Common failures:

- Does not answer the goal.
- Gives background the audience does not need.
- Omits required context for an unfamiliar audience.
- Describes a detail but not the requested comparison, advantage, theory, category, sample, generalization, achievement, or research finding.
- Uses the right topic but omits a requested method, publication detail, measurement comparison, or significance claim.

Generation implication: the grammar module should add finer synthesis metadata instead of treating all notes questions as one broad `choose_best_notes_synthesis` bucket.

## Recommended Rule Additions

### 1. Add Paper-Accommodation Module Blueprint

Add a source-format field to module generation requests:

```json
{
  "test_format_key": "digital_app_adaptive | nondigital_linear_accommodation",
  "module_length": 27,
  "source_stats_format": "official_digital | official_nondigital_linear"
}
```

For PT4 nondigital linear Reading and Writing, observed module structure is:

- Q1-Q18: Reading/Craft/Information
- Q19-Q26: Standard English Conventions
- Q27-Q30 in Module 1 and Q27-Q28 in Module 2: transitions
- Q31-Q33 in Module 1 and Q29-Q33 in Module 2: notes synthesis

Do not let a 33-question paper source override the 27-question digital-app default unless the request is explicitly targeting the paper accommodation format.

### 2. Add WIC Polarity Trap

Observed official examples include negated contexts where the correct word must preserve logical polarity:

- "by no means" plus a word whose meaning is reversed by negation
- "isn't atypical" meaning the trait is common, not unusual

Suggested additions:

```json
{
  "reading_focus_key_candidate": "polarity_fit",
  "parent_skill_family_key": "words_in_context",
  "reasoning_trap_key_candidate": "polarity_mismatch",
  "student_failure_mode_key_candidate": "negation_blindness"
}
```

If avoiding new production keys, add a generation note under `contextual_meaning`: WIC items with negators, concessive phrases, or contrast markers must annotate the polarity cue in `evidence_span_text` and classify wrong answers that reverse the cue as `semantic_imprecision` or `contradiction`.

### 3. Add Experimental-Control Architecture

PT4 and PT6 repeatedly test hypotheses, controls, outcomes, indirect effects, alternative explanations, and expected vs surprising results. Suggested passage architecture:

```json
{
  "passage_architecture_key_candidate": "experiment_hypothesis_control_result",
  "uses": [
    "evidence_supports_claim",
    "evidence_weakens_claim",
    "data_supports_claim",
    "data_weakens_claim",
    "implication_inference"
  ],
  "required_elements": [
    "hypothesis",
    "experimental group",
    "control group or comparison baseline",
    "predicted direction",
    "observed outcome"
  ]
}
```

This would improve generation of items like acidic soil/choy sum, mycorrhizal fungi, elected-office control-group reasoning, leave-time attentiveness, placebo-awareness comparisons, and microorganism community composition.

Two narrower variants are also worth adding:

```json
{
  "passage_architecture_key_candidate": "indirect_effect_mediation",
  "required_elements": [
    "initial attitude or condition",
    "intermediate variable",
    "final behavior or outcome",
    "claim that the effect operates through the intermediate variable"
  ]
}
```

```json
{
  "passage_architecture_key_candidate": "alternative_explanation_ruled_out",
  "required_elements": [
    "observed change",
    "possible alternative cause",
    "control or finding that removes the alternative cause",
    "remaining explanation"
  ]
}
```

Add a mechanism-test architecture for items where researchers manipulate one
component to test whether it drives an observed effect:

```json
{
  "passage_architecture_key_candidate": "mechanism_manipulation_test",
  "required_elements": [
    "observed phenomenon",
    "candidate mechanism",
    "experimental replacement or manipulation",
    "predicted result if mechanism is causal",
    "observed result"
  ]
}
```

Add a subgroup-generalization pattern for items where evidence about one
well-studied group is tempting but may not support a broader population claim:

```json
{
  "passage_architecture_key_candidate": "studied_subgroup_generalization_limit",
  "required_elements": [
    "broad population or category",
    "well-studied subgroup",
    "evidence concentrated in that subgroup",
    "warning that subgroup evidence may not generalize"
  ],
  "primary_trap": "scope_extension"
}
```

### 4. Add No-Punctuation-Inside-Unit Grammar Rule

Observed PT4 and PT6 grammar includes cases where no punctuation is needed inside a required syntactic unit:

- PT4: no punctuation between a preposition and its complement.
- PT6: no punctuation between a verb and its object.

Current punctuation keys can absorb these, but generation would be clearer with an explicit rule under punctuation:

```json
{
  "grammar_focus_key_candidate": "unnecessary_internal_punctuation",
  "parent_grammar_role_key": "punctuation",
  "examples": [
    "no punctuation between preposition and complement",
    "no punctuation between verb and object",
    "no punctuation between subject and verb",
    "no punctuation inside an integrated relative clause"
  ]
}
```

If not adding a new key, add this as a passage construction and distractor pattern under `punctuation_comma`.

Also add explicit question-punctuation coverage:

```json
{
  "grammar_focus_key_candidate": "end_punctuation_question_statement",
  "parent_grammar_role_key": "punctuation",
  "examples": [
    "question mark for coordinated direct questions",
    "period for indirect questions embedded in declarative sentences"
  ]
}
```

If not adding a new key, include these under the existing sentence-boundary or punctuation generation rules.

Add explicit no-punctuation title/name and appositive patterns:

```json
{
  "punctuation_pattern_key": "title_name_no_punctuation | restrictive_appositive_no_punctuation",
  "examples": [
    "plant cell biologist Yuree Lee",
    "the chemical compound aluminum oxide"
  ]
}
```

For verb-form generation, add a finite-relative-clause pattern:

```json
{
  "verb_form_pattern_key": "finite_verb_in_relative_clause",
  "template": "[Noun phrase], which ______ [object/complement], [main verb phrase].",
  "wrong_option_pattern": "nonfinite participle or infinitive where a finite verb is required"
}
```

Also add a finite-main-clause pattern:

```json
{
  "verb_form_pattern_key": "finite_verb_in_main_clause",
  "template": "[Subject] ______ [object/complement].",
  "wrong_option_pattern": "nonfinite participle or infinitive where a finite verb is required"
}
```

Add a modal auxiliary pattern:

```json
{
  "verb_form_pattern_key": "modal_plus_plain_form",
  "template": "[Subject] would/could/should/might ______ [object/complement].",
  "wrong_option_pattern": "inflected or nonfinite form after modal auxiliary"
}
```

For pronouns, add event-reference cases:

```json
{
  "pronoun_pattern_key": "singular_event_reference",
  "template": "[Complete prior event or fact]. ______ [effect or significance].",
  "expected_pronoun_number": "singular"
}
```

Also add a tense/register note for literary-present items:

```json
{
  "passage_tense_register_key": "literary_present",
  "expected_tense_key": "simple_present",
  "tense_register_notes": "Use present tense when describing events or patterns in a literary work."
}
```

### 5. Expand Quantitative Evidence Patterns

PT6 confirms that quantitative questions are not limited to simple highest/lowest or two-value comparisons. Official items also use:

- two-variable trends moving in opposite directions
- binned distributions where individual-level comparison is not possible
- timing constraints, such as pre-leave versus post-leave measurements
- all-measures comparisons across study groups
- highest-across-every-month line-graph patterns
- exact-value lookup from a table
- changing percentage composition over time

Suggested additions:

```json
{
  "quantitative_pattern_key": "two_variable_opposite_trend | binned_distribution | timing_constrained_comparison | all_measures_group_comparison | repeated_highest_across_periods | exact_value_lookup | composition_change_over_time",
  "distractor_trap_candidates": [
    "wrong_time_window",
    "individual_inference_from_aggregate_bins",
    "single_measure_focus",
    "wrong_group_comparison",
    "wrong_table_row_or_column",
    "direction_reversal_over_time",
    "constraint_ignored"
  ]
}
```

These can live as non-production generation metadata if adding production keys is too heavy.

### 6. Expand Notes Synthesis Subtypes

PT4 and PT6 final questions show repeated official patterns:

- emphasize a difference
- emphasize a similarity
- explain an advantage
- present research to an unfamiliar audience
- present a theory to an unfamiliar audience
- describe a work to an unfamiliar audience
- introduce a book to an audience already familiar with a named source
- emphasize a relative comparison from notes
- emphasize a named person's achievement
- make a generalization
- contrast quantities
- emphasize a specific sample
- indicate a classification category
- identify a type of scientist or profession
- indicate a literary setting
- identify a title
- identify a year or date
- use a quotation to challenge an explanation
- present an overview of study findings
- explain an advantage of an object, format, or tool
- emphasize the significance of a discovery or fossil
- compare lengths or measurements
- present a study and its methodology
- present a study and its conclusions
- emphasize duration and purpose together
- emphasize size similarity
- contrast origins
- identify real author behind a pseudonym
- explain a technical mechanism
- compare structural types
- identify distance
- present the aim of a study
- identify statistical-authorship methods
- explain an advantage of a technique
- explain a misconception as the cause of a name
- provide a historical overview
- contrast poetic meters or formal structures
- place a document/event in context of changing beliefs
- compare hypothesis scope
- emphasize age similarity

Suggested metadata under `expression_of_ideas`:

```json
{
  "synthesis_goal_key": "emphasize_similarity | emphasize_difference | explain_advantage | present_research | present_theory | introduce_work | describe_work | emphasize_achievement | make_generalization | contrast_quantities | compare_measurements | emphasize_sample | identify_category | identify_profession | identify_setting | identify_title | identify_year | identify_duration | identify_distance | identify_author_pseudonym | explain_mechanism | contrast_structural_types | present_study_aim | identify_statistical_authorship_method | explain_technique_advantage | explain_misconception_naming | challenge_explanation_with_quote | present_study_overview | present_methodology | present_study_conclusions | emphasize_significance | explain_format_advantage | emphasize_duration_and_purpose | emphasize_size_similarity | contrast_origins | provide_historical_overview | contrast_formal_structures | contextualize_changing_beliefs | compare_hypothesis_scope | emphasize_age_similarity",
  "audience_knowledge_key": "audience_familiar | audience_unfamiliar | not_specified",
  "required_content_key": "definition_needed | background_omit | comparison_needed | measurement_values_needed | result_needed | title_and_content_needed | owner_of_achievement_needed | category_label_needed | sample_location_needed | profession_label_needed | setting_needed | year_needed | duration_needed | distance_needed | author_identity_needed | mechanism_needed | structural_roles_needed | study_aim_needed | statistical_method_needed | misconception_needed | quotation_needed | study_finding_summary_needed | method_needed | conclusion_needed | significance_needed | advantage_needed | purpose_needed | origin_labels_needed | timeline_needed | formal_feature_labels_needed | scope_terms_needed"
}
```

This is likely the largest generation-quality gap for matching College Board final-question behavior.

## Practical Generation Guidance From Official Practice Tests

For future generated Reading and Writing items:

- Make the correct answer boringly precise. College Board rewards exact fit, not cleverness.
- Distractors should sound official but fail on one axis only.
- Use official-style stems without paraphrase drift.
- For evidence items, preserve the exact variable in the claim. Wrong answers often change the variable, population, direction, or comparison.
- For data items, include at least one distractor that cites real data but answers the wrong question.
- For binned data, do not allow an option to infer individual-level information unless the graph supports it.
- For exact-value data items, make wrong answers come from nearby rows, columns, categories, or units.
- For constrained data items, make one distractor accurate in isolation but invalid because it ignores a stated constraint.
- For quote-illustration items, make one distractor satisfy only half of the claim.
- For parenthetical definition function items, make the correct answer identify clarification of a term, not a broader passage purpose.
- For mechanism-test items, keep the manipulated component, predicted effect, and observed result aligned.
- For subgroup-generalization items, make one distractor overextend evidence from a well-studied subgroup to the broader group.
- For WIC, keep all options grammatically viable in the blank.
- For grammar, include the smallest possible error zone and do not rely on topic difficulty.
- For literary tense questions, use present tense when discussing events or patterns inside a literary work.
- For finite-verb items, distinguish main-clause finite requirements from relative-clause finite requirements.
- For modal items, require the plain form after modal auxiliaries.
- For pronoun items, include singular pronouns that refer back to an entire event or fact, not only noun antecedents.
- For punctuation, test both required punctuation and required absence of punctuation inside syntactic units.
- For no-punctuation questions, include title/name, restrictive appositive, subject/verb, verb/object, and preposition/complement variants.
- For transitions, predefine the relation before writing options.
- For notes synthesis, define the audience and goal before writing the correct sentence.

## Bottom Line

The current rules are structurally aligned with College Board PT4, PT5, PT6, PT7, PT8, PT9, PT10, and PT11. They already encode most of the official reasoning: exact evidence, direct support, precise word choice, named grammar conventions, transition relations, and per-distractor explanations.

To better match official generation, prioritize additions for paper-format distribution, WIC polarity, experimental/control-group, mechanism-test, subgroup-generalization, and indirect-effect logic, quantitative exact-value/constrained/binned/timing patterns, finite-verb and modal subpatterns, event-reference pronouns, no-punctuation-inside-unit grammar, restrictive appositive and title/name punctuation, direct/indirect question punctuation, literary-present tense, parenthetical-definition function items, transition subtypes, and finer notes-synthesis audience/goal metadata.
