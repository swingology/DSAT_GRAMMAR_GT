# data_interpretation_claims — Sub-pattern Drafts (Tier B, 1 PT example)

**Sub-pattern — Classification Logic Synthesis from Structured Notes**

(PT6 M2 Q33: "Having the potential to damage national security if disclosed, most routine diplomatic correspondence is classified as Confidential")

Construct a notes-synthesis prompt whose goal asks the student to apply a
classification or conditional rule from the notes to a specific case. The
correct option must combine two facts — the rule ("information causing 'damage'
is Confidential") and the case ("routine diplomatic correspondence causes damage
but not serious damage") — to produce a single sentence that identifies the
correct category. Distractors reverse the causal attribution (the government
classifies *as* Confidential rather than *because it is* Confidential), describe
the system without applying it, or broaden the scope to include irrelevant
details. The trap is that reversed-attribution options sound authoritative
because they use vocabulary directly from the notes.

Distractors: a reversed-attribution option that swaps the subject and predicate
of the classification rule, a partial-purpose option that restates the general
principle without specifying which category applies, and a scope-extension
option that introduces an irrelevant detail from the notes.

Classify with `syntactic_trap_key: "none"` and
`student_failure_mode_key: "notes_synthesis_wrong_goal"`.

---

**Sub-pattern — Proportional vs. Absolute Claim from Data**

[NO PT EVIDENCE — source: The Critical Reader]

Construct a passage or data set where values increase in absolute terms but
decrease or remain flat in proportional (per-capita, percentage, rate) terms —
or vice versa. The stem asks which claim the data best supports. The correct
option frames the claim in the proportional dimension; distractors state the
absolute trend (which is technically true but answers the wrong question), claim
a causal mechanism the data does not support, or conflate the two dimensions.
The trap is that students who read only the directional trend (up or down)
without checking whether the unit is absolute or proportional will select the
absolute-trend distractor.

Distractors: an absolute-trend option that is directionally true but addresses
the wrong unit, a causal-claim option that overreaches beyond the data, and a
scope-blend option that mixes absolute and proportional language ambiguously.

Classify with `syntactic_trap_key: "presupposition_trap"` and
`student_failure_mode_key: "overreading"`.

---

**Sub-pattern — Reversed Attribution in Data-Backed Claims**

[NO PT EVIDENCE — source: Khan Academy]

Construct a sentence or synthesis prompt where a relationship between two
variables is described, and the correct option must preserve the direction of
the relationship (X predicts Y, not Y predicts X). Distractors reverse the
independent and dependent variables, present a correlational statement as
causal, or swap the compared groups. All distractors use vocabulary and values
drawn directly from the source material, making them feel substantiated. The
trap is that the reversed-attribution distractor is nearly identical to the
correct answer except for which variable is the subject and which is the
outcome.

Distractors: a reversed-direction option that swaps cause and effect, a
correlation-as-causation option that overstates the relationship, and a
wrong-group option that attributes the finding to the wrong population.

Classify with `syntactic_trap_key: "none"` and
`student_failure_mode_key: "scope_blindness"`.