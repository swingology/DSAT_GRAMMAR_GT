# precision_word_choice — Sub-pattern Drafts (Tier B, 2 PT examples)

**Sub-pattern — Vague Pronoun vs. Specific Name in Rhetorical Synthesis**

(PT5 M1 Q31: "The real author of Adam Bede was Mary Ann Evans, who published the novel using the pseudonym George Eliot")

Construct a notes-synthesis prompt whose stated goal requires the student to
identify a specific person, entity, or value by name. The correct option names
the entity explicitly; distractors use vague pronominal references ("a woman,"
"someone," "they") or paraphrase around the name without actually stating it.
The trap is that vague options feel like they address the goal ("identifies the
author") while omitting the precise detail the goal demands (the actual name).
Students who prefer a fluent-sounding sentence over an exact one fall for the
vague option.

Distractors: partial-purpose option that restates context without naming the
target, a vague-pronoun option that gestures at the answer without specifying,
and an over-scope option that adds unsupported claims.

Classify with `syntactic_trap_key: "none"` and
`student_failure_mode_key: "notes_synthesis_content_omission"`.

---

**Sub-pattern — Qualified Generalization vs. Overstatement in Notes Synthesis**

(PT6 M1 Q33: "Although most materials used in dhow replicas are traditional, some modern materials are used")

Construct a notes-synthesis prompt whose goal asks for a generalization about a
topic where the notes include both a dominant pattern and a qualifier (e.g.,
"most X are Y" plus "some X are Z"). The correct option preserves the qualifier
("Although most…, some…"); distractors either drop the qualifier (pure
generalization), focus on a single detail, or shift scope to a different topic.
The trap is that the unqualified generalization sounds more confident and
"academic," but it overstates what the notes actually support.

Distractors: unqualified generalization that drops the qualifier, a narrow-
focus option that highlights one detail rather than generalizing, and a wrong-
scope option that discusses a related but irrelevant aspect.

Classify with `syntactic_trap_key: "none"` and
`student_failure_mode_key: "notes_synthesis_wrong_goal"`.

---

**Sub-pattern — Exact Word Selection in a Semantic Field**

[NO PT EVIDENCE — source: PrepScholar]

Construct a sentence with a blank where four real words share a broad semantic
field but only one carries the precise denotation, connotation, or selectional
fit the context requires (e.g., "exacerbated" vs. "worsened" vs. "increased" vs.
"heightened" before "tensions"). The passage context narrows the choice to one
word whose exact shade of meaning matches the noun or verb it modifies. The
trap is that near-synonyms are all grammatically viable and feel "close enough,"
but only one is precise. This sub-pattern is for word-precision items in
grammar-land, not for commonly-confused-word pairs (which belong in
`commonly_confused_words`).

Distractors: a near-synonym that is too broad or neutral, a near-synonym that
is too strong or extreme, and a near-synonym whose connotation clashes with the
surrounding register or tone.

Classify with `syntactic_trap_key: "none"` and
`student_failure_mode_key: "confused_word_substitution"`.