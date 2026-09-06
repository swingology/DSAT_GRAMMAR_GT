# Grammar Rules TODO — Stem Key Taxonomy

## Problems with the current stem key set

The current set mixes three different axes under one key, which will bite at generation time:

- `choose_best_quote` is a **stem surface form**.
- `choose_command_of_evidence_textual` is a **skill**.
- `choose_best_weakener` is a **stem variant** of that same skill.
- `choose_detail` vs. `choose_central_detail` is a **construct distinction** with an identical stem.
- `most_logically_completes` and `choose_best_inference` are the same item type.
- `word_in_context` / `words_in_context` collide.
- The `active…` prefix looks like a status badge that got pasted in by mistake.

## Proposed restructuring

Use `stem_key` (the exact wording template) as one field, with `skill`, `passage_mode`, and `answer_form` as separate columns.

College Board's own framing supports this: it says the stems are deliberately consistent regardless of passage, and lists roughly a dozen canonical forms across the four domains. It also notes the Standard English Conventions stem is identical for Boundaries and Form/Structure/Sense, with the skill distinguished only by whether the options differ in punctuation or in words/structure. The Reading and Writing section's consistency means the questions look similar no matter what passage you're reading — for SEC, the single stem covers Boundaries (options contain different punctuation) and Form, Structure, and Sense (options contain different words or sentence structures).

## Full stem inventory (operational bank)

Organized `domain → skill → stem_key → template → slots`. Bracketed items in a template are slots the generator fills.

### Craft and Structure

**Words in Context**
- `wic_fill_blank` — "Which choice completes the text with the most logical and precise word or phrase?" (blank in passage; answer_form: word | phrase)
- `wic_most_nearly_mean` — "As used in the text, what does the word "[word]" most nearly mean?" (word underlined in passage)
- `wic_phrase_most_nearly_mean` — same, but "the phrase "[phrase]""

**Text Structure and Purpose**
- `tsp_main_purpose` — "Which choice best states the main purpose of the text?" (variant verb: "describes")
- `tsp_overall_structure` — "Which choice best describes the overall structure of the text?"
- `tsp_underlined_function` — "Which choice best describes the function of the underlined sentence in the text as a whole?" (slot: sentence | portion | question)
- `tsp_ordinal_function` — "…the function of the second sentence in the text as a whole?" (no underline; ordinal slot; appears mostly in literary/poetry items)
- `tsp_purpose_of_element` — "Which choice best describes the main purpose of the [image/data/…] in the text?" (rare — keep flagged low-frequency)

**Cross-Text Connections** (paired texts only)
- `ctc_agree` — "Based on the texts, both authors would most likely agree with which statement?" (variant: "the author of Text 1 and the author of Text 2 would most likely agree…")
- `ctc_respond_underlined` — "Based on the texts, how would the author of Text 2 most likely respond to the underlined claim in Text 1?"
- `ctc_respond_named` — "…how would [researcher/critic name] (Text 2) most likely respond to the [claim/hypothesis/conclusion/argument] presented in Text 1?"
- `ctc_respond_group` — "…how would the researchers in Text 2 most likely respond to…" (slot: author | researchers | authors)
- `ctc_relationship` — "Which choice best describes the relationship between Text 1 and Text 2?" (rare)
- `ctc_view_of_topic` — "Based on the texts, how would the author of Text 2 most likely characterize [topic] as discussed in Text 1?" (rare)

### Information and Ideas

**Central Ideas and Details**
- `cid_main_idea` — "Which choice best states the main idea of the text?"
- `cid_detail_according_to` — "According to the text, [what/why/how] [proposition]?" (informational)
- `cid_detail_true_about` — "According to the text, what is true about [entity]?"
- `cid_detail_narrator` — "According to the text, what does the narrator indicate about [character/thing]?" (literary)
- `cid_detail_speaker` — "According to the text, what is the speaker's attitude toward / what does the speaker indicate about…" (poetry)
- `cid_based_on_text` — "Based on the text, [what/how/why]…?" (a softer detail stem that shades toward inference — tag it CID, not Inferences)

**Command of Evidence — Textual**
- `coe_t_finding_support` — "Which finding, if true, would most directly support [name]'s [hypothesis/claim/conclusion]?"
- `coe_t_finding_weaken` — "Which finding, if true, would most directly weaken/undermine [name]'s [claim]?"
- `coe_t_quotation_illustrate` — "Which quotation from [work title] most effectively illustrates the claim?" (passage is a student/critic claim, no primary text)
- `coe_t_quotation_support` — "Which quotation from [a critic / a reviewer / an expert] would most effectively support the student's claim?"
- `coe_t_statement_support` — "Which statement, if true, would most directly support the underlined claim?" (underlined-claim variant)
- `coe_t_example_illustrate` — "Which choice best illustrates the [idea] described in the text?" (rare)

**Command of Evidence — Quantitative** (table or graph present)
- `coe_q_complete_example` — "Which choice most effectively uses data from the [table/graph] to complete the example?"
- `coe_q_complete_statement` — "…to complete the statement / to complete the text?"
- `coe_q_support_claim` — "Which choice best describes data from the [table/graph] that support [name]'s [claim/conclusion]?"
- `coe_q_weaken_claim` — "…data from the graph that weaken [name]'s [claim]?" (rare)
- `coe_q_justify_conclusion` — "Which choice most effectively uses data from the table to justify the researchers' conclusion?"

**Inferences**
- `inf_logically_completes` — "Which choice most logically completes the text?" (passage ends with blank; nearly all inference items)
- `inf_most_strongly_suggests` — "Based on the text, what can most reasonably be inferred about / what does the text most strongly suggest about [X]?" (low frequency — keep because it appears)

### Expression of Ideas

**Transitions**
- `trans_logical` — "Which choice completes the text with the most logical transition?" (single stem; variation is entirely in the blank position and the logical relation being tested — that's a separate tag: contrast | addition | causal | sequence | example | concession | conclusion)

**Rhetorical Synthesis** (notes-bulleted passage)
- `rs_notes_goal` — "The student wants to [goal]. Which choice most effectively uses relevant information from the notes to accomplish this goal?" — one stem; the **goal slot** is the real generation key. Enumeration: `emphasize_similarity`, `emphasize_difference`, `introduce_to_unfamiliar_audience`, `present_study_and_findings`, `explain_advantage`, `explain_process`, `make_generalization`, `compare_two_items`, `emphasize_a_quantity/scale`, `describe_purpose_of_work`, `present_a_person's_accomplishment`, `note_a_limitation/caveat`.

### Standard English Conventions
- `sec_conform` — "Which choice completes the text so that it conforms to the conventions of Standard English?" — the only stem. Generation keys live below it:
  - `boundaries.*` — comma_splice, fragment, colon_before_list_or_explanation, semicolon_between_clauses, dash_supplement, nonessential_commas, no_punct_between_subject_verb
  - `fss.*` — subject_verb_agreement_with_interruption, verb_tense_consistency, pronoun_antecedent, dangling_modifier, parallelism, possessive_vs_plural, who/whom

---

That's ~40 stem keys, ~20 of which do 95% of the volume.

## Mapping the current list onto this inventory

- `choose_best_support`, `choose_command_of_evidence_textual`, `choose_best_quote`, `choose_best_illustration`, `choose_best_weakener` → collapse into the `coe_t_*` family
- `choose_main_purpose` / `choose_structure_description` / `choose_sentence_function` → become `tsp_*`
- `synthesize_information` and `choose_best_notes_synthesis` → one stem (`rs_notes_goal`) with a goal slot
- `most_logically_completes` and `choose_best_inference` → merge into `inf_logically_completes`
- `compare_contributions` → doesn't correspond to anything in the operational bank; drop it

## Next steps (research order)

1. `passage_mode` taxonomy — single, paired, notes, table, graph, poem, underlined-claim, drama excerpt with stage directions
2. Rhetorical-synthesis goal enumeration (verify against operational bank)
3. Math stem set
