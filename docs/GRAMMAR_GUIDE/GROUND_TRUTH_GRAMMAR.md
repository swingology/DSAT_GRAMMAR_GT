# Digital SAT Grammar Ground Truth

**Purpose**: Authoritative reference for LLM-based question ingestion, classification, and generation.  
**Source**: Official College Board Digital SAT Practice Tests (4, 5, 6, 7-10)  
**Alignment**: College Board Reading & Writing Specifications — Standard English Conventions  
**Generated**: 2026-04-18

---

## How to Use This Document

### For LLM Ingestion (Pass 2 Annotation)

1. **Identify** whether the question tests Standard English Conventions (SEC)
2. **Select** the primary `grammar_role_key` from Section 2
3. **Select** the specific `grammar_focus_key` from Section 3
4. **Apply** disambiguation rules from Section 4 if multiple rules could apply
5. **Propose amendment** via `grammar_amendment.md` if the question reveals a gap

### For Human Review

- Use Section 5 (Frequency Data) to validate classifications
- Use Section 6 (Distractor Patterns) to verify option analysis
- Review amendment proposals in `grammar_amendment.md` quarterly

---

## Part 1: College Board Framework

The Digital SAT organizes Standard English Conventions into two top-level categories:

### 1.1 Boundaries

Tests selection of appropriate punctuation to delimit clauses, phrases, and sentence units.

**Rule types**:
- Sentence boundaries (fragments, run-ons, comma splices)
- Boundary punctuation (periods, semicolons, colons, dashes)
- Nonessential element punctuation (matched pairs of commas, dashes, parentheses)

**Frequency**: ~25-30% of all SEC questions

### 1.2 Form, Structure, and Sense

Tests grammar and usage independent of punctuation mechanics.

**Rule types** (College Board official):
- Subject-verb agreement
- Verb forms (finite/nonfinite, tense, mood, voice)
- Pronoun-antecedent agreement
- Subject-modifier placement
- Plural/possessive forms of nouns

**Additional rule types** (confirmed by released tests):
- Parallel structure
- Comparative structures
- Conjunction usage
- Logical predication
- Noun countability
- Elliptical constructions
- Negation patterns
- Idioms & preposition selection

**Frequency**: ~70-75% of all SEC questions

---

## Part 2: Grammar Role Keys (`grammar_role_key`)

**Table**: `lookup_grammar_role`

| Key | Description | Frequency |
|-----|-------------|-----------|
| `sentence_boundary` | Fragments, run-ons, comma splices, boundary punctuation | High |
| `agreement` | Subject-verb, pronoun-antecedent, case, number | Very High |
| `verb_form` | Tense, mood, voice, finite/nonfinite, participles | High |
| `modifier` | Placement, dangling, comparative, logical predication | Medium |
| `punctuation` | Comma, semicolon, colon, dash, apostrophe mechanics | Very High |
| `parallel_structure` | Lists, correlative conjunctions, comparisons | Medium-High |
| `pronoun` | Pronoun-specific errors (ambiguity, case, agreement) | Medium |
| `expression_of_ideas` | Rhetorical effectiveness, concision, precision, register | Medium-High |

---

## Part 3: Grammar Focus Keys (`grammar_focus_key`)

**Table**: `lookup_grammar_focus`

Each key maps to a `grammar_role_key` (shown in header as `→ role_name`). These mappings are authoritative; if another document conflicts, this document's section placement governs.

### 3.1 Sentence Boundary Rules

#### `sentence_fragment` → sentence_boundary
**Definition**: Incomplete grammatical unit punctuated as a sentence.

**Patterns**:
- Dependent clause standing alone: "Because the evidence was insufficient."
- Phrase without subject or verb: "The study showing clear results."
- Missing finite verb: "Was found to be effective."

**Correction**: Attach to independent clause or add missing elements.

**SAT Frequency**: Medium (1-2 per module)

---

#### `comma_splice` → sentence_boundary
**Definition**: Two independent clauses joined only by a comma.

**Error**: "The results were significant, they changed our understanding."

**Corrections**:
1. Period: "The results were significant. They changed our understanding."
2. Semicolon: "The results were significant; they changed our understanding."
3. Comma + FANBOYS: "The results were significant, and they changed our understanding."
4. Subordination: "Because the results were significant, they changed our understanding."

**SAT Frequency**: High (2-3 per module)

---

#### `run_on_sentence` → sentence_boundary
**Definition**: Two independent clauses without any punctuation or conjunction.

**Error**: "The results were significant they changed our understanding."

**SAT Frequency**: Low-Medium

---

#### `sentence_boundary` (catch-all) → sentence_boundary
**Definition**: Structural boundary issues not covered by specific fragment/comma splice keys.

**Includes**:
- Boundary punctuation with complex interruptions not covered by specific keys
- Terminal punctuation (question marks for direct vs. indirect questions)

**Note**: Colon/dash mechanics and matched-pair nonessential elements are now covered by `colon_dash_use`.

**SAT Frequency**: Medium

---

### 3.2 Agreement Rules

#### `subject_verb_agreement` → agreement
**Definition**: Verb must agree in number with its subject.

**Patterns**:
- **Simple**: "The scientist studies" / "The scientists study"
- **Intervening phrases**: "The bouquet of flowers IS" (ignore "of flowers")
- **Compound subjects**: "A and B" = plural; "A or B" = agree with nearer
- **Indefinite pronouns**: 
  - Always singular: each, either, neither, one, anyone, everyone
  - Always plural: both, few, many, several
  - Context-dependent: some, none, all, most
- **Collective nouns**: Usually singular (team, group, committee)
- **Inverted order**: "There ARE three reasons" (reasons = plural)

**Trap**: Nearest-noun attraction — students match verb to closest noun rather than head noun.

**SAT Frequency**: Very High (2-4 per module)

---

#### `pronoun_antecedent_agreement` → agreement
**Definition**: Pronoun must agree in number (and gender where applicable) with its antecedent.

**Patterns**:
- Singular antecedent → singular pronoun
- Plural antecedent → plural pronoun
- Compound with "and" → plural
- Compound with "or/nor" → agree with nearer

**Pronoun clarity** (ambiguity): The pronoun must clearly refer to one noun.
- Ambiguous: "When Alex met Jordan, he was late." (who is "he"?)
- Clear: "When Alex met Jordan, Alex was late."

**Reference clarity** (vague nouns): Demonstrative pronouns ("this," "that," "it") must have a clear antecedent.
- Vague: "The researchers conducted the experiment. This was significant." (What was significant? The experiment? The conducting?)
- Clear: "The researchers conducted the experiment. The results were significant."

**Overly distant references**: A pronoun must not be too far from its noun.
- Distant: "The scientist published a paper last year about climate change. She also won an award." (Who is "she"?)

**Implicit vs explicit clarity**: DSAT often prefers explicit clarity over elegance.
- Implicit: "The study was criticized because it was flawed." (vague — what was flawed?)
- Explicit: "The study was criticized because its methodology was flawed."

**SAT Note**: Follows traditional grammar (avoids singular "they").

**SAT Frequency**: Medium

---

#### `pronoun_case` → pronoun
**Definition**: Select subjective, objective, or possessive case based on grammatical role.

**Cases**:
- **Subjective**: I, he, she, we, they, who (subject position)
- **Objective**: me, him, her, us, them, whom (object of verb/preposition)
- **Possessive**: my/mine, his, her/hers, our/ours, their/theirs, whose

**SAT Traps**:
- "Between you and I" → "Between you and me" (object of preposition)
- "Him and I went" → "He and I went" (compound subject)
- "Who did you call?" → "Whom did you call?" (object position)

**SAT Frequency**: Medium

---

#### `pronoun_clarity` → pronoun
**Definition**: The pronoun must clearly refer to one unambiguous noun.

**Patterns**:
- **Ambiguous reference**: Multiple possible antecedents.
  - Ambiguous: "When Alex met Jordan, he was late." (who is "he"?)
  - Clear: "When Alex met Jordan, Alex was late."
- **Vague demonstratives**: "This," "that," "it" without a clear referent.
  - Vague: "The researchers conducted the experiment. This was significant."
  - Clear: "The researchers conducted the experiment. The results were significant."

**Disambiguation from `pronoun_antecedent_agreement`**: Use `pronoun_clarity` when the issue is ambiguity (who does "he" refer to?), not number/gender mismatch.

**SAT Frequency**: Medium

---

#### `noun_countability` → agreement
**Definition**: Distinguish count vs. mass nouns; select appropriate quantifiers.

**Patterns**:
- **Count nouns**: Can be pluralized, use "many" (book/books, idea/ideas)
- **Mass nouns**: Cannot be pluralized, use "much" (research, information, evidence)
- **Amount** → mass nouns; **Number** → count nouns
- **Fewer** → count nouns; **Less** → mass nouns

**Error**: "The amount of students" → "The number of students"

**Proportional clarity**: "Twice as many" (count nouns) vs "Twice as much" (mass nouns)
- Wrong: "Twice as much students"
- Correct: "Twice as many students"

**Overgeneral quantifiers**: "All," "most," "some" must be accurate relative to context.
- Wrong: "All scientists agree" (unless universal consensus is proven)
- Correct: "Many scientists agree" or "Most scientists agree"

**SAT Frequency**: Low-Medium

---

#### `determiners_articles` → agreement
**Definition**: Proper selection of articles and determiners based on noun specificity and countability.

**Patterns**:
- **"a" vs "an"**: Use "an" before vowel sounds; "a" before consonant sounds
- **"a" vs "the"**: "a" = indefinite (any one); "the" = definite (specific one)
- **"this" / "that" / "these" / "those"**: Demonstrative determiners must match number and proximity

**Error**: "She found a solution to the problem." vs "She found the solution to the problem." (meaning shifts from any solution to the specific correct one)

**SAT Frequency**: Low-Medium

---

#### `affirmative_agreement` → agreement
**Definition**: So/neither inversion patterns, tag questions.

**Note**: `affirmative_agreement` is placed under `agreement` because so/neither inversion requires agreement with the antecedent clause's auxiliary verb. Some taxonomies map it to `verb_form` because it involves auxiliary selection, but the agreement interpretation is canonical per this document's section placement. Disambiguation priority 7 (`noun_countability > subject_verb_agreement`) applies when both countability and agreement are at issue.

**Patterns**:
- "So + auxiliary + subject" = affirmative agreement
- "Neither/Nor + auxiliary + subject" = negative agreement

**Note**: Low frequency on Digital SAT; more common on ACT.

**SAT Frequency**: Very Low

---

### 3.3 Verb Form Rules

#### `verb_tense_consistency` → verb_form
**Definition**: Maintain consistent verb tense unless context requires shift.

**Patterns**:
- Narrative passages: past tense
- Scientific facts: present tense
- Historical present: occasional

**Error**: "The researcher observes the data and recorded the results."

**Perfect tense distinctions**:
- **Present perfect** (has/have + past participle): Action begun in past, continuing to present. "The team HAS collected data for three years." (still collecting)
- **Past perfect** (had + past participle): Action completed before another past action. "The team HAD collected data before the grant expired." (collection finished first)
- **SAT pattern**: "By the time the conference began, the researchers had already submitted their paper." (submission precedes conference — past perfect required)

**SAT Frequency**: High

---

#### `verb_form` → verb_form
**Definition**: Finite vs. nonfinite forms, mood, voice, participle selection.

**Patterns**:
- **Finite verbs**: Have tense, person, number (studies, studied)
- **Nonfinite**: Infinitives (to study), gerunds (studying), participles (studied)
- **Subjunctive mood**: "If I WERE", "I demand that he BE"
- **Voice**: Active vs. passive

**Verb patterning / subcategorization**: Certain verbs require specific structures after them.
- **Infinitive after specific verbs**: want TO go, decide TO run, allow him TO go
- **Gerund after specific verbs**: avoid running, suggest going, enjoy reading
- **Both possible with meaning shift**: "I stopped to smoke" (purpose) vs "I stopped smoking" (quit the habit)
- **SAT trap**: "allow him to go" (correct) vs "allow going" (wrong — allow requires an object + infinitive)

**Key SAT test**: Choosing nonfinite infinitive when sentence already has finite main verb.

**Subjunctive mood patterns**:
- **Contrary-to-fact conditions**: "If I WERE rich" (not "was") — subjunctive required
- **Demands/requirements after certain verbs**: "The guidelines require that he BE present" — base form, not "is"
- **Common trigger verbs**: require, suggest, recommend, demand, insist + "that" clause

**Conditional sentences — real vs. unreal**:
- **Real (possible)**: "If the experiment succeeds, the results WILL be significant." (present + future)
- **Unreal (hypothetical)**: "If the experiment succeeded, the results WOULD be significant." (past + would)
- **Past unreal**: "If the experiment HAD succeeded, the results WOULD HAVE been significant."
- **SAT trap**: Mixing real and unreal — "If the experiment succeeds, the results WOULD be significant" is wrong.

**Temporal & conditional logic**: Events must occur in logical order; conditionals must be internally consistent.
- **Timeline consistency**: "By the time the conference began, the researchers had already submitted their paper." (submission precedes conference)
- **Sequence clarity**: Avoid ambiguity in event order. "After studying, she took the test, and then she reviewed her answers."
- **Mixed conditionals**: Combining different conditional types is usually wrong on DSAT.
  - Wrong: "If she studied, she would have passed yesterday." (present if-clause with past result)
  - Correct: "If she had studied, she would have passed yesterday." (past unreal)

**SAT Frequency**: Medium

---

#### `voice_active_passive` → verb_form
**Definition**: Active vs. passive voice selection and errors.

**Patterns**:
- **Active**: "The team conducted experiments"
- **Passive**: "Experiments were conducted"

**Errors**:
- Unnecessary passive shift obscuring agency
- Missing "by" phrase when agency matters
- Passivizing intransitive verbs ("An accident was happened" → "An accident happened")

**SAT Frequency**: Low

---

### 3.4 Modifier Rules

#### `modifier_placement` → modifier
**Definition**: Modifiers must be placed adjacent to words they modify.

**Patterns**:
- **Misplaced**: "The scientist only found three samples" → "found only three samples"
- **Dangling**: "Walking through the lab, the equipment was impressive" → "Walking through the lab, I found the equipment impressive"
- **Squinting**: "Studying hard often leads to success" (ambiguous)

**Absolute phrases** (noun + participle modifying whole sentence, not a specific word):
- Structure: Noun + participle + modifiers
- "The experiment complete, the team analyzed the results." (absolute phrase — no dangling issue since it modifies the whole clause)
- "Their work finished, the researchers presented their findings."
- Absolute phrases are tested less frequently but appear in complex sentences.

**Modifier scope** (semantic logic): Even if grammatically placed, a modifier must logically modify the right element.
- Wrong scope: "Walking down the street, the trees looked beautiful." (trees aren't walking)
- Correct: "Walking down the street, she found the trees beautiful."

**Scope ambiguity**: A modifier can attach to multiple elements, creating confusion.
- "She only eats vegetables on weekends." (Does she eat only vegetables? Or only on weekends?)
- "The scientist found the solution quickly in the lab." (Was the solution found quickly, or was it in the lab quickly?)

**Overextended modifiers**: A modifier accidentally applies to too much of the sentence.
- "Covered in snow, the hikers admired the mountain." (Implies hikers are covered, not the mountain)

**SAT Frequency**: Medium

---

#### `comparative_structures` → modifier
**Definition**: Comparative and superlative forms, "as...as" patterns, faulty comparisons.

**Patterns**:
- **Comparative** (-er, more): Two items
- **Superlative** (-est, most): Three+ items
- **Double comparatives**: "more better" (error)
- **Adjective vs. adverb**: Adjectives modify nouns; adverbs modify verbs, adjectives, or other adverbs. After linking verbs (feel, seem, look, become), use adjectives.
  - Wrong: "feel badly" (badly modifies the verb feel — but feel is a linking verb)
  - Correct: "feel bad" (bad describes the subject)
  - Wrong: "real good" → "really good"
- **Illogical comparisons**: "The results of Experiment 1 were more significant than Experiment 2" → "than THOSE of Experiment 2"
- **Implied comparisons**: Missing "that of" or "those of" creates a category mismatch.
  - Wrong: "Her salary is higher than a teacher." (salary vs person)
  - Correct: "Her salary is higher than that of a teacher." (salary vs salary)
- **False equivalence**: Comparing unlike categories even if grammar is correct.
  - Wrong: "The speed of the car is faster than the bicycle." (speed vs vehicle)
  - Correct: "The speed of the car is faster than that of the bicycle."
- **"As...as" ellipsis**: "She is as tall, if not taller, than" → "as tall AS, if not taller THAN"

**SAT Frequency**: Medium

---

#### `logical_predication` → modifier
**Definition**: Logical relationships between sentence elements.

**Patterns**:
- **"Reason is because"**: "The reason she left is THAT she was tired" (not "because")
- **"Is when/where"**: "A paradox is A STATEMENT THAT contradicts itself" (not "when")
- **Faulty equations**: Subject complement must match subject type

**Sentence-level logic consistency**: Time, cause-effect, and contrast must make sense across clauses.
- Illogical: "She was tired; therefore, she went for a run." (tiredness doesn't cause running)
- Logical: "She was tired; therefore, she went to bed."

**Subject–predicate compatibility**: The subject must logically perform or possess the action.
- Wrong: "The theory argues that..." (theories don't argue; people do)
- Correct: "The theory suggests that..."

**Category errors**: Avoid mismatched causality or attribution.
- Wrong: "The price increased the demand" (reverses causality)
- Wrong: "The painting was excited to be displayed" (inanimate objects lack emotions)

**SAT Frequency**: Low

---

### 3.5 Punctuation Rules

#### `punctuation_comma` → punctuation
**Definition**: Comma usage for separation and delimiting.

**Required**:
- Before FANBOYS joining independent clauses
  - With two independent clauses: "I studied, and I passed."
  - Without two independent clauses: "I studied and passed." (no comma)
- After introductory elements
- Between coordinate adjectives
- In series (Oxford comma: "A, B, and C")
- To set off non-restrictive modifiers
- To set off parenthetical elements

**Prohibited**:
- Between subject and verb
- Between verb and object
  - Wrong: "She completed, the project."
  - Correct: "She completed the project."
- In restrictive modifiers

**SAT Frequency**: Very High

---

#### `colon_dash_use` → punctuation
**Definition**: Colon and dash as clause-boundary punctuation and matched-pair markers for nonessential elements.

**Patterns**:
- **Colon after independent clause**: Introduces a list, explanation, or elaboration — the preceding clause must be grammatically complete. "The team had one goal: to finish the study."
- **Dash (colon equivalent)**: Introduces an explanation or summary, more emphatic than a colon. "The results pointed to one conclusion—the hypothesis was correct."
- **Matched-pair dashes for nonessential elements**: Use two dashes to set off parenthetical material. "The experiment—conducted over three years—produced surprising results."
- **Matched-pair rule**: Commas, dashes, and parentheses must be used consistently in pairs. Mixing (one comma + one dash) is an error.

**SAT Trap**: Using a colon where the preceding clause is incomplete, or mixing a dash on one side with a comma on the other for the same nonessential element.

**Disambiguation from `semicolon_use`**: Semicolons join two independent clauses of equal weight; colons introduce explanation or elaboration after an independent clause.

**Disambiguation from `punctuation_comma`**: Use `colon_dash_use` when the specific mechanics of colons or dashes are being tested, not general comma placement.

**SAT Frequency**: Medium-High (confirmed as a frequent Boundaries question type in released tests)

---

#### `semicolon_use` → punctuation
**Definition**: Semicolon joins closely related independent clauses.

**Patterns**:
- Two independent clauses: "The study was complete; the team submitted findings."
- Before conjunctive adverb: "The data was limited; HOWEVER, the findings were significant."
- Complex series (items contain internal commas): "The team included John, a pitcher; Sarah, a catcher; and Mike, a coach."

**Conjunctive adverbs**: however, therefore, moreover, consequently, otherwise, nevertheless, thus

**SAT Frequency**: High

---

#### `conjunctive_adverb_usage` → punctuation
**Definition**: Punctuation of conjunctive adverbs as clause connectors. Hybrid logic + punctuation rule.

**Patterns**:
- **Semicolon before, comma after**: "The data was limited; however, the findings were significant."
- **Comma only is wrong**: "The data was limited, however, the findings were significant." (comma splice)
- **Standalone however**: "The data was limited. However, the findings were significant." (period + comma after)

**Disambiguation from `conjunction_usage`**: FANBOYS take a comma when joining two independent clauses; conjunctive adverbs take a semicolon or period before and a comma after.

**SAT Frequency**: High

---

#### `apostrophe_use` → punctuation
**Definition**: Apostrophes for possession and contractions.

**Patterns**:
- **Singular possessive**: student's, boss's, Jones's (or Jones')
- **Plural possessive** (ending in s): students', bosses'
- **Plural possessive** (not ending in s): children's, men's
- **Joint possession**: Kim and Dale's research (shared)
- **Separate possession**: Kim's and Dale's research papers (individual)
- **Contractions**: it's = it is, they're = they are, who's = who is

**SAT Trap**: its (possessive) vs. it's (contraction)

**SAT Frequency**: High

---

#### `possessive_contraction` → punctuation
**Definition**: Homophone confusion between possessive pronouns and contractions.

**Patterns**:
- its (possessive) vs. it's (contraction)
- their (possessive) vs. they're (contraction)
- whose (possessive) vs. who's (contraction)
- your (possessive) vs. you're (contraction)

**SAT Frequency**: Medium

---

#### `relative_pronouns` → modifier
**Definition**: Which/that, who/whom in restrictive vs. non-restrictive clauses.

**Patterns**:
- **That** → restrictive (essential, no commas): "The book THAT I read"
- **Which** → non-restrictive (supplementary, commas): "The book, WHICH I read yesterday,"
- **Who** → people, subject position
- **Whom** → people, object position (or after preposition: "to whom")

**SAT Frequency**: High

---

#### `appositive_punctuation` → punctuation
**Definition**: Punctuation rules for appositive phrases (noun phrases that rename another noun).

**Non-restrictive appositives** (commas required — appositive adds bonus info to already-specific noun):
- "My first professor, **Dr. Smith**, inspired my career." (already specific = "my first professor")
- "The researchers, **a team of five scientists**, published their findings."

**Restrictive appositives** (no commas — appositive identifies which one):
- "The scientist **Darwin** developed the theory of evolution." (specifies which scientist)
- "My friend **Sarah** called yesterday." (specifies which friend)

**SAT trap**: Omitting commas around non-restrictive appositive, or adding commas around restrictive one.

**Colon introducing appositive**: "The study revealed one key finding: the treatment was effective." — colon can introduce an appositive that renames a preceding noun.

**Disambiguation from `punctuation_comma`**: Use `appositive_punctuation` when the specific mechanics of appositive phrases are being tested; use `punctuation_comma` for general non-restrictive modifier comma rules.

**SAT Frequency**: Medium-High

---

#### `hyphen_usage` → punctuation
**Definition**: Hyphens in compound modifiers, compound numbers.

**Patterns**:
- **Compound modifier before noun**: "well-known author", "high-speed chase"
- **Compound numbers**: twenty-one, ninety-nine
- **Compound modifiers after noun**: Usually no hyphen ("The author is well known")

**SAT Frequency**: Low-Medium

---

#### `quotation_punctuation` → punctuation
**Definition**: Punctuation placement relative to quotation marks (American English convention).

**Rules**:
- **Periods and commas**: Go INSIDE closing quotation marks — "groundbreaking."
- **Semicolons and colons**: Go OUTSIDE closing quotation marks — "significance"; however...
- **Question marks**: Inside if the question is part of the quote; outside if the question applies to the whole sentence

**SAT Frequency**: Low

---

### 3.6 Parallel Structure Rules

#### `parallel_structure` → parallel_structure
**Definition**: Items in series or comparisons must share grammatical form.

**Patterns**:
- **Lists**: "collecting, analyzing, and writing" (all gerunds)
- **Correlative conjunctions**: "both rigorous AND innovative" (parallel adjectives)
- **"Not only...but also"**: "not only WAS published but also WON" (parallel verb forms)
- **Comparisons**: "The results of E1 were more significant than THOSE of E2"

**SAT Frequency**: Medium-High

---

#### `elliptical_constructions` → parallel_structure
**Definition**: Omitted words in comparisons and coordinate structures.

**Patterns**:
- **Comparative ellipsis**: "She likes him better than I" (than I do) vs. "than me" (than she likes me)
- **Coordinate ellipsis**: "She likes tea, and he [likes] coffee"
- **Recoverability**: Missing words must be easily inferred from context.
  - Recoverable: "She likes baseball; he, basketball." (likes is clearly implied)
  - Ambiguous: "She likes baseball more than her sister." (more than her sister likes? or more than she likes her sister?)
- **Structural consistency**: Parallel structures allow ellipsis only when the grammar remains clear.
  - Clear: "She studies chemistry, and he, biology."
  - Unclear: "She studies chemistry, and he biology." (missing verb is awkward without comma)

**SAT Frequency**: Low

---

#### `conjunction_usage` → parallel_structure
**Definition**: Coordinating, subordinating conjunctions and conjunctive adverbs.

**Patterns**:
- **FANBOYS**: For, And, Nor, But, Or, Yet, So (comma before when joining independent clauses)
- **Conjunctive adverbs**: Semicolon before, comma after ("The results were significant; however, they were unexpected.")
- **"As" vs. "Like"**: "As" introduces clause; "Like" compares nouns
- **Subordinators**: after, before, since, until, when, while, because, although, whereas

**SAT Frequency**: Medium

---

### 3.7 Negation Rules

#### `negation` → verb_form
**Definition**: Double negatives, negative concord, hardly/scarcely/no sooner patterns.

**Patterns**:
- **Double negatives**: "I don't have no money" → "I don't have any money"
- **Misplaced negation**: The position of "not" changes meaning.
  - "She didn't almost win" (she lost by a lot)
  - "She almost didn't win" (she won, but barely)
- **Scope of negation**: What exactly is being negated?
  - "Not all scientists believe the results are reliable" (some do, some don't)
  - "All scientists do not believe the results are reliable" (intended: none believe — but grammar suggests each individually doesn't believe)
- **Logical reversals**: "Not uncommon" = somewhat common (subtle)
- **Hardly/Scarcely...when**: "Hardly HAD she arrived WHEN it began" (not "than")
- **No sooner...than**: "No sooner HAD she arrived THAN it began" (not "when")
- **Inversion**: "Never HAVE I seen" (negative adverb triggers inversion)

**Note**: Low frequency on Digital SAT; more common on ACT.

**SAT Frequency**: Very Low

---

### 3.8 Idiom and Preposition Rules

#### `preposition_idiom` → verb_form
**Definition**: Selection of specific prepositions required by certain verbs, nouns, or adjectives.

**Patterns**:
- **"Agree"**: agree WITH (a person), agree TO (a proposal), agree ON (a plan)
- **Common phrases**: responsible FOR, different FROM, composed OF
- **Double Prepositions**: "between YOU AND ME" (pronoun case + preposition combined)
- **Fixed expressions**: "as a result of," "in contrast to," "on the other hand"
- **Verb patterns**: "prefer X to Y" (not "prefer X over Y" on DSAT)
- **Subtle idiom traps**: Grammatically valid but nonstandard phrasing.
  - Wrong: "capable to do" → "capable OF doing"
  - Wrong: "distinguish between X and Y" is standard; "distinguish X from Y" is also acceptable, but "distinguish X and Y" is nonstandard

**SAT Frequency**: Low-Medium

---

### 3.9 Expression of Ideas

// Note: Expression of Ideas rules are not Standard English Conventions (SEC). They test rhetorical effectiveness rather than grammatical correctness. These may be separated into a standalone taxonomy later; included here for completeness during ingestion.

#### `redundancy_concision` → expression_of_ideas
**Definition**: Remove unnecessary repetition and wordiness.

**Patterns**:
- **Redundancy**: "advance planning" → "planning" (advance is implied)
- **Tautology**: "unexpected surprise" → "surprise"
- **Wordiness**: "due to the fact that" → "because"
- **Circular definitions**: "A solution that solves the problem" (solution already implies solving)
- **Repeated meaning across clauses**: "She returned back to her home" (returned = came back)
- **Low-value filler phrases**: "in order to" → "to"; "at this point in time" → "now"

**SAT Frequency**: Medium

---

#### `precision_word_choice` → expression_of_ideas
**Definition**: Select the most logically accurate and contextually appropriate word.

**Patterns**:
- **Denotation precision**: "increase" vs "improve" vs "expand" (different meanings)
- **Connotation fit**: "thrifty" (positive) vs "stingy" (negative) vs "frugal" (neutral)
- **Contextual accuracy**: "The results indicate" (supported) vs "The results prove" (too strong)
- **Near-synonym distinction**: Words that are close in meaning but not interchangeable.
  - "Efficient" (uses resources well) vs "effective" (achieves the goal)
  - "Economic" (related to economics) vs "economical" (thrifty)
- **Domain-specific precision**: Scientific, historical, or technical wording must be accurate.
  - "Hypothesis" (untested idea) vs "theory" (well-supported explanation)
  - "Correlation" (relationship) vs "causation" (one causes the other)
- **Avoiding vagueness**: Replace weak words with precise ones.
  - Weak: "things," "stuff," "very," "a lot"
  - Strong: "evidence," "findings," "significantly," "substantially"

**SAT Frequency**: High

---

#### `register_style_consistency` → expression_of_ideas
**Definition**: Maintain consistent tone and formality throughout the passage.

**Patterns**:
- **Formal vs informal**: Avoid mixing "kids" with "children" in the same passage
- **Technical register**: "The experiment yielded significant data" (formal) vs "The test gave good results" (informal)
- **Tone shifts**: A passage about scientific research should not suddenly use colloquialisms

**SAT Frequency**: Medium

---

#### `logical_relationships` → expression_of_ideas
**Definition**: The connection between clauses must be meaningful and logically correct.

**Patterns**:
- **Cause vs correlation**: "Because" (causation) vs "since" (time or reason) vs "as" (while or because)
- **Contrast accuracy**: "Although" and "however" require genuine contrast; "nevertheless" requires a prior contradiction
- **Result relationships**: "Therefore," "thus," "so" — the second clause must follow logically from the first
- **Mismatched transitions**: "She was tired; therefore, she went for a run." (illogical result)

**SAT Frequency**: High

---

#### `emphasis_meaning_shifts` → expression_of_ideas
**Definition**: Small structural changes alter meaning without creating a grammar error.

**Patterns**:
- **"Only" placement**: "Only she said that" (no one else spoke) vs "She only said that" (she did nothing else)
- **Restrictive emphasis**: Subtle shifts in what is highlighted by word order
- **Word order effects**: "Quickly the scientist completed the experiment" vs "The scientist quickly completed the experiment"

**SAT Frequency**: Low-Medium

---

#### `data_interpretation_claims` → expression_of_ideas
**Definition**: Claims involving charts, studies, or data must be accurately stated.

**Patterns**:
- **Overclaiming**: "The study proves that X causes Y" when the data only shows correlation
- **Underprecision**: Using "proves" when "suggests" or "indicates" is warranted
- **Correlation vs causation**: Presenting a relationship as causal when it is only correlational
- **Inaccurate summarization**: A choice that distorts the data's actual meaning

**SAT Frequency**: Medium

---

#### `transition_logic` → expression_of_ideas
**Definition**: Select the transition word that accurately expresses the relationship between ideas.

**Patterns**:
- **Contrast**: "however," "nevertheless," "on the other hand" — requires genuine opposition
- **Cause/result**: "therefore," "thus," "consequently" — the second idea must follow from the first
- **Addition**: "furthermore," "moreover," "in addition" — extends the same direction
- **Example**: "for example," "for instance," "specifically" — introduces a concrete illustration
- **Mismatched transitions**: "She was tired; therefore, she went for a run." (illogical result)

**Disambiguation from `conjunction_usage`**: Conjunctions join clauses structurally; transitions express logical relationships between ideas. A sentence can have correct conjunction punctuation but the wrong transition word.

**SAT Frequency**: High

---

## Part 4: Disambiguation Rules

**Purpose**: When multiple `grammar_focus_key` values could apply, use these priority rules.

### Philosophy: Meaning Over Form

DSAT increasingly prioritizes **why a sentence is wrong** over **what grammatical rule it breaks**. A sentence can be grammatically perfect but logically invalid — and the test will key on the meaning failure.

**Hierarchy**:
1. Sentence validity (boundary)
2. Meaning correctness (logic, transitions, negation)
3. Highly specific grammar (comparative, pronoun_case, etc.)
4. General grammar (verb_form, modifier_placement, etc.)
5. Pure punctuation

### Priority Order

| Priority | Rule | Explanation |
|----------|------|-------------|
| 1 | `sentence_boundary` > `punctuation` | Structural boundary issues take precedence |
| 2 | `logical_predication` > `modifier_placement`, `comparative_structures`, `parallel_structure`, `conjunction_usage` | Meaning correctness over structural mechanics |
| 3 | `transition_logic` > `conjunction_usage`, `parallel_structure` | Logical relationship between ideas takes precedence |
| 4 | `conjunctive_adverb_usage` > `punctuation`, `conjunction_usage` | Hybrid logic + punctuation rule |
| 5 | `negation` > `logical_predication`, `parallel_structure`, `modifier_placement`, `verb_form` | Negation flips meaning and overrides logic |
| 6 | `pronoun_case` > `pronoun_antecedent_agreement` | Case errors are easier to identify |
| 7 | `pronoun_clarity` > `pronoun_antecedent_agreement` | Ambiguity is a meaning issue, not agreement |
| 8 | `comparative_structures` > `parallel_structure`, `modifier_placement` | Comparison defines the structure; parallelism is secondary |
| 9 | `voice_active_passive` > `verb_form` | Voice is more specific than general verb form |
| 10 | `noun_countability` > `subject_verb_agreement` | Countability determines agreement |
| 11 | `relative_pronouns` > `modifier_placement` | Relative pronoun selection is more specific |
| 12 | `possessive_contraction` > `apostrophe_use` | Homophone confusion is more specific |
| 13 | `hyphen_usage` > `punctuation`, `modifier_placement` | Compound modifier hyphenation is specific |
| 14 | `preposition_idiom` > `conjunction_usage` | Specific verb-preposition pairings take precedence |

### Decision Tree

```
Step 1: Is the error a sentence boundary issue (fragment, run-on, comma splice)?
  → YES: Use sentence_boundary family (comma_splice, sentence_fragment, run_on_sentence)
  → NO: Continue to Step 2

Step 2: Is the error purely punctuation mechanics (comma, semicolon, apostrophe)?
  → YES: Use punctuation subtypes (punctuation_comma, semicolon_use, apostrophe_use)
  → NO: Continue to Step 2.5

Step 2.5: Is the error about logical meaning or sentence validity (even if grammatically correct)?
  → Illogical subject–predicate: logical_predication
  → Wrong transition word (however vs therefore): transition_logic
  → Negation flips meaning unexpectedly: negation
  → Ambiguous pronoun reference: pronoun_clarity
  → NO: Continue to Step 3

Step 3: Is the error about pronouns?
  → Case confusion (I/me, who/whom): pronoun_case
  → Ambiguous reference: pronoun_clarity
  → Antecedent mismatch: pronoun_antecedent_agreement

Step 4: Is the error about verbs?
  → Voice issue (active/passive): voice_active_passive
  → Tense inconsistency: verb_tense_consistency
  → Mood (subjunctive) or general form: verb_form

Step 5: Is the error about modifiers?
  → Dangling/misplaced participle: modifier_placement
  → Predication error ("reason is because", "is when/where"): logical_predication
  → Scope ambiguity or overextension: modifier_placement

Step 6: Is the error about comparison or parallel structure?
  → Comparison structure: comparative_structures
  → List/conjunction: parallel_structure, conjunction_usage
  → Ellipsis: elliptical_constructions

Step 7: Is the error about agreement?
  → Subject-verb: subject_verb_agreement
  → Countability (fewer/less, amount/number): noun_countability
  → Indefinite pronoun: subject_verb_agreement

Step 8: Is the error about negation?
  → YES: negation (double negatives, hardly/scarcely patterns)

Step 9: Is the error about relative clauses?
  → Which vs. that (restrictive vs. non-restrictive): relative_pronouns
  → Who vs. whom (case in relative clauses): relative_pronouns

Step 10: Is the error a homophone confusion?
  → Its/it's, their/they're, whose/who's: possessive_contraction

Step 11: Is the error about hyphenation?
  → Compound modifier: hyphen_usage
  → Compound number: hyphen_usage

Step 12: Is the error about conjunctive adverb punctuation?
  → ; however, / , however: conjunctive_adverb_usage

Step 13: Is the error about a specific required preposition or idiom pairing?
  → YES: preposition_idiom

Step 14: Default to most specific applicable category
```

---

## Part 5: SAT Frequency Data

Based on analysis of Official SAT Practice Tests 4, 5, 6, 7-10:

| Rule Category | Frequency | Avg. Questions per Module |
|--------------|-----------|---------------------------|
| `punctuation_comma` | Very High | 2-3 |
| `subject_verb_agreement` | Very High | 2-3 |
| `verb_tense_consistency` | High | 1-2 |
| `colon_dash_use` | Medium-High | 1-2 |
| `semicolon_use` | High | 1-2 |
| `apostrophe_use` | High | 1-2 |
| `sentence_boundary` | High | 1-2 |
| `comma_splice` | High | 1-2 |
| `parallel_structure` | Medium-High | 1-2 |
| `relative_pronouns` | High | 1-2 |
| `modifier_placement` | Medium | 1 |
| `pronoun_case` | Medium | 1 |
| `pronoun_antecedent_agreement` | Medium | 1 |
| `possessive_contraction` | Medium | 1 |
| `verb_form` | Medium | 1 |
| `conjunction_usage` | Medium | 1 |
| `comparative_structures` | Medium | 1 |
| `appositive_punctuation` | Medium-High | 1-2 |
| `hyphen_usage` | Low-Medium | 0-1 |
| `sentence_fragment` | Medium | 0-1 |
| `noun_countability` | Low-Medium | 0-1 |
| `voice_active_passive` | Low | 0-1 |
| `logical_predication` | Low | 0-1 |
| `elliptical_constructions` | Low | 0-1 |
| `affirmative_agreement` | Very Low | 0 |
| `negation` | Very Low | 0 |
| `preposition_idiom` | Low-Medium | 0-1 |

**Note**: `affirmative_agreement` and `negation` appear to be ACT-adjacent; minimal evidence from released Digital SAT tests.

---

## Part 6: Distractor Patterns by Rule

### 6.1 Agreement Distractors

| Pattern | Description | Example |
|---------|-------------|---------|
| `nearest_noun_attraction` | Students match verb to closest noun | "The key to the cabinets ARE" (should be IS) |
| `intervening_phrase_trap` | Long phrase between subject and verb | "The members of the committee, along with their families, IS" |

### 6.2 Punctuation Distractors

| Pattern | Description | Example |
|---------|-------------|---------|
| `punctuation_style_bias` | Preference for "sophisticated" punctuation | Choosing dash over period for style over correctness |
| `comma_splice_with_conjunctive_adverb` | However/therefore don't fix comma splices | "The results were significant, however, they were unexpected." |
| `mixed_nonessential_pair` | Mixing comma and dash for same parenthetical | "The study—published in 2020), received attention." |

### 6.3 Verb Form Distractors

| Pattern | Description | Example |
|---------|-------------|---------|
| `tense_bait` | Tense matches nearby verbs but wrong for meaning | Using past tense for general scientific truth |
| `finite_nonfinite_confusion` | Choosing finite verb when nonfinite required | "The researcher TO STUDY the data" (should be "studied") |

### 6.4 Modifier Distractors

| Pattern | Description | Example |
|---------|-------------|---------|
| `modifier_attachment_trap` | Modifier grammatically attaches to wrong word | "Walking down the street, the trees were beautiful." |
| `split_infinitive_avoidance` | Over-correcting to avoid split infinitive | "To boldly go" → "To go boldly" (both acceptable) |

### 6.5 Parallel Structure Distractors

| Pattern | Description | Example |
|---------|-------------|---------|
| `partial_parallelism` | Some items parallel, one breaks pattern | "collecting, analyzing, and TO WRITE" |
| `correlative_misplacement` | Not only/but also placed incorrectly | "The research not only WAS published but also WON" |

---

## Part 7: Syntactic Traps

Source: `VERBAL_TRAPS.md` (seeded in `migrations/017_prose_grammar_complexity.sql`). These patterns increase question difficulty independent of which grammar rule is being tested. Use during difficulty calibration and Pass 2 annotation of `syntactic_trap_key`.

**Schema fields**:
- `syntactic_trap_key` → `question_classifications` (labels the trap in an official question)
- `target_syntactic_trap_key` → `question_generation_profiles` (instructs LLM to embed a trap when generating)
- `hidden_clue_type_key` → `question_reasoning` (the non-obvious clue revealing the correct answer — related but distinct)
- `syntactic_trap` annotation type → `coaching_annotations` (Note: `syntactic_trap` is just one of several annotation types stored here, alongside `key_evidence`, `clause_boundary`, etc., which collectively power the frontend's interactive highlighting)

| Trap Key | Description | Example |
|----------|-------------|---------|
| `none` | No notable syntactic trap present | — |
| `nearest_noun_attraction` | Verb matches closest noun instead of head noun | "The key to the cabinets ARE lost" |
| `garden_path` | Initial parse leads down wrong structural path requiring mid-sentence revision | "The horse raced past the barn fell." |
| `early_clause_anchor` | Initial subordinate clause causes students to anchor on the wrong subject for the main clause | "Because the researcher analyzed the data, the results..." (student anchors on "researcher" as main subject when it shifts) |
| `nominalization_obscures_subject` | Heavy nominalization hides who is doing what; students misidentify agent or action | "The investigation of the findings by the team was completed" |
| `interruption_breaks_subject_verb` | Long interrupting phrase between subject and verb causes agreement errors | "The CEO, along with the entire executive team and board members, ARE present" |
| `long_distance_dependency` | Grammatical relationship spans many words; high working memory load | Relative pronoun far from its antecedent across a long sentence |
| `pronoun_ambiguity` | Pronoun could refer to multiple antecedents; students must resolve via discourse context | "When the researcher met the director, she was impressed." (who was impressed?) |
| `scope_of_negation` | Negation word (not, never, no) has wide scope but students apply it narrowly, or vice versa | "Not all scientists believe the results are reliable" — scope of "not" applies to "all," not to "believe" |
| `modifier_attachment_ambiguity` | Participial or prepositional phrase could attach to multiple NPs | "I saw the man with the telescope." |
| `presupposition_trap` | Sentence presupposes something students incorrectly accept as stated | "Since X stopped doing Y, X must have done Y before" — students accept the presupposition without checking |
| `temporal_sequence_ambiguity` | Order of events is unclear due to mixed tense or non-linear narration | Mixed tense passage where past and present perfect alternate without clear sequence |
| `multiple` | More than one syntactic trap present | — |

---

## Part 8: LLM Ingestion Notes

Guidance for Pass 2 annotation of official SAT grammar questions.

### 8.1 "No Change" Questions

Approximately 20% of official SAT grammar questions have the original text as the correct answer. Do not assume an error is present. Read all four options before classifying the rule being tested.

### 8.2 Multi-Error Questions

Some questions simultaneously test multiple grammar concepts — one option may fix one error but introduce another. When annotating:

1. Identify all errors present in each option independently.
2. Classify the `grammar_focus_key` by the **primary rule tested** — the error that eliminates the most wrong options.
3. Note secondary rules in `validation_errors_json` if relevant.

**Example**: A question with a comma splice where a distractor also has subject-verb disagreement. Primary key = `comma_splice`; the SVA error is a distractor mechanic, not the rule being tested.

### 8.3 Stylistic vs. Grammatical Corrections

Some options are grammatically correct but rhetorically inferior — choppy, verbose, or awkward. On the SAT, the best answer is both grammatically correct AND rhetorically appropriate. If multiple options are grammatically valid, classify the question as Expression of Ideas (transitions, rhetorical synthesis) rather than Standard English Conventions.

### 8.4 Passage-Level Tense Register

SAT passages follow predictable tense conventions that affect which verb forms are correct:

| Passage Type | Expected Tense |
|---|---|
| Narrative / literary | Past tense throughout |
| Scientific fact / general truth | Simple present |
| Historical accounts | Past, with past perfect for prior events |
| Specific study procedures | Past ("we investigated") |
| Established findings | Present ("the results indicate") |

**Correct annotation**: If a verb tense error is due to passage-level register mismatch (not a local consistency error), classify as `verb_tense_consistency` and note the expected register.

---

## Part 10: Amendment Process

When the LLM encounters an official College Board question that:

1. **Does not fit** any existing `grammar_focus_key`
2. **Reveals a sub-pattern** not explicitly covered
3. **Requires clarification** of disambiguation rules

**Action**: Propose an amendment via `grammar_amendment.md`

**Format**: See `grammar_amendment.md` for template.

**Review**: Human reviewers evaluate proposals quarterly and update this document via migration if needed.

---

## Part 9: Lookup Table Seed Reference

Cross-reference between this document and the PRD v2 database schema. All tables below are seeded in migrations M-004, M-022–M-028 per `docs/seed_data_addendum.md`.

| Lookup Table | Source Document | Keys Defined | Seeds In |
|---|---|---|---|
| `lookup_grammar_role` | This doc Part 2 | 8 (7 SEC + 1 expression_of_ideas) | M-004 |
| `lookup_grammar_focus` | This doc Part 3 | 32 (29 SEC + 3 expression_of_ideas) | M-004 |
| `lookup_dimension_compatibility` | PRD M-003 | 4 rules | M-004 |
| `lookup_syntactic_trap` | This doc Part 7 | 13 | M-022–M-028 |
| `lookup_syntactic_interruption` | seed_data_addendum.md | 4 | M-022–M-028 |
| `lookup_distractor_type` | Taxonomy v2 §4 | 4 | M-022–M-028 |
| `lookup_distractor_subtype` | Taxonomy v2 §4.1–4.5 | 25 | M-022–M-028 |
| `lookup_distractor_construction` | Taxonomy v2 §4.5–4.6 | 8 | M-022–M-028 |
| `lookup_semantic_relation` | Taxonomy v2 §4.7 | 8 | M-022–M-028 |
| `lookup_plausibility_source` | Taxonomy v2 §4.6 | 6 | M-022–M-028 |
| `lookup_eliminability` | seed_data_addendum.md | 3 | M-022–M-028 |

Style/difficulty tables (seeded in M-022–M-028, definitions in `seed_data_addendum.md`):

| Lookup Table | Keys |
|---|---|
| `lookup_syntactic_complexity` | 5 |
| `lookup_lexical_tier` | 5 |
| `lookup_inference_distance` | 5 |
| `lookup_evidence_distribution` | 5 |
| `lookup_noun_phrase_complexity` | 3 |
| `lookup_vocabulary_profile` | 5 |
| `lookup_cohesion_device` | 6 |
| `lookup_epistemic_stance` | 5 |
| `lookup_transitional_logic` | 6 |

---

## Appendix A: Quick Reference — Rule Selection

| If the question tests... | Use this `grammar_focus_key` |
|--------------------------|------------------------------|
| Incomplete sentence | `sentence_fragment` |
| Two clauses with comma only | `comma_splice` |
| Two clauses with no punctuation | `run_on_sentence` |
| Verb doesn't match subject number | `subject_verb_agreement` |
| Pronoun doesn't match antecedent | `pronoun_antecedent_agreement` |
| I/me, who/whom confusion | `pronoun_case` |
| Dangling or misplaced modifier | `modifier_placement` |
| List items with different forms | `parallel_structure` |
| Tense shift without reason | `verb_tense_consistency` |
| Finite vs. nonfinite verb | `verb_form` |
| Active vs. passive voice | `voice_active_passive` |
| Which vs. that, who vs. whom | `relative_pronouns` |
| Its vs. it's, their vs. they're | `possessive_contraction` |
| Comma usage (non-restrictive, intro, series) | `punctuation_comma` |
| Colon or dash after independent clause; matched-pair nonessential elements | `colon_dash_use` |
| Semicolon between independent clauses | `semicolon_use` |
| Apostrophe for possession | `apostrophe_use` |
| Appositive phrase punctuation (restrictive vs. non-restrictive) | `appositive_punctuation` |
| Hyphen in compound modifier | `hyphen_usage` |
| Fewer vs. less, amount vs. number | `noun_countability` |
| "Reason is because" | `logical_predication` |
| As vs. like, FANBOYS punctuation | `conjunction_usage` |
| More/most, -er/-est, as...as | `comparative_structures` |
| Double negatives, hardly...when | `negation` |
| So/neither inversion | `affirmative_agreement` |
| Omitted words in comparison | `elliptical_constructions` |
| Fixed preposition pairs (agree with/to, different from) | `preposition_idiom` |
| Article/determiner choice (a/an/the/this) | `determiners_articles` |
| Redundancy or wordiness | `redundancy_concision` |
| Precision/word choice (increase vs improve vs expand) | `precision_word_choice` |
| Register/tone consistency | `register_style_consistency` |
| Cause vs correlation, mismatched transitions | `logical_relationships` |
| "Only" placement, word order effects | `emphasis_meaning_shifts` |
| Overclaiming, correlation vs causation, data claims | `data_interpretation_claims` |

---

## Appendix B: Changelog

### v1.5 (2026-04-22)
- Added 3 new Expression of Ideas keys: `logical_relationships`, `emphasis_meaning_shifts`, `data_interpretation_claims`
- Expanded 12 existing keys with deep taxonomy sub-patterns from Meaning-Driven Grammar guide:
  - `logical_predication`: subject–predicate compatibility, category errors
  - `modifier_placement`: scope ambiguity, overextended modifiers
  - `comparative_structures`: implied comparisons, false equivalence
  - `noun_countability`: proportional clarity, overgeneral quantifiers
  - `negation`: misplaced negation, scope of negation, logical reversals
  - `redundancy_concision`: circular definitions, repeated meaning
  - `precision_word_choice`: near-synonym distinction, domain-specific precision, avoiding vagueness
  - `preposition_idiom`: fixed expressions, subtle idiom traps
  - `verb_form`: temporal & conditional logic, sequence clarity, mixed conditionals
  - `pronoun_antecedent_agreement`: reference clarity, vague nouns, distant references, implicit vs explicit
  - `elliptical_constructions`: recoverability, structural consistency, ambiguity in omission
n- Updated `lookup_grammar_role` count to 8 (added `expression_of_ideas`)
- Updated `lookup_grammar_focus` count to 32 (added `determiners_articles`, `logical_relationships`, `emphasis_meaning_shifts`, `data_interpretation_claims`)

### v1.4 (2026-04-22)
- Added `determiners_articles` grammar_focus_key under Agreement Rules
- Expanded `pronoun_antecedent_agreement` with pronoun clarity/ambiguity pattern
- Expanded `comparative_structures` with adjective vs. adverb after linking verbs
- Expanded `verb_form` with verb patterning / subcategorization and gerund vs. infinitive selection
- Expanded `modifier_placement` with modifier scope (semantic logic)
- Expanded `logical_predication` with sentence-level logic consistency
- Added new Part 3.9: Expression of Ideas (`redundancy_concision`, `precision_word_choice`, `register_style_consistency`) — marked for future separation from SEC taxonomy

### v1.3 (2026-04-21)
- Added explicit FANBOYS comma examples ("I studied, and I passed." vs "I studied and passed.")
- Added Oxford comma guidance in `punctuation_comma` Required list
- Added verb phrase splitting example in `punctuation_comma` Prohibited list ("She completed, the project.")
- Clarified complex series semicolon example in `semicolon_use`

### v1.2 (2026-04-18)
- Added `preposition_idiom` tracking structure to cover prepositional phrases and idiomatic combinations
- Added the `coaching_annotations` schema mapping to the Syntactic Traps section to fully align with VERBAL_TRAPS.md

### v1.1 (2026-04-18)
- Added `appositive_punctuation` as a distinct grammar_focus_key (restrictive vs. non-restrictive appositives)
- Added `quotation_punctuation` key (American English convention for periods/commas inside quotes)
- Expanded `verb_form` with subjunctive mood patterns and real vs. unreal conditional sentences
- Expanded `verb_tense_consistency` with present perfect vs. past perfect distinction
- Expanded `modifier_placement` with absolute phrase coverage
- Expanded Part 7 (Syntactic Traps) to full 13-key set from VERBAL_TRAPS.md; added schema field reference
- Added Part 8: LLM Ingestion Notes (No Change guidance, multi-error questions, passage-level tense register)
- Renumbered old Part 8 (Amendment Process) → Part 10
- Sources: DSAT_Grammar_Rules_Complete.md (Parts 3, 8, 12, 13, 15, 19), VERBAL_TRAPS.md

### v1.0 (2026-04-18)
- Initial consolidation from DSAT_Grammar_Rules_Complete.md, DSAT_Verbal_Master_Taxonomy_v2.md, grammar_research.md
- Aligned with College Board Digital SAT specifications
- Added 26 `grammar_focus_key` values with mappings
- Added disambiguation priority rules and decision tree
- Added frequency data from PT4, PT5, PT6, PT7-10 analysis
- Added distractor patterns by rule category
- Integrated syntactic traps from VERBAL_TRAPS.md
